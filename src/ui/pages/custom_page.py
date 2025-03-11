# src/ui/pages/custom_page.py
from PyQt5.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QListWidget, QPushButton,
    QGroupBox, QSpinBox, QDoubleSpinBox, QCheckBox, QFileDialog,
    QMessageBox, QListWidgetItem, QComboBox, QWidget, QScrollArea, QFrame
)
from PyQt5.QtCore import Qt, pyqtSlot
import logging
import os

from .base_page import BasePage
from ...core.config import TestConfig

logger = logging.getLogger(__name__)

class CustomTestPage(BasePage):
    """
    Custom test page with advanced options.
    
    This page provides full control over all test parameters:
    - Individual image selection
    - Detailed transformation controls
    - Test execution parameters
    """
    
    PAGE_TITLE = "Custom Test"
    
    def _create_content(self):
        """Create custom test controls."""
        content = QVBoxLayout()
        
        # Split into two columns
        main_layout = QHBoxLayout()
        
        # Left column: Image selection
        image_group = QGroupBox("Image Selection")
        image_layout = QVBoxLayout()
        
        # Image list
        self.image_list = QListWidget()
        self.image_list.setSelectionMode(QListWidget.ExtendedSelection)
        self.image_list.itemSelectionChanged.connect(self.on_selection_changed)
        self.image_list.setMinimumHeight(150)  # Ensure a reasonable minimum height
        image_layout.addWidget(self.image_list)
        
        # Image controls
        image_buttons = QHBoxLayout()
        
        self.add_button = QPushButton("Add Files")
        self.add_button.clicked.connect(self.on_add_files)
        image_buttons.addWidget(self.add_button)
        
        self.remove_button = QPushButton("Remove Selected")
        self.remove_button.clicked.connect(self.on_remove_files)
        image_buttons.addWidget(self.remove_button)
        
        image_layout.addLayout(image_buttons)
        image_group.setLayout(image_layout)
        main_layout.addWidget(image_group, 1)  # Give weight of 1 to the image section
        
        # Right column: Test settings (in a scroll area to handle more complex controls)
        settings_scroll = QScrollArea()
        settings_scroll.setWidgetResizable(True)
        settings_scroll.setFrameShape(QFrame.NoFrame)
        
        settings_container = QWidget()
        settings_layout = QVBoxLayout(settings_container)
        
        settings_group = QGroupBox("Test Settings")
        settings_inner_layout = QVBoxLayout()
        
        # Transformation controls
        transforms_group = QGroupBox("Transformations")
        transforms_layout = QVBoxLayout()
        
        # Rotation
        rotation_layout = QHBoxLayout()
        rotation_layout.addWidget(QLabel("Rotation:"))
        self.rotation_spin = QSpinBox()
        self.rotation_spin.setRange(0, 360)
        self.rotation_spin.setSingleStep(15)
        self.rotation_spin.valueChanged.connect(self.on_settings_changed)
        rotation_layout.addWidget(self.rotation_spin)
        rotation_layout.addWidget(QLabel("degrees"))
        transforms_layout.addLayout(rotation_layout)

        scale_group = QGroupBox("Scaling Options")
        scale_layout = QVBoxLayout()

        # Scale Type Selection
        scale_type_layout = QHBoxLayout()
        scale_type_layout.addWidget(QLabel("Scaling Type:"))
        self.scale_type_combo = QComboBox()
        self.scale_type_combo.addItems(["Relative (factor)", "Absolute (mm)"])
        self.scale_type_combo.currentIndexChanged.connect(self.on_scale_type_changed)
        scale_type_layout.addWidget(self.scale_type_combo)
        scale_layout.addLayout(scale_type_layout)

        # Relative Scaling (spinner) - in a container widget
        self.relative_scale_widget = QWidget()
        relative_scale_layout = QHBoxLayout(self.relative_scale_widget)
        relative_scale_layout.setContentsMargins(0, 0, 0, 0)
        relative_scale_layout.addWidget(QLabel("Scale Factor:"))
        self.scale_spin = QDoubleSpinBox()
        self.scale_spin.setRange(0.1, 5.0)
        self.scale_spin.setSingleStep(0.1)
        self.scale_spin.setDecimals(1)
        self.scale_spin.setValue(1.0)
        self.scale_spin.valueChanged.connect(self.on_settings_changed)
        relative_scale_layout.addWidget(self.scale_spin)
        relative_scale_layout.addWidget(QLabel("x"))
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
        transforms_layout.addWidget(scale_group)
        
        # Mirror
        self.mirror_check = QCheckBox("Mirror Horizontally")
        self.mirror_check.stateChanged.connect(self.on_settings_changed)
        transforms_layout.addWidget(self.mirror_check)
        
        # Auto-center
        self.center_check = QCheckBox("Auto-center on Display")
        self.center_check.setChecked(True)
        self.center_check.stateChanged.connect(self.on_settings_changed)
        transforms_layout.addWidget(self.center_check)
        
        transforms_group.setLayout(transforms_layout)
        settings_inner_layout.addWidget(transforms_group)
        
        # Test execution controls
        execution_group = QGroupBox("Execution")
        execution_layout = QVBoxLayout()
        
        # Delay
        delay_layout = QHBoxLayout()
        delay_layout.addWidget(QLabel("Delay:"))
        self.delay_spin = QDoubleSpinBox()
        self.delay_spin.setRange(0.1, 10.0)
        self.delay_spin.setSingleStep(0.1)
        self.delay_spin.setDecimals(1)
        self.delay_spin.setValue(1.0)
        delay_layout.addWidget(self.delay_spin)
        delay_layout.addWidget(QLabel("seconds"))
        execution_layout.addLayout(delay_layout)
        
        # Repetitions
        repeat_layout = QHBoxLayout()
        repeat_layout.addWidget(QLabel("Repetitions:"))
        self.repeat_spin = QSpinBox()
        self.repeat_spin.setRange(1, 10)
        self.repeat_spin.setValue(1)
        repeat_layout.addWidget(self.repeat_spin)
        execution_layout.addLayout(repeat_layout)
        
        execution_group.setLayout(execution_layout)
        settings_inner_layout.addWidget(execution_group)
        
        # Fill remaining space
        settings_inner_layout.addStretch()
        
        settings_group.setLayout(settings_inner_layout)
        settings_layout.addWidget(settings_group)
        settings_scroll.setWidget(settings_container)
        
        main_layout.addWidget(settings_scroll, 1)  # Give equal weight to settings
        
        content.addLayout(main_layout)

        # Load initial images
        self.load_images_from_dir('examples')
        
        return content
        
    def load_images_from_dir(self, directory):
        """Load all images recursively from a directory into the list."""
        if not os.path.exists(directory):
            logger.warning(f"Directory not found: {directory}")
            return
            
        self.image_list.clear()
        
        # Recursively find images in the directory
        for root, _, files in os.walk(directory):
            for file in files:
                if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                    path = os.path.join(root, file)
                    # Use relative path for display if inside the directory
                    display_name = os.path.relpath(path, directory)
                    item = QListWidgetItem(display_name)
                    item.setData(Qt.UserRole, path)
                    self.image_list.addItem(item)
                
        logger.info(f"Loaded {self.image_list.count()} images recursively from {directory}")
        
        # Select first item
        if self.image_list.count() > 0:
            self.image_list.setCurrentRow(0)
            
    @pyqtSlot()
    def on_add_files(self):
        """Handle add files button click."""
        files, _ = QFileDialog.getOpenFileNames(
            self, "Select Barcode Images", "",
            "Images (*.png *.jpg *.jpeg)"
        )
        
        if not files:
            return
            
        for file in files:
            name = os.path.basename(file)
            item = QListWidgetItem(name)
            item.setData(Qt.UserRole, file)
            self.image_list.addItem(item)
            
        # Select first item if none selected
        if not self.image_list.selectedItems() and self.image_list.count() > 0:
            self.image_list.setCurrentRow(0)
            
    @pyqtSlot()
    def on_remove_files(self):
        """Handle remove files button click."""
        selected = self.image_list.selectedItems()
        if not selected:
            return
            
        for item in selected:
            row = self.image_list.row(item)
            self.image_list.takeItem(row)
            
    def on_selection_changed(self):
        """Handle selection change in image list."""
        selected = self.image_list.selectedItems()
        if not selected:
            self.preview.clear()
            return
            
        # Use first selected item for preview
        path = selected[0].data(Qt.UserRole)
        self.preview.load_image(path)
        self.update_preview()
        
    def on_settings_changed(self):
        """Handle settings changes."""
        self.update_preview()
        
    def on_scale_type_changed(self, index):
        """Handle switching between relative and absolute scaling."""
        is_relative = index == 0
        self.relative_scale_widget.setVisible(is_relative)
        self.absolute_scale_widget.setVisible(not is_relative)
        self.update_preview()

    def update_preview(self):
        """Update preview with current settings."""
        transformations = {
            'rotation': {
                'angle': self.rotation_spin.value()
            }
        }
        
        # Add scale transformation based on selected type
        if hasattr(self, 'scale_type_combo'):
            if self.scale_type_combo.currentIndex() == 0:
                # Relative scaling
                transformations['scale'] = {
                    'factor': self.scale_spin.value()
                }
            else:
                # Absolute scaling (mm)
                transformations['scale'] = {
                    'width_mm': self.width_mm_spin.value()
                }
        else:
            # Fallback to original behavior
            transformations['scale'] = {
                'factor': self.scale_spin.value()
            }
        
        if self.mirror_check.isChecked():
            transformations['mirror'] = {'horizontal': True}
            
        if self.center_check.isChecked():
            transformations['center'] = {'width': 800, 'height': 600}
            
        self.preview.update_preview(transformations)

    def get_test_config(self):
        """Get test configuration from UI settings."""
        # Get selected image paths
        selected = self.image_list.selectedItems()
        if not selected:
            QMessageBox.warning(
                self, "No Images Selected",
                "Please select at least one image for testing."
            )
            return None
            
        image_paths = []
        for item in selected:
            path = item.data(Qt.UserRole)
            image_paths.append(path)
            
        # Repeat if needed
        repetitions = self.repeat_spin.value()
        if repetitions > 1:
            original_paths = image_paths.copy()
            for _ in range(repetitions - 1):
                image_paths.extend(original_paths)
                
        # Create transformations dict
        transformations = {
            'rotation': {'angle': self.rotation_spin.value()}
        }
        
        # Add scale transformation based on selected type
        if hasattr(self, 'scale_type_combo'):
            if self.scale_type_combo.currentIndex() == 0:
                # Relative scaling
                transformations['scale'] = {
                    'factor': self.scale_spin.value()
                }
            else:
                # Absolute scaling (mm)
                transformations['scale'] = {
                    'width_mm': self.width_mm_spin.value()
                }
        else:
            # Fallback to original behavior
            transformations['scale'] = {
                'factor': self.scale_spin.value()
            }
        
        if self.mirror_check.isChecked():
            transformations['mirror'] = {'horizontal': True}
            
        if self.center_check.isChecked():
            transformations['center'] = {'width': 800, 'height': 600}
            
        return TestConfig(
            barcode_type="Custom",
            image_paths=image_paths,
            delay_between_images=self.delay_spin.value(),
            transformations=transformations
        )