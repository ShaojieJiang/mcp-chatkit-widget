"""Helpers for translating JSON Schema definitions into Pydantic models."""

from typing import Any
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
        components = snake_or_lower.split("_")
        return "".join(component.title() for component in components)
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
    if item_type == "array":
        return list[Any]

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
    if field_type == "array":
        return _resolve_array_type(field_schema, model_name, field_name)

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


__all__ = [
    "json_schema_to_pydantic",
    "_to_title_case",
]
