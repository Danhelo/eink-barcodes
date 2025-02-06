# functions defined in this file
__all__ = [
    'print_system_info',
    'clear_display',
    'display_gradient',
    'display_image_8bpp',
    'partial_update'
]
#import cv2
import PIL
import PIL.Image    
if not hasattr(PIL.Image, 'Transpose'):  
    PIL.Image.Transpose = PIL.Image   
import csv
import json
import os
from os import listdir
from PIL import Image, ImageDraw, ImageFont
from IT8951 import constants
import time
from time import sleep
import datetime
from sys import path
import subprocess
import asyncio
import websockets

def print_system_info(display):
    epd = display.epd

    print('System info:')
    print('  display size: {}x{}'.format(epd.width, epd.height))
    print('  img buffer address: {:X}'.format(epd.img_buf_address))
    print('  firmware version: {}'.format(epd.firmware_version))
    print('  LUT version: {}'.format(epd.lut_version))
    print()

def clear_display(display):
    print('Clearing display...')
    display.clear()

def display_gradient(display):
    print('Displaying gradient...')

    # set frame buffer to gradient
    for i in range(16):
        color = i*0x10
        box = (
            i*display.width//16,      # xmin
            0,                        # ymin
            (i+1)*display.width//16,  # xmax
            display.height            # ymax
        )

        display.frame_buf.paste(color, box=box)

    # update display
    display.draw_full(constants.DisplayModes.GC16)

    # then add some black and white bars on top of it, to test updating with DU on top of GC16
    box = (0, display.height//5, display.width, 2*display.height//5)
    display.frame_buf.paste(0x00, box=box)

    box = (0, 3*display.height//5, display.width, 4*display.height//5)
    display.frame_buf.paste(0xF0, box=box)

    display.draw_partial(constants.DisplayModes.DU)

def partial_update(display):
    print('Starting partial update...')

    # clear image to white
    display.frame_buf.paste(0xFF, box=(0, 0, display.width, display.height))

    print('  writing full...')
    _place_text(display.frame_buf, 'partial', x_offset=-display.width//4)
    display.draw_full(constants.DisplayModes.GC16)

    # TODO: should use 1bpp for partial text update
    print('  writing partial...')
    _place_text(display.frame_buf, 'update', x_offset=+display.width//4)
    display.draw_partial(constants.DisplayModes.DU)

def get_latest_extracted_dir(base_path='testing-barcode'):
    full_base_path = os.path.join('/greengrass/v2/work/e-ink', base_path)
    
    # List all directories in the base path
    directories = [d for d in os.listdir(full_base_path) if os.path.isdir(os.path.join(full_base_path, d))]
    
    if not directories:
        return None
    
    # Sort directories based on their names (which include timestamps)
    sorted_dirs = sorted(directories, reverse=True)
    
    # Return the full path of the latest directory
    return os.path.join(full_base_path, sorted_dirs[0])

async def test(msg):
    uri = "ws://192.168.1.1:5432"
    async with websockets.connect(uri) as websocket:
        await websocket.send(msg)
        response = await websocket.recv()
        print(response)

def calculate_resize_dimensions(image, max_width, max_height):
            """
            Calculate new dimensions that maintain aspect ratio and fit within max bounds.
            Returns (new_width, new_height)
            """
            # Get current aspect ratio
            aspect_ratio = image.width / image.height
            
            # Try scaling by width first
            new_width = max_width
            new_height = int(new_width / aspect_ratio)
            
            # If too tall, scale by height instead
            if new_height > max_height:
                new_height = max_height
                new_width = int(new_height * aspect_ratio)
            
            return new_width, new_height
    
async def display_image_8bpp(websocket,display,msg):
    print("_________________________________________")

    display_barcode = True


    # Determine the folder directory based on test type and barcode type
    if msg['pre-test'] == 'yes':
        # Set directory for pre-test
        folder_dir = path[0] + "/pre_test/"
        print("Pre-test directory selected", folder_dir)

    elif msg['known_barcode'] == 'yes':
        # Set directory for known_barcode
        folder_dir = path[0] + "/known_barcode/"
        print("Known barcode directory selected", folder_dir)

    else:
        # If not a pre-test or known barcode, use the barcode type
        barcode_type = msg.get('barcode-type', 'unknown')
        folder_dir = path[0] + '/' + barcode_type + '/'
        print(f"Regular test directory selected for barcode type: {barcode_type}", folder_dir)

    for image in os.listdir(folder_dir):
        display.frame_buf.paste(0xFF, box=(0, 0, display.width, display.height))
        # image adjusment
        img = Image.open(folder_dir + image)
        
        # Calculate dimensions that maintain aspect ratio and fit display
        new_width, new_height = calculate_resize_dimensions(img, display.width//2, display.height)
        # Resize maintaining aspect ratio
        img = img.resize((new_width, new_height))

        # centering image
        x = (display.width - img.width) // 2
        y = (display.height - img.height) // 2

        if not display_barcode:
            continue

        # display image
        display.frame_buf.paste(img, (x, y))
        display.draw_full(constants.DisplayModes.GC16)

        # send barcode back to carbon
        input_barcode = image.split('_')[1][:-4]
        print('Displaying "{}"...'.format(image))
        display_barcode = False

        if msg['socket-type'] == 'ws':
            data = await websocket.recv()
            data = data.decode("utf-8")
            print("From test function:", data)
            display_barcode = True

            if data == "Decoding Finished":
                message = bytes(f"{input_barcode}", 'utf-8')
                await websocket.send(message)
                
        else:
            display_barcode = True

    await websocket.send(bytes('done','utf-8'))
    

