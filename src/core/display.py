# src/core/display.py
"""
Display interface with virtual and hardware implementations.
"""
import logging
from abc import ABC, abstractmethod
from PIL import Image
from typing import Optional, Tuple, Dict, Any

logger = logging.getLogger(__name__)

class Display(ABC):
    """Abstract display interface."""
    
    @abstractmethod
    def initialize(self) -> bool:
        """Initialize the display."""
        pass
        
    @abstractmethod
    def display_image(self, image: Image.Image) -> bool:
        """Display an image."""
        pass
        
    @abstractmethod
    def clear(self) -> bool:
        """Clear the display."""
        pass
        
    @abstractmethod
    def cleanup(self) -> bool:
        """Clean up resources."""
        pass
        
    @property
    @abstractmethod
    def dimensions(self) -> Tuple[int, int]:
        """Get display dimensions (width, height)."""
        pass

class VirtualDisplay(Display):
    """Virtual display implementation for development and testing."""
    
    def __init__(self, width: int = 800, height: int = 600):
        self._width = width
        self._height = height
        self._current_image = None
        self._initialized = False
        
    def initialize(self) -> bool:
        logger.info(f"Initialized virtual display {self._width}x{self._height}")
        self._initialized = True
        return True
        
    def display_image(self, image: Image.Image) -> bool:
        if not self._initialized:
            logger.error("Display not initialized")
            return False
            
        self._current_image = image.copy()
        logger.info(f"Virtual display updated with image {image.width}x{image.height}")
        return True
        
    def clear(self) -> bool:
        if not self._initialized:
            return False
            
        self._current_image = None
        logger.info("Virtual display cleared")
        return True
        
    def cleanup(self) -> bool:
        self._current_image = None
        self._initialized = False
        return True
        
    @property
    def dimensions(self) -> Tuple[int, int]:
        return (self._width, self._height)
        
    @property
    def current_image(self) -> Optional[Image.Image]:
        """Get the currently displayed image."""
        return self._current_image

class HardwareDisplay(Display):
    """Hardware display implementation using IT8951 library."""
    
    def __init__(self, config: Dict[str, Any]):
        self._config = config
        self._vcom = config.get('vcom', -2.06)
        self._display = None
        self._width = 0
        self._height = 0
        self._initialized = False
        
    def initialize(self) -> bool:
        try:
            from IT8951.display import AutoEPDDisplay
            
            # Get configuration parameters
            spi_hz = self._config.get('spi_hz', 24000000)
            mirror = self._config.get('mirror', False)
            
            # Initialize the display
            self._display = AutoEPDDisplay(vcom=self._vcom, spi_hz=spi_hz, mirror=mirror)
            self._width = self._display.width
            self._height = self._display.height
            self._initialized = True
            
            logger.info(f"Hardware display initialized: {self._width}x{self._height}")
            return True
            
        except ImportError:
            logger.error("IT8951 library not available")
            return False
            
        except Exception as e:
            logger.error(f"Failed to initialize hardware display: {e}")
            return False
            
    def display_image(self, image: Image.Image) -> bool:
        if not self._initialized or not self._display:
            logger.error("Display not initialized")
            return False
            
        try:
            # Prepare the image (resize if needed)
            if image.width > self._width or image.height > self._height:
                # Maintain aspect ratio
                ratio = min(self._width / image.width, self._height / image.height)
                new_width = int(image.width * ratio)
                new_height = int(image.height * ratio)
                image = image.resize((new_width, new_height), Image.BICUBIC)
                
            # Center the image
            x = (self._width - image.width) // 2
            y = (self._height - image.height) // 2
            
            # Clear the frame buffer
            self._display.frame_buf.paste(0xFF, box=(0, 0, self._width, self._height))
            
            # Paste the image
            self._display.frame_buf.paste(image, (x, y))
            
            # Display with appropriate mode
            from IT8951 import constants
            display_mode = self._config.get('display_mode', constants.DisplayModes.GC16)
            self._display.draw_full(display_mode)
            
            return True
            
        except Exception as e:
            logger.error(f"Error displaying image: {e}")
            return False
            
    def clear(self) -> bool:
        if not self._initialized or not self._display:
            return False
            
        try:
            self._display.clear()
            return True
        except Exception as e:
            logger.error(f"Error clearing display: {e}")
            return False
            
    def cleanup(self) -> bool:
        if not self._initialized:
            return True
            
        try:
            if self._display:
                self.clear()
            self._initialized = False
            return True
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
            return False
            
    @property
    def dimensions(self) -> Tuple[int, int]:
        return (self._width, self._height)

def create_display(config: Dict[str, Any]) -> Display:
    """Factory function to create appropriate display instance."""
    virtual = config.get('virtual', False)
    
    if virtual:
        # Create virtual display with configured dimensions
        dimensions = config.get('dimensions', (800, 600))
        return VirtualDisplay(dimensions[0], dimensions[1])
        
    # Try hardware display
    hardware = HardwareDisplay(config)
    if hardware.initialize():
        return hardware
        
    # Fall back to virtual if hardware initialization fails
    logger.warning("Hardware display initialization failed, falling back to virtual")
    dimensions = config.get('dimensions', (800, 600))
    return VirtualDisplay(dimensions[0], dimensions[1])