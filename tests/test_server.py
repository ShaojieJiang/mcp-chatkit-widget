"""Unit tests for server module."""

import inspect
import json
from pathlib import Path
from typing import Any
import pytest
from chatkit.widgets import WidgetComponentBase
from mcp_chatkit_widget.server import (
    DEFAULT_WIDGETS_DIR,
    _create_widget_tool_function,
    _sanitize_tool_name,
    _to_camel_case,
    register_widget_tools,
    server,
)
from mcp_chatkit_widget.widget_loader import WidgetDefinition


register_widget_tools(DEFAULT_WIDGETS_DIR)


@pytest.fixture
def simple_schema() -> dict[str, Any]:
    """Return a simple JSON schema for testing."""
    return {
        "type": "object",
        "properties": {
            "title": {"type": "string"},
            "description": {"type": "string"},
        },
        "required": ["title"],
    }


@pytest.fixture
def simple_template() -> str:
    """Return a simple Jinja2 template for testing."""
    return """
{
    "type": "Card",
    "children": [
        {"type": "Title", "value": "{{ title }}"},
        {"type": "Text", "value": "{{ description }}"}
    ]
}
""".strip()


@pytest.fixture
def simple_widget_file(
    tmp_path: Path, simple_schema: dict[str, Any], simple_template: str
) -> Path:
    """Write a simple .widget file to disk."""
    preview = {"type": "Card", "children": []}
    payload = {
        "version": "1.0",
        "name": "Test Widget",
        "template": simple_template,
        "jsonSchema": simple_schema,
        "outputJsonPreview": preview,
    }
    path = tmp_path / "test.widget"
    path.write_text(json.dumps(payload))
    return path


@pytest.fixture
def simple_widget_definition(
    simple_widget_file: Path,
    simple_schema: dict[str, Any],
    simple_template: str,
) -> WidgetDefinition:
    """Return a WidgetDefinition backed by a temporary file."""
    return WidgetDefinition(
        name="Test Widget",
        version="1.0",
        json_schema=simple_schema,
        output_json_preview={"type": "Card", "children": []},
        template=simple_template,
        encoded_widget=None,
        file_path=simple_widget_file,
    )


class TestSanitizeToolName:
    """Tests for _sanitize_tool_name function."""

    def test_normal_name_conversion(self) -> None:
        assert _sanitize_tool_name("Flight Tracker") == "flight_tracker"
        assert _sanitize_tool_name("Create Event") == "create_event"

    def test_name_starting_with_digit(self) -> None:
        assert _sanitize_tool_name("123 Widget") == "_123_widget"
        assert _sanitize_tool_name("9 Grid") == "_9_grid"

    def test_special_characters_removal(self) -> None:
        assert _sanitize_tool_name("Widget-Name!") == "widget_name"
        assert _sanitize_tool_name("Test@Widget#") == "testwidget"

    def test_multiple_spaces_and_hyphens(self) -> None:
        assert _sanitize_tool_name("Multi  Space  Name") == "multi__space__name"
        assert _sanitize_tool_name("Dash-Separated-Name") == "dash_separated_name"


class TestToCamelCase:
    """Tests for _to_camel_case function."""

    def test_snake_case_to_camel_case(self) -> None:
        assert _to_camel_case("flight_tracker") == "FlightTracker"
        assert _to_camel_case("create_event") == "CreateEvent"
        assert _to_camel_case("single") == "Single"


class TestCreateWidgetToolFunction:
    """Tests for _create_widget_tool_function."""

    def test_function_name_and_signature(
        self, simple_widget_definition: WidgetDefinition
    ) -> None:
        tool_func = _create_widget_tool_function(simple_widget_definition)
        assert tool_func.__name__ == "TestWidget"
        sig = inspect.signature(tool_func)
        assert "title" in sig.parameters
        assert "description" in sig.parameters
        assert sig.return_annotation == WidgetComponentBase

    def test_function_docstring(
        self, simple_widget_definition: WidgetDefinition
    ) -> None:
        tool_func = _create_widget_tool_function(simple_widget_definition)
        assert tool_func.__doc__ is not None
        assert "Test Widget" in tool_func.__doc__
        assert "Generate a" in tool_func.__doc__

    def test_function_execution(
        self, simple_widget_definition: WidgetDefinition
    ) -> None:
        tool_func = _create_widget_tool_function(simple_widget_definition)
        result = tool_func(title="Test Title", description="Test Description")
        assert isinstance(result, WidgetComponentBase)
        assert result.type == "Card"

    def test_function_with_optional_parameters(
        self, simple_widget_definition: WidgetDefinition
    ) -> None:
        tool_func = _create_widget_tool_function(simple_widget_definition)
        result = tool_func(title="Test Title")
        assert isinstance(result, WidgetComponentBase)
        assert result.type == "Card"
        sig = inspect.signature(tool_func)
        assert sig.parameters["description"].default is None

    def test_template_compiled_once(
        self,
        simple_widget_definition: WidgetDefinition,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        import mcp_chatkit_widget.rendering as rendering_module

        call_count = 0
        original_from_file = rendering_module.WidgetTemplate.from_file.__func__

        def counting_from_file(cls: type[Any], file_path: str) -> Any:
            nonlocal call_count
            call_count += 1
            return original_from_file(cls, file_path)

        monkeypatch.setattr(
            rendering_module.WidgetTemplate,
            "from_file",
            classmethod(counting_from_file),
        )

        tool_func = _create_widget_tool_function(simple_widget_definition)
        assert call_count == 0

        tool_func(title="Title One", description="Desc")
        tool_func(title="Title Two")

        assert call_count == 1

    def test_function_annotations(
        self, simple_widget_definition: WidgetDefinition
    ) -> None:
        tool_func = _create_widget_tool_function(simple_widget_definition)
        annotations = getattr(tool_func, "__annotations__", {})
        assert "return" in annotations
        assert annotations["return"] == WidgetComponentBase


class TestRegisterWidgetTools:
    """Tests for register_widget_tools function."""

    def test_register_widget_tools_runs(self) -> None:
        server._tool_manager._tools.clear()
        register_widget_tools(DEFAULT_WIDGETS_DIR)
        assert hasattr(server, "_tool_manager")
        assert len(server._tool_manager._tools) >= 2

    def test_registered_tools_have_correct_names(self) -> None:
        tool_names = list(server._tool_manager._tools.keys())
        assert "flight_tracker" in tool_names
        assert "create_event" in tool_names


class TestServerInstance:
    """Tests for the server instance."""

    def test_server_has_correct_name(self) -> None:
        assert server.name == "mcp-chatkit-widget"

    def test_server_is_fastmcp_instance(self) -> None:
        from fastmcp import FastMCP

        assert isinstance(server, FastMCP)
