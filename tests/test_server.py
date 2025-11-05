"""Unit tests for server module."""

import inspect
from typing import Any
import pytest
from chatkit.widgets import WidgetComponentBase
from mcp_chatkit_widget.schema_utils import json_schema_to_pydantic
from mcp_chatkit_widget.server import (
    _create_widget_tool_function,
    _sanitize_tool_name,
    _to_camel_case,
    server,
)


class TestSanitizeToolName:
    """Tests for _sanitize_tool_name function."""

    def test_normal_name_conversion(self) -> None:
        """Test conversion of normal widget names."""
        assert _sanitize_tool_name("Flight Tracker") == "flight_tracker"
        assert _sanitize_tool_name("Create Event") == "create_event"

    def test_name_starting_with_digit(self) -> None:
        """Test names starting with digits get prefixed (line 35)."""
        assert _sanitize_tool_name("123 Widget") == "_123_widget"
        assert _sanitize_tool_name("9 Grid") == "_9_grid"

    def test_special_characters_removal(self) -> None:
        """Test removal of special characters."""
        assert _sanitize_tool_name("Widget-Name!") == "widget_name"
        assert _sanitize_tool_name("Test@Widget#") == "testwidget"

    def test_multiple_spaces_and_hyphens(self) -> None:
        """Test handling of multiple spaces and hyphens."""
        assert _sanitize_tool_name("Multi  Space  Name") == "multi__space__name"
        assert _sanitize_tool_name("Dash-Separated-Name") == "dash_separated_name"


class TestToCamelCase:
    """Tests for _to_camel_case function."""

    def test_snake_case_to_camel_case(self) -> None:
        """Test conversion from snake_case to CamelCase."""
        assert _to_camel_case("flight_tracker") == "FlightTracker"
        assert _to_camel_case("create_event") == "CreateEvent"
        assert _to_camel_case("single") == "Single"


class TestCreateWidgetToolFunction:
    """Tests for _create_widget_tool_function."""

    @pytest.fixture
    def simple_schema(self) -> dict[str, Any]:
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
    def simple_template(self) -> str:
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

    def test_function_name_and_signature(
        self, simple_schema: dict[str, Any], simple_template: str
    ) -> None:
        """Test that function has correct name and signature."""
        pydantic_model = json_schema_to_pydantic(simple_schema, "TestModel")
        tool_func = _create_widget_tool_function(
            "Test Widget", pydantic_model, simple_template
        )

        # Check function name is in CamelCase
        assert tool_func.__name__ == "TestWidget"

        # Check signature has correct parameters
        sig = inspect.signature(tool_func)
        assert "title" in sig.parameters
        assert "description" in sig.parameters

        # Check return annotation
        assert sig.return_annotation == WidgetComponentBase

    def test_function_docstring(
        self, simple_schema: dict[str, Any], simple_template: str
    ) -> None:
        """Test that function has appropriate docstring."""
        pydantic_model = json_schema_to_pydantic(simple_schema, "TestModel")
        tool_func = _create_widget_tool_function(
            "Test Widget", pydantic_model, simple_template
        )

        assert tool_func.__doc__ is not None
        assert "Test Widget" in tool_func.__doc__
        assert "Generate a" in tool_func.__doc__

    def test_function_execution(
        self, simple_schema: dict[str, Any], simple_template: str
    ) -> None:
        """Test that generated function executes correctly."""
        pydantic_model = json_schema_to_pydantic(simple_schema, "TestModel")
        tool_func = _create_widget_tool_function(
            "Test Widget", pydantic_model, simple_template
        )

        result = tool_func(title="Test Title", description="Test Description")

        assert isinstance(result, WidgetComponentBase)
        assert result.type == "Card"

    def test_function_with_optional_parameters(
        self, simple_schema: dict[str, Any], simple_template: str
    ) -> None:
        """Test function with optional parameters (line 107)."""
        pydantic_model = json_schema_to_pydantic(simple_schema, "TestModel")
        tool_func = _create_widget_tool_function(
            "Test Widget", pydantic_model, simple_template
        )

        # Call with only required parameter
        result = tool_func(title="Test Title")

        assert isinstance(result, WidgetComponentBase)
        assert result.type == "Card"

        # Verify optional parameter has correct default in signature
        sig = inspect.signature(tool_func)
        assert sig.parameters["description"].default is None

    def test_template_compiled_once(
        self,
        simple_schema: dict[str, Any],
        simple_template: str,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Ensure template compilation happens only once per widget."""
        import sys

        call_count = 0
        original_template = sys.modules["mcp_chatkit_widget.server"].Template

        def counting_template(*args: Any, **kwargs: Any) -> Any:
            nonlocal call_count
            call_count += 1
            return original_template(*args, **kwargs)

        # Get the actual module from sys.modules
        server_module = sys.modules["mcp_chatkit_widget.server"]
        monkeypatch.setattr(server_module, "Template", counting_template)

        pydantic_model = json_schema_to_pydantic(simple_schema, "TestModel")
        tool_func = _create_widget_tool_function(
            "Test Widget", pydantic_model, simple_template
        )

        assert call_count == 1

        tool_func(title="Title One", description="Desc")
        tool_func(title="Title Two")

        assert call_count == 1

    def test_function_annotations(
        self, simple_schema: dict[str, Any], simple_template: str
    ) -> None:
        """Test that function has correct annotations."""
        pydantic_model = json_schema_to_pydantic(simple_schema, "TestModel")
        tool_func = _create_widget_tool_function(
            "Test Widget", pydantic_model, simple_template
        )

        assert hasattr(tool_func, "__annotations__")
        assert "return" in tool_func.__annotations__
        assert tool_func.__annotations__["return"] == WidgetComponentBase


class TestRegisterWidgetTools:
    """Tests for register_widget_tools function."""

    def test_register_widget_tools_runs(self) -> None:
        """Test that register_widget_tools executes without errors."""
        # The function should have been called on module import
        # We can verify by checking that the server has tools in its registry
        # Access the server's internal tool registry
        assert hasattr(server, "_tool_manager")
        assert len(server._tool_manager._tools) >= 2

    def test_registered_tools_have_correct_names(self) -> None:
        """Test that registered tools have correct naming."""
        # Access tool names from the server's tool registry
        tool_names = list(server._tool_manager._tools.keys())

        # Should have snake_case names
        assert "flight_tracker" in tool_names
        assert "create_event" in tool_names


class TestServerInstance:
    """Tests for the server instance."""

    def test_server_has_correct_name(self) -> None:
        """Test that server has the correct name."""
        assert server.name == "mcp-chatkit-widget"

    def test_server_is_fastmcp_instance(self) -> None:
        """Test that server is a FastMCP instance."""
        from fastmcp import FastMCP

        assert isinstance(server, FastMCP)
