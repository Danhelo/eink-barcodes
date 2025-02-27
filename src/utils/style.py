# src/utils/style.py
from PyQt5.QtWidgets import QApplication
import logging

logger = logging.getLogger(__name__)

def apply_stylesheet(widget):
    """Apply application stylesheet.
    
    Args:
        widget: Widget to apply stylesheet to
    """
    stylesheet = """
        /* Base styles */
        QMainWindow, QWidget {
            background-color: #2D2D2D;
            color: white;
        }
        
        /* Text styles */
        QLabel {
            color: white;
            font-size: 12pt;
        }
        
        QGroupBox {
            font-size: 12pt;
            font-weight: bold;
            border: 1px solid #555555;
            border-radius: 5px;
            margin-top: 20px;
            padding-top: 20px;
        }
        
        QGroupBox::title {
            subcontrol-origin: margin;
            subcontrol-position: top center;
            padding: 0 8px;
            color: #0078D7;
        }
        
        /* Button styles */
        QPushButton {
            background-color: #0078D7;
            color: white;
            border: none;
            border-radius: 5px;
            padding: 8px 16px;
            font-size: 10pt;
            min-height: 20px;
        }
        
        QPushButton:hover {
            background-color: #0086E6;
        }
        
        QPushButton:pressed {
            background-color: #005EA3;
        }
        
        QPushButton:disabled {
            background-color: #555555;
            color: #AAAAAA;
        }
        
        /* Control styles */
        QComboBox, QSpinBox, QDoubleSpinBox {
            background-color: #3C3C3C;
            color: white;
            border: 1px solid #555555;
            border-radius: 3px;
            padding: 5px;
            min-height: 20px;
        }
        
        QComboBox::drop-down {
            border: none;
            background-color: #0078D7;
            border-top-right-radius: 3px;
            border-bottom-right-radius: 3px;
        }
        
        QComboBox:on {
            background-color: #444444;
        }
        
        QComboBox QAbstractItemView {
            background-color: #3C3C3C;
            color: white;
            selection-background-color: #0078D7;
        }
        
        /* Slider styles */
        QSlider::groove:horizontal {
            border: 1px solid #555555;
            height: 6px;
            background: #3C3C3C;
            border-radius: 3px;
        }
        
        QSlider::handle:horizontal {
            background: #0078D7;
            border: none;
            width: 16px;
            margin: -5px 0;
            border-radius: 8px;
        }
        
        QSlider::handle:horizontal:hover {
            background: #0086E6;
        }
        
        /* List styles */
        QListWidget {
            background-color: #3C3C3C;
            color: white;
            border: 1px solid #555555;
            border-radius: 3px;
        }
        
        QListWidget::item:selected {
            background-color: #0078D7;
            color: white;
        }
        
        QListWidget::item:hover {
            background-color: #444444;
        }
        
        /* Progress bar styles */
        QProgressBar {
            border: 1px solid #555555;
            border-radius: 3px;
            text-align: center;
            background-color: #3C3C3C;
            color: white;
            font-weight: bold;
        }
        
        QProgressBar::chunk {
            background-color: #0078D7;
            border-radius: 2px;
        }
        
        /* Checkbox styles */
        QCheckBox {
            spacing: 8px;
        }
        
        QCheckBox::indicator {
            width: 18px;
            height: 18px;
            border: 1px solid #555555;
            border-radius: 3px;
            background-color: #3C3C3C;
        }
        
        QCheckBox::indicator:checked {
            background-color: #0078D7;
        }
    """
    
    widget.setStyleSheet(stylesheet)
    logger.debug("Applied application stylesheet")