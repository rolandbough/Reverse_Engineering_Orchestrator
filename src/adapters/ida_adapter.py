"""
IDA Pro Adapter Implementation

ADR Note: Uses direct RPC client to communicate with IDA Pro's RPC server.
This provides full control and avoids dependency on external MCP servers.
Based on query_ida_functions.py RPC client implementation.
"""

import logging
from pathlib import Path
from typing import Optional, Dict, Any

from .base_adapter import BaseAdapter, AdapterResult, BreakpointType
from ..utils.ida_rpc_client import IDAProRPCClient

logger = logging.getLogger(__name__)


class IDAAdapter(BaseAdapter):
    """
    Adapter for IDA Pro reverse engineering tool
    
    ADR Note: Uses direct RPC client to communicate with IDA Pro's RPC server.
    Requires IDA Pro to be running with MCP plugin loaded. Works with
    already-loaded databases (binary loading happens via GUI).
    """
    
    def __init__(self, install_path: Path, rpc_url: str = "http://127.0.0.1:13337"):
        """
        Initialize IDA adapter
        
        Args:
            install_path: IDA Pro installation path (for reference)
            rpc_url: IDA Pro RPC server URL
        """
        super().__init__(install_path)
        self.rpc_client = IDAProRPCClient(rpc_url)
        self.current_database: Optional[str] = None
    
    def connect(self) -> AdapterResult:
        """
        Connect to IDA Pro via RPC
        
        ADR Note: Tests RPC connection. IDA Pro must be running with
        MCP plugin loaded for this to work.
        """
        try:
            if not self.rpc_client.check_connection():
                return AdapterResult(
                    success=False,
                    error="Cannot connect to IDA Pro RPC server. Make sure IDA Pro is running with MCP plugin loaded."
                )
            
            # Get metadata to verify connection
            metadata = self.rpc_client.get_metadata()
            self.current_database = metadata.get("module", "unknown")
            
            self.is_connected = True
            return AdapterResult(
                success=True,
                data={
                    "message": "Connected to IDA Pro",
                    "database": self.current_database,
                    "metadata": metadata
                }
            )
        except Exception as e:
            return AdapterResult(
                success=False,
                error=f"Failed to connect to IDA Pro: {e}"
            )
    
    def disconnect(self) -> AdapterResult:
        """Disconnect from IDA Pro"""
        self.is_connected = False
        self.current_database = None
        return AdapterResult(success=True, data={"message": "Disconnected"})
    
    def load_binary(self, binary_path: Path, project_name: Optional[str] = None) -> AdapterResult:
        """
        Load binary in IDA Pro
        
        ADR Note: IDA Pro binary loading typically happens through GUI.
        This method checks if the binary is already loaded. For programmatic
        loading, would need IDA Pro command-line mode or scripting.
        """
        # Check if binary is already loaded by comparing paths
        try:
            metadata = self.rpc_client.get_metadata()
            current_path = metadata.get("path", "")
            
            if str(binary_path) in current_path or current_path in str(binary_path):
                self.current_database = metadata.get("module", "unknown")
                return AdapterResult(
                    success=True,
                    data={
                        "message": "Binary already loaded",
                        "database": self.current_database,
                        "path": current_path
                    }
                )
            else:
                return AdapterResult(
                    success=False,
                    error=f"Binary not loaded. Current database: {metadata.get('module', 'unknown')}. "
                          "Please load the binary in IDA Pro GUI first."
                )
        except Exception as e:
            return AdapterResult(
                success=False,
                error=f"Failed to check binary status: {e}"
            )
    
    def decompile_function(self, address: int) -> AdapterResult:
        """
        Decompile function using Hex-Rays decompiler
        
        ADR Note: Uses IDA Pro RPC decompile_function method.
        Requires Hex-Rays decompiler license.
        IDA Pro RPC expects address as hex string.
        """
        try:
            # IDA Pro RPC expects address as hex string
            addr_str = f"0x{address:X}"
            code = self.rpc_client._call_rpc("decompile_function", [addr_str])
            if isinstance(code, str):
                return AdapterResult(
                    success=True,
                    data={
                        "address": addr_str,
                        "code": code
                    }
                )
            return AdapterResult(
                success=False,
                error="Unexpected response format from decompile_function"
            )
        except Exception as e:
            return AdapterResult(
                success=False,
                error=f"Decompilation failed: {e}"
            )
    
    def set_breakpoint(self, address: int, bp_type: BreakpointType) -> AdapterResult:
        """
        Set breakpoint in IDA Pro debugger
        
        ADR Note: IDA Pro RPC may not support breakpoint setting directly.
        This would require unsafe RPC methods or IDAPython scripting.
        For now, returns not implemented.
        """
        # Check if unsafe methods are available
        # Most breakpoint operations require unsafe RPC access
        return AdapterResult(
            success=False,
            error="Breakpoint setting requires unsafe RPC methods. "
                  "Use IDA Pro GUI or enable unsafe mode in ida-pro-mcp."
        )
    
    def read_memory(self, address: int, size: int) -> AdapterResult:
        """
        Read memory from binary (static analysis)
        
        ADR Note: Uses read_memory_bytes RPC method. This reads from
        the loaded binary file, not runtime memory. For runtime memory,
        need to be debugging a process.
        """
        try:
            data = self.rpc_client.read_memory_bytes(address, size)
            return AdapterResult(
                success=True,
                data={
                    "address": f"0x{address:X}",
                    "size": size,
                    "data": data.hex(),
                    "note": "Reading from binary file, not runtime memory"
                }
            )
        except Exception as e:
            return AdapterResult(
                success=False,
                error=f"Memory read failed: {e}"
            )
    
    def get_function_at(self, address: int) -> AdapterResult:
        """Get function information at address"""
        try:
            func = self.rpc_client.get_function_by_address(address)
            return AdapterResult(
                success=True,
                data=func
            )
        except Exception as e:
            return AdapterResult(
                success=False,
                error=f"Failed to get function info: {e}"
            )
    
    def find_references(self, address: int) -> AdapterResult:
        """Find references to address"""
        try:
            refs = self.rpc_client.get_xrefs_to(address)
            return AdapterResult(
                success=True,
                data={
                    "address": f"0x{address:X}",
                    "references": refs,
                    "count": len(refs)
                }
            )
        except Exception as e:
            return AdapterResult(
                success=False,
                error=f"Failed to find references: {e}"
            )

