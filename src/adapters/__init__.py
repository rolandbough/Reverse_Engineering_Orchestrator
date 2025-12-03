"""
Tool Adapters Module

Unified interface for reverse engineering tools (IDA Pro, Ghidra).
"""

from .base_adapter import BaseAdapter, AdapterResult, BreakpointType
from .ghidra_adapter import GhidraAdapter
from .ida_adapter import IDAAdapter
from .adapter_factory import AdapterFactory

__all__ = [
    "BaseAdapter",
    "AdapterResult",
    "BreakpointType",
    "GhidraAdapter",
    "IDAAdapter",
    "AdapterFactory",
]

