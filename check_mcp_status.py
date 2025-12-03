#!/usr/bin/env python3
"""
Check MCP Server Status

ADR Note: Simple script to verify IDA Pro MCP setup and connection status.
"""

import sys
import subprocess
from pathlib import Path

def check_plugin_installed():
    """Check if IDA Pro plugin is installed"""
    plugin_path = Path.home() / "AppData" / "Roaming" / "Hex-Rays" / "IDA Pro" / "plugins" / "mcp-plugin.py"
    if plugin_path.exists():
        print(f"✅ IDA Pro plugin installed: {plugin_path}")
        return True
    else:
        print(f"❌ IDA Pro plugin not found: {plugin_path}")
        return False

def check_cursor_config():
    """Check if Cursor MCP config includes ida-pro-mcp"""
    config_path = Path.home() / ".cursor" / "mcp.json"
    if config_path.exists():
        try:
            import json
            with open(config_path, 'r') as f:
                config = json.load(f)
                if "ida-pro-mcp" in config.get("mcpServers", {}):
                    print(f"✅ Cursor MCP config includes ida-pro-mcp")
                    return True
                else:
                    print(f"❌ Cursor MCP config missing ida-pro-mcp")
                    return False
        except Exception as e:
            print(f"❌ Error reading Cursor config: {e}")
            return False
    else:
        print(f"❌ Cursor MCP config not found: {config_path}")
        return False

def check_ida_running():
    """Check if IDA Pro is running"""
    try:
        import psutil
        for proc in psutil.process_iter(['name']):
            try:
                name = proc.info['name'].lower()
                if 'ida' in name and ('exe' in name or 'app' in name):
                    print(f"✅ IDA Pro is running (PID: {proc.pid})")
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        print("⚠️  IDA Pro is not running")
        print("   → Start IDA Pro to activate the MCP plugin")
        return False
    except ImportError:
        print("⚠️  psutil not available, cannot check IDA Pro process")
        return None

def check_mcp_server():
    """Check if ida-pro-mcp command is available"""
    try:
        result = subprocess.run(
            ["ida-pro-mcp", "--help"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            print("✅ ida-pro-mcp command is available")
            return True
        else:
            print("❌ ida-pro-mcp command failed")
            return False
    except FileNotFoundError:
        print("❌ ida-pro-mcp command not found")
        print("   → Run: pip install --upgrade ida-pro-mcp")
        return False
    except Exception as e:
        print(f"❌ Error checking ida-pro-mcp: {e}")
        return False

def main():
    print("=" * 60)
    print("IDA Pro MCP Server Status Check")
    print("=" * 60)
    print()
    
    results = {
        "Plugin Installed": check_plugin_installed(),
        "Cursor Config": check_cursor_config(),
        "MCP Command": check_mcp_server(),
        "IDA Running": check_ida_running(),
    }
    
    print()
    print("=" * 60)
    print("Summary")
    print("=" * 60)
    
    all_setup = all(v for k, v in results.items() if k != "IDA Running" and v is not None)
    ida_running = results.get("IDA Running", False)
    
    if all_setup:
        print("✅ Setup is complete!")
        if ida_running:
            print("✅ IDA Pro is running - MCP server should be active")
            print()
            print("Next steps:")
            print("1. Restart Cursor to load MCP configuration")
            print("2. In Cursor, the AI should be able to interact with IDA Pro")
        else:
            print("⚠️  IDA Pro is not running")
            print()
            print("To activate:")
            print("1. Start IDA Pro (plugin will load automatically)")
            print("2. Restart Cursor to connect to the MCP server")
            print("3. The MCP server will start when Cursor connects")
    else:
        print("❌ Setup is incomplete")
        print()
        print("Missing components:")
        for key, value in results.items():
            if value is False:
                print(f"  - {key}")
    
    print()
    print("=" * 60)

if __name__ == "__main__":
    main()


