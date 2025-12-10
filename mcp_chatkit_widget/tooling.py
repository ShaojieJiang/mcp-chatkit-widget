"""Tooling helpers that expose FastMCP registration utilities."""

from __future__ import annotations
import inspect
from collections.abc import Callable
from typing import Any, cast
from chatkit.widgets import WidgetComponentBase
from fastmcp import FastMCP
from mcp_chatkit_widget.naming import _sanitize_tool_name, _to_camel_case
from mcp_chatkit_widget.rendering import build_widget_model, render_widget_definition
from mcp_chatkit_widget.widget_loader import WidgetDefinition


def _create_widget_tool_function(
    widget_def: WidgetDefinition,
) -> Callable[..., WidgetComponentBase]:
    """Create a FastMCP tool function for a given widget definition."""
    pydantic_model = build_widget_model(widget_def)

    def widget_tool(**kwargs: Any) -> WidgetComponentBase:
        return render_widget_definition(widget_def, **kwargs)

    camel_name = _to_camel_case(_sanitize_tool_name(widget_def.name))
    widget_tool.__name__ = camel_name
    widget_tool.__doc__ = (
        f"Generate a {widget_def.name} widget.\n\n"
        f"This tool creates a {widget_def.name} widget with the provided data.\n"
        f"The input must conform to the widget's JSON schema."
    )

    parameters: list[inspect.Parameter] = []
    for field_name, field_info in pydantic_model.model_fields.items():
        if field_info.is_required():
            default = inspect.Parameter.empty
        else:
            default = field_info.default

        parameters.append(
            inspect.Parameter(
                field_name,
                inspect.Parameter.KEYWORD_ONLY,
                default=default,
                annotation=field_info.annotation,
            )
        )

    cast(
        Any,
        widget_tool,
    ).__signature__ = inspect.Signature(
        parameters, return_annotation=WidgetComponentBase
    )

    annotations: dict[str, Any] = {
        field_name: field_info.annotation
        for field_name, field_info in pydantic_model.model_fields.items()
    }
    annotations["return"] = WidgetComponentBase
    cast(Any, widget_tool).__annotations__ = annotations

    return widget_tool


def generate_widget_tools(server: FastMCP, widget_defs: list[WidgetDefinition]) -> None:
    """Register sanitized FastMCP tools for each widget definition."""
    for widget_def in widget_defs:
        tool_func = _create_widget_tool_function(widget_def)
        tool_name = _sanitize_tool_name(widget_def.name)
        server.tool(name=tool_name)(tool_func)


__all__ = [
    "_sanitize_tool_name",
    "_to_camel_case",
    "_create_widget_tool_function",
    "generate_widget_tools",
]
