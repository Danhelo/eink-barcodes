from enum import Enum, auto
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from PyQt5.QtCore import QObject

class TestState(Enum):
    NOT_STARTED = auto()
    IDLE = auto()
    INITIALIZING = auto()
    RUNNING = auto()
    PAUSED = auto()
    COMPLETED = auto()
    FAILED = auto()
    STOPPED = auto()
    ERROR = auto()  # Added ERROR state to match test_controller.py
    READY = auto()  # Added READY state to match test_controller.py

class DisplayState(Enum):
    """Display hardware states"""
    DISCONNECTED = auto()
    INITIALIZING = auto()
    READY = auto()
    BUSY = auto()
    ERROR = auto()

@dataclass
class TestContext:
    """Stores test execution context"""
    test_id: str
    config: Dict[str, Any]
    total_images: int
    current_image: str = ""
    processed_images: int = 0
    progress: float = 0.0
    error: Optional[str] = None

class StateObserver(QObject):
    """Base class for state observers using Qt's metaclass"""

    def __init__(self):
        super().__init__()
        self._test_state = TestState.IDLE
        self._display_state = DisplayState.DISCONNECTED

    def on_state_changed(self, new_state: TestState, context: Optional[Dict] = None):
        """Called when test state changes"""
        self._test_state = new_state

    def on_display_state_changed(self, new_state: DisplayState):
        """Called when display state changes"""
        self._display_state = new_state

class StateManager(QObject):
    """Manages application state and notifies observers"""

    def __init__(self):
        super().__init__()
        self._test_state = TestState.IDLE  # Start in IDLE state
        self._display_state = DisplayState.DISCONNECTED
        self._context: Optional[TestContext] = None
        self._observers: List[StateObserver] = []

    def add_observer(self, observer: StateObserver):
        """Add an observer to be notified of state changes"""
        if observer not in self._observers:
            self._observers.append(observer)

    def remove_observer(self, observer: StateObserver):
        """Remove an observer"""
        if observer in self._observers:
            self._observers.remove(observer)

    def get_test_state(self) -> TestState:
        """Get current test state"""
        return self._test_state

    def get_display_state(self) -> DisplayState:
        """Get current display state"""
        return self._display_state

    def get_context(self) -> Optional[TestContext]:
        """Get current test context"""
        return self._context

    def set_context(self, context: TestContext):
        """Set test context"""
        self._context = context

    def clear_context(self):
        """Clear test context"""
        self._context = None

    def update_state(self, new_state: TestState, context_updates: Dict[str, Any] = None):
        """Update test state and context, then notify observers"""
        if new_state != self._test_state and self.can_transition_to(new_state):
            self._test_state = new_state

            # Update context if provided
            if context_updates and self._context:
                for key, value in context_updates.items():
                    setattr(self._context, key, value)

            self._notify_test_state()

    # Add transition_to method for compatibility with test_controller.py
    def transition_to(self, new_state: TestState, context_updates: Dict[str, Any] = None):
        """Alias for update_state to maintain compatibility"""
        self.update_state(new_state, context_updates)

    def update_display_state(self, new_state: DisplayState):
        """Update display state and notify observers"""
        if new_state != self._display_state:
            self._display_state = new_state
            self._notify_display_state()

    def can_transition_to(self, new_state: TestState) -> bool:
        """Check if transition to new state is valid"""
        # Define valid transitions
        valid_transitions = {
            TestState.NOT_STARTED: [TestState.IDLE],
            TestState.IDLE: [TestState.INITIALIZING, TestState.READY],  # Added READY
            TestState.INITIALIZING: [TestState.RUNNING, TestState.FAILED, TestState.READY],  # Added READY
            TestState.READY: [TestState.RUNNING, TestState.IDLE],  # Added READY transitions
            TestState.RUNNING: [TestState.PAUSED, TestState.COMPLETED, TestState.FAILED, TestState.STOPPED, TestState.ERROR],  # Added ERROR
            TestState.PAUSED: [TestState.RUNNING, TestState.STOPPED],
            TestState.COMPLETED: [TestState.IDLE],
            TestState.FAILED: [TestState.IDLE],
            TestState.STOPPED: [TestState.IDLE],
            TestState.ERROR: [TestState.IDLE]  # Added ERROR transition
        }

        # If no valid transitions defined or all transitions allowed, permit the change
        if self._test_state not in valid_transitions:
            return True

        return new_state in valid_transitions.get(self._test_state, [])

    def _notify_test_state(self):
        """Notify observers of test state change"""
        context_dict = None
        if self._context:
            context_dict = {
                'test_id': self._context.test_id,
                'progress': self._context.progress,
                'current_image': self._context.current_image,
                'error': self._context.error
            }

        for observer in self._observers:
            observer.on_state_changed(self._test_state, context_dict)

    def _notify_display_state(self):
        """Notify observers of display state change"""
        for observer in self._observers:
            observer.on_display_state_changed(self._display_state)
