"""
Message Protocol for Component Communication

ADR Note: JSON-based message protocol for inter-component communication.
Messages are structured JSON objects with type, payload, and metadata.
This allows components to communicate reliably over TCP sockets.
"""

import json
import logging
from dataclasses import dataclass, asdict
from enum import Enum
from typing import Any, Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class MessageType(str, Enum):
    """Types of messages in the communication protocol"""
    # Visual Analyzer messages
    VISUAL_CHANGE = "visual_change"  # UI change detected
    VALUE_EXTRACTED = "value_extracted"  # Value extracted from UI
    
    # Memory Scanner messages
    SCAN_REQUEST = "scan_request"  # Request to scan for value
    SCAN_RESULT = "scan_result"  # Scan results with addresses
    FILTER_REQUEST = "filter_request"  # Request to filter scan
    FILTER_RESULT = "filter_result"  # Filtered scan results
    
    # MCP Server messages
    BREAKPOINT_SET = "breakpoint_set"  # Breakpoint set at address
    BREAKPOINT_HIT = "breakpoint_hit"  # Breakpoint triggered
    DECOMPILE_REQUEST = "decompile_request"  # Request decompilation
    DECOMPILE_RESULT = "decompile_result"  # Decompiled code
    
    # Control messages
    PING = "ping"  # Keep-alive ping
    PONG = "pong"  # Keep-alive pong
    ERROR = "error"  # Error message
    STATUS = "status"  # Status update


@dataclass
class Message:
    """
    Communication message between components
    
    ADR Note: All messages use this structure for consistency.
    Messages are serialized to JSON for transmission over TCP sockets.
    """
    message_type: MessageType
    payload: Dict[str, Any]
    timestamp: Optional[str] = None
    source: Optional[str] = None  # Component that sent the message
    message_id: Optional[str] = None  # Unique message ID for tracking
    
    def __post_init__(self):
        """Set timestamp if not provided"""
        if self.timestamp is None:
            self.timestamp = datetime.utcnow().isoformat()
    
    def to_json(self) -> str:
        """Serialize message to JSON"""
        return json.dumps(asdict(self), default=str)
    
    @classmethod
    def from_json(cls, json_str: str) -> "Message":
        """Deserialize message from JSON"""
        try:
            data = json.loads(json_str)
            # Convert message_type string back to enum
            if isinstance(data.get("message_type"), str):
                data["message_type"] = MessageType(data["message_type"])
            return cls(**data)
        except Exception as e:
            logger.error(f"Failed to parse message: {e}")
            raise


class MessageCodec:
    """
    Encoder/decoder for messages
    
    ADR Note: Handles serialization and deserialization of messages.
    Provides error handling and validation.
    """
    
    @staticmethod
    def encode(message: Message) -> bytes:
        """
        Encode message to bytes for transmission
        
        Args:
            message: Message to encode
        
        Returns:
            UTF-8 encoded JSON bytes
        """
        try:
            json_str = message.to_json()
            return json_str.encode('utf-8')
        except Exception as e:
            logger.error(f"Failed to encode message: {e}")
            raise
    
    @staticmethod
    def decode(data: bytes) -> Message:
        """
        Decode bytes to message
        
        Args:
            data: UTF-8 encoded JSON bytes
        
        Returns:
            Decoded Message object
        """
        try:
            json_str = data.decode('utf-8')
            return Message.from_json(json_str)
        except Exception as e:
            logger.error(f"Failed to decode message: {e}")
            raise
    
    @staticmethod
    def create_visual_change(
        value: Any,
        coordinates: Dict[str, int],
        source: str = "visual_analyzer"
    ) -> Message:
        """Create a visual change message"""
        return Message(
            message_type=MessageType.VISUAL_CHANGE,
            payload={
                "value": value,
                "coordinates": coordinates,
                "timestamp": datetime.utcnow().isoformat()
            },
            source=source
        )
    
    @staticmethod
    def create_scan_request(
        value: Any,
        value_type: str,
        scan_type: str = "exact",
        source: str = "mcp_server"
    ) -> Message:
        """Create a scan request message"""
        return Message(
            message_type=MessageType.SCAN_REQUEST,
            payload={
                "value": value,
                "value_type": value_type,
                "scan_type": scan_type
            },
            source=source
        )
    
    @staticmethod
    def create_scan_result(
        addresses: list[str],
        count: int,
        source: str = "memory_scanner"
    ) -> Message:
        """Create a scan result message"""
        return Message(
            message_type=MessageType.SCAN_RESULT,
            payload={
                "addresses": addresses,
                "count": count
            },
            source=source
        )
    
    @staticmethod
    def create_error(
        error: str,
        source: str = "unknown"
    ) -> Message:
        """Create an error message"""
        return Message(
            message_type=MessageType.ERROR,
            payload={"error": error},
            source=source
        )

