"""
Tool Detection Module

Automatic detection of available reverse engineering tools (IDA Pro, Ghidra).
"""

from .detector import ToolDetector
from .types import DetectionResult, ToolType

__all__ = ["ToolDetector", "DetectionResult", "ToolType"]

