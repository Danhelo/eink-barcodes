"""
Display management interface and implementations.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Tuple, Optional, Dict, Any
import logging
from PIL import Image

from .state_manager import StateManager, DisplayState
from IT8951.display import AutoEPDDisplay, VirtualEPDDisplay

logger = logging.getLogger(__name__)

@dataclass
class DisplayConfig:
    """Display configuration parameters"""
    virtual: bool = False
    mirror: bool = False
    vcom: float = -2.02
    spi_hz: int = 24000000
    dimensions: Tuple[int, int] = (800, 600)

class DisplayManager(ABC):
    """Abstract display management interface"""
    def __init__(self, config: DisplayConfig, state_manager: StateManager):
        self.config = config
        self.state_manager = state_manager
        self._display = None

    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize display hardware"""
        pass

    @abstractmethod
    async def display_image(self, image_path: str, transform_params: Dict[str, Any]) -> bool:
        """Display image with transformations"""
        pass

    @abstractmethod
    async def clear(self) -> bool:
        """Clear display"""
        pass

    @abstractmethod
    async def cleanup(self) -> None:
        """Cleanup resources"""
        pass

    @property
    def is_ready(self) -> bool:
        """Check if display is ready"""
        return self._display is not None

class EPDDisplayManager(DisplayManager):
    """E-ink display manager implementation"""
    async def initialize(self) -> bool:
        """Initialize EPD display"""
        try:
            self.state_manager.update_display_state(DisplayState.INITIALIZING)

            if self.config.virtual:
                self._display = VirtualEPDDisplay(
                    dims=self.config.dimensions,
                    mirror=self.config.mirror
                )
            else:
                self._display = AutoEPDDisplay(
                    vcom=self.config.vcom,
                    mirror=self.config.mirror,
                    spi_hz=self.config.spi_hz
                )
                logger.info(f"VCOM set to {self._display.epd.get_vcom()}")

            self.state_manager.update_display_state(DisplayState.READY)
            return True

        except Exception as e:
            logger.error(f"Display initialization failed: {e}")
            self.state_manager.update_display_state(DisplayState.ERROR)
            return False

    async def display_image(self, image_path: str, transform_params: Dict[str, Any]) -> bool:
        """Display image with transformations"""
        if not self.is_ready:
            logger.error("Display not initialized")
            return False

        try:
            self.state_manager.update_display_state(DisplayState.BUSY)

            # Load and transform image
            image = Image.open(image_path)

            # Apply transformations
            if transform_params.get("mirror", False):
                image = image.transpose(Image.FLIP_LEFT_RIGHT)

            # TODO: Add more transformations

            # Display image
            self._display.display_image_8bpp(image)

            self.state_manager.update_display_state(DisplayState.READY)
            return True

        except Exception as e:
            logger.error(f"Failed to display image: {e}")
            self.state_manager.update_display_state(DisplayState.ERROR)
            return False

    async def clear(self) -> bool:
        """Clear display"""
        if not self.is_ready:
            logger.error("Display not initialized")
            return False

        try:
            self.state_manager.update_display_state(DisplayState.BUSY)
            self._display.clear()
            self.state_manager.update_display_state(DisplayState.READY)
            return True

        except Exception as e:
            logger.error(f"Failed to clear display: {e}")
            self.state_manager.update_display_state(DisplayState.ERROR)
            return False

    async def cleanup(self) -> None:
        """Cleanup display resources"""
        try:
            if self.is_ready:
                await self.clear()
                self._display = None
            self.state_manager.update_display_state(DisplayState.DISCONNECTED)

        except Exception as e:
            logger.error(f"Error during display cleanup: {e}")
            self.state_manager.update_display_state(DisplayState.ERROR)
