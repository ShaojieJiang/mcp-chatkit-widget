"""Helpers for inspecting tool output and rendering chatkit card metadata."""

from __future__ import annotations
import json
from typing import Any
from chatkit import widgets


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


def display_card_widget(
    card_widget: widgets.WidgetComponentBase, widget_name: str
) -> None:
    """Print a lightweight summary about the generated ``card_widget``."""
    print("\nConverting to chatkit.widgets.Card...")
    print(f"Widget type: {type(card_widget).__name__}")
    print(f"Is Card instance: {isinstance(card_widget, widgets.Card)}")

    if isinstance(card_widget, widgets.Card):
        print(f"Card size: {card_widget.size}")
        print(f"Card theme: {card_widget.theme}")
        print(f"Card background: {card_widget.background}")
        print(f"Number of children: {len(card_widget.children)}")

    print("\n" + "=" * 80)
    print("Card widget created successfully!")
