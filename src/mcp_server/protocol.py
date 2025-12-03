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

