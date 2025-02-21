"""
Test suite for base test page functionality.
"""
from tests.base_test import BaseTestCase
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
import sys
from src.ui.pages.base_test_page import BaseTestPage
from src.core.state_manager import TestState, TestContext
from src.core.test_controller import TestConfig

class MockTestPage(BaseTestPage):
    """Mock implementation of base test page."""
    page_title = "Mock Test Page"

    def validate_config(self) -> bool:
        return True

    def create_test_config(self) -> TestConfig:
        return TestConfig(
            barcode_type="Test",
            image_paths=["test.png"],
            transformations={}
        )

class TestBaseTestPage(BaseTestCase):
    """Test cases for base test page."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Create QApplication instance
        cls.app = QApplication.instance() or QApplication(sys.argv)

    def setUp(self):
        super().setUp()
        self.page = MockTestPage()

    def test_initial_state(self):
        """Test initial page state."""
        self.assertIsNotNone(self.page.state_manager)
        self.assertIsNotNone(self.page.display_manager)
        self.assertIsNotNone(self.page.test_controller)
        self.assertIsNone(self.page.current_config)

    def test_ui_setup(self):
        """Test UI component setup."""
        # Verify title
        title_label = self.page.findChild(QLabel, "title")
        self.assertIsNotNone(title_label)
        self.assertEqual(title_label.text(), "Mock Test Page")

        # Verify buttons
        self.assertIsNotNone(self.page.start_button)
        self.assertIsNotNone(self.page.stop_button)
        self.assertIsNotNone(self.page.back_button)

        # Verify initial button states
        self.assertTrue(self.page.start_button.isEnabled())
        self.assertFalse(self.page.stop_button.isEnabled())
        self.assertTrue(self.page.back_button.isEnabled())

    def test_start_test(self):
        """Test starting a test."""
        # Start test
        self.page.start_test()

        # Verify UI state
        self.assertFalse(self.page.start_button.isEnabled())
        self.assertTrue(self.page.stop_button.isEnabled())

        # Verify test started
        self.assertEqual(self.page.state_manager.current_state, TestState.RUNNING)

    def test_stop_test(self):
        """Test stopping a test."""
        # Start then stop test
        self.page.start_test()
        self.page.stop_test()

        # Verify UI state
        self.assertTrue(self.page.start_button.isEnabled())
        self.assertFalse(self.page.stop_button.isEnabled())

        # Verify test stopped
        self.assertEqual(self.page.state_manager.current_state, TestState.STOPPED)

    def test_state_change_handling(self):
        """Test handling of state changes."""
        # Create test context
        context = TestContext(progress=0.5)

        # Simulate state changes
        self.page.on_state_change(TestState.RUNNING, context)
        self.assertFalse(self.page.start_button.isEnabled())
        self.assertTrue(self.page.stop_button.isEnabled())

        self.page.on_state_change(TestState.COMPLETED, context)
        self.assertTrue(self.page.start_button.isEnabled())
        self.assertFalse(self.page.stop_button.isEnabled())

    def test_error_handling(self):
        """Test error handling."""
        with self.assertLogs(level='ERROR'):
            self.page.handle_error("Test error")

        # Verify UI state after error
        self.assertTrue(self.page.start_button.isEnabled())
        self.assertFalse(self.page.stop_button.isEnabled())

    def test_cleanup(self):
        """Test resource cleanup."""
        # Get initial observer count
        initial_observers = len(self.page.state_manager._observers)

        # Trigger cleanup
        self.page.cleanup()

        # Verify observer removed
        self.assertEqual(
            len(self.page.state_manager._observers),
            initial_observers - 1
        )

    def test_progress_update(self):
        """Test progress bar updates."""
        # Create test context with progress
        context = TestContext(progress=0.75)

        # Update progress
        self.page.on_state_change(TestState.RUNNING, context)

        # Verify progress bar
        self.assertEqual(self.page.progress.value(), 75)

    def test_invalid_config(self):
        """Test handling of invalid configuration."""
        # Override validation to fail
        self.page.validate_config = lambda: False

        # Attempt to start test
        self.page.start_test()

        # Verify test not started
        self.assertEqual(self.page.state_manager.current_state, TestState.NOT_STARTED)
        self.assertTrue(self.page.start_button.isEnabled())
        self.assertFalse(self.page.stop_button.isEnabled())
