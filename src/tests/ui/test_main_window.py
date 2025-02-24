import pytest
from PyQt5.QtCore import Qt
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QApplication, QMainWindow
from src.ui.main_window import MainWindow
from src.core.state_manager import StateManager, TestState
from src.core.test_controller import TestController
from src.ui.pages.quick_test import QuickTestPage
from src.ui.pages.custom_test import CustomTestPage

class TestMainWindow:
    @pytest.fixture
    def main_window(self, qapp, test_controller):
        window = MainWindow(test_controller)
        window.show()
        return window

    def test_window_init(self, main_window):
        """Test main window initialization."""
        assert main_window.windowTitle() == "E-Ink Testing Interface"
        assert main_window.central_widget is not None
        assert main_window.test_controller is not None

    def test_menu_page_initial(self, main_window):
        """Test main menu page is shown initially."""
        assert main_window.menu_page is not None
        assert main_window.central_widget.currentWidget() == main_window.menu_page

    def test_quick_test_navigation(self, qtbot, main_window):
        """Test navigation to quick test page."""
        # Click quick test button
        quick_test_button = main_window.menu_page.quick_test_button
        qtbot.mouseClick(quick_test_button, Qt.LeftButton)

        # Verify page change
        current_widget = main_window.central_widget.currentWidget()
        assert isinstance(current_widget, QuickTestPage)

        # Return to menu
        back_button = current_widget.back_button
        qtbot.mouseClick(back_button, Qt.LeftButton)
        assert main_window.central_widget.currentWidget() == main_window.menu_page

    def test_custom_test_navigation(self, qtbot, main_window):
        """Test navigation to custom test page."""
        # Click custom test button
        custom_test_button = main_window.menu_page.custom_test_button
        qtbot.mouseClick(custom_test_button, Qt.LeftButton)

        # Verify page change
        current_widget = main_window.central_widget.currentWidget()
        assert isinstance(current_widget, CustomTestPage)

        # Return to menu
        back_button = current_widget.back_button
        qtbot.mouseClick(back_button, Qt.LeftButton)
        assert main_window.central_widget.currentWidget() == main_window.menu_page

    def test_state_updates(self, qtbot, main_window):
        """Test window updates on state changes."""
        # Test initializing state
        main_window.test_controller.state_manager.update_state(TestState.INITIALIZING)
        qtbot.wait(100)  # Allow UI to update
        assert main_window.statusBar().currentMessage() == "Initializing..."

        # Test running state
        main_window.test_controller.state_manager.update_state(TestState.RUNNING)
        qtbot.wait(100)
        assert main_window.statusBar().currentMessage() == "Running test..."

        # Test completed state
        main_window.test_controller.state_manager.update_state(TestState.COMPLETED)
        qtbot.wait(100)
        assert main_window.statusBar().currentMessage() == "Test completed"

    def test_error_handling(self, qtbot, main_window):
        """Test error state handling."""
        # Simulate error state
        main_window.test_controller.state_manager.update_state(TestState.FAILED)
        qtbot.wait(100)
        assert main_window.statusBar().currentMessage() == "Test failed"
        assert "error" in main_window.statusBar().styleSheet().lower()
