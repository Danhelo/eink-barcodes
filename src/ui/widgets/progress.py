# src/ui/widgets/progress.py
from PyQt5.QtWidgets import QProgressBar
from PyQt5.QtCore import Qt, pyqtSlot
import logging
import time

logger = logging.getLogger(__name__)

class EnhancedProgressBar(QProgressBar):
    """
    Enhanced progress bar with throttling and better status display.
    
    This widget improves on the standard QProgressBar with:
    - Throttled updates to improve performance
    - Better status message handling
    - Automatic visibility management
    """
    
    def __init__(self, parent=None):
        """Initialize the progress bar.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.setTextVisible(True)
        self.setAlignment(Qt.AlignCenter)
        self.setFormat("%p% - %v")
        self.setMinimum(0)
        self.setMaximum(100)
        self.setValue(0)
        
        # For throttling updates
        self._last_update_time = 0
        self._last_message = ""
        self._visible_when_zero = False
        
    @pyqtSlot(float, str)
    def update_progress(self, value, message=""):
        """Update progress bar with value and message.
        
        Args:
            value: Progress value (0.0-1.0)
            message: Status message
            
        Returns:
            bool: True if progress was actually updated
        """
        try:
            # Convert to percentage (0-100)
            percent = int(value * 100)
            
            # Throttle updates to improve performance
            current_time = time.time()
            message_changed = message != self._last_message
            
            # Only update UI if:
            # 1. It's been more than 100ms since last update
            # 2. OR the progress change is significant
            # 3. OR the message has changed
            # 4. OR it's an important milestone (0, 25, 50, 75, 100%)
            should_update = (
                current_time - self._last_update_time > 0.1 or
                abs(percent - self.value()) >= 5 or
                message_changed or
                percent in [0, 25, 50, 75, 100]
            )
            
            if not should_update:
                return False
                
            # Update time and message
            self._last_update_time = current_time
            self._last_message = message
            
            # Update value
            self.setValue(percent)
            
            # Update format with message
            if message:
                self.setFormat(f"{percent}% - {message}")
            else:
                self.setFormat(f"{percent}%")
                
            # Manage visibility
            self._update_visibility(percent)
            return True
            
        except Exception as e:
            logger.error(f"Error updating progress bar: {e}")
            return False
            
    def _update_visibility(self, percent):
        """Update visibility based on progress.
        
        Args:
            percent: Progress percentage (0-100)
        """
        # Show when progress is non-zero or when explicitly enabled
        if percent > 0 or self._visible_when_zero:
            self.setVisible(True)
        else:
            self.setVisible(False)
            
    def set_visible_when_zero(self, visible):
        """Set whether to show progress bar when at 0%.
        
        Args:
            visible: True to show at 0%, False to hide
        """
        self._visible_when_zero = visible
        self._update_visibility(self.value())
        
    def reset(self):
        """Reset the progress bar."""
        super().reset()
        self._last_message = ""
        self.setFormat("%p%")
        self._update_visibility(0)