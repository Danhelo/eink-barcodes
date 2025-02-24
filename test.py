import argparse
import json
import time
import socket
import signal
import sys
import csv
from test_functions import *
from time import sleep

def parse_display_args(virtual=False, mirror=False):
    """Create a namespace object with display configuration"""
    class DisplayArgs:
        def __init__(self):
            self.virtual = virtual
            self.mirror = mirror
    return DisplayArgs()

def display_connection(virtual=False, mirror=False):
    """Initialize display with given configuration"""
    args = parse_display_args(virtual, mirror)
    tests = []

    if not args.virtual:
        from IT8951.display import AutoEPDDisplay

        print('Initializing EPD...')

        # here, spi_hz controls the rate of data transfer to the device, so a higher
        # value means faster display refreshes. the documentation for the IT8951 device
        # says the max is 24 MHz (24000000), but my device seems to still work as high as
        # 80 MHz (80000000)
        display = AutoEPDDisplay(vcom=-2.02, mirror=args.mirror, spi_hz=24000000)

        print('VCOM set to', display.epd.get_vcom())

        tests += [print_system_info]

    else:
        from IT8951.display import VirtualEPDDisplay
        display = VirtualEPDDisplay(dims=(800, 600), mirror=args.mirror)

    return display, tests

async def testing(websocket, msg, project_root=None):
    print(msg)
    try:
        success = False
        # Get mirror setting from transformations if present
        mirror = msg.get('transformations', {}).get('mirror', False)

        # Initialize display with mirror setting only
        display, tests = display_connection(
            virtual=False,  # Always use real display when called from app.py
            mirror=mirror
        )

        print("Display connected, starting to display barcode.....")
        clear_display(display)
        await display_image_8bpp(websocket, display, msg, project_root)

        success = True
        # Send success message
        await websocket.send(json.dumps({
            "status": "success",
            "message": "Test completed successfully"
        }))

        # Mark test as completed
        await websocket.send(json.dumps({"status": "complete"}))

    except Exception as e:
        # Send error message
        await websocket.send(json.dumps({
            "status": "error",
            "message": str(e)
        }))
        raise

if __name__ == "__main__":
    # This section only runs when test.py is run directly, not when imported
    parser = argparse.ArgumentParser(description='Test EPD functionality')
    parser.add_argument('-v', '--virtual', action='store_true',
                       help='display using a Tkinter window instead of the '
                            'actual e-paper device (for testing without a '
                            'physical device)')
    parser.add_argument('-m', '--mirror', action='store_true',
                       help='Mirror the display (use this if text appears backwards)')
    args = parser.parse_args()

    display, tests = display_connection(args.virtual, args.mirror)

    # Run any standalone tests here when script is run directly
    for test in tests:
        test(display)
