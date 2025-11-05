"""Unit tests for widget_loader module."""

import json
import os
import tempfile
from pathlib import Path
from typing import Any
import pytest
from mcp_chatkit_widget import widget_loader
from mcp_chatkit_widget.widget_loader import (
    WidgetDefinition,
    _build_search_paths,
    _validate_directory,
    discover_widgets,
    get_widget_by_name,
    load_widget,
)


@pytest.fixture
def temp_widgets_dir() -> Path:
    """Create a temporary directory for widget files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_widget_data() -> dict[str, Any]:
    """Return sample widget data for testing."""
    return {
        "name": "Test Widget",
        "version": "1.0",
        "jsonSchema": {
            "type": "object",
            "properties": {"title": {"type": "string"}},
        },
        "outputJsonPreview": {"type": "Card", "children": []},
        "template": '{"type": "Card", "children": []}',
        "encodedWidget": "base64encodeddata",
    }


@pytest.fixture
def create_widget_file(
    temp_widgets_dir: Path, sample_widget_data: dict[str, Any]
) -> Path:
    """Create a valid widget file in temp directory."""
    widget_path = temp_widgets_dir / "Test Widget.widget"
    with open(widget_path, "w") as f:
        json.dump(sample_widget_data, f)
    return widget_path


class TestValidateDirectory:
    """Tests for _validate_directory helper."""

    def test_file_path_non_strict_warns_and_returns_false(
        self, temp_widgets_dir: Path, capsys: Any
    ) -> None:
        """Ensure non-directory path prints warning when not strict (lines 46-47)."""
        file_path = temp_widgets_dir / "not_a_dir.txt"
        file_path.write_text("data")

        result = _validate_directory(file_path, strict=False)

        assert result is False
        captured = capsys.readouterr()
        assert "Custom widgets path is not a directory" in captured.out


class TestBuildSearchPaths:
    """Tests for _build_search_paths helper."""

    def test_skips_blank_custom_entries(
        self, temp_widgets_dir: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Ensure empty CUSTOM_WIDGETS_DIR entries are ignored (line 64)."""
        env_value = f"{temp_widgets_dir}{os.pathsep} {os.pathsep}"
        monkeypatch.setenv("CUSTOM_WIDGETS_DIR", env_value)

        paths = _build_search_paths(None)
        custom_paths = [path for path, strict in paths if not strict]

        assert custom_paths == [temp_widgets_dir]


