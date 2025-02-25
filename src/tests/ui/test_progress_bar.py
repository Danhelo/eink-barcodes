"""
Tests for progress bar functionality in BaseTestPage.

This module tests the progress bar functionality in the BaseTestPage class,
ensuring that it correctly updates in response to progress events from the
test controller.
"""
import pytest
import asyncio
from unittest.mock import MagicMock, patch
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt

from src.ui.pages.base_test_page import BaseTestPage
from src.core.test_controller import TestController
from src.core.state_manager import StateManager, TestState


@pytest.fixture
def app():
    """Create a QApplication instance for testing."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


@pytest.fixture
def test_controller():
    """Create a mock test controller for testing."""
    controller = MagicMock(spec=TestController)
    controller.state_manager = MagicMock(spec=StateManager)
    return controller


@pytest.fixture
def base_page(app, test_controller):
    """Create a BaseTestPage instance for testing."""
    # Create a concrete implementation of BaseTestPage for testing
    class TestPage(BaseTestPage):
        def validate_config(self):
            return True

        def create_test_config(self):
            return MagicMock()

    page = TestPage(test_controller=test_controller)
    # Create the progress bar
    page.progress = page.create_progress_bar()
    return page


@pytest.mark.asyncio
async def test_progress_bar_creation(base_page):
    """Test that the progress bar is created correctly."""
    progress = base_page.create_progress_bar()

    # Check that the progress bar has the correct properties
    assert progress.minimum() == 0
    assert progress.maximum() == 100
    assert progress.value() == 0
    assert not progress.isVisible()
    assert progress.textVisible()


@pytest.mark.asyncio
async def test_progress_direct_update(base_page):
    """Test that the progress bar updates correctly when update_progress_direct is called."""
    # Call update_progress_direct
    base_page.update_progress_direct(0.5, "test_image.png")

    # Process events to ensure signal is processed
    QApplication.processEvents()

    # Check that the progress bar has been updated
    assert base_page.progress.value() == 50
    assert "50%" in base_page.progress.format()
    assert "test_image.png" in base_page.progress.format()


@pytest.mark.asyncio
async def test_progress_state_update(base_page):
    """Test that the progress bar updates correctly when state changes."""
    # Call on_state_changed
    base_page.on_state_changed(
        TestState.RUNNING,
        {"progress": 0.75, "current_image": "another_image.png"}
    )

    # Process events to ensure signal is processed
    QApplication.processEvents()

    # Check that the progress bar has been updated
    assert base_page.progress.value() == 75
    assert "75%" in base_page.progress.format()
    assert "another_image.png" in base_page.progress.format()


@pytest.mark.asyncio
async def test_progress_callback_registration(base_page, test_controller):
    """Test that the progress callback is registered correctly."""
    # Check that the progress callback was registered
    test_controller.set_progress_callback.assert_called_once()

    # The callback should be base_page.update_progress_direct
    callback = test_controller.set_progress_callback.call_args[0][0]
    assert callback == base_page.update_progress_direct


@pytest.mark.asyncio
async def test_start_test_progress_updates(base_page, test_controller):
    """Test that the progress bar updates correctly during test execution."""
    # Mock the run_test method to return a successful result
    test_controller.run_test.return_value = {
        "success": True,
        "total_images": 5,
        "successful_images": 5
    }

    # Start the test
    await base_page.start_test()

    # Check that the progress bar was shown and updated to 100% at completion
    assert base_page.progress.value() == 100
    assert "100%" in base_page.progress.format()
    assert "Complete" in base_page.progress.format()


@pytest.mark.asyncio
async def test_progress_prevents_jumps(base_page):
    """Test that the progress bar prevents jumps in progress."""
    # Set initial progress
    base_page.update_progress_direct(0.8, "test_image.png")
    QApplication.processEvents()
    assert base_page.progress.value() == 80

    # Try to update with a lower progress value
    base_page.update_progress_direct(0.5, "another_image.png")
    QApplication.processEvents()

    # Progress should not have decreased
    assert base_page.progress.value() == 80
    assert "80%" in base_page.progress.format()

    # Reset should work
    base_page.update_progress_direct(0.0, "reset.png")
    QApplication.processEvents()
    assert base_page.progress.value() == 0
