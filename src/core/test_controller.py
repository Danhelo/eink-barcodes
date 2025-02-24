"""
Test execution controller.
"""
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import logging
import uuid
import asyncio

from .state_manager import StateManager, TestState, TestContext
from .display_manager import DisplayManager, DisplayConfig

logger = logging.getLogger(__name__)

@dataclass
class TestConfig:
    """Test configuration parameters"""
    test_id: str
    barcode_type: str
    image_paths: List[str]
    transformations: Dict[str, Any]
    display_config: DisplayConfig

class TestController:
    """Manages test execution lifecycle"""
    def __init__(self, state_manager: StateManager, display_manager: DisplayManager):
        self.state_manager = state_manager
        self.display_manager = display_manager
        self._current_config: Optional[TestConfig] = None
        self._stop_requested = False

    async def initialize_test(self, config: TestConfig) -> bool:
        """Initialize test with configuration"""
        try:
            if not self.state_manager.can_transition_to(TestState.INITIALIZING):
                raise ValueError("Invalid state transition")

            self.state_manager.update_state(TestState.INITIALIZING)
            self._current_config = config
            self._stop_requested = False

            # Create test context
            context = TestContext(
                test_id=config.test_id,
                config=config.__dict__,
                total_images=len(config.image_paths)
            )
            self.state_manager.set_context(context)

            # Initialize display
            if not await self.display_manager.initialize():
                raise RuntimeError("Display initialization failed")

            self.state_manager.update_state(TestState.RUNNING)
            return True

        except Exception as e:
            logger.error(f"Test initialization failed: {e}")
            self.state_manager.update_state(TestState.FAILED, {"error": str(e)})
            return False

    async def execute_test(self) -> bool:
        """Execute current test"""
        if not self._current_config:
            raise ValueError("No test configured")

        try:
            for idx, image_path in enumerate(self._current_config.image_paths):
                if self._stop_requested:
                    logger.info("Test stop requested")
                    self.state_manager.update_state(TestState.STOPPED)
                    return False

                # Update context
                self.state_manager.update_state(TestState.RUNNING, {
                    "current_image": image_path,
                    "progress": (idx + 1) / len(self._current_config.image_paths),
                    "processed_images": idx + 1
                })

                # Display image
                if not await self.display_manager.display_image(
                    image_path,
                    self._current_config.transformations
                ):
                    raise RuntimeError(f"Failed to display image: {image_path}")

                # Small delay between images
                await asyncio.sleep(0.1)

            self.state_manager.update_state(TestState.COMPLETED)
            return True

        except Exception as e:
            logger.error(f"Test execution failed: {e}")
            self.state_manager.update_state(TestState.FAILED, {"error": str(e)})
            return False

    async def stop_test(self) -> None:
        """Stop current test"""
        self._stop_requested = True
        if self.state_manager.can_transition_to(TestState.STOPPED):
            self.state_manager.update_state(TestState.STOPPED)
            await self.display_manager.clear()

    async def cleanup(self) -> None:
        """Cleanup resources"""
        try:
            await self.display_manager.cleanup()
            self._current_config = None
            self._stop_requested = False
            self.state_manager.clear_context()
            self.state_manager.update_state(TestState.NOT_STARTED)
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")
            self.state_manager.update_state(TestState.FAILED, {"error": str(e)})

    @staticmethod
    def create_config(
        barcode_type: str,
        image_paths: List[str],
        transformations: Dict[str, Any] = None,
        display_config: DisplayConfig = None
    ) -> TestConfig:
        """Create test configuration"""
        return TestConfig(
            test_id=str(uuid.uuid4()),
            barcode_type=barcode_type,
            image_paths=image_paths,
            transformations=transformations or {},
            display_config=display_config or DisplayConfig()
        )

    def get_current_config(self) -> Optional[TestConfig]:
        """Get current test configuration"""
        return self._current_config
