"""
Adapter Factory

ADR Note: Factory pattern for creating appropriate adapters based on
detected tools. Handles tool selection and adapter initialization.
"""

import logging
from pathlib import Path
from typing import Optional

from .base_adapter import BaseAdapter
from .ida_adapter import IDAAdapter
from .ghidra_adapter import GhidraAdapter
from ..tool_detection import DetectionResult, ToolType

logger = logging.getLogger(__name__)


class AdapterFactory:
    """
    Factory for creating tool adapters
    
    ADR Note: Centralized adapter creation logic. Handles tool-specific
    initialization requirements (e.g., IDA Pro needs RPC URL, Ghidra needs install path).
    """
    
    @staticmethod
    def create_adapter(
        detection_result: DetectionResult,
        rpc_url: Optional[str] = None
    ) -> Optional[BaseAdapter]:
        """
        Create adapter based on detection result
        
        Args:
            detection_result: Tool detection result
            rpc_url: IDA Pro RPC URL (for IDA adapter)
        
        Returns:
            Initialized adapter or None if creation fails
        """
        if not detection_result.is_available:
            logger.warning(f"Tool {detection_result.tool_type.value} not available")
            return None
        
        try:
            if detection_result.tool_type == ToolType.IDA_PRO:
                # IDA adapter uses RPC, install_path is optional
                rpc_url = rpc_url or "http://127.0.0.1:13337"
                adapter = IDAAdapter(
                    detection_result.install_path or Path("."),
                    rpc_url=rpc_url
                )
                logger.info(f"Created IDA adapter with RPC URL: {rpc_url}")
                return adapter
            
            elif detection_result.tool_type == ToolType.GHIDRA:
                if not detection_result.install_path:
                    logger.error("Ghidra detected but install path not found")
                    return None
                
                adapter = GhidraAdapter(detection_result.install_path)
                logger.info(f"Created Ghidra adapter for: {detection_result.install_path}")
                return adapter
            
            else:
                logger.error(f"Unsupported tool type: {detection_result.tool_type}")
                return None
        
        except Exception as e:
            logger.exception(f"Failed to create adapter: {e}")
            return None

