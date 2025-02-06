import asyncio
import websockets
import json
import sys

async def test(ip):
    uri = f"ws://{ip}:5440"
    data = {
        "command": "Display Barcode",
        "Presigned URL":"",
        "pre-test" : "no",
        "barcode-type": "code128",
        "socket-type": "ss",
        "transformations": {
            "rotation": 180,
            "scale": 1
        }
    }

    # Serialize JSON data to string
    json_data = json.dumps(data)

    try:
        async with websockets.connect(uri) as websocket:
            print(f"Connected to {uri}")
            # Send JSON string data
            await websocket.send(json_data)
            # Receive response
            response = await websocket.recv()
            print(f"Response: {response}")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script.py <ip_address>")
        sys.exit(1)

    ip_address = sys.argv[1]
    
    # Start the event loop and run the test coroutine
    asyncio.run(test(ip_address))