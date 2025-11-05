"""Unit tests for schema_utils module."""

from typing import Any
import pytest
from chatkit.widgets import Card, Text, Title
from pydantic import BaseModel, ValidationError
from mcp_chatkit_widget.schema_utils import (
    _dict_to_widget_component,
    _to_title_case,
    create_widget_instance,
    json_schema_to_chatkit_widget,
    json_schema_to_pydantic,
)


class TestToTitleCase:
    """Tests for _to_title_case function."""

    def test_snake_case_conversion(self) -> None:
        """Test conversion of snake_case strings."""
        assert _to_title_case("flight_tracker") == "FlightTracker"
        assert _to_title_case("create_event") == "CreateEvent"
        assert _to_title_case("multi_word_name") == "MultiWordName"

    def test_single_word_conversion(self) -> None:
        """Test conversion of single word strings (line 28)."""
        assert _to_title_case("date") == "Date"
        assert _to_title_case("name") == "Name"
        assert _to_title_case("widget") == "Widget"


class TestJsonSchemaToPydantic:
    """Tests for json_schema_to_pydantic function."""

    def test_non_object_schema_raises_error(self) -> None:
        """Test that non-object schemas raise ValueError (line 65)."""
        schema = {"type": "string"}
        with pytest.raises(ValueError, match="Root schema must be of type 'object'"):
            json_schema_to_pydantic(schema)

    def test_optional_field_conversion(self) -> None:
        """Test optional fields are converted with None default (lines 99-100)."""
        schema = {
            "type": "object",
            "properties": {
                "required_field": {"type": "string"},
                "optional_field": {"type": "string"},
            },
            "required": ["required_field"],
        }
        model = json_schema_to_pydantic(schema, "TestModel")

        # Create instance with only required field
        instance = model(required_field="test")
        assert instance.required_field == "test"
        assert instance.optional_field is None

        # Verify optional field can be set
        instance2 = model(required_field="test", optional_field="optional")
        assert instance2.optional_field == "optional"

    def test_schema_title_in_config(self) -> None:
        """Test custom schema title is used in model config (lines 106-107)."""
        schema = {
            "type": "object",
            "properties": {"name": {"type": "string"}},
        }
        model = json_schema_to_pydantic(schema, "TestModel", schema_title="CustomTitle")

        # Verify model config has custom title
        assert model.model_config.get("title") == "CustomTitle"


class TestDictToWidgetComponent:
    """Tests for _dict_to_widget_component function."""

    def test_missing_type_raises_error(self) -> None:
        """Test component dict without type raises ValueError (line 155)."""
        component_dict: dict[str, Any] = {"value": "test"}
        with pytest.raises(
            ValueError, match="Component dictionary must have a 'type' field"
        ):
            _dict_to_widget_component(component_dict)

    def test_unknown_component_type_raises_error(self) -> None:
        """Test unknown component type raises ValueError (line 187)."""
        component_dict = {"type": "UnknownWidget"}
        with pytest.raises(ValueError, match="Unknown component type: UnknownWidget"):
            _dict_to_widget_component(component_dict)

    def test_valid_component_conversion(self) -> None:
        """Test successful conversion of valid component dict."""
        component_dict = {"type": "Text", "value": "Hello"}
        result = _dict_to_widget_component(component_dict)
        assert isinstance(result, Text)
        assert result.value == "Hello"

    def test_nested_children_conversion(self) -> None:
        """Test recursive conversion of nested children."""
        component_dict = {
            "type": "Card",
            "children": [
                {"type": "Title", "value": "Test Title"},
                {"type": "Text", "value": "Test content"},
            ],
        }
        result = _dict_to_widget_component(component_dict)
        assert isinstance(result, Card)
        assert len(result.children) == 2
        assert isinstance(result.children[0], Title)
        assert isinstance(result.children[1], Text)


class TestJsonSchemaToChatKitWidget:
    """Tests for json_schema_to_chatkit_widget function."""

    def test_converts_output_json_to_widget(self) -> None:
        """Test conversion of JSON structure to ChatKit widget."""
        output_json = {
            "type": "Card",
            "children": [{"type": "Text", "value": "Test"}],
        }
        result = json_schema_to_chatkit_widget(output_json, "TestWidget")
        assert isinstance(result, Card)
        assert len(result.children) == 1
        assert isinstance(result.children[0], Text)


