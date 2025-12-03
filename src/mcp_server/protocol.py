"""
MCP Protocol Handler

ADR Note: Implements MCP protocol using Python SDK. Handles JSON-RPC 2.0
communication over stdio for Cursor integration.
"""

import json
import sys
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent, ImageContent, EmbeddedResource

from .config import ServerConfig
from ..tool_detection import ToolDetector, ToolType, DetectionResult
from ..adapters import BaseAdapter, AdapterFactory

# Visual analyzer (optional, Phase 2)
try:
    from ..visual_analyzer import VisualAnalyzer
    VISUAL_ANALYZER_AVAILABLE = True
except ImportError:
    VISUAL_ANALYZER_AVAILABLE = False
    VisualAnalyzer = None

# Workflow orchestrator (Phase 3)
try:
    from ..orchestrator import WorkflowOrchestrator
    ORCHESTRATOR_AVAILABLE = True
except ImportError:
    ORCHESTRATOR_AVAILABLE = False
    WorkflowOrchestrator = None

logger = logging.getLogger(__name__)


class MCPProtocolHandler:
    """
    Handles MCP protocol communication
    
    ADR Note: Wraps MCP SDK server and provides tool/resource registration.
    All MCP operations are handled through this class.
    """
    
    def __init__(self, config: ServerConfig, tool_detector: ToolDetector):
        self.config = config
        self.tool_detector = tool_detector
        self.server = Server(self.config.server_name)
        self.current_adapter: Optional[BaseAdapter] = None
        
        # Visual analyzer (Phase 2)
        self.visual_analyzer: Optional[VisualAnalyzer] = None
        if VISUAL_ANALYZER_AVAILABLE:
            try:
                self.visual_analyzer = VisualAnalyzer()
            except Exception as e:
                logger.warning(f"Failed to initialize visual analyzer: {e}")
        
        # Workflow orchestrator (Phase 3)
        self.orchestrator: Optional[WorkflowOrchestrator] = None
        if ORCHESTRATOR_AVAILABLE:
            try:
                self.orchestrator = WorkflowOrchestrator()
                # Connect orchestrator to RE adapter when available
                if self.current_adapter:
                    self.orchestrator.re_adapter = self.current_adapter
            except Exception as e:
                logger.warning(f"Failed to initialize orchestrator: {e}")
        
        # Register MCP handlers
        self._register_handlers()
    
    def _register_handlers(self):
        """Register MCP protocol handlers"""
        
        # List available tools
        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            """
            List available MCP tools
            
            ADR Note: Returns list of tools that can be called by the AI agent.
            Tools correspond to reverse engineering operations.
            """
            return [
                Tool(
                    name="detect_re_tool",
                    description="Detect and select available reverse engineering tool (IDA Pro or Ghidra)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "preferred_tool": {
                                "type": "string",
                                "enum": ["ida", "ghidra"],
                                "description": "Preferred tool if multiple available"
                            }
                        }
                    }
                ),
                Tool(
                    name="load_binary",
                    description="Load a binary file for analysis",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "binary_path": {
                                "type": "string",
                                "description": "Path to binary file to load"
                            },
                            "project_name": {
                                "type": "string",
                                "description": "Optional project name (for Ghidra)"
                            }
                        },
                        "required": ["binary_path"]
                    }
                ),
                Tool(
                    name="decompile_function",
                    description="Decompile function at given address",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "address": {
                                "type": "string",
                                "description": "Memory address in hex (e.g., '0x401000')"
                            }
                        },
                        "required": ["address"]
                    }
                ),
                Tool(
                    name="set_breakpoint",
                    description="Set a breakpoint at the given address",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "address": {
                                "type": "string",
                                "description": "Memory address in hex"
                            },
                            "type": {
                                "type": "string",
                                "enum": ["software", "hardware", "write", "read", "execute"],
                                "description": "Type of breakpoint"
                            }
                        },
                        "required": ["address", "type"]
                    }
                ),
                Tool(
                    name="read_memory",
                    description="Read memory at the given address",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "address": {
                                "type": "string",
                                "description": "Memory address in hex"
                            },
                            "size": {
                                "type": "integer",
                                "description": "Number of bytes to read"
                            }
                        },
                        "required": ["address", "size"]
                    }
                ),
                Tool(
                    name="get_function_info",
                    description="Get function information at address",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "address": {
                                "type": "string",
                                "description": "Memory address in hex"
                            }
                        },
                        "required": ["address"]
                    }
                ),
                Tool(
                    name="find_references",
                    description="Find references to the given address",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "address": {
                                "type": "string",
                                "description": "Memory address in hex"
                            }
                        },
                        "required": ["address"]
                    }
                ),
                Tool(
                    name="start_visual_monitoring",
                    description="Start monitoring screen regions for changes",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "regions": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "name": {"type": "string"},
                                        "x": {"type": "integer"},
                                        "y": {"type": "integer"},
                                        "w": {"type": "integer"},
                                        "h": {"type": "integer"}
                                    }
                                }
                            },
                            "change_threshold": {"type": "number", "default": 0.1},
                            "capture_interval": {"type": "number", "default": 0.1}
                        }
                    }
                ),
                Tool(
                    name="stop_visual_monitoring",
                    description="Stop visual monitoring",
                    inputSchema={"type": "object", "properties": {}}
                ),
                Tool(
                    name="get_detected_changes",
                    description="Get list of detected visual changes",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "limit": {"type": "integer", "default": 10}
                        }
                    }
                ),
                Tool(
                    name="analyze_region",
                    description="Analyze a specific screen region for changes",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "x": {"type": "integer", "description": "X coordinate"},
                            "y": {"type": "integer", "description": "Y coordinate"},
                            "width": {"type": "integer", "description": "Region width"},
                            "height": {"type": "integer", "description": "Region height"},
                            "region_name": {"type": "string", "description": "Name for this region"}
                        },
                        "required": ["x", "y", "width", "height"]
                    }
                ),
                Tool(
                    name="capture_process_window",
                    description="Capture full window screenshot of a process",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "process_name": {
                                "type": "string",
                                "description": "Process name (e.g., 'game.exe')"
                            },
                            "process_id": {
                                "type": "integer",
                                "description": "Process ID (PID) - alternative to process_name"
                            }
                        }
                    }
                ),
                Tool(
                    name="select_region_from_screenshot",
                    description="Select a region of interest from a screenshot (returns region coordinates)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "screenshot_base64": {
                                "type": "string",
                                "description": "Base64-encoded screenshot (from capture_process_window)"
                            },
                            "x": {
                                "type": "integer",
                                "description": "X coordinate of region top-left corner (optional if using interactive mode)"
                            },
                            "y": {
                                "type": "integer",
                                "description": "Y coordinate of region top-left corner (optional if using interactive mode)"
                            },
                            "width": {
                                "type": "integer",
                                "description": "Width of region (optional if using interactive mode)"
                            },
                            "height": {
                                "type": "integer",
                                "description": "Height of region (optional if using interactive mode)"
                            },
                            "region_name": {
                                "type": "string",
                                "description": "Name for this region"
                            },
                            "interactive": {
                                "type": "boolean",
                                "description": "Use interactive rectangle selection (opens window to drag and select)",
                                "default": False
                            }
                        }
                    }
                ),
                Tool(
                    name="select_region_interactive",
                    description="Interactively select a region by dragging a rectangle on the screenshot (opens a window)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "screenshot_base64": {
                                "type": "string",
                                "description": "Base64-encoded screenshot (from capture_process_window)"
                            }
                        },
                        "required": ["screenshot_base64"]
                    }
                ),
            ]
        
        # Handle tool calls
        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            """
            Handle tool execution requests
            
            ADR Note: Routes tool calls to appropriate adapter methods.
            Handles errors and formats responses for MCP.
            """
            try:
                # Ensure adapter is initialized
                if not self.current_adapter:
                    # Auto-detect and initialize adapter
                    result = await self._initialize_adapter()
                    if not result["success"]:
                        return [TextContent(
                            type="text",
                            text=f"Error: {result['error']}"
                        )]
                
                # Route to appropriate handler
                if name == "detect_re_tool":
                    return await self._handle_detect_tool(arguments)
                elif name == "load_binary":
                    return await self._handle_load_binary(arguments)
                elif name == "decompile_function":
                    return await self._handle_decompile_function(arguments)
                elif name == "set_breakpoint":
                    return await self._handle_set_breakpoint(arguments)
                elif name == "read_memory":
                    return await self._handle_read_memory(arguments)
                elif name == "get_function_info":
                    return await self._handle_get_function_info(arguments)
                elif name == "find_references":
                    return await self._handle_find_references(arguments)
                elif name == "start_visual_monitoring":
                    return await self._handle_start_visual_monitoring(arguments)
                elif name == "stop_visual_monitoring":
                    return await self._handle_stop_visual_monitoring(arguments)
                elif name == "get_detected_changes":
                    return await self._handle_get_detected_changes(arguments)
                elif name == "analyze_region":
                    return await self._handle_analyze_region(arguments)
                elif name == "capture_process_window":
                    return await self._handle_capture_process_window(arguments)
                elif name == "select_region_from_screenshot":
                    return await self._handle_select_region_from_screenshot(arguments)
                elif name == "select_region_interactive":
                    return await self._handle_select_region_interactive(arguments)
                elif name == "start_workflow":
                    return await self._handle_start_workflow(arguments)
                elif name == "stop_workflow":
                    return await self._handle_stop_workflow(arguments)
                elif name == "get_workflow_status":
                    return await self._handle_get_workflow_status(arguments)
                elif name == "set_breakpoints_at_addresses":
                    return await self._handle_set_breakpoints_at_addresses(arguments)
                else:
                    return [TextContent(
                        type="text",
                        text=f"Unknown tool: {name}"
                    )]
            
            except Exception as e:
                logger.exception(f"Error executing tool {name}")
                return [TextContent(
                    type="text",
                    text=f"Error: {str(e)}"
                )]
        
        # List available resources
        @self.server.list_resources()
        async def list_resources() -> List[EmbeddedResource]:
            """
            List available MCP resources
            
            ADR Note: Resources provide read-only state information.
            """
            return [
                EmbeddedResource(
                    uri="reo://tool_status",
                    name="Tool Status",
                    description="Current reverse engineering tool status",
                    mimeType="application/json"
                ),
                EmbeddedResource(
                    uri="reo://visual_analyzer_status",
                    name="Visual Analyzer Status",
                    description="Current visual analyzer monitoring status",
                    mimeType="application/json"
                )
            ]
        
        # Get resource content
        @self.server.read_resource()
        async def read_resource(uri: str) -> str:
            """Get resource content"""
            if uri == "reo://tool_status":
                status = self._get_tool_status()
                return json.dumps(status, indent=2)
            elif uri == "reo://visual_analyzer_status":
                if VISUAL_ANALYZER_AVAILABLE and self.visual_analyzer:
                    status = self.visual_analyzer.get_status()
                    return json.dumps(status, indent=2)
                else:
                    return json.dumps({"available": False, "error": "Visual analyzer not initialized"})
            else:
                raise ValueError(f"Unknown resource: {uri}")
    
    async def _initialize_adapter(self) -> Dict[str, Any]:
        """
        Initialize adapter based on detected tool
        
        ADR Note: Creates appropriate adapter (IDA or Ghidra) based on
        detection results. IDA adapter uses RPC URL, Ghidra uses install path.
        """
        detected = self.tool_detector.detect_available()
        
        if not detected or not detected.is_available:
            return {
                "success": False,
                "error": "No reverse engineering tools detected. Please install IDA Pro or Ghidra."
            }
        
        # Use factory to create adapter
        rpc_url = getattr(self.config, 'ida_rpc_url', 'http://127.0.0.1:13337')
        self.current_adapter = AdapterFactory.create_adapter(detected, rpc_url=rpc_url)
        
        if not self.current_adapter:
            return {
                "success": False,
                "error": f"Failed to create adapter for {detected.tool_type.value}"
            }
        
        # Connect adapter
        result = self.current_adapter.connect()
        if not result.success:
            return {
                "success": False,
                "error": f"Failed to connect to tool: {result.error}"
            }
        
        # Connect orchestrator to adapter if available
        if self.orchestrator:
            self.orchestrator.re_adapter = self.current_adapter
        
        return {"success": True}
    
    async def _handle_detect_tool(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handle detect_re_tool tool call"""
        preferred = arguments.get("preferred_tool")
        if preferred:
            self.tool_detector.preferred_tool = preferred
        
        # Clear cache and re-detect
        self.tool_detector.clear_cache()
        result = await self._initialize_adapter()
        
        if result["success"]:
            status = self._get_tool_status()
            return [TextContent(
                type="text",
                text=f"Tool detected and initialized:\n{json.dumps(status, indent=2)}"
            )]
        else:
            return [TextContent(
                type="text",
                text=f"Detection failed: {result['error']}"
            )]
    
    async def _handle_load_binary(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handle load_binary tool call"""
        from pathlib import Path
        
        binary_path = Path(arguments["binary_path"])
        project_name = arguments.get("project_name")
        
        result = self.current_adapter.load_binary(binary_path, project_name)
        
        if result.success:
            return [TextContent(
                type="text",
                text=f"Binary loaded successfully:\n{json.dumps(result.data, indent=2)}"
            )]
        else:
            return [TextContent(
                type="text",
                text=f"Failed to load binary: {result.error}"
            )]
    
    async def _handle_decompile_function(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handle decompile_function tool call"""
        address_str = arguments["address"]
        # Parse hex address
        address = int(address_str, 16) if address_str.startswith("0x") else int(address_str, 16)
        
        result = self.current_adapter.decompile_function(address)
        
        if result.success:
            return [TextContent(
                type="text",
                text=f"Decompiled code:\n{json.dumps(result.data, indent=2)}"
            )]
        else:
            return [TextContent(
                type="text",
                text=f"Decompilation failed: {result.error}"
            )]
    
    async def _handle_set_breakpoint(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handle set_breakpoint tool call"""
        from ..adapters import BreakpointType
        
        address_str = arguments["address"]
        address = int(address_str, 16) if address_str.startswith("0x") else int(address_str, 16)
        bp_type = BreakpointType(arguments["type"])
        
        result = self.current_adapter.set_breakpoint(address, bp_type)
        
        if result.success:
            return [TextContent(
                type="text",
                text=f"Breakpoint set:\n{json.dumps(result.data, indent=2)}"
            )]
        else:
            return [TextContent(
                type="text",
                text=f"Failed to set breakpoint: {result.error}"
            )]
    
    async def _handle_read_memory(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handle read_memory tool call"""
        address_str = arguments["address"]
        address = int(address_str, 16) if address_str.startswith("0x") else int(address_str, 16)
        size = arguments["size"]
        
        result = self.current_adapter.read_memory(address, size)
        
        if result.success:
            return [TextContent(
                type="text",
                text=f"Memory read:\n{json.dumps(result.data, indent=2)}"
            )]
        else:
            return [TextContent(
                type="text",
                text=f"Failed to read memory: {result.error}"
            )]
    
    async def _handle_get_function_info(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handle get_function_info tool call"""
        address_str = arguments["address"]
        address = int(address_str, 16) if address_str.startswith("0x") else int(address_str, 16)
        
        result = self.current_adapter.get_function_at(address)
        
        if result.success:
            return [TextContent(
                type="text",
                text=f"Function information:\n{json.dumps(result.data, indent=2)}"
            )]
        else:
            return [TextContent(
                type="text",
                text=f"Failed to get function info: {result.error}"
            )]
    
    async def _handle_find_references(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handle find_references tool call"""
        if not self.current_adapter:
            return [TextContent(
                type="text",
                text="No reverse engineering tool connected. Use detect_re_tool first."
            )]
        
        address_str = arguments["address"]
        address = int(address_str, 16) if address_str.startswith("0x") else int(address_str, 16)
        
        result = self.current_adapter.find_references(address)
        
        if result.success:
            return [TextContent(
                type="text",
                text=f"References found:\n{json.dumps(result.data, indent=2)}"
            )]
        else:
            return [TextContent(
                type="text",
                text=f"Failed to find references: {result.error}"
            )]
    
    async def _handle_start_visual_monitoring(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handle start_visual_monitoring tool call"""
        if not VISUAL_ANALYZER_AVAILABLE or not self.visual_analyzer:
            return [TextContent(
                type="text",
                text="Visual analyzer not available. Install dependencies: pip install opencv-python mss numpy"
            )]
        
        regions = arguments.get("regions", [])
        change_threshold = arguments.get("change_threshold", 0.1)
        capture_interval = arguments.get("capture_interval", 0.1)
        
        # Update analyzer settings
        self.visual_analyzer.change_detector.threshold = change_threshold
        self.visual_analyzer.capture_interval = capture_interval
        
        # Start monitoring
        success = self.visual_analyzer.start_monitoring(regions)
        
        if success:
            return [TextContent(
                type="text",
                text=f"Started monitoring {len(regions)} regions:\n{json.dumps(regions, indent=2)}"
            )]
        else:
            return [TextContent(
                type="text",
                text="Failed to start monitoring. Monitoring may already be in progress."
            )]
    
    async def _handle_stop_visual_monitoring(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handle stop_visual_monitoring tool call"""
        if not VISUAL_ANALYZER_AVAILABLE or not self.visual_analyzer:
            return [TextContent(
                type="text",
                text="Visual analyzer not available"
            )]
        
        self.visual_analyzer.stop_monitoring()
        
        return [TextContent(
            type="text",
            text="Visual monitoring stopped"
        )]
    
    async def _handle_get_detected_changes(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handle get_detected_changes tool call"""
        if not VISUAL_ANALYZER_AVAILABLE or not self.visual_analyzer:
            return [TextContent(
                type="text",
                text="Visual analyzer not available"
            )]
        
        limit = arguments.get("limit", 10)
        changes = self.visual_analyzer.get_detected_changes(limit=limit)
        
        return [TextContent(
            type="text",
            text=f"Detected {len(changes)} changes:\n{json.dumps(changes, indent=2, default=str)}"
        )]
    
    async def _handle_analyze_region(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handle analyze_region tool call"""
        if not VISUAL_ANALYZER_AVAILABLE or not self.visual_analyzer:
            return [TextContent(
                type="text",
                text="Visual analyzer not available. Install dependencies: pip install opencv-python mss numpy"
            )]
        
        x = arguments["x"]
        y = arguments["y"]
        width = arguments["width"]
        height = arguments["height"]
        region_name = arguments.get("region_name", "region")
        
        result = self.visual_analyzer.analyze_region(x, y, width, height, region_name)
        
        return [TextContent(
            type="text",
            text=f"Region analysis:\n{json.dumps(result, indent=2, default=str)}"
        )]
    
    async def _handle_capture_process_window(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handle capture_process_window tool call"""
        if not VISUAL_ANALYZER_AVAILABLE or not self.visual_analyzer:
            return [TextContent(
                type="text",
                text="Visual analyzer not available. Install dependencies: pip install opencv-python mss numpy pywin32"
            )]
        
        process_name = arguments.get("process_name")
        process_id = arguments.get("process_id")
        
        if not process_name and not process_id:
            return [TextContent(
                type="text",
                text="Error: Either process_name or process_id must be provided"
            )]
        
        result = self.visual_analyzer.capture_process_window(
            process_name=process_name,
            process_id=process_id
        )
        
        if result is None:
            return [TextContent(
                type="text",
                text=f"Failed to capture window for process: {process_name or process_id}"
            )]
        
        # Return screenshot as base64 and metadata
        return [
            TextContent(
                type="text",
                text=f"Screenshot captured:\n{json.dumps({k: v for k, v in result.items() if k != 'screenshot_base64'}, indent=2)}"
            ),
            ImageContent(
                type="image",
                data=result["screenshot_base64"],
                mimeType="image/png"
            ) if result.get("screenshot_base64") else TextContent(
                type="text",
                text="Screenshot data available in result"
            )
        ]
    
    async def _handle_select_region_from_screenshot(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handle select_region_from_screenshot tool call"""
        if not VISUAL_ANALYZER_AVAILABLE or not self.visual_analyzer:
            return [TextContent(
                type="text",
                text="Visual analyzer not available"
            )]
        
        x = arguments["x"]
        y = arguments["y"]
        width = arguments["width"]
        height = arguments["height"]
        region_name = arguments.get("region_name", "selected_region")
        
        # Validate region coordinates if screenshot provided
        screenshot_base64 = arguments.get("screenshot_base64")
        if screenshot_base64:
            try:
                import base64
                import cv2
                import numpy as np
                
                img_data = base64.b64decode(screenshot_base64)
                nparr = np.frombuffer(img_data, np.uint8)
                img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                
                if img is None:
                    return [TextContent(
                        type="text",
                        text="Error: Invalid screenshot data"
                    )]
                
                img_height, img_width = img.shape[:2]
                
                # Validate coordinates
                if x < 0 or y < 0 or x + width > img_width or y + height > img_height:
                    return [TextContent(
                        type="text",
                        text=f"Error: Region coordinates out of bounds. Image size: {img_width}x{img_height}"
                    )]
            except Exception as e:
                logger.error(f"Error validating screenshot: {e}")
        
        # Return region information
        region_info = {
            "region_name": region_name,
            "coordinates": {
                "x": x,
                "y": y,
                "width": width,
                "height": height
            },
            "ready_for_monitoring": True
        }
        
        return [TextContent(
            type="text",
            text=f"Region selected:\n{json.dumps(region_info, indent=2)}\n\n"
                 f"You can now use this region with start_visual_monitoring or start_workflow tools."
        )]
    
    async def _handle_select_region_interactive(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handle select_region_interactive tool call"""
        if not VISUAL_ANALYZER_AVAILABLE or not self.visual_analyzer:
            return [TextContent(
                type="text",
                text="Visual analyzer not available. Install dependencies: pip install opencv-python"
            )]
        
        screenshot_base64 = arguments.get("screenshot_base64")
        
        if not screenshot_base64:
            return [TextContent(
                type="text",
                text="Error: screenshot_base64 is required"
            )]
        
        # Use interactive selection
        result = self.visual_analyzer.select_region_interactive(
            screenshot_base64=screenshot_base64
        )
        
        if result is None:
            return [TextContent(
                type="text",
                text="Region selection was cancelled. Press ESC or close the window to cancel."
            )]
        
        return [TextContent(
            type="text",
            text=f"Region selected interactively:\n{json.dumps(result, indent=2)}\n\n"
                 f"Instructions:\n"
                 f"1. A window will open showing the screenshot\n"
                 f"2. Click and drag to select a rectangle\n"
                 f"3. Press SPACE or ENTER to confirm\n"
                 f"4. Press ESC to cancel\n\n"
                 f"You can now use this region with start_visual_monitoring or start_workflow tools."
        )]
    
    async def _handle_start_workflow(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handle start_workflow tool call"""
        if not ORCHESTRATOR_AVAILABLE or not self.orchestrator:
            return [TextContent(
                type="text",
                text="Workflow orchestrator not available. Install dependencies: pip install opencv-python mss numpy pymem"
            )]
        
        process_name = arguments.get("process_name")
        process_id = arguments.get("process_id")
        regions = arguments.get("regions", [])
        value_type = arguments.get("value_type", "int32")
        
        # Update orchestrator process info if provided
        if process_name:
            self.orchestrator.process_name = process_name
        if process_id:
            self.orchestrator.process_id = process_id
        
        # Connect orchestrator to RE adapter if available
        if self.current_adapter:
            self.orchestrator.re_adapter = self.current_adapter
        
        # Start workflow
        result = self.orchestrator.start_workflow(regions, value_type)
        
        if result["success"]:
            return [TextContent(
                type="text",
                text=f"Workflow started:\n{json.dumps(result, indent=2)}"
            )]
        else:
            return [TextContent(
                type="text",
                text=f"Failed to start workflow: {result.get('error', 'Unknown error')}"
            )]
    
    async def _handle_stop_workflow(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handle stop_workflow tool call"""
        if not ORCHESTRATOR_AVAILABLE or not self.orchestrator:
            return [TextContent(
                type="text",
                text="Workflow orchestrator not available"
            )]
        
        result = self.orchestrator.stop_workflow()
        
        return [TextContent(
            type="text",
            text=f"Workflow stopped:\n{json.dumps(result, indent=2)}"
        )]
    
    async def _handle_get_workflow_status(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handle get_workflow_status tool call"""
        if not ORCHESTRATOR_AVAILABLE or not self.orchestrator:
            return [TextContent(
                type="text",
                text="Workflow orchestrator not available"
            )]
        
        status = self.orchestrator.get_workflow_status()
        
        return [TextContent(
            type="text",
            text=f"Workflow status:\n{json.dumps(status, indent=2, default=str)}"
        )]
    
    async def _handle_set_breakpoints_at_addresses(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handle set_breakpoints_at_addresses tool call"""
        if not ORCHESTRATOR_AVAILABLE or not self.orchestrator:
            return [TextContent(
                type="text",
                text="Workflow orchestrator not available"
            )]
        
        if not self.current_adapter:
            return [TextContent(
                type="text",
                text="No reverse engineering tool connected. Use detect_re_tool first."
            )]
        
        addresses = arguments.get("addresses", [])
        
        # Set breakpoints via orchestrator
        result = self.orchestrator.set_breakpoints(addresses)
        
        if result["success"]:
            # Actually set breakpoints using adapter
            breakpoint_results = []
            for addr in result["addresses"]:
                bp_result = self.current_adapter.set_breakpoint(
                    int(addr, 16) if isinstance(addr, str) else addr,
                    "write"  # Hardware write breakpoint
                )
                breakpoint_results.append({
                    "address": addr,
                    "success": bp_result.success,
                    "error": bp_result.error
                })
            
            return [TextContent(
                type="text",
                text=f"Breakpoints set:\n{json.dumps({'summary': result, 'breakpoints': breakpoint_results}, indent=2)}"
            )]
        else:
            return [TextContent(
                type="text",
                text=f"Failed to set breakpoints: {result.get('error', 'Unknown error')}"
            )]
    
    def _get_tool_status(self) -> Dict[str, Any]:
        """Get current tool status"""
        if self.current_adapter:
            return {
                "adapter": self.current_adapter.get_tool_info(),
                "connected": self.current_adapter.is_connected
            }
        else:
            detected = self.tool_detector.detect_available()
            if detected:
                return {
                    "tool_type": detected.tool_type.value,
                    "is_available": detected.is_available,
                    "install_path": str(detected.install_path) if detected.install_path else None,
                    "connected": False
                }
            return {"tool_type": "none", "is_available": False, "connected": False}
    
    async def run(self):
        """Run the MCP server"""
        logger.info("Starting MCP Server...")
        logger.info(f"Server: {self.config.server_name} v{self.config.server_version}")
        
        # Run server with stdio transport
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options()
            )

