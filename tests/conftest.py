"""Shared fixtures for widget integration tests."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from mcp_chatkit_widget.widget_loader import discover_widgets, load_widget


@pytest.fixture
def widgets_dir() -> Path:
    """Return the directory containing bundled widget definitions."""
    return (Path(__file__).parent / ".." / "mcp_chatkit_widget" / "widgets").resolve()


@pytest.fixture
def all_widgets(widgets_dir: Path) -> list[Any]:
    """Load all widget definitions from the widgets directory."""
    return discover_widgets(widgets_dir)


@pytest.fixture
def create_event_widget(widgets_dir: Path) -> Any:
    """Return the Create Event widget definition."""
    return load_widget(widgets_dir / "Create Event.widget")


@pytest.fixture
def flight_tracker_widget(widgets_dir: Path) -> Any:
    """Return the Flight Tracker widget definition."""
    return load_widget(widgets_dir / "Flight Tracker.widget")
