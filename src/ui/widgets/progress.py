from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QProgressBar,
    QLabel,
    QPushButton
)
from PyQt5.QtCore import Qt

class ProgressDialog(QWidget):
    """Dialog showing test progress with cancel option."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)

        # Status label
        self.status_label = QLabel("Initializing test...")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(0)  # Indeterminate progress
        layout.addWidget(self.progress_bar)

        # Cancel button
        self.cancel_button = QPushButton("Cancel")
        layout.addWidget(self.cancel_button)

    def update_status(self, message):
        """Update the status message."""
        self.status_label.setText(message)
