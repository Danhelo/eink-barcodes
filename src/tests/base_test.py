import pytest
import asyncio
from pathlib import Path
import shutil
from PyQt5.QtWidgets import QApplication
from src.core.display_manager import DisplayManager
from src.core.state_manager import StateManager
from src.core.test_controller import TestController

class BaseTestCase:
    """Base class for all test cases."""

    @pytest.fixture(autouse=True)
    def setup_test(self, qapp):
        """Set up test environment with QApplication instance."""
        self.app = qapp
        yield
        self.app.processEvents()

    @pytest.fixture
    async def display_manager(self):
        """Create a virtual display manager for testing."""
        manager = DisplayManager(virtual=True)
        await manager.initialize()
        yield manager
        await manager.cleanup()

    @pytest.fixture
    def state_manager(self):
        """Create a state manager instance."""
        return StateManager()

    @pytest.fixture
    def test_controller(self, state_manager, display_manager):
        """Create a test controller instance."""
        return TestController(state_manager, display_manager)

    @pytest.fixture
    def test_resources(self):
        """Set up and clean up test resources directory."""
        resource_dir = Path("test_resources")
        resource_dir.mkdir(exist_ok=True)
        yield resource_dir
        if resource_dir.exists():
            shutil.rmtree(resource_dir)

    @staticmethod
    async def process_events(qtbot, timeout=100):
        """Process Qt events with timeout."""
        qtbot.wait(timeout)

    @staticmethod
    def create_test_image(size=(100, 100), color=255):
        """Create a test image with specified size and color."""
        from PIL import Image
        return Image.new('L', size, color)

    @staticmethod
    def compare_images(img1, img2, tolerance=0):
        """Compare two images with optional tolerance."""
        import numpy as np
        if img1.size != img2.size:
            return False
        arr1 = np.array(img1)
        arr2 = np.array(img2)
        return np.all(np.abs(arr1 - arr2) <= tolerance)

    @staticmethod
    def get_test_file_path(filename):
        """Get path to a test file in the test resources directory."""
        return Path("test_resources") / filename

class BaseUITestCase(BaseTestCase):
    """Base class for UI-specific test cases."""

    @pytest.fixture(autouse=True)
    def setup_ui_test(self, qtbot):
        """Set up UI test environment with qtbot."""
        self.qtbot = qtbot
        yield

    async def click_button(self, button, timeout=100):
        """Click a button and wait for events to process."""
        from PyQt5.QtCore import Qt
        self.qtbot.mouseClick(button, Qt.LeftButton)
        await self.process_events(self.qtbot, timeout)

    async def enter_text(self, widget, text, timeout=100):
        """Enter text into a widget and wait for events to process."""
        widget.setText(text)
        await self.process_events(self.qtbot, timeout)

    def verify_widget_state(self, widget, property_name, expected_value):
        """Verify a widget's property value."""
        actual_value = getattr(widget, property_name)
        assert actual_value == expected_value, \
            f"Widget {widget.__class__.__name__} {property_name} mismatch. " \
            f"Expected {expected_value}, got {actual_value}"

class BaseIntegrationTestCase(BaseTestCase):
    """Base class for integration test cases."""

    @pytest.fixture(autouse=True)
    async def setup_integration_test(self, display_manager, state_manager):
        """Set up integration test environment."""
        self.display_manager = display_manager
        self.state_manager = state_manager
        yield
        await self.cleanup_integration_test()

    async def cleanup_integration_test(self):
        """Clean up integration test resources."""
        if hasattr(self, 'display_manager'):
            await self.display_manager.cleanup()

    async def verify_display_state(self, expected_image=None, timeout=1000):
        """Verify the display state matches expectations."""
        await self.process_events(self.qtbot, timeout)
        if expected_image:
            current_image = self.display_manager.get_current_image()
            assert self.compare_images(current_image, expected_image), \
                "Display image does not match expected image"
