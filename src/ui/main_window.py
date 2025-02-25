from PyQt5.QtWidgets import (
    QMainWindow, QStackedWidget, QMessageBox, QFrame,
    QVBoxLayout, QStyleFactory, QApplication
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPalette, QColor
import platform
import logging

from .pages import MainMenuPage, QuickTestPage, CustomTestPage
from ..core.test_controller import TestController

logger = logging.getLogger(__name__)

class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self, test_controller: TestController):
        super().__init__()
        self.test_controller = test_controller
        self.setWindowTitle("E-ink Barcode Testing")
        self.setMinimumSize(1000, 800)

        self.setup_ui()
        self.apply_theme()

    def setup_ui(self):
        """Initialize the user interface."""
        # Create main container
        self.container = QFrame(self)
        self.setCentralWidget(self.container)

        # Create stacked widget
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.setStyleSheet("""
            QStackedWidget {
                background: transparent;
            }
        """)

        # Create layout for container
        container_layout = QVBoxLayout()
        container_layout.addWidget(self.stacked_widget)
        container_layout.setContentsMargins(20, 20, 20, 20)
        self.container.setLayout(container_layout)

        # Create pages
        self.menu_page = MainMenuPage(self)
        self.quick_test_page = QuickTestPage(self, self.test_controller)
        self.custom_test_page = CustomTestPage(self, self.test_controller)

        # Add pages to stack
        self.stacked_widget.addWidget(self.menu_page)
        self.stacked_widget.addWidget(self.quick_test_page)
        self.stacked_widget.addWidget(self.custom_test_page)

        # Show menu initially
        self.show_menu()

    def apply_theme(self):
        """Apply application theme and styling."""
        # Set Fusion style for better cross-platform compatibility
        QApplication.setStyle('Fusion')

        # Define colors based on platform
        if platform.system() == 'Darwin':
            # Lighter theme for Mac
            bg_color = "#2D2D2D"
            accent_color = "#0073BB"
            hover_color = "#0095EE"
            text_color = "white"
        else:
            # Darker theme for others
            bg_color = "#1A1A1A"
            accent_color = "#0073BB"
            hover_color = "#0095EE"
            text_color = "white"

        self.setStyleSheet(f"""
            QMainWindow, QWidget {{
                background-color: {bg_color};
                color: {text_color};
            }}
            QFrame {{
                background-color: {bg_color};
                border-radius: 12px;
            }}
            QPushButton {{
                background-color: {accent_color};
                color: {text_color};
                border: none;
                border-radius: 6px;
                padding: 12px 24px;
                font-size: 16px;
                min-width: 160px;
            }}
            QPushButton:hover {{
                background-color: {hover_color};
            }}
            QPushButton:pressed {{
                background-color: #005C99;
            }}
            QPushButton:disabled {{
                background-color: #555555;
            }}
            QLabel {{
                color: {text_color};
                font-size: 16px;
            }}
            QComboBox {{
                background-color: #3E3E3E;
                color: {text_color};
                border: none;
                border-radius: 6px;
                padding: 8px;
                min-width: 200px;
                font-size: 14px;
            }}
            QComboBox:hover {{
                background-color: #4E4E4E;
            }}
            QComboBox::drop-down {{
                border: none;
            }}
            QComboBox::down-arrow {{
                image: none;
            }}
            QSpinBox, QDoubleSpinBox {{
                background-color: #3E3E3E;
                color: {text_color};
                border: none;
                border-radius: 6px;
                padding: 8px;
                min-width: 100px;
                font-size: 14px;
            }}
            QSpinBox:hover, QDoubleSpinBox:hover {{
                background-color: #4E4E4E;
            }}
            QGroupBox {{
                color: {text_color};
                border: none;
                border-radius: 8px;
                margin-top: 1em;
                padding: 15px;
                font-size: 16px;
                background-color: rgba(255, 255, 255, 0.05);
            }}
            QGroupBox:title {{
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 5px 0 5px;
                color: {hover_color};
            }}
            QSlider::groove:horizontal {{
                border: none;
                height: 6px;
                background: #3E3E3E;
                margin: 2px 0;
                border-radius: 3px;
            }}
            QSlider::handle:horizontal {{
                background: {accent_color};
                border: none;
                width: 16px;
                margin: -5px 0;
                border-radius: 8px;
            }}
            QSlider::handle:horizontal:hover {{
                background: {hover_color};
            }}
            QCheckBox {{
                color: {text_color};
            }}
            QCheckBox::indicator {{
                width: 16px;
                height: 16px;
                border: 1px solid #505050;
                border-radius: 3px;
                background: #3E3E3E;
            }}
            QCheckBox::indicator:checked {{
                background: {accent_color};
            }}
            QProgressBar {{
                border: 1px solid #505050;
                border-radius: 4px;
                text-align: center;
                background-color: #2E2E2E;
                color: {text_color};
                font-weight: bold;
                height: 25px;
                min-height: 25px;
                font-size: 14px;
            }}
            QProgressBar::chunk {{
                background-color: {accent_color};
                width: 1px;
            }}
        """)

    def show_menu(self):
        """Switch to menu page."""
        self.stacked_widget.setCurrentWidget(self.menu_page)

    def show_quick_test(self):
        """Switch to quick test page."""
        self.stacked_widget.setCurrentWidget(self.quick_test_page)

    def show_custom_test(self):
        """Switch to custom test page."""
        self.stacked_widget.setCurrentWidget(self.custom_test_page)

    def navigate_to(self, page_index: int):
        """Navigate to specified page index."""
        self.stacked_widget.setCurrentIndex(page_index)
