"""Tests for the WidgetDefinition dataclass."""

from pathlib import Path
from mcp_chatkit_widget.widget_loader import WidgetDefinition


class TestWidgetDefinition:
    """Tests for WidgetDefinition dataclass."""

    def test_widget_definition_creation(self) -> None:
        """Test creating WidgetDefinition instance."""
        widget_def = WidgetDefinition(
            name="Test",
            version="1.0",
            json_schema={"type": "object"},
            output_json_preview={"type": "Card"},
            template="{}",
            encoded_widget="base64data",
            file_path=Path("/test/path.widget"),
        )

        assert widget_def.name == "Test"
        assert widget_def.version == "1.0"
        assert widget_def.json_schema == {"type": "object"}
        assert widget_def.output_json_preview == {"type": "Card"}
        assert widget_def.template == "{}"
        assert widget_def.encoded_widget == "base64data"
        assert widget_def.file_path == Path("/test/path.widget")

    def test_widget_definition_with_none_encoded_widget(self) -> None:
        """Test WidgetDefinition with None encoded_widget."""
        widget_def = WidgetDefinition(
            name="Test",
            version="1.0",
            json_schema={"type": "object"},
            output_json_preview={"type": "Card"},
            template="{}",
            encoded_widget=None,
            file_path=Path("/test/path.widget"),
        )

        assert widget_def.encoded_widget is None
