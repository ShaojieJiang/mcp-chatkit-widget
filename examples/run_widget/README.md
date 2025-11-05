# Widget Runner Example

This example showcases how does MCP ChatKit Widget server work.

## Overview

The widget runner shows how to:
- Load a widget definition from a file path
- Extract example input data from the widget's `outputJsonPreview`
- Connect to the MCP ChatKit Widget server via stdio transport
- Call widget tools with input data
- Convert the JSON output to `chatkit.widgets.Card` objects

Especially with the last two steps, it demonstrates how the tools might be called by AI agents, and how to consume the results for displaying in the ChatKit UI.

## Prerequisites

Make sure you have the project installed with all dependencies:

```bash
uv sync --all-groups
```

## Usage

Run any widget by providing its file path:

```bash
python examples/run_widget/run_widget.py <path/to/widget.widget>
```

**Examples:**
```bash
# Run Flight Tracker widget
python examples/run_widget/run_widget.py mcp_chatkit_widget/widgets/"Flight Tracker.widget"

# Run Create Event widget
python examples/run_widget/run_widget.py mcp_chatkit_widget/widgets/"Create Event.widget"
```

You can replace the widget file path with any other widget in the `mcp_chatkit_widget/widgets/` directory.

## How It Works

1. **Load widget definition** from the provided file path
2. **Extract sample input data** from the widget's `outputJsonPreview`
3. **Connect to MCP server** via stdio transport
4. **Call the widget tool** with the extracted data
5. **Display raw JSON output**
6. **Convert result** to a `chatkit.widgets.Card` object
7. **Show Card properties**

## Input Data Extraction

The script uses the `extract_input_data_from_preview()` function to intelligently extract input data:

- **Known widgets** (Flight Tracker, Create Event): Extracts specific data from the preview structure
- **Unknown widgets**: Generates default values based on the JSON schema
  - Strings: `"2025-01-01"` (to handle DatePicker fields)
  - Numbers: `0`
  - Booleans: `false`
  - Arrays: `[]`
  - Objects: Recursively generates nested defaults

## Available Widgets

All widget definitions are stored in:
```
mcp_chatkit_widget/widgets/
```

To see available widgets:
```bash
ls mcp_chatkit_widget/widgets/
```

## Example Output

When you run a widget, you'll see:

```
================================================================================
Flight Tracker Example (FastMCP Client)
================================================================================

Input Data:
{
  "number": "PA 845",
  "date": "Fri, Apr 25",
  "progress": "30%",
  "airline": {
    "name": "Pan American",
    "logo": "/panam.png"
  },
  ...
}

================================================================================

Tool Output (Raw JSON):
================================================================================
{
  "type": "Card",
  "size": "medium",
  "theme": "light",
  "children": [...]
}
================================================================================

Converting to chatkit.widgets.Card...
Widget type: Card
Is Card instance: True
Card size: medium
Card theme: light
Card background: white
Number of children: 3

================================================================================
Card widget created successfully!
================================================================================
Flight Tracker example completed successfully!
```

## MCP Server Configuration

The example uses the following FastMCP Client configuration:

```python
config = {
    "mcpServers": {
        "chatkit": {
            "transport": "stdio",
            "command": "mcp-chatkit-widget",
        }
    }
}
```

This connects to the installed `mcp-chatkit-widget` command via stdio transport.

## Implementation Details

The script consists of two main functions:

### `extract_input_data_from_preview(json_schema, output_json_preview)`

Extracts input data from the widget's `outputJsonPreview` by:
- Identifying known widget patterns (Flight Tracker, Create Event)
- Navigating the output structure to extract the original input values
- For unknown widgets, generating default values based on the JSON schema

### `run_widget_example(widget_path_str)`

Main function that:
- Loads the widget definition using `load_widget()`
- Extracts input data from the preview
- Connects to the MCP server using FastMCP Client
- Calls the widget tool with `client.call_tool()`
- Displays results and converts to Card widget

## Troubleshooting

**Error: "Widget file not found"**
- Check that the file path is correct
- Make sure the widget file exists in `mcp_chatkit_widget/widgets/`
- Use quotes around paths with spaces: `"Flight Tracker.widget"`

**Error: "command not found: mcp-chatkit-widget"**
- Make sure the package is installed: `uv sync`
- The `mcp-chatkit-widget` command should be available after installation

**Error: "Failed to connect to MCP server"**
- Verify the server is properly installed
- Check that the `mcp-chatkit-widget` command works: `mcp-chatkit-widget --help`

## Related Files

- **Widget Loader:** `../../mcp_chatkit_widget/widget_loader.py`
- **Schema Utils:** `../../mcp_chatkit_widget/schema_utils.py`
- **Server Implementation:** `../../mcp_chatkit_widget/server.py`
- **Integration Tests:** `../../tests/test_widget_integration.py`
