# src/ui/pages/menu_page.py
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton,
    QApplication
)
from PyQt5.QtCore import Qt, pyqtSlot
import logging

logger = logging.getLogger(__name__)

class MainMenuPage(QWidget):
    """
    Main menu page with navigation options.
    
    This page serves as the application entry point with links to:
    - Quick Test (simple configuration)
    - Custom Test (advanced configuration)
    """
    
    def __init__(self, parent=None):
        """Initialize menu page.
        
        Args:
            parent: Parent widget (main window)
        """
        super().__init__(parent)
        self.main_window = parent
        self._setup_ui()
        
    def _setup_ui(self):
        """Set up the UI components."""
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("E-ink Barcode Testing")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 24pt; font-weight: bold; margin: 20px;")
        layout.addWidget(title)
        
        # Subtitle
        subtitle = QLabel("Select a test type to begin")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("font-size: 14pt; margin-bottom: 40px;")
        layout.addWidget(subtitle)
        
        # Add spacer
        layout.addStretch()
        
        # Quick Test button
        self.quick_button = QPushButton("Quick Test")
        self.quick_button.setMinimumSize(200, 60)
        self.quick_button.clicked.connect(self.on_quick_test)
        layout.addWidget(self.quick_button, 0, Qt.AlignCenter)
        
        layout.addSpacing(20)
        
        # Custom Test button
        self.custom_button = QPushButton("Custom Test")
        self.custom_button.setMinimumSize(200, 60)
        self.custom_button.clicked.connect(self.on_custom_test)
        layout.addWidget(self.custom_button, 0, Qt.AlignCenter)
        
        layout.addSpacing(20)

        # Generate Barcodes button
        self.generate_button = QPushButton("Generate Barcodes")
        self.generate_button.setMinimumSize(200, 60)
        self.generate_button.clicked.connect(self.on_generate)
        layout.addWidget(self.generate_button, 0, Qt.AlignCenter)

        layout.addStretch()
        
        # Exit button
        self.exit_button = QPushButton("Exit")
        self.exit_button.setMinimumWidth(100)
        self.exit_button.clicked.connect(QApplication.quit)
        layout.addWidget(self.exit_button, 0, Qt.AlignRight)
        
    @pyqtSlot()
    def on_quick_test(self):
        """Handle quick test button click."""
        if self.main_window:
            self.main_window.show_quick_test()
            
    @pyqtSlot()
    def on_custom_test(self):
        """Handle custom test button click."""
        if self.main_window:
            self.main_window.show_custom_test()

    @pyqtSlot()
    def on_generate(self):
        """Handle generate barcodes button click."""
        if self.main_window:
            self.main_window.show_generate()