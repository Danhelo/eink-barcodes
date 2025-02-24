from abc import ABC, abstractmethod
import logging
from typing import Optional, Tuple
import numpy as np
from PIL import Image
from IT8951.display import AutoEPDDisplay
from .state_manager import StateManager, DisplayState

logger = logging.getLogger(__name__)

class DisplayConfig:
    """Display configuration settings"""
    def __init__(self, vcom: float = -2.06):
        self.vcom = vcom
        self.rotation = 0
        self.scale = 1.0

class BaseDisplayManager(ABC):
    """Abstract base class for display management"""

    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize the display"""
        pass

    @abstractmethod
    async def cleanup(self):
        """Clean up display resources"""
        pass

    @abstractmethod
    async def display_image(self, image: Image.Image) -> bool:
        """Display an image"""
        pass

    @abstractmethod
    async def clear(self) -> bool:
        """Clear the display"""
        pass

class EPDDisplayManager(BaseDisplayManager):
    """Concrete implementation for IT8951 E-Paper display"""

    def __init__(self, state_manager: StateManager, config: Optional[DisplayConfig] = None):
        self.state_manager = state_manager
        self.config = config or DisplayConfig()
        self.display: Optional[AutoEPDDisplay] = None
        self.dimensions: Optional[Tuple[int, int]] = None
        logger.info("EPD Display Manager initialized with VCOM %.2f", self.config.vcom)

    async def initialize(self) -> bool:
        """Initialize the IT8951 display"""
        try:
            self.state_manager.update_display_state(DisplayState.INITIALIZING)
            self.display = AutoEPDDisplay(vcom=self.config.vcom)
            self.dimensions = (self.display.width, self.display.height)
            self.state_manager.update_display_state(DisplayState.READY)
            logger.info("Display initialized successfully: %dx%d", *self.dimensions)
            return True
        except Exception as e:
            self.state_manager.update_display_state(DisplayState.ERROR)
            logger.error("Failed to initialize display: %s", str(e))
            return False

    async def cleanup(self):
        """Clean up display resources"""
        try:
            if self.display:
                # Add any necessary cleanup for IT8951
                self.display = None
            self.state_manager.update_display_state(DisplayState.DISCONNECTED)
            logger.info("Display cleaned up successfully")
        except Exception as e:
            logger.error("Error during display cleanup: %s", str(e))

    async def display_image(self, image: Image.Image) -> bool:
        """Display an image on the EPD"""
        if not self.display or self.state_manager.get_display_state() != DisplayState.READY:
            logger.error("Display not ready")
            return False

        try:
            self.state_manager.update_display_state(DisplayState.BUSY)

            # Apply transformations
            if self.config.rotation:
                image = image.rotate(self.config.rotation, expand=True)
            if self.config.scale != 1.0:
                new_size = tuple(int(dim * self.config.scale) for dim in image.size)
                image = image.resize(new_size, Image.Resampling.LANCZOS)

            # Convert to grayscale if needed
            if image.mode != 'L':
                image = image.convert('L')

            # Center the image
            display_width, display_height = self.dimensions
            image_width, image_height = image.size
            x = (display_width - image_width) // 2
            y = (display_height - image_height) // 2

            # Display the image
            self.display.display_image(image, xy=(x, y))
            self.state_manager.update_display_state(DisplayState.READY)
            return True

        except Exception as e:
            self.state_manager.update_display_state(DisplayState.ERROR)
            logger.error("Error displaying image: %s", str(e))
            return False

    async def clear(self) -> bool:
        """Clear the display"""
        if not self.display or self.state_manager.get_display_state() != DisplayState.READY:
            logger.error("Display not ready")
            return False

        try:
            self.state_manager.update_display_state(DisplayState.BUSY)
            self.display.clear()
            self.state_manager.update_display_state(DisplayState.READY)
            return True
        except Exception as e:
            self.state_manager.update_display_state(DisplayState.ERROR)
            logger.error("Error clearing display: %s", str(e))
            return False

# Factory function to create the appropriate display manager
def create_display_manager(state_manager: StateManager, config: Optional[DisplayConfig] = None) -> BaseDisplayManager:
    """Create appropriate display manager based on environment"""
    try:
        # Try to create EPD display manager
        return EPDDisplayManager(state_manager, config)
    except Exception as e:
        logger.error("Failed to create EPD display manager: %s", str(e))
        raise
