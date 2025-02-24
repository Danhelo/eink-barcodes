"""
Base test page implementation.
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QProgressBar,
    QGroupBox, QMessageBox
)
from PyQt5.QtCore import Qt
import logging
from typing import Optional, Tuple
import asyncio
from qasync import asyncSlot

from ..widgets.preview import PreviewWidget
from ...core.test_controller import TestController, TestConfig

logger = logging.getLogger(__name__)

class BaseTestPage(QWidget):
    """Base class for test pages."""

    page_title = "Test Page"

    def __init__(self, parent=None, test_controller: Optional[TestController] = None):
        """Initialize BaseTestPage.

        Args:
            parent: Parent widget (should be MainWindow)
            test_controller: Test controller instance
        """
        super().__init__(parent)
        self.test_controller = test_controller
        self.main_window = parent
        self._test_running = False

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
            # Update UI
            self._test_running = True
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            self.progress.show()

            # Initialize test
            if not await self.test_controller.initialize_test(config):
                raise RuntimeError("Failed to initialize test")

            # Execute test
            success = await self.test_controller.execute_test()
            if not success:
                raise RuntimeError("Test execution failed")

        except Exception as e:
            logger.error(f"Test execution error: {e}")
            self.handle_error(str(e))

        finally:
            # Reset UI and cleanup
            self._test_running = False
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            await self.test_controller.cleanup()
            self.progress.hide()

    async def stop_test(self):
        """Stop test execution."""
        if not self._test_running:
            return

        try:
            await self.test_controller.stop_test()  # This sets the stop flag
            await self.test_controller.cleanup()    # Clean up resources
        except Exception as e:
            logger.error(f"Failed to stop test: {e}")
            self.handle_error(str(e))
        finally:
            self._test_running = False
