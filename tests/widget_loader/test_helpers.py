"""Tests covering helper utilities for widget loading."""

from pathlib import Path
import pytest
from mcp_chatkit_widget.widget_loader import _validate_widgets_dir


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
