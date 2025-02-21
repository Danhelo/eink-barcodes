"""
Integration tests for E-ink display rotation functionality.
"""
import unittest
from PIL import Image
import numpy as np
import time
import psutil
import threading
from pathlib import Path
from IT8951.display import AutoEPDDisplay
from IT8951.img_transform import prepare_image_for_display, rotate_image
from IT8951 import constants

class TestDisplayRotation(unittest.TestCase):
    """Test suite for E-ink display rotation functionality."""

    @classmethod
    def setUpClass(cls):
        """Set up test environment."""
        try:
            cls.display = AutoEPDDisplay(vcom=-2.02)
        except Exception as e:
            cls.skipTest(cls, f"E-ink display not available: {e}")

        # Create test patterns
        cls.test_patterns = cls._create_test_patterns()

    def setUp(self):
        """Set up each test."""
        self.display.clear()
        self.start_memory = psutil.Process().memory_info().rss

    def _create_test_patterns(self):
        """Create test patterns for rotation testing."""
        patterns = {}

        # Simple cross pattern
        cross = Image.new('L', (100, 100), 255)
        for i in range(100):
            cross.putpixel((i, 50), 0)  # Horizontal line
            cross.putpixel((50, i), 0)  # Vertical line
        patterns['cross'] = cross

        # Grid pattern
        grid = Image.new('L', (100, 100), 255)
        for i in range(0, 100, 10):
            for j in range(100):
                grid.putpixel((i, j), 0)
                grid.putpixel((j, i), 0)
        patterns['grid'] = grid

        # Text pattern
        text = Image.new('L', (100, 30), 255)
        # Add text using PIL's ImageDraw here if needed
        patterns['text'] = text

        return patterns

    def test_basic_rotation(self):
        """Test basic rotation functionality."""
        test_angles = [0, 90, 180, 270]
        pattern = self.test_patterns['cross']

        for angle in test_angles:
            with self.subTest(angle=angle):
                # Rotate image
                rotated = prepare_image_for_display(pattern, angle=angle)

                # Display image
                self.display.draw_full(rotated)

                # Verify dimensions
                if angle in [0, 180]:
                    self.assertEqual(rotated.size, pattern.size)
                else:
                    self.assertEqual(rotated.size[0], pattern.size[1])
                    self.assertEqual(rotated.size[1], pattern.size[0])

    def test_arbitrary_rotation(self):
        """Test arbitrary angle rotation."""
        pattern = self.test_patterns['grid']
        test_angles = [30, 45, 60, 120, 150]

        for angle in test_angles:
            with self.subTest(angle=angle):
                # Rotate and display
                rotated = prepare_image_for_display(pattern, angle=angle)
                self.display.draw_full(rotated)

                # Verify image properties
                self.assertGreater(rotated.size[0], pattern.size[0])
                self.assertGreater(rotated.size[1], pattern.size[1])

                # Check content preservation
                # Convert to numpy arrays for analysis
                rotated_arr = np.array(rotated)
                self.assertGreater(np.sum(rotated_arr < 128), 100)  # Some black pixels remain

    def test_rotation_performance(self):
        """Test rotation performance metrics."""
        pattern = self.test_patterns['grid']
        angles = list(range(0, 360, 5))
        timings = []

        for angle in angles:
            start_time = time.time()
            rotated = prepare_image_for_display(pattern, angle=angle)
            self.display.draw_full(rotated)
            timings.append(time.time() - start_time)

        # Performance assertions
        avg_time = sum(timings) / len(timings)
        self.assertLess(avg_time, 0.5)  # Should complete in under 500ms

    def test_memory_management(self):
        """Test memory management during rotation."""
        pattern = self.test_patterns['grid']

        # Test memory usage during multiple rotations
        for _ in range(10):
            for angle in range(0, 360, 15):
                rotated = prepare_image_for_display(pattern, angle=angle)
                self.display.draw_full(rotated)

        # Check memory usage
        end_memory = psutil.Process().memory_info().rss
        memory_increase = end_memory - self.start_memory

        # Should not increase by more than 50MB
        self.assertLess(memory_increase, 50 * 1024 * 1024)

    def test_continuous_rotation(self):
        """Test continuous rotation stability."""
        pattern = self.test_patterns['cross']
        stop_event = threading.Event()
        error_event = threading.Event()

        def rotation_thread():
            try:
                angle = 0
                while not stop_event.is_set():
                    rotated = prepare_image_for_display(pattern, angle=angle)
                    self.display.draw_full(rotated)
                    angle = (angle + 5) % 360
                    time.sleep(0.1)
            except Exception as e:
                error_event.set()
                self.fail(f"Rotation thread failed: {e}")

        # Run rotation for 5 seconds
        thread = threading.Thread(target=rotation_thread)
        thread.start()
        time.sleep(5)
        stop_event.set()
        thread.join()

        self.assertFalse(error_event.is_set())

    def test_rotation_quality(self):
        """Test image quality preservation during rotation."""
        pattern = self.test_patterns['grid']
        original_stats = self._get_image_stats(pattern)

        test_angles = [45, 90, 135]
        for angle in test_angles:
            with self.subTest(angle=angle):
                rotated = prepare_image_for_display(pattern, angle=angle)
                rotated_stats = self._get_image_stats(rotated)

                # Verify quality metrics
                self.assertAlmostEqual(
                    original_stats['mean'],
                    rotated_stats['mean'],
                    delta=10
                )
                self.assertAlmostEqual(
                    original_stats['std'],
                    rotated_stats['std'],
                    delta=10
                )

    def test_error_handling(self):
        """Test error handling during rotation."""
        # Test invalid angles
        with self.assertRaises(ValueError):
            prepare_image_for_display(self.test_patterns['cross'], angle=400)

        # Test None image
        with self.assertRaises(TypeError):
            prepare_image_for_display(None, angle=45)

        # Test invalid image mode
        rgb_image = Image.new('RGB', (100, 100))
        rotated = prepare_image_for_display(rgb_image, angle=45)
        self.assertEqual(rotated.mode, 'L')  # Should convert to grayscale

    def test_display_modes(self):
        """Test different display update modes."""
        pattern = self.test_patterns['cross']
        angle = 45

        # Test different display modes
        modes = [
            constants.DisplayModes.GC16,
            constants.DisplayModes.GL16,
            constants.DisplayModes.DU,
            constants.DisplayModes.A2
        ]

        for mode in modes:
            with self.subTest(mode=mode):
                rotated = prepare_image_for_display(pattern, angle=angle)
                self.display.draw_full(rotated, mode)
                time.sleep(1)  # Allow display update

    def _get_image_stats(self, image):
        """Calculate image statistics."""
        arr = np.array(image)
        return {
            'mean': np.mean(arr),
            'std': np.std(arr),
            'min': np.min(arr),
            'max': np.max(arr)
        }

    def tearDown(self):
        """Clean up after each test."""
        self.display.clear()

    @classmethod
    def tearDownClass(cls):
        """Clean up test environment."""
        if hasattr(cls, 'display'):
            cls.display.clear()
            cls.display._close()
