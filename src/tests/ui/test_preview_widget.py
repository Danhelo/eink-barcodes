"""
Test suite for preview widget functionality.
"""
from tests.base_test import BaseTestCase
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt, QSize
import sys
from PIL import Image
from src.ui.widgets.preview import PreviewWidget

class TestPreviewWidget(BaseTestCase):
    """Test cases for preview widget."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Create QApplication instance
        cls.app = QApplication.instance() or QApplication(sys.argv)

    def setUp(self):
        super().setUp()
        self.widget = PreviewWidget()

    def test_initial_state(self):
        """Test initial widget state."""
        self.assertIsNone(self.widget.current_image)
        self.assertEqual(self.widget.preview_label.pixmap(), None)

    def test_update_preview(self):
        """Test preview update with new image."""
        # Create test image
        test_image = self.create_test_image((200, 200))

        # Update preview
        self.widget.update_preview(test_image)

        # Verify update
        self.assertIsNotNone(self.widget.current_image)
        self.assertIsNotNone(self.widget.preview_label.pixmap())
        self.assertImageEqual(
            Image.fromqpixmap(self.widget.preview_label.pixmap()),
            test_image
        )

    def test_clear_preview(self):
        """Test preview clearing."""
        # Set initial image
        test_image = self.create_test_image()
        self.widget.update_preview(test_image)

        # Clear preview
        self.widget.clear_preview()

        # Verify cleared
        self.assertIsNone(self.widget.current_image)
        self.assertEqual(self.widget.preview_label.pixmap(), None)

    def test_resize_handling(self):
        """Test preview handling of resize events."""
        # Set initial image
        test_image = self.create_test_image((400, 400))
        self.widget.update_preview(test_image)

        # Resize widget
        new_size = QSize(200, 200)
        self.widget.resize(new_size)

        # Verify image scaled
        pixmap = self.widget.preview_label.pixmap()
        self.assertLessEqual(pixmap.width(), new_size.width())
        self.assertLessEqual(pixmap.height(), new_size.height())

    def test_aspect_ratio_maintained(self):
        """Test that image aspect ratio is maintained."""
        # Create non-square test image
        test_image = self.create_test_image((400, 200))
        original_ratio = test_image.size[0] / test_image.size[1]

        # Update preview
        self.widget.update_preview(test_image)

        # Get displayed image
        pixmap = self.widget.preview_label.pixmap()
        displayed_ratio = pixmap.width() / pixmap.height()

        # Verify ratio maintained
        self.assertAlmostEqual(original_ratio, displayed_ratio, places=2)

    def test_invalid_image(self):
        """Test handling of invalid image input."""
        with self.assertLogs(level='ERROR'):
            self.widget.update_preview(None)

        self.assertIsNone(self.widget.current_image)
        self.assertEqual(self.widget.preview_label.pixmap(), None)

    def test_get_current_image(self):
        """Test getting current image."""
        # Set test image
        test_image = self.create_test_image()
        self.widget.update_preview(test_image)

        # Get current image
        current = self.widget.get_current_image()

        # Verify image
        self.assertIsNotNone(current)
        self.assertImageEqual(current, test_image)

        # Verify returned copy
        self.assertIsNot(current, self.widget.current_image)

    def test_minimum_size(self):
        """Test widget maintains minimum size."""
        min_size = self.widget.preview_label.minimumSize()

        # Try to resize smaller
        self.widget.resize(10, 10)

        # Verify size constraints
        self.assertGreaterEqual(self.widget.width(), min_size.width())
        self.assertGreaterEqual(self.widget.height(), min_size.height())
