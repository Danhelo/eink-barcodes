"""
State management system for test execution.
"""
from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from abc import ABC, abstractmethod
import time
import logging

logger = logging.getLogger(__name__)

class TestState(Enum):
    """Test execution states"""
    NOT_STARTED = auto()
    INITIALIZING = auto()
    RUNNING = auto()
    PAUSED = auto()
    COMPLETED = auto()
    FAILED = auto()
    STOPPED = auto()

class DisplayState(Enum):
    """Display hardware states"""
    DISCONNECTED = auto()
    INITIALIZING = auto()
    READY = auto()
    BUSY = auto()
    ERROR = auto()

@dataclass
class TestContext:
    """Test execution context"""
    test_id: str
    config: Dict[str, Any]
    current_image: Optional[str] = None
    progress: float = 0.0
    total_images: int = 0
    processed_images: int = 0
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    error: Optional[str] = None
    metrics: Dict[str, Any] = field(default_factory=dict)

    def add_metric(self, key: str, value: Any) -> None:
        """Add a metric to the context"""
        self.metrics[key] = value

    @property
    def duration(self) -> Optional[float]:
        """Get test duration in seconds"""
        if self.start_time:
            end = self.end_time or time.time()
            return end - self.start_time
        return None

class StateObserver(ABC):
    """State observer interface"""
    @abstractmethod
    def on_state_change(self, state: TestState, context: TestContext) -> None:
        """Handle state change events"""
        pass

class StateManager:
    """Centralized state management"""
    def __init__(self):
        self._test_state: TestState = TestState.NOT_STARTED
        self._display_state: DisplayState = DisplayState.DISCONNECTED
        self._context: Optional[TestContext] = None
        self._observers: List[StateObserver] = []
        self._state_history: List[tuple[TestState, TestContext]] = []

    def register_observer(self, observer: StateObserver) -> None:
        """Register new state observer"""
        if observer not in self._observers:
            self._observers.append(observer)
            logger.debug(f"Registered observer: {observer.__class__.__name__}")

    def remove_observer(self, observer: StateObserver) -> None:
        """Remove state observer"""
        if observer in self._observers:
            self._observers.remove(observer)
            logger.debug(f"Removed observer: {observer.__class__.__name__}")

    def update_state(self, new_state: TestState, context_updates: Dict[str, Any] = None) -> None:
        """Update test state with context"""
        if not self.can_transition_to(new_state):
            raise ValueError(f"Invalid state transition from {self._test_state} to {new_state}")

        old_state = self._test_state
        self._test_state = new_state

        # Update context if provided
        if context_updates and self._context:
            for key, value in context_updates.items():
                setattr(self._context, key, value)

            # Auto-update timestamps
            if new_state == TestState.RUNNING and not self._context.start_time:
                self._context.start_time = time.time()
            elif new_state in (TestState.COMPLETED, TestState.FAILED, TestState.STOPPED):
                self._context.end_time = time.time()

        # Record state change
        self._state_history.append((new_state, self._context))

        # Log state change
        logger.info(f"State transition: {old_state} -> {new_state}")
        if context_updates:
            logger.debug(f"Context updates: {context_updates}")

        # Notify observers
        self._notify_observers()

    def _notify_observers(self) -> None:
        """Notify all observers of state change"""
        for observer in self._observers:
            try:
                observer.on_state_change(self._test_state, self._context)
            except Exception as e:
                logger.error(f"Error notifying observer {observer.__class__.__name__}: {e}")

    def get_current_state(self) -> tuple[TestState, Optional[TestContext]]:
        """Get current state and context"""
        return self._test_state, self._context

    def can_transition_to(self, target_state: TestState) -> bool:
        """Validate state transition"""
        valid_transitions = {
            TestState.NOT_STARTED: [TestState.INITIALIZING],
            TestState.INITIALIZING: [TestState.RUNNING, TestState.FAILED],
            TestState.RUNNING: [TestState.PAUSED, TestState.COMPLETED, TestState.FAILED, TestState.STOPPED],
            TestState.PAUSED: [TestState.RUNNING, TestState.STOPPED],
            TestState.COMPLETED: [TestState.NOT_STARTED],
            TestState.FAILED: [TestState.NOT_STARTED],
            TestState.STOPPED: [TestState.NOT_STARTED]
        }
        return target_state in valid_transitions.get(self._test_state, [])

    def set_context(self, context: TestContext) -> None:
        """Set new test context"""
        self._context = context
        logger.info(f"New test context set: {context.test_id}")
        self._notify_observers()

    def clear_context(self) -> None:
        """Clear current context"""
        self._context = None
        logger.info("Test context cleared")
        self._notify_observers()

    def get_state_history(self) -> List[tuple[TestState, TestContext]]:
        """Get state transition history"""
        return self._state_history.copy()

    def update_display_state(self, state: DisplayState) -> None:
        """Update display hardware state"""
        self._display_state = state
        logger.info(f"Display state updated: {state}")
        # Note: Display state changes don't trigger observer notifications

    def get_display_state(self) -> DisplayState:
        """Get current display state"""
        return self._display_state
