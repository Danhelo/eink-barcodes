#!/usr/bin/env python3
# File: scripts/run_app.py
"""
Main entry point for the E-ink Barcode Testing application.
"""
import sys
import os
import logging
import asyncio
import signal
import argparse
from PyQt5.QtWidgets import QApplication
import qasync

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.controller import TestController
from src.core.display import create_display
from src.core.image_transform import create_transform_pipeline
from src.ui.main_window import MainWindow

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s'
)
logger = logging.getLogger(__name__)

class Application:
    """Main application class."""
    
    def __init__(self, use_virtual=False):
        """Initialize application."""
        self.app = QApplication(sys.argv)
        self.loop = None
        self.window = None
        self.controller = None
        self.use_virtual = use_virtual
        
    async def initialize(self):
        """Initialize application components."""
        try:
            # Create and initialize controller
            self.controller = TestController()
            
            # Define factories
            def display_factory():
                display_config = {
                    'virtual': self.use_virtual,
                    'dimensions': (800, 600),
                    'vcom': -2.06
                }
                return create_display(display_config)
                
            def transform_factory():
                return create_transform_pipeline()
                
            # Initialize controller
            logger.info("Initializing controller...")
            success = await self.controller.initialize(
                display_factory, transform_factory)
                
            if not success:
                logger.error("Failed to initialize controller")
                return False
                
            # Create main window
            logger.info("Creating main window...")
            self.window = MainWindow(self.controller)
            self.window.show()
            
            logger.info("Application initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Initialization error: {e}")
            return False
            
    async def cleanup(self):
        """Clean up resources."""
        logger.info("Cleaning up...")
        
        if self.controller:
            await self.controller.cleanup()
            
        if self.window:
            self.window.close()
            
    def run(self):
        """Run the application."""
        try:
            # Create event loop
            self.loop = qasync.QEventLoop(self.app)
            asyncio.set_event_loop(self.loop)
            
            # Set up signal handlers
            for sig in (signal.SIGINT, signal.SIGTERM):
                self.loop.add_signal_handler(
                    sig, lambda: asyncio.create_task(self.cleanup()))
                    
            # Initialize components
            if not self.loop.run_until_complete(self.initialize()):
                return 1
                
            # Run event loop
            logger.info("Starting application main loop")
            with self.loop:
                return self.loop.run_forever()
                
        except Exception as e:
            logger.error(f"Application error: {e}")
            return 1
            
def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='E-ink Barcode Testing Application'
    )
    parser.add_argument('--virtual', action='store_true',
                      help='Use virtual display instead of hardware (default: use hardware)')
    
    args = parser.parse_args()
    
    app = Application(use_virtual=args.virtual)
    return app.run()
    
if __name__ == "__main__":
    sys.exit(main())