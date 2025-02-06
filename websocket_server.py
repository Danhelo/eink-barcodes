import asyncio
import websockets
import socket
import fcntl
import struct
import zipfile
from sys import path
import os
import io
import requests
import re
from test import *
from test_functions import *


async def download_and_unzip_s3_file(websocket, s3_url, extract_to='.'):
    """
    Downloads a ZIP file from an S3 URL and extracts its contents.

    Parameters:
    - s3_url (str): The URL of the ZIP file on S3.
    - extract_to (str): The directory to extract the contents to. Defaults to the current directory.

    """
    # Download the file
    print("URL Received:", s3_url)
    response = requests.get(s3_url)
    response.raise_for_status()
    
    try:
    # Create a ZipFile object
        with zipfile.ZipFile(io.BytesIO(response.content)) as zip_ref:
            # Extract all the contents into the specified directory
            zip_ref.extractall(extract_to)
        
        message = f"done"

        await websocket.send(bytes(message,'utf-8'))

    except Exception as e:
    # Handle the exception
        error_message = f"Error extracting contents: {str(e)}"
        
        # Send the error message back through the websocket
        await websocket.send(bytes(error_message, 'utf-8')) 

def get_ip_address(ifname):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    return socket.inet_ntoa(fcntl.ioctl(
        s.fileno(),
        0x8915,  # SIOCGIFADDR
        struct.pack('256s', bytes(ifname[:15], 'utf-8'))
    )[20:24])


# create handler for each connection
async def handler(websocket):
    print(f"New client connected from {websocket.remote_address}")    

    try:
        data = await websocket.recv()
        json_data = json.loads(data)
        print("Message Received:", json_data)

        if isinstance(json_data, dict):
            if json_data.get('command') == "Display Barcode":
                await testing(websocket, json_data)

            elif 'Presigned URL' in json_data:
                url = json_data.get('Presigned URL')
                await download_and_unzip_s3_file(websocket, url, extract_to = 'testing-barcode')

            else:
                await websocket.send("Unknown command or data format")

        else:
            await websocket.send("Invalid JSON data")

    except json.JSONDecodeError:
        await websocket.send("Invalid JSON format")
        
    except Exception as e:
        await websocket.send(f"An error occurred: {str(e)}")


async def main():
    interface = 'eth1'  # Replace with the correct network interface
    ip_address = get_ip_address(interface)

    host = ip_address
    port = 5440
    print(f"Creating WebSocket Server with host {host} and port {port}")

    start_server = await websockets.serve(handler, host, port)
    await asyncio.Future()

# Entry point for the asyncio event loop
if __name__ == "__main__":
    asyncio.run(main())
        


