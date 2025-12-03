"""
TCP Socket Server for Component Communication

ADR Note: TCP server for receiving messages from other components.
Used by Memory Scanner and MCP Server to receive messages from
Visual Analyzer and other components.
"""

import socket
import threading
import logging
from typing import Callable, Optional, Dict
from queue import Queue

from .message_protocol import Message, MessageCodec

logger = logging.getLogger(__name__)


class ComponentServer:
    """
    TCP server for component communication
    
    ADR Note: Listens for incoming connections and messages from other components.
    Messages are handled by registered callback functions. Supports multiple
    concurrent connections.
    """
    
    def __init__(self, host: str = "127.0.0.1", port: int = 0):
        """
        Initialize component server
        
        Args:
            host: Host address to bind to
            port: Port to bind to (0 = auto-select)
        """
        self.host = host
        self.port = port
        self.socket: Optional[socket.socket] = None
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self.message_handlers: Dict[str, Callable[[Message], None]] = {}
        self.connections: list[socket.socket] = []
        self.message_queue = Queue()
    
    def register_handler(self, message_type: str, handler: Callable[[Message], None]):
        """
        Register a message handler
        
        Args:
            message_type: Type of message to handle
            handler: Callback function to call when message received
        """
        self.message_handlers[message_type] = handler
        logger.debug(f"Registered handler for {message_type}")
    
    def start(self) -> int:
        """
        Start the server
        
        Returns:
            Port number the server is listening on
        """
        if self.running:
            logger.warning("Server already running")
            return self.port
        
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((self.host, self.port))
        self.socket.listen(5)
        
        # Get actual port (if 0 was specified)
        self.port = self.socket.getsockname()[1]
        
        self.running = True
        self.thread = threading.Thread(target=self._accept_connections, daemon=True)
        self.thread.start()
        
        logger.info(f"Component server started on {self.host}:{self.port}")
        return self.port
    
    def stop(self):
        """Stop the server"""
        self.running = False
        
        if self.socket:
            try:
                self.socket.close()
            except Exception:
                pass
        
        # Close all connections
        for conn in self.connections:
            try:
                conn.close()
            except Exception:
                pass
        
        self.connections.clear()
        logger.info("Component server stopped")
    
    def _accept_connections(self):
        """Accept incoming connections"""
        while self.running:
            try:
                conn, addr = self.socket.accept()
                logger.info(f"Connection from {addr}")
                self.connections.append(conn)
                
                # Handle connection in separate thread
                thread = threading.Thread(
                    target=self._handle_connection,
                    args=(conn, addr),
                    daemon=True
                )
                thread.start()
            
            except Exception as e:
                if self.running:
                    logger.error(f"Error accepting connection: {e}")
    
    def _handle_connection(self, conn: socket.socket, addr: tuple):
        """Handle messages from a connection"""
        try:
            buffer = b""
            while self.running:
                data = conn.recv(4096)
                if not data:
                    break
                
                buffer += data
                
                # Try to parse complete messages
                # Simple protocol: messages are newline-separated JSON
                while b"\n" in buffer:
                    line, buffer = buffer.split(b"\n", 1)
                    if line:
                        try:
                            message = MessageCodec.decode(line)
                            self._handle_message(message, conn, addr)
                        except Exception as e:
                            logger.error(f"Failed to handle message: {e}")
        
        except Exception as e:
            logger.error(f"Error handling connection from {addr}: {e}")
        finally:
            try:
                conn.close()
                if conn in self.connections:
                    self.connections.remove(conn)
            except Exception:
                pass
    
    def _handle_message(self, message: Message, conn: socket.socket, addr: tuple):
        """Handle a received message"""
        logger.debug(f"Received {message.message_type} from {addr}")
        
        # Put message in queue for processing
        self.message_queue.put((message, conn, addr))
        
        # Call registered handler if available
        handler = self.message_handlers.get(message.message_type.value)
        if handler:
            try:
                handler(message)
            except Exception as e:
                logger.error(f"Error in message handler: {e}")
        else:
            logger.debug(f"No handler registered for {message.message_type}")

