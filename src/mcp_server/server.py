"""
MCP Server Implementation

ADR Note: Main entry point for MCP server. Uses protocol handler for
actual MCP communication. Provides high-level server management.
"""

import asyncio
import logging
from typing import Optional

from .config import ServerConfig
from .protocol import MCPProtocolHandler
from ..tool_detection import ToolDetector

logger = logging.getLogger(__name__)


class MCPServer:
    """
    Main MCP Server for Reverse Engineering Orchestrator
    
    ADR Note: Server handles MCP protocol communication via stdio (standard
    for Cursor). Tools and resources are registered and exposed to the AI agent.
    """
    
    def __init__(self, config: Optional[ServerConfig] = None):
        """Initialize MCP server"""
        self.config = config or ServerConfig.from_env()
        self.tool_detector = ToolDetector(
            preferred_tool=self.config.preferred_tool
        )
        
        # Initialize logging
        self._setup_logging()
        
        # Create protocol handler
        self.protocol_handler = MCPProtocolHandler(self.config, self.tool_detector)
        
        # Auto-detect tools on startup if configured
        if self.config.auto_detect_tools:
            detected = self.tool_detector.detect_available()
            if detected:
                logger.info(f"Detected tool: {detected.tool_type.value}")
            else:
                logger.warning("No reverse engineering tools detected")
    
    def _setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=getattr(logging, self.config.log_level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            filename=self.config.log_file,
        )
    
    def run(self):
        """
        Run the MCP server
        
        ADR Note: Runs async MCP server using stdio transport.
        This is the main entry point for the server.
        """
        logger.info("Starting MCP Server...")
        logger.info(f"Server: {self.config.server_name} v{self.config.server_version}")
        
        # Run async server
        asyncio.run(self.protocol_handler.run())

