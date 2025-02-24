"""
Preview widget for displaying barcode images.
"""
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QPixmap, QImage
import logging
from PIL import Image
import numpy as np
from typing import Optional

logger = logging.getLogger(__name__)

class PreviewWidget(QWidget):
    """Widget for displaying and manipulating preview images."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_image: Optional[Image.Image] = None
        self.setup_ui()

    def setup_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        # Preview label
        self.preview_label = QLabel()
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setMinimumSize(QSize(300, 200))
        self.preview_label.setStyleSheet("""
            QLabel {
                background-color: #2E2E2E;
                border: 1px solid #555555;
                border-radius: 4px;
            }
        """)
        layout.addWidget(self.preview_label)

        self.setLayout(layout)

    def pil_to_pixmap(self, image: Image.Image) -> QPixmap:
        """Convert PIL Image to QPixmap.

        Args:
            image: PIL Image to convert

        Returns:
            QPixmap version of the image
        """
        # Convert PIL image to RGB if it isn't
        if image.mode != 'RGB':
            image = image.convert('RGB')

        # Convert to numpy array
        data = np.array(image)
        height, width, channels = data.shape

        # Create QImage from numpy array
        bytes_per_line = channels * width
        qimage = QImage(
            data.data,
            width,
            height,
            bytes_per_line,
            QImage.Format_RGB888
        )

        return QPixmap.fromImage(qimage)

    def update_preview(self, image: Image.Image):
        """Update preview with new image.

        Args:
            image: PIL Image to display
        """
        try:
            self.current_image = image

            # Convert PIL image to QPixmap
            pixmap = self.pil_to_pixmap(image)

            # Scale pixmap to fit label while maintaining aspect ratio
            scaled = pixmap.scaled(
                self.preview_label.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )

            self.preview_label.setPixmap(scaled)

        except Exception as e:
            logger.error(f"Failed to update preview: {e}")
            self.clear_preview()

    def clear_preview(self):
        """Clear the current preview."""
        self.current_image = None
        self.preview_label.clear()

    def resizeEvent(self, event):
        """Handle widget resize events."""
        super().resizeEvent(event)
        if self.current_image:
            # Re-scale image on resize
            self.update_preview(self.current_image)

    def get_current_image(self) -> Optional[Image.Image]:
        """Get the currently displayed image.

        Returns:
            Current image or None if no image is displayed
        """
        return self.current_image.copy() if self.current_image else None
