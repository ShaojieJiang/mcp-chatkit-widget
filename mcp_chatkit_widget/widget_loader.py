"""Widget discovery and loading utilities.

This module provides functionality to load curated .widget definitions and
expose them in a controlled way so the tooling always targets the same
directory.
"""

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any


LOGGER = logging.getLogger(__name__)


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


def _validate_widgets_dir(widgets_dir: Path | None) -> Path:
    """Ensure the provided widgets directory exists and is a directory."""
    if widgets_dir is None:
        raise ValueError("The widgets_dir argument is required to load widgets.")
    resolved_dir = widgets_dir.resolve()
    if not resolved_dir.exists():
        raise ValueError(f"Widgets directory does not exist: {resolved_dir}")
    if not resolved_dir.is_dir():
        raise ValueError(f"Widgets directory is not a directory: {resolved_dir}")
    return resolved_dir


def _collect_widget_files(base_dir: Path) -> list[Path]:
    """Return .widget files that physically live inside the base directory."""
    base_resolved = base_dir.resolve()
    widget_files: list[Path] = []
    seen_files: set[Path] = set()
    for widget_file in sorted(base_dir.rglob("*.widget")):
        if not widget_file.is_file():
            continue
        try:
            resolved_path = widget_file.resolve()
        except OSError as exc:
            LOGGER.warning(
                "Skipping widget %s because it could not be resolved (%s)",
                widget_file,
                exc,
            )
            continue
        try:
            resolved_path.relative_to(base_resolved)
        except ValueError:
            LOGGER.warning(
                "Skipping widget %s because it is outside the widgets directory",
                widget_file,
            )
            continue
        if resolved_path in seen_files:
            continue
        seen_files.add(resolved_path)
        widget_files.append(widget_file)
    return widget_files


def load_widgets(widgets_dir: Path | None) -> list[WidgetDefinition]:
    """Load all .widget files from the curated directory.

    Args:
        widgets_dir: Path to the curated widgets directory. Must exist.

    Returns:
        List of loaded WidgetDefinition instances.
    """
    base_dir = _validate_widgets_dir(widgets_dir)
    widget_files = _collect_widget_files(base_dir)

    if not widget_files:
        LOGGER.warning("No widget definitions found in %s", base_dir)

    return [load_widget(widget_file) for widget_file in widget_files]


def discover_widgets(widgets_dir: Path | None = None) -> list[WidgetDefinition]:
    """Discover widgets from a curated directory."""
    return load_widgets(widgets_dir)


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

    required_fields = ["name", "version", "jsonSchema", "outputJsonPreview", "template"]
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        raise ValueError(
            f"Widget file {widget_path} missing required fields: "
            f"{', '.join(missing_fields)}"
        )

    template_value = data["template"]
    if not isinstance(template_value, str):
        raise ValueError(f"Widget template must be a string: {widget_path}")

    return WidgetDefinition(
        name=data["name"],
        version=data["version"],
        json_schema=data["jsonSchema"],
        output_json_preview=data["outputJsonPreview"],
        template=template_value,
        encoded_widget=data.get("encodedWidget"),
        file_path=widget_path,
    )


def get_widget_by_name(name: str, widgets_dir: Path) -> WidgetDefinition | None:
    """Get a specific widget by name.

    Args:
        name: The widget name to search for
        widgets_dir: Directory to search for .widget files.

    Returns:
        WidgetDefinition if found, None otherwise
    """
    widgets = load_widgets(widgets_dir)
    for widget in widgets:
        if widget.name == name:
            return widget
    return None
