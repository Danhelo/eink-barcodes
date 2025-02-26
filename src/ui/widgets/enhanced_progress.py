"""
Enhanced progress bar implementation with efficient progress display.
"""
from PyQt5.QtWidgets import QProgressBar
from PyQt5.QtCore import Qt
import logging
import time
from typing import Optional

logger = logging.getLogger(__name__)

class EnhancedProgressBar(QProgressBar):
    """Enhanced progress bar with improved styling and throttled updates."""
    
    def __init__(self, parent=None):
        """Initialize enhanced progress bar.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.setTextVisible(True)
        self.setAlignment(Qt.AlignCenter)
        self.setMinimumHeight(30)
        self.setFixedHeight(30)
        self.setFormat("%p%")
        self.setRange(0, 100)
        self.setValue(0)
        self._last_update_time = 0
        self._visible_when_zero = False
        
    def updateProgress(self, value: float, message: str = "") -> bool:
        """Update progress with throttling and proper formatting.
        
        Args:
            value: Progress value (0.0-1.0)
            message: Optional message to display
            
        Returns:
            bool: True if progress was actually updated
        """
        try:
            # Convert to percentage
            percent = int(value * 100)
            
            # Throttle updates for better performance but ensure important updates are displayed
            current_time = time.time()
            
            # Always update if:
            # 1. It's been more than 100ms since last update (REDUCED from 250ms for more responsive updates)
            # 2. OR the change in percentage is significant (≥1%)
            # 3. OR message has changed
            # 4. OR it's the first update (0%), any 25% milestone, or final update (100%)
            should_update = (
                current_time - self._last_update_time > 0.1 or      # REDUCED Time-based threshold
                abs(percent - self.value()) >= 1 or                # Value change threshold
                message != self.text() or                          # Message changed
                percent in (0, 25, 50, 75, 100) or                 # Important milestones
                percent == 0 or percent == 100                     # Start/end of process
            )
            
            # Store current values regardless of throttling for visual tracking
            current_percent = self.value()
            
            if not should_update:
                # CRITICAL FIX: Even when throttled, we should update visuals
                # if there's any change at all, just don't reset the timer
                if percent != current_percent:
                    self.setValue(percent)
                    # Force repaint even for throttled updates
                    self.repaint()
                return False
                
            # Store last update time
            self._last_update_time = current_time
            
            # Update value
            self.setValue(percent)
            
            # Update format
            if message:
                # Keep message brief, extract filename if it's a path
                if '/' in message and len(message) > 30:
                    display_message = message.split('/')[-1]
                    self.setFormat(f"{percent}% - {display_message}")
                else:
                    self.setFormat(f"{percent}% - {message}")
            else:
                self.setFormat(f"{percent}%")
                
            # Manage visibility based on progress
            self._updateVisibility(percent)
                
            # CRITICAL FIX: Force immediate update and ensure it happens
            # This ensures the progress bar visually updates immediately
            self.repaint()
                
            return True
                
        except Exception as e:
            logger.error(f"Error updating progress bar: {e}")
            return False
            
    def _updateVisibility(self, percent: int):
        """Update visibility based on progress value.
        
        Args:
            percent: Progress percentage (0-100)
        """
        # Show when progress is non-zero or when explicitly configured
        should_show = percent > 0 or self._visible_when_zero
        
        if should_show:
            self.show()
        else:
            self.hide()
            
    def reset(self):
        """Reset progress to zero."""
        self.setValue(0)
        self.setFormat("0%")
        self._updateVisibility(0)
        
    def setVisibleWhenZero(self, visible: bool):
        """Set whether progress bar should be visible when progress is zero.
        
        Args:
            visible: True to show even at 0%
        """
        self._visible_when_zero = visible
        self._updateVisibility(self.value())