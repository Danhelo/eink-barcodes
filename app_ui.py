#!/usr/bin/env python3
"""
E-Ink Testing Interface
Main UI Application with Enhanced Styling and Cross-Platform Support
"""
import os
import sys
import platform
from typing import Optional, Dict, Any, List
from pathlib import Path

# Platform-specific display handling
def setup_display() -> str:
    """Configure display environment based on platform."""
    system = platform.system()
    if system == 'Darwin':  # macOS
        if not os.environ.get('DISPLAY'):
            os.environ['DISPLAY'] = ':0'
        return 'cocoa'
    elif system == 'Linux':
        if os.environ.get('WAYLAND_DISPLAY'):
            return 'wayland'
        elif os.environ.get('DISPLAY'):
            return 'xcb'
        else:
            os.environ['QT_QPA_PLATFORM'] = 'offscreen'
            return 'offscreen'
    else:
        return 'unknown'

# Import Qt after display setup
os.environ['QT_MAC_WANTS_LAYER'] = '1'  # Prevent rendering issues on Mac
platform_type = setup_display()

from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QStackedWidget,
    QComboBox,
    QSpinBox,
    QDoubleSpinBox,
    QSlider,
    QGridLayout,
    QGroupBox,
    QFrame,
    QMessageBox,
    QProgressBar,
    QCheckBox,
    QStyleFactory
)
from PyQt5.QtCore import Qt, QSize, pyqtSignal
from PyQt5.QtGui import (
    QFont,
    QPixmap,
    QPalette,
    QColor,
    QBrush,
    QLinearGradient,
    QImage
)

# Constants
KNOWN_BARCODES_DIR = "known_barcode"

class TestConfig:
    """Configuration class for test parameters."""
    def __init__(self):
        self.barcode_type: str = "Code128"
        self.scale: float = 1.0
        self.rotation: int = 0
        self.count: int = 1
        self.refresh_rate: float = 1.0
        self.auto_center: bool = True
        self.barcode_path: Optional[str] = None

class StyledWidget(QWidget):
    """Base widget with gradient background"""
    def __init__(self):
        super().__init__()
        # Create and set gradient background
        gradient = QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0, QColor("#1A1A1A"))
        gradient.setColorAt(1, QColor("#2D2D2D"))

        palette = self.palette()
        palette.setBrush(QPalette.Window, QBrush(gradient))
        self.setAutoFillBackground(True)
        self.setPalette(palette)

