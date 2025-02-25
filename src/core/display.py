from PIL import Image
import logging
from typing import Optional, Union, Tuple
import os

logger = logging.getLogger(__name__)

class VirtualDisplay:
    """Virtual display for development/testing without physical hardware."""

    def __init__(self, width=800, height=600):
        self.width = width
        self.height = height
        self.current_image = None
        logger.info("Initialized virtual display %dx%d", width, height)

    def prepare_display(self, **kwargs):
        """Simulate display preparation."""
        pass

    def display_image(self, image):
        """Store the image that would be displayed."""
        self.current_image = image
        logger.info("Virtual display updated with image %dx%d",
                   image.width, image.height)
        return True

    def clear(self):
        """Clear the virtual display."""
        self.current_image = None
        logger.info("Virtual display cleared")
        return True

class AutoEPDDisplayWrapper:
    """Wrapper for IT8951.display.AutoEPDDisplay to provide consistent interface."""

    def __init__(self, epd_display):
        """Initialize with an AutoEPDDisplay instance."""
        self.display = epd_display
        self.width = self.display.width
        self.height = self.display.height

    def prepare_display(self, **kwargs):
        """Prepare the display for use."""
        # Nothing needed here as initialization is done in constructor
        pass

    def display_image(self, image: Image.Image) -> bool:
        """Display an image on the e-ink display.

        Args:
            image: PIL Image to display

        Returns:
            bool: True if successful
        """
        try:
            # Resize image if needed
            if image.width > self.width or image.height > self.height:
                # Maintain aspect ratio
                aspect_ratio = image.width / image.height
                if image.width > image.height:
                    new_width = self.width
                    new_height = int(new_width / aspect_ratio)
                else:
                    new_height = self.height
                    new_width = int(new_height * aspect_ratio)

                image = image.resize((new_width, new_height), Image.BICUBIC)
                logger.info(f"Resized image to {new_width}x{new_height}")

            # Calculate position to center the image
            x = (self.width - image.width) // 2
            y = (self.height - image.height) // 2

            # Clear the frame buffer
            self.display.frame_buf.paste(0xFF, box=(0, 0, self.width, self.height))

            # Paste the image onto the frame buffer
            self.display.frame_buf.paste(image, (x, y))

            # Use the appropriate display mode for best quality
            from IT8951 import constants
            self.display.draw_full(constants.DisplayModes.GC16)

            logger.info(f"Displayed image at position ({x}, {y})")
            return True

        except Exception as e:
            logger.error(f"Error displaying image: {e}")
            return False

    def clear(self) -> bool:
        """Clear the display.

        Returns:
            bool: True if successful
        """
        try:
            self.display.clear()
            logger.info("Display cleared")
            return True
        except Exception as e:
            logger.error(f"Error clearing display: {e}")
            return False

class DisplayManager:
    """Manages display initialization and provides fallback to virtual display."""

    @staticmethod
    def get_display(virtual=False, vcom=-2.06):
        """Get appropriate display instance.

        Args:
            virtual (bool): Force virtual display mode
            vcom (float): VCOM value for e-ink display

        Returns:
            Display instance (either IT8951 or Virtual)
        """
        if virtual:
            logger.info("Using virtual display as requested")
            return VirtualDisplay()

        try:
            from IT8951.display import AutoEPDDisplay
            display = AutoEPDDisplay(vcom=vcom)
            logger.info(f"EPD Display Manager initialized with VCOM {vcom}")

            # Initialize the display
            display.clear()
            logger.info(f"Display initialized successfully: {display.width}x{display.height}")

            # Wrap the display to provide consistent interface
            return AutoEPDDisplayWrapper(display)

        except (ImportError, ModuleNotFoundError) as e:
            logger.warning("IT8951 module not available, falling back to virtual display: %s", e)
            return VirtualDisplay()
        except Exception as e:
            logger.error("Failed to initialize IT8951 display: %s", e)
            return VirtualDisplay()
