"""Compatibility layer that re-exports schema utility helpers.

Historically, schema utilities lived in this single module. The implementation
now resides in dedicated modules for Pydantic model generation and ChatKit
widget construction. Import here to preserve existing public interfaces.
"""

from .pydantic_conversion import _to_title_case, json_schema_to_pydantic
from .widget_conversion import (
    _dict_to_widget_component,
    create_widget_instance,
    json_schema_to_chatkit_widget,
)


__all__ = [
    "json_schema_to_pydantic",
    "json_schema_to_chatkit_widget",
    "create_widget_instance",
    "_to_title_case",
    "_dict_to_widget_component",
]
