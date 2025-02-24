import pytest
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtCore import Qt

def test_qt5_basic(qapp):
    """Basic test to verify PyQt5 is working."""
    button = QPushButton("Test")
    assert button.text() == "Test"

def test_qt5_signals(qtbot):
    """Test PyQt5 signals and slots are working."""
    button = QPushButton("Click me")
    qtbot.addWidget(button)

    # Create a flag to track if the signal was emitted
    clicked = False
    def on_click():
        nonlocal clicked
        clicked = True

    button.clicked.connect(on_click)
    qtbot.mouseClick(button, Qt.LeftButton)

    assert clicked is True
