# src/ui/widgets/preview.py
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt, pyqtSlot
import logging
import numpy as np
from PIL import Image
import os

logger = logging.getLogger(__name__)

class PreviewWidget(QWidget):
    """
    Widget for displaying image previews with transformations.
    
    This widget shows real-time previews of barcodes with
    transformations that will be applied during the test.
    """
    
    def __init__(self, parent=None, transform_pipeline=None):
        """Initialize preview widget.
        
        Args:
            parent: Parent widget
            transform_pipeline: Optional transformation pipeline
        """
        super().__init__(parent)
        self._original_image = None
        self._current_path = None
        self._transform_pipeline = transform_pipeline
        self._setup_ui()
        
    def _setup_ui(self):
        """Set up the UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Preview label
        self.preview_label = QLabel("No image selected")
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setMinimumSize(300, 200)
        self.preview_label.setStyleSheet("""
            QLabel {
                background-color: #333333;
                border: 1px solid #555555;
                color: #CCCCCC;
            }
        """)
        
        layout.addWidget(self.preview_label)
        
    def set_transform_pipeline(self, pipeline):
        """Set the transformation pipeline.
        
        Args:
            pipeline: Transformation pipeline to use
        """
        self._transform_pipeline = pipeline
        # Update preview if we have an image
        if self._original_image:
            self.update_preview()
            
    def load_image(self, path):
        """Load an image from path.
        
        Args:
            path: Path to image file
        
        Returns:
            bool: True if successful, False otherwise
        """
        if not path or not os.path.exists(path):
            logger.error(f"Image not found: {path}")
            self.clear()
            return False
            
        try:
            # Load image with PIL and convert to grayscale
            self._original_image = Image.open(path).convert('L')
            self._current_path = path
            
            # Update preview
            self.update_preview()
            return True
            
        except Exception as e:
            logger.error(f"Error loading image {path}: {e}")
            self.clear()
            return False
            
    @pyqtSlot(dict)
    def update_preview(self, transformations=None):
        """Update preview with current transformations.
        
        Args:
            transformations: Dictionary of transformations to apply
        """
        if not self._original_image:
            return
            
        if not self._transform_pipeline:
            # No pipeline, just show original
            self._display_image(self._original_image)
            return
            
        try:
            # Apply transformations if provided
            if transformations:
                transformed = self._transform_pipeline.transform(
                    self._original_image, transformations)
                self._display_image(transformed)
                
        except Exception as e:
            logger.error(f"Error applying transformations: {e}")
            # Show original as fallback
            self._display_image(self._original_image)
            
    def _display_image(self, image):
        """Convert PIL image to QPixmap and display.
        
        Args:
            image: PIL Image to display
        """
        try:
            # Convert PIL Image to numpy array
            img_array = np.array(image)
            height, width = img_array.shape if len(img_array.shape) == 2 else img_array.shape[:2]
            
            # Create QImage from numpy array
            if len(img_array.shape) == 2:
                # Grayscale image
                bytes_per_line = width
                q_image = QImage(img_array.data, width, height, 
                                bytes_per_line, QImage.Format_Grayscale8)
            else:
                # RGB image
                bytes_per_line = 3 * width
                q_image = QImage(img_array.data, width, height,
                                bytes_per_line, QImage.Format_RGB888)
                
            # Create pixmap and scale to fit label
            pixmap = QPixmap.fromImage(q_image)
            
            # Calculate size to maintain aspect ratio
            label_size = self.preview_label.size()
            scaled_pixmap = pixmap.scaled(
                label_size, 
                Qt.KeepAspectRatio, 
                Qt.SmoothTransformation
            )
            
            # Set pixmap
            self.preview_label.setPixmap(scaled_pixmap)
            self.preview_label.setAlignment(Qt.AlignCenter)
            
        except Exception as e:
            logger.error(f"Error displaying image: {e}")
            self.preview_label.setText(f"Error: {str(e)}")
            
    def clear(self):
        """Clear the current preview."""
        self._original_image = None
        self._current_path = None
        self.preview_label.clear()
        self.preview_label.setText("No image selected")
        
    def get_current_path(self):
        """Get the path to the currently displayed image."""
        return self._current_path
        
    def resizeEvent(self, event):
        """Handle resize events to keep preview scaled properly."""
        super().resizeEvent(event)
        if self._original_image:
            # Re-display with current size
            self.update_preview()