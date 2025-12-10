"""Server module."""

from argparse import ArgumentParser
from pathlib import Path
from .server import register_widget_tools, server


def main() -> None:  # pragma: no cover
    """Start the MCP server."""
    parser = ArgumentParser(description="MCP ChatKit widget server")
    parser.add_argument(
        "--widgets-dir",
        type=Path,
        required=True,
        help="Path to the curated widgets directory that contains .widget files",
    )
    args, _ = parser.parse_known_args()

    register_widget_tools(args.widgets_dir)
    server.run()
