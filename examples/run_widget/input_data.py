"""Utilities for inferring example widget input payloads from previews."""

from __future__ import annotations
from typing import Any


def extract_input_data_from_preview(  # noqa: C901, PLR0912, PLR0915
    json_schema: dict[str, Any],
    output_json_preview: dict[str, Any],
) -> dict[str, Any]:
    """Infer the original input payload that produced ``output_json_preview``.

    The logic handles a couple of well-known widget types with custom extractors
    and falls back to building a schema-driven default payload when faced with
    an unfamiliar widget definition.
    """
    if _is_calendar_schema(json_schema):
        return _extract_calendar_input(output_json_preview)

    if _is_flight_tracker_schema(json_schema):
        return _extract_flight_tracker_input(output_json_preview)

    return _build_schema_defaults(json_schema)


def _is_calendar_schema(json_schema: dict[str, Any]) -> bool:
    properties = json_schema.get("properties", {})
    return "date" in properties and "events" in properties


def _extract_calendar_input(output_json_preview: dict[str, Any]) -> dict[str, Any]:
    date_info = None
    events_list = []

    if output_json_preview.get("type") != "Card":
        return {"date": date_info, "events": events_list}

    for child in output_json_preview.get("children", []):
        if child.get("type") != "Row":
            continue

        for col in child.get("children", []):
            if col.get("type") != "Col":
                continue

            if "width" in col:
                date_info = _extract_calendar_date(col)
            elif col.get("flex") == "auto":
                events_list.extend(_extract_calendar_events(col))

    return {"date": date_info, "events": events_list}


def _extract_calendar_date(col: dict[str, Any]) -> dict[str, Any] | None:
    col_children = col.get("children", [])
    if len(col_children) < 2:
        return None

    caption, title = col_children[0], col_children[1]
    return {
        "name": caption.get("value"),
        "number": title.get("value"),
    }


def _extract_calendar_events(col: dict[str, Any]) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for event_row in col.get("children", []):
        if event_row.get("type") != "Row" or "key" not in event_row:
            continue

        row_children = event_row.get("children", [])
        if len(row_children) < 2:
            continue

        box, event_col = row_children[0], row_children[1]
        event_texts = event_col.get("children", [])

        if len(event_texts) < 2:
            continue

        events.append(
            {
                "id": event_row.get("key"),
                "title": event_texts[0].get("value"),
                "time": event_texts[1].get("value"),
                "color": box.get("background"),
                "isNew": event_row.get("background") == "none",
            }
        )

    return events


def _is_flight_tracker_schema(json_schema: dict[str, Any]) -> bool:
    properties = json_schema.get("properties", {})
    return "airline" in properties and "departure" in properties


def _extract_flight_tracker_input(
    output_json_preview: dict[str, Any],
) -> dict[str, Any]:
    data: dict[str, Any] = {
        "number": "",
        "date": "",
        "progress": "",
        "airline": {"name": "", "logo": ""},
        "departure": {"city": "", "status": "", "time": ""},
        "arrival": {"city": "", "status": "", "time": ""},
    }

    if output_json_preview.get("type") != "Card":
        return data

    children = output_json_preview.get("children", [])
    _extract_flight_header(children, data)
    _extract_flight_body(children, data)

    return data


def _extract_flight_header(
    children: list[dict[str, Any]],
    data: dict[str, Any],
) -> None:
    if not children or children[0].get("type") != "Row":
        return

    header_children = children[0].get("children", [])
    if len(header_children) < 4:
        return

    data["airline"]["logo"] = header_children[0].get("src", "")
    data["number"] = header_children[1].get("value", "")
    data["date"] = header_children[3].get("value", "")


def _extract_flight_body(
    children: list[dict[str, Any]],
    data: dict[str, Any],
) -> None:
    if len(children) <= 2 or children[2].get("type") != "Col":
        return

    col_children = children[2].get("children", [])
    _extract_flight_cities(col_children, data)
    _extract_flight_progress(col_children, data)
    _extract_flight_times(col_children, data)


def _extract_flight_cities(
    col_children: list[dict[str, Any]],
    data: dict[str, Any],
) -> None:
    if not col_children or col_children[0].get("type") != "Row":
        return

    city_children = col_children[0].get("children", [])
    if len(city_children) < 3:
        return

    data["departure"]["city"] = city_children[0].get("value", "")
    data["arrival"]["city"] = city_children[2].get("value", "")


def _extract_flight_progress(
    col_children: list[dict[str, Any]],
    data: dict[str, Any],
) -> None:
    if len(col_children) <= 1 or col_children[1].get("type") != "Box":
        return

    progress_children = col_children[1].get("children", [])
    if not progress_children:
        return

    data["progress"] = progress_children[0].get("width", "")


def _extract_flight_times(
    col_children: list[dict[str, Any]],
    data: dict[str, Any],
) -> None:
    if len(col_children) <= 2 or col_children[2].get("type") != "Row":
        return

    time_children = col_children[2].get("children", [])
    if len(time_children) < 3:
        return

    _extract_flight_departure(time_children[0], data)
    _extract_flight_arrival(time_children[2], data)


def _extract_flight_departure(
    section: dict[str, Any],
    data: dict[str, Any],
) -> None:
    dep_children = section.get("children", [])
    if len(dep_children) < 2:
        return

    data["departure"]["time"] = dep_children[0].get("value", "")
    data["departure"]["status"] = dep_children[1].get("value", "")


def _extract_flight_arrival(
    section: dict[str, Any],
    data: dict[str, Any],
) -> None:
    arr_children = section.get("children", [])
    if len(arr_children) < 2:
        return

    data["arrival"]["status"] = arr_children[0].get("value", "")
    data["arrival"]["time"] = arr_children[1].get("value", "")


def _build_schema_defaults(json_schema: dict[str, Any]) -> dict[str, Any]:
    properties = json_schema.get("properties", {})
    defaults: dict[str, Any] = {}
    for prop, schema in properties.items():
        defaults[prop] = _create_default_value(schema)
    return defaults


def _create_default_value(schema_def: dict[str, Any]) -> Any:
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
        result: dict[str, Any] = {}
        for name, prop_schema in properties.items():
            result[name] = _create_default_value(prop_schema)
        return result
    return None
