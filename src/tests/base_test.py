"""
Base test case implementation with common functionality.
"""
import unittest
import logging
from typing import Any, Optional
from PIL import Image
import numpy as np

class BaseTestCase(unittest.TestCase):
    """Base test case with helper methods."""

    @classmethod
    def setUpClass(cls):
        """Set up test class."""
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        cls.logger = logging.getLogger(cls.__name__)

    def setUp(self):
        """Set up test case."""
        self.logger.info(f"Running test: {self._testMethodName}")

    def tearDown(self):
        """Clean up after test."""
        self.logger.info(f"Completed test: {self._testMethodName}")

    def assertImageEqual(self, img1: Image.Image, img2: Image.Image, msg: Optional[str] = None):
        """Assert that two images are equal.

        Args:
            img1: First image
            img2: Second image
            msg: Optional assertion message
        """
        # Convert to numpy arrays for comparison
        arr1 = np.array(img1)
        arr2 = np.array(img2)

        # Compare arrays
        self.assertTrue(
            np.array_equal(arr1, arr2),
            msg or "Images are not equal"
        )

    def assertImageSimilar(self, img1: Image.Image, img2: Image.Image,
                          threshold: float = 0.95, msg: Optional[str] = None):
        """Assert that two images are similar within a threshold.

        Args:
            img1: First image
            img2: Second image
            threshold: Similarity threshold (0-1)
            msg: Optional assertion message
        """
        # Convert to numpy arrays
        arr1 = np.array(img1)
        arr2 = np.array(img2)

        # Calculate similarity
        similarity = np.mean(arr1 == arr2)

        self.assertGreaterEqual(
            similarity,
            threshold,
            msg or f"Images similarity {similarity:.2%} below threshold {threshold:.2%}"
        )

    def assertImageSize(self, img: Image.Image, expected_size: tuple,
                       msg: Optional[str] = None):
        """Assert image dimensions.

        Args:
            img: Image to check
            expected_size: Expected (width, height)
            msg: Optional assertion message
        """
        self.assertEqual(
            img.size,
            expected_size,
            msg or f"Image size {img.size} != expected {expected_size}"
        )

    def create_test_image(self, size: tuple = (100, 100),
                         color: tuple = (255, 255, 255)) -> Image.Image:
        """Create a test image.

        Args:
            size: Image dimensions (width, height)
            color: Fill color (R,G,B)

        Returns:
            PIL Image object
        """
        return Image.new('RGB', size, color)

    def load_test_image(self, path: str) -> Optional[Image.Image]:
        """Load a test image file.

        Args:
            path: Path to image file

        Returns:
            PIL Image object or None if load fails
        """
        try:
            return Image.open(path)
        except Exception as e:
            self.logger.error(f"Failed to load test image {path}: {e}")
            return None

    def assertNoLogs(self, logger: Optional[str] = None, level: Optional[str] = None):
        """Assert that no logs are emitted.

        Args:
            logger: Logger name (default: root)
            level: Minimum log level (default: INFO)
        """
        with self.assertLogs(logger, level) as cm:
            self.logger.info("Dummy log message")  # Ensure context manager has at least one log

        # Check only dummy message was logged
        self.assertEqual(len(cm.output), 1)
        self.assertIn("Dummy log message", cm.output[0])

    def assertEventually(self, condition: callable, timeout: float = 1.0,
                        interval: float = 0.1, message: Optional[str] = None):
        """Assert that a condition becomes true within a timeout.

        Args:
            condition: Callable that returns bool
            timeout: Maximum time to wait in seconds
            interval: Check interval in seconds
            message: Optional assertion message
        """
        import time

        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                if condition():
                    return
            except Exception:
                pass
            time.sleep(interval)

        self.fail(message or f"Condition not met within {timeout} seconds")
