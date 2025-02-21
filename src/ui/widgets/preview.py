from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QImage
from PIL import Image
import logging

logger = logging.getLogger(__name__)

class PreviewWidget(QWidget):
    """Widget for displaying image previews."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        # Preview label
        self.preview_label = QLabel()
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setMinimumSize(300, 300)
        self.preview_label.setStyleSheet("""
            QLabel {
                background-color: #2A2A2A;
                border: 1px solid #3E3E3E;
                border-radius: 4px;
            }
        """)
        layout.addWidget(self.preview_label)

        self.setLayout(layout)

    def update_preview(self, image: Image.Image):
        """Update the preview with a PIL Image."""
        try:
            # Convert PIL image to QPixmap
            if image.mode == 'RGBA':
                data = image.tobytes('raw', 'RGBA')
                qim = QImage(data, image.size[0], image.size[1], QImage.Format_RGBA8888)
            else:
                data = image.convert('RGBA').tobytes('raw', 'RGBA')
                qim = QImage(data, image.size[0], image.size[1], QImage.Format_RGBA8888)

            # Create pixmap and scale to fit
            pixmap = QPixmap.fromImage(qim)
            scaled = pixmap.scaled(
                self.preview_label.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )

            # Update label
            self.preview_label.setPixmap(scaled)

        except Exception as e:
            logger.error(f"Failed to update preview: {e}")
            self.clear_preview()

    def clear_preview(self):
        """Clear the preview."""
        self.preview_label.clear()
        self.preview_label.setText("No preview available")
