# Product Requirements Document

## Project

**Name:** `mcp-chatkit-widget`

## Overview

- `mcp-chatkit-widget` is a Model Context Protocol (MCP) server that transforms ChatKit Studio `.widget` definition files into callable MCP tools.
- Each `.widget` file defines a UI component with input schema (JSON Schema), template (Jinja2), and output preview.
- The server exposes these widgets as MCP tools so agents can dynamically generate ChatKit widgets using the `openai-chatkit` Python SDK.

## Goals

- Automate MCP tool generation from ChatKit `.widget` files.
- Enable agents to dynamically generate ChatKit widgets by calling MCP tools with AI-generated parameters.
- Preserve fidelity between ChatKit Studio definitions and the Python runtime model.

## Inputs

- **Directory:** `mcp_chatkit_widget/widgets/`
- Each `.widget` file is JSON with the following fields:
  - `version`: Widget format version (e.g., "1.0")
  - `name`: Widget display name used to derive tool identifiers (e.g., "Flight Tracker")
  - `template`: Jinja2 template string that renders to JSON widget structure
  - `jsonSchema`: JSON Schema definition for widget input parameters
  - `outputJsonPreview`: Example output structure showing the rendered widget
  - `encodedWidget`: (Optional) Base64-encoded representation of the widget layout from ChatKit Studio

## Core Functionality

### 1. MCP Tool Generation

For every `.widget` file, a dynamic MCP tool is created with:

- **Tool name:** Widget `name` field converted to `snake_case` (e.g., "Flight Tracker" → `flight_tracker`)
- **Input schema:** `jsonSchema` converted to a dynamic Pydantic model with:
  - Support for nested objects, arrays, primitives, and optional fields
  - Type-safe validation of all input parameters
  - Individual parameters exposed directly (not wrapped in a single object)
- **Output:** ChatKit `WidgetComponentBase` instance from the `openai-chatkit` library
- **Tool behavior:**
  1. Validate input parameters against the generated Pydantic model
  2. Render the Jinja2 template with validated data to produce JSON
  3. Parse the rendered JSON and convert to ChatKit widget objects
  4. Return a structured widget that can be serialized and displayed

#### Implementation Example

For `Flight Tracker.widget`, the system generates:

```python
# Generated Pydantic model
class FlightTrackerModel(BaseModel):
    number: str
    date: str
    progress: str
    airline: FlightTrackerModelAirline  # Nested model
    departure: FlightTrackerModelDeparture  # Nested model
    arrival: FlightTrackerModelArrival  # Nested model

# Generated tool function
@server.tool(name="flight_tracker")
def FlightTracker(
    number: str,
    date: str,
    progress: str,
    airline: FlightTrackerModelAirline,
    departure: FlightTrackerModelDeparture,
    arrival: FlightTrackerModelArrival,
) -> WidgetComponentBase:
    """Generate a Flight Tracker widget.

    This tool creates a Flight Tracker widget with the provided data.
    The input must conform to the widget's JSON schema.
    """
    # Validate input
    validated_data = FlightTrackerModel(
        number=number, date=date, progress=progress,
        airline=airline, departure=departure, arrival=arrival
    )

    # Render Jinja2 template
    template = Template(widget_def.template)
    rendered_json_str = template.render(**validated_data.model_dump())

    # Convert to ChatKit widget
    rendered_json = json.loads(rendered_json_str)
    widget = json_schema_to_chatkit_widget(rendered_json, "Flight Tracker")

    return widget  # Returns chatkit.widgets.Card instance
```

## System Architecture

The system consists of several modular components:

### Widget Loader (`widget_loader.py`)
- **Responsibility:** Discover and parse `.widget` files
- **Key Functions:**
  - `discover_widgets()`: Scans `mcp_chatkit_widget/widgets/` directory
  - `load_widget()`: Parses JSON and validates required fields
  - `get_widget_by_name()`: Retrieves a specific widget by name
- **Output:** `WidgetDefinition` dataclass containing all widget metadata

