"""
Server Configuration

ADR Note: Configuration uses environment variables and defaults to allow
flexible deployment. Sensible defaults ensure the server works out of the box.
"""

import os
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field


class ServerConfig(BaseModel):
    """
    MCP Server Configuration
    
    ADR Note: Using Pydantic for configuration validation and type safety.
    Environment variables can override defaults, allowing easy deployment
    without code changes.
    """
    
    # Server settings
    server_name: str = Field(default="reverse-engineering-orchestrator")
    server_version: str = Field(default="0.1.0")
    log_level: str = Field(default="INFO")
    log_file: Optional[Path] = Field(default=None)
    
    # Tool detection settings
    auto_detect_tools: bool = Field(default=True)
    preferred_tool: Optional[str] = Field(default=None)  # "ida" or "ghidra"
    
    # IDA Pro settings
    ida_path: Optional[Path] = Field(default=None)
    ida_python_path: Optional[Path] = Field(default=None)
    
    # Ghidra settings
    ghidra_install_dir: Optional[Path] = Field(default=None)
    ghidra_bridge_port: int = Field(default=1337)
    
    # MCP settings
    mcp_transport: str = Field(default="stdio")  # stdio or http
    
    @classmethod
    def from_env(cls) -> "ServerConfig":
        """
        Create configuration from environment variables
        
        ADR Note: Environment variables allow configuration without code changes.
        This is especially useful for deployment and testing.
        """
        return cls(
            server_name=os.getenv("REO_SERVER_NAME", "reverse-engineering-orchestrator"),
            server_version=os.getenv("REO_SERVER_VERSION", "0.1.0"),
            log_level=os.getenv("REO_LOG_LEVEL", "INFO"),
            log_file=Path(os.getenv("REO_LOG_FILE")) if os.getenv("REO_LOG_FILE") else None,
            auto_detect_tools=os.getenv("REO_AUTO_DETECT", "true").lower() == "true",
            preferred_tool=os.getenv("REO_PREFERRED_TOOL"),  # "ida" or "ghidra"
            ida_path=Path(os.getenv("IDA_PATH")) if os.getenv("IDA_PATH") else None,
            ida_python_path=Path(os.getenv("IDA_PYTHON_PATH")) if os.getenv("IDA_PYTHON_PATH") else None,
            ghidra_install_dir=Path(os.getenv("GHIDRA_INSTALL_DIR")) if os.getenv("GHIDRA_INSTALL_DIR") else None,
            ghidra_bridge_port=int(os.getenv("GHIDRA_BRIDGE_PORT", "1337")),
            mcp_transport=os.getenv("REO_MCP_TRANSPORT", "stdio"),
        )

