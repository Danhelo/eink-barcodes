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

class BackendInterface:
    def __init__(self, host: str = "localhost", port: int = 5440):
        self.host = host
        self.port = port
        self.server = None
        self.client_task = None
        self.loop = None

    async def start_server(self):
        """Start the WebSocket server"""
        try:
            self.server = await websockets.serve(
                self._websocket_handler,
                self.host,
                self.port
            )
            print(f"WebSocket server running on {self.host}:{self.port}")
        except Exception as e:
            print(f"Failed to start server: {e}")
            raise

    async def _websocket_handler(self, websocket, path):
        """Handle WebSocket connections"""
        print(f"New client connected from {websocket.remote_address}")
        try:
            data = await websocket.recv()
            json_data = json.loads(data)
            print("Message Received:", json_data)

            if isinstance(json_data, dict):
                if json_data.get('command') == "Display Barcode":
                    from test import testing
                    await testing(websocket, json_data, project_root=os.path.dirname(os.path.abspath(__file__)))
                else:
                    await websocket.send("Unknown command")
            else:
                await websocket.send("Invalid JSON data")
        except Exception as e:
            await websocket.send(f"Error: {str(e)}")

    async def send_test_config(self, config: Dict[str, Any]):
        """Send test configuration to server"""
        uri = f"ws://{self.host}:{self.port}"

        try:
            async with websockets.connect(uri) as websocket:
                print(f"Client connected to {uri}")
                await websocket.send(json.dumps(config))
                response = await websocket.recv()
                print(f"Server response: {response}")
                return response
        except Exception as e:
            print(f"Client error: {e}")
            raise

    def run_quick_test(self, barcode_path: str):
        """Run quick test with default parameters"""
        config = {
            "command": "Display Barcode",
            "Presigned URL": "",
            "pre-test": "no",
            "known_barcode": "yes",  # Using known_barcode directory
            "barcode-type": "code128",
            "socket-type": "ss",
            "transformations": {
                "rotation": 0.0,
                "scale": 1.0,
                "mirror": False
            },
            "barcode_path": barcode_path  # Added to specify which barcode to use
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
            print(f"Error running quick test: {e}")
            raise
        finally:
            if self.server:
                self.server.close()
                self.loop.run_until_complete(self.server.wait_closed())
            self.loop.close()

    def run_custom_test(self, rotation: float, scale: float, mirror: bool, barcode_type: str):
        """Run custom test with specified parameters"""
        # TODO: In the future, this will call the barcode generation API
        # For now, using known_barcode directory as placeholder
        config = {
            "command": "Display Barcode",
            "Presigned URL": "",
            "pre-test": "no",
            "known_barcode": "yes",
            "barcode-type": barcode_type,
            "socket-type": "ss",
            "transformations": {
                "rotation": rotation % 360.0,  # Normalize to 0-360
                "scale": min(max(scale, 0.1), 2.0),  # Clamp to 0.1-2.0
                "mirror": mirror
            }
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
            print(f"Error running custom test: {e}")
            raise
        finally:
            if self.server:
                self.server.close()
                self.loop.run_until_complete(self.server.wait_closed())
            self.loop.close()

    def cleanup(self):
        """Cleanup resources"""
        if self.loop and not self.loop.is_closed():
            if self.server:
                self.server.close()
                self.loop.run_until_complete(self.server.wait_closed())
            self.loop.close()
