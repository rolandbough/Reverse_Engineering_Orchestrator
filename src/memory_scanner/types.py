"""
Memory Scanner Types

ADR Note: Common data structures for memory scanner operations.
"""

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Any, Dict


class ValueType(str, Enum):
    """Supported value types for memory scanning"""
    INT_8 = "int8"
    INT_16 = "int16"
    INT_32 = "int32"
    INT_64 = "int64"
    UINT_8 = "uint8"
    UINT_16 = "uint16"
    UINT_32 = "uint32"
    UINT_64 = "uint64"
    FLOAT = "float"
    DOUBLE = "double"
    STRING = "string"
    BYTES = "bytes"


class ScanStatus(str, Enum):
    """Status of a memory scan"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ScanResult:
    """
    Result of a memory scan operation
    
    ADR Note: Contains address and metadata about the scan result.
    Addresses are stored as hex strings for consistency with RE tools.
    """
    address: str  # Hex address (e.g., "0x401000")
    value: Any  # The value found at this address
    value_type: ValueType
    size: int  # Size in bytes
    region: Optional[str] = None  # Memory region name (e.g., ".data", "heap")
    protection: Optional[str] = None  # Memory protection (e.g., "RWX")
    module: Optional[str] = None  # Module name if in module memory
    offset: Optional[int] = None  # Offset within module
    metadata: Optional[Dict[str, Any]] = None  # Additional metadata


@dataclass
class ScannerResult:
    """
    Result of a scanner operation
    
    ADR Note: Standard result structure for all scanner operations.
    Provides success/failure status and optional error message.
    """
    success: bool
    error: Optional[str] = None
    data: Optional[Any] = None  # Additional result data
    metadata: Optional[Dict[str, Any]] = None  # Additional metadata

