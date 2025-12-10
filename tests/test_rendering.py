"""Tests for the rendering helpers."""

from __future__ import annotations
from pathlib import Path
from typing import Any
import pytest
from chatkit.widgets import DynamicWidgetRoot
from mcp_chatkit_widget.rendering import render_widget_definition
from mcp_chatkit_widget.widget_loader import WidgetDefinition, load_widget
from tests.widget_integration.input_extractors import extract_input_data_from_preview
from tests.widget_integration.tooling import deep_compare


@pytest.fixture
def create_event_widget() -> WidgetDefinition:
    """Load the Create Event widget definition from the curated widgets folder."""
    repo_root = Path(__file__).resolve().parents[1]
    widget_path = repo_root / "mcp_chatkit_widget" / "widgets" / "Create Event.widget"
    return load_widget(widget_path)


def test_render_widget_definition_matches_preview(create_event_widget: Any) -> None:
    """Ensure the renderer reproduces the preview payload for a widget."""
    input_data = extract_input_data_from_preview(
        create_event_widget.json_schema,
        create_event_widget.output_json_preview,
    )

    result = render_widget_definition(create_event_widget, **input_data)

    assert isinstance(result, DynamicWidgetRoot)
    result_dict = result.model_dump(exclude_none=True)
    match = deep_compare(result_dict, create_event_widget.output_json_preview)
    assert match, "Rendered widget does not match the preview payload"
