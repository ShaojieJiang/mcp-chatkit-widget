"""Integration tests for widget files.

This module tests that:
1. JSON Schema to Pydantic model conversion preserves schema structure
2. Widget tools execute correctly and produce expected output
3. Output matches the outputJsonPreview defined in widget files
"""

import json
from pathlib import Path
from typing import Any
import pytest
from chatkit.widgets import Card
from mcp_chatkit_widget.schema_utils import (
    json_schema_to_pydantic,
)
from mcp_chatkit_widget.server import (
    _create_widget_tool_function,
    _sanitize_tool_name,
    _to_camel_case,
)
from mcp_chatkit_widget.widget_loader import discover_widgets, load_widget


@pytest.fixture
def widgets_dir() -> Path:
    """Return the path to the widgets directory."""
    return Path(__file__).parent.parent / "mcp_chatkit_widget" / "widgets"


@pytest.fixture
def all_widgets(widgets_dir: Path) -> list[Any]:
    """Load all widget definitions from the widgets directory."""
    return discover_widgets(widgets_dir)


@pytest.fixture
def create_event_widget(widgets_dir: Path) -> Any:
    """Load the Create Event widget definition."""
    widget_path = widgets_dir / "Create Event.widget"
    return load_widget(widget_path)


@pytest.fixture
def flight_tracker_widget(widgets_dir: Path) -> Any:
    """Load the Flight Tracker widget definition."""
    widget_path = widgets_dir / "Flight Tracker.widget"
    return load_widget(widget_path)


