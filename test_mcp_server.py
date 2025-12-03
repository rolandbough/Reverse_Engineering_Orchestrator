#!/usr/bin/env python3
"""
Test MCP Server

Basic test to verify MCP server can start and initialize adapters.
"""

import sys
import asyncio
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.mcp_server.config import ServerConfig
from src.mcp_server.protocol import MCPProtocolHandler
from src.tool_detection import ToolDetector

async def test_server():
    print("Testing MCP Server Initialization\n")
    
    # Create config
    config = ServerConfig.from_env()
    print(f"Server: {config.server_name} v{config.server_version}")
    
    # Create tool detector
    detector = ToolDetector()
    detected = detector.detect_available()
    
    if detected:
        print(f"✅ Tool detected: {detected.tool_type.value}")
        if detected.install_path:
            print(f"   Path: {detected.install_path}")
    else:
        print("⚠️  No tools detected")
    
    # Create protocol handler
    print("\nCreating MCP Protocol Handler...")
    handler = MCPProtocolHandler(config, detector)
    
    # Initialize adapter
    print("Initializing adapter...")
    init_result = await handler._initialize_adapter()
    
    if init_result.get("success"):
        print("✅ Adapter initialized successfully")
        
        # Get tool status
        status = handler._get_tool_status()
        print(f"\nTool Status:")
        print(f"  Adapter: {status.get('adapter', {}).get('tool_name', 'unknown')}")
        print(f"  Connected: {status.get('connected', False)}")
    else:
        print(f"❌ Adapter initialization failed: {init_result.get('error')}")
        return 1
    
    print("\n✅ MCP Server test passed!")
    return 0

if __name__ == "__main__":
    try:
        result = asyncio.run(test_server())
        sys.exit(result)
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

