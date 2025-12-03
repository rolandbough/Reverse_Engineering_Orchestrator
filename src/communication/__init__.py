"""
Component Communication Layer

ADR Note: Provides TCP socket-based communication between components:
- Visual Analyzer → Memory Scanner
- Memory Scanner → MCP Server
- MCP Server → Visual Analyzer (for coordination)
"""

from .message_protocol import Message, MessageType, MessageCodec
from .socket_server import ComponentServer
from .socket_client import ComponentClient

__all__ = [
    "Message",
    "MessageType",
    "MessageCodec",
    "ComponentServer",
    "ComponentClient",
]

