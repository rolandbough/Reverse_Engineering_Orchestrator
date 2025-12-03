"""
MCP Server Entry Point

ADR Note: Allows running server as module: python -m src.mcp_server
This is the standard way to run the MCP server for Cursor integration.
"""

import sys
from .server import MCPServer

def main():
    """Main entry point"""
    server = MCPServer()
    try:
        server.run()
    except KeyboardInterrupt:
        print("Server stopped by user", file=sys.stderr)
        sys.exit(0)
    except Exception as e:
        print(f"Server error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()

