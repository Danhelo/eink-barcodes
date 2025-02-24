"""
Integration tests for UI and backend components.
"""
from tests.base_test import BaseTestCase
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtTest import QTest
import sys
from pathlib import Path
from PIL import Image
from src.ui.pages.quick_test import QuickTestPage
from src.ui.pages.custom_test import CustomTestPage
from src.core.state_manager import TestState, TestContext
from src.core.display_manager import DisplayManager
from src.core.test_controller import TestController, TestConfig

class TestUIIntegration(BaseTestCase):
    """Integration tests for UI components with backend."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.app = QApplication.instance() or QApplication(sys.argv)

        # Create test data
        cls.test_data_dir = Path("test_data")
        cls.test_data_dir.mkdir(exist_ok=True)
        cls.test_image = cls.test_data_dir / "test_barcode.png"
        cls.create_test_image().save(cls.test_image)

    def setUp(self):
        super().setUp()
        self.display_manager = DisplayManager()
        self.test_controller = TestController()

        # Create test pages
        self.quick_page = QuickTestPage()
        self.custom_page = CustomTestPage()

    def test_quick_test_flow(self):
        """Test complete quick test flow."""
        # Configure test
        self.quick_page.barcode_combo.setCurrentIndex(0)

        # Start test
        QTest.mouseClick(self.quick_page.start_button, Qt.MouseButton.LeftButton)

        # Verify backend state
        self.assertEqual(
            self.quick_page.state_manager.current_state,
            TestState.RUNNING
        )

        # Verify display update
        self.assertIsNotNone(self.quick_page.preview.current_image)

        # Simulate test completion
        context = TestContext(progress=1.0)
        self.quick_page.on_state_change(TestState.COMPLETED, context)

        # Verify final state
        self.assertEqual(
            self.quick_page.state_manager.current_state,
            TestState.COMPLETED
        )

    def test_custom_test_flow(self):
        """Test complete custom test flow."""
        # Configure test
        self.custom_page.barcode_combo.setCurrentIndex(0)
        self.custom_page.rotation_slider.setValue(90)
        self.custom_page.scale_spinbox.setValue(1.5)

        # Start test
        QTest.mouseClick(self.custom_page.start_button, Qt.MouseButton.LeftButton)

        # Verify backend state
        self.assertEqual(
            self.custom_page.state_manager.current_state,
            TestState.RUNNING
        )

        # Verify display update with transformations
        preview_image = self.custom_page.preview.current_image
        self.assertIsNotNone(preview_image)

        # Verify transformations applied
        config = self.custom_page.create_test_config()
        self.assertEqual(config.transformations.get('rotation'), 90)
        self.assertEqual(config.transformations.get('scale'), 1.5)

    def test_state_synchronization(self):
        """Test state synchronization between UI and backend."""
        # Start test on both pages
        self.quick_page.start_test()
        self.custom_page.start_test()

        # Verify states synchronized
        self.assertEqual(
            self.quick_page.state_manager.current_state,
            self.custom_page.state_manager.current_state
        )

        # Stop test
        self.quick_page.stop_test()

        # Verify states still synchronized
        self.assertEqual(
            self.quick_page.state_manager.current_state,
            self.custom_page.state_manager.current_state
        )

    def test_display_updates(self):
        """Test display updates propagate to UI."""
        # Create test image
        test_image = self.create_test_image()

        # Update display
        self.display_manager.update_display(test_image)

        # Verify UI updates
        self.assertImageEqual(
            self.quick_page.preview.current_image,
            test_image
        )
        self.assertImageEqual(
            self.custom_page.preview.current_image,
            test_image
        )

    def test_error_propagation(self):
        """Test error propagation from backend to UI."""
        # Start test
        self.quick_page.start_test()

        # Simulate backend error
        error_msg = "Backend error"
        with self.assertLogs(level='ERROR'):
            self.test_controller.handle_error(error_msg)

        # Verify error state propagated
        self.assertEqual(
            self.quick_page.state_manager.current_state,
            TestState.ERROR
        )

    def test_config_validation(self):
        """Test configuration validation between UI and backend."""
        # Create invalid config
        self.custom_page.scale_spinbox.setValue(3.0)  # Invalid scale

        # Verify validation fails
        self.assertFalse(self.custom_page.validate_config())

        # Create valid config
        self.custom_page.scale_spinbox.setValue(1.5)

        # Verify validation passes
        self.assertTrue(self.custom_page.validate_config())

    def test_concurrent_operations(self):
        """Test concurrent operations between UI and backend."""
        # Start tests on both pages
        self.quick_page.start_test()
        self.custom_page.start_test()

        # Update display
        test_image = self.create_test_image()
        self.display_manager.update_display(test_image)

        # Verify both pages updated
        self.assertImageEqual(
            self.quick_page.preview.current_image,
            test_image
        )
        self.assertImageEqual(
            self.custom_page.preview.current_image,
            test_image
        )

    def test_cleanup_synchronization(self):
        """Test cleanup synchronization between UI and backend."""
        # Start test
        self.quick_page.start_test()

        # Cleanup
        self.quick_page.cleanup()

        # Verify backend state reset
        self.assertEqual(
            self.quick_page.state_manager.current_state,
            TestState.NOT_STARTED
        )

    def tearDown(self):
        super().tearDown()
        self.quick_page.cleanup()
        self.custom_page.cleanup()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        # Clean up test data
        if cls.test_data_dir.exists():
            for file in cls.test_data_dir.iterdir():
                file.unlink()
            cls.test_data_dir.rmdir()
