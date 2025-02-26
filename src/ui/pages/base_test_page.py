"""
Base test page implementation with improved progress tracking.
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QApplication,
    QGroupBox, QMessageBox
)
from PyQt5.QtCore import Qt, pyqtSlot, pyqtSignal, QTimer
import logging
from typing import Optional, Tuple, Dict, Any, Callable
import asyncio
from qasync import asyncSlot
import time

from ..widgets.preview import PreviewWidget
from ..widgets.enhanced_progress import EnhancedProgressBar
from ...core.test_controller import TestController
from ...core.test_config import TestConfig
from ...core.state_manager import StateObserver, TestState
from ...core.progress_manager import ProgressManager

logger = logging.getLogger(__name__)

class BaseTestPage(QWidget, StateObserver):
    """Base class for test pages with improved progress tracking."""

    page_title = "Test Page"

    # Define signals for progress updates
    progress_started = pyqtSignal()
    progress_updated = pyqtSignal(float, str)
    progress_finished = pyqtSignal()

    def __init__(self, parent=None, test_controller: Optional[TestController] = None, 
                 progress_manager: Optional[ProgressManager] = None):
        """Initialize BaseTestPage.

        Args:
            parent: Parent widget (should be MainWindow)
            test_controller: Test controller instance
            progress_manager: Optional progress manager to coordinate updates
        """
        QWidget.__init__(self, parent)
        StateObserver.__init__(self)
        self.test_controller = test_controller
        self.main_window = parent
        self._test_running = False
        self._progress_update_timer = None
        
        # Create or use provided progress manager
        self.progress_manager = progress_manager or ProgressManager()
        
        # Connect the progress signals
        self.progress_started.connect(self._on_progress_started)
        self.progress_updated.connect(self._on_progress_updated)
        self.progress_finished.connect(self._on_progress_finished)

        # Register as observer if test_controller is available
        if self.test_controller and hasattr(self.test_controller, 'state_manager'):
            self.test_controller.state_manager.add_observer(self)

            # Register direct progress callback with test controller
            if hasattr(self.test_controller, 'set_progress_callback'):
                # Use progress manager as intermediary
                self.progress_manager.register_observer(self.update_progress_direct)
                self.test_controller.set_progress_callback(self.progress_manager.update_progress)
                logger.debug("Progress callback registered with test controller")

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
        title.setObjectName("title")
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
        self.back_button = QPushButton("Back to Menu")
        self.back_button.clicked.connect(self.show_menu)
        controls_layout.addWidget(self.back_button)

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

    def create_progress_bar(self) -> EnhancedProgressBar:
        """Create enhanced progress bar widget."""
        progress = EnhancedProgressBar(self)
        progress.hide()  # Initially hidden
        return progress

    def add_progress_bar_to_layout(self, layout: QVBoxLayout):
        """Add progress bar to layout with proper setup.
        
        Args:
            layout: Layout to add progress bar to
        """
        if not hasattr(self, 'progress'):
            self.progress = self.create_progress_bar()
        
        # Add to layout
        layout.addWidget(self.progress)

    def handle_error(self, message: str):
        """Display error message to user."""
        logger.error(message)
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

        # Create test ID
        test_id = f"test_{int(time.time())}"
        
        # Start progress tracking via progress manager
        self.progress_manager.start_progress(test_id)
        
        # Emit progress started signal to update UI
        logger.debug("Emitting progress_started signal")
        self.progress_started.emit()

        try:
            # Update UI state for test execution
            logger.info("Starting test execution")
            self._test_running = True
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            
            # Update state in state manager
            if hasattr(self.test_controller, 'state_manager'):
                self.test_controller.state_manager.transition_to(
                    TestState.RUNNING,
                    {"test_id": test_id, "progress": 0.0, "current_image": "", "error": None}
                )

            # Run test
            results = await self.test_controller.run_test(config)

            if results.get("success", False):
                # Mark progress as complete
                self.progress_manager.complete_progress("Test completed successfully")
                
                QMessageBox.information(
                    self,
                    "Test Completed",
                    f"Test completed successfully.\n"
                    f"Processed {results.get('successful_images', 0)}/{results.get('total_images', 0)} images."
                )
            else:
                error_msg = results.get("error", "Unknown error")
                
                # Mark progress as aborted
                self.progress_manager.abort_progress(f"Error: {error_msg}")
                
                raise RuntimeError(f"Test failed: {error_msg}")

        except Exception as e:
            logger.error(f"Test execution error: {e}")
            self.handle_error(str(e))
            
            # Update state in state manager
            if hasattr(self.test_controller, 'state_manager'):
                self.test_controller.state_manager.transition_to(
                    TestState.ERROR,
                    {"error": str(e), "test_id": test_id}
                )
                
            # Ensure progress is marked as aborted
            if self.progress_manager.is_active():
                self.progress_manager.abort_progress(f"Error: {str(e)}")

        finally:
            # Reset UI state
            self._test_running = False
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            
            # Emit progress finished signal
            logger.debug("Emitting progress_finished signal")
            self.progress_finished.emit()
            
            logger.info("Test execution completed")

    async def stop_test(self):
        """Stop test execution."""
        if not self._test_running:
            return

        try:
            # Mark progress as stopped in progress manager
            if self.progress_manager.is_active():
                self.progress_manager.abort_progress("Test stopped by user")
            
            # Stop the test in test controller
            await self.test_controller.stop_test()
            
            # Update UI state
            self._test_running = False
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            
            # Emit progress finished signal
            self.progress_finished.emit()

            QMessageBox.information(
                self,
                "Test Stopped",
                "Test was stopped by user."
            )

        except Exception as e:
            logger.error(f"Failed to stop test: {e}")
            self.handle_error(str(e))

    def update_progress_direct(self, progress: float, message: str):
        """Direct callback for progress updates from test controller or progress manager.

        Args:
            progress: Progress value (0.0-1.0)
            message: Current status message
        """
        try:
            # Emit signal to update progress in the UI thread
            self.progress_updated.emit(progress, message)
        except Exception as e:
            logger.error(f"Error in progress callback: {e}")

    def _on_progress_started(self):
        """Handle progress start signal."""
        if hasattr(self, 'progress'):
            # Reset and show progress bar
            self.progress.reset()
            self.progress.setVisibleWhenZero(True)
            self.progress.show()
        else:
            logger.warning("Progress bar not found when handling progress start")

    def _on_progress_updated(self, value: float, message: str):
        """Handle progress update signal in the UI thread.

        Args:
            value: Progress value (0.0-1.0)
            message: Current status message
        """
        if hasattr(self, 'progress'):
            # Update progress bar and ensure UI updates
            updated = self.progress.updateProgress(value, message)
            
            # CRITICAL FIX: Always process events regardless of whether the update was throttled
            # This ensures the UI repaints even when the progress bar is throttling updates
            QApplication.processEvents()
            
            # Log progress updates to help with debugging
            logger.debug(f"Progress updated: {value:.2f} - {message} (UI updated: {updated})")
        else:
            logger.warning("Progress bar not found when handling progress update")

    def _on_progress_finished(self):
        """Handle progress finished signal."""
        if hasattr(self, 'progress'):
            # Hide progress bar
            self.progress.setVisibleWhenZero(False)
            self.progress.hide()

    def _start_progress_timer(self):
        """Start timer for periodic UI updates during progress."""
        # We no longer need a timer for progress updates
        # This method remains for backward compatibility
        pass

    def _stop_progress_timer(self):
        """Stop progress update timer if running."""
        # We no longer need a timer for progress updates
        # This method remains for backward compatibility
        pass

    def _refresh_progress_ui(self):
        """Periodic refresh of progress UI from timer."""
        # This method is now a no-op as we don't need timer-based polling
        # Progress updates come directly through signals from progress_manager
        pass

    def on_state_changed(self, new_state: TestState, context: Optional[Dict] = None):
        """Called when test state changes.

        Args:
            new_state: New test state
            context: Optional context dict with state information
        """
        # Call parent method
        super().on_state_changed(new_state, context)
        
        # Only update progress from state manager in specific cases to avoid conflicts
        # with direct progress updates from TestController
        if context and hasattr(self, 'progress'):
            progress_value = context.get('progress', 0.0)
            current_image = context.get('current_image', '')
            
            # Only handle state transitions that aren't covered by regular progress updates
            if new_state == TestState.COMPLETED:
                # Force progress to 100% on completion
                self.progress_updated.emit(1.0, "Complete")
                logger.debug("State manager enforcing 100% on completion")
            elif new_state == TestState.ERROR:
                # Show error in progress bar
                error_msg = context.get('error', 'Unknown error')
                self.progress_updated.emit(progress_value, f"Error: {error_msg}")
                logger.debug(f"State manager showing error: {error_msg}")
            # Don't update progress for RUNNING state - let progress_manager handle it

    def cleanup(self):
        """Clean up resources."""
        # Stop any running timer
        self._stop_progress_timer()
        
        # Abort any in-progress operations
        if self.progress_manager and self.progress_manager.is_active():
            self.progress_manager.abort_progress("Page cleanup")
        
        # Remove observer from state manager
        if self.test_controller and hasattr(self.test_controller, 'state_manager'):
            self.test_controller.state_manager.remove_observer(self)
            
        # Remove observer from progress manager
        if hasattr(self, 'progress_manager'):
            self.progress_manager.unregister_observer(self.update_progress_direct)