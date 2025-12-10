"""Server module."""

from argparse import ArgumentParser
from pathlib import Path
from mcp_chatkit_widget.rendering import render_widget_definition
from mcp_chatkit_widget.server import (
    generate_widget_tools,
    register_widget_tools,
    server,
)
from mcp_chatkit_widget.widget_loader import load_widget, load_widgets


def main() -> None:  # pragma: no cover
    """Start the MCP server."""
    parser = ArgumentParser(description="MCP ChatKit widget server")
    parser.add_argument(
        "--widgets-dir",
        type=Path,
        required=True,
        help="Path to the curated widgets directory that contains .widget files (e.g., https://github.com/ShaojieJiang/mcp-chatkit-widget/tree/main/examples/widgets)",
    )
    args, _ = parser.parse_known_args()

    register_widget_tools(args.widgets_dir)
    server.run()


__all__ = [
    "generate_widget_tools",
    "load_widget",
    "load_widgets",
    "render_widget_definition",
    "register_widget_tools",
    "server",
]
