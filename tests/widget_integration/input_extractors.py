"""Utilities to infer widget input data from preview JSON."""

from __future__ import annotations
from collections.abc import Iterable
from typing import Any


def extract_input_data_from_preview(
    json_schema: dict[str, Any],
    output_json_preview: dict[str, Any],
) -> dict[str, Any]:
    """Infer input data for a widget run from its preview output."""
    if _looks_like_create_event(json_schema):
        return _create_event_input(output_json_preview)
    if _looks_like_flight_tracker(json_schema):
        return _flight_tracker_input(output_json_preview)
    return _generic_input(json_schema)


def _looks_like_create_event(json_schema: dict[str, Any]) -> bool:
    properties = json_schema.get("properties", {})
    return {"date", "events"}.issubset(properties)


def _looks_like_flight_tracker(json_schema: dict[str, Any]) -> bool:
    properties = json_schema.get("properties", {})
    return {"airline", "departure", "arrival"}.issubset(properties)


def _create_event_input(output_json_preview: dict[str, Any]) -> dict[str, Any]:
    date_info = _create_event_date(output_json_preview)
    events = _create_event_entries(output_json_preview)
    return {"date": date_info, "events": events}


def _create_event_date(output_json_preview: dict[str, Any]) -> dict[str, Any] | None:
    for column in _card_columns(output_json_preview):
        if column.get("type") != "Col" or "width" not in column:
            continue
        caption, title = _first_two_children(column)
        if caption is None or title is None:
            continue
        return {"name": caption.get("value"), "number": title.get("value")}
    return None


def _create_event_entries(output_json_preview: dict[str, Any]) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for column in _card_columns(output_json_preview):
        if column.get("type") != "Col" or column.get("flex") != "auto":
            continue
        for row in _child_dicts(column, "Row"):
            entry = _parse_event_row(row)
            if entry is not None:
                entries.append(entry)
    return entries


def _parse_event_row(row: dict[str, Any]) -> dict[str, Any] | None:
    if "key" not in row:
        return None
    box, event_col = _first_two_children(row)
    text_a, text_b = _first_two_children(event_col)
    if text_a is None or text_b is None:
        return None
    background = box.get("background") if isinstance(box, dict) else None
    return {
        "id": row.get("key"),
        "title": text_a.get("value"),
        "time": text_b.get("value"),
        "color": background,
        "isNew": row.get("background") == "none",
    }


def _flight_tracker_input(output_json_preview: dict[str, Any]) -> dict[str, Any]:
    data: dict[str, Any] = {
        "number": "",
        "date": "",
        "progress": "",
        "airline": {"name": "", "logo": ""},
        "departure": {"city": "", "status": "", "time": ""},
        "arrival": {"city": "", "status": "", "time": ""},
    }
    if not _is_card(output_json_preview):
        return data

    children = _child_dicts(output_json_preview)
    header = next(children, None)
    details = list(children)

    if header is not None:
        _populate_header(data, header)
    if len(details) >= 2:
        _populate_details(data, details[1])
    return data


def _populate_header(data: dict[str, Any], row: dict[str, Any]) -> None:
    if row.get("type") != "Row":
        return
    cells = list(_child_dicts(row))
    if len(cells) < 4:
        return
    logo, number, _, date = (cell if isinstance(cell, dict) else {} for cell in cells)
    data["airline"]["logo"] = logo.get("src", "")
    data["number"] = number.get("value", "")
    data["date"] = date.get("value", "")


def _populate_details(data: dict[str, Any], column: dict[str, Any]) -> None:
    if column.get("type") != "Col":
        return
    items = list(_child_dicts(column))
    if items:
        _populate_cities(data, items[0])
    if len(items) > 1:
        _populate_progress(data, items[1])
    if len(items) > 2:
        _populate_times(data, items[2])


def _populate_cities(data: dict[str, Any], row: dict[str, Any]) -> None:
    if row.get("type") != "Row":
        return
    cells = list(_child_dicts(row))
    if len(cells) < 3:
        return
    departure = cells[0] if isinstance(cells[0], dict) else {}
    arrival = cells[2] if isinstance(cells[2], dict) else {}
    data["departure"]["city"] = departure.get("value", "")
    data["arrival"]["city"] = arrival.get("value", "")


def _populate_progress(data: dict[str, Any], box: dict[str, Any]) -> None:
    if box.get("type") != "Box":
        return
    progress = next(_child_dicts(box), {})
    data["progress"] = progress.get("width", "")


def _populate_times(data: dict[str, Any], row: dict[str, Any]) -> None:
    if row.get("type") != "Row":
        return
    cells = list(_child_dicts(row))
    if len(cells) < 3:
        return
    _set_time_block(data["departure"], cells[0])
    _set_time_block(data["arrival"], cells[2])


def _set_time_block(target: dict[str, Any], column: dict[str, Any]) -> None:
    first, second = _first_two_children(column)
    if first is None or second is None:
        return
    first_value = first.get("value")
    second_value = second.get("value")

    if isinstance(first_value, str) and ":" in first_value:
        target["time"] = first_value
        target["status"] = second_value if isinstance(second_value, str) else ""
    elif isinstance(second_value, str) and ":" in second_value:
        target["time"] = second_value
        target["status"] = first_value if isinstance(first_value, str) else ""
    else:
        target["status"] = first_value if isinstance(first_value, str) else ""
        target["time"] = second_value if isinstance(second_value, str) else ""


def _generic_input(json_schema: dict[str, Any]) -> dict[str, Any]:
    properties = json_schema.get("properties", {})
    return {name: _default_value(schema_def) for name, schema_def in properties.items()}


def _default_value(schema_def: dict[str, Any]) -> Any:
    schema_type = schema_def.get("type")
    if schema_type == "string":
        return "2025-01-01"
    if schema_type in {"number", "integer"}:
        return 0
    if schema_type == "boolean":
        return False
    if schema_type == "array":
        return []
    if schema_type == "object":
        properties = schema_def.get("properties", {})
        return {prop: _default_value(defn) for prop, defn in properties.items()}
    return None


def _is_card(obj: Any) -> bool:
    return isinstance(obj, dict) and obj.get("type") == "Card"


def _card_columns(card: dict[str, Any]) -> Iterable[dict[str, Any]]:
    for row in _child_dicts(card, "Row"):
        yield from _child_dicts(row, "Col")


def _child_dicts(node: Any, type_name: str | None = None) -> Iterable[dict[str, Any]]:
    if not isinstance(node, dict):
        return
    children = node.get("children", [])
    if not isinstance(children, list):
        children = [children]
    for child in children:
        if isinstance(child, dict) and (
            type_name is None or child.get("type") == type_name
        ):
            yield child


def _first_two_children(
    node: Any,
) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    if not isinstance(node, dict):
        return None, None
    children = node.get("children", [])
    if not isinstance(children, list):
        children = [children]
    first = children[0] if len(children) > 0 and isinstance(children[0], dict) else None
    second = (
        children[1] if len(children) > 1 and isinstance(children[1], dict) else None
    )
    return first, second
