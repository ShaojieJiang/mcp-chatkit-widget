"""Compatibility layer that re-exports schema utility helpers.

Historically, schema utilities lived in this single module. The implementation
now resides in dedicated modules for Pydantic model generation. Import here
to preserve the public interfaces that remain in use.
"""

from mcp_chatkit_widget.pydantic_conversion import (
    _to_title_case,
    json_schema_to_pydantic,
)


__all__ = [
    "json_schema_to_pydantic",
    "_to_title_case",
]
