# src/ui/pages/base_page.py
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QLabel, QMessageBox, 
    QApplication, QSplitter, QScrollArea, QFrame
)
from PyQt5.QtCore import Qt, pyqtSlot
import logging
import asyncio
import qasync

from ..widgets.preview import PreviewWidget
from ..widgets.progress import EnhancedProgressBar
from ...core.controller import TestState

logger = logging.getLogger(__name__)

class BasePage(QWidget):
    """
    Base class for test pages with common functionality.
    
    This abstract class provides:
    - Common UI elements (preview, progress bar, buttons)
    - State change handling
    - Test execution infrastructure
    """
    # Title displayed at the top of the page
    PAGE_TITLE = "Test Page"
    
    def __init__(self, parent=None, controller=None):
        """Initialize base page.
        
        Args:
            parent: Parent widget (main window)
            controller: Test controller instance
        """
        super().__init__(parent)
        self.main_window = parent
        self.controller = controller
        self.preview = None  # Initialize to None, will be created in _setup_ui
        
        # Register for state updates
        if self.controller:
            self.controller.register_observer(self.on_state_change)
            
        self._test_running = False
        self._setup_ui()
        
    def _setup_ui(self):
        """Set up the base UI components."""
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Title
        title = QLabel(self.PAGE_TITLE)
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 18pt; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title)
        
        # Create preview first so it can be referenced in content creation
        self.preview = self._create_preview()
        
        # Create a splitter for content and preview
        self.splitter = QSplitter(Qt.Vertical)
        self.splitter.setChildrenCollapsible(False)  # Don't allow sections to collapse completely
        self.splitter.setHandleWidth(8)  # Make the handle even easier to grab
        
        # Create scrollable content area (controls)
        content_scroll = QScrollArea()
        content_scroll.setWidgetResizable(True)  # Important for dynamic resizing
        content_scroll.setFrameShape(QFrame.NoFrame)  # Remove border
        
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(5, 5, 5, 5)  # Smaller margins
        
        # Get content from subclass
        content = self._create_content()
        content_layout.addLayout(content)
        
        # Set content widget as the scroll area's widget
        content_scroll.setWidget(content_widget)
        
        # Add to splitter
        self.splitter.addWidget(content_scroll)
        self.splitter.addWidget(self.preview)
        
        # Set initial sizes - give more space to preview
        self.splitter.setSizes([2, 3])  # Proportional sizes
        
        # Add splitter to main layout
        layout.addWidget(self.splitter, 1)
        
        # Controls at bottom
        controls = self._create_controls()
        layout.addLayout(controls)
        
        # Progress bar
        self.progress = self._create_progress_bar()
        self.progress.setVisible(False)
        layout.addWidget(self.progress)
        
        # Let the user save splitter positions
        self.splitter.splitterMoved.connect(self._splitter_moved)
        
    def _create_content(self):
        """Create the main content area.
        
        Override in subclasses to add specific controls.
        
        Returns:
            QLayout: Layout containing the content
        """
        # Default implementation returns an empty layout
        return QVBoxLayout()
        
    def _create_preview(self):
        """Create the preview widget.
        
        Returns:
            PreviewWidget: Preview widget instance
        """
        preview = PreviewWidget(self)
        # Set transform pipeline if available
        if self.controller and hasattr(self.controller, '_transform_pipeline'):
            preview.set_transform_pipeline(self.controller._transform_pipeline)
        return preview
        
    def _create_controls(self):
        """Create the control buttons.
        
        Returns:
            QLayout: Layout containing the controls
        """
        controls = QHBoxLayout()
        
        # Spacer to push buttons to the right
        controls.addStretch()
        
        # Back button
        self.back_button = QPushButton("Back")
        self.back_button.clicked.connect(self.on_back)
        controls.addWidget(self.back_button)
        
        # Start button
        self.start_button = QPushButton("Start")
        self.start_button.clicked.connect(self.on_start)
        controls.addWidget(self.start_button)
        
        # Stop button
        self.stop_button = QPushButton("Stop")
        self.stop_button.clicked.connect(self.on_stop)
        self.stop_button.setEnabled(False)
        controls.addWidget(self.stop_button)
        
        return controls
        
    def _create_progress_bar(self):
        """Create the progress bar.
        
        Returns:
            EnhancedProgressBar: Progress bar instance
        """
        return EnhancedProgressBar(self)
        
    @pyqtSlot()
    def on_back(self):
        """Handle back button click."""
        if self._test_running:
            # Confirm before navigating away
            reply = QMessageBox.question(
                self, "Test Running",
                "A test is running. Stop it and go back?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.No:
                return
                
            # Stop the test
            asyncio.create_task(self.controller.stop_test())
            
        # Navigate back to main menu
        if self.main_window:
            self.main_window.show_main_menu()
            
    @pyqtSlot()
    def on_start(self):
        """Handle start button click."""
        # Start testing asynchronously
        asyncio.create_task(self._run_test())
            
    @pyqtSlot()
    def on_stop(self):
        """Handle stop button click."""
        if not self._test_running:
            return
            
        # Stop the test
        asyncio.create_task(self.controller.stop_test())
        
    def on_state_change(self, state, context):
        """Handle state changes from the controller.
        
        Args:
            state: Current test state
            context: State context dictionary
        """
        try:
            if state == TestState.RUNNING:
                # Update progress
                progress = context.get('progress', 0.0)
                status = context.get('status', '')
                self.progress.update_progress(progress, status)
                
                # Update UI state
                self._test_running = True
                self.start_button.setEnabled(False)
                self.stop_button.setEnabled(True)
                self.progress.setVisible(True)
                
            elif state == TestState.COMPLETED:
                # Test finished successfully
                self.progress.update_progress(1.0, "Test completed")
                self._test_running = False
                self.start_button.setEnabled(True)
                self.stop_button.setEnabled(False)
                
            elif state == TestState.ERROR:
                # Test encountered an error
                error = context.get('error', 'Unknown error')
                self.progress.update_progress(
                    context.get('progress', 0.0), f"Error: {error}")
                self._test_running = False
                self.start_button.setEnabled(True)
                self.stop_button.setEnabled(False)
                
                # Show error message
                QMessageBox.critical(
                    self, "Test Error", f"Test failed: {error}")
                
            elif state == TestState.STOPPED:
                # Test was stopped
                self.progress.update_progress(
                    context.get('progress', 0.0), "Test stopped")
                self._test_running = False
                self.start_button.setEnabled(True)
                self.stop_button.setEnabled(False)
                
        except Exception as e:
            logger.error(f"Error handling state change: {e}")
            
    async def _run_test(self):
        """Run a test with current configuration."""
        if self._test_running:
            return
            
        # Get test configuration
        config = self.get_test_config()
        if not config:
            return
            
        # Update UI state
        self._test_running = True
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.progress.setValue(0)
        self.progress.setVisible(True)
        
        try:
            # Run the test
            results = await self.controller.run_test(config)
            
            # Show results if not already shown by state handler
            if results.get('success', False) and not self._test_running:
                QMessageBox.information(
                    self, "Test Complete",
                    f"Test completed successfully.\n"
                    f"{results.get('successful_images', 0)}/{results.get('total_images', 0)} images processed."
                )
                
        except Exception as e:
            logger.error(f"Error running test: {e}")
            QMessageBox.critical(
                self, "Test Error", f"Unexpected error: {str(e)}")
                
            # Update UI state
            self._test_running = False
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            
    def get_test_config(self):
        """Get test configuration based on current settings.
        
        Override in subclasses to provide specific configuration.
        
        Returns:
            TestConfig: Test configuration or None if invalid
        """
        # Base implementation returns None
        return None
        
    def cleanup(self):
        """Clean up resources when page is closed."""
        if self._test_running:
            asyncio.create_task(self.controller.stop_test())
            
        if self.controller:
            self.controller.unregister_observer(self.on_state_change)

    def _splitter_moved(self, pos, index):
        """Handle splitter movement to remember positions."""
        # In a real app, you might save this to settings
        # For now, we'll just log it
        logger.debug(f"Splitter position changed: {self.splitter.sizes()}")