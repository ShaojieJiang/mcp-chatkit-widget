"""Utilities for converting JSON schemas to Pydantic models and ChatKit widgets.

This module provides functions to dynamically convert JSON Schema definitions
into Pydantic models and to transform widget JSON structures into ChatKit
widget component objects.
"""

from typing import Any
from chatkit import widgets
from pydantic import BaseModel, ConfigDict, create_model


def _to_title_case(snake_or_lower: str) -> str:
    """Convert a string to TitleCase.

    Args:
        snake_or_lower: String in snake_case or lowercase
            (e.g., "flight_tracker" or "date")

    Returns:
        String in TitleCase (e.g., "FlightTracker" or "Date")
    """
    if "_" in snake_or_lower:
        # snake_case: split and title each part
        components = snake_or_lower.split("_")
        return "".join(x.title() for x in components)
    # Single word: just capitalize
    return snake_or_lower.capitalize()


def _get_type_map() -> dict[str, type]:
    """Return mapping from JSON Schema types to Python types."""
    return {
        "string": str,
        "integer": int,
        "number": float,
        "boolean": bool,
        "array": list,
        "object": dict,
    }


def _resolve_array_type(
    field_schema: dict[str, Any], model_name: str, field_name: str
) -> Any:
    """Resolve Python type for array field schema."""
    items_schema = field_schema.get("items")
    if not isinstance(items_schema, dict):
        return list[Any]

    item_type = items_schema.get("type")
    if item_type == "object":
        item_model_name = f"{model_name}{_to_title_case(field_name)}Item"
        item_model = json_schema_to_pydantic(items_schema, item_model_name)
        return list[item_model]  # type: ignore[valid-type]
    elif item_type == "array":
        return list[Any]
    else:
        type_map = _get_type_map()
        mapped_type = type_map.get(item_type or "", Any)
        return list[mapped_type]  # type: ignore[valid-type]


def _resolve_field_type(
    field_schema: dict[str, Any], model_name: str, field_name: str
) -> Any:
    """Resolve Python type for a field based on its schema."""
    field_type = field_schema.get("type")

    if field_type == "object":
        nested_model_name = f"{model_name}{_to_title_case(field_name)}"
        return json_schema_to_pydantic(field_schema, nested_model_name)
    elif field_type == "array":
        return _resolve_array_type(field_schema, model_name, field_name)
    else:
        type_map = _get_type_map()
        return type_map.get(field_type or "", Any)


def _build_field_definitions(
    properties: dict[str, Any], required_fields: set[str], model_name: str
) -> dict[str, Any]:
    """Build field definitions dict for Pydantic model creation."""
    field_definitions: dict[str, Any] = {}

    for field_name, field_schema in properties.items():
        python_type = _resolve_field_type(field_schema, model_name, field_name)

        if field_name not in required_fields:
            python_type = python_type | None
            field_definitions[field_name] = (python_type, None)
        else:
            field_definitions[field_name] = (python_type, ...)

    return field_definitions


def _build_model_config(
    schema: dict[str, Any], schema_title: str | None
) -> dict[str, Any]:
    """Build configuration kwargs for Pydantic model."""
    config_kwargs: dict[str, Any] = {}
    if schema_title:
        config_kwargs["title"] = schema_title
    if schema.get("additionalProperties") is False:
        config_kwargs["extra"] = "forbid"
    return config_kwargs


def json_schema_to_pydantic(
    schema: dict[str, Any],
    model_name: str = "DynamicModel",
    schema_title: str | None = None,
) -> type[BaseModel]:
    """Convert a JSON schema to a Pydantic model.

    This function recursively converts JSON schema definitions into Pydantic model
    classes, handling nested objects and required fields.

    Args:
        schema: JSON schema dictionary conforming to JSON Schema spec
        model_name: Name for the generated Pydantic model class
        schema_title: Optional custom title for the JSON schema (defaults to model_name)

    Returns:
        A dynamically created Pydantic BaseModel class

    Raises:
        ValueError: If the root schema is not of type 'object'

    Example:
        >>> schema = {
        ...     "type": "object",
        ...     "properties": {
        ...         "name": {"type": "string"},
        ...         "age": {"type": "integer"}
        ...     },
        ...     "required": ["name"]
        ... }
        >>> Model = json_schema_to_pydantic(schema, "Person")
        >>> person = Model(name="Alice", age=30)
    """
    if schema.get("type") != "object":
        raise ValueError("Root schema must be of type 'object'")

    properties = schema.get("properties", {})
    required_fields = set(schema.get("required", []))

    field_definitions = _build_field_definitions(
        properties, required_fields, model_name
    )
    config_kwargs = _build_model_config(schema, schema_title)

    if config_kwargs:
        config = ConfigDict(**config_kwargs)  # type: ignore[typeddict-item]
        return create_model(model_name, __config__=config, **field_definitions)

    return create_model(model_name, **field_definitions)


def json_schema_to_chatkit_widget(
    output_json_preview: dict[str, Any], widget_name: str
) -> widgets.WidgetComponentBase:
    """Convert output JSON preview to OpenAI ChatKit widget object.

    This function transforms a widget preview JSON structure into a proper
    ChatKit WidgetComponentBase object by dynamically instantiating the
    appropriate widget component classes.

    Args:
        output_json_preview: Widget structure with type and children components
        widget_name: Display name for the widget (used for logging/debugging)

    Returns:
        A ChatKit WidgetComponentBase instance (Card, Row, Col, etc.)

    Example:
        >>> preview = {
        ...     "type": "Card",
        ...     "children": [{"type": "Text", "value": "Hello"}]
        ... }
        >>> widget = json_schema_to_chatkit_widget(preview, "Greeting")
        >>> isinstance(widget, widgets.Card)
        True
    """
    return _dict_to_widget_component(output_json_preview)


def _dict_to_widget_component(
    component_dict: dict[str, Any],
) -> widgets.WidgetComponentBase:
    """Recursively convert dictionary to ChatKit widget component instance.

    Args:
        component_dict: Dictionary with 'type' and component properties

    Returns:
        Instantiated ChatKit widget component

    Raises:
        ValueError: If component type is unknown or not supported
    """
    component_type = component_dict.get("type")
    if not component_type:
        raise ValueError("Component dictionary must have a 'type' field")

    # Map component type names to widget classes
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

    # Extract all properties except 'type'
    props = {k: v for k, v in component_dict.items() if k != "type"}

    # Recursively process children if present
    if "children" in props and props["children"]:
        props["children"] = [
            _dict_to_widget_component(child) for child in props["children"]
        ]

    # Instantiate the widget component with the properties
    return widget_class(**props)


def create_widget_instance(
    pydantic_model: type[BaseModel], data: dict[str, Any]
) -> BaseModel:
    """Create a widget instance from a Pydantic model and input data.

    This function validates input data against the schema and creates
    a type-safe instance of the widget's data model.

    Args:
        pydantic_model: Pydantic model class defining the schema
        data: Dictionary containing the widget data

    Returns:
        Validated Pydantic model instance

    Raises:
        ValidationError: If data doesn't conform to the schema

    Example:
        >>> Model = json_schema_to_pydantic(schema, "FlightData")
        >>> instance = create_widget_instance(Model, flight_data)
        >>> print(instance.airline.name)
    """
    return pydantic_model(**data)
