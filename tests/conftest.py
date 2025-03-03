# File: tests/conftest.py
import pytest
import asyncio
from PIL import Image
import os
import sys

# Add src to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.controller import TestController
from src.core.config import TestConfig
from src.core.display import VirtualDisplay
from src.core.image_transform import create_transform_pipeline

@pytest.fixture
def virtual_display():
    """Fixture providing a virtual display."""
    display = VirtualDisplay(800, 600)
    display.initialize()
    return display

@pytest.fixture
def transform_pipeline():
    """Fixture providing a transformation pipeline."""
    return create_transform_pipeline()

@pytest.fixture
def test_controller():
    """Fixture providing a test controller."""
    controller = TestController()
    return controller

@pytest.fixture
def test_config():
    """Fixture providing a test configuration."""
    return TestConfig(
        barcode_type="Code128",
        image_paths=[os.path.join("examples", "code128_sample.png")],
        delay_between_images=0.1,
        transformations={
            'rotation': {'angle': 0},
            'scale': {'factor': 1.0}
        }
    )

@pytest.fixture
def test_image():
    """Fixture providing a test image."""
    # Create a simple test image
    img = Image.new('L', (100, 100), 255)  # White background
    # Draw some black bars
    for i in range(0, 100, 20):
        for j in range(0, i, 2):
            img.putpixel((j, i), 0)  # Black pixels
    
    # Save to examples directory if it doesn't exist
    os.makedirs('examples', exist_ok=True)
    img_path = os.path.join('examples', 'code128_sample.png')
    if not os.path.exists(img_path):
        img.save(img_path)
    
    return img