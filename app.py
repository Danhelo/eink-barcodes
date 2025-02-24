import sys
import asyncio
import logging
from PyQt5.QtWidgets import QApplication
from src.ui.main_window import MainWindow
from src.core.state_manager import StateManager
from src.core.test_controller import TestController
from src.core.display_manager import create_display_manager, DisplayConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def initialize_managers():
    """Initialize all managers"""
    try:
        # Create state manager first
        state_manager = StateManager()

        # Create display manager with default config
        display_manager = create_display_manager(
            state_manager,
            DisplayConfig(vcom=-2.06)  # Adjust VCOM as needed
        )

        # Initialize display
        if not await display_manager.initialize():
            raise RuntimeError("Failed to initialize display")

        # Create test controller
        test_controller = TestController(state_manager, display_manager)
        return test_controller

    except Exception as e:
        logger.error("Failed to initialize managers: %s", str(e))
        raise

def main():
    """Main application entry point"""
    try:
        # Create Qt application
        app = QApplication(sys.argv)

        # Initialize managers
        test_controller = asyncio.run(initialize_managers())

        # Create and show main window
        window = MainWindow(test_controller)
        window.show()

        # Start Qt event loop
        return app.exec_()

    except Exception as e:
        logger.error("Application failed to start: %s", str(e))
        return 1

if __name__ == '__main__':
    sys.exit(main())
