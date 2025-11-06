"""Utilities for translating JSON structures into ChatKit widget components."""

from typing import Any
from chatkit import widgets
from pydantic import BaseModel


def json_schema_to_chatkit_widget(
    output_json_preview: dict[str, Any], widget_name: str
) -> widgets.WidgetComponentBase:
    """Convert output JSON preview to OpenAI ChatKit widget object."""
    return _dict_to_widget_component(output_json_preview)


def _dict_to_widget_component(
    component_dict: dict[str, Any],
) -> widgets.WidgetComponentBase:
    """Recursively convert dictionary to ChatKit widget component instance."""
    component_type = component_dict.get("type")
    if not component_type:
        raise ValueError("Component dictionary must have a 'type' field")

    component_class_map = {
        "Card": widgets.Card,
        "Row": widgets.Row,
        "Col": widgets.Col,
        "Box": widgets.Box,
        "Text": widgets.Text,
        "Title": widgets.Title,
        "Caption": widgets.Caption,
        "Image": widgets.Image,
        "Icon": widgets.Icon,
        "Button": widgets.Button,
        "Divider": widgets.Divider,
        "Spacer": widgets.Spacer,
        "Badge": widgets.Badge,
        "Markdown": widgets.Markdown,
        "Input": widgets.Input,
        "Textarea": widgets.Textarea,
        "Select": widgets.Select,
        "Checkbox": widgets.Checkbox,
        "RadioGroup": widgets.RadioGroup,
        "DatePicker": widgets.DatePicker,
        "Form": widgets.Form,
        "ListView": widgets.ListView,
        "Transition": widgets.Transition,
        "Chart": widgets.Chart,
    }

    widget_class = component_class_map.get(component_type)
    if not widget_class:
        raise ValueError(f"Unknown component type: {component_type}")

    props = {key: value for key, value in component_dict.items() if key != "type"}

    if "children" in props and props["children"]:
        props["children"] = [
            _dict_to_widget_component(child) for child in props["children"]
        ]

    return widget_class(**props)


def create_widget_instance(
    pydantic_model: type[BaseModel], data: dict[str, Any]
) -> BaseModel:
    """Create a widget instance from a Pydantic model and input data."""
    return pydantic_model(**data)


__all__ = [
    "json_schema_to_chatkit_widget",
    "_dict_to_widget_component",
    "create_widget_instance",
]
