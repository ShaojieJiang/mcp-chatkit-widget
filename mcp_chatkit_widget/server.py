"""Tools for UI components."""

import inspect
import json
from typing import Any
from chatkit.widgets import WidgetComponentBase
from fastmcp import FastMCP
from jinja2 import Template
from pydantic import BaseModel
from mcp_chatkit_widget.schema_utils import (
    json_schema_to_chatkit_widget,
    json_schema_to_pydantic,
)
from mcp_chatkit_widget.widget_loader import discover_widgets


server = FastMCP("mcp-chatkit-widget")


def _sanitize_tool_name(widget_name: str) -> str:
    """Convert widget name to a valid Python function name.

    Args:
        widget_name: The widget name (e.g., "Flight Tracker")

    Returns:
        Sanitized function name (e.g., "flight_tracker")
    """
    # Replace spaces and special characters with underscores
    sanitized = widget_name.lower().replace(" ", "_").replace("-", "_")
    # Remove any non-alphanumeric characters except underscores
    sanitized = "".join(c for c in sanitized if c.isalnum() or c == "_")
    # Ensure it starts with a letter or underscore
    if sanitized and sanitized[0].isdigit():
        sanitized = "_" + sanitized
    return sanitized


def _to_camel_case(snake_str: str) -> str:
    """Convert snake_case string to CamelCase.

    Args:
        snake_str: String in snake_case format (e.g., "flight_tracker")

    Returns:
        String in CamelCase format (e.g., "FlightTracker")
    """
    components = snake_str.split("_")
    return "".join(x.title() for x in components)


def _create_widget_tool_function(
    widget_name: str,
    pydantic_model: type[BaseModel],
    template_str: str,
) -> Any:
    """Create a tool function for a specific widget.

    Args:
        widget_name: Display name of the widget
        pydantic_model: Pydantic model for input validation
        template_str: Jinja2 template string for rendering the widget

    Returns:
        Function that can be registered as an MCP tool
    """
    compiled_template = Template(template_str)

    def widget_tool(**kwargs: Any) -> WidgetComponentBase:
        """Dynamically generated tool function for a widget.

        This function validates input data against the widget's schema
        and returns a ChatKit widget component.
        """
        # Validate input using the Pydantic model
        validated_data = pydantic_model(**kwargs)

        # Render the template with the validated data
        # Include 'undefined' as None for Jinja2 templates that use it
        render_context = validated_data.model_dump()
        render_context["undefined"] = None
        rendered_json_str = compiled_template.render(**render_context)

        # Parse the rendered JSON string
        rendered_json = json.loads(rendered_json_str)

        # Convert the rendered JSON to a ChatKit widget
        widget = json_schema_to_chatkit_widget(rendered_json, widget_name)
        return widget

    # Set function metadata
    # Use CamelCase for function name (generates CamelCase schema title)
    widget_tool.__name__ = _to_camel_case(_sanitize_tool_name(widget_name))
    widget_tool.__doc__ = (
        f"Generate a {widget_name} widget.\n\n"
        f"This tool creates a {widget_name} widget with the provided data.\n"
        f"The input must conform to the widget's JSON schema."
    )

    # Create dynamic signature with individual parameters
    parameters = []
    for field_name, field_info in pydantic_model.model_fields.items():
        # Determine if the field is required
        if field_info.is_required():
            default = inspect.Parameter.empty
        else:
            default = field_info.default

        param = inspect.Parameter(
            field_name,
            inspect.Parameter.KEYWORD_ONLY,
            default=default,
            annotation=field_info.annotation,
        )
        parameters.append(param)

    widget_tool.__signature__ = inspect.Signature(  # type: ignore[attr-defined]
        parameters, return_annotation=WidgetComponentBase
    )

    # Also set annotations for compatibility
    annotations: dict[str, Any] = {}
    for field_name, field_info in pydantic_model.model_fields.items():
        annotations[field_name] = field_info.annotation
    annotations["return"] = WidgetComponentBase
    widget_tool.__annotations__ = annotations

    return widget_tool


def register_widget_tools() -> None:
    """Automatically discover and register tools for all widgets.

    This function scans the widgets directory, loads all .widget files,
    and dynamically creates and registers MCP tools for each widget.
    """
    widgets = discover_widgets()

    for widget_def in widgets:
        # Convert JSON schema to Pydantic model
        camel_name = _to_camel_case(_sanitize_tool_name(widget_def.name))
        model_name = camel_name + "Model"
        schema_title = camel_name + "Arguments"
        pydantic_model = json_schema_to_pydantic(
            widget_def.json_schema, model_name, schema_title
        )

        # Create the tool function
        tool_func = _create_widget_tool_function(
            widget_def.name, pydantic_model, widget_def.template
        )

        # Register the tool with FastMCP
        # Use snake_case for tool name, but function name is CamelCase
        tool_name = _sanitize_tool_name(widget_def.name)
        server.tool(name=tool_name)(tool_func)


# Automatically register all widget tools on module import
register_widget_tools()


if __name__ == "__main__":  # pragma: no cover
    import asyncio

    # For debugging, print registered tool names
    async def list_tools() -> None:
        """List all registered tools."""
        print("Registered tools:")
        tools = await server.get_tools()
        for tool_name in sorted(tools):
            print(f"  - {tool_name}")
            tool = await server.get_tool(tool_name)
            if tool and tool.description:
                print(f"    {tool.description.strip().split(chr(10))[0]}")

    asyncio.run(list_tools())
