"""
Workflow Orchestrator

ADR Note: Coordinates the complete reverse engineering workflow:
1. Visual Analyzer detects UI changes
2. Memory Scanner finds corresponding addresses
3. RE Tool sets breakpoints and decompiles code
4. AI analyzes the decompiled code

This orchestrator manages the communication between all components.
"""

import logging
import threading
from typing import Optional, Dict, List, Any, Callable
from queue import Queue

# Component imports
try:
    from ..visual_analyzer import VisualAnalyzer
    VISUAL_ANALYZER_AVAILABLE = True
except ImportError:
    VISUAL_ANALYZER_AVAILABLE = False
    VisualAnalyzer = None

try:
    from ..memory_scanner import MemoryScannerFactory, BaseMemoryScanner
    MEMORY_SCANNER_AVAILABLE = True
except ImportError:
    MEMORY_SCANNER_AVAILABLE = False
    MemoryScannerFactory = None
    BaseMemoryScanner = None

from ..communication import (
    ComponentServer,
    ComponentClient,
    Message,
    MessageType,
    MessageCodec
)

logger = logging.getLogger(__name__)


class WorkflowOrchestrator:
    """
    Orchestrates the complete reverse engineering workflow
    
    ADR Note: This is the central coordinator that connects:
    - Visual Analyzer (detects UI changes)
    - Memory Scanner (finds memory addresses)
    - RE Tool Adapter (sets breakpoints, decompiles)
    - MCP Server (exposes tools to AI)
    
    The orchestrator manages the communication flow and state.
    """
    
    def __init__(
        self,
        process_name: Optional[str] = None,
        process_id: Optional[int] = None,
        memory_scanner_backend: Optional[str] = None
    ):
        """
        Initialize workflow orchestrator
        
        Args:
            process_name: Name of target process
            process_id: PID of target process
            memory_scanner_backend: Preferred memory scanner backend
        """
        self.process_name = process_name
        self.process_id = process_id
        
        # Components
        self.visual_analyzer: Optional[VisualAnalyzer] = None
        self.memory_scanner: Optional[BaseMemoryScanner] = None
        self.re_adapter = None  # Set by MCP server
        
        # Communication
        self.communication_server: Optional[ComponentServer] = None
        self.communication_port: Optional[int] = None
        
        # State
        self.is_running = False
        self.current_scan_addresses: List[str] = []
        self.detected_values: List[Dict[str, Any]] = []
        self.workflow_state: Dict[str, Any] = {
            "visual_monitoring": False,
            "memory_scanning": False,
            "breakpoints_set": False,
            "current_addresses": []
        }
        
        # Callbacks
        self.on_address_found: Optional[Callable[[List[str]], None]] = None
        self.on_breakpoint_hit: Optional[Callable[[str], None]] = None
        
        # Initialize components
        self._initialize_components(memory_scanner_backend)
    
    def _initialize_components(self, memory_scanner_backend: Optional[str]):
        """Initialize all components"""
        # Initialize visual analyzer
        if VISUAL_ANALYZER_AVAILABLE:
            try:
                self.visual_analyzer = VisualAnalyzer()
                logger.info("Visual analyzer initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize visual analyzer: {e}")
        
        # Initialize memory scanner
        if MEMORY_SCANNER_AVAILABLE and MemoryScannerFactory:
            try:
                self.memory_scanner = MemoryScannerFactory.create_scanner(
                    preferred_backend=memory_scanner_backend,
                    process_name=self.process_name,
                    process_id=self.process_id
                )
                if self.memory_scanner:
                    result = self.memory_scanner.connect()
                    if result.success:
                        logger.info(f"Memory scanner initialized: {self.memory_scanner.get_scanner_info()['name']}")
                    else:
                        logger.warning(f"Memory scanner connection failed: {result.error}")
                        self.memory_scanner = None
                else:
                    logger.warning("No memory scanner backends available")
            except Exception as e:
                logger.warning(f"Failed to initialize memory scanner: {e}")
        
        # Initialize communication server
        try:
            self.communication_server = ComponentServer(host="127.0.0.1", port=0)
            self.communication_server.register_handler(
                MessageType.VISUAL_CHANGE.value,
                self._handle_visual_change
            )
            self.communication_server.register_handler(
                MessageType.SCAN_RESULT.value,
                self._handle_scan_result
            )
            self.communication_port = self.communication_server.start()
            logger.info(f"Communication server started on port {self.communication_port}")
        except Exception as e:
            logger.error(f"Failed to start communication server: {e}")
    
    def start_workflow(
        self,
        regions: Optional[List[Dict[str, int]]] = None,
        value_type: str = "int32"
    ) -> Dict[str, Any]:
        """
        Start the complete workflow
        
        ADR Note: Starts visual monitoring and prepares for memory scanning.
        The workflow will:
        1. Monitor UI for changes
        2. When change detected, scan memory for the value
        3. Filter scans on subsequent changes
        4. When addresses found, set breakpoints
        5. When breakpoint hits, decompile and analyze
        
        Args:
            regions: Screen regions to monitor (if None, monitors full screen)
            value_type: Type of value to scan for (int32, float, etc.)
        
        Returns:
            Status dictionary
        """
        if self.is_running:
            return {"success": False, "error": "Workflow already running"}
        
        # Start visual monitoring
        if self.visual_analyzer:
            success = self.visual_analyzer.start_monitoring(regions)
            if not success:
                return {"success": False, "error": "Failed to start visual monitoring"}
            self.workflow_state["visual_monitoring"] = True
        else:
            return {"success": False, "error": "Visual analyzer not available"}
        
        # Check memory scanner
        if not self.memory_scanner:
            return {"success": False, "error": "Memory scanner not available"}
        
        self.is_running = True
        self.workflow_state["value_type"] = value_type
        
        logger.info("Workflow started")
        return {
            "success": True,
            "communication_port": self.communication_port,
            "state": self.workflow_state
        }
    
    def stop_workflow(self) -> Dict[str, Any]:
        """Stop the workflow"""
        if not self.is_running:
            return {"success": False, "error": "Workflow not running"}
        
        # Stop visual monitoring
        if self.visual_analyzer:
            self.visual_analyzer.stop_monitoring()
            self.workflow_state["visual_monitoring"] = False
        
        # Clear memory scanner
        if self.memory_scanner:
            self.memory_scanner.clear_scan()
            self.workflow_state["memory_scanning"] = False
        
        self.is_running = False
        self.current_scan_addresses = []
        self.detected_values = []
        
        logger.info("Workflow stopped")
        return {"success": True}
    
    def _handle_visual_change(self, message: Message):
        """
        Handle visual change detected by visual analyzer
        
        ADR Note: When a visual change is detected, trigger memory scan
        for the detected value. This is the first step in the workflow.
        """
        if not self.is_running:
            return
        
        value = message.payload.get("value")
        coordinates = message.payload.get("coordinates", {})
        
        logger.info(f"Visual change detected: value={value}, coords={coordinates}")
        
        # Store detected value
        self.detected_values.append({
            "value": value,
            "coordinates": coordinates,
            "timestamp": message.timestamp
        })
        
        # Determine if this is initial scan or filter scan
        if not self.current_scan_addresses:
            # Initial scan
            self._perform_initial_scan(value)
        else:
            # Filter scan
            self._perform_filter_scan(value)
    
    def _perform_initial_scan(self, value: Any):
        """Perform initial memory scan for value"""
        if not self.memory_scanner:
            return
        
        logger.info(f"Performing initial scan for value: {value}")
        
        # Determine value type
        value_type = self.workflow_state.get("value_type", "int32")
        from ..memory_scanner.types import ValueType
        
        try:
            value_type_enum = ValueType(value_type)
        except ValueError:
            value_type_enum = ValueType.INT_32  # Default
        
        # Perform scan
        results = self.memory_scanner.initial_scan(value, value_type_enum)
        self.current_scan_addresses = [r.address for r in results]
        
        logger.info(f"Initial scan found {len(results)} addresses")
        
        if results:
            self.workflow_state["memory_scanning"] = True
            self.workflow_state["current_addresses"] = self.current_scan_addresses
            
            # Notify callback if set
            if self.on_address_found:
                self.on_address_found(self.current_scan_addresses)
    
    def _perform_filter_scan(self, value: Any):
        """Perform filter scan on previous results"""
        if not self.memory_scanner or not self.current_scan_addresses:
            return
        
        logger.info(f"Performing filter scan for value: {value}")
        
        # Determine value type
        value_type = self.workflow_state.get("value_type", "int32")
        from ..memory_scanner.types import ValueType
        
        try:
            value_type_enum = ValueType(value_type)
        except ValueError:
            value_type_enum = ValueType.INT_32  # Default
        
        # Perform filter scan
        results = self.memory_scanner.filter_scan(value, value_type_enum)
        self.current_scan_addresses = [r.address for r in results]
        
        logger.info(f"Filter scan found {len(results)} addresses")
        
        if results:
            self.workflow_state["current_addresses"] = self.current_scan_addresses
            
            # If we have few addresses left, suggest setting breakpoints
            if len(results) <= 5:
                logger.info(f"Few addresses remaining ({len(results)}). Ready for breakpoint setting.")
            
            # Notify callback if set
            if self.on_address_found:
                self.on_address_found(self.current_scan_addresses)
    
    def _handle_scan_result(self, message: Message):
        """Handle scan result from memory scanner"""
        addresses = message.payload.get("addresses", [])
        count = message.payload.get("count", 0)
        
        logger.info(f"Received scan result: {count} addresses")
        self.current_scan_addresses = addresses
        self.workflow_state["current_addresses"] = addresses
    
    def set_breakpoints(self, addresses: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Set breakpoints at the specified addresses
        
        ADR Note: Uses the RE tool adapter to set breakpoints. When breakpoints
        are hit, the orchestrator will decompile and analyze the code.
        
        Args:
            addresses: Addresses to set breakpoints at (if None, uses current scan addresses)
        
        Returns:
            Status dictionary
        """
        if not self.re_adapter:
            return {"success": False, "error": "RE tool adapter not set"}
        
        if addresses is None:
            addresses = self.current_scan_addresses
        
        if not addresses:
            return {"success": False, "error": "No addresses to set breakpoints at"}
        
        # Set breakpoints using adapter
        # Note: This requires the adapter to be set by the MCP server
        logger.info(f"Setting breakpoints at {len(addresses)} addresses")
        
        # TODO: Implement breakpoint setting via adapter
        # For now, just update state
        self.workflow_state["breakpoints_set"] = True
        
        return {
            "success": True,
            "addresses": addresses,
            "count": len(addresses)
        }
    
    def get_workflow_status(self) -> Dict[str, Any]:
        """Get current workflow status"""
        return {
            "is_running": self.is_running,
            "state": self.workflow_state.copy(),
            "detected_values_count": len(self.detected_values),
            "current_addresses_count": len(self.current_scan_addresses),
            "components": {
                "visual_analyzer": self.visual_analyzer is not None,
                "memory_scanner": self.memory_scanner is not None,
                "re_adapter": self.re_adapter is not None,
                "communication_server": self.communication_server is not None
            }
        }
    
    def cleanup(self):
        """Cleanup resources"""
        self.stop_workflow()
        
        if self.memory_scanner:
            self.memory_scanner.disconnect()
        
        if self.communication_server:
            self.communication_server.stop()

