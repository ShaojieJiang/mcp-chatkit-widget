"""Tests for widget discovery helpers."""

import json
from pathlib import Path
from typing import Any
import pytest
from mcp_chatkit_widget.widget_loader import (
    WidgetDefinition,
    discover_widgets,
    load_widgets,
)


class TestLoadWidgets:
    """Tests for load_widgets and discover_widgets helpers."""

    def test_discover_widgets_requires_widgets_dir(self) -> None:
        """Calling discover_widgets without a path should raise a clear error."""
        with pytest.raises(ValueError, match="widgets_dir argument is required"):
            discover_widgets()  # type: ignore[arg-type]

    def test_load_widgets_returns_widget_definitions(
        self, temp_widgets_dir: Path, sample_widget_data: dict[str, Any]
    ) -> None:
        """Valid .widget files are returned as WidgetDefinition instances."""
        for index in range(3):
            widget_path = temp_widgets_dir / f"Widget{index}.widget"
            data = sample_widget_data.copy()
            data["name"] = f"Widget {index}"
            with open(widget_path, "w", encoding="utf-8") as file:
                json.dump(data, file)

        widgets = load_widgets(temp_widgets_dir)

        assert len(widgets) == 3
        assert all(isinstance(widget, WidgetDefinition) for widget in widgets)

    def test_load_widgets_includes_nested_widget_files(
        self, temp_widgets_dir: Path, sample_widget_data: dict[str, Any]
    ) -> None:
        """Widgets located inside subdirectories are also discovered."""
        nested_dir = temp_widgets_dir / "nested"
        nested_dir.mkdir()
        widget_path = nested_dir / "Nested.widget"
        data = sample_widget_data.copy()
        data["name"] = "Nested Widget"
        with open(widget_path, "w", encoding="utf-8") as file:
            json.dump(data, file)

        widgets = load_widgets(temp_widgets_dir)

        assert len(widgets) == 1
        assert widgets[0].name == "Nested Widget"

    def test_load_widgets_rejects_missing_template(
        self, temp_widgets_dir: Path
    ) -> None:
        """Widgets that omit the template field cause discovery to fail."""
        widget_path = temp_widgets_dir / "Broken.widget"
        bad_data = {
            "name": "Broken",
            "version": "1.0",
            "jsonSchema": {},
            "outputJsonPreview": {},
        }
        with open(widget_path, "w", encoding="utf-8") as file:
            json.dump(bad_data, file)

        with pytest.raises(ValueError, match="missing required fields"):
            load_widgets(temp_widgets_dir)
