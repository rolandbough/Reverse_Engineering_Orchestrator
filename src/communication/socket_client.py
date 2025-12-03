"""
TCP Socket Client for Component Communication

ADR Note: TCP client for sending messages to other components.
Used by Visual Analyzer to send messages to Memory Scanner,
and by Memory Scanner to send messages to MCP Server.
"""

import socket
import logging
from typing import Optional

from .message_protocol import Message, MessageCodec

logger = logging.getLogger(__name__)


class ComponentClient:
    """
    TCP client for component communication
    
    ADR Note: Connects to a component server and sends messages.
    Handles reconnection and error recovery.
    """
    
    def __init__(self, host: str = "127.0.0.1", port: int = 0):
        """
        Initialize component client
        
        Args:
            host: Host address to connect to
            port: Port to connect to
        """
        self.host = host
        self.port = port
        self.socket: Optional[socket.socket] = None
        self.connected = False
    
    def connect(self) -> bool:
        """
        Connect to the server
        
        Returns:
            True if connected successfully, False otherwise
        """
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            self.connected = True
            logger.info(f"Connected to {self.host}:{self.port}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to {self.host}:{self.port}: {e}")
            self.connected = False
            return False
    
    def disconnect(self):
        """Disconnect from the server"""
        if self.socket:
            try:
                self.socket.close()
            except Exception:
                pass
            self.socket = None
        self.connected = False
        logger.info("Disconnected from server")
    
    def send_message(self, message: Message) -> bool:
        """
        Send a message to the server
        
        Args:
            message: Message to send
        
        Returns:
            True if sent successfully, False otherwise
        """
        if not self.connected or not self.socket:
            logger.warning("Not connected, attempting to reconnect...")
            if not self.connect():
                return False
        
        try:
            data = MessageCodec.encode(message)
            # Add newline for message separation
            self.socket.sendall(data + b"\n")
            logger.debug(f"Sent {message.message_type} to {self.host}:{self.port}")
            return True
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            self.connected = False
            return False
    
    def is_connected(self) -> bool:
        """Check if client is connected"""
        return self.connected and self.socket is not None

