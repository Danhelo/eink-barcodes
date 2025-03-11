# src/ui/widgets/preview.py
from PyQt5.QtWidgets import QFrame, QVBoxLayout, QLabel, QSizePolicy
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt, pyqtSlot, QSize
import logging
import numpy as np
from PIL import Image
import os

logger = logging.getLogger(__name__)

class PreviewWidget(QFrame):  # Using QFrame for better visual control
    """
    Widget for displaying image previews with transformations.
    
    This widget shows real-time previews of barcodes with
    transformations that will be applied during the test.
    """
    
    def __init__(self, parent=None, transform_pipeline=None):
        """Initialize preview widget."""
        super().__init__(parent)
        self._original_image = None
        self._current_path = None
        self._transform_pipeline = transform_pipeline
        self._original_pixmap = None
        self._last_transformations = None
        self._setup_ui()
        
    def _setup_ui(self):
        """Set up the UI components."""
        # Style the frame with a subtle border and dark background
        self.setFrameStyle(QFrame.Panel | QFrame.Sunken)
        self.setLineWidth(1)
        self.setStyleSheet("background-color: #2D2D2D;")
        
        # Make sure the widget can expand
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # Create a simple layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)  # Small margins for padding
        layout.setSpacing(0)
        
        # Preview label
        self.preview_label = QLabel("No image selected")
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setStyleSheet("color: #CCCCCC; border: none;")
        
        # Critical: Use Ignored size policy to prevent layout fighting
        self.preview_label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        
        layout.addWidget(self.preview_label)
        
    def set_transform_pipeline(self, pipeline):
        """Set the transformation pipeline."""
        self._transform_pipeline = pipeline
        # Update the preview if we have an image and transformations
        if self._original_image and self._last_transformations:
            self.update_preview(self._last_transformations)
            
    def load_image(self, path):
        """Load an image from file."""
        if not path or not os.path.exists(path):
            logger.error(f"Image not found: {path}")
            self.clear()
            return False
            
        try:
            # Load image with PIL
            self._original_image = Image.open(path)
            self._current_path = path
            
            # Apply any previous transformations or just show original
            if self._last_transformations:
                self.update_preview(self._last_transformations)
            else:
                self._display_image(self._original_image)
                
            return True
            
        except Exception as e:
            logger.error(f"Error loading image {path}: {e}")
            self.clear()
            return False
    
    @pyqtSlot(dict)        
    def update_preview(self, transformations=None):
        """Update the preview with transformations."""
        if not self._original_image:
            return
            
        # Store transformations for reuse
        if transformations:
            self._last_transformations = transformations
            
        try:
            # Apply transformations if available
            if self._last_transformations and self._transform_pipeline:
                # Always work on a copy of the original image
                transformed = self._transform_pipeline.transform(
                    self._original_image.copy(), self._last_transformations)
                self._display_image(transformed)
            else:
                # Just show the original
                self._display_image(self._original_image)
                
        except Exception as e:
            logger.error(f"Error applying transformations: {e}")
            # Fall back to original image
            self._display_image(self._original_image)
            
    def _display_image(self, image):
        """Convert PIL image to QPixmap and display it."""
        try:
            # Convert PIL Image to numpy array
            img_array = np.array(image)
            height, width = img_array.shape[:2] if len(img_array.shape) > 2 else img_array.shape
            
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
                
            # Create pixmap and store original for scaling
            self._original_pixmap = QPixmap.fromImage(q_image)
            
            # Scale and display
            self._update_pixmap_size()
            
        except Exception as e:
            logger.error(f"Error displaying image: {e}")
            self.preview_label.setText(f"Error: {str(e)}")

    def _update_pixmap_size(self):
        """Update the pixmap size for the available space."""
        if not self._original_pixmap:
            return
            
        # Get the available size for the image
        available_size = self.preview_label.size()
        
        # Only scale if we have a valid size
        if available_size.width() > 10 and available_size.height() > 10:
            # Scale pixmap to fit available space while maintaining aspect ratio
            scaled_pixmap = self._original_pixmap.scaled(
                available_size, 
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            
            # Set the pixmap
            self.preview_label.setPixmap(scaled_pixmap)
            
    def clear(self):
        """Clear the current preview."""
        self._original_image = None
        self._current_path = None
        self._original_pixmap = None
        self._last_transformations = None
        self.preview_label.clear()
        self.preview_label.setText("No image selected")
        
    def get_current_path(self):
        """Get the path to the currently displayed image."""
        return self._current_path
    
    def sizeHint(self):
        """Provide a recommended size for the widget."""
        return QSize(400, 300)
    
    def minimumSizeHint(self):
        """Provide a minimum size for the widget."""
        return QSize(200, 150)
        
    def resizeEvent(self, event):
        """Handle resize events to update the image display."""
        super().resizeEvent(event)
        self._update_pixmap_size()