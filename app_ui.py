#!/usr/bin/env python3
"""
E-Ink Testing Interface
Main UI Application with Enhanced Styling
"""

from PyQt6.QtWidgets import (
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
    QFrame
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import (
    QFont,
    QPixmap,
    QPalette,
    QLinearGradient,
    QColor,
    QBrush,
    QImage
)
import sys
import os
from pathlib import Path

# Constants
KNOWN_BARCODES_DIR = "known_barcode"

class StyledWidget(QWidget):
    """Base widget with gradient background"""
    def __init__(self):
        super().__init__()
        # Create and set gradient background
        gradient = QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0, QColor("#1A1A1A"))
        gradient.setColorAt(1, QColor("#2D2D2D"))

        palette = self.palette()
        palette.setBrush(QPalette.ColorRole.Window, QBrush(gradient))
        self.setAutoFillBackground(True)
        self.setPalette(palette)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("E-Ink Testing Interface")
        self.setMinimumSize(1000, 800)

        # Create main container
        self.container = QFrame(self)
        self.setCentralWidget(self.container)

        # Create stacked widget with fade effect
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

        # Apply simplified theme
        self.apply_theme()

    def apply_theme(self):
        # Simplified dark theme with subtle accents
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1A1A1A;
            }
            QFrame {
                background-color: #2D2D2D;
                border-radius: 12px;
            }
            QPushButton {
                background-color: #0073BB;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 12px 24px;
                font-size: 16px;
                min-width: 160px;
            }
            QPushButton:hover {
                background-color: #0095EE;
            }
            QPushButton:pressed {
                background-color: #005C99;
            }
            QPushButton:disabled {
                background-color: #555555;
            }
            QLabel {
                color: #FFFFFF;
                font-size: 16px;
            }
            QComboBox {
                background-color: #3E3E3E;
                color: #FFFFFF;
                border: none;
                border-radius: 6px;
                padding: 8px;
                min-width: 200px;
                font-size: 14px;
            }
            QComboBox:hover {
                background-color: #4E4E4E;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: none;
            }
            QSpinBox, QDoubleSpinBox {
                background-color: #3E3E3E;
                color: #FFFFFF;
                border: none;
                border-radius: 6px;
                padding: 8px;
                min-width: 100px;
                font-size: 14px;
            }
            QSpinBox:hover, QDoubleSpinBox:hover {
                background-color: #4E4E4E;
            }
            QGroupBox {
                color: #FFFFFF;
                border: none;
                border-radius: 8px;
                margin-top: 1em;
                padding: 15px;
                font-size: 16px;
                background-color: rgba(255, 255, 255, 0.05);
            }
            QGroupBox:title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 5px 0 5px;
                color: #0095EE;
            }
            QSlider::groove:horizontal {
                border: none;
                height: 6px;
                background: #3E3E3E;
                margin: 2px 0;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #0073BB;
                border: none;
                width: 16px;
                margin: -5px 0;
                border-radius: 8px;
            }
            QSlider::handle:horizontal:hover {
                background: #0095EE;
            }
        """)

    def navigate_to(self, page_index):
        self.stacked_widget.setCurrentIndex(page_index)

class MainMenuPage(StyledWidget):
    def __init__(self, stacked_widget, main_window):
        super().__init__()
        self.main_window = main_window
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(30)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Title with shadow effect
        title = QLabel("E-Ink Testing Interface")
        title.setFont(QFont("Arial", 36, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("""
            color: #FFFFFF;
            margin-bottom: 20px;
        """)
        layout.addWidget(title)

        # Subtitle
        subtitle = QLabel("Select testing mode")
        subtitle.setFont(QFont("Arial", 20))
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("""
            color: #0095EE;
            margin-bottom: 40px;
        """)
        layout.addWidget(subtitle)

        layout.addSpacing(50)

        # Quick Test Button
        quick_test_btn = QPushButton("Quick Test")
        quick_test_btn.setFixedWidth(300)
        quick_test_btn.clicked.connect(lambda: self.main_window.navigate_to(1))
        layout.addWidget(quick_test_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        layout.addSpacing(20)

        # Custom Test Button
        custom_test_btn = QPushButton("Custom Test")
        custom_test_btn.setFixedWidth(300)
        custom_test_btn.clicked.connect(lambda: self.main_window.navigate_to(2))
        layout.addWidget(custom_test_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        layout.addSpacing(50)
        self.setLayout(layout)

class QuickTestPage(StyledWidget):
    def __init__(self, stacked_widget, main_window):
        super().__init__()
        self.main_window = main_window
        self.current_barcodes = []
        self.current_index = 0
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(25)
        layout.setContentsMargins(30, 30, 30, 30)

        # Title
        title = QLabel("Quick Test")
        title.setFont(QFont("Arial", 32, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("""
            color: #FFFFFF;
            margin-bottom: 20px;
        """)
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
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
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
        self.counter_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
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

        # Action Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(20)

        back_btn = QPushButton("Back")
        back_btn.clicked.connect(lambda: self.main_window.navigate_to(0))

        self.start_btn = QPushButton("Start Test")
        self.start_btn.clicked.connect(self.start_test)
        self.start_btn.setEnabled(False)

        button_layout.addWidget(back_btn)
        button_layout.addWidget(self.start_btn)

        layout.addLayout(button_layout)
        self.setLayout(layout)

        # Load initial barcodes
        self.load_barcodes(self.barcode_combo.currentText())

    def load_barcodes(self, barcode_type):
        """Load barcodes of the selected type from known_barcode directory"""
        self.current_barcodes = []
        self.current_index = 0

        # Map UI names to directory and filename patterns
        type_config = {
            "Code128": {
                "dir": "Code128",
                "patterns": ["hcX"]  # Updated to match your actual filenames
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
                self.show_error(f"No {barcode_type} barcodes found in {type_dir}")
                return

            # Sort barcodes for consistent ordering
            self.current_barcodes.sort()
            self.show_current_barcode()
            self.update_navigation()

        except Exception as e:
            self.show_error(f"Error loading barcodes: {str(e)}")
            print(f"Debug - Error details: {str(e)}")  # For debugging

    def show_current_barcode(self):
        """Display the current barcode image"""
        if not self.current_barcodes:
            return

        try:
            pixmap = QPixmap(self.current_barcodes[self.current_index])
            scaled_pixmap = pixmap.scaled(
                self.preview_label.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )

            self.preview_label.setPixmap(scaled_pixmap)
            self.counter_label.setText(f"{self.current_index + 1}/{len(self.current_barcodes)}")
            self.start_btn.setEnabled(True)

        except Exception as e:
            self.show_error(f"Error displaying barcode: {str(e)}")

    def show_error(self, message):
        """Display error message in preview label"""
        self.preview_label.setPixmap(QPixmap())
        self.preview_label.setText(message)
        self.counter_label.setText("0/0")
        self.start_btn.setEnabled(False)
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

    def start_test(self):
        """Start the test with the currently selected barcode"""
        if self.current_barcodes:
            current_barcode = self.current_barcodes[self.current_index]
            print(f"Starting quick test with barcode: {current_barcode}")
            # TODO: Implement actual test logic

class CustomTestPage(StyledWidget):
    def __init__(self, stacked_widget, main_window):
        super().__init__()
        self.main_window = main_window
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(25)
        layout.setContentsMargins(30, 30, 30, 30)

        # Title
        title = QLabel("Custom Test")
        title.setFont(QFont("Arial", 32, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("""
            color: #FFFFFF;
            margin-bottom: 20px;
        """)
        layout.addWidget(title)

        # Settings
        settings_group = QGroupBox("Test Settings")
        settings_layout = QGridLayout()
        settings_layout.setSpacing(20)

        # Rotation
        settings_layout.addWidget(QLabel("Rotation:"), 0, 0)
        self.rotation_slider = QSlider(Qt.Orientation.Horizontal)
        self.rotation_slider.setRange(0, 360)
        self.rotation_slider.setValue(0)
        settings_layout.addWidget(self.rotation_slider, 0, 1)
        self.rotation_label = QLabel("0°")
        settings_layout.addWidget(self.rotation_label, 0, 2)
        self.rotation_slider.valueChanged.connect(
            lambda v: self.rotation_label.setText(f"{v}°"))

        # Scale
        settings_layout.addWidget(QLabel("Scale:"), 1, 0)
        self.scale_spin = QDoubleSpinBox()
        self.scale_spin.setRange(0.1, 2.0)
        self.scale_spin.setSingleStep(0.1)
        self.scale_spin.setValue(1.0)
        settings_layout.addWidget(self.scale_spin, 1, 1)

        # Barcode Type
        settings_layout.addWidget(QLabel("Barcode Type:"), 2, 0)
        self.barcode_combo = QComboBox()
        self.barcode_combo.addItems(["Code128", "QR Code", "DataMatrix"])
        settings_layout.addWidget(self.barcode_combo, 2, 1)

        # Number of Tests
        settings_layout.addWidget(QLabel("Number of Tests:"), 3, 0)
        self.test_count = QSpinBox()
        self.test_count.setRange(1, 100)
        self.test_count.setValue(10)
        settings_layout.addWidget(self.test_count, 3, 1)

        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)

        # Preview Area
        preview_group = QGroupBox("Preview")
        preview_layout = QVBoxLayout()
        preview_label = QLabel("Configure settings to preview barcode")
        preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        preview_label.setMinimumHeight(300)
        preview_label.setStyleSheet("""
            QLabel {
                background-color: rgba(0, 0, 0, 0.2);
                border-radius: 8px;
                color: #888888;
            }
        """)
        preview_layout.addWidget(preview_label)
        preview_group.setLayout(preview_layout)
        layout.addWidget(preview_group)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(20)

        back_btn = QPushButton("Back")
        back_btn.clicked.connect(lambda: self.main_window.navigate_to(0))

        start_btn = QPushButton("Start Test")
        start_btn.clicked.connect(self.start_test)

        button_layout.addWidget(back_btn)
        button_layout.addWidget(start_btn)

        layout.addLayout(button_layout)
        self.setLayout(layout)

    def start_test(self):
        print("Starting custom test...")
        print(f"Rotation: {self.rotation_slider.value()}°")
        print(f"Scale: {self.scale_spin.value()}")
        print(f"Barcode Type: {self.barcode_combo.currentText()}")
        print(f"Number of Tests: {self.test_count.value()}")

def main():
    app = QApplication(sys.argv)

    # Set application-wide attributes
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