def extract_input_data_from_preview(  # noqa: C901, PLR0912, PLR0915
    json_schema: dict[str, Any],
    output_json_preview: dict[str, Any],
) -> dict[str, Any]:
    """Extract input data from the widget's outputJsonPreview.

    This function infers what input data was used to generate the preview
    based on the JSON schema structure. For the test widgets, we extract
    the data from the known structure.

    Args:
        json_schema: The widget's JSON schema
        output_json_preview: The preview output JSON

    Returns:
        Dictionary with input data that should produce the output
    """
    # For Create Event widget
    if "date" in json_schema.get("properties", {}) and "events" in json_schema.get(
        "properties", {}
    ):
        # Extract date information
        date_info = None
        events_list = []

        # Navigate through the output structure to find the data
        if output_json_preview.get("type") == "Card":
            for child in output_json_preview.get("children", []):
                if child.get("type") == "Row":
                    for col in child.get("children", []):
                        if col.get("type") == "Col" and "width" in col:
                            # This is the date column
                            col_children = col.get("children", [])
                            if len(col_children) >= 2:
                                caption = col_children[0]
                                title = col_children[1]
                                date_info = {
                                    "name": caption.get("value"),
                                    "number": title.get("value"),
                                }
                        elif col.get("type") == "Col" and col.get("flex") == "auto":
                            # This is the events column
                            for event_row in col.get("children", []):
                                if (
                                    event_row.get("type") == "Row"
                                    and "key" in event_row
                                ):
                                    row_children = event_row.get("children", [])
                                    if len(row_children) >= 2:
                                        # First child is the colored box
                                        box = row_children[0]
                                        # Second child is the Col with title and time
                                        event_col = row_children[1]
                                        event_texts = event_col.get("children", [])

                                        if len(event_texts) >= 2:
                                            event = {
                                                "id": event_row.get("key"),
                                                "title": event_texts[0].get("value"),
                                                "time": event_texts[1].get("value"),
                                                "color": box.get("background"),
                                                "isNew": event_row.get("background")
                                                == "none",
                                            }
                                            events_list.append(event)

        return {"date": date_info, "events": events_list}

    # For Flight Tracker widget
    if "airline" in json_schema.get(
        "properties", {}
    ) and "departure" in json_schema.get("properties", {}):
        data: dict[str, Any] = {
            "number": "",
            "date": "",
            "progress": "",
            "airline": {"name": "", "logo": ""},
            "departure": {"city": "", "status": "", "time": ""},
            "arrival": {"city": "", "status": "", "time": ""},
        }

        if output_json_preview.get("type") == "Card":
            children = output_json_preview.get("children", [])

            # First row contains airline logo, flight number, and date
            if len(children) > 0 and children[0].get("type") == "Row":
                header_children = children[0].get("children", [])
                if len(header_children) >= 4:
                    data["airline"]["logo"] = header_children[0].get("src", "")
                    data["number"] = header_children[1].get("value", "")
                    data["date"] = header_children[3].get("value", "")

            # Third element is Col with flight details
            if len(children) > 2 and children[2].get("type") == "Col":
                col_children = children[2].get("children", [])

                # First row has cities
                if len(col_children) > 0 and col_children[0].get("type") == "Row":
                    city_children = col_children[0].get("children", [])
                    if len(city_children) >= 3:
                        data["departure"]["city"] = city_children[0].get("value", "")
                        data["arrival"]["city"] = city_children[2].get("value", "")

                # Second element is the progress box
                if len(col_children) > 1 and col_children[1].get("type") == "Box":
                    progress_children = col_children[1].get("children", [])
                    if progress_children:
                        data["progress"] = progress_children[0].get("width", "")

                # Third row has times and statuses
                if len(col_children) > 2 and col_children[2].get("type") == "Row":
                    time_children = col_children[2].get("children", [])
                    if len(time_children) >= 3:
                        # Departure info
                        dep_children = time_children[0].get("children", [])
                        if len(dep_children) >= 2:
                            data["departure"]["time"] = dep_children[0].get("value", "")
                            data["departure"]["status"] = dep_children[1].get(
                                "value", ""
                            )

                        # Arrival info
                        arr_children = time_children[2].get("children", [])
                        if len(arr_children) >= 2:
                            data["arrival"]["status"] = arr_children[0].get("value", "")
                            data["arrival"]["time"] = arr_children[1].get("value", "")

        return data

    # Generic extraction for other widgets - extract values from preview
    # and create a simple data structure that matches the schema
    def extract_simple_values(obj: Any) -> list[Any]:
        """Recursively extract simple values (strings, numbers) from nested object."""
        values = []
        if isinstance(obj, dict):
            # Extract direct value fields
            if "value" in obj:
                values.append(obj["value"])
            if "src" in obj:
                values.append(obj["src"])
            # Recurse into children
            if "children" in obj and isinstance(obj["children"], list):
                for child in obj["children"]:
                    values.extend(extract_simple_values(child))
        elif isinstance(obj, list):
            for item in obj:
                values.extend(extract_simple_values(item))
        return values

    def create_default_value(schema_def: dict[str, Any]) -> Any:
        """Create a default value based on schema type."""
        schema_type = schema_def.get("type")
        if schema_type == "string":
            # Use a valid date format as default to handle DatePicker fields
            return "2025-01-01"
        elif schema_type in {"number", "integer"}:
            return 0
        elif schema_type == "boolean":
            return False
        elif schema_type == "array":
            return []
        elif schema_type == "object":
            obj = {}
            properties = schema_def.get("properties", {})
            for prop_name, prop_schema in properties.items():
                obj[prop_name] = create_default_value(prop_schema)
            return obj
        return None

    # For other widgets, create a minimal valid input based on schema
    properties = json_schema.get("properties", {})
    result = {}

    for prop_name, prop_schema in properties.items():
        result[prop_name] = create_default_value(prop_schema)

    return result


