import pytest
from src.core.state_manager import (
    StateManager, TestState, DisplayState, TestContext, StateObserver
)

class MockObserver(StateObserver):
    def __init__(self):
        self.last_state = None
        self.last_context = None
        self.notification_count = 0

    def on_state_change(self, state, context):
        self.last_state = state
        self.last_context = context
        self.notification_count += 1

@pytest.fixture
def state_manager():
    return StateManager()

@pytest.fixture
def mock_observer():
    return MockObserver()

def test_initial_state(state_manager):
    assert state_manager.get_current_state() == (TestState.NOT_STARTED, None)
    assert state_manager.get_display_state() == DisplayState.DISCONNECTED

def test_observer_registration(state_manager, mock_observer):
    state_manager.register_observer(mock_observer)
    assert mock_observer in state_manager._observers

    state_manager.remove_observer(mock_observer)
    assert mock_observer not in state_manager._observers

def test_state_transitions(state_manager):
    # Valid transitions
    state_manager.update_state(TestState.INITIALIZING)
    assert state_manager.get_current_state()[0] == TestState.INITIALIZING

    state_manager.update_state(TestState.RUNNING)
    assert state_manager.get_current_state()[0] == TestState.RUNNING

    # Invalid transition
    with pytest.raises(ValueError):
        state_manager.update_state(TestState.NOT_STARTED)

def test_context_management(state_manager):
    context = TestContext(
        test_id="test-123",
        config={"type": "test"},
        total_images=5
    )

    state_manager.set_context(context)
    current_state, current_context = state_manager.get_current_state()
    assert current_context == context

    state_manager.clear_context()
    assert state_manager.get_current_state()[1] is None

def test_observer_notifications(state_manager, mock_observer):
    state_manager.register_observer(mock_observer)
    context = TestContext(test_id="test-123", config={})
    state_manager.set_context(context)

    state_manager.update_state(TestState.INITIALIZING)
    assert mock_observer.last_state == TestState.INITIALIZING
    assert mock_observer.last_context == context
    assert mock_observer.notification_count == 2  # set_context + update_state

def test_display_state_updates(state_manager):
    state_manager.update_display_state(DisplayState.INITIALIZING)
    assert state_manager.get_display_state() == DisplayState.INITIALIZING

    state_manager.update_display_state(DisplayState.READY)
    assert state_manager.get_display_state() == DisplayState.READY

def test_state_history(state_manager):
    context = TestContext(test_id="test-123", config={})
    state_manager.set_context(context)

    state_manager.update_state(TestState.INITIALIZING)
    state_manager.update_state(TestState.RUNNING)

    history = state_manager.get_state_history()
    assert len(history) == 2
    assert history[0][0] == TestState.INITIALIZING
    assert history[1][0] == TestState.RUNNING
