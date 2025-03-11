# src/ui/pages/quick_page.py
from PyQt5.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QGroupBox, QSlider, QMessageBox, QDoubleSpinBox, QWidget,
    QScrollArea, QSplitter, QSizePolicy
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
        # Make the layout compact
        content = QVBoxLayout()
        content.setSpacing(8)
        
        # Barcode type selection
        type_group = QGroupBox("Barcode Type")
        type_group.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)  # Don't expand vertically
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
        transform_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)  # Allow horizontal expansion
        transform_layout = QVBoxLayout()
        
        # Rotation control
        rotation_group = QGroupBox("Rotation")
        rotation_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)  # Don't expand vertically
        rotation_layout = QHBoxLayout()
        
        rotation_layout.addWidget(QLabel("Angle:"))
        self.rotation_slider = QSlider(Qt.Horizontal)
        self.rotation_slider.setRange(0, 360)
        self.rotation_slider.setTickInterval(45)
        self.rotation_slider.setTickPosition(QSlider.TicksBelow)
        self.rotation_slider.setValue(0)
        self.rotation_slider.valueChanged.connect(self.on_settings_changed)
        rotation_layout.addWidget(self.rotation_slider)
        self.rotation_value = QLabel("0°")
        self.rotation_value.setMinimumWidth(30)  # Ensure space for the text
        rotation_layout.addWidget(self.rotation_value)
        
        rotation_group.setLayout(rotation_layout)
        transform_layout.addWidget(rotation_group)
        
        # Scale control with type selector
        scale_group = QGroupBox("Scale")
        scale_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)  # Don't expand vertically
        scale_layout = QVBoxLayout()
        
        # Scale type selection
        scale_type_layout = QHBoxLayout()
        scale_type_layout.addWidget(QLabel("Scale Type:"))
        self.scale_type_combo = QComboBox()
        self.scale_type_combo.addItems(["Relative (%)", "Absolute (mm)"])
        self.scale_type_combo.currentIndexChanged.connect(self.on_scale_type_changed)
        scale_type_layout.addWidget(self.scale_type_combo)
        scale_layout.addLayout(scale_type_layout)
        
        # Relative Scaling (slider)
        self.relative_scale_widget = QWidget()
        relative_scale_layout = QHBoxLayout(self.relative_scale_widget)
        relative_scale_layout.setContentsMargins(0, 0, 0, 0)
        
        label = QLabel("Size:")
        label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        label.setMinimumWidth(40)
        relative_scale_layout.addWidget(label)
        
        self.scale_slider = QSlider(Qt.Horizontal)
        self.scale_slider.setRange(10, 200)  # 10% to 200%
        self.scale_slider.setTickInterval(10)
        self.scale_slider.setTickPosition(QSlider.TicksBelow)
        self.scale_slider.setValue(100)  # 100% default
        self.scale_slider.valueChanged.connect(self.on_settings_changed)
        relative_scale_layout.addWidget(self.scale_slider)
        
        self.scale_value = QLabel("100%")
        self.scale_value.setMinimumWidth(50)  # Ensure space for the text
        self.scale_value.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        relative_scale_layout.addWidget(self.scale_value)
        
        scale_layout.addWidget(self.relative_scale_widget)

        # Absolute Scaling (mm input)
        self.absolute_scale_widget = QWidget()
        absolute_scale_layout = QHBoxLayout(self.absolute_scale_widget)
        absolute_scale_layout.setContentsMargins(0, 0, 0, 0)
        
        label = QLabel("Width:")
        label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        label.setMinimumWidth(40)
        absolute_scale_layout.addWidget(label)
        
        self.width_mm_spin = QDoubleSpinBox()
        self.width_mm_spin.setRange(5.0, 200.0)  # 5mm to 200mm
        self.width_mm_spin.setValue(20.0)  # 20mm default
        self.width_mm_spin.setSuffix(" mm")
        self.width_mm_spin.valueChanged.connect(self.on_settings_changed)
        absolute_scale_layout.addWidget(self.width_mm_spin)
        absolute_scale_layout.addStretch()  # Add stretch to right-align the spin box
        scale_layout.addWidget(self.absolute_scale_widget)

        # Make sure to initially hide the absolute scale widget
        self.absolute_scale_widget.setVisible(False)

        scale_group.setLayout(scale_layout)
        transform_layout.addWidget(scale_group)
        
        transform_group.setLayout(transform_layout)
        content.addWidget(transform_group)
        
        # Initialize
        self.barcode_images = []
        
        # Set initial state and load images
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
        # Update rotation display
        angle = self.rotation_slider.value()
        self.rotation_value.setText(f"{angle}°")
        
        # Update scale display for relative scaling
        if hasattr(self, 'scale_type_combo') and self.scale_type_combo.currentIndex() == 0:
            scale = self.scale_slider.value()
            self.scale_value.setText(f"{scale}%")
        
        # Log changes to help with debugging
        logger.debug(f"Settings changed: rotation={angle}°, scale={self.scale_slider.value()}%")
        
        # Update the preview
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
        # Use exact same transformation structure as custom page
        transformations = {
            'rotation': {'angle': self.rotation_slider.value()}
        }
        
        # Use exact same scaling approach as custom page
        if hasattr(self, 'scale_type_combo'):
            if self.scale_type_combo.currentIndex() == 0:
                # Relative scaling - use direct division like custom page
                # Instead of slider's 10-200 range representing 10-200%
                # We'll use the actual factor directly
                transformations['scale'] = {
                    'factor': self.scale_slider.value() / 100.0  # Convert percentage to factor
                }
            else:
                # Absolute scaling (mm) - this part is the same
                transformations['scale'] = {
                    'width_mm': self.width_mm_spin.value()
                }
        else:
            transformations['scale'] = {
                'factor': self.scale_slider.value() / 100.0
            }
        
        # Always add center transformation like custom page
        transformations['center'] = {'width': 800, 'height': 600}
        
        # Debug the transformations
        logger.debug(f"Applying transformations: {transformations}")
        
        # Call preview update with complete transformation dict
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
        
        # Create transformations dict using exact same structure as update_preview
        transformations = {
            'rotation': {'angle': self.rotation_slider.value()}
        }
        
        # Match the exact same scaling approach
        if hasattr(self, 'scale_type_combo'):
            if self.scale_type_combo.currentIndex() == 0:
                # Relative scaling
                transformations['scale'] = {
                    'factor': self.scale_slider.value() / 100.0  # Convert percentage to factor
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
        
        # Always include center transformation
        transformations['center'] = {'width': 800, 'height': 600}
        
        return TestConfig(
            barcode_type=barcode_type,
            image_paths=self.barcode_images,
            delay_between_images=0.5,
            transformations=transformations
        )