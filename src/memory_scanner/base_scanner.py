"""
Base Memory Scanner Interface

ADR Note: Abstract base class defining the memory scanner interface.
All scanner implementations (x64dbg, Cheat Engine, custom) must implement
this interface to ensure consistent behavior across backends.
"""

import logging
from abc import ABC, abstractmethod
from typing import List, Optional, Any

from .types import ScanResult, ScannerResult, ValueType

logger = logging.getLogger(__name__)


class BaseMemoryScanner(ABC):
    """
    Abstract base class for memory scanners
    
    ADR Note: Defines the standard interface for all memory scanner backends.
    This allows the system to work with different tools (x64dbg, Cheat Engine,
    custom) interchangeably. The factory pattern selects the appropriate scanner
    based on availability.
    """
    
    def __init__(self, process_name: Optional[str] = None, process_id: Optional[int] = None):
        """
        Initialize memory scanner
        
        Args:
            process_name: Name of target process (e.g., "game.exe")
            process_id: PID of target process (alternative to process_name)
        """
        self.process_name = process_name
        self.process_id = process_id
        self.is_connected = False
        self.current_scan_results: List[ScanResult] = []
        self.scan_count = 0
    
    @abstractmethod
    def connect(self) -> ScannerResult:
        """
        Connect to the memory scanner backend
        
        Returns:
            ScannerResult indicating success or failure
        """
        pass
    
    @abstractmethod
    def disconnect(self) -> ScannerResult:
        """
        Disconnect from the memory scanner backend
        
        Returns:
            ScannerResult indicating success or failure
        """
        pass
    
    @abstractmethod
    def initial_scan(
        self,
        value: Any,
        value_type: ValueType,
        scan_type: str = "exact"
    ) -> List[ScanResult]:
        """
        Perform initial memory scan for a value
        
        ADR Note: This is the first scan in the workflow. It searches the entire
        process memory for the specified value. Results are cached for filtering.
        
        Args:
            value: Value to search for
            value_type: Type of value (int32, float, string, etc.)
            scan_type: Type of scan ("exact", "greater", "less", "changed", etc.)
        
        Returns:
            List of ScanResult objects containing addresses where value was found
        """
        pass
    
    @abstractmethod
    def filter_scan(
        self,
        value: Any,
        value_type: ValueType,
        scan_type: str = "exact"
    ) -> List[ScanResult]:
        """
        Filter previous scan results based on new value
        
        ADR Note: This is the filtering step. It takes the results from the
        initial scan and filters them based on a new value. This narrows down
        the candidate addresses.
        
        Args:
            value: New value to filter by
            value_type: Type of value
            scan_type: Type of scan ("exact", "greater", "less", "changed", etc.)
        
        Returns:
            Filtered list of ScanResult objects
        """
        pass
    
    @abstractmethod
    def read_memory(self, address: str, size: int) -> Optional[bytes]:
        """
        Read memory at the specified address
        
        Args:
            address: Hex address (e.g., "0x401000")
            size: Number of bytes to read
        
        Returns:
            Bytes read from memory, or None if failed
        """
        pass
    
    @abstractmethod
    def write_memory(self, address: str, data: bytes) -> ScannerResult:
        """
        Write data to memory at the specified address
        
        ADR Note: Writing memory is useful for testing and verification.
        Should be used carefully as it can crash the target process.
        
        Args:
            address: Hex address (e.g., "0x401000")
            data: Bytes to write
        
        Returns:
            ScannerResult indicating success or failure
        """
        pass
    
    def get_scan_results(self) -> List[ScanResult]:
        """
        Get current scan results
        
        Returns:
            List of current scan results
        """
        return self.current_scan_results.copy()
    
    @abstractmethod
    def clear_scan(self) -> ScannerResult:
        """
        Clear current scan results
        
        Returns:
            ScannerResult indicating success or failure
        """
        pass
    
    @abstractmethod
    def get_scanner_info(self) -> dict:
        """
        Get information about the scanner backend
        
        Returns:
            Dictionary with scanner information (name, version, capabilities)
        """
        pass

