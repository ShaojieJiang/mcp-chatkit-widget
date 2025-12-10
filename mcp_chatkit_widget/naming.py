"""Helper utilities for widget naming conventions."""


def _sanitize_tool_name(widget_name: str) -> str:
    """Convert widget names into safe snake_case identifiers."""
    sanitized = widget_name.lower().replace(" ", "_").replace("-", "_")
    sanitized = "".join(c for c in sanitized if c.isalnum() or c == "_")
    if sanitized and sanitized[0].isdigit():
        sanitized = "_" + sanitized
    return sanitized


def _to_camel_case(snake_str: str) -> str:
    """Convert a snake_case string into CamelCase."""
    components = snake_str.split("_")
    return "".join(x.title() for x in components)
