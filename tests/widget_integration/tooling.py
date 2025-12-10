"""Support utilities for widget integration tests."""

from __future__ import annotations
from typing import Any
from mcp_chatkit_widget.rendering import build_widget_model
from mcp_chatkit_widget.server import _create_widget_tool_function


def deep_compare(obj1: Any, obj2: Any) -> bool:
    """Recursively compare two objects for equality with relaxed numeric checks."""
    if obj1 is obj2:
        result = True
    elif obj1 is None or obj2 is None:
        result = False
    elif isinstance(obj1, (int, float)) and isinstance(obj2, (int, float)):
        result = abs(obj1 - obj2) < 1e-10
    elif type(obj1) is not type(obj2):
        result = False
    elif isinstance(obj1, dict):
        result = _compare_dicts(obj1, obj2)
    elif isinstance(obj1, list):
        result = _compare_lists(obj1, obj2)
    elif isinstance(obj1, str):
        result = obj1 == obj2
    else:
        result = obj1 == obj2
    return result


def build_tool_components(widget: Any):
    """Return the pydantic model and tool function for a widget definition."""
    pydantic_model = build_widget_model(widget)
    tool_func = _create_widget_tool_function(widget)
    return pydantic_model, tool_func


def _compare_dicts(left: dict[str, Any], right: dict[str, Any]) -> bool:
    for key in right:
        if key not in left:
            return False
        if not deep_compare(left[key], right[key]):
            return False
    return True


def _compare_lists(left: list[Any], right: list[Any]) -> bool:
    if len(left) != len(right):
        return False
    return all(deep_compare(a, b) for a, b in zip(left, right, strict=True))