class TestWidgetSchemaConversion:
    """Test JSON Schema to Pydantic model conversion."""

    def test_create_event_schema_conversion(self, create_event_widget: Any) -> None:
        """Test that Create Event widget schema converts correctly to Pydantic."""
        # Convert JSON schema to Pydantic model
        camel_name = _to_camel_case(_sanitize_tool_name(create_event_widget.name))
        model_name = camel_name + "Model"
        pydantic_model = json_schema_to_pydantic(
            create_event_widget.json_schema, model_name
        )

        # Verify model fields match schema properties
        schema_props = create_event_widget.json_schema["properties"]
        model_fields = pydantic_model.model_fields

        assert set(model_fields.keys()) == set(schema_props.keys())

        # Verify required fields
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

        # Test that we can create an instance with valid data
        input_data = extract_input_data_from_preview(
            create_event_widget.json_schema,
            create_event_widget.output_json_preview,
        )
        instance = pydantic_model(**input_data)
        assert instance is not None

        # Verify the JSON schema round-trip
        instance_dict = instance.model_dump()
        assert "date" in instance_dict
        assert "events" in instance_dict
        assert isinstance(instance_dict["events"], list)

    def test_flight_tracker_schema_conversion(self, flight_tracker_widget: Any) -> None:
        """Test that Flight Tracker widget schema converts correctly to Pydantic."""
        # Convert JSON schema to Pydantic model
        camel_name = _to_camel_case(_sanitize_tool_name(flight_tracker_widget.name))
        model_name = camel_name + "Model"
        pydantic_model = json_schema_to_pydantic(
            flight_tracker_widget.json_schema, model_name
        )

        # Verify model fields match schema properties
        schema_props = flight_tracker_widget.json_schema["properties"]
        model_fields = pydantic_model.model_fields

        assert set(model_fields.keys()) == set(schema_props.keys())

        # Verify required fields
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

        # Test that we can create an instance with valid data
        input_data = extract_input_data_from_preview(
            flight_tracker_widget.json_schema,
            flight_tracker_widget.output_json_preview,
        )
        instance = pydantic_model(**input_data)
        assert instance is not None

        # Verify the JSON schema round-trip
        instance_dict = instance.model_dump()
        assert "airline" in instance_dict
        assert "departure" in instance_dict
        assert "arrival" in instance_dict

    def test_pydantic_model_preserves_nested_objects(
        self, flight_tracker_widget: Any
    ) -> None:
        """Test that nested objects in schema are preserved in Pydantic model."""
        camel_name = _to_camel_case(_sanitize_tool_name(flight_tracker_widget.name))
        model_name = camel_name + "Model"
        pydantic_model = json_schema_to_pydantic(
            flight_tracker_widget.json_schema, model_name
        )

        # Check nested object fields exist and are BaseModel instances
        airline_field = pydantic_model.model_fields["airline"]
        assert airline_field.annotation is not None

        # Verify nested model can be validated
        input_data = extract_input_data_from_preview(
            flight_tracker_widget.json_schema,
            flight_tracker_widget.output_json_preview,
        )
        instance = pydantic_model(**input_data)
        assert hasattr(instance.airline, "name")
        assert hasattr(instance.airline, "logo")