class TestCreateWidgetInstance:
    """Tests for create_widget_instance function."""

    def test_create_valid_instance(self) -> None:
        """Test creating valid widget instance."""
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"},
            },
            "required": ["name"],
        }
        model = json_schema_to_pydantic(schema, "PersonModel")

        data = {"name": "Alice", "age": 30}
        instance = create_widget_instance(model, data)

        assert isinstance(instance, BaseModel)
        assert instance.name == "Alice"  # type: ignore[attr-defined]
        assert instance.age == 30  # type: ignore[attr-defined]

    def test_create_instance_with_invalid_data(self) -> None:
        """Test that invalid data raises ValidationError (line 225)."""
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"},
            },
            "required": ["name"],
        }
        model = json_schema_to_pydantic(schema, "PersonModel")

        # Missing required field
        data: dict[str, Any] = {"age": 30}
        with pytest.raises(ValidationError):
            create_widget_instance(model, data)

        # Wrong type for field
        data2 = {"name": "Alice", "age": "not an integer"}
        with pytest.raises(ValidationError):
            create_widget_instance(model, data2)


class TestComplexSchemaConversions:
    """Tests for complex schema scenarios."""

    def test_nested_object_with_optional_fields(self) -> None:
        """Test nested object schema with optional fields."""
        schema = {
            "type": "object",
            "properties": {
                "person": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "email": {"type": "string"},
                    },
                    "required": ["name"],
                },
            },
            "required": ["person"],
        }
        model = json_schema_to_pydantic(schema, "TestModel")

        # Create instance with nested optional field
        data = {"person": {"name": "Bob"}}
        instance = model(**data)
        assert instance.person.name == "Bob"  # type: ignore[attr-defined]
        assert instance.person.email is None  # type: ignore[attr-defined]

    def test_array_field_conversion(self) -> None:
        """Test array field conversion."""
        schema = {
            "type": "object",
            "properties": {
                "tags": {"type": "array"},
                "items": {"type": "string"},
            },
        }
        model = json_schema_to_pydantic(schema, "ArrayModel")

        data = {"tags": ["tag1", "tag2"], "items": "item1"}
        instance = model(**data)
        assert instance.tags == ["tag1", "tag2"]  # type: ignore[attr-defined]

    def test_array_items_type_mapping(self) -> None:
        """Test array items map to typed lists (lines 98-103)."""
        schema = {
            "type": "object",
            "properties": {
                "scores": {
                    "type": "array",
                    "items": {"type": "integer"},
                }
            },
            "required": ["scores"],
        }

        model = json_schema_to_pydantic(schema, "ScoreModel")

        instance = model(scores=[1, 2, 3])
        assert instance.scores == [1, 2, 3]  # type: ignore[attr-defined]

    def test_nested_array_falls_back_to_list_any(self) -> None:
        """Test nested arrays default to list[Any] (line 100)."""
        schema = {
            "type": "object",
            "properties": {
                "matrix": {
                    "type": "array",
                    "items": {
                        "type": "array",
                        "items": {"type": "integer"},
                    },
                }
            },
            "required": ["matrix"],
        }

        model = json_schema_to_pydantic(schema, "MatrixModel")

        instance = model(matrix=[[1, 2], [3, 4]])
        assert instance.matrix == [[1, 2], [3, 4]]  # type: ignore[attr-defined]

    def test_various_widget_types(self) -> None:
        """Test conversion for various widget component types."""
        # Test a sample of widget types with their required fields
        widget_configs = [
            ("Card", {"children": []}),
            ("Row", {"children": []}),
            ("Col", {"children": []}),
            ("Box", {"children": []}),
            ("Text", {"value": "test"}),
            ("Title", {"value": "test"}),
            ("Caption", {"value": "test"}),
            ("Image", {"src": "test.jpg"}),
            ("Icon", {"name": "star"}),
            ("Divider", {}),
            ("Spacer", {}),
            ("Markdown", {"value": "test"}),
        ]

        for widget_type, props in widget_configs:
            component_dict = {"type": widget_type, **props}
            result = _dict_to_widget_component(component_dict)
            assert result is not None
            assert result.type == widget_type
