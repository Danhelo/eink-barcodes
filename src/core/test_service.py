"""
Core test service module for managing E-ink display test execution.

This module provides the primary interface between the UI and backend test infrastructure.
It handles test configuration, execution, and result management with support for both
quick tests and custom test scenarios.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any, List
from enum import Enum
import asyncio
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestMode(Enum):
    """Test execution modes supported by the system"""
    QUICK = "quick"  # Pre-configured test with minimal parameters
    CUSTOM = "custom"  # Full parameter control test

@dataclass
class ImageTransform:
    """Configuration for image transformations applied during testing"""
    rotation: float = 0.0  # Rotation angle in degrees
    scale: float = 1.0    # Scale factor (1.0 = original size)
    mirror: bool = False  # Mirror image horizontally

    def to_dict(self) -> Dict[str, Any]:
        """Convert transform settings to dictionary format for backend"""
        return {
            "rotation": self.rotation,
            "scale": self.scale,
            "mirror": self.mirror
        }

@dataclass
class TestConfig:
    """Complete test configuration parameters"""
    mode: TestMode
    barcode_type: str
    transforms: ImageTransform
    barcode_path: Optional[str] = None  # Path for pre-generated barcodes
    presigned_url: Optional[str] = None # URL for remote barcode generation

    # Optional parameters for custom tests
    num_iterations: int = 1
    delay_between_tests: float = 0.0

    def validate(self) -> List[str]:
        """
        Validate configuration parameters
        Returns list of validation error messages (empty if valid)
        """
        errors = []

        if not self.barcode_type:
            errors.append("Barcode type must be specified")

        if self.mode == TestMode.QUICK and not self.barcode_path:
            errors.append("Quick test requires barcode path")

        if self.mode == TestMode.CUSTOM and not self.presigned_url:
            errors.append("Custom test requires presigned URL")

        if self.num_iterations < 1:
            errors.append("Number of iterations must be >= 1")

        if self.delay_between_tests < 0:
            errors.append("Delay between tests must be >= 0")

        return errors

class TestService:
    """
    Core service for managing test execution

    This class handles:
    - Test configuration validation and normalization
    - Backend server lifecycle management
    - Test execution and monitoring
    - Result aggregation and reporting
    """

    def __init__(self):
        """Initialize test service with default configuration"""
        self.backend = None  # Lazy-loaded backend interface
        self._active_test = None
        self._test_results = []

    async def initialize(self):
        """Initialize backend components and verify connectivity"""
        try:
            # Lazy-load backend to avoid circular imports
            from backend_interface import BackendInterface
            self.backend = BackendInterface()
            await self.backend.start_server()
            logger.info("Backend server initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize backend: {e}")
            raise RuntimeError(f"Backend initialization failed: {e}")

    async def run_test(self, config: TestConfig) -> Dict[str, Any]:
        """
        Execute test with given configuration

        Args:
            config: Complete test configuration

        Returns:
            Dictionary containing test results and metadata

        Raises:
            ValueError: If configuration validation fails
            RuntimeError: If test execution fails
        """
        # Validate configuration
        if errors := config.validate():
            raise ValueError(f"Invalid test configuration: {', '.join(errors)}")

        self._active_test = config

        try:
            # Ensure backend is initialized
            if not self.backend:
                await self.initialize()

            # Convert TestConfig to backend format
            backend_config = self._create_backend_config(config)

            # Execute test iterations
            results = []
            for i in range(config.num_iterations):
                if i > 0 and config.delay_between_tests > 0:
                    await asyncio.sleep(config.delay_between_tests)

                result = await self.backend.send_test_config(backend_config)
                results.append(result)

            # Aggregate results
            aggregated = self._aggregate_results(results)
            self._test_results.append(aggregated)

            return {
                "status": "success",
                "results": aggregated,
                "metadata": {
                    "config": config.__dict__,
                    "timestamp": aggregated["timestamp"]
                }
            }

        except Exception as e:
            logger.error(f"Test execution failed: {e}")
            return {
                "status": "error",
                "message": str(e),
                "metadata": {
                    "config": config.__dict__
                }
            }

        finally:
            self._active_test = None

    def _create_backend_config(self, config: TestConfig) -> Dict[str, Any]:
        """Convert TestConfig to backend-compatible format"""
        backend_config = {
            "command": "Display Barcode",
            "Presigned URL": config.presigned_url or "",
            "pre-test": "no",
            "known_barcode": "yes" if config.mode == TestMode.QUICK else "no",
            "barcode-type": config.barcode_type,
            "socket-type": "ss",
            "transformations": config.transforms.to_dict()
        }

        if config.barcode_path:
            backend_config["barcode_path"] = str(Path(config.barcode_path))

        return backend_config

    def _aggregate_results(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Aggregate multiple test iteration results

        Combines timing data, success rates, and error information from
        multiple test iterations into a single result summary.
        """
        import time

        total_success = sum(1 for r in results if r.get("status") == "success")

        return {
            "timestamp": time.time(),
            "total_iterations": len(results),
            "successful_iterations": total_success,
            "success_rate": total_success / len(results) if results else 0,
            "average_duration": sum(r.get("duration", 0) for r in results) / len(results) if results else 0,
            "errors": [r.get("error") for r in results if r.get("error")],
            "individual_results": results
        }

    def get_test_history(self) -> List[Dict[str, Any]]:
        """Return history of completed test results"""
        return self._test_results.copy()

    def clear_test_history(self):
        """Clear stored test result history"""
        self._test_results.clear()

    async def cleanup(self):
        """Clean up backend resources"""
        if self.backend:
            await self.backend.cleanup()
            self.backend = None
