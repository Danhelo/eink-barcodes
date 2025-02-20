#!/usr/bin/env python3
import os
import sys
from PyQt5.QtWidgets import QApplication, QStyleFactory
from PyQt5.QtCore import Qt

# Set platform to offscreen if no display available
if not os.environ.get('DISPLAY'):
    os.environ['QT_QPA_PLATFORM'] = 'offscreen'

# Create application instance
app = QApplication(sys.argv)

# Force platform plugin
app.setStyle('Fusion')

print("PyQt5 imported successfully!")
print(f"Available styles: {QStyleFactory.keys()}")
print(f"Platform: {app.platformName()}")
print(f"Current style: {app.style().objectName()}")

# Don't actually show any windows for this test
sys.exit(0)
