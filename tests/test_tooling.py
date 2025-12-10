"""Tests for tooling helpers that register widget tools."""

from __future__ import annotations
import json
from collections.abc import Callable
from pathlib import Path
from typing import Any
import pytest
from chatkit.widgets import WidgetComponentBase
from mcp_chatkit_widget.tooling import generate_widget_tools
from mcp_chatkit_widget.widget_loader import load_widget


class DummyServer:
    """Minimal stand-in for FastMCP to capture registered tools."""

    def __init__(self) -> None:
        self.registered: dict[str, Callable[..., Any]] = {}

    def tool(self, name: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            self.registered[name] = func
            return func

        return decorator


def _write_sample_widget(tmp_path: Path, widget_name: str) -> Path:
    """Create a simple widget file that satisfies the loader requirements."""
    payload = {
        "version": "1.0",
        "name": widget_name,
        "template": '{"type":"Card","children":[]}',
        "jsonSchema": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
            },
            "required": ["title"],
        },
        "outputJsonPreview": {"type": "Card", "children": []},
    }
    safe_name = widget_name.replace(" ", "_")
    widget_path = tmp_path / f"{safe_name}.widget"
    widget_path.write_text(json.dumps(payload))
    return widget_path


class TestGenerateWidgetTools:
    """Ensure tooling helpers register sanitized FastMCP tools."""

    @pytest.mark.parametrize(
        ("widget_name", "expected_tool_name"),
        [
            ("123 Fancy Widget", "_123_fancy_widget"),
            ("My-Widget!", "my_widget"),
        ],
    )
    def test_registers_sanitized_tool_names(
        self, tmp_path: Path, widget_name: str, expected_tool_name: str
    ) -> None:
        widget_path = _write_sample_widget(tmp_path, widget_name)
        widget_def = load_widget(widget_path)
        server = DummyServer()

        generate_widget_tools(server, [widget_def])

        assert expected_tool_name in server.registered
        tool_func = server.registered[expected_tool_name]

        result = tool_func(title="Test Title")

        assert isinstance(result, WidgetComponentBase)
        assert result.type == "Card"
        assert len(server.registered) == 1
