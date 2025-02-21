import sys
import os
import logging
from PyQt5.QtWidgets import QApplication
from src.ui.main_window import MainWindow

def setup_logging():
    """Configure logging for the application."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def main():
    """Main application entry point."""
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)

    # Create required directories if they don't exist
    for path in [
        'known_barcode/Code128',
        'known_barcode/QR Code',
        'known_barcode/DataMatrix'
    ]:
        os.makedirs(path, exist_ok=True)
    
    # Create and run application
    logger.info("Starting application")
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
