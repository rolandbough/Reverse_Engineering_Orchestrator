"""
Base Adapter Interface

ADR Note: Adapter pattern provides unified interface for different RE tools.
This allows MCP tools to work with either IDA Pro or Ghidra transparently.
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Optional, Dict, Any, List
from pathlib import Path
from pydantic import BaseModel


class BreakpointType(str, Enum):
    """Types of breakpoints supported"""
    SOFTWARE = "software"
    HARDWARE = "hardware"
    WRITE = "write"  # Hardware write watchpoint
    READ = "read"    # Hardware read watchpoint
    EXECUTE = "execute"  # Hardware execute breakpoint


class AdapterResult(BaseModel):
    """
    Standard result format from adapter operations
    
    ADR Note: Unified result format allows consistent error handling
    and response formatting across different tools.
    """
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    tool_specific: Optional[Dict[str, Any]] = None  # Tool-specific metadata


class BaseAdapter(ABC):
    """
    Base class for reverse engineering tool adapters
    
    ADR Note: All tool adapters must implement this interface.
    This ensures MCP tools can work with any supported tool.
    """
    
    def __init__(self, install_path: Path):
        """
        Initialize adapter
        
        Args:
            install_path: Path to tool installation directory
        """
        self.install_path = install_path
        self.is_connected = False
    
    @abstractmethod
    def connect(self) -> AdapterResult:
        """
        Connect to the tool
        
        ADR Note: Connection may mean different things for different tools:
        - Ghidra: Verify pyGhidraRun is available
        - IDA Pro: Check if IDA is running or can be launched
        """
        pass
    
    @abstractmethod
    def disconnect(self) -> AdapterResult:
        """Disconnect from the tool"""
        pass
    
    @abstractmethod
    def load_binary(self, binary_path: Path, project_name: Optional[str] = None) -> AdapterResult:
        """
        Load a binary file for analysis
        
        Args:
            binary_path: Path to binary file
            project_name: Optional project name (for Ghidra)
        
        Returns:
            AdapterResult with binary information
        """
        pass
    
    @abstractmethod
    def decompile_function(self, address: int) -> AdapterResult:
        """
        Decompile function at given address
        
        Args:
            address: Memory address of function
        
        Returns:
            AdapterResult with decompiled code
        """
        pass
    
    @abstractmethod
    def set_breakpoint(self, address: int, bp_type: BreakpointType) -> AdapterResult:
        """
        Set a breakpoint at the given address
        
        Args:
            address: Memory address
            bp_type: Type of breakpoint
        
        Returns:
            AdapterResult with breakpoint information
        """
        pass
    
    @abstractmethod
    def read_memory(self, address: int, size: int) -> AdapterResult:
        """
        Read memory at the given address
        
        Args:
            address: Memory address
            size: Number of bytes to read
        
        Returns:
            AdapterResult with memory data
        """
        pass
    
    @abstractmethod
    def get_function_at(self, address: int) -> AdapterResult:
        """
        Get function information at address
        
        Args:
            address: Memory address
        
        Returns:
            AdapterResult with function information
        """
        pass
    
    @abstractmethod
    def find_references(self, address: int) -> AdapterResult:
        """
        Find references to the given address
        
        Args:
            address: Memory address
        
        Returns:
            AdapterResult with list of references
        """
        pass
    
    def get_tool_info(self) -> Dict[str, Any]:
        """
        Get information about the tool
        
        ADR Note: Non-abstract method providing basic tool information.
        Subclasses can override for tool-specific details.
        """
        return {
            "tool_type": self.__class__.__name__,
            "install_path": str(self.install_path),
            "is_connected": self.is_connected,
        }

