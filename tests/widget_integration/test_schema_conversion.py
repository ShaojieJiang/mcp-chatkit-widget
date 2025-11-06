"""Tests for JSON schema to Pydantic model conversion."""

from __future__ import annotations
from typing import Any
from mcp_chatkit_widget.schema_utils import json_schema_to_pydantic
from mcp_chatkit_widget.server import _sanitize_tool_name, _to_camel_case
from .input_extractors import extract_input_data_from_preview


def _model_from_widget(widget: Any):
    camel_name = _to_camel_case(_sanitize_tool_name(widget.name))
    model_name = f"{camel_name}Model"
    return json_schema_to_pydantic(widget.json_schema, model_name)


class TestWidgetSchemaConversion:
    """Test JSON Schema to Pydantic model conversion."""

    def test_create_event_schema_conversion(self, create_event_widget: Any) -> None:
        """Test that Create Event widget schema converts correctly to Pydantic."""
        pydantic_model = _model_from_widget(create_event_widget)

        schema_props = create_event_widget.json_schema["properties"]
        model_fields = pydantic_model.model_fields

        assert set(model_fields.keys()) == set(schema_props.keys())

        required_fields = create_event_widget.json_schema.get("required", [])
        for field_name, field_info in model_fields.items():
            if field_name in required_fields:
                assert field_info.is_required(), (
                    f"Field {field_name} should be required"
                )
            else:
                assert not field_info.is_required(), (
                    f"Field {field_name} should be optional"
                )

        input_data = extract_input_data_from_preview(
            create_event_widget.json_schema,
            create_event_widget.output_json_preview,
        )
        instance = pydantic_model(**input_data)
        instance_dict = instance.model_dump()

        assert "date" in instance_dict
        assert "events" in instance_dict
        assert isinstance(instance_dict["events"], list)

    def test_flight_tracker_schema_conversion(self, flight_tracker_widget: Any) -> None:
        """Test that Flight Tracker widget schema converts correctly to Pydantic."""
        pydantic_model = _model_from_widget(flight_tracker_widget)

        schema_props = flight_tracker_widget.json_schema["properties"]
        model_fields = pydantic_model.model_fields

        assert set(model_fields.keys()) == set(schema_props.keys())

        required_fields = flight_tracker_widget.json_schema.get("required", [])
        for field_name, field_info in model_fields.items():
            if field_name in required_fields:
                assert field_info.is_required(), (
                    f"Field {field_name} should be required"
                )
            else:
                assert not field_info.is_required(), (
                    f"Field {field_name} should be optional"
                )

        input_data = extract_input_data_from_preview(
            flight_tracker_widget.json_schema,
            flight_tracker_widget.output_json_preview,
        )
        instance = pydantic_model(**input_data)
        instance_dict = instance.model_dump()

        assert "airline" in instance_dict
        assert "departure" in instance_dict
        assert "arrival" in instance_dict

    def test_pydantic_model_preserves_nested_objects(
        self, flight_tracker_widget: Any
    ) -> None:
        """Test that nested objects in schema are preserved in Pydantic model."""
        pydantic_model = _model_from_widget(flight_tracker_widget)

        airline_field = pydantic_model.model_fields["airline"]
        assert airline_field.annotation is not None

        input_data = extract_input_data_from_preview(
            flight_tracker_widget.json_schema,
            flight_tracker_widget.output_json_preview,
        )
        instance = pydantic_model(**input_data)

        assert hasattr(instance.airline, "name")
        assert hasattr(instance.airline, "logo")
