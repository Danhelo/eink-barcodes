import argparse
import json
import time
import socket
import signal
import sys
import csv
from test_functions import *
from time import sleep

def parse_display_args(virtual=False, rotate=None, mirror=False):
    """Create a namespace object with display configuration"""
    class DisplayArgs:
        def __init__(self):
            self.virtual = virtual
            self.rotate = rotate
            self.mirror = mirror
    return DisplayArgs()

def display_connection(virtual=False, rotate=None, mirror=False):
    """Initialize display with given configuration"""
    args = parse_display_args(virtual, rotate, mirror)
    tests = []

    if not args.virtual:
        from IT8951.display import AutoEPDDisplay

        print('Initializing EPD...')

        # here, spi_hz controls the rate of data transfer to the device, so a higher
        # value means faster display refreshes. the documentation for the IT8951 device
        # says the max is 24 MHz (24000000), but my device seems to still work as high as
        # 80 MHz (80000000)
        display = AutoEPDDisplay(vcom=-2.02, rotate=args.rotate, mirror=args.mirror, spi_hz=24000000)

        print('VCOM set to', display.epd.get_vcom())

        tests += [print_system_info]

    else:
        from IT8951.display import VirtualEPDDisplay
        display = VirtualEPDDisplay(dims=(800, 600), rotate=args.rotate, mirror=args.mirror)

    return display, tests

async def testing(websocket, msg, project_root=None):
    print(msg)
    # Convert rotation from degrees to EPD rotation format
    rotation = msg.get('transformations', {}).get('rotation', 0)
    if rotation == 90:
        epd_rotation = 'CW'
    elif rotation == 180:
        epd_rotation = 'flip'
    elif rotation == 270:
        epd_rotation = 'CCW'
    else:
        epd_rotation = None  # No rotation

    # Get mirror setting from transformations if present
    mirror = msg.get('transformations', {}).get('mirror', False)

    # Initialize display with rotation and mirror settings
    display, tests = display_connection(
        virtual=False,  # Always use real display when called from app.py
        rotate=epd_rotation,
        mirror=mirror
    )

    print("Display connected, starting to display barcode.....")
    clear_display(display)
    await display_image_8bpp(websocket, display, msg, project_root)

if __name__ == "__main__":
    # This section only runs when test.py is run directly, not when imported
    parser = argparse.ArgumentParser(description='Test EPD functionality')
    parser.add_argument('-v', '--virtual', action='store_true',
                       help='display using a Tkinter window instead of the '
                            'actual e-paper device (for testing without a '
                            'physical device)')
    parser.add_argument('-r', '--rotate', default=None, choices=['CW', 'CCW', 'flip'],
                       help='run the tests with the display rotated by the specified value')
    parser.add_argument('-m', '--mirror', action='store_true',
                       help='Mirror the display (use this if text appears backwards)')
    args = parser.parse_args()

    display, tests = display_connection(args.virtual, args.rotate, args.mirror)

    # Run any standalone tests here when script is run directly
    for test in tests:
        test(display)
