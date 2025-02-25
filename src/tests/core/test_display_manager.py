"""
Unit tests for display manager functionality.
"""
import unittest
from unittest.mock import Mock, patch, AsyncMock
import asyncio
import numpy as np
from PIL import Image
from pathlib import Path
import tempfile
import os
import time

from src.core.display_manager import DisplayManager, DisplayConfig
from src.core.state_manager import StateManager, DisplayState
from src.core.display import VirtualDisplay, AutoEPDDisplayWrapper

class TestDisplayManager(unittest.TestCase):
    """Test suite for DisplayManager class."""

    def setUp(self):
        """Set up test environment."""
        self.test_images_dir = Path(tempfile.mkdtemp())
        self.create_test_images()
        self.state_manager = StateManager()
        self.display_config = DisplayConfig(
            virtual=True,
            vcom=-2.02,
            rotation=0,
            scale=1.0
        )

    def create_test_images(self):
        """Create test images for display testing."""
        # Create simple test pattern
        test_pattern = Image.new('L', (800, 600), 255)
        for i in range(0, 800, 100):
            for j in range(0, 600, 100):
                box = (i, j, i+50, j+50)
                test_pattern.paste(0, box)
        self.test_pattern_path = str(self.test_images_dir / 'test_pattern.png')
        test_pattern.save(self.test_pattern_path)

        # Create large test image
        large_pattern = Image.new('L', (2000, 1500), 255)
        self.large_image_path = str(self.test_images_dir / 'large_pattern.png')
        large_pattern.save(self.large_image_path)

    async def async_setup(self):
        """Async setup for tests requiring initialization."""
        self.display_manager = await DisplayManager.create(
            state_manager=self.state_manager,
            config=self.display_config
        )

    async def async_teardown(self):
        """Async teardown for cleanup."""
        if hasattr(self, 'display_manager'):
            await self.display_manager.cleanup()

    def test_initialization(self):
        """Test display manager initialization."""
        async def run_test():
            # Test successful initialization
            display_manager = await DisplayManager.create(
                state_manager=self.state_manager,
                config=self.display_config
            )
            self.assertTrue(display_manager.initialized)
            self.assertEqual(self.state_manager.get_display_state(), DisplayState.READY)

            # Test cleanup
            await display_manager.cleanup()
            self.assertFalse(display_manager.initialized)
            self.assertEqual(self.state_manager.get_display_state(), DisplayState.DISCONNECTED)

        asyncio.run(run_test())

    def test_display_image_basic(self):
        """Test basic image display functionality."""
        async def run_test():
            await self.async_setup()

            # Test basic image display
            result = await self.display_manager.display_image(self.test_pattern_path)
            self.assertTrue(result)

            # Verify display state
            self.assertEqual(self.state_manager.get_display_state(), DisplayState.READY)

            await self.async_teardown()

        asyncio.run(run_test())

    def test_error_handling(self):
        """Test error handling scenarios."""
        async def run_test():
            await self.async_setup()

            # Test invalid image path
            result = await self.display_manager.display_image('nonexistent.png')
            self.assertFalse(result)
            self.assertEqual(self.state_manager.get_display_state(), DisplayState.ERROR)

            # Reset state
            self.state_manager.update_display_state(DisplayState.READY)

            await self.async_teardown()

        asyncio.run(run_test())

    def test_clear_display(self):
        """Test clearing the display."""
        async def run_test():
            await self.async_setup()

            # First display an image
            await self.display_manager.display_image(self.test_pattern_path)

            # Then clear it
            result = await self.display_manager.clear()
            self.assertTrue(result)
            self.assertEqual(self.state_manager.get_display_state(), DisplayState.READY)

            await self.async_teardown()

        asyncio.run(run_test())

    def test_virtual_display_fallback(self):
        """Test virtual display fallback functionality."""
        async def run_test():
            # Mock hardware display failure
            with patch('src.core.display.AutoEPDDisplayWrapper', side_effect=Exception("Hardware error")):
                # Should fall back to virtual display
                display_manager = await DisplayManager.create(
                    state_manager=self.state_manager,
                    config=DisplayConfig(virtual=False)  # Try hardware but should fall back
                )

                self.assertTrue(display_manager.initialized)
                self.assertIsInstance(display_manager.display, VirtualDisplay)

                # Should still handle display operations
                result = await display_manager.display_image(self.test_pattern_path)
                self.assertTrue(result)

                await display_manager.cleanup()

        asyncio.run(run_test())

    def tearDown(self):
        """Clean up test environment."""
        # Remove test images
        for path in Path(self.test_images_dir).glob('*.png'):
            path.unlink()
        self.test_images_dir.rmdir()
