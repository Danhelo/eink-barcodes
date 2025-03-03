# src/ui/pages/generate_page.py
from PyQt5.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QSpinBox,
    QGroupBox, QCheckBox, QLineEdit, QTabWidget, QPushButton,
    QMessageBox, QFileDialog, QGridLayout, QWidget
)
from PyQt5.QtCore import Qt, pyqtSlot
import logging
import os
import json
import asyncio

from .base_page import BasePage

logger = logging.getLogger(__name__)

class BarcodeGeneratePage(BasePage):
    """
    Barcode generation page for creating custom barcode images.
    
    This page provides an interface for generating various barcode types:
    - Configure barcode types, quantities, and prefixes
    - Set transformation effects
    - Generate and save barcodes to examples directory
    """
    
    PAGE_TITLE = "Generate Barcodes"
    
    # Available barcode types from the API
    BARCODE_TYPES = ["code128", "upca", "upce", "datamatrix"]
    
    # Available transformation effects
    TRANSFORM_EFFECTS = ["none", "blur", "noise", "rotate", "perspective"]
    
    def _create_content(self):
        """Create barcode generation controls."""
        content = QVBoxLayout()
        
        # Tabs for different barcode configurations
        self.tab_widget = QTabWidget()
        
        # First tab - single barcode type
        self.single_tab = QWidget()
        self.tab_widget.addTab(self.single_tab, "Single Type")
        self._create_single_tab()
        
        # Second tab - multiple barcode types
        self.multi_tab = QWidget()
        self.tab_widget.addTab(self.multi_tab, "Multiple Types")
        self._create_multi_tab()
        
        content.addWidget(self.tab_widget)
        
        # Advanced options
        advanced_group = QGroupBox("Advanced Options")
        advanced_layout = QGridLayout()
        
        advanced_layout.addWidget(QLabel("DPI:"), 0, 0)
        self.dpi_spin = QSpinBox()
        self.dpi_spin.setRange(72, 600)
        self.dpi_spin.setValue(300)
        self.dpi_spin.setSingleStep(72)
        advanced_layout.addWidget(self.dpi_spin, 0, 1)
        
        advanced_group.setLayout(advanced_layout)
        content.addWidget(advanced_group)
        
        # Output directory selection
        dir_group = QGroupBox("Output Location")
        dir_layout = QHBoxLayout()
        
        dir_layout.addWidget(QLabel("Save to:"))
        self.dir_path = QLineEdit("examples")
        self.dir_path.setReadOnly(True)
        dir_layout.addWidget(self.dir_path, 1)
        
        self.browse_btn = QPushButton("Browse...")
        self.browse_btn.clicked.connect(self.on_browse)
        dir_layout.addWidget(self.browse_btn)
        
        dir_group.setLayout(dir_layout)
        content.addWidget(dir_group)
        
        # Preview controls
        preview_controls = QHBoxLayout()
        
        self.preview_label = QLabel("Preview:")
        preview_controls.addWidget(self.preview_label)
        
        self.refresh_preview_btn = QPushButton("Refresh Preview")
        self.refresh_preview_btn.clicked.connect(self.on_refresh_preview)
        preview_controls.addWidget(self.refresh_preview_btn)
        
        preview_controls.addStretch()
        
        # This button will be shown only after generation
        self.view_results_button = QPushButton("View All Barcodes")
        self.view_results_button.clicked.connect(lambda: self._open_results_folder(self.dir_path.text()))
        self.view_results_button.hide()  # Hidden by default
        preview_controls.addWidget(self.view_results_button)
        
        content.addLayout(preview_controls)
        
        # Status label
        self.status_label = QLabel("Ready to generate barcodes")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("font-style: italic; color: #555555;")
        content.addWidget(self.status_label)
        
        return content
    
    def _create_single_tab(self):
        """Create the single barcode type tab."""
        layout = QVBoxLayout(self.single_tab)
        
        # Barcode type selection
        type_group = QGroupBox("Barcode Type")
        type_layout = QGridLayout()
        
        type_layout.addWidget(QLabel("Type:"), 0, 0)
        self.type_combo = QComboBox()
        self.type_combo.addItems(self.BARCODE_TYPES)
        type_layout.addWidget(self.type_combo, 0, 1)
        
        type_layout.addWidget(QLabel("Quantity:"), 1, 0)
        self.quantity_spin = QSpinBox()
        self.quantity_spin.setRange(1, 1000)
        self.quantity_spin.setValue(10)
        type_layout.addWidget(self.quantity_spin, 1, 1)
        
        type_layout.addWidget(QLabel("Prefix:"), 2, 0)
        self.prefix_edit = QLineEdit()
        self.prefix_edit.setPlaceholderText("Optional prefix for barcode values")
        type_layout.addWidget(self.prefix_edit, 2, 1)
        
        type_group.setLayout(type_layout)
        layout.addWidget(type_group)
        
        # Transformation
        transform_group = QGroupBox("Transformation")
        transform_layout = QGridLayout()
        
        transform_layout.addWidget(QLabel("Effect:"), 0, 0)
        self.transform_combo = QComboBox()
        self.transform_combo.addItems(self.TRANSFORM_EFFECTS)
        transform_layout.addWidget(self.transform_combo, 0, 1)
        
        transform_group.setLayout(transform_layout)
        layout.addWidget(transform_group)
        
        layout.addStretch()
    
    def _create_multi_tab(self):
        """Create the multiple barcode types tab."""
        layout = QVBoxLayout(self.multi_tab)
        
        # Create checkboxes for each barcode type
        types_group = QGroupBox("Barcode Types")
        types_layout = QVBoxLayout()
        
        self.type_checks = {}
        self.type_amounts = {}
        
        for barcode_type in self.BARCODE_TYPES:
            type_layout = QHBoxLayout()
            
            # Checkbox for selecting this type
            check = QCheckBox(barcode_type)
            self.type_checks[barcode_type] = check
            type_layout.addWidget(check, 1)
            
            # Quantity spinner
            type_layout.addWidget(QLabel("Quantity:"))
            amount = QSpinBox()
            amount.setRange(1, 100)
            amount.setValue(10)
            amount.setEnabled(False)
            self.type_amounts[barcode_type] = amount
            type_layout.addWidget(amount)
            
            # Enable/disable spinner based on checkbox
            check.stateChanged.connect(lambda state, s=amount, t=barcode_type: s.setEnabled(self.type_checks[t].isChecked()))
            
            types_layout.addLayout(type_layout)
        
        types_group.setLayout(types_layout)
        layout.addWidget(types_group)
        
        # Common settings
        common_group = QGroupBox("Common Settings")
        common_layout = QGridLayout()
        
        common_layout.addWidget(QLabel("Prefix:"), 0, 0)
        self.common_prefix = QLineEdit()
        self.common_prefix.setPlaceholderText("Optional common prefix")
        common_layout.addWidget(self.common_prefix, 0, 1)
        
        common_layout.addWidget(QLabel("Transformation:"), 1, 0)
        self.common_transform = QComboBox()
        self.common_transform.addItems(self.TRANSFORM_EFFECTS)
        common_layout.addWidget(self.common_transform, 1, 1)
        
        common_group.setLayout(common_layout)
        layout.addWidget(common_group)
        
        layout.addStretch()
    
    @pyqtSlot()
    def on_browse(self):
        """Handle browse button click for output directory."""
        directory = QFileDialog.getExistingDirectory(
            self, "Select Output Directory", self.dir_path.text()
        )
        
        if directory:
            self.dir_path.setText(directory)
            # Try to preview barcodes from the new directory
            self.on_refresh_preview()
            
    @pyqtSlot()
    def on_refresh_preview(self):
        """Refresh the preview with barcode images from the output directory."""
        try:
            output_dir = self.dir_path.text()
            if not os.path.exists(output_dir):
                self.status_label.setText(f"Output directory does not exist: {output_dir}")
                return
                
            # Look for barcode images
            self._preview_generated_barcodes(output_dir)
            
        except Exception as e:
            logger.error(f"Error refreshing preview: {e}")
            self.status_label.setText(f"Error refreshing preview: {str(e)}")
    
    def _get_single_config(self):
        """Get API request data for single barcode type."""
        return [{
            "img_amount": self.quantity_spin.value(),
            "symbology_type": self.type_combo.currentText(),
            "prefix": self.prefix_edit.text() if self.prefix_edit.text() else "none",
            "transformation": self.transform_combo.currentText()
        }]
    
    def _get_multi_config(self):
        """Get API request data for multiple barcode types."""
        config = []
        
        for barcode_type, check in self.type_checks.items():
            if check.isChecked():
                config.append({
                    "img_amount": self.type_amounts[barcode_type].value(),
                    "symbology_type": barcode_type,
                    "prefix": self.common_prefix.text() if self.common_prefix.text() else "none",
                    "transformation": self.common_transform.currentText()
                })
        
        return config
    
    def get_api_config(self):
        """Get the API request configuration based on current UI state."""
        if self.tab_widget.currentIndex() == 0:
            return self._get_single_config()
        else:
            return self._get_multi_config()

    def _preview_generated_barcodes(self, extract_to):
        """Preview the generated barcodes."""
        try:
            # Find barcode images in the extract directory
            barcode_files = []
            for root, _, files in os.walk(extract_to):
                for file in files:
                    if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                        barcode_files.append(os.path.join(root, file))
            
            if not barcode_files:
                logger.warning("No barcode images found for preview")
                return
                
            # Sort files to ensure consistent preview
            barcode_files.sort()
            
            # Load the first image into the preview
            if hasattr(self, 'preview') and self.preview:
                self.preview.load_image(barcode_files[0])
                
                # Update status with file count
                self.status_label.setText(f"Generated {len(barcode_files)} barcodes. Showing first image.")
                
                # Add a button to view all barcodes
                if not hasattr(self, 'view_results_button'):
                    self.view_results_button = QPushButton("View All Barcodes")
                    self.view_results_button.clicked.connect(lambda: self._open_results_folder(extract_to))
                    self.layout().insertWidget(self.layout().count() - 1, self.view_results_button)
                    self.view_results_button.show()
                else:
                    self.view_results_button.show()
        
        except Exception as e:
            logger.error(f"Error previewing barcodes: {e}")
    
    def _open_results_folder(self, folder_path):
        """Open the folder containing generated barcodes."""
        import platform
        import subprocess
        
        try:
            # Open folder based on OS
            if platform.system() == "Windows":
                os.startfile(folder_path)
            elif platform.system() == "Darwin":  # macOS
                subprocess.call(["open", folder_path])
            else:  # Linux
                subprocess.call(["xdg-open", folder_path])
                
        except Exception as e:
            logger.error(f"Error opening folder: {e}")
            QMessageBox.warning(
                self, "Failed to Open Folder", 
                f"Could not open the folder: {str(e)}\n\nManually browse to: {folder_path}"
            )
    
    async def _run_test(self):
        """Run barcode generation with current settings."""
        if self._test_running:
            return
            
        # Get API configuration
        api_config = self.get_api_config()
        
        if not api_config:
            QMessageBox.warning(
                self, "No Selection",
                "Please select at least one barcode type to generate."
            )
            return
            
        # Check total barcode count to avoid timeouts
        total_barcodes = sum(config["img_amount"] for config in api_config)
        if total_barcodes > 1000:
            reply = QMessageBox.question(
                self, "Large Request",
                f"You're requesting {total_barcodes} barcodes, which may cause timeout issues. " +
                "It's recommended to keep the total under 1000. Continue anyway?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.No:
                return
            
        # Update UI state
        self._test_running = True
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.progress.setValue(0)
        self.progress.setVisible(True)
        self.status_label.setText("Preparing request...")
        
        try:
            # Show what would be sent to API
            request_json = json.dumps(api_config, indent=2)
            logger.info(f"API Request: {request_json}")
            
            # Update progress
            self.progress.update_progress(0.2, "Generating barcodes...")
            self.status_label.setText("Sending request to barcode generation service...")
            
            # Import here to avoid circular imports
            from ..utils.barcode_api import generate_barcodes
            from ..utils.download import download_and_unzip_s3_file
            
            # Call the API service
            s3_url = await generate_barcodes(api_config)
            
            if s3_url:
                # Download and extract
                self.progress.update_progress(0.5, "Downloading barcodes...")
                self.status_label.setText("Downloading generated barcodes...")
                
                success, message = download_and_unzip_s3_file(s3_url, self.dir_path.text())
                
                if success:
                    self.progress.update_progress(1.0, "Download complete")
                    self.status_label.setText("Barcodes downloaded successfully")
                    
                    # Preview the first barcode
                    self._preview_generated_barcodes(extract_to=self.dir_path.text())
                    
                    QMessageBox.information(
                        self, "Generation Complete",
                        f"Barcodes generated and downloaded successfully.\n{message}"
                    )
                else:
                    raise RuntimeError(message)
            else:
                self.progress.update_progress(1.0, "API error")
                self.status_label.setText("Failed to get download URL from API")
                
                raise RuntimeError("Failed to get download URL from API service.")
                
        except Exception as e:
            logger.error(f"Error generating barcodes: {e}")
            QMessageBox.critical(
                self, "Generation Error", 
                f"Failed to generate barcodes: {str(e)}"
            )
            self.status_label.setText(f"Error: {str(e)}")
                
        # Update UI state
        self._test_running = False
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
            
    def get_test_config(self):
        """
        Overrides base method. We're using custom logic for barcode generation.
        """
        return None