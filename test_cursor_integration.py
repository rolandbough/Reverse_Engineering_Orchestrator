#!/usr/bin/env python3
"""
Test Cursor Integration

Verifies that the MCP server configuration is correct and can be used in Cursor.
"""

import sys
import json
from pathlib import Path

def check_cursor_config():
    """Check if Cursor MCP config includes our server"""
    config_path = Path.home() / ".cursor" / "mcp.json"
    
    if not config_path.exists():
        print("❌ Cursor MCP config not found")
        print(f"   Expected: {config_path}")
        print("\n   Run: .\\setup_cursor_mcp.ps1")
        return False
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        servers = config.get("mcpServers", {})
        
        if "reverse-engineering-orchestrator" in servers:
            server_config = servers["reverse-engineering-orchestrator"]
            print("✅ Reverse Engineering Orchestrator found in Cursor config")
            print(f"   Command: {server_config.get('command', 'N/A')}")
            print(f"   Args: {server_config.get('args', [])}")
            print(f"   CWD: {server_config.get('cwd', 'N/A')}")
            return True
        else:
            print("❌ Reverse Engineering Orchestrator not found in Cursor config")
            print(f"   Available servers: {list(servers.keys())}")
            print("\n   Run: .\\setup_cursor_mcp.ps1")
            return False
    
    except json.JSONDecodeError as e:
        print(f"❌ Error parsing mcp.json: {e}")
        return False
    except Exception as e:
        print(f"❌ Error reading config: {e}")
        return False

def check_python_path():
    """Check if Python path in config is valid"""
    config_path = Path.home() / ".cursor" / "mcp.json"
    
    if not config_path.exists():
        return False
    
    try:
        with open(config_path, 'r', encoding='utf-8-sig') as f:
            config = json.load(f)
        
        server_config = config.get("mcpServers", {}).get("reverse-engineering-orchestrator")
        if not server_config:
            return False
        
        python_path = Path(server_config.get("command", ""))
        if python_path.exists():
            print(f"✅ Python executable found: {python_path}")
            return True
        else:
            print(f"❌ Python executable not found: {python_path}")
            return False
    
    except Exception:
        return False

def check_project_path():
    """Check if project path in config is valid"""
    config_path = Path.home() / ".cursor" / "mcp.json"
    
    if not config_path.exists():
        return False
    
    try:
        with open(config_path, 'r', encoding='utf-8-sig') as f:
            config = json.load(f)
        
        server_config = config.get("mcpServers", {}).get("reverse-engineering-orchestrator")
        if not server_config:
            return False
        
        project_path = Path(server_config.get("cwd", ""))
        if project_path.exists() and (project_path / "src" / "mcp_server").exists():
            print(f"✅ Project path valid: {project_path}")
            return True
        else:
            print(f"❌ Project path invalid: {project_path}")
            return False
    
    except Exception:
        return False

def main():
    print("Testing Cursor Integration\n")
    print("=" * 50)
    
    results = []
    
    # Check 1: Config file exists and contains our server
    print("\n1. Checking Cursor MCP configuration...")
    results.append(("Config", check_cursor_config()))
    
    # Check 2: Python path is valid
    print("\n2. Checking Python executable...")
    results.append(("Python", check_python_path()))
    
    # Check 3: Project path is valid
    print("\n3. Checking project path...")
    results.append(("Project", check_project_path()))
    
    # Summary
    print("\n" + "=" * 50)
    print("Summary:")
    all_passed = all(result[1] for result in results)
    
    for name, passed in results:
        status = "✅" if passed else "❌"
        print(f"  {status} {name}")
    
    if all_passed:
        print("\n✅ All checks passed! Cursor integration is ready.")
        print("\nNext steps:")
        print("1. Restart Cursor completely")
        print("2. The MCP server should start automatically")
        print("3. Try: 'What reverse engineering tools are available?'")
        return 0
    else:
        print("\n❌ Some checks failed. Run .\\setup_cursor_mcp.ps1 to fix.")
        return 1

if __name__ == "__main__":
    sys.exit(main())

