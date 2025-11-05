"""Generalized example for running any widget tool using FastMCP Client.

This example demonstrates how to:
1. Load a widget definition from a file path
2. Extract example input data from the widget's outputJsonPreview
3. Call the widget tool via MCP
4. Convert the result to a chatkit.widgets.Card object

Usage:
    python examples/run_widget.py <path/to/widget.widget>
    python examples/run_widget.py mcp_chatkit_widget/widgets/"Flight Tracker.widget"
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Any
from chatkit import widgets
from fastmcp import Client
from mcp_chatkit_widget.schema_utils import json_schema_to_chatkit_widget
from mcp_chatkit_widget.server import _sanitize_tool_name
from mcp_chatkit_widget.widget_loader import load_widget


def extract_input_data_from_preview(  # noqa: C901, PLR0912, PLR0915
    json_schema: dict[str, Any],
    output_json_preview: dict[str, Any],
) -> dict[str, Any]:
    """Extract input data from the widget's outputJsonPreview.

    This function infers what input data was used to generate the preview
    based on the JSON schema structure. For known widgets, we extract
    the data from the known structure. For unknown widgets, we create
    default values based on the schema.

    Args:
        json_schema: The widget's JSON schema
        output_json_preview: The preview output JSON

    Returns:
        Dictionary with input data that should produce the output
    """
    # For Create Event widget
    if "date" in json_schema.get("properties", {}) and "events" in json_schema.get(
        "properties", {}
    ):
        # Extract date information
        date_info = None
        events_list = []

        # Navigate through the output structure to find the data
        if output_json_preview.get("type") == "Card":
            for child in output_json_preview.get("children", []):
                if child.get("type") == "Row":
                    for col in child.get("children", []):
                        if col.get("type") == "Col" and "width" in col:
                            # This is the date column
                            col_children = col.get("children", [])
                            if len(col_children) >= 2:
                                caption = col_children[0]
                                title = col_children[1]
                                date_info = {
                                    "name": caption.get("value"),
                                    "number": title.get("value"),
                                }
                        elif col.get("type") == "Col" and col.get("flex") == "auto":
                            # This is the events column
                            for event_row in col.get("children", []):
                                if (
                                    event_row.get("type") == "Row"
                                    and "key" in event_row
                                ):
                                    row_children = event_row.get("children", [])
                                    if len(row_children) >= 2:
                                        # First child is the colored box
                                        box = row_children[0]
                                        # Second child is the Col with title and time
                                        event_col = row_children[1]
                                        event_texts = event_col.get("children", [])

                                        if len(event_texts) >= 2:
                                            event = {
                                                "id": event_row.get("key"),
                                                "title": event_texts[0].get("value"),
                                                "time": event_texts[1].get("value"),
                                                "color": box.get("background"),
                                                "isNew": event_row.get("background")
                                                == "none",
                                            }
                                            events_list.append(event)

        return {"date": date_info, "events": events_list}

    # For Flight Tracker widget
    if "airline" in json_schema.get(
        "properties", {}
    ) and "departure" in json_schema.get("properties", {}):
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

            # First row contains airline logo, flight number, and date
            if len(children) > 0 and children[0].get("type") == "Row":
                header_children = children[0].get("children", [])
                if len(header_children) >= 4:
                    data["airline"]["logo"] = header_children[0].get("src", "")
                    data["number"] = header_children[1].get("value", "")
                    data["date"] = header_children[3].get("value", "")

            # Third element is Col with flight details
            if len(children) > 2 and children[2].get("type") == "Col":
                col_children = children[2].get("children", [])

                # First row has cities
                if len(col_children) > 0 and col_children[0].get("type") == "Row":
                    city_children = col_children[0].get("children", [])
                    if len(city_children) >= 3:
                        data["departure"]["city"] = city_children[0].get("value", "")
                        data["arrival"]["city"] = city_children[2].get("value", "")

                # Second element is the progress box
                if len(col_children) > 1 and col_children[1].get("type") == "Box":
                    progress_children = col_children[1].get("children", [])
                    if progress_children:
                        data["progress"] = progress_children[0].get("width", "")

                # Third row has times and statuses
                if len(col_children) > 2 and col_children[2].get("type") == "Row":
                    time_children = col_children[2].get("children", [])
                    if len(time_children) >= 3:
                        # Departure info
                        dep_children = time_children[0].get("children", [])
                        if len(dep_children) >= 2:
                            data["departure"]["time"] = dep_children[0].get("value", "")
                            data["departure"]["status"] = dep_children[1].get(
                                "value", ""
                            )

                        # Arrival info
                        arr_children = time_children[2].get("children", [])
                        if len(arr_children) >= 2:
                            data["arrival"]["status"] = arr_children[0].get("value", "")
                            data["arrival"]["time"] = arr_children[1].get("value", "")

        return data

    # Generic extraction for other widgets - create default values based on schema
    def create_default_value(schema_def: dict[str, Any]) -> Any:
        """Create a default value based on schema type."""
        schema_type = schema_def.get("type")
        if schema_type == "string":
            # Use a valid date format as default to handle DatePicker fields
            return "2025-01-01"
        elif schema_type in {"number", "integer"}:
            return 0
        elif schema_type == "boolean":
            return False
        elif schema_type == "array":
            return []
        elif schema_type == "object":
            obj = {}
            properties = schema_def.get("properties", {})
            for prop_name, prop_schema in properties.items():
                obj[prop_name] = create_default_value(prop_schema)
            return obj
        return None

    # For other widgets, create a minimal valid input based on schema
    properties = json_schema.get("properties", {})
    result = {}

    for prop_name, prop_schema in properties.items():
        result[prop_name] = create_default_value(prop_schema)

    return result


def _handle_missing_widget(widget_path: Path) -> None:
    """Handle case where widget file is not found."""
    print(f"Error: Widget file not found at {widget_path}")

    widgets_dir = Path(__file__).parent.parent / "mcp_chatkit_widget" / "widgets"
    if widgets_dir.exists():
        print(f"\nAvailable widgets in {widgets_dir}:")
        for widget_file in sorted(widgets_dir.glob("*.widget")):
            print(f"  - {widget_file}")
    sys.exit(1)


def _parse_tool_result(result: Any) -> dict[str, Any] | None:
    """Parse tool call result and extract widget dictionary."""
    widget_dict = None
    if not result.content:
        return None

    for content_item in result.content:
        if hasattr(content_item, "text"):
            try:
                widget_dict = json.loads(content_item.text)
            except json.JSONDecodeError:
                pass
            print(json.dumps(widget_dict, indent=2))
        elif hasattr(content_item, "data"):
            widget_dict = content_item.data
            print(json.dumps(widget_dict, indent=2))
        else:
            print(content_item)

    return widget_dict


def _display_card_widget(
    card_widget: widgets.WidgetComponentBase, widget_name: str
) -> None:
    """Display information about the converted card widget."""
    print("\nConverting to chatkit.widgets.Card...")
    print(f"Widget type: {type(card_widget).__name__}")
    print(f"Is Card instance: {isinstance(card_widget, widgets.Card)}")

    if isinstance(card_widget, widgets.Card):
        print(f"Card size: {card_widget.size}")
        print(f"Card theme: {card_widget.theme}")
        print(f"Card background: {card_widget.background}")
        print(f"Number of children: {len(card_widget.children)}")

    print("\n" + "=" * 80)
    print("Card widget created successfully!")


async def run_widget_example(widget_path_str: str) -> None:
    """Run an example for the specified widget.

    Args:
        widget_path_str: Path to the widget file (e.g., "widgets/Flight Tracker.widget")
    """
    widget_path = Path(widget_path_str).resolve()

    if not widget_path.exists():
        _handle_missing_widget(widget_path)

    widget_def = load_widget(widget_path)
    widget_name = widget_path.stem

    input_data = extract_input_data_from_preview(
        widget_def.json_schema,
        widget_def.output_json_preview,
    )

    print("=" * 80)
    print(f"{widget_name} Example (FastMCP Client)")
    print("=" * 80)
    print("\nInput Data:")
    print(json.dumps(input_data, indent=2))
    print("\n" + "=" * 80)

    config = {
        "mcpServers": {
            "chatkit": {
                "transport": "stdio",
                "command": "mcp-chatkit-widget",
            }
        }
    }

    tool_name = _sanitize_tool_name(widget_name)

    async with Client(config) as client:
        result = await client.call_tool(tool_name, input_data)

        print("\nTool Output (Raw JSON):")
        print("=" * 80)

        widget_dict = _parse_tool_result(result)
        print("=" * 80)

        if widget_dict:
            card_widget = json_schema_to_chatkit_widget(widget_dict, widget_name)
            _display_card_widget(card_widget, widget_name)
        else:
            print("\nNo widget data found in result.")

        print("=" * 80)
        print(f"\n{widget_name} example completed successfully!")


async def main() -> None:
    """Main entry point for the script."""
    if len(sys.argv) < 2:
        print("Usage: python examples/run_widget.py <widget_file_path>")
        print("\nExample:")
        print(
            "  python examples/run_widget.py "
            'mcp_chatkit_widget/widgets/"Flight Tracker.widget"'
        )
        print(
            "  python examples/run_widget.py "
            'mcp_chatkit_widget/widgets/"Create Event.widget"'
        )
        sys.exit(1)

    widget_path = sys.argv[1]
    await run_widget_example(widget_path)


if __name__ == "__main__":
    asyncio.run(main())
