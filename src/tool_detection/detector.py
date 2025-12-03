"""
Tool Detection System

ADR Note: Multi-method detection ensures tools are found regardless of
installation method. Detection runs on startup and can be manually triggered.
Results are cached to avoid repeated expensive checks.
"""

import logging
from typing import Optional, Dict

from .types import ToolType, DetectionResult
from .ida_detector import IDADetector
from .ghidra_detector import GhidraDetector

logger = logging.getLogger(__name__)


class ToolDetector:
    """
    Main tool detection system
    
    ADR Note: Detector tries multiple methods and returns the first successful
    detection. Preference can be set via configuration. Detection is cached
    to avoid repeated expensive operations.
    """
    
    def __init__(self, preferred_tool: Optional[str] = None):
        """
        Initialize detector
        
        Args:
            preferred_tool: Preferred tool ("ida" or "ghidra"). If both are
                           available, preferred one is selected.
        """
        self.preferred_tool = preferred_tool
        self._cache: Optional[Dict[ToolType, DetectionResult]] = None
        self.ida_detector = IDADetector()
        self.ghidra_detector = GhidraDetector()
    
    def detect_all(self, use_cache: bool = True) -> Dict[ToolType, DetectionResult]:
        """
        Detect all available tools
        
        ADR Note: Returns results for all tools, not just the first one.
        This allows users to see what's available and manually select if needed.
        """
        if use_cache and self._cache is not None:
            return self._cache
        
        results = {
            ToolType.IDA_PRO: self.ida_detector.detect(),
            ToolType.GHIDRA: self.ghidra_detector.detect(),
        }
        
        self._cache = results
        return results
    
    def detect_available(self) -> Optional[DetectionResult]:
        """
        Detect and return the first available tool
        
        ADR Note: If preferred_tool is set and available, returns that.
        Otherwise returns first available tool. Returns None if none available.
        """
        all_results = self.detect_all()
        
        # Check preferred tool first if set
        if self.preferred_tool:
            preferred_type = (
                ToolType.IDA_PRO if self.preferred_tool.lower() == "ida"
                else ToolType.GHIDRA if self.preferred_tool.lower() == "ghidra"
                else None
            )
            
            if preferred_type and all_results[preferred_type].is_available:
                logger.info(f"Using preferred tool: {preferred_type.value}")
                return all_results[preferred_type]
        
        # Return first available tool
        for tool_type, result in all_results.items():
            if result.is_available:
                logger.info(f"Auto-detected tool: {tool_type.value}")
                return result
        
        logger.warning("No reverse engineering tools detected")
        return None
    
    def clear_cache(self):
        """Clear detection cache to force re-detection"""
        self._cache = None
        logger.debug("Detection cache cleared")

