"""
Base test page implementation.
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QProgressBar, QApplication,
    QGroupBox, QMessageBox
)
from PyQt5.QtCore import Qt, pyqtSlot, pyqtSignal
import logging
from typing import Optional, Tuple, Dict, Any
import asyncio
from qasync import asyncSlot

from ..widgets.preview import PreviewWidget
from ...core.test_controller import TestController
from ...core.test_config import TestConfig
from ...core.state_manager import StateObserver, TestState

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  # Set to DEBUG level to see progress updates

class BaseTestPage(QWidget, StateObserver):
    """Base class for test pages."""

    page_title = "Test Page"

    # Define a signal for progress updates
    progress_updated = pyqtSignal(int, str)

    def __init__(self, parent=None, test_controller: Optional[TestController] = None):
        """Initialize BaseTestPage.

        Args:
            parent: Parent widget (should be MainWindow)
            test_controller: Test controller instance
        """
        QWidget.__init__(self, parent)
        StateObserver.__init__(self)
        self.test_controller = test_controller
        self.main_window = parent
        self._test_running = False
        self._last_progress_value = 0  # Track last progress value to prevent jumps

        # Connect the progress signal to the update slot
        self.progress_updated.connect(self._update_progress_ui)

        # Register as observer if test_controller is available
        if self.test_controller and self.test_controller.state_manager:
            self.test_controller.state_manager.add_observer(self)

            # Register direct progress callback
            if hasattr(self.test_controller, 'set_progress_callback'):
                self.test_controller.set_progress_callback(self.update_progress_direct)

    def setup_base_ui(self) -> Tuple[QVBoxLayout, QHBoxLayout]:
        """Set up base UI elements.

        Returns:
            Tuple of (main layout, header layout)
        """
        # Main layout
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)

        # Header with title
        header = QHBoxLayout()
        title = QLabel(self.page_title)
        title.setAlignment(Qt.AlignCenter)
        header.addWidget(title)
        layout.addLayout(header)

        return layout, header

    def create_preview_widget(self) -> PreviewWidget:
        """Create preview widget."""
        self.preview = PreviewWidget(self)
        return self.preview

    def create_preview_group(self) -> QGroupBox:
        """Create preview group with preview widget."""
        preview_group = QGroupBox("Preview")
        preview_layout = QVBoxLayout()
        self.preview = self.create_preview_widget()
        preview_layout.addWidget(self.preview)
        preview_group.setLayout(preview_layout)
        return preview_group

    def create_controls_group(self) -> QGroupBox:
        """Create controls group with start/stop/back buttons."""
        controls_group = QGroupBox("Controls")
        controls_layout = QHBoxLayout()

        # Back button
        back_button = QPushButton("Back to Menu")
        back_button.clicked.connect(self.show_menu)
        controls_layout.addWidget(back_button)

        # Start button
        self.start_button = QPushButton("Start Test")
        self.start_button.clicked.connect(self._handle_start_click)
        controls_layout.addWidget(self.start_button)

        # Stop button
        self.stop_button = QPushButton("Stop Test")
        self.stop_button.clicked.connect(self._handle_stop_click)
        self.stop_button.setEnabled(False)
        controls_layout.addWidget(self.stop_button)

        controls_group.setLayout(controls_layout)
        return controls_group

    def create_progress_bar(self) -> QProgressBar:
        """Create progress bar widget."""
        progress = QProgressBar()
        progress.setTextVisible(True)
        progress.setAlignment(Qt.AlignCenter)
        progress.setMinimumHeight(30)
        progress.setFixedHeight(30)
        progress.setFormat("%p%")  # Default format
        progress.setRange(0, 100)  # Ensure range is set correctly
        progress.setValue(0)       # Initialize to 0
        progress.hide()
        return progress

    def handle_error(self, message: str):
        """Display error message to user."""
        QMessageBox.critical(self, "Error", message)

    def show_menu(self):
        """Navigate back to main menu."""
        if self._test_running:
            reply = QMessageBox.question(
                self,
                "Test Running",
                "A test is currently running. Stop it and return to menu?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                asyncio.create_task(self.stop_test())
            else:
                return

        if self.main_window:
            self.main_window.navigate_to(0)
        else:
            logger.error("No main window found")

    def validate_config(self) -> bool:
        """Validate test configuration.

        Returns:
            bool: True if configuration is valid
        """
        raise NotImplementedError("Subclasses must implement validate_config")

    def create_test_config(self) -> Optional[TestConfig]:
        """Create test configuration.

        Returns:
            TestConfig or None if configuration is invalid
        """
        raise NotImplementedError("Subclasses must implement create_test_config")

    @asyncSlot()
    async def _handle_start_click(self):
        """Handle start button click by calling start_test asynchronously."""
        try:
            await self.start_test()
        except Exception as e:
            logger.error(f"Error in start test handler: {e}")
            self.handle_error(str(e))

    @asyncSlot()
    async def _handle_stop_click(self):
        """Handle stop button click by calling stop_test asynchronously."""
        try:
            await self.stop_test()
        except Exception as e:
            logger.error(f"Error in stop test handler: {e}")
            self.handle_error(str(e))

    async def start_test(self):
        """Start test execution."""
        if self._test_running:
            logger.warning("Test already running")
            return

        if not self.validate_config():
            return

        config = self.create_test_config()
        if not config:
            return

        try:
            # Reset progress tracking
            self._last_progress_value = 0

            # Update UI
            self._test_running = True
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            self.progress.setValue(0)  # Reset to 0
            self.progress.setFormat("0% - Starting test...")
            self.progress.show()
            self.progress.setVisible(True)
            self.progress.repaint()  # Force immediate repaint

            # Process pending events to ensure UI updates
            QApplication.processEvents()

            # Add a small delay to ensure the UI updates before test starts
            await asyncio.sleep(0.1)

            # Run test
            results = await self.test_controller.run_test(config)

            # Ensure progress bar shows 100% at completion
            self.progress.setValue(100)
            self.progress.setFormat("100% - Complete")
            self.progress.repaint()
            QApplication.processEvents()

            if results.get("success", False):
                QMessageBox.information(
                    self,
                    "Test Completed",
                    f"Test completed successfully.\n"
                    f"Processed {results.get('successful_images', 0)}/{results.get('total_images', 0)} images."
                )
            else:
                error_msg = results.get("error", "Unknown error")
                raise RuntimeError(f"Test failed: {error_msg}")

        except Exception as e:
            logger.error(f"Test execution error: {e}")
            self.handle_error(str(e))

        finally:
            # Reset UI and cleanup
            self._test_running = False
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            self.progress.hide()

    async def stop_test(self):
        """Stop test execution."""
        if not self._test_running:
            return

        try:
            await self.test_controller.stop_test()
            self._test_running = False
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            self.progress.hide()

            QMessageBox.information(
                self,
                "Test Stopped",
                "Test was stopped by user."
            )

        except Exception as e:
            logger.error(f"Failed to stop test: {e}")
            self.handle_error(str(e))

    def update_progress_direct(self, progress: float, current_image: str):
        """Direct callback for progress updates.

        This method is called directly from the test controller.

        Args:
            progress: Progress value (0.0-1.0)
            current_image: Current image being processed
        """
        try:
            # Calculate percentage
            progress_value = int(progress * 100)

            # Log the progress update
            logger.debug(f"Progress update received: {progress_value}% - {current_image}")

            # Validate progress value to prevent jumps
            if progress_value < self._last_progress_value and progress_value != 0:
                logger.warning(f"Progress decreased from {self._last_progress_value}% to {progress_value}%, ignoring")
                return

            # Update last progress value
            self._last_progress_value = progress_value

            # Emit the signal to update the UI in the main thread
            self.progress_updated.emit(progress_value, current_image)

        except Exception as e:
            logger.error(f"Error in progress callback: {e}")

    @pyqtSlot(int, str)
    def _update_progress_ui(self, progress_value: int, current_image: str):
        """Update the progress bar UI.

        This slot is connected to the progress_updated signal and runs in the UI thread.

        Args:
            progress_value: Progress value (0-100)
            current_image: Current image being processed
        """
        try:
            if not hasattr(self, 'progress'):
                logger.warning("Progress bar not found")
                return

            # Log the UI update
            logger.debug(f"Updating progress UI: {progress_value}% - {current_image}")

            # Set the value
            self.progress.setValue(progress_value)

            # Format text with current image if available
            if current_image:
                image_name = current_image.split('/')[-1] if '/' in current_image else current_image  # Get just the filename
                self.progress.setFormat(f"{progress_value}% - Processing {image_name}")
            else:
                self.progress.setFormat(f"{progress_value}%")

            # Force the progress bar to update visually
            self.progress.repaint()
            QApplication.processEvents()  # Process pending UI events

        except Exception as e:
            logger.error(f"Error updating progress bar UI: {e}")

    def on_state_changed(self, new_state: TestState, context: Optional[Dict] = None):
        """Called when test state changes.

        Overrides StateObserver.on_state_changed to update the progress bar.
        """
        # Call parent method to update internal state
        super().on_state_changed(new_state, context)

        # Log state change
        logger.debug(f"State changed to {new_state} with context: {context}")

        # We're now using the direct callback approach, but we'll keep this as a backup
        # Update progress bar if context contains progress information
        if context and 'progress' in context and hasattr(self, 'progress'):
            progress_value = int(context['progress'] * 100)
            current_image = context.get('current_image', '')

            # Log the state-based progress update
            logger.debug(f"State-based progress update: {progress_value}% - {current_image}")

            # Use the signal to update the UI in the main thread
            self.progress_updated.emit(progress_value, current_image)
