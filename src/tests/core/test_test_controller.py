import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import os
from PIL import Image
import tempfile

from src.core.test_controller import TestController
from src.core.test_config import TestConfig
from src.core.state_manager import StateManager, TestState
from src.core.display_manager import DisplayManager, DisplayConfig

@pytest.fixture
def state_manager():
    return StateManager()

@pytest.fixture
def display_manager():
    manager = AsyncMock()
    manager.initialize.return_value = True
    manager.display_image.return_value = True
    manager.clear.return_value = True
    return manager

@pytest.fixture
def test_controller(state_manager, display_manager):
    return TestController(
        state_manager=state_manager,
        display_manager=display_manager
    )

@pytest.fixture
def test_images():
    # Create temporary directory for test images
    temp_dir = tempfile.mkdtemp()

    # Create test images
    image_paths = []
    for i in range(3):
        img = Image.new('L', (100, 100), 255)
        path = os.path.join(temp_dir, f"test_image_{i}.png")
        img.save(path)
        image_paths.append(path)

    yield temp_dir, image_paths

    # Cleanup
    for path in image_paths:
        if os.path.exists(path):
            os.remove(path)
    os.rmdir(temp_dir)

@pytest.fixture
def test_config(test_images):
    _, image_paths = test_images
    return TestConfig(
        barcode_type="code128",
        image_paths=image_paths,
        delay_between_images=0.1
    )

@pytest.mark.asyncio
async def test_initialize(test_controller):
    result = await test_controller.initialize(virtual=True)
    assert result is True
    assert test_controller.state_manager.get_test_state() == TestState.READY

@pytest.mark.asyncio
async def test_initialize_failure(test_controller, display_manager):
    display_manager.initialize.return_value = False
    result = await test_controller.initialize()
    assert result is False
    assert test_controller.state_manager.get_test_state() == TestState.ERROR

@pytest.mark.asyncio
async def test_run_test(test_controller, test_config):
    await test_controller.initialize()
    results = await test_controller.run_test(test_config)

    assert results["success"] is True
    assert results["total_images"] == len(test_config.image_paths)
    assert results["successful_images"] == len(test_config.image_paths)
    assert test_controller.state_manager.get_test_state() == TestState.COMPLETED

@pytest.mark.asyncio
async def test_run_test_failure(test_controller, test_config, display_manager):
    await test_controller.initialize()
    display_manager.display_image.return_value = False

    results = await test_controller.run_test(test_config)

    assert results["success"] is False
    assert "error" in results
    assert test_controller.state_manager.get_test_state() == TestState.ERROR

@pytest.mark.asyncio
async def test_stop_test(test_controller, test_config):
    await test_controller.initialize()

    # Start a test
    test_controller.test_running = True
    test_controller.current_test = test_config

    # Stop it
    result = await test_controller.stop_test()

    assert result is True
    assert test_controller.test_running is False
    assert test_controller.state_manager.get_test_state() == TestState.STOPPED

@pytest.mark.asyncio
async def test_cleanup(test_controller):
    await test_controller.initialize()
    result = await test_controller.cleanup()

    assert result is True
    assert test_controller.display_manager.cleanup.called
