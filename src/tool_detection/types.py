"""
Tool Detection Types

ADR Note: Shared types are in a separate module to avoid circular imports.
This allows detector implementations to import types without importing
the main detector class.
"""

from enum import Enum
from typing import Optional, Dict, Any
from pathlib import Path
from pydantic import BaseModel


class ToolType(str, Enum):
    """Supported reverse engineering tools"""
    IDA_PRO = "ida_pro"
    GHIDRA = "ghidra"
    NONE = "none"


class DetectionResult(BaseModel):
    """
    Result of tool detection
    
    ADR Note: Structured result allows easy inspection and debugging.
    Includes all relevant information about detected tool.
    """
    tool_type: ToolType
    is_available: bool
    install_path: Optional[Path] = None
    version: Optional[str] = None
    python_module_available: bool = False
    is_running: bool = False
    detection_method: Optional[str] = None  # How it was detected
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = {}  # Tool-specific metadata

