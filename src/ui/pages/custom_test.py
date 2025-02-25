"""
Custom test page implementation with advanced options.
"""
from PyQt5.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel,
    QComboBox, QSpinBox, QDoubleSpinBox,
    QSlider, QGroupBox, QCheckBox,
    QFileDialog, QPushButton
)
from PyQt5.QtCore import Qt
import os
import logging
from PIL import Image
from typing import Optional

from .base_test_page import BaseTestPage
from ...core.test_controller import TestController
from ...core.test_config import TestConfig

logger = logging.getLogger(__name__)

class CustomTestPage(BaseTestPage):
    """Custom test page with advanced configuration options."""

    page_title = "Custom Test"

    def __init__(self, parent=None, test_controller: Optional[TestController] = None):
        """Initialize CustomTestPage.

        Args:
            parent: Parent widget (should be MainWindow)
            test_controller: Test controller instance
        """
        # Ensure parent is set before base class initialization
        super().__init__(parent, test_controller)
        self.current_image: Optional[Image.Image] = None
        self.current_image_path: Optional[str] = None
        self.setup_ui()

    def setup_ui(self):
        """Initialize the user interface."""
        layout, _ = self.setup_base_ui()

        # Split into left and right columns
        content_layout = QHBoxLayout()

        # Left side - Configuration
        config_layout = QVBoxLayout()

        # Barcode Selection
        barcode_group = QGroupBox("Barcode Selection")
        barcode_layout = QVBoxLayout()

        # Type selection
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("Type:"))
        self.type_combo = QComboBox()
        self.type_combo.addItems(["Code128", "QR Code", "DataMatrix"])
        type_layout.addWidget(self.type_combo)
        barcode_layout.addLayout(type_layout)

        # File selection
        file_layout = QHBoxLayout()
        self.file_path = QLabel("No file selected")
        file_layout.addWidget(self.file_path)
        self.browse_button = QPushButton("Browse")
        self.browse_button.clicked.connect(self.browse_file)
        file_layout.addWidget(self.browse_button)
        barcode_layout.addLayout(file_layout)

        barcode_group.setLayout(barcode_layout)
        config_layout.addWidget(barcode_group)

        # Image Transformations
        transform_group = QGroupBox("Image Transformations")
        transform_layout = QVBoxLayout()

        # Scale
        scale_layout = QHBoxLayout()
        scale_layout.addWidget(QLabel("Scale:"))
        self.scale_spin = QDoubleSpinBox()
        self.scale_spin.setRange(0.1, 2.0)
        self.scale_spin.setSingleStep(0.1)
        self.scale_spin.setValue(1.0)
        self.scale_spin.valueChanged.connect(self.update_preview)
        scale_layout.addWidget(self.scale_spin)
        transform_layout.addLayout(scale_layout)

        # Rotation
        rotation_layout = QVBoxLayout()
        rotation_label = QHBoxLayout()
        rotation_label.addWidget(QLabel("Rotation:"))
        self.rotation_value = QLabel("0°")
        rotation_label.addWidget(self.rotation_value)
        rotation_layout.addLayout(rotation_label)

        self.rotation_slider = QSlider(Qt.Horizontal)
        self.rotation_slider.setRange(0, 360)
        self.rotation_slider.setValue(0)
        self.rotation_slider.setTickPosition(QSlider.TicksBelow)
        self.rotation_slider.setTickInterval(90)
        self.rotation_slider.valueChanged.connect(self.rotation_changed)
        rotation_layout.addWidget(self.rotation_slider)
        transform_layout.addLayout(rotation_layout)

        # Auto-center
        self.auto_center = QCheckBox("Auto-center image")
        self.auto_center.setChecked(True)
        self.auto_center.stateChanged.connect(self.update_preview)
        transform_layout.addWidget(self.auto_center)

        transform_group.setLayout(transform_layout)
        config_layout.addWidget(transform_group)

        # Test Parameters
        params_group = QGroupBox("Test Parameters")
        params_layout = QVBoxLayout()

        # Count
        count_layout = QHBoxLayout()
        count_layout.addWidget(QLabel("Test count:"))
        self.count_spin = QSpinBox()
        self.count_spin.setRange(1, 100)
        self.count_spin.setValue(1)
        count_layout.addWidget(self.count_spin)
        params_layout.addLayout(count_layout)

        # Refresh rate
        refresh_layout = QHBoxLayout()
        refresh_layout.addWidget(QLabel("Refresh rate (Hz):"))
        self.refresh_spin = QDoubleSpinBox()
        self.refresh_spin.setRange(0.1, 10.0)
        self.refresh_spin.setSingleStep(0.1)
        self.refresh_spin.setValue(1.0)
        refresh_layout.addWidget(self.refresh_spin)
        params_layout.addLayout(refresh_layout)

        params_group.setLayout(params_layout)
        config_layout.addWidget(params_group)

        # Right side - Preview
        preview_layout = QVBoxLayout()
        preview_layout.addWidget(self.create_preview_group())

        # Combine layouts
        content_layout.addLayout(config_layout, 1)
        content_layout.addLayout(preview_layout, 1)
        layout.addLayout(content_layout)

        # Controls
        layout.addWidget(self.create_controls_group())

        # Add the progress bar that was created in the parent class
        self.add_progress_bar_to_layout(layout)
        self.setLayout(layout)

    def browse_file(self):
        """Open file dialog to select a barcode image."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Barcode Image",
            "",
            "Images (*.png *.jpg *.jpeg)"
        )

        if file_path:
            try:
                self.current_image = Image.open(file_path)
                self.current_image_path = file_path
                self.file_path.setText(os.path.basename(file_path))
                self.update_preview()
            except Exception as e:
                logger.error(f"Failed to load image: {e}")
                self.current_image = None
                self.current_image_path = None
                self.file_path.setText("Failed to load image")
                self.preview.clear_preview()

    def rotation_changed(self, value: int):
        """Handle rotation slider value change."""
        self.rotation_value.setText(f"{value}°")
        self.update_preview()

    def update_preview(self):
        """Update the preview with current transformations."""
        if not self.current_image:
            return

        try:
            # Apply transformations
            image = self.current_image.copy()

            # Scale
            if self.scale_spin.value() != 1.0:
                new_size = tuple(int(dim * self.scale_spin.value()) for dim in image.size)
                image = image.resize(new_size, Image.Resampling.LANCZOS)

            # Rotate
            if self.rotation_slider.value() != 0:
                image = image.rotate(
                    self.rotation_slider.value(),
                    expand=True,
                    resample=Image.Resampling.BICUBIC
                )

            # Update preview
            self.preview.update_preview(image)

        except Exception as e:
            logger.error(f"Failed to update preview: {e}")
            self.preview.clear_preview()

    def validate_config(self) -> bool:
        """Validate test configuration."""
        if not self.current_image or not self.current_image_path:
            self.handle_error("No image selected")
            return False
        return True

    def create_test_config(self) -> Optional[TestConfig]:
        """Create test configuration."""
        try:
            # Save the transformed image to a temporary file if needed
            image_paths = [self.current_image_path] * self.count_spin.value()

            return TestConfig(
                barcode_type=self.type_combo.currentText(),
                image_paths=image_paths,
                rotation=float(self.rotation_slider.value()),
                scale=self.scale_spin.value(),
                auto_center=self.auto_center.isChecked(),
                refresh_rate=self.refresh_spin.value(),
                count=self.count_spin.value(),
                delay_between_images=1.0 / self.refresh_spin.value()
            )
        except Exception as e:
            logger.error(f"Failed to create test config: {e}")
            self.handle_error(str(e))
            return None
