"""Run any widget tool example via the FastMCP client.

Usage:
    python examples/run_widget/run_widget.py <path/to/widget.widget>
    python examples/run_widget/run_widget.py \
        examples/widgets/"Flight Tracker.widget"
"""

from __future__ import annotations
import asyncio
import json
import sys
from pathlib import Path
from typing import Any
from fastmcp import Client


try:
    from examples.run_widget.input_data import extract_input_data_from_preview
    from examples.run_widget.output_processing import (
        display_widget_payload,
        parse_tool_result,
    )
except ModuleNotFoundError:
    # Support running as ``python examples/run_widget/run_widget.py`` where the
    # package name is not importable.
    from input_data import extract_input_data_from_preview  # type: ignore
    from output_processing import (  # type: ignore
        display_widget_payload,
        parse_tool_result,
    )
from mcp_chatkit_widget.server import _sanitize_tool_name
from mcp_chatkit_widget.widget_loader import load_widget


def _build_mcp_config(widgets_dir: Path) -> dict[str, Any]:
    """Create the FastMCP configuration for running widgets from ``widgets_dir``."""
    return {
        "mcpServers": {
            "chatkit": {
                "transport": "stdio",
                "command": "mcp-chatkit-widget",
                "args": ["--widgets-dir", str(widgets_dir)],
            }
        }
    }


def _handle_missing_widget(widget_path: Path) -> None:
    """Handle case where widget file is not found."""
    print(f"Error: Widget file not found at {widget_path}")

    widgets_dir = Path(__file__).parent.parent / "widgets"
    if widgets_dir.exists():
        print(f"\nAvailable widgets in {widgets_dir}:")
        for widget_file in sorted(widgets_dir.glob("*.widget")):
            print(f"  - {widget_file}")
    sys.exit(1)


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

    tool_name = _sanitize_tool_name(widget_name)
    widgets_dir = widget_path.parent
    client_config = _build_mcp_config(widgets_dir)

    async with Client(client_config) as client:
        result = await client.call_tool(tool_name, input_data)

        print("\nTool Output (Raw JSON):")
        print("=" * 80)

        widget_dict = parse_tool_result(result)
        print("=" * 80)

        if widget_dict:
            display_widget_payload(widget_dict, widget_name)
        else:
            print("\nNo widget data found in result.")

        print("=" * 80)
        print(f"\n{widget_name} example completed successfully!")


async def main() -> None:
    """Main entry point for the script."""
    if len(sys.argv) < 2:
        print("Usage: python examples/run_widget/run_widget.py <widget_file_path>")
        print("\nExample:")
        print(
            "  python examples/run_widget/run_widget.py "
            'examples/widgets/"Flight Tracker.widget"'
        )
        print(
            "  python examples/run_widget/run_widget.py "
            'examples/widgets/"Create Event.widget"'
        )
        sys.exit(1)

    widget_path = sys.argv[1]
    await run_widget_example(widget_path)


if __name__ == "__main__":
    asyncio.run(main())
