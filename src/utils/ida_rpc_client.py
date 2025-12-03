"""
IDA Pro RPC Client (Shared)

ADR Note: Shared RPC client for IDA Pro communication. Used by both
the query script and the IDA adapter. Provides unified interface to
IDA Pro's RPC server.
"""

import json
import http.client
from urllib.parse import urlparse
from typing import Any, Optional, List, Dict


class IDAProRPCClient:
    """
    IDA Pro RPC Client
    
    ADR Note: Connects to IDA Pro's RPC server (default port 13337).
    Uses JSON-RPC 2.0 protocol to communicate with IDA Pro plugin.
    This is the shared implementation used by adapters and tools.
    """
    
    def __init__(self, rpc_url: str = "http://127.0.0.1:13337"):
        """
        Initialize RPC client
        
        Args:
            rpc_url: IDA Pro RPC server URL
        """
        self.rpc_url = rpc_url
        parsed = urlparse(rpc_url)
        self.host = parsed.hostname or "127.0.0.1"
        self.port = parsed.port or 13337
        self._request_id = 1
    
    def _call_rpc(self, method: str, params: Optional[List[Any]] = None) -> Any:
        """
        Make JSON-RPC 2.0 call to IDA Pro
        
        ADR Note: Standard JSON-RPC 2.0 protocol. IDA Pro plugin uses /mcp endpoint.
        Parameters are passed as a list (not dict) matching ida-pro-mcp format.
        """
        # Build JSON-RPC request
        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "id": self._request_id
        }
        self._request_id += 1
        
        # Parameters as list (not dict) - matching ida-pro-mcp format
        if params is not None:
            payload["params"] = params
        
        # Create connection
        conn = http.client.HTTPConnection(self.host, self.port)
        
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
            raise Exception(f"Cannot connect to IDA Pro RPC server at {self.host}:{self.port}. "
                          "Make sure IDA Pro is running with the MCP plugin loaded.")
        except Exception as e:
            raise Exception(f"RPC call failed: {e}")
        finally:
            conn.close()
    
    def check_connection(self) -> bool:
        """Check if IDA Pro RPC server is accessible"""
        try:
            result = self._call_rpc("get_metadata")
            return result is not None
        except Exception:
            return False
    
    def get_metadata(self) -> Dict[str, Any]:
        """Get IDA Pro database metadata"""
        result = self._call_rpc("get_metadata")
        if isinstance(result, dict):
            return result
        return {"module": "unknown", "result": result}
    
    def list_functions(self, offset: int = 0, count: int = 0) -> Dict[str, Any]:
        """List functions (paginated)"""
        return self._call_rpc("list_functions", [offset, count])
    
    def get_function_by_address(self, address: int) -> Dict[str, Any]:
        """Get function by address"""
        return self._call_rpc("get_function_by_address", [address])
    
    def get_function_by_name(self, name: str) -> Dict[str, Any]:
        """Get function by name"""
        return self._call_rpc("get_function_by_name", [name])
    
    def decompile_function(self, address: Optional[int] = None) -> str:
        """
        Decompile function at address
        
        ADR Note: IDA Pro RPC expects address as hex string (e.g., "0x401000"),
        not integer. This method converts int to hex string.
        """
        if address is not None:
            # IDA Pro RPC expects hex string
            addr_str = f"0x{address:X}"
            params = [addr_str]
        else:
            params = []
        result = self._call_rpc("decompile_function", params)
        if isinstance(result, str):
            return result
        return str(result) if result else ""
    
    def get_xrefs_to(self, address: int) -> List[Dict[str, Any]]:
        """Get cross-references to address"""
        result = self._call_rpc("get_xrefs_to", [address])
        if isinstance(result, list):
            return result
        return []
    
    def read_memory_bytes(self, address: int, size: int) -> bytes:
        """Read memory bytes"""
        result = self._call_rpc("read_memory_bytes", [address, size])
        if isinstance(result, str):
            # May be hex string or base64
            import base64
            try:
                return base64.b64decode(result)
            except:
                # Try hex
                return bytes.fromhex(result.replace("0x", ""))
        return result

