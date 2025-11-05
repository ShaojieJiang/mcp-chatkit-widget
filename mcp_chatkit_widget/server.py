"""Tools for UI components."""

from mcp.server.fastmcp import FastMCP


server = FastMCP("mcp-chatkit-widget")



if __name__ == "__main__":  # pragma: no cover
    server.run()
