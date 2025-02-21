from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

class MainMenuPage(QWidget):
    """Main menu page with navigation buttons."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = self.window()
        self.setup_ui()

    def setup_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout()
        layout.setSpacing(25)
        layout.setContentsMargins(30, 30, 30, 30)

        # Title
        title = QLabel("E-Ink Testing Interface")
        title.setFont(QFont("Arial", 32, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #FFFFFF; margin-bottom: 20px;")
        layout.addWidget(title)

        # Add some spacing at the top
        layout.addStretch()

        # Quick test button
        self.quick_test_button = QPushButton("Quick Test")
        self.quick_test_button.clicked.connect(lambda: self.main_window.navigate_to(1))
        self.quick_test_button.setMinimumWidth(200)
        layout.addWidget(self.quick_test_button, 0, Qt.AlignCenter)

        # Custom test button
        self.custom_test_button = QPushButton("Custom Test")
        self.custom_test_button.clicked.connect(lambda: self.main_window.navigate_to(2))
        self.custom_test_button.setMinimumWidth(200)
        layout.addWidget(self.custom_test_button, 0, Qt.AlignCenter)

        # Add some spacing at the bottom
        layout.addStretch()

        self.setLayout(layout)
