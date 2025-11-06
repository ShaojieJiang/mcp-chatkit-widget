"""Unit tests for `json_schema_to_chatkit_widget`."""

from chatkit.widgets import Card, Text
from mcp_chatkit_widget.schema_utils import json_schema_to_chatkit_widget


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
