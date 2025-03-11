# src/ui/pages/custom_page.py
from PyQt5.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QListWidget, QPushButton,
    QGroupBox, QSpinBox, QDoubleSpinBox, QCheckBox, QFileDialog,
    QMessageBox, QListWidgetItem, QComboBox, QWidget, QScrollArea, QFrame, QGridLayout,
    QLayout
)
from PyQt5.QtCore import Qt, pyqtSlot, Qt
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
        transforms_layout = QVBoxLayout()  # Switch back to vertical layout for simplicity
        
        # Rotation with better alignment
        rotation_layout = QHBoxLayout()
        rotation_label = QLabel("Rotation:")
        rotation_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        rotation_label.setMinimumWidth(80)
        rotation_layout.addWidget(rotation_label)

        self.rotation_spin = QSpinBox()
        self.rotation_spin.setRange(0, 360)
        self.rotation_spin.setSingleStep(15)
        self.rotation_spin.valueChanged.connect(self.on_settings_changed)
        rotation_layout.addWidget(self.rotation_spin)

        degrees_label = QLabel("degrees")
        degrees_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        degrees_label.setMinimumWidth(60)
        rotation_layout.addWidget(degrees_label)

        transforms_layout.addLayout(rotation_layout)
        
        # Scale group
        scale_group = QGroupBox("Scaling Options")
        scale_layout = QGridLayout()  # Use grid layout for perfect alignment
        scale_layout.setColumnStretch(1, 1)  # Make the widget column stretch
        
        # Row 0: Scale Type
        scale_type_label = QLabel("Scaling Type:")
        scale_type_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        scale_layout.addWidget(scale_type_label, 0, 0)

        self.scale_type_combo = QComboBox()
        self.scale_type_combo.addItems(["Relative (factor)", "Absolute (mm)"])
        self.scale_type_combo.currentIndexChanged.connect(self.on_scale_type_changed)
        scale_layout.addWidget(self.scale_type_combo, 0, 1)

        # Row 1: Relative Scaling (will be hidden/shown based on selection)
        scale_factor_label = QLabel("Scale Factor:")
        scale_factor_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        scale_layout.addWidget(scale_factor_label, 1, 0)

        scale_factor_layout = QHBoxLayout()
        self.scale_spin = QDoubleSpinBox()
        self.scale_spin.setRange(0.1, 5.0)
        self.scale_spin.setSingleStep(0.1)
        self.scale_spin.setDecimals(1)
        self.scale_spin.setValue(1.0)
        self.scale_spin.valueChanged.connect(self.on_settings_changed)
        scale_factor_layout.addWidget(self.scale_spin)
        scale_factor_layout.addWidget(QLabel("x"))
        scale_factor_layout.addStretch(1)  # Add stretch to align left
        scale_layout.addLayout(scale_factor_layout, 1, 1)

        # Row 2: Absolute Scaling (will be hidden/shown based on selection)
        width_label = QLabel("Width:")
        width_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        scale_layout.addWidget(width_label, 2, 0)

        width_layout = QHBoxLayout()
        self.width_mm_spin = QDoubleSpinBox()
        self.width_mm_spin.setRange(5.0, 200.0)
        self.width_mm_spin.setSingleStep(1.0)
        self.width_mm_spin.setDecimals(1)
        self.width_mm_spin.setValue(20.0)
        self.width_mm_spin.setSuffix(" mm")
        self.width_mm_spin.valueChanged.connect(self.on_settings_changed)
        width_layout.addWidget(self.width_mm_spin)
        width_layout.addStretch(1)  # Add stretch to align left
        scale_layout.addLayout(width_layout, 2, 1)

        scale_group.setLayout(scale_layout)
        transforms_layout.addWidget(scale_group)

        # Store references to rows instead of widgets for visibility control
        self.scale_factor_row = [scale_factor_label, scale_factor_layout]
        self.width_mm_row = [width_label, width_layout]

        # Initially show the right widgets based on combo selection
        self.on_scale_type_changed(self.scale_type_combo.currentIndex())
        
        # Checkboxes with better spacing
        checkbox_layout = QVBoxLayout()
        checkbox_layout.setSpacing(10)  # Add space between checkboxes

        # Mirror
        self.mirror_check = QCheckBox("Mirror Horizontally")
        self.mirror_check.stateChanged.connect(self.on_settings_changed)
        checkbox_layout.addWidget(self.mirror_check)

        # Auto-center
        self.center_check = QCheckBox("Auto-center on Display")
        self.center_check.setChecked(True)
        self.center_check.stateChanged.connect(self.on_settings_changed)
        checkbox_layout.addWidget(self.center_check)

        transforms_layout.addLayout(checkbox_layout)
        transforms_group.setLayout(transforms_layout)
        
        # Test execution controls with better alignment
        execution_group = QGroupBox("Execution")
        execution_layout = QGridLayout()  # Use grid layout for consistent alignment
        execution_layout.setColumnStretch(1, 1)  # Make the control column stretch

        # Delay with better alignment - row 0
        delay_label = QLabel("Delay:")
        delay_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        delay_label.setMinimumWidth(80)
        execution_layout.addWidget(delay_label, 0, 0)

        delay_input_layout = QHBoxLayout()
        self.delay_spin = QDoubleSpinBox()
        self.delay_spin.setRange(0.1, 10.0)
        self.delay_spin.setSingleStep(0.1)
        self.delay_spin.setDecimals(1)
        self.delay_spin.setValue(1.0)
        delay_input_layout.addWidget(self.delay_spin)
        delay_input_layout.addWidget(QLabel("seconds"))
        delay_input_layout.addStretch(1)  # Add stretch to align left
        execution_layout.addLayout(delay_input_layout, 0, 1)

        # Repetitions with better alignment - row 1
        repeat_label = QLabel("Repetitions:")
        repeat_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        repeat_label.setMinimumWidth(80)
        execution_layout.addWidget(repeat_label, 1, 0)

        repeat_input_layout = QHBoxLayout()
        self.repeat_spin = QSpinBox()
        self.repeat_spin.setRange(1, 10)
        self.repeat_spin.setValue(1)
        repeat_input_layout.addWidget(self.repeat_spin)
        repeat_input_layout.addStretch(1)  # Add stretch to align left
        execution_layout.addLayout(repeat_input_layout, 1, 1)

        execution_group.setLayout(execution_layout)
        settings_inner_layout.addWidget(transforms_group)
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
        """Handle scale type selector change."""
        if index == 0:  # Relative (factor)
            # Show scale factor, hide width mm
            for widget in self.scale_factor_row:
                if isinstance(widget, QLayout):
                    for i in range(widget.count()):
                        item = widget.itemAt(i).widget()
                        if item:
                            item.setVisible(True)
                else:
                    widget.setVisible(True)
                
            for widget in self.width_mm_row:
                if isinstance(widget, QLayout):
                    for i in range(widget.count()):
                        item = widget.itemAt(i).widget()
                        if item:
                            item.setVisible(False)
                else:
                    widget.setVisible(False)
        else:  # Absolute (mm)
            # Hide scale factor, show width mm
            for widget in self.scale_factor_row:
                if isinstance(widget, QLayout):
                    for i in range(widget.count()):
                        item = widget.itemAt(i).widget()
                        if item:
                            item.setVisible(False)
                else:
                    widget.setVisible(False)
                
            for widget in self.width_mm_row:
                if isinstance(widget, QLayout):
                    for i in range(widget.count()):
                        item = widget.itemAt(i).widget()
                        if item:
                            item.setVisible(True)
                else:
                    widget.setVisible(True)
        
        # Update the preview with the new settings
        self.update_preview()

    def update_preview(self):
        """Update preview with current settings."""
        transformations = {}
        
        # Add rotation if the spin control exists
        if hasattr(self, 'rotation_spin'):
            transformations['rotation'] = {
                'angle': self.rotation_spin.value()
            }
        
        # Add scale transformation based on selected type
        if hasattr(self, 'scale_type_combo') and hasattr(self, 'scale_spin') and hasattr(self, 'width_mm_spin'):
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
        elif hasattr(self, 'scale_spin'):
            # Fallback to original behavior
            transformations['scale'] = {
                'factor': self.scale_spin.value()
            }
        
        # Add mirror if the checkbox exists
        if hasattr(self, 'mirror_check') and self.mirror_check.isChecked():
            transformations['mirror'] = {'horizontal': True}
            
        # Add center if the checkbox exists
        if hasattr(self, 'center_check') and self.center_check.isChecked():
            transformations['center'] = {'width': 800, 'height': 600}
        
        # Only update if we have a preview
        if hasattr(self, 'preview') and self.preview:
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