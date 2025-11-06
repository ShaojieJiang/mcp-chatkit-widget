"""Utilities shared by widget integration tests."""

from __future__ import annotations

from typing import Any


def extract_input_data_from_preview(
    json_schema: dict[str, Any],
    output_json_preview: dict[str, Any],
) -> dict[str, Any]:
    """Infer input payloads that reproduce the preview output for a widget."""
    if "date" in json_schema.get("properties", {}) and "events" in json_schema.get(
        "properties", {}
    ):
        date_info: dict[str, Any] | None = None
        events_list: list[dict[str, Any]] = []

        if output_json_preview.get("type") == "Card":
            for child in output_json_preview.get("children", []):
                if child.get("type") != "Row":
                    continue
                for col in child.get("children", []):
                    if col.get("type") != "Col":
                        continue
                    if "width" in col:
                        col_children = col.get("children", [])
                        if len(col_children) >= 2:
                            caption, title = col_children[:2]
                            date_info = {
                                "name": caption.get("value"),
                                "number": title.get("value"),
                            }
                    elif col.get("flex") == "auto":
                        for event_row in col.get("children", []):
                            if event_row.get("type") != "Row" or "key" not in event_row:
                                continue
                            row_children = event_row.get("children", [])
                            if len(row_children) < 2:
                                continue
                            box, event_col = row_children[:2]
                            event_texts = event_col.get("children", [])
                            if len(event_texts) < 2:
                                continue
                            events_list.append(
                                {
                                    "id": event_row.get("key"),
                                    "title": event_texts[0].get("value"),
                                    "time": event_texts[1].get("value"),
                                    "color": box.get("background"),
                                    "isNew": event_row.get("background") == "none",
                                }
                            )
        return {"date": date_info, "events": events_list}

    if "airline" in json_schema.get("properties", {}) and "departure" in json_schema.get(
        "properties", {}
    ):
        data: dict[str, Any] = {
            "number": "",
            "date": "",
            "progress": "",
            "airline": {"name": "", "logo": ""},
            "departure": {"city": "", "status": "", "time": ""},
            "arrival": {"city": "", "status": "", "time": ""},
        }

        if output_json_preview.get("type") == "Card":
            children = output_json_preview.get("children", [])

            if children and children[0].get("type") == "Row":
                header_children = children[0].get("children", [])
                if len(header_children) >= 4:
                    data["airline"]["logo"] = header_children[0].get("src", "")
                    data["number"] = header_children[1].get("value", "")
                    data["date"] = header_children[3].get("value", "")

            if len(children) > 2 and children[2].get("type") == "Col":
                col_children = children[2].get("children", [])

                if col_children and col_children[0].get("type") == "Row":
                    city_children = col_children[0].get("children", [])
                    if len(city_children) >= 3:
                        data["departure"]["city"] = city_children[0].get("value", "")
                        data["arrival"]["city"] = city_children[2].get("value", "")

                if len(col_children) > 1 and col_children[1].get("type") == "Box":
                    progress_children = col_children[1].get("children", [])
                    if progress_children:
                        data["progress"] = progress_children[0].get("width", "")

                if len(col_children) > 2 and col_children[2].get("type") == "Row":
                    time_children = col_children[2].get("children", [])
                    if len(time_children) >= 3:
                        dep_children = time_children[0].get("children", [])
                        if len(dep_children) >= 2:
                            data["departure"]["time"] = dep_children[0].get("value", "")
                            data["departure"]["status"] = dep_children[1].get("value", "")

                        arr_children = time_children[2].get("children", [])
                        if len(arr_children) >= 2:
                            data["arrival"]["status"] = arr_children[0].get("value", "")
                            data["arrival"]["time"] = arr_children[1].get("value", "")
        return data

    def extract_simple_values(obj: Any) -> list[Any]:
        values: list[Any] = []
        if isinstance(obj, dict):
            if "value" in obj:
                values.append(obj["value"])
            if "src" in obj:
                values.append(obj["src"])
            if "children" in obj and isinstance(obj["children"], list):
                for child in obj["children"]:
                    values.extend(extract_simple_values(child))
        elif isinstance(obj, list):
            for item in obj:
                values.extend(extract_simple_values(item))
        return values

    def create_default_value(schema_def: dict[str, Any]) -> Any:
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
            obj: dict[str, Any] = {}
            for prop_name, prop_schema in schema_def.get("properties", {}).items():
                obj[prop_name] = create_default_value(prop_schema)
            return obj
        return None

    properties = json_schema.get("properties", {})
    return {name: create_default_value(prop) for name, prop in properties.items()}


def deep_compare(obj1: Any, obj2: Any) -> bool:
    """Recursively compare two objects while tolerating numeric coercion."""
    if obj1 is None and obj2 is None:
        return True
    if obj1 is None or obj2 is None:
        return False

    if isinstance(obj1, (int, float)) and isinstance(obj2, (int, float)):
        return abs(obj1 - obj2) < 1e-10

    if not isinstance(obj1, type(obj2)):
        return False

    if isinstance(obj1, dict):
        for key in obj2.keys():
            if key not in obj1:
                return False
            if not deep_compare(obj1[key], obj2[key]):
                return False
        return True

    if isinstance(obj1, list):
        if len(obj1) != len(obj2):
            return False
        return all(deep_compare(a, b) for a, b in zip(obj1, obj2, strict=True))

    if isinstance(obj1, str):
        return obj1 == obj2

    return obj1 == obj2
