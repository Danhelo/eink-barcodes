# functions defined in this file
__all__ = [
    'print_system_info',
    'clear_display',
    'display_gradient',
    'display_image_8bpp',
    'partial_update'
]

import PIL
import PIL.Image    
if not hasattr(PIL.Image, 'Transpose'):  
    PIL.Image.Transpose = PIL.Image   
import csv
import json
import os
from os import listdir
from PIL import Image, ImageDraw, ImageFont
from IT8951.src.IT8951 import constants
from IT8951.src.IT8951.img_transform import prepare_image_for_display
import time
from time import sleep
import datetime
import sys
import subprocess
import asyncio
import websockets
import logging

logger = logging.getLogger(__name__)

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

    print('  writing partial...')
    _place_text(display.frame_buf, 'update', x_offset=+display.width//4)
    display.draw_partial(constants.DisplayModes.DU)

def calculate_resize_dimensions(image, max_width, max_height, scale=1.0):
    """Calculate new dimensions that maintain aspect ratio and fit within max bounds."""
    aspect_ratio = image.width / image.height
    scaled_max_width = int(max_width * scale)
    scaled_max_height = int(max_height * scale)

    # Try scaling by width first
    new_width = scaled_max_width
    new_height = int(new_width / aspect_ratio)

    # If too tall, scale by height instead
    if new_height > scaled_max_height:
        new_height = scaled_max_height
        new_width = int(new_height * aspect_ratio)

    logger.info(f"Scaling image: original size={image.width}x{image.height}, "
          f"new size={new_width}x{new_height} (scale={scale:.2f})")

    return new_width, new_height

async def display_image_8bpp(websocket, display, msg, project_root=None):
    """Display barcode images on the e-ink display."""
    logger.info("Starting barcode display test")

    # Use provided project_root or fall back to current directory
    if project_root is None:
        project_root = os.getcwd()

    logger.info(f"Using project root: {project_root}")

    # Get transformation parameters
    transformations = msg.get('transformations', {})
    rotation = transformations.get('rotation', 0.0)
    scale = transformations.get('scale', 1.0)
    logger.info(f"Using rotation: {rotation:.1f}°, scale: {scale:.2f}")

    try:
        # Determine the folder directory based on test type and barcode type
        if msg['pre-test'] == 'yes':
            folder_dir = os.path.join(project_root, "pre_test")
            logger.info("Pre-test directory selected: %s", folder_dir)
        elif msg.get('known_barcode') == 'yes':
            folder_dir = os.path.join(project_root, "known_barcode")
            logger.info("Known barcode directory selected: %s", folder_dir)
        else:
            barcode_type = msg.get('barcode-type', 'unknown')
            folder_dir = os.path.join(project_root, barcode_type)
            logger.info("Regular test directory selected for barcode type: %s", folder_dir)

        # Verify the directory exists
        if not os.path.exists(folder_dir):
            error_msg = f"Error: Directory not found: {folder_dir}"
            logger.error(error_msg)
            await websocket.send(json.dumps({
                "status": "error",
                "message": error_msg
            }))
            return

        # List all image files in the directory
        image_files = [f for f in os.listdir(folder_dir)
                      if f.lower().endswith(('.png', '.jpg', '.jpeg'))]

        if not image_files:
            error_msg = f"No image files found in directory: {folder_dir}"
            logger.error(error_msg)
            await websocket.send(json.dumps({
                "status": "error",
                "message": error_msg
            }))
            return

        logger.info(f"Found {len(image_files)} image files")
        total_images = len(image_files)

        for idx, image in enumerate(image_files, 1):
            # Check for stop signal
            try:
                # Use select to check for messages without blocking
                response = await asyncio.wait_for(websocket.recv(), timeout=0.1)
                data = json.loads(response)
                if data.get("command") == "stop":
                    logger.info("Received stop command")
                    await websocket.send(json.dumps({
                        "status": "stopped",
                        "message": "Test stopped by user"
                    }))
                    return
            except (asyncio.TimeoutError, websockets.exceptions.ConnectionClosed):
                # No message received, continue with test
                pass
            except Exception as e:
                logger.error(f"Error checking for stop signal: {e}")

            # Clear display
            display.frame_buf.paste(0xFF, box=(0, 0, display.width, display.height))

            # Load and process image
            img_path = os.path.join(folder_dir, image)
            try:
                img = Image.open(img_path)
            except Exception as e:
                logger.error(f"Error opening image {img_path}: {str(e)}")
                continue

            # Calculate dimensions that maintain aspect ratio and fit display
            new_width, new_height = calculate_resize_dimensions(
                img,
                display.width//2,
                display.height,
                scale=scale
            )

            # Resize maintaining aspect ratio
            img = img.resize((new_width, new_height))

            # Apply transformations (rotation and any other processing)
            transformed_img = prepare_image_for_display(
                img,
                angle=rotation,
                scale=1.0,  # Scale already applied
                background=0xFF  # White background for e-ink
            )

            # Center image
            x = (display.width - transformed_img.width) // 2
            y = (display.height - transformed_img.height) // 2

            # Display image
            display.frame_buf.paste(transformed_img, (x, y))
            display.draw_full(constants.DisplayModes.GC16)

            # Send progress update
            progress = int((idx / total_images) * 100)
            await websocket.send(json.dumps({
                "status": "progress",
                "progress": progress,
                "current": idx,
                "total": total_images
            }))

            # Get barcode value from filename
            input_barcode = image.split('_')[1][:-4]
            logger.info('Displaying "%s"...', image)

            if msg['socket-type'] == 'ws':
                try:
                    # Send barcode value immediately
                    await websocket.send(json.dumps({
                        "status": "barcode",
                        "value": input_barcode
                    }))

                    # Wait a short time before next image
                    await asyncio.sleep(2)

                except Exception as e:
                    logger.error(f"Error handling WebSocket message: {e}")
                    continue

        # Send completion message
        await websocket.send(json.dumps({
            "status": "complete",
            "message": "Test sequence completed successfully"
        }))

    except Exception as e:
        error_msg = f"Error during test: {str(e)}"
        logger.error(error_msg)
        await websocket.send(json.dumps({
            "status": "error",
            "message": error_msg
        }))
