#!/usr/bin/env python3
"""
Format mcp.json file properly
Fixes malformed JSON and ensures proper formatting
"""

import json
import sys
from pathlib import Path

def format_mcp_json(mcp_path: Path):
    """Format mcp.json file"""
    if not mcp_path.exists():
        print(f"Error: {mcp_path} not found")
        return 1
    
    # Read existing config
    try:
        with open(mcp_path, 'r', encoding='utf-8-sig') as f:
            content = f.read()
            # Try to parse
            config = json.loads(content)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {mcp_path}")
        print(f"  {e}")
        return 1
    except Exception as e:
        print(f"Error reading file: {e}")
        return 1
    
    # Ensure mcpServers exists
    if "mcpServers" not in config:
        config["mcpServers"] = {}
    
    # Write back with proper formatting
    try:
        with open(mcp_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        print(f"✅ Formatted {mcp_path}")
        return 0
    except Exception as e:
        print(f"Error writing file: {e}")
        return 1

if __name__ == "__main__":
    if len(sys.argv) > 1:
        mcp_path = Path(sys.argv[1])
    else:
        # Default to user's .cursor/mcp.json
        mcp_path = Path.home() / ".cursor" / "mcp.json"
    
    sys.exit(format_mcp_json(mcp_path))

