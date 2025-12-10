"""Shared fixtures for widget integration tests."""

from __future__ import annotations
from pathlib import Path
from typing import Any
import pytest
from mcp_chatkit_widget.widget_loader import discover_widgets, load_widget


@pytest.fixture
def widgets_dir() -> Path:
    """Return the path to the widgets directory."""
    root_dir = Path(__file__).resolve().parents[2]
    return root_dir / "examples" / "widgets"


@pytest.fixture
def all_widgets(widgets_dir: Path) -> list[Any]:
    """Load all widget definitions from the widgets directory."""
    return discover_widgets(widgets_dir)


@pytest.fixture
def create_event_widget(widgets_dir: Path) -> Any:
    """Load the Create Event widget definition."""
    widget_path = widgets_dir / "Create Event.widget"
    return load_widget(widget_path)


@pytest.fixture
def flight_tracker_widget(widgets_dir: Path) -> Any:
    """Load the Flight Tracker widget definition."""
    widget_path = widgets_dir / "Flight Tracker.widget"
    return load_widget(widget_path)
