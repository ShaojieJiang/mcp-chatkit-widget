"""Widget discovery and loading utilities.

This module provides functionality to automatically discover .widget files
and load their configuration for use in MCP tools.
"""

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class WidgetDefinition:
    """Represents a loaded widget definition.

    Attributes:
        name: The widget name
        version: Widget format version
        json_schema: JSON Schema defining the widget's input structure
        output_json_preview: Preview of the rendered widget output
        template: Jinja2 template string for rendering the widget
        encoded_widget: Base64 encoded widget data (optional)
        file_path: Path to the .widget file
    """

    name: str
    version: str
    json_schema: dict[str, Any]
    output_json_preview: dict[str, Any]
    template: str
    encoded_widget: str | None
    file_path: Path


def _validate_directory(path: Path, *, strict: bool) -> bool:
    if not path.exists():
        if strict:
            raise ValueError(f"Widgets directory does not exist: {path}")
        print(f"Warning: Custom widgets directory does not exist: {path}")
        return False
    if not path.is_dir():
        if strict:
            raise ValueError(f"Path is not a directory: {path}")
        print(f"Warning: Custom widgets path is not a directory: {path}")
        return False
    return True


def _build_search_paths(widgets_dir: Path | None) -> list[tuple[Path, bool]]:
    if widgets_dir is not None:
        return [(widgets_dir, True)]

    paths: list[tuple[Path, bool]] = []
    default_dir = Path(__file__).parent / "widgets"
    paths.append((default_dir, True))

    custom_dirs = os.environ.get("CUSTOM_WIDGETS_DIR", "")
    if custom_dirs:
        for entry in custom_dirs.split(os.pathsep):
            cleaned_entry = entry.strip()
            if not cleaned_entry:
                continue
            paths.append((Path(cleaned_entry).expanduser(), False))

    return paths


def discover_widgets(widgets_dir: Path | None = None) -> list[WidgetDefinition]:
    """Discover all .widget files from bundled and custom directories.

    Args:
        widgets_dir: Directory to search for .widget files. If provided, only
            this directory is scanned. When None, the default package widgets
            directory is scanned along with any directories defined via the
            ``CUSTOM_WIDGETS_DIR`` environment variable (supports multiple
            directories separated by ``os.pathsep``).

    Returns:
        List of WidgetDefinition objects for all discovered widgets

    Raises:
        ValueError: If ``widgets_dir`` doesn't exist or isn't a directory
    """
    search_paths = _build_search_paths(widgets_dir)

    widgets: list[WidgetDefinition] = []
    seen_files: set[Path] = set()

    for path, strict in search_paths:
        if not _validate_directory(path, strict=strict):
            continue

        for widget_file in sorted(path.glob("*.widget")):
            resolved_file = widget_file.resolve()
            if resolved_file in seen_files:
                continue
            seen_files.add(resolved_file)
            try:
                widget_def = load_widget(widget_file)
                widgets.append(widget_def)
            except Exception as e:
                # Log the error but continue discovering other widgets
                print(f"Warning: Failed to load widget {widget_file}: {e}")

    return widgets


def load_widget(widget_path: Path) -> WidgetDefinition:
    """Load a widget definition from a .widget file.

    Args:
        widget_path: Path to the .widget file

    Returns:
        WidgetDefinition object containing the parsed widget data

    Raises:
        ValueError: If the widget file is invalid or missing required fields
        json.JSONDecodeError: If the widget file contains invalid JSON
    """
    with open(widget_path) as f:
        data = json.load(f)

    # Validate required fields
    required_fields = ["name", "version", "jsonSchema", "outputJsonPreview", "template"]
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        raise ValueError(
            f"Widget file missing required fields: {', '.join(missing_fields)}"
        )

    return WidgetDefinition(
        name=data["name"],
        version=data["version"],
        json_schema=data["jsonSchema"],
        output_json_preview=data["outputJsonPreview"],
        template=data["template"],
        encoded_widget=data.get("encodedWidget"),
        file_path=widget_path,
    )


def get_widget_by_name(
    name: str, widgets_dir: Path | None = None
) -> WidgetDefinition | None:
    """Get a specific widget by name.

    Args:
        name: The widget name to search for
        widgets_dir: Directory to search for .widget files.
                    If None, uses the default package widgets directory.

    Returns:
        WidgetDefinition if found, None otherwise
    """
    widgets = discover_widgets(widgets_dir)
    for widget in widgets:
        if widget.name == name:
            return widget
    return None