class TestWidgetToolExecution:
    """Test widget tool execution with preview data."""

    def test_create_event_tool_produces_expected_output(
        self, create_event_widget: Any
    ) -> None:
        """Test that Create Event tool produces output matching outputJsonPreview."""
        # Create Pydantic model
        camel_name = _to_camel_case(_sanitize_tool_name(create_event_widget.name))
        model_name = camel_name + "Model"
        pydantic_model = json_schema_to_pydantic(
            create_event_widget.json_schema, model_name
        )

        # Create tool function
        tool_func = _create_widget_tool_function(
            create_event_widget.name,
            pydantic_model,
            create_event_widget.template,
        )

        # Extract input data from preview
        input_data = extract_input_data_from_preview(
            create_event_widget.json_schema,
            create_event_widget.output_json_preview,
        )

        # Execute the tool
        result = tool_func(**input_data)

        # Verify result is a Card widget
        assert isinstance(result, Card)

        # Convert result to dict for comparison
        result_dict = result.model_dump(exclude_none=True)

        # Verify key structural elements match
        assert result_dict["type"] == "Card"
        assert result_dict["size"] == create_event_widget.output_json_preview["size"]
        assert len(result_dict["children"]) == len(
            create_event_widget.output_json_preview["children"]
        )

        # Verify the result JSON structure matches the expected output
        # Use deep comparison to handle type coercion (int vs float)
        match = TestWidgetOutputJsonPreview._deep_compare(
            result_dict, create_event_widget.output_json_preview
        )
        expected_json = json.dumps(create_event_widget.output_json_preview, indent=2)
        result_json = json.dumps(result_dict, indent=2)
        assert match, f"Output mismatch:\nExpected: {expected_json}\nGot: {result_json}"

    def test_flight_tracker_tool_produces_expected_output(
        self, flight_tracker_widget: Any
    ) -> None:
        """Test that Flight Tracker tool produces output matching outputJsonPreview."""
        # Create Pydantic model
        camel_name = _to_camel_case(_sanitize_tool_name(flight_tracker_widget.name))
        model_name = camel_name + "Model"
        pydantic_model = json_schema_to_pydantic(
            flight_tracker_widget.json_schema, model_name
        )

        # Create tool function
        tool_func = _create_widget_tool_function(
            flight_tracker_widget.name,
            pydantic_model,
            flight_tracker_widget.template,
        )

        # Extract input data from preview
        input_data = extract_input_data_from_preview(
            flight_tracker_widget.json_schema,
            flight_tracker_widget.output_json_preview,
        )

        # Execute the tool
        result = tool_func(**input_data)

        # Verify result is a Card widget
        assert isinstance(result, Card)

        # Convert result to dict for comparison
        result_dict = result.model_dump(exclude_none=True)

        # Verify key structural elements match
        assert result_dict["type"] == "Card"
        assert result_dict["size"] == flight_tracker_widget.output_json_preview["size"]
        assert (
            result_dict["theme"] == flight_tracker_widget.output_json_preview["theme"]
        )
        assert len(result_dict["children"]) == len(
            flight_tracker_widget.output_json_preview["children"]
        )

        # Verify the result JSON structure matches the expected output
        # Use deep comparison to handle type coercion (int vs float)
        match = TestWidgetOutputJsonPreview._deep_compare(
            result_dict, flight_tracker_widget.output_json_preview
        )
        expected_json = json.dumps(flight_tracker_widget.output_json_preview, indent=2)
        result_json = json.dumps(result_dict, indent=2)
        assert match, f"Output mismatch:\nExpected: {expected_json}\nGot: {result_json}"

    def test_all_widgets_can_execute_with_preview_data(
        self, all_widgets: list[Any]
    ) -> None:
        """Test that all widgets can execute successfully with their preview data."""
        assert len(all_widgets) > 0, "No widgets found"

        for widget_def in all_widgets:
            # Create Pydantic model
            camel_name = _to_camel_case(_sanitize_tool_name(widget_def.name))
            model_name = camel_name + "Model"
            pydantic_model = json_schema_to_pydantic(widget_def.json_schema, model_name)

            # Create tool function
            tool_func = _create_widget_tool_function(
                widget_def.name,
                pydantic_model,
                widget_def.template,
            )

            # Extract input data from preview
            input_data = extract_input_data_from_preview(
                widget_def.json_schema,
                widget_def.output_json_preview,
            )

            # Execute the tool - should not raise any exceptions
            result = tool_func(**input_data)

            # Verify result is a widget
            assert result is not None
            assert isinstance(result, Card)


