#!/usr/bin/env python3
"""
Test IDA Pro MCP Connection

ADR Note: Simple test to verify IDA Pro RPC server is accessible.
This doesn't test the full MCP integration, just the underlying RPC.
"""

import requests
import json

def test_ida_rpc():
    """Test if IDA Pro RPC server is responding"""
    rpc_url = "http://127.0.0.1:13337"
    
    try:
        # Try a simple RPC call
        # Note: Actual RPC protocol may differ, this is just a connectivity test
        response = requests.get(rpc_url, timeout=2)
        print(f"✅ IDA Pro RPC server is responding")
        print(f"   Status: {response.status_code}")
        return True
    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to IDA Pro RPC server at {rpc_url}")
        print("   → Make sure IDA Pro is running with the MCP plugin loaded")
        return False
    except requests.exceptions.Timeout:
        print(f"⚠️  Connection to IDA Pro RPC server timed out")
        return False
    except Exception as e:
        print(f"⚠️  Error testing connection: {e}")
        return False

if __name__ == "__main__":
    print("Testing IDA Pro RPC Connection...")
    print("=" * 60)
    test_ida_rpc()
    print()
    print("Note: This only tests RPC connectivity.")
    print("Full MCP integration requires Cursor to be restarted.")

