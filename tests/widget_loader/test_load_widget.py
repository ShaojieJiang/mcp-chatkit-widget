"""Tests for load_widget."""

import json
from pathlib import Path
from typing import Any
import pytest
from mcp_chatkit_widget.widget_loader import WidgetDefinition, load_widget


class TestLoadWidget:
    """Tests for load_widget function."""

    def test_load_valid_widget(
        self, create_widget_file: Path, sample_widget_data: dict[str, Any]
    ) -> None:
        """Test loading a valid widget file."""
        widget = load_widget(create_widget_file)

        assert isinstance(widget, WidgetDefinition)
        assert widget.name == sample_widget_data["name"]
        assert widget.version == sample_widget_data["version"]
        assert widget.json_schema == sample_widget_data["jsonSchema"]
        assert widget.output_json_preview == sample_widget_data["outputJsonPreview"]
        assert widget.template == sample_widget_data["template"]
        assert widget.encoded_widget == sample_widget_data["encodedWidget"]
        assert widget.file_path == create_widget_file

    def test_load_widget_missing_required_fields(self, temp_widgets_dir: Path) -> None:
        """Test loading widget with missing required fields."""
        widget_path = temp_widgets_dir / "Incomplete.widget"
        incomplete_data: dict[str, Any] = {
            "name": "Incomplete Widget",
            "version": "1.0",
        }
        with open(widget_path, "w", encoding="utf-8") as file:
            json.dump(incomplete_data, file)

        with pytest.raises(ValueError, match="Widget file missing required fields"):
            load_widget(widget_path)

    def test_load_widget_partial_missing_fields(self, temp_widgets_dir: Path) -> None:
        """Test loading widget with some required fields missing."""
        widget_path = temp_widgets_dir / "Partial.widget"
        partial_data: dict[str, Any] = {
            "name": "Partial Widget",
            "version": "1.0",
            "jsonSchema": {"type": "object"},
        }
        with open(widget_path, "w", encoding="utf-8") as file:
            json.dump(partial_data, file)

        with pytest.raises(ValueError) as exc_info:
            load_widget(widget_path)

        error_message = str(exc_info.value)
        assert "missing required fields" in error_message
        assert "outputJsonPreview" in error_message
        assert "template" in error_message

    def test_load_widget_with_invalid_json(self, temp_widgets_dir: Path) -> None:
        """Test loading widget with invalid JSON."""
        widget_path = temp_widgets_dir / "Invalid.widget"
        with open(widget_path, "w", encoding="utf-8") as file:
            file.write("{not valid json}")

        with pytest.raises(json.JSONDecodeError):
            load_widget(widget_path)

    def test_load_widget_without_encoded_widget(self, temp_widgets_dir: Path) -> None:
        """Test loading widget without optional encodedWidget field."""
        widget_path = temp_widgets_dir / "NoEncoded.widget"
        data: dict[str, Any] = {
            "name": "No Encoded Widget",
            "version": "1.0",
            "jsonSchema": {"type": "object"},
            "outputJsonPreview": {"type": "Card"},
            "template": "{}",
        }
        with open(widget_path, "w", encoding="utf-8") as file:
            json.dump(data, file)

        widget = load_widget(widget_path)

        assert widget.encoded_widget is None
