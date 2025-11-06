"""Unit tests for `_dict_to_widget_component`."""

from typing import Any
import pytest
from chatkit.widgets import Card, Text, Title
from mcp_chatkit_widget.schema_utils import _dict_to_widget_component


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
