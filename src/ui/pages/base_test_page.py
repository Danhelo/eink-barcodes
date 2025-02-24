"""
Base test page implementation with common functionality.
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QProgressBar, QGroupBox, QMessageBox
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont
import logging
from typing import Optional, Dict, Any

from ..widgets.preview import PreviewWidget
from ...core.state_manager import StateManager, StateObserver, TestState, TestContext
from ...core.test_controller import TestController, TestConfig
from ...core.display_manager import DisplayManager, DisplayConfig

logger = logging.getLogger(__name__)

class BaseTestPage(QWidget, StateObserver):
    """Base class for test pages with common functionality."""

    test_started = pyqtSignal(TestConfig)
    test_stopped = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = self.window()
        self.state_manager = StateManager()
        self.display_manager = None
        self.test_controller = None
        self.current_config = None

        # Register as observer
        self.state_manager.register_observer(self)

        # Initialize managers
        self.initialize_managers()

    def initialize_managers(self):
        """Initialize display and test controllers."""
        try:
            # Create display manager
            self.display_manager = DisplayManager(
                DisplayConfig(),
                self.state_manager
            )

            # Create test controller
            self.test_controller = TestController(
                self.state_manager,
                self.display_manager
            )

        except Exception as e:
            logger.error(f"Failed to initialize managers: {e}")
            QMessageBox.critical(
                self,
                "Initialization Error",
                f"Failed to initialize test system: {e}"
            )

    def setup_base_ui(self) -> tuple[QVBoxLayout, QLabel]:
        """Setup common UI elements.

        Returns:
            tuple: (main layout, title label)
        """
        layout = QVBoxLayout()
        layout.setSpacing(25)
        layout.setContentsMargins(30, 30, 30, 30)

        # Title
        title = QLabel(self.page_title)
        title.setFont(QFont("Arial", 32, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #FFFFFF; margin-bottom: 20px;")
        layout.addWidget(title)

        return layout, title

    def create_preview_group(self) -> QGroupBox:
        """Create preview group box."""
        preview_group = QGroupBox("Preview")
        preview_layout = QVBoxLayout()

        # Preview widget
        self.preview = PreviewWidget()
        preview_layout.addWidget(self.preview)

        preview_group.setLayout(preview_layout)
        return preview_group

    def create_controls_group(self) -> QGroupBox:
        """Create test controls group."""
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
        return controls_group

    def create_progress_bar(self) -> QProgressBar:
        """Create progress bar."""
        progress = QProgressBar()
        progress.setTextVisible(True)
        progress.setAlignment(Qt.AlignCenter)
        return progress

    def start_test(self):
        """Start test execution."""
        try:
            if not self.validate_config():
                return

            config = self.create_test_config()
            if not config:
                return

            # Initialize test
            self.test_controller.initialize_test(config)

            # Update UI state
            self.update_ui_state(TestState.RUNNING)

            # Start test
            self.test_started.emit(config)
            self.test_controller.execute_test()

        except Exception as e:
            logger.error(f"Failed to start test: {e}")
            self.handle_error(str(e))

    def stop_test(self):
        """Stop current test."""
        try:
            if self.test_controller:
                self.test_controller.stop_test()
                self.test_stopped.emit()
            self.update_ui_state(TestState.STOPPED)
        except Exception as e:
            logger.error(f"Failed to stop test: {e}")
            self.handle_error(str(e))

    def validate_config(self) -> bool:
        """Validate test configuration.

        Override in subclasses.
        """
        return True

    def create_test_config(self) -> Optional[TestConfig]:
        """Create test configuration.

        Override in subclasses.
        """
        return None

    def update_ui_state(self, state: TestState):
        """Update UI elements based on state."""
        self.start_button.setEnabled(state in (TestState.NOT_STARTED, TestState.COMPLETED, TestState.FAILED))
        self.stop_button.setEnabled(state == TestState.RUNNING)

    def handle_error(self, error_msg: str):
        """Handle test errors."""
        logger.error(f"Test error: {error_msg}")
        self.update_ui_state(TestState.FAILED)
        QMessageBox.critical(self, "Test Error", f"Error during test: {error_msg}")

    def on_state_change(self, state: TestState, context: TestContext):
        """Handle state changes."""
        self.update_ui_state(state)

        # Update progress if available
        if hasattr(self, 'progress') and context:
            self.progress.setValue(int(context.progress * 100))

        # Show completion message
        if state == TestState.COMPLETED:
            QMessageBox.information(self, "Test Complete", "Test sequence completed successfully")
        elif state == TestState.STOPPED:
            QMessageBox.information(self, "Test Stopped", "Test sequence was stopped by user")

    def cleanup(self):
        """Clean up resources."""
        if self.test_controller:
            self.test_controller.cleanup()
        if self.state_manager:
            self.state_manager.remove_observer(self)

    def closeEvent(self, event):
        """Handle widget close event."""
        self.cleanup()
        super().closeEvent(event)
