"""
Test suite for custom test page functionality.
"""
from tests.base_test import BaseTestCase
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtTest import QTest
import sys
import numpy as np
from pathlib import Path
from PIL import Image
from src.ui.pages.custom_test import CustomTestPage
from src.core.state_manager import TestState, TestContext

class TestCustomTestPage(BaseTestCase):
    """Test cases for custom test page."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.app = QApplication.instance() or QApplication(sys.argv)

        # Create test data directory
        cls.test_data_dir = Path("test_data")
        cls.test_data_dir.mkdir(exist_ok=True)

        # Create test image
        cls.test_image = cls.test_data_dir / "test_barcode.png"
        cls.create_test_image().save(cls.test_image)

    def setUp(self):
        super().setUp()
        self.page = CustomTestPage()

    def test_arbitrary_rotation(self):
        """Test arbitrary angle rotation."""
        # Load test image
        self.page.current_image = self.create_test_image()
        self.page.current_image_path = str(self.test_image)

        # Test various angles
        test_angles = [0, 30, 45, 60, 90, 120, 180, 270, 315]

        for angle in test_angles:
            with self.subTest(angle=angle):
                # Set rotation
                self.page.rotation_slider.setValue(angle)
                QTest.qWait(100)  # Allow UI updates

                # Verify rotation value displayed
                self.assertEqual(
                    self.page.rotation_value.text(),
                    f"{angle}°"
                )

                # Verify preview updated
                self.assertIsNotNone(self.page.preview.current_image)

                # Verify config
                config = self.page.create_test_config()
                self.assertEqual(
                    config.transformations.get('rotation'),
                    float(angle)
                )

    def test_rotation_edge_cases(self):
        """Test rotation edge cases."""
        self.page.current_image = self.create_test_image()
        self.page.current_image_path = str(self.test_image)

        # Test rotation limits
        self.page.rotation_slider.setValue(-10)
        self.assertEqual(self.page.rotation_slider.value(), 0)

        self.page.rotation_slider.setValue(400)
        self.assertEqual(self.page.rotation_slider.value(), 360)

        # Test small angle increments
        small_angles = [1, 5, 10]
        for angle in small_angles:
            self.page.rotation_slider.setValue(angle)
            QTest.qWait(100)
            self.assertIsNotNone(self.page.preview.current_image)

    def test_rotation_with_scale(self):
        """Test rotation combined with scaling."""
        self.page.current_image = self.create_test_image()
        self.page.current_image_path = str(self.test_image)

        # Test combinations
        test_cases = [
            (45, 0.5),
            (90, 1.5),
            (180, 2.0),
            (270, 0.75)
        ]

        for angle, scale in test_cases:
            with self.subTest(angle=angle, scale=scale):
                # Set transformations
                self.page.rotation_slider.setValue(angle)
                self.page.scale_spin.setValue(scale)
                QTest.qWait(100)

                # Verify preview
                self.assertIsNotNone(self.page.preview.current_image)

                # Verify config
                config = self.page.create_test_config()
                self.assertEqual(
                    config.transformations.get('rotation'),
                    float(angle)
                )
                self.assertEqual(
                    config.transformations.get('scale'),
                    scale
                )

    def test_auto_center(self):
        """Test auto-center with rotation."""
        self.page.current_image = self.create_test_image()
        self.page.current_image_path = str(self.test_image)

        # Enable auto-center
        self.page.auto_center.setChecked(True)

        # Test with rotation
        self.page.rotation_slider.setValue(45)
        QTest.qWait(100)

        # Verify preview centered
        preview = self.page.preview.current_image
        self.assertIsNotNone(preview)

        # Get preview center
        center_x = preview.width // 2
        center_y = preview.height // 2

        # Check image content near center
        # This is a basic check - could be enhanced for more precise validation
        self.assertGreater(
            np.mean(np.array(preview)[
                center_y-10:center_y+10,
                center_x-10:center_x+10
            ]),
            0
        )

    def test_rotation_quality(self):
        """Test image quality preservation during rotation."""
        # Create test pattern
        pattern = Image.new('L', (100, 100), 255)
        for x in range(0, 100, 10):
            for y in range(0, 100, 10):
                pattern.putpixel((x, y), 0)

        self.page.current_image = pattern
        self.page.current_image_path = str(self.test_image)

        # Test rotation quality
        angles = [45, 90, 135]
        for angle in angles:
            with self.subTest(angle=angle):
                self.page.rotation_slider.setValue(angle)
                QTest.qWait(100)

                # Get preview
                preview = self.page.preview.current_image
                self.assertIsNotNone(preview)

                # Calculate image statistics
                orig_stats = self._get_image_stats(pattern)
                preview_stats = self._get_image_stats(preview)

                # Verify quality maintained
                self.assertAlmostEqual(
                    orig_stats['mean'],
                    preview_stats['mean'],
                    delta=10
                )
                self.assertAlmostEqual(
                    orig_stats['std'],
                    preview_stats['std'],
                    delta=10
                )

    def test_rotation_performance(self):
        """Test rotation performance."""
        self.page.current_image = self.create_test_image((500, 500))
        self.page.current_image_path = str(self.test_image)

        import time

        # Test rotation speed
        angles = list(range(0, 360, 15))
        times = []

        for angle in angles:
            start = time.time()
            self.page.rotation_slider.setValue(angle)
            QTest.qWait(100)
            times.append(time.time() - start)

        # Verify reasonable performance
        avg_time = sum(times) / len(times)
        self.assertLess(avg_time, 0.5)  # Should update in under 500ms

    @staticmethod
    def _get_image_stats(image):
        """Calculate basic image statistics."""
        arr = np.array(image)
        return {
            'mean': np.mean(arr),
            'std': np.std(arr)
        }

    @classmethod
    def create_test_image(cls, size=(200, 100)):
        """Create a test barcode-like image."""
        image = Image.new('L', size, 255)  # White background
        draw = Image.ImageDraw.Draw(image)

        # Draw some black bars
        bar_width = size[0] // 10
        for i in range(0, size[0], bar_width * 2):
            draw.rectangle([(i, 0), (i + bar_width, size[1])], fill=0)

        return image

    def tearDown(self):
        super().tearDown()
        self.page.cleanup()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        # Clean up test data
        if cls.test_data_dir.exists():
            for file in cls.test_data_dir.iterdir():
                file.unlink()
            cls.test_data_dir.rmdir()
