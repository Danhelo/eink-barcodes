"""
Preview widget for displaying barcode images.
"""
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QPixmap, QImage
import logging
from PIL import Image
from PIL.ImageQt import ImageQt
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

    def update_preview(self, image: Image.Image):
        """Update preview with new image.

        Args:
            image: PIL Image to display
        """
        try:
            self.current_image = image

            # Convert PIL image to QImage
            qimage = ImageQt(image)
            pixmap = QPixmap.fromImage(qimage)

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
