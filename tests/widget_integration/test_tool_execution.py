"""Tests that widget tools run successfully using preview-derived payloads."""

from __future__ import annotations

from typing import Any

from chatkit.widgets import Card
from mcp_chatkit_widget.schema_utils import json_schema_to_pydantic
from mcp_chatkit_widget.server import (
    _create_widget_tool_function,
    _sanitize_tool_name,
    _to_camel_case,
)

from .helpers import extract_input_data_from_preview, deep_compare


def _model_name(widget_name: str) -> str:
    camel_name = _to_camel_case(_sanitize_tool_name(widget_name))
    return f"{camel_name}Model"


def test_create_event_tool_produces_expected_output(create_event_widget: Any) -> None:
    """Create Event tool should match the bundled outputJsonPreview."""
    pydantic_model = json_schema_to_pydantic(
        create_event_widget.json_schema, _model_name(create_event_widget.name)
    )
    tool_func = _create_widget_tool_function(
        create_event_widget.name, pydantic_model, create_event_widget.template
    )
    input_data = extract_input_data_from_preview(
        create_event_widget.json_schema,
        create_event_widget.output_json_preview,
    )

    result = tool_func(**input_data)
    assert isinstance(result, Card)

    result_dict = result.model_dump(exclude_none=True)
    assert result_dict["type"] == "Card"
    assert result_dict["size"] == create_event_widget.output_json_preview["size"]
    assert len(result_dict["children"]) == len(
        create_event_widget.output_json_preview["children"]
    )

    assert deep_compare(result_dict, create_event_widget.output_json_preview)


def test_flight_tracker_tool_produces_expected_output(
    flight_tracker_widget: Any,
) -> None:
    """Flight Tracker tool should match the bundled outputJsonPreview."""
    pydantic_model = json_schema_to_pydantic(
        flight_tracker_widget.json_schema, _model_name(flight_tracker_widget.name)
    )
    tool_func = _create_widget_tool_function(
        flight_tracker_widget.name, pydantic_model, flight_tracker_widget.template
    )
    input_data = extract_input_data_from_preview(
        flight_tracker_widget.json_schema,
        flight_tracker_widget.output_json_preview,
    )

    result = tool_func(**input_data)
    assert isinstance(result, Card)

    result_dict = result.model_dump(exclude_none=True)
    assert result_dict["type"] == "Card"
    assert result_dict["size"] == flight_tracker_widget.output_json_preview["size"]
    assert (
        result_dict["theme"] == flight_tracker_widget.output_json_preview["theme"]
    )
    assert len(result_dict["children"]) == len(
        flight_tracker_widget.output_json_preview["children"]
    )

    assert deep_compare(result_dict, flight_tracker_widget.output_json_preview)


def test_all_widgets_can_execute_with_preview_data(all_widgets: list[Any]) -> None:
    """Every bundled widget should render successfully using its preview data."""
    assert all_widgets, "No widgets found"

    for widget_def in all_widgets:
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
        result = tool_func(**input_data)
        assert isinstance(result, Card)
