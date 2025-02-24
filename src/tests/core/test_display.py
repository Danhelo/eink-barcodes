import pytest
from PIL import Image
from src.core.display import VirtualDisplay, DisplayManager

@pytest.fixture
def virtual_display():
    return VirtualDisplay(800, 600)

def test_virtual_display_init():
    display = VirtualDisplay(800, 600)
    assert display.width == 800
    assert display.height == 600
    assert display.current_image is None

def test_virtual_display_image():
    display = VirtualDisplay(800, 600)
    test_image = Image.new('L', (800, 600), 255)
    display.display_image(test_image)
    assert display.current_image == test_image

def test_virtual_display_clear():
    display = VirtualDisplay(800, 600)
    test_image = Image.new('L', (800, 600), 255)
    display.display_image(test_image)
    display.clear()
    assert display.current_image is None

def test_display_manager_virtual():
    display = DisplayManager.get_display(virtual=True)
    assert isinstance(display, VirtualDisplay)

def test_display_manager_hardware_fallback(mocker):
    # Mock IT8951 import failure
    mocker.patch('src.core.display.AutoEPDDisplay', side_effect=ImportError)
    display = DisplayManager.get_display(virtual=False)
    assert isinstance(display, VirtualDisplay)
