"""Tools for UI components."""

from pathlib import Path
from fastmcp import FastMCP
from .tooling import (
    _create_widget_tool_function,
    _sanitize_tool_name,
    _to_camel_case,
    generate_widget_tools,
)
from .widget_loader import load_widgets


server = FastMCP("mcp-chatkit-widget")

DEFAULT_WIDGETS_DIR = Path(__file__).resolve().parent / "widgets"


def register_widget_tools(widgets_dir: Path) -> None:
    """Discover widget definitions and register FastMCP tools."""
    widget_defs = load_widgets(widgets_dir)
    generate_widget_tools(server, widget_defs)


__all__ = [
    "DEFAULT_WIDGETS_DIR",
    "generate_widget_tools",
    "_create_widget_tool_function",
    "_sanitize_tool_name",
    "_to_camel_case",
    "register_widget_tools",
    "server",
]


if __name__ == "__main__":  # pragma: no cover
    import asyncio

    async def list_tools() -> None:
        """List all registered tools."""
        print("Registered tools:")
        tools = await server.get_tools()
        for tool_name in sorted(tools):
            print(f"  - {tool_name}")
            tool = await server.get_tool(tool_name)
            if tool and tool.description:
                print(f"    {tool.description.strip().split(chr(10))[0]}")

    asyncio.run(list_tools())
