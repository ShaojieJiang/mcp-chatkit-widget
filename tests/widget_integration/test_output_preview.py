"""Tests that widget output matches the preview JSON exactly."""

from __future__ import annotations
import json
from typing import Any
from .input_extractors import extract_input_data_from_preview
from .tooling import build_tool_components, deep_compare


class TestWidgetOutputJsonPreview:
    """Test that tool output matches outputJsonPreview exactly."""

    def test_create_event_output_matches_preview_exactly(
        self, create_event_widget: Any
    ) -> None:
        _, tool_func = build_tool_components(create_event_widget)

        input_data = extract_input_data_from_preview(
            create_event_widget.json_schema,
            create_event_widget.output_json_preview,
        )

        result = tool_func(**input_data)
        result_dict = result.model_dump(exclude_none=True)

        expected = create_event_widget.output_json_preview
        match = deep_compare(result_dict, expected)

        expected_json = json.dumps(expected, indent=2)
        result_json = json.dumps(result_dict, indent=2)
        assert match, f"Output mismatch:\nExpected: {expected_json}\nGot: {result_json}"

    def test_flight_tracker_output_matches_preview_exactly(
        self, flight_tracker_widget: Any
    ) -> None:
        _, tool_func = build_tool_components(flight_tracker_widget)

        input_data = extract_input_data_from_preview(
            flight_tracker_widget.json_schema,
            flight_tracker_widget.output_json_preview,
        )

        result = tool_func(**input_data)
        result_dict = result.model_dump(exclude_none=True)

        expected = flight_tracker_widget.output_json_preview
        match = deep_compare(result_dict, expected)

        expected_json = json.dumps(expected, indent=2)
        result_json = json.dumps(result_dict, indent=2)
        assert match, f"Output mismatch:\nExpected: {expected_json}\nGot: {result_json}"
