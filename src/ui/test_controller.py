from PyQt5.QtCore import QObject, QThread, pyqtSignal
from PIL import Image
from ..core.display import DisplayManager
import logging

logger = logging.getLogger(__name__)

class TestWorker(QObject):
    """Worker for running barcode tests in a separate thread."""

    finished = pyqtSignal()
    progress = pyqtSignal(int)
    error = pyqtSignal(str)
    preview = pyqtSignal(Image.Image)  # Add preview signal

    def __init__(self, config, virtual=False):
        super().__init__()
        self.config = config
        self.virtual = virtual
        self.display = None
        self._running = True

    def run(self):
        """Run the test sequence."""
        try:
            # Initialize display
            self.display = DisplayManager.get_display(virtual=self.virtual)

            # Run test sequence
            total_steps = len(self.config.get('images', []))
            for i, image in enumerate(self.config.get('images', []), 1):
                if not self._running:
                    break

                self.progress.emit(int(100 * i / total_steps))
                self.display_image(image)

            self.progress.emit(100)
            self.finished.emit()

        except Exception as e:
            logger.error("Test failed: %s", e)
            self.error.emit(str(e))

    def stop(self):
        """Stop the test sequence."""
        self._running = False

    def display_image(self, image):
        """Display an image on the e-ink screen and emit preview."""
        if self.display:
            self.display.display_image(image)
            self.preview.emit(image)  # Emit the image for preview

class TestController(QObject):
    """Controls test execution and manages worker threads."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.thread = None
        self.worker = None

    def start_test(self, config, virtual=False):
        """Start a new test sequence.

        Args:
            config (dict): Test configuration
            virtual (bool): Use virtual display
        """
        # Stop any existing test
        self.stop_test()

        # Create worker and thread
        self.thread = QThread()
        self.worker = TestWorker(config, virtual)
        self.worker.moveToThread(self.thread)

        # Connect signals
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        # Start the thread
        self.thread.start()

    def stop_test(self):
        """Stop the current test if running."""
        if self.worker:
            self.worker.stop()

        if self.thread:
            self.thread.quit()
            self.thread.wait()
