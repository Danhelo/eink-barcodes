import pytest
from unittest.mock import AsyncMock, MagicMock
from src.core.test_controller import TestController, TestConfig
from src.core.state_manager import StateManager, TestState
from src.core.display_manager import create_display_manager, DisplayConfig

@pytest.fixture
def state_manager():
    return StateManager()

@pytest.fixture
def display_config():
    return DisplayConfig(
        virtual=True,
        vcom=-2.02,
        dimensions=(800, 600)
    )

@pytest.fixture
def display_manager(state_manager, display_config):
    manager = AsyncMock()
    manager.initialize.return_value = True
    manager.display_image.return_value = True
    manager.clear.return_value = True
    manager.is_ready = True
    return manager

@pytest.fixture
def test_controller(state_manager, display_manager):
    return TestController(
        state_manager=state_manager,
        display_manager=display_manager
    )

@pytest.fixture
def test_config():
    return TestConfig(
        test_id="test-123",
        barcode_type="code128",
        image_paths=["test1.png", "test2.png"],
        transformations={"mirror": True},
        display_config=DisplayConfig(virtual=True)
    )

@pytest.mark.asyncio
async def test_initialize_test(test_controller, test_config):
    result = await test_controller.initialize_test(test_config)
    assert result is True
    state, context = test_controller.state_manager.get_current_state()
    assert state == TestState.RUNNING
    assert context.test_id == test_config.test_id
    assert context.total_images == len(test_config.image_paths)

@pytest.mark.asyncio
async def test_initialize_test_failure(test_controller, test_config, display_manager):
    display_manager.initialize.return_value = False
    result = await test_controller.initialize_test(test_config)
    assert result is False
    state, _ = test_controller.state_manager.get_current_state()
    assert state == TestState.FAILED

@pytest.mark.asyncio
async def test_execute_test(test_controller, test_config):
    await test_controller.initialize_test(test_config)
    result = await test_controller.execute_test()
    assert result is True
    state, context = test_controller.state_manager.get_current_state()
    assert state == TestState.COMPLETED
    assert context.processed_images == len(test_config.image_paths)

@pytest.mark.asyncio
async def test_execute_test_failure(test_controller, test_config, display_manager):
    await test_controller.initialize_test(test_config)
    display_manager.display_image.return_value = False
    result = await test_controller.execute_test()
    assert result is False
    state, _ = test_controller.state_manager.get_current_state()
    assert state == TestState.FAILED

@pytest.mark.asyncio
async def test_stop_test(test_controller, test_config):
    await test_controller.initialize_test(test_config)
    await test_controller.stop_test()
    state, _ = test_controller.state_manager.get_current_state()
    assert state == TestState.STOPPED
    assert test_controller.display_manager.clear.called

@pytest.mark.asyncio
async def test_cleanup(test_controller, test_config):
    await test_controller.initialize_test(test_config)
    await test_controller.cleanup()
    state, context = test_controller.state_manager.get_current_state()
    assert state == TestState.NOT_STARTED
    assert context is None
    assert test_controller.get_current_config() is None

def test_create_config():
    config = TestController.create_config(
        barcode_type="code128",
        image_paths=["test.png"],
        transformations={"mirror": True}
    )
    assert config.barcode_type == "code128"
    assert config.image_paths == ["test.png"]
    assert config.transformations == {"mirror": True}
    assert isinstance(config.display_config, DisplayConfig)
