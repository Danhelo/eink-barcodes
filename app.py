import asyncio
import websockets
import json
import os
import argparse
from test import testing
from test_functions import *
import sys
import signal

# Get the absolute path of the project root directory
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

# Ensure required directories exist
REQUIRED_DIRS = ['pre_test', 'known_barcode', 'code128']
for dir_name in REQUIRED_DIRS:
    dir_path = os.path.join(PROJECT_ROOT, dir_name)
    if not os.path.exists(dir_path):
        print(f"Creating directory: {dir_path}")
        os.makedirs(dir_path, exist_ok=True)

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Barcode Test Application')

    # Rotation argument (0, 90, 180, 270 degrees)
    parser.add_argument('-r', '--rotation', type=float, default=0.0,
                      help='Image rotation in degrees (preferably 0, 90, 180, or 270 for best results)')

    # Scale argument (0.1 to 2.0)
    parser.add_argument('-s', '--scale', type=float, default=1.0,
                      help='Image scale factor (0.1 to 2.0)')

    # Mirror argument
    parser.add_argument('-m', '--mirror', action='store_true',
                      help='Mirror the display output')

    # Barcode type argument
    parser.add_argument('-b', '--barcode-type', type=str, choices=['code128'],
                      default='code128', help='Barcode type (currently only code128 supported)')

    args = parser.parse_args()

    # Validate scale range
    if not 0.1 <= args.scale <= 2.0:
        parser.error("Scale must be between 0.1 and 2.0")

    # Normalize rotation to closest 90-degree increment
    args.rotation = args.rotation % 360.0
    if args.rotation not in [0, 90, 180, 270]:
        print(f"Warning: Rotation {args.rotation:.1f}° will be approximated to nearest 90° increment")
        args.rotation = round(args.rotation / 90) * 90 % 360
        print(f"Using rotation: {args.rotation:.1f}°")

    return args

async def websocket_handler(websocket, args):
    """Handler for WebSocket connections"""
    print(f"New client connected from {websocket.remote_address}")    
    try:
        data = await websocket.recv()
        json_data = json.loads(data)
        print("Message Received:", json_data)

        if isinstance(json_data, dict):
            if json_data.get('command') == "Display Barcode":
                # Update json_data with command line arguments
                json_data['barcode-type'] = args.barcode_type
                json_data['transformations'] = {
                    'rotation': args.rotation,
                    'scale': args.scale,
                    'mirror': args.mirror
                }
                # Pass the PROJECT_ROOT to the testing function
                await testing(websocket, json_data, project_root=PROJECT_ROOT)
            elif 'Presigned URL' in json_data:
                url = json_data.get('Presigned URL')
                await download_and_unzip_s3_file(websocket, url, extract_to='testing-barcode')
            else:
                await websocket.send("Unknown command or data format")
        else:
            await websocket.send("Invalid JSON data")
    except json.JSONDecodeError:
        await websocket.send("Invalid JSON format")
    except Exception as e:
        await websocket.send(f"An error occurred: {str(e)}")

async def start_server(host, port, args):
    """Start the WebSocket server"""
    print(f"Starting WebSocket server on {host}:{port}")
    server = await websockets.serve(
        lambda ws: websocket_handler(ws, args),
        host,
        port
    )
    return server

async def run_client(args):
    """Run the WebSocket client"""
    uri = "ws://localhost:5440"
    test_data = {
        "command": "Display Barcode",
        "Presigned URL": "",
        "pre-test": "no",
        "known_barcode": "no",
        "barcode-type": args.barcode_type,
        "socket-type": "ss",
        "transformations": {
            "rotation": args.rotation,
            "scale": args.scale,
            "mirror": args.mirror
        }
    }
    
    # Add delay to ensure server is ready
    await asyncio.sleep(2)
    
    try:
        async with websockets.connect(uri) as websocket:
            print(f"Client connected to {uri}")
            await websocket.send(json.dumps(test_data))
            response = await websocket.recv()
            print(f"Client received response: {response}")
    except Exception as e:
        print(f"Client error: {e}")

async def main():
    # Parse command line arguments
    args = parse_args()

    host = "localhost"
    port = 5440
    
    print(f"Project root directory: {PROJECT_ROOT}")
    print("Available directories:")
    for dir_name in REQUIRED_DIRS:
        dir_path = os.path.join(PROJECT_ROOT, dir_name)
        print(f"  - {dir_path} {'(exists)' if os.path.exists(dir_path) else '(missing)'}")

    print("\nConfiguration:")
    print(f"  Rotation: {args.rotation:.1f} degrees")
    print(f"  Scale: {args.scale:.2f}x")
    print(f"  Mirror: {'Yes' if args.mirror else 'No'}")
    print(f"  Barcode Type: {args.barcode_type}")

    # Start server
    server = await start_server(host, port, args)
    print("WebSocket server is running on localhost:5440")
    
    # Start client
    client_task = asyncio.create_task(run_client(args))
    
    try:
        # Wait for client to finish
        await client_task
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        server.close()
        await server.wait_closed()

def signal_handler(sig, frame):
    print("\nCtrl+C pressed. Cleaning up...")
    sys.exit(0)

if __name__ == "__main__":
    # Register signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    
    print("Starting barcode test application on localhost...")
    print("Press Ctrl+C to exit")
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nApplication terminated by user")
