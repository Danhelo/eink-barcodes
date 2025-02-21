from PIL import Image
import logging

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

    def clear(self):
        """Clear the virtual display."""
        self.current_image = None

class DisplayManager:
    """Manages display initialization and provides fallback to virtual display."""

    @staticmethod
    def get_display(virtual=False):
        """Get appropriate display instance.

        Args:
            virtual (bool): Force virtual display mode

        Returns:
            Display instance (either IT8951 or Virtual)
        """
        if virtual:
            return VirtualDisplay()

        try:
            from IT8951.display import AutoEPDDisplay
            display = AutoEPDDisplay(vcom=-2.06)
            logger.info("Initialized IT8951 display")
            return display
        except (ImportError, ModuleNotFoundError) as e:
            logger.warning("IT8951 module not available, falling back to virtual display: %s", e)
            return VirtualDisplay()
        except Exception as e:
            logger.error("Failed to initialize IT8951 display: %s", e)
            return VirtualDisplay()
