# src/ui/main_window.py
from PyQt5.QtWidgets import QMainWindow, QStackedWidget
from PyQt5.QtCore import Qt
import logging
import asyncio

from .pages.menu_page import MainMenuPage
from .pages.quick_page import QuickTestPage
from .pages.custom_page import CustomTestPage
from ..utils.style import apply_stylesheet

logger = logging.getLogger(__name__)

class MainWindow(QMainWindow):
    """
    Main application window.
    
    This window contains:
    - A stacked widget for page navigation
    - Methods for switching between pages
    - Styling for the entire application
    """
    
    def __init__(self, controller=None):
        """Initialize main window.
        
        Args:
            controller: Test controller instance
        """
        super().__init__()
        self.controller = controller
        
        self.setWindowTitle("E-ink Barcode Testing")
        self.setMinimumSize(900, 700)
        
        self._setup_ui()
        apply_stylesheet(self)
        
    def _setup_ui(self):
        """Set up the UI components."""
        # Central stacked widget
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)
        
        # Create pages
        self.menu_page = MainMenuPage(self)
        self.quick_test_page = QuickTestPage(self, self.controller)
        self.custom_test_page = CustomTestPage(self, self.controller)
        
        # Add pages to stack
        self.stacked_widget.addWidget(self.menu_page)
        self.stacked_widget.addWidget(self.quick_test_page)
        self.stacked_widget.addWidget(self.custom_test_page)
        
        # Show menu page initially
        self.show_main_menu()
        
    def show_main_menu(self):
        """Show the main menu page."""
        self.stacked_widget.setCurrentWidget(self.menu_page)
        
    def show_quick_test(self):
        """Show the quick test page."""
        self.stacked_widget.setCurrentWidget(self.quick_test_page)
        
    def show_custom_test(self):
        """Show the custom test page."""
        self.stacked_widget.setCurrentWidget(self.custom_test_page)
        
    def closeEvent(self, event):
        """Handle window close event."""
        # Clean up pages
        self.quick_test_page.cleanup()
        self.custom_test_page.cleanup()
        
        # Clean up controller
        asyncio.create_task(self.controller.cleanup())
        
        event.accept()