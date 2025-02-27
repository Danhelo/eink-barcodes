# src/ui/pages/quick_page.py
from PyQt5.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QGroupBox, QSlider, QMessageBox
)
from PyQt5.QtCore import Qt, pyqtSlot
import logging
import os

from .base_page import BasePage
from ...core.config import TestConfig

logger = logging.getLogger(__name__)

class QuickTestPage(BasePage):
    """
    Quick test page with simplified controls.
    
    This page provides a streamlined interface for common testing needs:
    - Barcode type selection
    - Basic transformation controls
    - Simple parameter adjustments
    """
    
    PAGE_TITLE = "Quick Test"
    
    def _create_content(self):
        """Create quick test controls."""
        content = QVBoxLayout()
        
        # Barcode type selection
        type_group = QGroupBox("Barcode Type")
        type_layout = QHBoxLayout()
        
        type_layout.addWidget(QLabel("Type:"))
        self.barcode_combo = QComboBox()
        self.barcode_combo.addItems(["Code128", "QR Code", "DataMatrix"])
        self.barcode_combo.currentIndexChanged.connect(self.on_barcode_changed)
        type_layout.addWidget(self.barcode_combo)
        
        type_group.setLayout(type_layout)
        content.addWidget(type_group)
        
        # Transformations
        transform_group = QGroupBox("Transformations")
        transform_layout = QVBoxLayout()
        
        # Rotation
        rotation_layout = QHBoxLayout()
        rotation_layout.addWidget(QLabel("Rotation:"))
        self.rotation_slider = QSlider(Qt.Horizontal)
        self.rotation_slider.setRange(0, 360)
        self.rotation_slider.setSingleStep(15)
        self.rotation_slider.setTickInterval(90)
        self.rotation_slider.setTickPosition(QSlider.TicksBelow)
        self.rotation_slider.setValue(0)
        self.rotation_slider.valueChanged.connect(self.on_settings_changed)
        rotation_layout.addWidget(self.rotation_slider)
        self.rotation_value = QLabel("0°")
        rotation_layout.addWidget(self.rotation_value)
        transform_layout.addLayout(rotation_layout)
        
        # Scale
        scale_layout = QHBoxLayout()
        scale_layout.addWidget(QLabel("Scale:"))
        self.scale_slider = QSlider(Qt.Horizontal)
        self.scale_slider.setRange(50, 200)  # 0.5x to 2.0x
        self.scale_slider.setSingleStep(10)  # 0.1x steps
        self.scale_slider.setTickInterval(50)
        self.scale_slider.setTickPosition(QSlider.TicksBelow)
        self.scale_slider.setValue(100)  # 1.0x
        self.scale_slider.valueChanged.connect(self.on_settings_changed)
        scale_layout.addWidget(self.scale_slider)
        self.scale_value = QLabel("1.0x")
        scale_layout.addWidget(self.scale_value)
        transform_layout.addLayout(scale_layout)
        
        transform_group.setLayout(transform_layout)
        content.addWidget(transform_group)
        
        # Initialize
        self.barcode_images = []
        # Make sure preview attribute exists before loading images
        if not hasattr(self, 'preview'):
            self.preview = self._create_preview()
        self.load_barcode_images()
        
        return content
        
    def on_barcode_changed(self, index):
        """Handle barcode type change."""
        self.load_barcode_images()
        
    def on_settings_changed(self):
        """Handle settings changes."""
        # Update labels
        rotation = self.rotation_slider.value()
        self.rotation_value.setText(f"{rotation}°")
        
        scale = self.scale_slider.value() / 100.0
        self.scale_value.setText(f"{scale:.1f}x")
        
        # Update preview
        self.update_preview()
        
    def load_barcode_images(self):
        """Load barcode images of the selected type."""
        barcode_type = self.barcode_combo.currentText()
        self.barcode_images = []
        
        # First try specific directory for this type
        dir_path = os.path.join('examples', barcode_type.replace(" ", "_"))
        
        # If not found, try the general examples directory
        if not os.path.exists(dir_path):
            dir_path = 'examples'
            
        # Find images
        if os.path.exists(dir_path):
            for file in os.listdir(dir_path):
                if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                    full_path = os.path.join(dir_path, file)
                    self.barcode_images.append(full_path)
                    
        # Update preview with first image if available
        if self.barcode_images:
            logger.info(f"Loaded {len(self.barcode_images)} images from {dir_path}")
            self.preview.load_image(self.barcode_images[0])
            self.update_preview()
        else:
            logger.warning(f"No images found in {dir_path}")
            self.preview.clear()
            
    def update_preview(self):
        """Update preview with current settings."""
        transformations = {
            'rotation': {
                'angle': self.rotation_slider.value()
            },
            'scale': {
                'factor': self.scale_slider.value() / 100.0
            },
            'center': {
                'width': 800,
                'height': 600
            }
        }
        
        self.preview.update_preview(transformations)
        
    def get_test_config(self):
        """Get test configuration from UI settings."""
        if not self.barcode_images:
            QMessageBox.warning(
                self, "No Images",
                "No barcode images found for the selected type."
            )
            return None
            
        return TestConfig(
            barcode_type=self.barcode_combo.currentText(),
            image_paths=self.barcode_images,
            delay_between_images=0.5,
            transformations={
                'rotation': {'angle': self.rotation_slider.value()},
                'scale': {'factor': self.scale_slider.value() / 100.0},
                'center': {'width': 800, 'height': 600}
            }
        )