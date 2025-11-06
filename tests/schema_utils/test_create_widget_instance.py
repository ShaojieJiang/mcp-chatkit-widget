"""Unit tests for `create_widget_instance`."""

from typing import Any
import pytest
from pydantic import BaseModel, ValidationError
from mcp_chatkit_widget.schema_utils import (
    create_widget_instance,
    json_schema_to_pydantic,
)


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
