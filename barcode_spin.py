#!/usr/bin/env python3
"""
Fun demo that shows a spinning barcode animation on the e-ink display.
Uses the fastest possible refresh rate and optimized display modes.
"""

import os
import time
from PIL import Image
from IT8951.display import AutoEPDDisplay
from IT8951 import constants
from IT8951.img_transform import prepare_image_for_display

def init_display():
    """Initialize the e-ink display with optimal settings for animation"""
    print('Initializing display...')
    display = AutoEPDDisplay(vcom=-2.02, spi_hz=24000000)  # Max SPI speed
    print('VCOM set to', display.epd.get_vcom())
    return display

def load_barcode(directory="code128"):
    """Load the first barcode found in the specified directory"""
    # Get the first barcode image from the directory
    for file in os.listdir(directory):
        if file.lower().endswith(('.png', '.jpg', '.jpeg')):
            return Image.open(os.path.join(directory, file))
    raise FileNotFoundError(f"No barcode images found in {directory}")

def calculate_center_position(display_width, display_height, image_width, image_height):
    """Calculate position to center the image"""
    x = (display_width - image_width) // 2
    y = (display_height - image_height) // 2
    return x, y

def optimize_barcode_size(image, display, scale_factor=0.3):
    """Resize barcode to optimal size for animation"""
    # Calculate dimensions that maintain aspect ratio
    aspect_ratio = image.width / image.height

    # Use a portion of the display height for better animation
    target_height = int(display.height * scale_factor)
    target_width = int(target_height * aspect_ratio)

    # Resize the image
    return image.resize((target_width, target_height), Image.BICUBIC)

def run_animation(display, image, total_frames=360, frame_delay=0.1):
    """Run the spinning animation"""
    print("\nStarting barcode spin animation!")
    print("Press Ctrl+C to stop\n")

    try:
        frame = 0
        while True:
            # Calculate rotation angle (0-360 degrees)
            angle = frame % total_frames

            # Clear display buffer
            display.frame_buf.paste(0xFF, box=(0, 0, display.width, display.height))

            # Rotate image
            rotated_img = prepare_image_for_display(
                image,
                angle=angle,
                background=0xFF
            )

            # Center the rotated image
            x, y = calculate_center_position(
                display.width, display.height,
                rotated_img.width, rotated_img.height
            )

            # Display the frame
            display.frame_buf.paste(rotated_img, (x, y))

            # Use the fastest refresh mode for animation
            display.draw_full(constants.DisplayModes.DU)

            # Small delay between frames
            time.sleep(frame_delay)

            # Update frame counter
            frame = (frame + 5) % total_frames  # Increment by 5 degrees each frame

            # Print progress indicator
            if frame % 45 == 0:  # Show progress every 45 degrees
                print(f"Rotation: {angle % 360}°")

    except KeyboardInterrupt:
        print("\nAnimation stopped by user")
    finally:
        # Clear display when done
        display.clear()

def main():
    # Initialize display
    display = init_display()

    try:
        # Load and prepare barcode image
        original_image = load_barcode()

        # Optimize barcode size for animation
        barcode = optimize_barcode_size(original_image, display)

        # Clear display before starting
        display.clear()

        # Run the animation
        run_animation(
            display,
            barcode,
            total_frames=360,    # Full 360-degree rotation
            frame_delay=0.1      # Adjust this to control speed
        )

    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("Please ensure there are barcode images in the code128 directory")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
