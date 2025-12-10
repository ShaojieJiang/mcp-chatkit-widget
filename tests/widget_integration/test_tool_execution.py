"""Tests for widget tool execution."""

from __future__ import annotations
import json
from typing import Any
from chatkit.widgets import DynamicWidgetRoot
from .input_extractors import extract_input_data_from_preview
from .tooling import build_tool_components, deep_compare


class TestWidgetToolExecution:
    """Test widget tool execution with preview data."""

    def test_create_event_tool_produces_expected_output(
        self, create_event_widget: Any
    ) -> None:
        _, tool_func = build_tool_components(create_event_widget)

        input_data = extract_input_data_from_preview(
            create_event_widget.json_schema,
            create_event_widget.output_json_preview,
        )

        result = tool_func(**input_data)

        assert isinstance(result, DynamicWidgetRoot)

        result_dict = result.model_dump(exclude_none=True)

        assert result_dict["type"] == "Card"
        assert result_dict["size"] == create_event_widget.output_json_preview["size"]
        assert len(result_dict["children"]) == len(
            create_event_widget.output_json_preview["children"]
        )

        match = deep_compare(result_dict, create_event_widget.output_json_preview)
        expected_json = json.dumps(create_event_widget.output_json_preview, indent=2)
        result_json = json.dumps(result_dict, indent=2)
        assert match, f"Output mismatch:\nExpected: {expected_json}\nGot: {result_json}"

    def test_flight_tracker_tool_produces_expected_output(
        self, flight_tracker_widget: Any
    ) -> None:
        _, tool_func = build_tool_components(flight_tracker_widget)

        input_data = extract_input_data_from_preview(
            flight_tracker_widget.json_schema,
            flight_tracker_widget.output_json_preview,
        )

        result = tool_func(**input_data)

        assert isinstance(result, DynamicWidgetRoot)

        result_dict = result.model_dump(exclude_none=True)

        assert result_dict["type"] == "Card"
        assert result_dict["size"] == flight_tracker_widget.output_json_preview["size"]
        assert (
            result_dict["theme"] == flight_tracker_widget.output_json_preview["theme"]
        )
        assert len(result_dict["children"]) == len(
            flight_tracker_widget.output_json_preview["children"]
        )

        match = deep_compare(result_dict, flight_tracker_widget.output_json_preview)
        expected_json = json.dumps(flight_tracker_widget.output_json_preview, indent=2)
        result_json = json.dumps(result_dict, indent=2)
        assert match, f"Output mismatch:\nExpected: {expected_json}\nGot: {result_json}"

    def test_all_widgets_can_execute_with_preview_data(
        self, all_widgets: list[Any]
    ) -> None:
        assert len(all_widgets) > 0, "No widgets found"

        for widget_def in all_widgets:
            _, tool_func = build_tool_components(widget_def)

            input_data = extract_input_data_from_preview(
                widget_def.json_schema,
                widget_def.output_json_preview,
            )

            result = tool_func(**input_data)

            assert result is not None
            assert isinstance(result, DynamicWidgetRoot)
