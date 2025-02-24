"""
Unit tests for display manager functionality.
"""
import unittest
from unittest.mock import Mock, patch
import asyncio
import numpy as np
from PIL import Image
from pathlib import Path
import tempfile
import psutil
import time

from src.core.display_manager import DisplayManager
from src.core.display import AutoEPDDisplay
from IT8951 import constants

class TestDisplayManager(unittest.TestCase):
    """Test suite for DisplayManager class."""

    def setUp(self):
        """Set up test environment."""
        self.test_images_dir = Path(tempfile.mkdtemp())
        self.create_test_images()
        self.start_memory = psutil.Process().memory_info().rss

    def create_test_images(self):
        """Create test images for display testing."""
        # Create simple test pattern
        test_pattern = Image.new('L', (800, 600), 255)
        for i in range(0, 800, 100):
            for j in range(0, 600, 100):
                box = (i, j, i+50, j+50)
                test_pattern.paste(0, box)
        self.test_pattern_path = self.test_images_dir / 'test_pattern.png'
        test_pattern.save(self.test_pattern_path)

        # Create large test image
        large_pattern = Image.new('L', (2000, 1500), 255)
        self.large_image_path = self.test_images_dir / 'large_pattern.png'
        large_pattern.save(self.large_image_path)

    async def async_setup(self):
        """Async setup for tests requiring initialization."""
        self.display_manager = DisplayManager()
        await self.display_manager.initialize()

    async def async_teardown(self):
        """Async teardown for cleanup."""
        if hasattr(self, 'display_manager'):
            await self.display_manager.cleanup()

    def test_initialization(self):
        """Test display manager initialization."""
        async def run_test():
            display_manager = DisplayManager()

            # Test successful initialization
            self.assertTrue(await display_manager.initialize())
            self.assertTrue(display_manager.is_ready)

            # Test double initialization
            self.assertTrue(await display_manager.initialize())

            await display_manager.cleanup()

        asyncio.run(run_test())

    def test_display_image_basic(self):
        """Test basic image display functionality."""
        async def run_test():
            await self.async_setup()

            # Test basic image display
            result = await self.display_manager.display_image(
                str(self.test_pattern_path),
                {'rotation': 0, 'scale': 1.0}
            )
            self.assertTrue(result)

            # Verify display state
            self.assertTrue(self.display_manager.is_ready)

            await self.async_teardown()

        asyncio.run(run_test())

    def test_display_image_transformations(self):
        """Test image display with various transformations."""
        async def run_test():
            await self.async_setup()

            # Test different rotations
            rotations = [0, 90, 180, 270]
            for rotation in rotations:
                with self.subTest(rotation=rotation):
                    result = await self.display_manager.display_image(
                        str(self.test_pattern_path),
                        {'rotation': rotation, 'scale': 1.0}
                    )
                    self.assertTrue(result)

            # Test different scales
            scales = [0.5, 1.0, 1.5, 2.0]
            for scale in scales:
                with self.subTest(scale=scale):
                    result = await self.display_manager.display_image(
                        str(self.test_pattern_path),
                        {'rotation': 0, 'scale': scale}
                    )
                    self.assertTrue(result)

            await self.async_teardown()

        asyncio.run(run_test())

    def test_display_modes(self):
        """Test different display update modes."""
        async def run_test():
            await self.async_setup()

            modes = [
                constants.DisplayModes.GC16,
                constants.DisplayModes.GL16,
                constants.DisplayModes.DU,
                constants.DisplayModes.A2
            ]

            for mode in modes:
                with self.subTest(mode=mode):
                    result = await self.display_manager.display_image(
                        str(self.test_pattern_path),
                        {'rotation': 0, 'scale': 1.0, 'mode': mode}
                    )
                    self.assertTrue(result)

            await self.async_teardown()

        asyncio.run(run_test())

    def test_error_handling(self):
        """Test error handling scenarios."""
        async def run_test():
            await self.async_setup()

            # Test invalid image path
            with self.assertRaises(FileNotFoundError):
                await self.display_manager.display_image(
                    'nonexistent.png',
                    {'rotation': 0, 'scale': 1.0}
                )

            # Test invalid rotation
            with self.assertRaises(ValueError):
                await self.display_manager.display_image(
                    str(self.test_pattern_path),
                    {'rotation': 45, 'scale': 1.0}
                )

            # Test invalid scale
            with self.assertRaises(ValueError):
                await self.display_manager.display_image(
                    str(self.test_pattern_path),
                    {'rotation': 0, 'scale': 0.0}
                )

            await self.async_teardown()

        asyncio.run(run_test())

    def test_concurrent_operations(self):
        """Test concurrent display operations."""
        async def run_test():
            await self.async_setup()

            # Create multiple concurrent display operations
            tasks = []
            for i in range(5):
                task = asyncio.create_task(
                    self.display_manager.display_image(
                        str(self.test_pattern_path),
                        {'rotation': 0, 'scale': 1.0}
                    )
                )
                tasks.append(task)

            # Wait for all tasks
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Verify results
            for result in results:
                self.assertIsInstance(result, bool)
                self.assertTrue(result)

            await self.async_teardown()

        asyncio.run(run_test())

    def test_resource_management(self):
        """Test resource management and cleanup."""
        async def run_test():
            await self.async_setup()

            # Test memory usage during operations
            for _ in range(10):
                await self.display_manager.display_image(
                    str(self.large_image_path),
                    {'rotation': 0, 'scale': 1.0}
                )

            # Check memory usage
            end_memory = psutil.Process().memory_info().rss
            memory_increase = end_memory - self.start_memory

            # Should not increase by more than 100MB
            self.assertLess(memory_increase, 100 * 1024 * 1024)

            # Test cleanup
            await self.async_teardown()
            self.assertFalse(self.display_manager.is_ready)

        asyncio.run(run_test())

    def test_performance(self):
        """Test display performance metrics."""
        async def run_test():
            await self.async_setup()

            # Measure display update time
            start_time = time.time()
            await self.display_manager.display_image(
                str(self.test_pattern_path),
                {'rotation': 0, 'scale': 1.0}
            )
            update_time = time.time() - start_time

            # Should complete within 1 second
            self.assertLess(update_time, 1.0)

            # Test multiple rapid updates
            times = []
            for _ in range(5):
                start_time = time.time()
                await self.display_manager.display_image(
                    str(self.test_pattern_path),
                    {'rotation': 0, 'scale': 1.0}
                )
                times.append(time.time() - start_time)

            # Check average and variance
            avg_time = sum(times) / len(times)
            self.assertLess(avg_time, 1.0)

            # Variance should be low (consistent performance)
            variance = sum((t - avg_time) ** 2 for t in times) / len(times)
            self.assertLess(variance, 0.1)

            await self.async_teardown()

        asyncio.run(run_test())

    def test_virtual_display_fallback(self):
        """Test virtual display fallback functionality."""
        async def run_test():
            # Mock hardware display failure
            with patch('IT8951.display.AutoEPDDisplay', side_effect=Exception):
                display_manager = DisplayManager()

                # Should fall back to virtual display
                self.assertTrue(await display_manager.initialize())
                self.assertTrue(display_manager.is_ready)

                # Should still handle display operations
                result = await display_manager.display_image(
                    str(self.test_pattern_path),
                    {'rotation': 0, 'scale': 1.0}
                )
                self.assertTrue(result)

                await display_manager.cleanup()

        asyncio.run(run_test())

    def test_display_recovery(self):
        """Test display recovery after errors."""
        async def run_test():
            await self.async_setup()

            # Simulate display error
            self.display_manager._display = None

            # Should recover on next operation
            result = await self.display_manager.display_image(
                str(self.test_pattern_path),
                {'rotation': 0, 'scale': 1.0}
            )
            self.assertTrue(result)
            self.assertTrue(self.display_manager.is_ready)

            await self.async_teardown()

        asyncio.run(run_test())

    def tearDown(self):
        """Clean up test environment."""
        # Remove test images
        for path in self.test_images_dir.glob('*.png'):
            path.unlink()
        self.test_images_dir.rmdir()