class MainMenuPage(StyledWidget):
    """Main menu page with navigation buttons."""
    def __init__(self, parent=None, main_window=None):
        super().__init__()
        self.main_window = main_window
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(25)
        layout.setContentsMargins(30, 30, 30, 30)

        # Title
        title = QLabel("E-Ink Testing Interface")
        title.setFont(QFont("Arial", 32, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #FFFFFF; margin-bottom: 20px;")
        layout.addWidget(title)

        # Quick Test Button
        quick_test_btn = QPushButton("Quick Test")
        quick_test_btn.clicked.connect(lambda: self.main_window.navigate_to(1))
        layout.addWidget(quick_test_btn)

        # Custom Test Button
        custom_test_btn = QPushButton("Custom Test")
        custom_test_btn.clicked.connect(lambda: self.main_window.navigate_to(2))
        layout.addWidget(custom_test_btn)

        layout.addStretch()
        self.setLayout(layout)

class QuickTestPage(StyledWidget):
    """Quick test configuration page with barcode preview."""
    test_started = pyqtSignal(TestConfig)

    def __init__(self, parent=None, main_window=None):
        super().__init__()
        self.main_window = main_window
        self.config = TestConfig()
        self.current_barcodes: List[str] = []
        self.current_index: int = 0
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(25)
        layout.setContentsMargins(30, 30, 30, 30)

        # Title
        title = QLabel("Quick Test")
        title.setFont(QFont("Arial", 32, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #FFFFFF; margin-bottom: 20px;")
        layout.addWidget(title)

        # Barcode Type Selection
        type_group = QGroupBox("Barcode Type")
        type_layout = QVBoxLayout()
        type_layout.setSpacing(15)
        self.barcode_combo = QComboBox()
        self.barcode_combo.addItems(["Code128", "QR Code", "DataMatrix"])
        self.barcode_combo.currentTextChanged.connect(self.load_barcodes)
        type_layout.addWidget(self.barcode_combo)
        type_group.setLayout(type_layout)
        layout.addWidget(type_group)

        # Preview Area
        preview_group = QGroupBox("Preview")
        preview_layout = QVBoxLayout()

        self.preview_label = QLabel("Select a barcode type to preview")
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setMinimumHeight(300)
        self.preview_label.setStyleSheet("""
            QLabel {
                background-color: rgba(0, 0, 0, 0.2);
                border-radius: 8px;
                color: #888888;
            }
        """)

        # Navigation with circular buttons
        nav_layout = QHBoxLayout()

        self.prev_btn = QPushButton("←")
        self.prev_btn.setFixedWidth(40)
        self.prev_btn.setFixedHeight(40)
        self.prev_btn.setStyleSheet("""
            QPushButton {
                border-radius: 20px;
                font-size: 20px;
                min-width: 40px;
            }
        """)
        self.prev_btn.clicked.connect(self.show_previous)
        self.prev_btn.setEnabled(False)

        self.next_btn = QPushButton("→")
        self.next_btn.setFixedWidth(40)
        self.next_btn.setFixedHeight(40)
        self.next_btn.setStyleSheet("""
            QPushButton {
                border-radius: 20px;
                font-size: 20px;
                min-width: 40px;
            }
        """)
        self.next_btn.clicked.connect(self.show_next)
        self.next_btn.setEnabled(False)

        # Counter with subtle background
        self.counter_label = QLabel("0/0")
        self.counter_label.setAlignment(Qt.AlignCenter)
        self.counter_label.setStyleSheet("""
            color: #FFFFFF;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 4px;
            padding: 4px 12px;
        """)
        self.counter_label.setFixedWidth(80)

        nav_layout.addStretch()
        nav_layout.addWidget(self.prev_btn)
        nav_layout.addWidget(self.counter_label)
        nav_layout.addWidget(self.next_btn)
        nav_layout.addStretch()

        preview_layout.addWidget(self.preview_label)
        preview_layout.addLayout(nav_layout)
        preview_group.setLayout(preview_layout)
        layout.addWidget(preview_group)

        # Settings
        settings_group = QGroupBox("Test Settings")
        settings_layout = QGridLayout()

        # Count
        settings_layout.addWidget(QLabel("Number of Tests:"), 0, 0)
        self.count_spin = QSpinBox()
        self.count_spin.setRange(1, 100)
        self.count_spin.setValue(1)
        self.count_spin.valueChanged.connect(self.update_config)
        settings_layout.addWidget(self.count_spin, 0, 1)

        # Auto-center
        self.auto_center = QCheckBox("Auto-center barcodes")
        self.auto_center.setChecked(True)
        self.auto_center.stateChanged.connect(self.update_config)
        settings_layout.addWidget(self.auto_center, 1, 0, 1, 2)

        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)

        # Buttons
        button_layout = QHBoxLayout()
        self.back_button = QPushButton("Back")
        self.back_button.clicked.connect(lambda: self.main_window.navigate_to(0))
        self.start_button = QPushButton("Start Test")
        self.start_button.clicked.connect(self.start_test)
        self.start_button.setEnabled(False)
        button_layout.addWidget(self.back_button)
        button_layout.addWidget(self.start_button)
        layout.addLayout(button_layout)

        self.setLayout(layout)

        # Load initial barcodes
        self.load_barcodes(self.barcode_combo.currentText())

    def load_barcodes(self, barcode_type: str):
        """Load barcodes of the selected type from known_barcode directory"""
        self.current_barcodes = []
        self.current_index = 0

        # Map UI names to directory and filename patterns
        type_config = {
            "Code128": {
                "dir": "Code128",
                "patterns": ["hcX"]
            },
            "QR Code": {
                "dir": "QR",
                "patterns": ["qr", "QR"]
            },
            "DataMatrix": {
                "dir": "DataMatrix",
                "patterns": ["matrix", "dm"]
            }
        }

        config = type_config.get(barcode_type)
        if not config:
            self.show_error("Invalid barcode type selected")
            return

        try:
            # Check main directory
            if not os.path.exists(KNOWN_BARCODES_DIR):
                self.show_error(f"Directory {KNOWN_BARCODES_DIR} not found")
                return

            # Check type-specific subdirectory
            type_dir = os.path.join(KNOWN_BARCODES_DIR, config["dir"])
            if os.path.exists(type_dir):
                # Look in type-specific subdirectory first
                for file in os.listdir(type_dir):
                    if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                        if any(pattern.lower() in file.lower() for pattern in config["patterns"]):
                            self.current_barcodes.append(os.path.join(type_dir, file))

            # Also look in main directory as fallback
            for file in os.listdir(KNOWN_BARCODES_DIR):
                if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                    if any(pattern.lower() in file.lower() for pattern in config["patterns"]):
                        full_path = os.path.join(KNOWN_BARCODES_DIR, file)
                        if full_path not in self.current_barcodes:  # Avoid duplicates
                            self.current_barcodes.append(full_path)

            if not self.current_barcodes:
                self.show_error(f"No {barcode_type} barcodes found")
                return

            # Sort barcodes for consistent ordering
            self.current_barcodes.sort()
            self.show_current_barcode()
            self.update_navigation()

        except Exception as e:
            self.show_error(f"Error loading barcodes: {str(e)}")
            print(f"Debug - Error details: {str(e)}")

    def show_current_barcode(self):
        """Display the current barcode image"""
        if not self.current_barcodes:
            return

        try:
            pixmap = QPixmap(self.current_barcodes[self.current_index])
            scaled_pixmap = pixmap.scaled(
                self.preview_label.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )

            self.preview_label.setPixmap(scaled_pixmap)
            self.counter_label.setText(f"{self.current_index + 1}/{len(self.current_barcodes)}")
            self.start_button.setEnabled(True)
            self.update_config()

        except Exception as e:
            self.show_error(f"Error displaying barcode: {str(e)}")

    def show_error(self, message: str):
        """Display error message in preview label"""
        self.preview_label.setPixmap(QPixmap())
        self.preview_label.setText(message)
        self.counter_label.setText("0/0")
        self.start_button.setEnabled(False)
        self.update_navigation()

    def update_navigation(self):
        """Update navigation button states"""
        has_barcodes = len(self.current_barcodes) > 0
        self.prev_btn.setEnabled(has_barcodes and self.current_index > 0)
        self.next_btn.setEnabled(has_barcodes and self.current_index < len(self.current_barcodes) - 1)

    def show_previous(self):
        """Show previous barcode"""
        if self.current_index > 0:
            self.current_index -= 1
            self.show_current_barcode()
            self.update_navigation()

    def show_next(self):
        """Show next barcode"""
        if self.current_index < len(self.current_barcodes) - 1:
            self.current_index += 1
            self.show_current_barcode()
            self.update_navigation()

    def update_config(self):
        """Update test configuration from UI values"""
        self.config.barcode_type = self.barcode_combo.currentText()
        self.config.count = self.count_spin.value()
        self.config.auto_center = self.auto_center.isChecked()
        if self.current_barcodes and 0 <= self.current_index < len(self.current_barcodes):
            self.config.barcode_path = self.current_barcodes[self.current_index]

    def start_test(self):
        """Start test with current configuration"""
        if not self.current_barcodes:
            return

        self.update_config()
        print(f"Starting quick test with config:")
        print(f"  Type: {self.config.barcode_type}")
        print(f"  Count: {self.config.count}")
        print(f"  Auto-center: {self.config.auto_center}")
        print(f"  Barcode: {self.config.barcode_path}")

        self.test_started.emit(self.config)
class CustomTestPage(StyledWidget):
    """Custom test configuration page with preview."""
    test_started = pyqtSignal(TestConfig)

    def __init__(self, parent=None, main_window=None):
        super().__init__()
        self.main_window = main_window
        self.config = TestConfig()
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(25)
        layout.setContentsMargins(30, 30, 30, 30)

        # Title
        title = QLabel("Custom Test")
        title.setFont(QFont("Arial", 32, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #FFFFFF; margin-bottom: 20px;")
        layout.addWidget(title)

        # Settings
        settings_group = QGroupBox("Test Settings")
        settings_layout = QGridLayout()
        settings_layout.setSpacing(20)

        # Rotation
        settings_layout.addWidget(QLabel("Rotation:"), 0, 0)
        self.rotation_slider = QSlider(Qt.Horizontal)
        self.rotation_slider.setRange(0, 360)
        self.rotation_slider.setValue(0)
        self.rotation_slider.setTickPosition(QSlider.TicksBelow)
        self.rotation_slider.setTickInterval(90)
        settings_layout.addWidget(self.rotation_slider, 0, 1)
        self.rotation_label = QLabel("0°")
        settings_layout.addWidget(self.rotation_label, 0, 2)
        self.rotation_slider.valueChanged.connect(
            lambda v: (self.rotation_label.setText(f"{v}°"), self.update_config()))

        # Scale
        settings_layout.addWidget(QLabel("Scale:"), 1, 0)
        self.scale_spin = QDoubleSpinBox()
        self.scale_spin.setRange(0.1, 2.0)
        self.scale_spin.setSingleStep(0.1)
        self.scale_spin.setValue(1.0)
        self.scale_spin.valueChanged.connect(self.update_config)
        settings_layout.addWidget(self.scale_spin, 1, 1)

        # Barcode Type
        settings_layout.addWidget(QLabel("Barcode Type:"), 2, 0)
        self.barcode_combo = QComboBox()
        self.barcode_combo.addItems(["Code128", "QR Code", "DataMatrix"])
        self.barcode_combo.currentTextChanged.connect(self.update_config)
        settings_layout.addWidget(self.barcode_combo, 2, 1)

        # Number of Tests
        settings_layout.addWidget(QLabel("Number of Tests:"), 3, 0)
        self.count_spin = QSpinBox()
        self.count_spin.setRange(1, 100)
        self.count_spin.setValue(10)
        self.count_spin.valueChanged.connect(self.update_config)
        settings_layout.addWidget(self.count_spin, 3, 1)

        # Refresh Rate
        settings_layout.addWidget(QLabel("Refresh Rate (Hz):"), 4, 0)
        self.refresh_spin = QDoubleSpinBox()
        self.refresh_spin.setRange(0.1, 10.0)
        self.refresh_spin.setSingleStep(0.1)
        self.refresh_spin.setValue(1.0)
        self.refresh_spin.valueChanged.connect(self.update_config)
        settings_layout.addWidget(self.refresh_spin, 4, 1)

        # Auto-center
        self.auto_center = QCheckBox("Auto-center barcodes")
        self.auto_center.setChecked(True)
        self.auto_center.stateChanged.connect(self.update_config)
        settings_layout.addWidget(self.auto_center, 5, 0, 1, 2)

        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)

        # Preview Area
        preview_group = QGroupBox("Preview")
        preview_layout = QVBoxLayout()
        self.preview_label = QLabel("Configure settings to preview barcode")
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setMinimumHeight(300)
        self.preview_label.setStyleSheet("""
            QLabel {
                background-color: rgba(0, 0, 0, 0.2);
                border-radius: 8px;
                color: #888888;
            }
        """)
        preview_layout.addWidget(self.preview_label)
        preview_group.setLayout(preview_layout)
        layout.addWidget(preview_group)

        # Buttons
        button_layout = QHBoxLayout()
        self.back_button = QPushButton("Back")
        self.back_button.clicked.connect(lambda: self.main_window.navigate_to(0))
        self.start_button = QPushButton("Start Test")
        self.start_button.clicked.connect(self.start_test)
        button_layout.addWidget(self.back_button)
        button_layout.addWidget(self.start_button)
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def update_config(self):
        """Update test configuration from UI values."""
        self.config.barcode_type = self.barcode_combo.currentText()
        self.config.scale = self.scale_spin.value()
        self.config.rotation = self.rotation_slider.value()
        self.config.count = self.count_spin.value()
        self.config.refresh_rate = self.refresh_spin.value()
        self.config.auto_center = self.auto_center.isChecked()

    def start_test(self):
        """Start test with current configuration."""
        self.update_config()
        print(f"Starting custom test with config:")
        print(f"  Type: {self.config.barcode_type}")
        print(f"  Scale: {self.config.scale}")
        print(f"  Rotation: {self.config.rotation}")
        print(f"  Count: {self.config.count}")
        print(f"  Refresh Rate: {self.config.refresh_rate}")
        print(f"  Auto-center: {self.config.auto_center}")

        self.test_started.emit(self.config)

class TestProgressDialog(QMessageBox):
    """Dialog showing test progress."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Test Progress")
        self.setIcon(QMessageBox.Information)

        # Add progress bar
        self.progress = QProgressBar(self)
        self.progress.setGeometry(self.width() // 4, 80, self.width() // 2, 20)
        self.progress.setRange(0, 100)

        # Add status label
        self.status = QLabel("Initializing test...", self)
        self.status.setGeometry(self.width() // 4, 110, self.width() // 2, 20)

        self.setStandardButtons(QMessageBox.Cancel)
        self.setDefaultButton(QMessageBox.Cancel)

    def update_progress(self, value: int, status: str):
        """Update progress bar and status text."""
        self.progress.setValue(value)
        self.status.setText(status)

class MainWindow(QMainWindow):
    """Main application window."""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("E-Ink Testing Interface")
        self.setMinimumSize(1000, 800)

        # Set up UI for headless operation if needed
        if not os.environ.get('DISPLAY') and platform.system() != 'Darwin':
            print("No display detected - running in headless mode")
            QApplication.setStyle('Fusion')

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
        self.main_menu = MainMenuPage(self.stacked_widget, self)
        self.quick_test = QuickTestPage(self.stacked_widget, self)
        self.custom_test = CustomTestPage(self.stacked_widget, self)

        # Add pages to stacked widget
        self.stacked_widget.addWidget(self.main_menu)
        self.stacked_widget.addWidget(self.quick_test)
        self.stacked_widget.addWidget(self.custom_test)

        # Connect test signals
        self.quick_test.test_started.connect(self.start_test)
        self.custom_test.test_started.connect(self.start_test)

        # Apply theme
        self.apply_theme()

    def apply_theme(self):
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
            }}
            QProgressBar::chunk {{
                background-color: {accent_color};
                width: 1px;
            }}
        """)

    def navigate_to(self, page_index: int):
        """Navigate to specified page index."""
        self.stacked_widget.setCurrentIndex(page_index)

    def start_test(self, config: TestConfig):
        """Start test with given configuration."""
        # Show progress dialog
        progress = TestProgressDialog(self)
        progress.show()

        # Simulate test progress
        for i in range(101):
            QApplication.processEvents()
            progress.update_progress(i, f"Processing test {i}%...")

            if progress.result() == QMessageBox.Cancel:
                print("Test cancelled")
                return

        progress.close()
        QMessageBox.information(self, "Test Complete", "Test completed successfully!")

def main():
    # Print environment info
    print(f"Operating System: {platform.system()}")
    print(f"Platform Type: {platform_type}")
    print(f"Display: {os.environ.get('DISPLAY')}")

    # Create application
    app = QApplication(sys.argv)

    # Print Qt debug info
    print(f"Available styles: {QStyleFactory.keys()}")
    print(f"Platform: {app.platformName()}")
    print(f"Style: {app.style().objectName()}")

    # Create and show window
    window = MainWindow()
    window.show()

    return app.exec_()

if __name__ == '__main__':
    sys.exit(main())
