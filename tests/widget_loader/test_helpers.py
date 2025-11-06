"""Tests covering helper utilities for widget loading."""

import os
from pathlib import Path
from typing import Any
import pytest
from mcp_chatkit_widget.widget_loader import _build_search_paths, _validate_directory


class TestValidateDirectory:
    """Tests for _validate_directory helper."""

    def test_file_path_non_strict_warns_and_returns_false(
        self, temp_widgets_dir: Path, capsys: Any
    ) -> None:
        """Ensure non-directory path prints warning when not strict."""
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
        """Ensure empty CUSTOM_WIDGETS_DIR entries are ignored."""
        env_value = f"{temp_widgets_dir}{os.pathsep} {os.pathsep}"
        monkeypatch.setenv("CUSTOM_WIDGETS_DIR", env_value)

        paths = _build_search_paths(None)
        custom_paths = [path for path, strict in paths if not strict]

        assert custom_paths == [temp_widgets_dir]
