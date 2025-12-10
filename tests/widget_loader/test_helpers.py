"""Tests covering helper utilities for widget loading."""

import logging
from pathlib import Path
import pytest
from mcp_chatkit_widget.widget_loader import (
    _collect_widget_files,
    _validate_widgets_dir,
)


class TestValidateWidgetsDir:
    """Tests for _validate_widgets_dir helper."""

    def test_missing_directory_raises_value_error(self) -> None:
        """The helper errors when the path does not exist."""
        missing_dir = Path("/tmp/this/does/not/exist")

        with pytest.raises(ValueError, match="Widgets directory does not exist"):
            _validate_widgets_dir(missing_dir)

    def test_file_path_raises_value_error(self, temp_widgets_dir: Path) -> None:
        """Passing a file path raises a helpful error."""
        file_path = temp_widgets_dir / "file.txt"
        file_path.write_text("content")

        with pytest.raises(ValueError, match="Widgets directory is not a directory"):
            _validate_widgets_dir(file_path)

    def test_none_path_raises_value_error(self) -> None:
        """None is rejected as an invalid widgets directory."""
        with pytest.raises(ValueError, match="widgets_dir argument is required"):
            _validate_widgets_dir(None)


def test_collect_skips_non_widget_directories(temp_widgets_dir: Path) -> None:
    """Ignore directory entries that match the widget pattern."""
    (temp_widgets_dir / "subdir.widget").mkdir()
    assert _collect_widget_files(temp_widgets_dir) == []


def test_collect_skips_unresolvable_widget(
    temp_widgets_dir: Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Widgets that cannot be resolved are skipped with a warning."""
    caplog.set_level(logging.WARNING, logger="mcp_chatkit_widget.widget_loader")
    widget_path = temp_widgets_dir / "bad.widget"
    widget_path.write_text("{}")

    original_resolve = Path.resolve

    def fake_resolve(self, *args, **kwargs):
        if self == widget_path:
            raise OSError("failure")
        return original_resolve(self, *args, **kwargs)

    monkeypatch.setattr(Path, "resolve", fake_resolve)

    assert _collect_widget_files(temp_widgets_dir) == []
    assert "Skipping widget" in caplog.text
    assert "could not be resolved" in caplog.text
    assert "bad.widget" in caplog.text


def test_collect_skips_widgets_outside_directory(
    temp_widgets_dir: Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Widgets whose resolved path is outside the base directory are ignored."""
    caplog.set_level(logging.WARNING, logger="mcp_chatkit_widget.widget_loader")
    widget_path = temp_widgets_dir / "outside.widget"
    widget_path.write_text("{}")

    resolved_widget_path = widget_path.resolve()
    original_relative_to = Path.relative_to

    def fake_relative_to(self, other, *args, **kwargs):
        if self == resolved_widget_path:
            raise ValueError("outside")
        return original_relative_to(self, other, *args, **kwargs)

    monkeypatch.setattr(Path, "relative_to", fake_relative_to)

    assert _collect_widget_files(temp_widgets_dir) == []
    assert "Skipping widget" in caplog.text
    assert "outside the widgets directory" in caplog.text
    assert "outside.widget" in caplog.text


def test_collect_deduplicates_same_resolved_path(
    temp_widgets_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Only the first widget that resolves to a given path is returned."""
    first_widget = temp_widgets_dir / "first.widget"
    second_widget = temp_widgets_dir / "second.widget"
    first_widget.write_text("{}")
    second_widget.write_text("{}")

    original_resolve = Path.resolve

    def fake_resolve(self, *args, **kwargs):
        if self == second_widget:
            return original_resolve(first_widget, *args, **kwargs)
        return original_resolve(self, *args, **kwargs)

    monkeypatch.setattr(Path, "resolve", fake_resolve)

    collected = _collect_widget_files(temp_widgets_dir)
    assert collected == [first_widget]
