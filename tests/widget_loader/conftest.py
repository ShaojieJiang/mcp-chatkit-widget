"""Shared fixtures for widget_loader tests."""

import json
import tempfile
from pathlib import Path
from typing import Any
import pytest


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
    with open(widget_path, "w") as file:
        json.dump(sample_widget_data, file)
    return widget_path
