"""Schema parsing and template rendering helpers."""

from __future__ import annotations
import json
from functools import cache
from typing import Any
from chatkit.widgets import WidgetRoot, WidgetTemplate
from pydantic import BaseModel
from mcp_chatkit_widget.naming import _sanitize_tool_name, _to_camel_case
from mcp_chatkit_widget.pydantic_conversion import json_schema_to_pydantic
from mcp_chatkit_widget.widget_loader import WidgetDefinition


def _model_metadata(widget_name: str) -> tuple[str, str]:
    """Build consistent model and schema titles from a widget name."""
    camel_name = _to_camel_case(_sanitize_tool_name(widget_name))
    return f"{camel_name}Model", f"{camel_name}Arguments"


@cache
def _build_pydantic_model(schema_dump: str, widget_name: str) -> type[BaseModel]:
    """Return a cached Pydantic model for the given schema snapshot."""
    schema = json.loads(schema_dump)
    model_name, schema_title = _model_metadata(widget_name)
    return json_schema_to_pydantic(schema, model_name, schema_title)


def build_widget_model(widget_def: WidgetDefinition) -> type[BaseModel]:
    """Convert a widget definition's JSON schema into a Pydantic model."""
    schema_dump = json.dumps(widget_def.json_schema, sort_keys=True)
    return _build_pydantic_model(schema_dump, widget_def.name)


@cache
def _load_widget_template(template_path: str) -> WidgetTemplate:
    """Load and cache a WidgetTemplate from disk."""
    return WidgetTemplate.from_file(template_path)


def render_widget_definition(widget_def: WidgetDefinition, **kwargs: Any) -> WidgetRoot:
    """Validate inputs, render the widget's template, and return a WidgetRoot."""
    model = build_widget_model(widget_def)
    validated = model(**kwargs)
    template = _load_widget_template(str(widget_def.file_path))
    render_context = validated.model_dump()
    render_context["undefined"] = None
    return template.build(render_context)


__all__ = [
    "build_widget_model",
    "render_widget_definition",
]
