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

logger = logging.getLogger(__name__)

class BackendInterface:
    def __init__(self, host: str = "localhost", port: int = 5440):
        self.host = host
        self.port = port
        self.server = None
        self.client_task = None
        self.loop = None
        self.project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    async def start_server(self):
        """Start the WebSocket server"""
        try:
            self.server = await websockets.serve(
                self.websocket_handler,  # Changed from _websocket_handler
                self.host,
                self.port
            )
            logger.info(f"WebSocket server running on {self.host}:{self.port}")
        except Exception as e:
            logger.error(f"Failed to start server: {e}")
            raise

    async def websocket_handler(self, websocket):  # Removed path parameter
        """Handle WebSocket connections"""
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

    async def send_test_config(self, config: Dict[str, Any]):
        """Send test configuration to server"""
        uri = f"ws://{self.host}:{self.port}"

        try:
            async with websockets.connect(uri) as websocket:
                logger.info(f"Client connected to {uri}")

                # Ensure config has required fields
                config.update({
                    "socket-type": "ws",  # Using WebSocket mode
                    "command": "Display Barcode"
                })

                # Send configuration
                await websocket.send(json.dumps(config))
                logger.info(f"Sent config: {config}")

                # Wait for responses
                while True:
                    try:
                        response = await websocket.recv()
                        data = json.loads(response)
                        logger.info(f"Received response: {data}")

                        if data.get("status") == "progress":
                            # Emit progress update
                            progress = data.get("progress", 0)
                            logger.info(f"Progress: {progress}%")
                        elif data.get("status") == "complete":
                            logger.info("Test completed successfully")
                            return True
                        elif data.get("status") == "error":
                            logger.error(f"Test error: {data.get('message')}")
                            raise RuntimeError(data.get("message"))
                    except json.JSONDecodeError:
                        logger.warning(f"Invalid JSON response: {response}")

        except Exception as e:
            logger.error(f"Client error: {e}")
            raise

    def run_quick_test(self, barcode_path: str):
        """Run quick test with default parameters"""
        config = {
            "command": "Display Barcode",
            "Presigned URL": "",
            "pre-test": "no",
            "known_barcode": "yes",  # Using known_barcode directory
            "barcode-type": "code128",
            "socket-type": "ws",  # Using WebSocket mode
            "transformations": {
                "rotation": 0.0,
                "scale": 1.0,
                "mirror": False
            },
            "barcode_path": barcode_path
        }

        # Create and run event loop
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

        try:
            # Start server
            self.loop.run_until_complete(self.start_server())

            # Send test config
            self.loop.run_until_complete(self.send_test_config(config))

        except Exception as e:
            logger.error(f"Error running quick test: {e}")
            raise
        finally:
            self.cleanup()

    def run_custom_test(self, config: Dict[str, Any]):
        """Run custom test with specified parameters"""
        # Ensure required fields
        config.update({
            "command": "Display Barcode",
            "Presigned URL": "",
            "socket-type": "ws"  # Using WebSocket mode
        })

        # Create and run event loop
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

        try:
            # Start server
            self.loop.run_until_complete(self.start_server())

            # Send test config
            self.loop.run_until_complete(self.send_test_config(config))

        except Exception as e:
            logger.error(f"Error running custom test: {e}")
            raise
        finally:
            self.cleanup()

    def cleanup(self):
        """Cleanup resources"""
        if self.loop and not self.loop.is_closed():
            if self.server:
                self.server.close()
                self.loop.run_until_complete(self.server.wait_closed())
            self.loop.close()
