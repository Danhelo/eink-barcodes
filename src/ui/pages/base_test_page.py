from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QProgressBar, QApplication,
    QGroupBox, QMessageBox
)
from PyQt5.QtCore import Qt, pyqtSlot, pyqtSignal, QTimer
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
    """Base class for test pages with integrated progress bar functionality.

    This class provides:
    - Standard UI layout for test pages
    - Progress bar with real-time updates
    - Integration with test controller and state manager
    - Common test execution flow

    Subclasses should implement:
    - validate_config(): Validate test configuration
    - create_test_config(): Create test configuration
    """

    page_title = "Test Page"

    # Define signals for progress updates
    progress_started = pyqtSignal()
    progress_finished = pyqtSignal()
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

        # Create progress bar as an instance attribute
        self.progress = self._create_progress_bar()
        logger.debug(f"Created progress bar with ID: {id(self.progress)}")
        
        # Progress update refresh timer
        self.refresh_timer = QTimer(self)
        self.refresh_timer.setInterval(100)  # 100ms refresh rate
        self.refresh_timer.timeout.connect(self._force_ui_refresh)

        # Connect progress signals
        self.progress_updated.connect(self._update_progress_ui)
        self.progress_started.connect(self._on_progress_started)
        self.progress_finished.connect(self._on_progress_finished)

        # Register as observer if test_controller is available
        if self.test_controller and self.test_controller.state_manager:
            self.test_controller.state_manager.add_observer(self)

            # Register direct progress callback
            if hasattr(self.test_controller, 'set_progress_callback'):
                self.test_controller.set_progress_callback(self.update_progress_direct)

    def _force_ui_refresh(self):
        """Force UI to refresh when timer fires."""
        if hasattr(self, 'progress') and self.progress.isVisible():
            # Log current progress value
            logger.debug(f"Timer refresh: progress bar value is {self.progress.value()}%")
            
            
            # Force a repaint of the progress bar
            self.progress.repaint()
            
            # Force top-level update
            top_level = self
            while top_level.parent():
                top_level = top_level.parent()
            top_level.repaint()
            
            # Process all pending events
            QApplication.processEvents()

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
        """Create preview widget.

        Returns:
            A new PreviewWidget instance
        """
        self.preview = PreviewWidget(self)
        return self.preview

    def create_preview_group(self) -> QGroupBox:
        """Create preview group with preview widget.

        Returns:
            QGroupBox containing a preview widget
        """
        preview_group = QGroupBox("Preview")
        preview_layout = QVBoxLayout()
        self.preview = self.create_preview_widget()
        preview_layout.addWidget(self.preview)
        preview_group.setLayout(preview_layout)
        return preview_group

    def create_controls_group(self) -> QGroupBox:
        """Create controls group with start/stop/back buttons.

        Returns:
            QGroupBox containing control buttons
        """
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

    def add_progress_bar_to_layout(self, layout: QVBoxLayout):
        """Add the progress bar to the given layout.

        This is a convenience method to ensure the progress bar is added correctly.
        """
        if layout and self.progress:
            logger.debug(f"Adding progress bar (ID: {id(self.progress)}) to layout")
            layout.addWidget(self.progress)
            return True
        return False

    def handle_error(self, message: str):
        """Display error message to user.

        Args:
            message: Error message to display
        """
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
        """Start test execution with progress tracking."""
        if self._test_running:
            logger.warning("Test already running")
            return

        if not self.validate_config():
            return

        config = self.create_test_config()
        if not config:
            return

        try:
            # Signal test start
            self.progress_started.emit()
            self._test_running = True
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            
            # Ensure progress bar is initialized properly
            self.progress.setValue(0)  # Reset to 0
            self.progress.setFormat("0% - Starting test...")
            self.progress.show()
            self.progress.setVisible(True)
            
            # Start the refresh timer
            logger.debug("Starting UI refresh timer")
            self.refresh_timer.start()
            
            # Force immediate repaint
            self.progress.repaint()
            QApplication.processEvents()

            # Add a delay to ensure the UI updates before test starts
            await asyncio.sleep(0.3)

            # Run test
            logger.info("Starting test execution")
            results = await self.test_controller.run_test(config)
            logger.info("Test execution completed")

            # Process pending events before final update
            # Signal test completion
            self.progress_finished.emit()

            QApplication.processEvents()
            await asyncio.sleep(0.1)

            # Ensure progress bar shows 100% at completion
            self.progress.setValue(100)
            self.progress.setFormat("100% - Complete")
            self.progress.repaint()
            QApplication.processEvents()
            
            # Allow timer to make final updates
            await asyncio.sleep(0.5)

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
            logger.error(f"Test execution error: {e}", exc_info=True)
            self.handle_error(str(e))

        finally:
            # Stop the refresh timer
            logger.debug("Stopping UI refresh timer")
            self.refresh_timer.stop()
            
            # Reset UI and cleanup
            self._test_running = False
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            self.progress.hide()

    async def stop_test(self):
        """Stop test execution and reset UI."""
        if not self._test_running:
            return

        try:
            # Stop refresh timer
            self.refresh_timer.stop()
            
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
        It safely updates the progress bar via signal/slot mechanism
        to ensure thread safety.

        Args:
            progress: Progress value (0.0-1.0)
            current_image: Current image being processed
        """
        try:
            # Calculate percentage
            progress_value = int(progress * 100)

            # Log the progress update with more information
            logger.debug(f"Progress update received: {progress_value}% - {current_image} (last: {self._last_progress_value}%)")

            # Validate progress value to prevent jumps
            if progress_value < self._last_progress_value and progress_value != 0:
                logger.warning(f"Progress decreased from {self._last_progress_value}% to {progress_value}%, ignoring")
                return

            # Special handling for values very close to previous
            if progress_value == self._last_progress_value and progress_value != 0 and progress_value != 100:
                logger.debug(f"Progress unchanged at {progress_value}%, still emitting signal")

            # Update last progress value
            self._last_progress_value = progress_value

            # Emit the signal to update the UI in the main thread
            logger.debug(f"Emitting progress_updated signal with {progress_value}% - {current_image}")
            self.progress_updated.emit(progress_value, current_image)

        except Exception as e:
            logger.error(f"Error in progress callback: {e}", exc_info=True)

    @pyqtSlot(int, str)
    def _update_progress_ui(self, progress_value: int, current_image: str):
        """Update the progress bar UI.

        This slot is connected to the progress_updated signal and runs in the UI thread.
        It safely updates the progress bar with the current progress value and image.

        Args:
            progress_value: Progress value (0-100)
            current_image: Current image being processed
        """
        try:
            if not hasattr(self, 'progress'):
                logger.warning("Progress bar not found")
                return

            # Log the UI update with more detail
            logger.debug(f"Current progress bar value: {self.progress.value()}, updating to: {progress_value}%")

            # Store current value to check if it actually changes
            old_value = self.progress.value()

            # Make sure progress bar is visible
            if not self.progress.isVisible():
                logger.warning("Progress bar was hidden! Making it visible.")
                self.progress.show()
                self.progress.setVisible(True)

            # Set the value
            self.progress.setValue(progress_value)

            # Format text with current image if available
            if current_image:
                image_name = current_image.split('/')[-1] if '/' in current_image else current_image  # Get just the filename
                self.progress.setFormat(f"{progress_value}% - Processing {image_name}")
            else:
                self.progress.setFormat(f"{progress_value}%")

            # Force stronger UI updates
            self.progress.repaint()
            
            # Force update on parent widgets too
            parent = self.progress.parent()
            if parent:
                parent.repaint()
            
            # Force update on the entire window
            top_level = self
            while top_level.parent():
                top_level = top_level.parent()
            top_level.repaint()
            
            # Process all pending UI events
            QApplication.processEvents()
            
            # Log if value actually changed
            if self.progress.value() != old_value:
                logger.debug(f"Progress bar value changed: {old_value} -> {self.progress.value()}")
            else:
                logger.warning(f"Progress bar value NOT changed: still {old_value} after update attempt")

        except Exception as e:
            logger.error(f"Error updating progress bar UI: {e}", exc_info=True)

    def _create_progress_bar(self) -> QProgressBar:
        """Create standardized progress bar widget with enhanced styling."""
        # Create the progress bar as an instance attribute
        progress = QProgressBar(self)  # Set parent to ensure proper ownership
        progress.setObjectName("testProgressBar")  # Give it a unique name
        progress.setTextVisible(True)
        progress.setAlignment(Qt.AlignCenter)

        # Increase size for better visibility
        progress.setMinimumHeight(50)
        progress.setFixedHeight(50)

        # Set a distinctive style to make it more visible
        progress.setStyleSheet("""
            QProgressBar {
                border: 2px solid grey;
                border-radius: 5px;
                text-align: center;
                background-color: #f0f0f0;
                font-weight: bold;
                font-size: 18px;
            }

            QProgressBar::chunk {
                background-color: #4CAF50;
                width: 20px;
                margin: 0.5px;
            }
        """)

        progress.setFormat("%p%")  # Default format
        progress.setRange(0, 100)  # Ensure range is set correctly
        progress.setValue(0)       # Initialize to 0
        progress.hide()            # Hidden by default until test starts

        return self.progress

    def _on_progress_started(self):
        """Handle progress start."""
        logger.debug("Progress started signal received")

        # Reset progress tracking
        self._last_progress_value = 0

        # Reset and show progress bar
        self.progress.setValue(0)
        self.progress.setFormat("0% - Starting test...")
        self.progress.show()
        self.progress.setVisible(True)

        # Start the refresh timer
        logger.debug("Starting UI refresh timer")
        self.refresh_timer.start()

        # Force immediate repaint
        self.progress.repaint()
        QApplication.processEvents()

    def _on_progress_finished(self):
        """Handle progress completion."""
        logger.debug("Progress finished signal received")

        # Stop the refresh timer
        logger.debug("Stopping UI refresh timer")
        self.refresh_timer.stop()

        # Ensure 100% is shown
        self.progress.setValue(100)
        self.progress.setFormat("100% - Complete")

    def on_state_changed(self, new_state: TestState, context: Optional[Dict] = None):
        """Called when test state changes.

        Overrides StateObserver.on_state_changed to update the progress bar.
        This provides a backup mechanism for progress updates in case the
        direct callback approach fails.

        Args:
            new_state: New test state
            context: Optional context with additional information
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
