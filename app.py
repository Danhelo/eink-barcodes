#!/usr/bin/env python3
"""
Main application entry point.
"""
import sys
import logging
import asyncio
import signal
import qasync
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt, QTimer

from src.ui.main_window import MainWindow
from src.core.display_manager import DisplayManager, DisplayConfig
from src.core.state_manager import StateManager
from src.core.test_controller import TestController

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

class Application:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.loop = None
        self.window = None
        self.display_manager = None
        self.test_controller = None
        self.state_manager = None
        self._cleanup_in_progress = False

    async def cleanup(self):
        """Asynchronous cleanup of resources"""
        if self._cleanup_in_progress:
            return

        self._cleanup_in_progress = True
        logger.info("Starting cleanup...")

        try:
            if self.display_manager:
                await self.display_manager.cleanup()

            if self.test_controller:
                await self.test_controller.cleanup()

            if self.window:
                self.window.close()

        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
        finally:
            self._cleanup_in_progress = False
            logger.info("Cleanup complete")

    def shutdown(self):
        """Initiate shutdown sequence"""
        logger.info("Shutting down...")
        if self.loop and self.loop.is_running():
            self.loop.create_task(self.cleanup())
            # Use QTimer to ensure we exit after cleanup
            QTimer.singleShot(500, self.app.quit)

    async def initialize(self):
        """Initialize application components"""
        try:
            # Initialize state manager first
            self.state_manager = StateManager()

            # Initialize display manager
            display_config = DisplayConfig(vcom=-2.06)

            # Create and initialize the display manager
            # DisplayManager.create() returns an already initialized instance
            display_manager = DisplayManager(
                state_manager=self.state_manager,
                config=display_config
            )
            await display_manager.initialize()
            self.display_manager = display_manager

            # Initialize test controller
            self.test_controller = TestController(
                state_manager=self.state_manager,
                display_manager=self.display_manager
            )

            # Initialize the test controller
            await self.test_controller.initialize()

            # Create main window
            self.window = MainWindow(self.test_controller)
            self.window.show()

            return True

        except Exception as e:
            logger.error(f"Initialization error: {e}")
            await self.cleanup()
            return False

    def run(self):
        """Run the application"""
        try:
            # Create and set event loop
            self.loop = qasync.QEventLoop(self.app)
            asyncio.set_event_loop(self.loop)

            # Set up signal handlers
            for sig in (signal.SIGINT, signal.SIGTERM):
                self.loop.add_signal_handler(
                    sig,
                    self.shutdown
                )

            # Initialize components
            init_success = self.loop.run_until_complete(self.initialize())
            if not init_success:
                return 1

            # Run event loop
            with self.loop:
                return self.loop.run_forever()

        except Exception as e:
            logger.error(f"Application error: {e}")
            return 1

def main():
    """Main application entry point"""
    app = Application()
    sys.exit(app.run())

if __name__ == '__main__':
    main()
