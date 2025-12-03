#!/usr/bin/env python3
"""
Query IDA Pro Functions via RPC

ADR Note: Direct RPC client for IDA Pro. Uses the same RPC interface
that ida-pro-mcp uses, allowing programmatic access to IDA Pro data.
"""

import requests
import json
import sys
from typing import List, Dict, Any, Optional

class IDAProRPC:
    """
    IDA Pro RPC Client
    
    ADR Note: Connects to IDA Pro's RPC server (default port 13337).
    Uses JSON-RPC 2.0 protocol to communicate with IDA Pro plugin.
    """
    
    def __init__(self, rpc_url: str = "http://127.0.0.1:13337"):
        """
        Initialize RPC client
        
        Args:
            rpc_url: IDA Pro RPC server URL
        """
        self.rpc_url = rpc_url
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
        })
    
    def _call_rpc(self, method: str, params: Optional[List[Any]] = None) -> Any:
        """
        Make JSON-RPC 2.0 call to IDA Pro
        
        ADR Note: Standard JSON-RPC 2.0 protocol. IDA Pro plugin uses /mcp endpoint.
        Parameters are passed as a list (not dict) matching ida-pro-mcp format.
        """
        import http.client
        from urllib.parse import urlparse
        
        # Parse URL
        parsed = urlparse(self.rpc_url)
        host = parsed.hostname or "127.0.0.1"
        port = parsed.port or 13337
        
        # Create connection
        conn = http.client.HTTPConnection(host, port)
        
        # Build JSON-RPC request
        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "id": 1
        }
        
        # Parameters as list (not dict) - matching ida-pro-mcp format
        if params is not None:
            payload["params"] = params
        
        try:
            # POST to /mcp endpoint
            conn.request("POST", "/mcp", json.dumps(payload), {
                "Content-Type": "application/json"
            })
            response = conn.getresponse()
            data = json.loads(response.read().decode())
            
            if "error" in data:
                error = data["error"]
                code = error.get("code", -1)
                message = error.get("message", "Unknown error")
                error_msg = f"RPC Error {code}: {message}"
                if "data" in error:
                    error_msg += f"\n{error['data']}"
                raise Exception(error_msg)
            
            result = data.get("result")
            # Handle empty responses
            if result is None:
                result = {}
            
            return result
        
        except http.client.HTTPException as e:
            raise Exception(f"HTTP error: {e}")
        except ConnectionRefusedError:
            raise Exception(f"Cannot connect to IDA Pro RPC server at {host}:{port}. "
                          "Make sure IDA Pro is running with the MCP plugin loaded.")
        except Exception as e:
            raise Exception(f"RPC call failed: {e}")
        finally:
            conn.close()
    
    def check_connection(self) -> bool:
        """Check if IDA Pro RPC server is accessible"""
        try:
            # Try get_metadata which should always work if connected
            result = self._call_rpc("get_metadata")
            return result is not None
        except Exception as e:
            print(f"Connection check failed: {e}")
            return False
    
    def get_metadata(self) -> Dict[str, Any]:
        """Get IDA Pro database metadata"""
        result = self._call_rpc("get_metadata")
        if isinstance(result, dict):
            return result
        return {"module": "unknown", "result": result}
    
    def list_functions(self, offset: int = 0, count: int = 0) -> Dict[str, Any]:
        """
        List all functions in the IDA Pro database (paginated)
        
        Args:
            offset: Offset to start listing from (start at 0)
            count: Number of functions to list (100 is a good default, 0 means remainder)
        
        Returns:
            Dictionary with 'items' (list of functions) and pagination info
        """
        result = self._call_rpc("list_functions", [offset, count])
        if isinstance(result, dict):
            return result
        return {"items": [], "total": 0}
    
    def get_function_by_address(self, address: int) -> Dict[str, Any]:
        """Get function information by address"""
        result = self._call_rpc("get_function_by_address", [address])
        if isinstance(result, dict):
            return result
        return {"address": address, "result": result}
    
    def get_function_by_name(self, name: str) -> Dict[str, Any]:
        """Get function information by name"""
        result = self._call_rpc("get_function_by_name", [name])
        if isinstance(result, dict):
            return result
        return {"name": name, "result": result}
    
    def get_current_address(self) -> int:
        """Get current cursor address in IDA Pro"""
        result = self._call_rpc("get_current_address", [])
        if isinstance(result, (int, str)):
            if isinstance(result, str):
                return int(result, 16) if result.startswith("0x") else int(result, 16)
            return result
        return 0
    
    def get_current_function(self) -> Optional[Dict[str, Any]]:
        """Get function at current cursor position"""
        result = self._call_rpc("get_current_function", [])
        if isinstance(result, dict):
            return result
        return None
    
    def decompile_function(self, address: Optional[int] = None) -> str:
        """
        Decompile function at address (or current address if None)
        
        Args:
            address: Function address (hex string or int), or None for current
        
        Returns:
            Decompiled C-like code
        """
        params = []
        if address is not None:
            if isinstance(address, str):
                # Convert hex string to int
                address = int(address, 16) if address.startswith("0x") else int(address, 16)
            params.append(address)
        
        result = self._call_rpc("decompile_function", params if params else [])
        if isinstance(result, str):
            return result
        return str(result) if result else ""


