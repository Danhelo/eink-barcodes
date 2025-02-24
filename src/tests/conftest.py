import pytest
from PyQt5.QtWidgets import QApplication
from unittest.mock import AsyncMock, MagicMock
from src.core.state_manager import StateManager
from src.core.display_manager import DisplayManager, DisplayConfig
from src.core.test_controller import TestController

@pytest.fixture(scope="session")
def qapp():
    """Create a QApplication instance for the entire test session."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app

@pytest.fixture
def state_manager():
    """Create a StateManager instance."""
    return StateManager()

@pytest.fixture
def display_manager():
    """Create a mock DisplayManager."""
    manager = AsyncMock(spec=DisplayManager)
    manager.initialize.return_value = True
    manager.display_image.return_value = True
    manager.clear.return_value = True
    return manager

@pytest.fixture
def test_controller(state_manager, display_manager):
    """Create a TestController instance with mock dependencies."""
    return TestController(state_manager, display_manager)

@pytest.fixture
def display_config():
    """Create a basic DisplayConfig."""
    return DisplayConfig(
        virtual=True,
        mirror=False,
        vcom=-2.02,
        spi_hz=24000000,
        dimensions=(800, 600)
    )
