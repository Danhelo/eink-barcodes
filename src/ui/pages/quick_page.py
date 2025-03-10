# src/ui/pages/quick_page.py
from PyQt5.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QGroupBox, QSlider, QMessageBox, QDoubleSpinBox, QWidget
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
        # Match types from generate_page (capitalized for display)
        self.barcode_combo.addItems(["code128", "upca", "upce", "datamatrix"])
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
        
        # Scale options
        scale_group = QGroupBox("Scaling")
        scale_layout = QVBoxLayout()

        # Scale Type Selection
        scale_type_layout = QHBoxLayout()
        scale_type_layout.addWidget(QLabel("Scaling Type:"))
        self.scale_type_combo = QComboBox()
        self.scale_type_combo.addItems(["Relative (factor)", "Absolute (mm)"])
        self.scale_type_combo.currentIndexChanged.connect(self.on_scale_type_changed)
        scale_type_layout.addWidget(self.scale_type_combo)
        scale_layout.addLayout(scale_type_layout)

        # Relative Scaling (Slider) - in a container widget
        self.relative_scale_widget = QWidget()
        relative_scale_layout = QHBoxLayout(self.relative_scale_widget)
        relative_scale_layout.setContentsMargins(0, 0, 0, 0)
        relative_scale_layout.addWidget(QLabel("Scale:"))
        self.scale_slider = QSlider(Qt.Horizontal)
        self.scale_slider.setRange(50, 200)  # 0.5x to 2.0x
        self.scale_slider.setSingleStep(10)  # 0.1x steps
        self.scale_slider.setTickInterval(50)
        self.scale_slider.setTickPosition(QSlider.TicksBelow)
        self.scale_slider.setValue(100)  # 1.0x
        self.scale_slider.valueChanged.connect(self.on_settings_changed)
        relative_scale_layout.addWidget(self.scale_slider)
        self.scale_value = QLabel("1.0x")
        relative_scale_layout.addWidget(self.scale_value)
        scale_layout.addWidget(self.relative_scale_widget)

        # Absolute Scaling (mm input) - in a container widget
        self.absolute_scale_widget = QWidget()
        absolute_scale_layout = QHBoxLayout(self.absolute_scale_widget)
        absolute_scale_layout.setContentsMargins(0, 0, 0, 0)
        absolute_scale_layout.addWidget(QLabel("Width:"))
        self.width_mm_spin = QDoubleSpinBox()
        self.width_mm_spin.setRange(5.0, 200.0)  # 5mm to 200mm
        self.width_mm_spin.setSingleStep(1.0)
        self.width_mm_spin.setDecimals(1)
        self.width_mm_spin.setValue(20.0)  # 20mm default
        self.width_mm_spin.setSuffix(" mm")
        self.width_mm_spin.valueChanged.connect(self.on_settings_changed)
        absolute_scale_layout.addWidget(self.width_mm_spin)
        scale_layout.addWidget(self.absolute_scale_widget)

        scale_group.setLayout(scale_layout)
        transform_layout.addWidget(scale_group)
        
        # Important: Set the layout for the transform group
        transform_group.setLayout(transform_layout)
        content.addWidget(transform_group)
        
        # Initialize
        self.barcode_images = []
        # Make sure preview attribute exists before loading images
        if not hasattr(self, 'preview'):
            self.preview = self._create_preview()
        
        # Set initial scale UI state
        self.on_scale_type_changed(0)
        self.load_barcode_images()
        
        return content
    
    def on_scale_type_changed(self, index):
        """Handle switching between relative and absolute scaling."""
        is_relative = index == 0
        self.relative_scale_widget.setVisible(is_relative)
        self.absolute_scale_widget.setVisible(not is_relative)
        self.update_preview()
        
    def on_barcode_changed(self, index):
        """Handle barcode type change."""
        self.load_barcode_images()
        
    def on_settings_changed(self):
        """Handle settings changes."""
        # Update labels
        rotation = self.rotation_slider.value()
        self.rotation_value.setText(f"{rotation}°")
        
        if hasattr(self, 'scale_type_combo') and self.scale_type_combo.currentIndex() == 0:
            # Only update the relative scale value label
            scale = self.scale_slider.value() / 100.0
            self.scale_value.setText(f"{scale:.1f}x")
        
        # Update preview
        self.update_preview()
        
    def load_barcode_images(self):
        """Load barcode images of the selected type recursively."""
        barcode_type = self.barcode_combo.currentText()
        self.barcode_images = []
        
        # Define directory mapping for different barcode types
        # This handles both capitalization and folder naming conventions
        dir_mapping = {
            "code128": ["code128", "Code128"],
            "upca": ["upca", "UPCA"],
            "upce": ["upce", "UPCE"],
            "datamatrix": ["datamatrix", "DataMatrix"]
        }
        
        # Try each possible directory name for this type
        dir_found = False
        if barcode_type in dir_mapping:
            for dir_name in dir_mapping[barcode_type]:
                dir_path = os.path.join('examples', dir_name)
                if os.path.exists(dir_path):
                    dir_found = True
                    break
        
        # If not found, fall back to the general examples directory
        if not dir_found:
            dir_path = 'examples'
            
        # Find images recursively
        if os.path.exists(dir_path):
            for root, _, files in os.walk(dir_path):
                for file in files:
                    if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                        full_path = os.path.join(root, file)
                        self.barcode_images.append(full_path)
                    
        # Update preview with first image if available
        if self.barcode_images:
            logger.info(f"Loaded {len(self.barcode_images)} images recursively from {dir_path}")
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
            'center': {
                'width': 800,
                'height': 600
            }
        }
        
        # Choose scaling type based on selection
        if hasattr(self, 'scale_type_combo'):
            if self.scale_type_combo.currentIndex() == 0:
                # Relative scaling
                transformations['scale'] = {
                    'factor': self.scale_slider.value() / 100.0
                }
            else:
                # Absolute scaling (mm)
                transformations['scale'] = {
                    'width_mm': self.width_mm_spin.value()
                }
        else:
            # Fallback to original behavior
            transformations['scale'] = {
                'factor': self.scale_slider.value() / 100.0
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
            
        # Ensure barcode type formatting is consistent regardless of how it's stored in dropdown
        barcode_type = self.barcode_combo.currentText()
        
        # Create transformations dict
        transformations = {
            'rotation': {'angle': self.rotation_slider.value()},
            'center': {'width': 800, 'height': 600}
        }
        
        # Add scale transformation based on selected type
        if hasattr(self, 'scale_type_combo'):
            if self.scale_type_combo.currentIndex() == 0:
                # Relative scaling
                transformations['scale'] = {
                    'factor': self.scale_slider.value() / 100.0
                }
            else:
                # Absolute scaling (mm)
                transformations['scale'] = {
                    'width_mm': self.width_mm_spin.value()
                }
        else:
            # Fallback to original behavior
            transformations['scale'] = {
                'factor': self.scale_slider.value() / 100.0
            }
        
        return TestConfig(
            barcode_type=barcode_type,
            image_paths=self.barcode_images,
            delay_between_images=0.5,
            transformations=transformations
        )