class TestDiscoverWidgets:
    """Tests for discover_widgets function."""

    def test_nonexistent_directory_raises_error(self) -> None:
        """Test that nonexistent directory raises ValueError (line 54)."""
        nonexistent_path = Path("/nonexistent/path/to/widgets")
        with pytest.raises(ValueError, match="Widgets directory does not exist"):
            discover_widgets(nonexistent_path)

    def test_file_instead_of_directory_raises_error(
        self, temp_widgets_dir: Path, sample_widget_data: dict[str, Any]
    ) -> None:
        """Test that file path raises ValueError (line 57)."""
        # Create a file instead of a directory
        file_path = temp_widgets_dir / "not_a_dir.txt"
        with open(file_path, "w") as f:
            f.write("test")

        with pytest.raises(ValueError, match="Path is not a directory"):
            discover_widgets(file_path)

    def test_discover_valid_widgets(
        self, temp_widgets_dir: Path, sample_widget_data: dict[str, Any]
    ) -> None:
        """Test discovering valid widget files."""
        # Create multiple widget files
        for i in range(3):
            widget_path = temp_widgets_dir / f"Widget{i}.widget"
            data = sample_widget_data.copy()
            data["name"] = f"Widget {i}"
            with open(widget_path, "w") as f:
                json.dump(data, f)

        widgets = discover_widgets(temp_widgets_dir)

        assert len(widgets) == 3
        assert all(isinstance(w, WidgetDefinition) for w in widgets)

    def test_discover_with_invalid_widget(
        self, temp_widgets_dir: Path, sample_widget_data: dict[str, Any], capsys: Any
    ) -> None:
        """Test that invalid widgets are skipped with warning (lines 66-68)."""
        # Create valid widget
        valid_path = temp_widgets_dir / "Valid.widget"
        with open(valid_path, "w") as f:
            json.dump(sample_widget_data, f)

        # Create invalid widget (missing required fields)
        invalid_path = temp_widgets_dir / "Invalid.widget"
        with open(invalid_path, "w") as f:
            json.dump({"name": "Invalid"}, f)

        widgets = discover_widgets(temp_widgets_dir)

        # Should only discover valid widget
        assert len(widgets) == 1
        assert widgets[0].name == "Test Widget"

        # Check warning was printed
        captured = capsys.readouterr()
        assert "Warning: Failed to load widget" in captured.out
        assert "Invalid.widget" in captured.out

    def test_discover_with_malformed_json(
        self, temp_widgets_dir: Path, sample_widget_data: dict[str, Any], capsys: Any
    ) -> None:
        """Test handling of malformed JSON files (lines 66-68)."""
        # Create valid widget
        valid_path = temp_widgets_dir / "Valid.widget"
        with open(valid_path, "w") as f:
            json.dump(sample_widget_data, f)

        # Create malformed JSON file
        malformed_path = temp_widgets_dir / "Malformed.widget"
        with open(malformed_path, "w") as f:
            f.write("{invalid json content")

        widgets = discover_widgets(temp_widgets_dir)

        # Should only discover valid widget
        assert len(widgets) == 1

        # Check warning was printed
        captured = capsys.readouterr()
        assert "Warning: Failed to load widget" in captured.out

    def test_default_widgets_directory(self) -> None:
        """Test discovering widgets from default directory."""
        # This should use the package's widgets directory
        widgets = discover_widgets()

        # Should find at least the bundled widgets
        assert len(widgets) >= 2
        widget_names = [w.name for w in widgets]
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
        with open(custom_widget_path, "w") as f:
            json.dump(custom_data, f)

        monkeypatch.setenv("CUSTOM_WIDGETS_DIR", str(temp_widgets_dir))

        widgets = discover_widgets()
        widget_names = [w.name for w in widgets]

        assert "Custom Widget" in widget_names
        assert any(w.file_path == custom_widget_path for w in widgets)

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
        """Ensure duplicate widget files are only loaded once (line 98)."""
        primary_dir = temp_widgets_dir / "primary"
        alias_dir = temp_widgets_dir / "alias"
        primary_dir.mkdir()
        alias_dir.mkdir()

        widget_path = primary_dir / "Duplicate.widget"
        with open(widget_path, "w") as f:
            json.dump(sample_widget_data, f)

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
        """Test loading widget with missing required fields (line 93)."""
        widget_path = temp_widgets_dir / "Incomplete.widget"
        incomplete_data = {
            "name": "Incomplete Widget",
            "version": "1.0",
            # Missing: jsonSchema, outputJsonPreview, template
        }
        with open(widget_path, "w") as f:
            json.dump(incomplete_data, f)

        with pytest.raises(ValueError, match="Widget file missing required fields"):
            load_widget(widget_path)

    def test_load_widget_partial_missing_fields(self, temp_widgets_dir: Path) -> None:
        """Test loading widget with some required fields missing (line 93)."""
        widget_path = temp_widgets_dir / "Partial.widget"
        partial_data = {
            "name": "Partial Widget",
            "version": "1.0",
            "jsonSchema": {"type": "object"},
            # Missing: outputJsonPreview, template
        }
        with open(widget_path, "w") as f:
            json.dump(partial_data, f)

        with pytest.raises(ValueError) as exc_info:
            load_widget(widget_path)

        error_message = str(exc_info.value)
        assert "missing required fields" in error_message
        assert "outputJsonPreview" in error_message
        assert "template" in error_message

    def test_load_widget_with_invalid_json(self, temp_widgets_dir: Path) -> None:
        """Test loading widget with invalid JSON."""
        widget_path = temp_widgets_dir / "Invalid.widget"
        with open(widget_path, "w") as f:
            f.write("{not valid json}")

        with pytest.raises(json.JSONDecodeError):
            load_widget(widget_path)

    def test_load_widget_without_encoded_widget(self, temp_widgets_dir: Path) -> None:
        """Test loading widget without optional encodedWidget field."""
        widget_path = temp_widgets_dir / "NoEncoded.widget"
        data = {
            "name": "No Encoded Widget",
            "version": "1.0",
            "jsonSchema": {"type": "object"},
            "outputJsonPreview": {"type": "Card"},
            "template": "{}",
            # encodedWidget is optional
        }
        with open(widget_path, "w") as f:
            json.dump(data, f)

        widget = load_widget(widget_path)

        assert widget.encoded_widget is None


class TestGetWidgetByName:
    """Tests for get_widget_by_name function."""

    def test_find_existing_widget(
        self, temp_widgets_dir: Path, sample_widget_data: dict[str, Any]
    ) -> None:
        """Test finding an existing widget by name (lines 121-125)."""
        # Create multiple widgets
        for i in range(3):
            widget_path = temp_widgets_dir / f"Widget{i}.widget"
            data = sample_widget_data.copy()
            data["name"] = f"Widget {i}"
            with open(widget_path, "w") as f:
                json.dump(data, f)

        widget = get_widget_by_name("Widget 1", temp_widgets_dir)

        assert widget is not None
        assert widget.name == "Widget 1"

    def test_widget_not_found_returns_none(
        self, temp_widgets_dir: Path, sample_widget_data: dict[str, Any]
    ) -> None:
        """Test that non-existent widget returns None (line 125)."""
        # Create one widget
        widget_path = temp_widgets_dir / "Widget.widget"
        with open(widget_path, "w") as f:
            json.dump(sample_widget_data, f)

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
