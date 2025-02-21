"""
Backend interface for E-Ink Testing Interface
Handles communication with app.py websocket server
"""

import asyncio
import websockets
import json
import os
from typing import Dict, Any, Optional
import sys
import signal
import logging
import socket
import time
import weakref

logger = logging.getLogger(__name__)

class BackendInterface:
    # Class variable to track the active server instance
    _active_instance = None

    def __init__(self, host: str = "localhost", port: int = 5440):
        self.host = host
        self.port = port
        self.server = None
        self.client_task = None
        self.loop = None
        self.active_connections = set()
        self.project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

        # Register this instance
        if BackendInterface._active_instance is not None:
            # Close the previous instance
            prev_instance = BackendInterface._active_instance()
            if prev_instance is not None:
                logger.info("Closing previous backend instance")
                if prev_instance.loop and not prev_instance.loop.is_closed():
                    try:
                        prev_instance.loop.run_until_complete(prev_instance.close_server())
                    except Exception as e:
                        logger.error(f"Error closing previous instance: {e}")

        # Use weak reference to allow garbage collection
        BackendInterface._active_instance = weakref.ref(self)

    def _is_port_available(self):
        """Check if port is available without killing anything"""
        try:
            # Try to create a socket
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(1)
                result = sock.connect_ex(('127.0.0.1', self.port))
                return result != 0
        except Exception as e:
            logger.error(f"Error checking port availability: {e}")
            return False

    async def start_server(self):
        """Start the WebSocket server"""
        try:
            # Close any existing server first
            await self.close_server()

            # Wait briefly for cleanup
            await asyncio.sleep(0.5)

            # Check port availability
            if not self._is_port_available():
                logger.warning(f"Port {self.port} is in use, waiting...")
                for _ in range(10):  # Try for 5 seconds
                    await asyncio.sleep(0.5)
                    if self._is_port_available():
                        break
                else:
                    raise RuntimeError(f"Port {self.port} is still in use after waiting")

            # Create new event loop if needed
            if not self.loop or self.loop.is_closed():
                self.loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self.loop)

            self.server = await websockets.serve(
                self.websocket_handler,
                self.host,
                self.port
            )
            logger.info(f"WebSocket server running on {self.host}:{self.port}")

        except Exception as e:
            logger.error(f"Failed to start server: {e}")
            raise

    async def close_server(self):
        """Close the WebSocket server if it exists"""
        if self.server:
            # Close all active connections
            for ws in self.active_connections.copy():
                try:
                    await ws.close()
                except Exception as e:
                    logger.debug(f"Error closing connection: {e}")
            self.active_connections.clear()

            # Close server
            self.server.close()
            await self.server.wait_closed()
            self.server = None
            logger.info("WebSocket server closed")

    async def websocket_handler(self, websocket):
        """Handle WebSocket connections"""
        self.active_connections.add(websocket)
        logger.info(f"New client connected from {websocket.remote_address}")

        try:
            data = await websocket.recv()
            json_data = json.loads(data)
            logger.info("Message Received: %s", json_data)

            if isinstance(json_data, dict):
                if json_data.get('command') == "Display Barcode":
                    # Import here to avoid circular imports
                    from test import testing
                    await testing(websocket, json_data, project_root=self.project_root)
                else:
                    await websocket.send(json.dumps({
                        "status": "error",
                        "message": "Unknown command"
                    }))
            else:
                await websocket.send(json.dumps({
                    "status": "error",
                    "message": "Invalid JSON data"
                }))
        except Exception as e:
            logger.error(f"WebSocket handler error: {e}")
            await websocket.send(json.dumps({
                "status": "error",
                "message": str(e)
            }))
        finally:
            self.active_connections.discard(websocket)

    def cleanup(self):
        """Cleanup resources"""
        try:
            if self.loop and not self.loop.is_closed():
                # Close server
                if self.server:
                    self.loop.run_until_complete(self.close_server())
                # Close loop
                self.loop.close()
                self.loop = None

            # Clear active connections
            self.active_connections.clear()

            # Clear class instance if this is the active one
            if BackendInterface._active_instance is not None:
                if BackendInterface._active_instance() is self:
                    BackendInterface._active_instance = None

            # Wait a moment for cleanup
            time.sleep(0.1)

        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
        logger.info("Backend interface cleaned up")
