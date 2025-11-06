"""Tests for discover_widgets."""

import json
import os
from pathlib import Path
from typing import Any
import pytest
from mcp_chatkit_widget import widget_loader
from mcp_chatkit_widget.widget_loader import WidgetDefinition, discover_widgets


class TestDiscoverWidgets:
    """Tests for discover_widgets function."""

    def test_nonexistent_directory_raises_error(self) -> None:
        """Test that nonexistent directory raises ValueError."""
        nonexistent_path = Path("/nonexistent/path/to/widgets")
        with pytest.raises(ValueError, match="Widgets directory does not exist"):
            discover_widgets(nonexistent_path)

    def test_file_instead_of_directory_raises_error(
        self, temp_widgets_dir: Path, sample_widget_data: dict[str, Any]
    ) -> None:
        """Test that file path raises ValueError."""
        file_path = temp_widgets_dir / "not_a_dir.txt"
        with open(file_path, "w", encoding="utf-8") as file:
            file.write("test")

        with pytest.raises(ValueError, match="Path is not a directory"):
            discover_widgets(file_path)

    def test_discover_valid_widgets(
        self, temp_widgets_dir: Path, sample_widget_data: dict[str, Any]
    ) -> None:
        """Test discovering valid widget files."""
        for index in range(3):
            widget_path = temp_widgets_dir / f"Widget{index}.widget"
            data = sample_widget_data.copy()
            data["name"] = f"Widget {index}"
            with open(widget_path, "w", encoding="utf-8") as file:
                json.dump(data, file)

        widgets = discover_widgets(temp_widgets_dir)

        assert len(widgets) == 3
        assert all(isinstance(widget, WidgetDefinition) for widget in widgets)

    def test_discover_with_invalid_widget(
        self, temp_widgets_dir: Path, sample_widget_data: dict[str, Any], capsys: Any
    ) -> None:
        """Test that invalid widgets are skipped with warning."""
        valid_path = temp_widgets_dir / "Valid.widget"
        with open(valid_path, "w", encoding="utf-8") as file:
            json.dump(sample_widget_data, file)

        invalid_path = temp_widgets_dir / "Invalid.widget"
        with open(invalid_path, "w", encoding="utf-8") as file:
            json.dump({"name": "Invalid"}, file)

        widgets = discover_widgets(temp_widgets_dir)

        assert len(widgets) == 1
        assert widgets[0].name == "Test Widget"

        captured = capsys.readouterr()
        assert "Warning: Failed to load widget" in captured.out
        assert "Invalid.widget" in captured.out

    def test_discover_with_malformed_json(
        self, temp_widgets_dir: Path, sample_widget_data: dict[str, Any], capsys: Any
    ) -> None:
        """Test handling of malformed JSON files."""
        valid_path = temp_widgets_dir / "Valid.widget"
        with open(valid_path, "w", encoding="utf-8") as file:
            json.dump(sample_widget_data, file)

        malformed_path = temp_widgets_dir / "Malformed.widget"
        with open(malformed_path, "w", encoding="utf-8") as file:
            file.write("{invalid json content")

        widgets = discover_widgets(temp_widgets_dir)

        assert len(widgets) == 1

        captured = capsys.readouterr()
        assert "Warning: Failed to load widget" in captured.out

    def test_default_widgets_directory(self) -> None:
        """Test discovering widgets from default directory."""
        widgets = discover_widgets()

        assert len(widgets) >= 2
        widget_names = [widget.name for widget in widgets]
        assert "Flight Tracker" in widget_names
        assert "Create Event" in widget_names

    def test_custom_widgets_directory_is_discovered(
        self,
        temp_widgets_dir: Path,
        sample_widget_data: dict[str, Any],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test that widgets from CUSTOM_WIDGETS_DIR are discovered."""
        custom_widget_path = temp_widgets_dir / "Custom.widget"
        custom_data = sample_widget_data.copy()
        custom_data["name"] = "Custom Widget"
        with open(custom_widget_path, "w", encoding="utf-8") as file:
            json.dump(custom_data, file)

        monkeypatch.setenv("CUSTOM_WIDGETS_DIR", str(temp_widgets_dir))

        widgets = discover_widgets()
        widget_names = [widget.name for widget in widgets]

        assert "Custom Widget" in widget_names
        assert any(widget.file_path == custom_widget_path for widget in widgets)

    def test_invalid_custom_widgets_directory_is_ignored(
        self, monkeypatch: pytest.MonkeyPatch, capsys: Any
    ) -> None:
        """Test that an invalid CUSTOM_WIDGETS_DIR is ignored with warning."""
        monkeypatch.setenv("CUSTOM_WIDGETS_DIR", "/path/does/not/exist")

        widgets = discover_widgets()

        assert len(widgets) >= 2
        captured = capsys.readouterr()
        assert "Custom widgets directory does not exist" in captured.out

    def test_duplicate_widget_files_are_skipped(
        self,
        temp_widgets_dir: Path,
        sample_widget_data: dict[str, Any],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Ensure duplicate widget files are only loaded once."""
        primary_dir = temp_widgets_dir / "primary"
        alias_dir = temp_widgets_dir / "alias"
        primary_dir.mkdir()
        alias_dir.mkdir()

        widget_path = primary_dir / "Duplicate.widget"
        with open(widget_path, "w", encoding="utf-8") as file:
            json.dump(sample_widget_data, file)

        symlink_path = alias_dir / "Duplicate.widget"
        os.symlink(widget_path, symlink_path)

        monkeypatch.setattr(
            widget_loader,
            "_build_search_paths",
            lambda widgets_dir: [(primary_dir, True), (alias_dir, False)],
        )

        widgets = discover_widgets()

        assert len(widgets) == 1
        assert widgets[0].file_path == widget_path
