"""Integration tests for bundled widget definitions."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from chatkit.widgets import Card
from mcp_chatkit_widget.schema_utils import json_schema_to_pydantic
from mcp_chatkit_widget.server import (
    _create_widget_tool_function,
    _sanitize_tool_name,
    _to_camel_case,
)
from mcp_chatkit_widget.widget_loader import discover_widgets, load_widget


CREATE_EVENT_INPUT: dict[str, Any] = {
    "date": {"name": "Friday", "number": "28"},
    "events": [
        {
            "id": "lunch",
            "title": "Lunch",
            "time": "12:00 - 12:45 PM",
            "color": "red-400",
            "isNew": False,
        },
        {
            "id": "q1-roadmap-review",
            "title": "Q1 roadmap review",
            "time": "1:00 - 2:00 PM",
            "color": "blue-400",
            "isNew": True,
        },
        {
            "id": "team-standup",
            "title": "Team standup",
            "time": "3:30 - 4:00 PM",
            "color": "red-400",
            "isNew": False,
        },
    ],
}


FLIGHT_TRACKER_INPUT: dict[str, Any] = {
    "number": "PA 845",
    "date": "Fri, Apr 25",
    "progress": "30%",
    "airline": {"name": "Pan Am", "logo": "/panam.png"},
    "departure": {"city": "San Francisco", "status": "On time", "time": "4:00 PM"},
    "arrival": {"city": "London", "status": "On time", "time": "10:25 AM +1"},
}


CASE_PARAMS: tuple[tuple[str, dict[str, Any]], ...] = (
    ("create_event_widget", CREATE_EVENT_INPUT),
    ("flight_tracker_widget", FLIGHT_TRACKER_INPUT),
)


@pytest.fixture
def widgets_dir() -> Path:
    """Return the path to the bundled widgets directory."""

    return Path(__file__).parent.parent / "mcp_chatkit_widget" / "widgets"


@pytest.fixture
def all_widgets(widgets_dir: Path) -> list[Any]:
    """Load all available widget definitions for smoke testing."""

    return discover_widgets(widgets_dir)


@pytest.fixture
def create_event_widget(widgets_dir: Path) -> Any:
    """Return the Create Event widget definition."""

    return load_widget(widgets_dir / "Create Event.widget")


@pytest.fixture
def flight_tracker_widget(widgets_dir: Path) -> Any:
    """Return the Flight Tracker widget definition."""

    return load_widget(widgets_dir / "Flight Tracker.widget")


def _build_model(widget: Any) -> type[Any]:
    camel_name = _to_camel_case(_sanitize_tool_name(widget.name))
    return json_schema_to_pydantic(widget.json_schema, f"{camel_name}Model")


def _create_tool(widget: Any, model: type[Any]) -> Any:
    return _create_widget_tool_function(widget.name, model, widget.template)


def _normalize_json(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: _normalize_json(v) for k, v in value.items() if v is not None}
    if isinstance(value, list):
        return [_normalize_json(item) for item in value]
    if isinstance(value, float):
        return round(value, 10)
    return value


def _sample_from_schema(schema: dict[str, Any]) -> Any:
    if "const" in schema:
        return schema["const"]
    if "enum" in schema and schema["enum"]:
        return schema["enum"][0]

    schema_type = schema.get("type")
    if schema_type == "object":
        properties = schema.get("properties", {})
        return {key: _sample_from_schema(defn) for key, defn in properties.items()}
    if schema_type == "array":
        item_schema = schema.get("items", {})
        if not item_schema:
            return []
        return [_sample_from_schema(item_schema)]
    if schema_type in {"number", "integer"}:
        return 0
    if schema_type == "boolean":
        return False
    return "sample"


def _assert_model_matches_schema(widget: Any, model: type[Any]) -> None:
    schema_props = widget.json_schema.get("properties", {})
    model_fields = model.model_fields
    assert set(model_fields) == set(schema_props)

    required = set(widget.json_schema.get("required", []))
    for field_name, field in model_fields.items():
        if field_name in required:
            assert field.is_required(), f"{field_name} should be required"
        else:
            assert not field.is_required(), f"{field_name} should be optional"


@pytest.mark.parametrize(("fixture_name", "input_data"), CASE_PARAMS)
def test_widget_schema_conversion(
    request: pytest.FixtureRequest, fixture_name: str, input_data: dict[str, Any]
) -> None:
    widget = request.getfixturevalue(fixture_name)
    model = _build_model(widget)

    _assert_model_matches_schema(widget, model)

    instance = model(**input_data)
    dumped = instance.model_dump()
    for key in input_data:
        assert key in dumped

    for field, schema_def in widget.json_schema.get("properties", {}).items():
        if schema_def.get("type") == "object":
            value = getattr(instance, field)
            assert hasattr(value, "model_dump"), f"Field {field} should be a model"


@pytest.mark.parametrize(("fixture_name", "input_data"), CASE_PARAMS)
def test_widget_tool_output_matches_preview(
    request: pytest.FixtureRequest, fixture_name: str, input_data: dict[str, Any]
) -> None:
    widget = request.getfixturevalue(fixture_name)
    model = _build_model(widget)
    tool = _create_tool(widget, model)

    result = tool(**input_data)
    assert isinstance(result, Card)

    actual = _normalize_json(result.model_dump(exclude_none=True))
    expected = _normalize_json(widget.output_json_preview)
    assert actual == expected


def test_all_widgets_execute_with_generated_data(all_widgets: list[Any]) -> None:
    assert all_widgets, "Expected bundled widgets to be discovered"

    for widget in all_widgets:
        model = _build_model(widget)
        tool = _create_tool(widget, model)
        sample_input = _sample_from_schema(widget.json_schema)
        result = tool(**sample_input)
        assert isinstance(result, Card)

