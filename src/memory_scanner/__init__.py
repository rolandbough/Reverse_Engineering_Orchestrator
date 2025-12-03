"""
Memory Scanner Module

ADR Note: Provides memory scanning capabilities to find addresses corresponding
to visual changes. Supports multiple backends (x64dbg, Cheat Engine, custom).
"""

from .types import (
    ScanResult,
    ScannerResult,
    ValueType,
    ScanStatus
)
from .base_scanner import BaseMemoryScanner
from .scanner_factory import MemoryScannerFactory

__all__ = [
    "BaseMemoryScanner",
    "MemoryScannerFactory",
    "ScanResult",
    "ScannerResult",
    "ValueType",
    "ScanStatus",
]

