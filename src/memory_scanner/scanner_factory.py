"""
Memory Scanner Factory

ADR Note: Factory pattern for creating appropriate memory scanner instances.
Detects available scanner backends and creates the best available scanner.
"""

import logging
from typing import Optional

from .base_scanner import BaseMemoryScanner
from .types import ScannerResult

logger = logging.getLogger(__name__)


class MemoryScannerFactory:
    """
    Factory for creating memory scanner instances
    
    ADR Note: Detects available scanner backends (x64dbg, Cheat Engine, custom)
    and creates the appropriate scanner. Preference order:
    1. x64dbg (recommended, free, powerful)
    2. Cheat Engine (alternative, free)
    3. Custom scanner (fallback, uses Windows API)
    """
    
    @staticmethod
    def create_scanner(
        preferred_backend: Optional[str] = None,
        process_name: Optional[str] = None,
        process_id: Optional[int] = None
    ) -> Optional[BaseMemoryScanner]:
        """
        Create a memory scanner instance
        
        Args:
            preferred_backend: Preferred backend ("x64dbg", "cheat_engine", "custom")
            process_name: Name of target process
            process_id: PID of target process
        
        Returns:
            Memory scanner instance, or None if no scanner available
        """
        # Try preferred backend first if specified
        if preferred_backend:
            scanner = MemoryScannerFactory._create_specific_scanner(
                preferred_backend, process_name, process_id
            )
            if scanner:
                return scanner
        
        # Try backends in preference order
        backends = ["x64dbg", "cheat_engine", "custom"]
        
        for backend in backends:
            if preferred_backend and backend == preferred_backend:
                continue  # Already tried
            
            scanner = MemoryScannerFactory._create_specific_scanner(
                backend, process_name, process_id
            )
            if scanner:
                logger.info(f"Created {backend} scanner")
                return scanner
        
        logger.warning("No memory scanner backends available")
        return None
    
    @staticmethod
    def _create_specific_scanner(
        backend: str,
        process_name: Optional[str],
        process_id: Optional[int]
    ) -> Optional[BaseMemoryScanner]:
        """Create a specific scanner backend"""
        try:
            if backend == "x64dbg":
                from .x64dbg_scanner import X64dbgScanner
                scanner = X64dbgScanner(process_name, process_id)
                # Test connection
                result = scanner.connect()
                if result.success:
                    return scanner
                else:
                    logger.debug(f"x64dbg scanner connection failed: {result.error}")
            
            elif backend == "cheat_engine":
                from .cheat_engine_scanner import CheatEngineScanner
                scanner = CheatEngineScanner(process_name, process_id)
                result = scanner.connect()
                if result.success:
                    return scanner
                else:
                    logger.debug(f"Cheat Engine scanner connection failed: {result.error}")
            
            elif backend == "custom":
                from .custom_scanner import CustomScanner
                scanner = CustomScanner(process_name, process_id)
                result = scanner.connect()
                if result.success:
                    return scanner
                else:
                    logger.debug(f"Custom scanner connection failed: {result.error}")
        
        except ImportError as e:
            logger.debug(f"Backend {backend} not available: {e}")
        except Exception as e:
            logger.debug(f"Failed to create {backend} scanner: {e}")
        
        return None
    
    @staticmethod
    def list_available_backends() -> list[str]:
        """
        List available scanner backends
        
        Returns:
            List of available backend names
        """
        available = []
        
        # Check x64dbg
        try:
            from .x64dbg_scanner import X64dbgScanner
            scanner = X64dbgScanner()
            if scanner.connect().success:
                available.append("x64dbg")
                scanner.disconnect()
        except Exception:
            pass
        
        # Check Cheat Engine
        try:
            from .cheat_engine_scanner import CheatEngineScanner
            scanner = CheatEngineScanner()
            if scanner.connect().success:
                available.append("cheat_engine")
                scanner.disconnect()
        except Exception:
            pass
        
        # Custom scanner is always available (uses Windows API)
        try:
            from .custom_scanner import CustomScanner
            scanner = CustomScanner()
            if scanner.connect().success:
                available.append("custom")
                scanner.disconnect()
        except Exception:
            pass
        
        return available

