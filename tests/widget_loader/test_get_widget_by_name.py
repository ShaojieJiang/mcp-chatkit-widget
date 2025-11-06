"""Tests for get_widget_by_name."""

import json
from pathlib import Path
from typing import Any
from mcp_chatkit_widget.widget_loader import get_widget_by_name


class TestGetWidgetByName:
    """Tests for get_widget_by_name function."""

    def test_find_existing_widget(
        self, temp_widgets_dir: Path, sample_widget_data: dict[str, Any]
    ) -> None:
        """Test finding an existing widget by name."""
        for index in range(3):
            widget_path = temp_widgets_dir / f"Widget{index}.widget"
            data = sample_widget_data.copy()
            data["name"] = f"Widget {index}"
            with open(widget_path, "w", encoding="utf-8") as file:
                json.dump(data, file)

        widget = get_widget_by_name("Widget 1", temp_widgets_dir)

        assert widget is not None
        assert widget.name == "Widget 1"

    def test_widget_not_found_returns_none(
        self, temp_widgets_dir: Path, sample_widget_data: dict[str, Any]
    ) -> None:
        """Test that non-existent widget returns None."""
        widget_path = temp_widgets_dir / "Widget.widget"
        with open(widget_path, "w", encoding="utf-8") as file:
            json.dump(sample_widget_data, file)

        widget = get_widget_by_name("Nonexistent Widget", temp_widgets_dir)

        assert widget is None

    def test_get_widget_from_default_directory(self) -> None:
        """Test getting widget from default directory."""
        widget = get_widget_by_name("Flight Tracker")

        assert widget is not None
        assert widget.name == "Flight Tracker"

    def test_get_nonexistent_widget_from_default_directory(self) -> None:
        """Test getting non-existent widget from default directory."""
        widget = get_widget_by_name("This Widget Does Not Exist")

        assert widget is None