def format_function_list(result: Dict[str, Any]) -> str:
    """Format function list for display"""
    # Handle both "data" and "items" keys
    items = result.get("data", result.get("items", []))
    next_offset = result.get("next_offset")
    
    if not items:
        return "No functions found in IDA Pro database."
    
    total_info = ""
    if next_offset is not None:
        total_info = f" (showing {len(items)}, next_offset: {next_offset})"
    else:
        total_info = f" (showing {len(items)})"
    
    lines = [f"Found {len(items)} functions{total_info}:\n"]
    lines.append(f"{'Address':<12} {'Name':<50} {'Size':<10}")
    lines.append("-" * 80)
    
    for func in items:
        addr = func.get("address", "N/A")
        if isinstance(addr, int):
            addr = f"0x{addr:X}"
        elif isinstance(addr, str) and not addr.startswith("0x"):
            addr = f"0x{addr}"
        
        name = func.get("name", "unknown")
        size = func.get("size", "0")
        if isinstance(size, int):
            size = f"0x{size:X}"
        elif isinstance(size, str) and not size.startswith("0x"):
            size = f"0x{size}"
        
        lines.append(f"{addr:<12} {name:<50} {size:<10}")
    
    return "\n".join(lines)


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Query IDA Pro functions via RPC")
    parser.add_argument("--rpc-url", default="http://127.0.0.1:13337",
                       help="IDA Pro RPC server URL")
    parser.add_argument("--offset", type=int, default=0,
                       help="Offset to start listing from (default: 0)")
    parser.add_argument("--count", type=int, default=0,
                       help="Number of functions to list (default: 0 = all, 100 is a good default)")
    parser.add_argument("--address", type=str,
                       help="Get specific function by address (hex)")
    parser.add_argument("--name", type=str,
                       help="Get specific function by name")
    parser.add_argument("--decompile", action="store_true",
                       help="Decompile function (use with --address or current)")
    parser.add_argument("--current", action="store_true",
                       help="Get current function at cursor")
    parser.add_argument("--metadata", action="store_true",
                       help="Show database metadata")
    
    args = parser.parse_args()
    
    # Create RPC client
    rpc = IDAProRPC(args.rpc_url)
    
    # Check connection
    print("Connecting to IDA Pro RPC server...")
    if not rpc.check_connection():
        print("❌ Failed to connect to IDA Pro RPC server")
        print("   Make sure:")
        print("   1. IDA Pro is running")
        print("   2. MCP plugin is loaded")
        print("   3. RPC server is running on port 13337")
        sys.exit(1)
    
    print("✅ Connected to IDA Pro\n")
    
    try:
        # Show metadata if requested
        if args.metadata:
            metadata = rpc.get_metadata()
            print("Database Metadata:")
            print(json.dumps(metadata, indent=2))
            print()
        
        # Get current function
        if args.current:
            current_addr = rpc.get_current_address()
            print(f"Current address: 0x{current_addr:X}")
            func = rpc.get_current_function()
            if func:
                print(f"Current function: {func.get('name', 'unknown')} @ 0x{func.get('address', 0):X}")
            else:
                print("No function at current address")
            print()
        
        # Get specific function by address
        if args.address:
            addr = int(args.address, 16) if args.address.startswith("0x") else int(args.address, 16)
            func = rpc.get_function_by_address(addr)
            print(f"Function at 0x{addr:X}:")
            print(json.dumps(func, indent=2))
            print()
            
            if args.decompile:
                code = rpc.decompile_function(addr)
                print("Decompiled code:")
                print(code)
                print()
        
        # Get specific function by name
        elif args.name:
            func = rpc.get_function_by_name(args.name)
            print(f"Function '{args.name}':")
            print(json.dumps(func, indent=2))
            print()
            
            if args.decompile and func:
                addr = func.get("address", 0)
                code = rpc.decompile_function(addr)
                print("Decompiled code:")
                print(code)
                print()
        
        # Decompile current function
        elif args.decompile and not args.address:
            code = rpc.decompile_function()
            print("Decompiled code (current function):")
            print(code)
            print()
        
        # List all functions (default)
        else:
            print("Fetching functions from IDA Pro...")
            try:
                result = rpc.list_functions(offset=args.offset, count=args.count)
                print(format_function_list(result))
            except Exception as e:
                print(f"Error fetching functions: {e}")
                print("\nTrying to get metadata to check database status...")
                try:
                    metadata = rpc.get_metadata()
                    print("Database metadata:")
                    print(json.dumps(metadata, indent=2))
                except Exception as e2:
                    print(f"Could not get metadata: {e2}")
    
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