class TestWidgetOutputJsonPreview:
    """Test that tool output matches outputJsonPreview exactly."""

    def test_create_event_output_matches_preview_exactly(
        self, create_event_widget: Any
    ) -> None:
        """Test that Create Event tool output is identical to outputJsonPreview."""
        # Create Pydantic model
        camel_name = _to_camel_case(_sanitize_tool_name(create_event_widget.name))
        model_name = camel_name + "Model"
        pydantic_model = json_schema_to_pydantic(
            create_event_widget.json_schema, model_name
        )

        # Create tool function
        tool_func = _create_widget_tool_function(
            create_event_widget.name,
            pydantic_model,
            create_event_widget.template,
        )

        # Extract input data
        input_data = extract_input_data_from_preview(
            create_event_widget.json_schema,
            create_event_widget.output_json_preview,
        )

        # Execute tool and get result
        result = tool_func(**input_data)
        result_dict = result.model_dump(exclude_none=True)

        # Compare with expected output
        expected = create_event_widget.output_json_preview

        # Deep comparison
        match = self._deep_compare(result_dict, expected)
        expected_json = json.dumps(expected, indent=2)
        result_json = json.dumps(result_dict, indent=2)
        assert match, f"Output mismatch:\nExpected: {expected_json}\nGot: {result_json}"

    def test_flight_tracker_output_matches_preview_exactly(
        self, flight_tracker_widget: Any
    ) -> None:
        """Test that Flight Tracker tool output is identical to outputJsonPreview."""
        # Create Pydantic model
        camel_name = _to_camel_case(_sanitize_tool_name(flight_tracker_widget.name))
        model_name = camel_name + "Model"
        pydantic_model = json_schema_to_pydantic(
            flight_tracker_widget.json_schema, model_name
        )

        # Create tool function
        tool_func = _create_widget_tool_function(
            flight_tracker_widget.name,
            pydantic_model,
            flight_tracker_widget.template,
        )

        # Extract input data
        input_data = extract_input_data_from_preview(
            flight_tracker_widget.json_schema,
            flight_tracker_widget.output_json_preview,
        )

        # Execute tool and get result
        result = tool_func(**input_data)
        result_dict = result.model_dump(exclude_none=True)

        # Compare with expected output
        expected = flight_tracker_widget.output_json_preview

        # Deep comparison
        match = self._deep_compare(result_dict, expected)
        expected_json = json.dumps(expected, indent=2)
        result_json = json.dumps(result_dict, indent=2)
        assert match, f"Output mismatch:\nExpected: {expected_json}\nGot: {result_json}"

    @staticmethod
    def _deep_compare(obj1: Any, obj2: Any) -> bool:  # noqa: C901, PLR0911
        """Recursively compare two objects for equality.

        This comparison is lenient with numeric types (int vs float)
        and handles None/missing field differences gracefully.

        Args:
            obj1: First object
            obj2: Second object

        Returns:
            True if objects are equal, False otherwise
        """
        # Handle None values
        if obj1 is None and obj2 is None:
            return True
        if obj1 is None or obj2 is None:
            return False

        # Handle numeric types with lenience (int 8 == float 8.0)
        if isinstance(obj1, (int, float)) and isinstance(obj2, (int, float)):
            return abs(obj1 - obj2) < 1e-10

        # Type mismatch (except for numeric types handled above)
        if not isinstance(obj1, type(obj2)):
            return False

        if isinstance(obj1, dict):
            # For dict comparison, we allow obj1 (actual) to have extra keys
            # that obj2 (expected) doesn't have, since the chatkit library
            # may add default values. However, all keys in obj2 must be in obj1.

            # Check all keys in expected (obj2)
            for key in obj2.keys():
                if key not in obj1:
                    # Expected key is missing from actual
                    return False

                val1 = obj1[key]
                val2 = obj2[key]

                # Compare values
                if not TestWidgetOutputJsonPreview._deep_compare(val1, val2):
                    return False

            return True

        if isinstance(obj1, list):
            if len(obj1) != len(obj2):
                return False
            return all(
                TestWidgetOutputJsonPreview._deep_compare(a, b)
                for a, b in zip(obj1, obj2, strict=True)
            )

        if isinstance(obj1, str):
            return obj1 == obj2

        return obj1 == obj2
