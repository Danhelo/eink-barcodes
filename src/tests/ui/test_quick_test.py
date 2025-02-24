"""
Test suite for Quick Test page functionality.
"""
from tests.base_test import BaseTestCase
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtTest import QTest
import sys
from pathlib import Path
from src.ui.pages.quick_test import QuickTestPage
from src.core.state_manager import TestState, TestContext
from src.core.test_controller import TestConfig
from src.core.display_manager import DisplayManager

class TestQuickTestPage(BaseTestCase):
    """Test cases for quick test page."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.app = QApplication.instance() or QApplication(sys.argv)

        # Create test data directory
        cls.test_data_dir = Path("test_data")
        cls.test_data_dir.mkdir(exist_ok=True)

        # Create test image
        cls.test_image = cls.test_data_dir / "test_barcode.png"
        cls.create_test_image().save(cls.test_image)

    def setUp(self):
        super().setUp()
        self.page = QuickTestPage()

    def test_initial_state(self):
        """Test initial page state."""
        # Verify UI components
        self.assertIsNotNone(self.page.barcode_combo)
        self.assertIsNotNone(self.page.preview)
        self.assertIsNotNone(self.page.progress)

        # Verify initial values
        self.assertTrue(len(self.page.barcode_combo.items()) > 0)
        self.assertIsNone(self.page.preview.current_image)
        self.assertEqual(self.page.progress.value(), 0)

    def test_barcode_selection(self):
        """Test barcode type selection."""
        # Select each barcode type
        for index in range(self.page.barcode_combo.count()):
            self.page.barcode_combo.setCurrentIndex(index)
            QTest.qWait(100)  # Allow UI updates

            # Verify selection reflected in config
            config = self.page.create_test_config()
            self.assertEqual(
                config.barcode_type,
                self.page.barcode_combo.currentText()
            )

    def test_preview_update(self):
        """Test preview updates with barcode selection."""
        # Select barcode type
        self.page.barcode_combo.setCurrentIndex(0)
        QTest.qWait(100)

        # Verify preview updated
        self.assertIsNotNone(self.page.preview.current_image)

    def test_test_execution(self):
        """Test complete test execution flow."""
        # Configure test
        self.page.barcode_combo.setCurrentIndex(0)

        # Start test
        QTest.mouseClick(self.page.start_button, Qt.MouseButton.LeftButton)

        # Verify initial state
        self.assertEqual(self.page.state_manager.current_state, TestState.RUNNING)
        self.assertFalse(self.page.start_button.isEnabled())
        self.assertTrue(self.page.stop_button.isEnabled())

        # Simulate progress
        context = TestContext(progress=0.5)
        self.page.on_state_change(TestState.RUNNING, context)
        self.assertEqual(self.page.progress.value(), 50)

        # Simulate completion
        context = TestContext(progress=1.0)
        self.page.on_state_change(TestState.COMPLETED, context)

        # Verify final state
        self.assertEqual(self.page.state_manager.current_state, TestState.COMPLETED)
        self.assertTrue(self.page.start_button.isEnabled())
        self.assertFalse(self.page.stop_button.isEnabled())
        self.assertEqual(self.page.progress.value(), 100)

    def test_error_handling(self):
        """Test error handling during test execution."""
        # Start test
        self.page.barcode_combo.setCurrentIndex(0)
        QTest.mouseClick(self.page.start_button, Qt.MouseButton.LeftButton)

        # Simulate error
        error_msg = "Test error message"
        with self.assertLogs(level='ERROR'):
            self.page.handle_error(error_msg)

        # Verify error state
        self.assertEqual(self.page.state_manager.current_state, TestState.ERROR)
        self.assertTrue(self.page.start_button.isEnabled())
        self.assertFalse(self.page.stop_button.isEnabled())

    def test_display_integration(self):
        """Test integration with display manager."""
        # Create test config
        config = self.page.create_test_config()

        # Verify display manager interaction
        self.assertTrue(self.page.display_manager.validate_config(config))

        # Test display update
        test_image = self.create_test_image()
        self.page.display_manager.update_display(test_image)

        # Verify preview updated
        self.assertImageEqual(
            self.page.preview.current_image,
            test_image
        )

    def test_back_navigation(self):
        """Test back button navigation."""
        # Click back button
        with self.assertLogs(level='INFO'):
            QTest.mouseClick(self.page.back_button, Qt.MouseButton.LeftButton)

        # Verify cleanup called
        self.assertEqual(self.page.state_manager.current_state, TestState.NOT_STARTED)

    def test_stop_during_execution(self):
        """Test stopping test during execution."""
        # Start test
        self.page.barcode_combo.setCurrentIndex(0)
        QTest.mouseClick(self.page.start_button, Qt.MouseButton.LeftButton)

        # Stop test
        QTest.mouseClick(self.page.stop_button, Qt.MouseButton.LeftButton)

        # Verify stopped state
        self.assertEqual(self.page.state_manager.current_state, TestState.STOPPED)
        self.assertTrue(self.page.start_button.isEnabled())
        self.assertFalse(self.page.stop_button.isEnabled())

    def test_config_validation(self):
        """Test test configuration validation."""
        # Valid config
        self.page.barcode_combo.setCurrentIndex(0)
        self.assertTrue(self.page.validate_config())

        # Invalid config (no selection)
        self.page.barcode_combo.setCurrentIndex(-1)
        self.assertFalse(self.page.validate_config())

    def tearDown(self):
        super().tearDown()
        self.page.cleanup()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        # Clean up test data
        if cls.test_data_dir.exists():
            for file in cls.test_data_dir.iterdir():
                file.unlink()
            cls.test_data_dir.rmdir()
