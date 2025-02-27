# File: tests/test_display.py
import pytest
from PIL import Image
import asyncio

from src.core.display import VirtualDisplay, create_display

def test_virtual_display_init():
    """Test virtual display initialization."""
    display = VirtualDisplay(800, 600)
    assert display.initialize() is True
    assert display.dimensions == (800, 600)

def test_virtual_display_image(test_image):
    """Test displaying an image on virtual display."""
    display = VirtualDisplay(800, 600)
    display.initialize()
    
    # Display test image
    result = display.display_image(test_image)
    assert result is True
    
    # Verify image was stored
    assert display.current_image is not None
    assert display.current_image.size == test_image.size

def test_virtual_display_clear(test_image):
    """Test clearing the virtual display."""
    display = VirtualDisplay(800, 600)
    display.initialize()
    
    # Display then clear
    display.display_image(test_image)
    result = display.clear()
    
    assert result is True
    assert display.current_image is None

def test_create_display():
    """Test display factory function."""
    # Test virtual display creation
    config = {'virtual': True, 'dimensions': (1024, 768)}
    display = create_display(config)
    
    assert display.dimensions == (1024, 768)
    assert isinstance(display, VirtualDisplay)