### Schema Utilities (`schema_utils.py`)
- **Responsibility:** Convert schemas and JSON to Python objects
- **Key Functions:**
  - `json_schema_to_pydantic()`: Creates dynamic Pydantic models from JSON Schema
    - Handles nested objects recursively
    - Maps JSON types to Python types (string→str, integer→int, etc.)
    - Supports optional vs. required fields
    - Sets custom schema titles for MCP tool documentation
  - `json_schema_to_chatkit_widget()`: Converts rendered JSON to ChatKit widget instances
  - `_dict_to_widget_component()`: Recursively instantiates ChatKit components (Card, Row, Text, etc.)

### MCP Server (`server.py`)
- **Responsibility:** FastMCP server implementation and tool registration
- **Key Functions:**
  - `_sanitize_tool_name()`: Converts widget names to valid Python identifiers
  - `_to_camel_case()`: Formats names for schema generation
  - `_create_widget_tool_function()`: Generates tool functions with proper signatures
  - `register_widget_tools()`: Automatically discovers and registers all widget tools
- **Server Instance:** `server = FastMCP("mcp-chatkit-widget")`
- **Tool Registration:** Tools are registered on module import via `register_widget_tools()`

### Data Flow

1. **Startup:** Server imports trigger `register_widget_tools()`
2. **Discovery:** `discover_widgets()` finds all `.widget` files
3. **Schema Conversion:** Each widget's `jsonSchema` → Pydantic model
4. **Tool Creation:** Dynamic function created with proper signature and docstring
5. **Registration:** Tool registered with FastMCP using snake_case name
6. **Runtime:** Agent calls tool → validation → template rendering → widget creation

## Technical Details

| Aspect                | Implementation                                        |
| --------------------- | ----------------------------------------------------- |
| Language              | Python 3.12+                                          |
| Package Manager       | `uv` (modern Python package manager)                  |
| Core Dependencies     | `fastmcp>=2.13.0.2`, `openai-chatkit>=1.1.0`         |
| MCP Framework         | FastMCP (high-level MCP server library)               |
| Template Engine       | Jinja2 (for rendering widget JSON from templates)     |
| Validation            | Pydantic v2 (dynamic model generation)                |
| Output format         | ChatKit `WidgetComponentBase` instances               |
| Directory convention  | `mcp_chatkit_widget/widgets/*.widget`                 |
| Entry Point           | `mcp-chatkit-widget` console script → `main()`        |
| Hot Reload            | Not currently implemented                             |

## Example Output (Resource Registration)

```json
{
  "resources": [
    {
      "id": "flight_tracker_template",
      "mime_type": "text/html",
      "data": "<Card size=\"md\" theme=\"dark\">...</Card>"
    },
    {
      "id": "flight_tracker_encoded",
      "mime_type": "application/base64",
      "data": "eyJpZCI6ICJ3aWdfajNhY..."
    }
  ]
}
```

## Success Criteria

- ✅ Every `.widget` in `mcp_chatkit_widget/widgets/` becomes an MCP tool
- ✅ Generated Pydantic models correctly validate input data
- ✅ Tool signatures expose individual parameters (not wrapped objects)
- ✅ Jinja2 templates render correctly with validated input data
- ✅ Returned ChatKit widgets are valid `WidgetComponentBase` instances
- ✅ Widgets can be serialized and rendered in ChatKit-compatible clients
- ✅ Tool discovery and invocation works in MCP-compatible environments

## Current Implementation Status

**Implemented:**
- ✅ Widget discovery and loading from `.widget` files
- ✅ Dynamic Pydantic model generation from JSON Schema
- ✅ Recursive handling of nested object schemas
- ✅ Jinja2 template rendering with validated data
- ✅ Conversion of JSON to ChatKit widget component tree
- ✅ FastMCP server with automatic tool registration
- ✅ 16+ example widgets included
- ✅ Load `.widget` files from user-specified widget directory

**Not Implemented:**
- ❌ MCP resources (template and encoded widget exposure)
- ❌ Support for enum types in JSON Schema
- ❌ Array item type constraints (currently `list[Any]`)
- ❌ Advanced JSON Schema features (conditionals, $ref, etc.)
