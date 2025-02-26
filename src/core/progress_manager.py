"""
Progress manager for coordinating progress updates across components.

This module provides a thread-safe central manager for tracking and reporting
progress across different components of the application.
"""
import logging
from typing import Dict, List, Callable, Optional, Any
import time
import threading

logger = logging.getLogger(__name__)

class ProgressManager:
    """
    Thread-safe manager for progress updates across multiple components.
    
    This class provides a central point for tracking progress and notifying
    observers of progress changes. It safely coordinates updates from different
    threads and ensures consistent progress reporting.
    """
    
    def __init__(self):
        """Initialize progress manager."""
        self._observers: List[Callable[[float, str], None]] = []
        self._current_progress: float = 0.0
        self._current_message: str = ""
        self._start_time: Optional[float] = None
        self._test_id: Optional[str] = None
        self._active: bool = False
        self._lock = threading.RLock()  # Reentrant lock for thread safety
        
    def register_observer(self, observer: Callable[[float, str], None]) -> None:
        """Register an observer for progress updates.
        
        Args:
            observer: Callback function that takes progress (0.0-1.0) and message
        """
        with self._lock:
            if observer not in self._observers:
                self._observers.append(observer)
            
    def unregister_observer(self, observer: Callable[[float, str], None]) -> None:
        """Unregister an observer.
        
        Args:
            observer: Observer to unregister
        """
        with self._lock:
            if observer in self._observers:
                self._observers.remove(observer)
    
    def start_progress(self, test_id: str = None) -> None:
        """Start progress tracking for a new operation.
        
        Args:
            test_id: Optional identifier for the operation
        """
        with self._lock:
            self._current_progress = 0.0
            self._current_message = "Starting..."
            self._start_time = time.time()
            self._test_id = test_id or f"op_{int(self._start_time)}"
            self._active = True
            
            # Create a snapshot of observers to notify outside the lock
            observers_to_notify = list(self._observers)
            current_progress = self._current_progress
            current_message = self._current_message
        
        # Notify observers outside the lock to avoid deadlock
        for observer in observers_to_notify:
            try:
                observer(current_progress, current_message)
            except Exception as e:
                logger.error(f"Error notifying observer: {e}")
        
    def update_progress(self, progress: float, message: str = "") -> None:
        """Update current progress.
        
        Args:
            progress: Progress value (0.0-1.0)
            message: Status message
        """
        # Validate input
        progress = min(max(0.0, float(progress)), 1.0)  # Ensure value is between 0.0-1.0
        
        with self._lock:
            if not self._active:
                return
            
            # Always update if:
            # 1. Progress value has changed significantly (>= 0.01)
            # 2. OR it's a milestone (0, 0.25, 0.5, 0.75, 1.0)
            # 3. OR message has changed
            # 4. OR starting or completing (0.0 or 1.0)
            should_update = (
                abs(progress - self._current_progress) >= 0.01 or
                progress in (0.0, 0.25, 0.5, 0.75, 1.0) or
                message != self._current_message or
                progress == 0.0 or progress == 1.0
            )
            
            if not should_update:
                return
                
            # Debug logging for progress updates
            logger.debug(f"Progress update: {progress:.2f} - {message}")
                
            # Update current values
            self._current_progress = progress
            self._current_message = message
            
            # Create a snapshot of observers to notify outside the lock
            observers_to_notify = list(self._observers)
        
        # Notify observers outside the lock to avoid deadlock
        for observer in observers_to_notify:
            try:
                observer(progress, message)
            except Exception as e:
                logger.error(f"Error notifying observer: {e}")
        
    def complete_progress(self, message: str = "Complete") -> None:
        """Mark progress as complete.
        
        Args:
            message: Final message to display
        """
        with self._lock:
            if not self._active:
                return
                
            # Calculate elapsed time
            elapsed = time.time() - self._start_time if self._start_time else 0
            logger.info(f"Progress completed in {elapsed:.2f}s")
            
            # Set to 100% and update message
            self._current_progress = 1.0
            self._current_message = message
            
            # Create a snapshot for notification
            observers_to_notify = list(self._observers)
            
            # Mark as inactive
            self._active = False
        
        # Notify observers outside the lock
        for observer in observers_to_notify:
            try:
                observer(1.0, message)
            except Exception as e:
                logger.error(f"Error notifying observer: {e}")
        
    def abort_progress(self, message: str = "Aborted") -> None:
        """Abort progress tracking.
        
        Args:
            message: Message explaining why progress was aborted
        """
        with self._lock:
            if not self._active:
                return
                
            # Update message but keep progress value
            current_progress = self._current_progress
            self._current_message = message
            
            # Create a snapshot for notification
            observers_to_notify = list(self._observers)
            
            # Mark as inactive
            self._active = False
        
        # Notify observers outside the lock
        for observer in observers_to_notify:
            try:
                observer(current_progress, message)
            except Exception as e:
                logger.error(f"Error notifying observer: {e}")
        
    def get_current_progress(self) -> Dict[str, Any]:
        """Get current progress information.
        
        Returns:
            Dict with current progress state
        """
        with self._lock:
            elapsed = time.time() - self._start_time if self._start_time and self._active else 0
            
            return {
                "progress": self._current_progress,
                "message": self._current_message,
                "active": self._active,
                "test_id": self._test_id,
                "elapsed": elapsed
            }
        
    def is_active(self) -> bool:
        """Check if progress tracking is active.
        
        Returns:
            bool: True if progress tracking is active
        """
        with self._lock:
            return self._active