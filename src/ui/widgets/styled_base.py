"""Base styled widget classes."""
from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QLinearGradient, QColor, QPalette, QBrush

class StyledWidget(QWidget):
    """Base widget with gradient background."""
    def __init__(self):
        super().__init__()
        self.setup_gradient()

    def setup_gradient(self):
        """Create and set gradient background."""
        gradient = QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0, QColor("#1A1A1A"))
        gradient.setColorAt(1, QColor("#2D2D2D"))

        palette = self.palette()
        palette.setBrush(QPalette.Window, QBrush(gradient))
        self.setAutoFillBackground(True)
        self.setPalette(palette)
