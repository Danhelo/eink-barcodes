from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QProgressBar, QGroupBox, QMessageBox
)
from PyQt5.QtCore import Qt, QTimer
from typing import Optional, Tuple
from PIL import Image
import asyncio
import qasync

from src.core.state_manager import StateObserver, TestState
from src.core.test_controller import TestController, TestConfig
from ..widgets.preview import PreviewWidget

class BaseTestPage(QWidget):
    """Base class for test pages"""

    page_title = "Test Page"

    def __init__(self, parent=None, test_controller: Optional[TestController] = None):
        super().__init__(parent)
        self.test_controller = test_controller
        self.preview: Optional[PreviewWidget] = None
        self.progress: Optional[QProgressBar] = None
        self._test_running = False

    def setup_base_ui(self) -> Tuple[QVBoxLayout, QLabel]:
        """Set up the basic UI elements"""
        # Main layout
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignTop)

        # Title
        title = QLabel(self.page_title)
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 24px; font-weight: bold; margin: 20px;")
        layout.addWidget(title)

        return layout, title

    def create_preview_widget(self) -> PreviewWidget:
        """Create preview widget"""
        self.preview = PreviewWidget()
        return self.preview

    def create_preview_group(self) -> QGroupBox:
        """Create preview group with widget"""
        group = QGroupBox("Preview")
        layout = QVBoxLayout()
        self.preview = self.create_preview_widget()
        layout.addWidget(self.preview)
        group.setLayout(layout)
        return group

    def create_controls_group(self) -> QGroupBox:
        """Create control buttons group"""
        group = QGroupBox("Controls")
        layout = QHBoxLayout()

        # Back button
        back_btn = QPushButton("Back to Menu")
        back_btn.clicked.connect(self.show_menu)
        layout.addWidget(back_btn)

        # Start button
        start_btn = QPushButton("Start Test")
        start_btn.clicked.connect(self._handle_start_click)
        layout.addWidget(start_btn)

        group.setLayout(layout)
        return group

    def create_progress_bar(self) -> QProgressBar:
        """Create progress bar"""
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        return self.progress

    def show_menu(self):
        """Return to main menu"""
        if hasattr(self.parent(), 'show_menu'):
            self.parent().show_menu()

    def _handle_start_click(self):
        """Handle start button click by scheduling async test"""
        if self._test_running:
            return

        self._test_running = True
        asyncio.create_task(self._run_test())

    async def _run_test(self):
        """Run test asynchronously"""
        try:
            await self.start_test()
        finally:
            self._test_running = False

    async def start_test(self):
        """Start test execution"""
        if not self.test_controller:
            self.handle_error("Test controller not initialized")
            return

        if not self.validate_config():
            return

        config = self.create_test_config()
        if not config:
            return

        try:
            await self.test_controller.initialize_test(config)
            await self.test_controller.execute_test()
        except Exception as e:
            self.handle_error(f"Test execution failed: {e}")

    def validate_config(self) -> bool:
        """Validate test configuration"""
        raise NotImplementedError("Subclasses must implement validate_config")

    def create_test_config(self) -> Optional[TestConfig]:
        """Create test configuration"""
        raise NotImplementedError("Subclasses must implement create_test_config")

    def handle_error(self, message: str):
        """Show error message to user"""
        QMessageBox.critical(self, "Error", message)

    def update_progress(self, value: int):
        """Update progress bar value"""
        if self.progress:
            self.progress.setValue(value)
