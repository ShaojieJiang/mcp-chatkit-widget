"""Helpers for inspecting tool output."""

from __future__ import annotations
import json
from typing import Any


def parse_tool_result(result: Any) -> dict[str, Any] | None:
    """Convert FastMCP tool output into a dictionary widget payload."""
    if not getattr(result, "content", None):
        return None

    widget_dict = None
    for content_item in result.content:
        if hasattr(content_item, "text"):
            widget_dict = _try_parse_json(content_item.text)
        elif hasattr(content_item, "data"):
            widget_dict = content_item.data
        else:
            print(content_item)
            continue

        if widget_dict is not None:
            print(json.dumps(widget_dict, indent=2))

    return widget_dict


def _try_parse_json(raw: str) -> dict[str, Any] | None:
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        print(raw)
        return None


def display_widget_payload(widget_dict: dict[str, Any], widget_name: str) -> None:
    """Print a lightweight summary of the widget payload returned by FastMCP."""
    root_type = widget_dict.get("type", "<unknown>")
    children = widget_dict.get("children")
    print("\nWidget result summary:")
    print(f"- Widget name: {widget_name}")
    print(f"- Root type: {root_type}")
    if isinstance(children, list):
        print(f"- Children count: {len(children)}")
    print("\n" + "=" * 80)
    print("Widget payload displayed successfully!")
