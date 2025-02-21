from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QComboBox, QSpinBox, QDoubleSpinBox,
    QSlider, QGroupBox, QProgressBar, QCheckBox,
    QFileDialog, QMessageBox
)
from PyQt5.QtCore import Qt, pyqtSignal, QThread
from PyQt5.QtGui import QFont, QPixmap
import os
import logging
from PIL import Image
from typing import Optional
import asyncio
import json

from ..widgets.preview import PreviewWidget
from ...core.test_config import TestConfig
from ...core.backend_interface import BackendInterface

logger = logging.getLogger(__name__)

class TestWorker(QThread):
    """Worker thread for running tests."""
    progress = pyqtSignal(int)
    error = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, config: dict):
        super().__init__()
        self.config = config
        self.backend = BackendInterface()
        self.running = True

    def run(self):
        """Run the test."""
        try:
            # Create event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            # Start server and run test
            loop.run_until_complete(self.backend.start_server())
            loop.run_until_complete(self.backend.send_test_config(self.config))

        except Exception as e:
            self.error.emit(str(e))
        finally:
            self.finished.emit()
            if hasattr(self, 'backend'):
                self.backend.cleanup()

class CustomTestPage(QWidget):
    """Custom test configuration page with advanced options."""
    test_started = pyqtSignal(TestConfig)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = self.window()
        self.config = TestConfig()
        self.current_image: Optional[Image.Image] = None
        self.test_worker: Optional[TestWorker] = None
        self.setup_ui()

    def setup_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout()
        layout.setSpacing(25)
        layout.setContentsMargins(30, 30, 30, 30)

        # Title
        title = QLabel("Custom Test")
        title.setFont(QFont("Arial", 32, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #FFFFFF; margin-bottom: 20px;")
        layout.addWidget(title)

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

        # Preview widget
        preview_group = QGroupBox("Preview")
        preview_inner = QVBoxLayout()
        self.preview = PreviewWidget()
        preview_inner.addWidget(self.preview)
        preview_group.setLayout(preview_inner)
        preview_layout.addWidget(preview_group)

        # Combine layouts
        content_layout = QHBoxLayout()
        content_layout.addLayout(config_layout, 1)
        content_layout.addLayout(preview_layout, 1)
        layout.addLayout(content_layout)

        # Controls
        controls_group = QGroupBox("Test Controls")
        controls_layout = QHBoxLayout()

        self.start_button = QPushButton("Start Test")
        self.start_button.clicked.connect(self.start_test)
        controls_layout.addWidget(self.start_button)

        self.stop_button = QPushButton("Stop")
        self.stop_button.clicked.connect(self.stop_test)
        self.stop_button.setEnabled(False)
        controls_layout.addWidget(self.stop_button)

        self.back_button = QPushButton("Back to Menu")
        self.back_button.clicked.connect(lambda: self.main_window.navigate_to(0))
        controls_layout.addWidget(self.back_button)

        controls_group.setLayout(controls_layout)
        layout.addWidget(controls_group)

        # Progress bar
        self.progress = QProgressBar()
        self.progress.setTextVisible(True)
        self.progress.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.progress)

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
                self.file_path.setText(os.path.basename(file_path))
                self.config.barcode_path = file_path
                self.update_preview()
            except Exception as e:
                logger.error(f"Failed to load image: {e}")
                self.current_image = None
                self.file_path.setText("Failed to load image")

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
                image = image.resize(new_size, Image.LANCZOS)

            # Rotate
            if self.rotation_slider.value() != 0:
                image = image.rotate(
                    self.rotation_slider.value(),
                    expand=True,
                    resample=Image.BICUBIC
                )

            # Update preview
            self.preview.update_preview(image)

        except Exception as e:
            logger.error(f"Failed to update preview: {e}")

    def start_test(self):
        """Start the test sequence."""
        try:
            if not self.current_image:
                raise ValueError("No image selected")

            # Create test configuration
            config = {
                "command": "Display Barcode",
                "Presigned URL": "",
                "pre-test": "no",
                "known_barcode": "no",  # Custom test uses uploaded image
                "barcode-type": self.type_combo.currentText(),
                "socket-type": "ws",  # Using WebSocket mode
                "transformations": {
                    "rotation": float(self.rotation_slider.value()),
                    "scale": self.scale_spin.value(),
                    "mirror": False
                },
                "barcode_path": self.config.barcode_path
            }

            # Create and start worker thread
            self.test_worker = TestWorker(config)
            self.test_worker.progress.connect(self.progress.setValue)
            self.test_worker.error.connect(self.handle_error)
            self.test_worker.finished.connect(self.test_finished)

            # Update UI state
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            self.progress.setValue(0)

            # Start test
            self.test_worker.start()

        except Exception as e:
            logger.error(f"Failed to start test: {e}")
            self.handle_error(str(e))

    def stop_test(self):
        """Stop the current test."""
        if self.test_worker and self.test_worker.isRunning():
            self.test_worker.running = False
            self.test_worker.wait()
        self.reset_ui()

    def test_finished(self):
        """Handle test completion."""
        self.reset_ui()
        QMessageBox.information(self, "Test Complete", "Test sequence completed successfully")

    def handle_error(self, error_msg: str):
        """Handle test errors."""
        logger.error(f"Test error: {error_msg}")
        self.reset_ui()
        QMessageBox.critical(self, "Test Error", f"Error during test: {error_msg}")

    def reset_ui(self):
        """Reset UI to initial state."""
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.progress.setValue(0)
