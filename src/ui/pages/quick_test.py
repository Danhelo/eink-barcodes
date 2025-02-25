"""
Quick test page implementation.
"""
from PyQt5.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel,
    QComboBox, QGroupBox, QPushButton,
    QSpinBox
)
from PyQt5.QtCore import Qt
import os
import logging
from PIL import Image
from typing import Optional, List

from .base_test_page import BaseTestPage
from ...core.test_controller import TestController
from ...core.test_config import TestConfig

logger = logging.getLogger(__name__)

class QuickTestPage(BaseTestPage):
    """Quick test page with basic barcode testing functionality."""

    page_title = "Quick Test"

    def __init__(self, parent=None, test_controller: Optional[TestController] = None):
        """Initialize QuickTestPage.

        Args:
            parent: Parent widget (should be MainWindow)
            test_controller: Test controller instance
        """
        # Ensure parent is set before base class initialization
        super().__init__(parent, test_controller)
        self.current_barcodes: List[str] = []
        self.current_index: int = 0
        self.setup_ui()

    def setup_ui(self):
        """Initialize the user interface."""
        layout, _ = self.setup_base_ui()

        # Barcode Type Selection
        type_group = QGroupBox("Barcode Type")
        type_layout = QVBoxLayout()

        self.barcode_combo = QComboBox()
        self.barcode_combo.addItems(["Code128", "QR Code", "DataMatrix"])
        self.barcode_combo.currentTextChanged.connect(self.load_barcodes)
        type_layout.addWidget(self.barcode_combo)

        type_group.setLayout(type_layout)
        layout.addWidget(type_group)

        # Test Configuration
        config_group = QGroupBox("Test Configuration")
        config_layout = QVBoxLayout()

        # Number of images to test
        image_count_layout = QHBoxLayout()
        image_count_layout.addWidget(QLabel("Number of images to test:"))
        self.image_count_spinner = QSpinBox()
        self.image_count_spinner.setMinimum(1)
        self.image_count_spinner.setMaximum(20)
        self.image_count_spinner.setValue(5)
        image_count_layout.addWidget(self.image_count_spinner)
        config_layout.addLayout(image_count_layout)

        # Add delay between images
        delay_layout = QHBoxLayout()
        delay_layout.addWidget(QLabel("Delay between images (seconds):"))
        self.delay_spinner = QSpinBox()
        self.delay_spinner.setMinimum(0)
        self.delay_spinner.setMaximum(10)
        self.delay_spinner.setValue(1)
        delay_layout.addWidget(self.delay_spinner)
        config_layout.addLayout(delay_layout)

        config_group.setLayout(config_layout)
        layout.addWidget(config_group)

        # Preview Area
        preview_group = QGroupBox("Preview")
        preview_layout = QVBoxLayout()

        # Preview widget
        self.preview = self.create_preview_widget()
        preview_layout.addWidget(self.preview)

        # Navigation controls
        nav_layout = QHBoxLayout()

        self.prev_button = QPushButton("Previous")
        self.prev_button.clicked.connect(self.show_previous)
        nav_layout.addWidget(self.prev_button)

        self.preview_label = QLabel("0/0")
        self.preview_label.setAlignment(Qt.AlignCenter)
        nav_layout.addWidget(self.preview_label)

        self.next_button = QPushButton("Next")
        self.next_button.clicked.connect(self.show_next)
        nav_layout.addWidget(self.next_button)

        preview_layout.addLayout(nav_layout)
        preview_group.setLayout(preview_layout)
        layout.addWidget(preview_group)

        # Controls
        controls_group = self.create_controls_group()
        layout.addWidget(controls_group)

        # Progress bar
        self.progress = self.create_progress_bar()
        layout.addWidget(self.progress)

        self.setLayout(layout)

        # Load initial barcodes
        self.load_barcodes(self.barcode_combo.currentText())

    def load_barcodes(self, barcode_type: str):
        """Load barcodes of the selected type."""
        try:
            # Clear current barcodes
            self.current_barcodes = []
            self.current_index = 0

            # Get path for barcode type
            path = os.path.join('known_barcode', barcode_type)
            if not os.path.exists(path):
                logger.warning(f"No directory found for {barcode_type}")
                self.update_preview()
                return

            # Load all images
            for filename in os.listdir(path):
                if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                    image_path = os.path.join(path, filename)
                    self.current_barcodes.append(image_path)

            # Update UI
            self.update_navigation()
            self.update_preview()

        except Exception as e:
            logger.error(f"Failed to load barcodes: {e}")

    def show_previous(self):
        """Show the previous barcode."""
        if self.current_barcodes and self.current_index > 0:
            self.current_index -= 1
            self.update_preview()
            self.update_navigation()

    def show_next(self):
        """Show the next barcode."""
        if self.current_barcodes and self.current_index < len(self.current_barcodes) - 1:
            self.current_index += 1
            self.update_preview()
            self.update_navigation()

    def update_navigation(self):
        """Update navigation controls state."""
        has_barcodes = bool(self.current_barcodes)
        self.prev_button.setEnabled(has_barcodes and self.current_index > 0)
        self.next_button.setEnabled(has_barcodes and self.current_index < len(self.current_barcodes) - 1)

        if has_barcodes:
            self.preview_label.setText(f"{self.current_index + 1}/{len(self.current_barcodes)}")
        else:
            self.preview_label.setText("0/0")

    def update_preview(self):
        """Update the preview widget with current barcode."""
        try:
            if self.current_barcodes and 0 <= self.current_index < len(self.current_barcodes):
                image_path = self.current_barcodes[self.current_index]
                image = Image.open(image_path)
                self.preview.update_preview(image)
            else:
                self.preview.clear_preview()
        except Exception as e:
            logger.error(f"Failed to update preview: {e}")
            self.preview.clear_preview()

    def validate_config(self) -> bool:
        """Validate test configuration."""
        if not self.current_barcodes:
            self.handle_error("No barcodes available for testing")
            return False

        # Check if we have enough images
        requested_count = self.image_count_spinner.value()
        available_count = len(self.current_barcodes)

        if requested_count > available_count:
            self.handle_error(f"Requested {requested_count} images but only {available_count} are available")
            return False

        return True

    def create_test_config(self) -> Optional[TestConfig]:
        """Create test configuration."""
        try:
            # Get the number of images to test
            count = min(self.image_count_spinner.value(), len(self.current_barcodes))

            # Start from the current index and wrap around if needed
            image_paths = []
            for i in range(count):
                index = (self.current_index + i) % len(self.current_barcodes)
                image_paths.append(self.current_barcodes[index])

            return TestConfig(
                barcode_type=self.barcode_combo.currentText(),
                image_paths=image_paths,
                count=count,
                delay_between_images=self.delay_spinner.value(),
                transformations={
                    "rotation": 0.0,
                    "scale": 1.0,
                    "mirror": False
                }
            )
        except Exception as e:
            logger.error(f"Failed to create test config: {e}")
            self.handle_error(str(e))
            return None
