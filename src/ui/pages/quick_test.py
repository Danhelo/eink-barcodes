from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QComboBox, QGroupBox, QProgressBar,
    QMessageBox
)
from PyQt5.QtCore import Qt, pyqtSignal, QThread
from PyQt5.QtGui import QFont, QPixmap
import os
import logging
from PIL import Image
from typing import List, Optional
import asyncio
import json
import websockets

from ..widgets.preview import PreviewWidget
from ...core.test_config import TestConfig
from ...core.backend_interface import BackendInterface

logger = logging.getLogger(__name__)

class TestWorker(QThread):
    """Worker thread for running tests."""
    progress = pyqtSignal(int)
    error = pyqtSignal(str)
    finished = pyqtSignal(bool)  # True if completed normally, False if stopped

    def __init__(self, config: dict):
        super().__init__()
        self.config = config
        self.backend = BackendInterface()
        self.running = True
        self.websocket = None
        self.server = None

    def run(self):
        """Run the test."""
        try:
            # Create event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            # Start server and run test
            loop.run_until_complete(self.backend.start_server())
            loop.run_until_complete(self.run_test())

        except Exception as e:
            self.error.emit(str(e))
            self.finished.emit(False)
        finally:
            self.cleanup()

    def cleanup(self):
        """Clean up resources."""
        try:
            # Close the backend
            if hasattr(self, 'backend'):
                self.backend.cleanup()

            # Close any event loop
            loop = asyncio.get_event_loop()
            if loop and not loop.is_closed():
                loop.close()
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

    async def run_test(self):
        """Run the test with WebSocket connection."""
        uri = f"ws://localhost:5440"
        try:
            async with websockets.connect(uri) as websocket:
                self.websocket = websocket
                logger.info(f"Client connected to {uri}")

                # Send configuration
                await websocket.send(json.dumps(self.config))

                # Wait for responses
                while self.running:
                    try:
                        response = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                        data = json.loads(response)

                        if data.get("status") == "progress":
                            self.progress.emit(data.get("progress", 0))
                        elif data.get("status") == "complete":
                            logger.info("Test completed successfully")
                            self.finished.emit(True)
                            break
                        elif data.get("status") == "error":
                            logger.error(f"Test error: {data.get('message')}")
                            self.error.emit(data.get("message"))
                            self.finished.emit(False)
                            break
                        elif data.get("status") == "stopped":
                            logger.info("Test stopped by user")
                            self.finished.emit(False)
                            break

                    except asyncio.TimeoutError:
                        # Check if we should stop
                        if not self.running:
                            # Send stop command
                            await websocket.send(json.dumps({
                                "command": "stop"
                            }))
                            self.finished.emit(False)
                            break
                    except websockets.exceptions.ConnectionClosed:
                        if self.running:  # Only emit error if we didn't stop intentionally
                            self.error.emit("Connection closed unexpectedly")
                        self.finished.emit(False)
                        break

        except Exception as e:
            logger.error(f"Client error: {e}")
            self.error.emit(str(e))
            self.finished.emit(False)

    def stop(self):
        """Stop the test."""
        self.running = False

class QuickTestPage(QWidget):
    """Quick test configuration page with barcode preview."""
    test_started = pyqtSignal(TestConfig)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = self.window()
        self.config = TestConfig()
        self.current_barcodes: List[str] = []
        self.current_index: int = 0
        self.test_worker: Optional[TestWorker] = None
        self.setup_ui()

    def setup_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout()
        layout.setSpacing(25)
        layout.setContentsMargins(30, 30, 30, 30)

        # Title
        title = QLabel("Quick Test")
        title.setFont(QFont("Arial", 32, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #FFFFFF; margin-bottom: 20px;")
        layout.addWidget(title)

        # Barcode Type Selection
        type_group = QGroupBox("Barcode Type")
        type_layout = QVBoxLayout()
        type_layout.setSpacing(15)

        self.barcode_combo = QComboBox()
        self.barcode_combo.addItems(["Code128", "QR Code", "DataMatrix"])
        self.barcode_combo.currentTextChanged.connect(self.load_barcodes)
        type_layout.addWidget(self.barcode_combo)

        type_group.setLayout(type_layout)
        layout.addWidget(type_group)

        # Preview Area
        preview_group = QGroupBox("Preview")
        preview_layout = QVBoxLayout()
        preview_layout.setSpacing(15)

        # Preview widget
        self.preview = PreviewWidget()
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

        # Test Controls
        controls_group = QGroupBox("Test Controls")
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(15)

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

        # Progress Bar
        self.progress = QProgressBar()
        self.progress.setTextVisible(True)
        self.progress.setAlignment(Qt.AlignCenter)
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

    def start_test(self):
        """Start the test sequence."""
        try:
            if not self.current_barcodes:
                raise ValueError("No barcodes available for testing")

            # Create test configuration
            config = {
                "command": "Display Barcode",
                "Presigned URL": "",
                "pre-test": "no",
                "known_barcode": "yes",
                "barcode-type": self.barcode_combo.currentText(),
                "socket-type": "ws",  # Using WebSocket mode
                "transformations": {
                    "rotation": 0.0,
                    "scale": 1.0,
                    "mirror": False
                },
                "barcode_path": self.current_barcodes[self.current_index]
            }

            # Create and start worker thread
            self.test_worker = TestWorker(config)
            self.test_worker.progress.connect(self.progress.setValue)
            self.test_worker.error.connect(self.handle_error)
            self.test_worker.finished.connect(self.test_finished)

            # Update UI state
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            self.barcode_combo.setEnabled(False)
            self.progress.setValue(0)

            # Start test
            self.test_worker.start()

        except Exception as e:
            logger.error(f"Failed to start test: {e}")
            self.handle_error(str(e))

    def stop_test(self):
        """Stop the current test."""
        if self.test_worker and self.test_worker.isRunning():
            self.test_worker.stop()  # Signal worker to stop
            self.test_worker.wait()  # Wait for worker to finish

    def test_finished(self, completed: bool):
        """Handle test completion."""
        self.reset_ui()
        if completed:
            QMessageBox.information(self, "Test Complete", "Test sequence completed successfully")
        else:
            QMessageBox.information(self, "Test Stopped", "Test sequence was stopped by user")

    def handle_error(self, error_msg: str):
        """Handle test errors."""
        logger.error(f"Test error: {error_msg}")
        self.reset_ui()
        QMessageBox.critical(self, "Test Error", f"Error during test: {error_msg}")

    def reset_ui(self):
        """Reset UI to initial state."""
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.barcode_combo.setEnabled(True)
        self.progress.setValue(0)

        # Clean up worker
        if self.test_worker:
            self.test_worker.cleanup()
            self.test_worker = None
