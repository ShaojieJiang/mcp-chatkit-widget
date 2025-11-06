"""Tests that tool output matches the expected preview payloads exactly."""

from __future__ import annotations

from typing import Any

from chatkit.widgets import Card
from mcp_chatkit_widget.schema_utils import json_schema_to_pydantic
from mcp_chatkit_widget.server import (
    _create_widget_tool_function,
    _sanitize_tool_name,
    _to_camel_case,
)

from .helpers import deep_compare, extract_input_data_from_preview


def _model_name(widget_name: str) -> str:
    camel_name = _to_camel_case(_sanitize_tool_name(widget_name))
    return f"{camel_name}Model"


def _render_widget(widget_def: Any) -> Card:
    pydantic_model = json_schema_to_pydantic(
        widget_def.json_schema, _model_name(widget_def.name)
    )
    tool_func = _create_widget_tool_function(
        widget_def.name, pydantic_model, widget_def.template
    )
    input_data = extract_input_data_from_preview(
        widget_def.json_schema,
        widget_def.output_json_preview,
    )
    return tool_func(**input_data)


def test_create_event_output_matches_preview(create_event_widget: Any) -> None:
    """Create Event tool output should be identical to its preview JSON."""
    result = _render_widget(create_event_widget)
    result_dict = result.model_dump(exclude_none=True)
    assert deep_compare(result_dict, create_event_widget.output_json_preview)


def test_flight_tracker_output_matches_preview(flight_tracker_widget: Any) -> None:
    """Flight Tracker tool output should be identical to its preview JSON."""
    result = _render_widget(flight_tracker_widget)
    result_dict = result.model_dump(exclude_none=True)
    assert deep_compare(result_dict, flight_tracker_widget.output_json_preview)
