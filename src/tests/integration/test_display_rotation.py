import pytest
from PIL import Image
import numpy as np
from src.tests.base_test import BaseIntegrationTestCase
from src.core.display_manager import create_display_manager, DisplayConfig
from src.core.state_manager import StateManager

class TestDisplayRotation(BaseIntegrationTestCase):
    @pytest.fixture(autouse=True)
    async def setup_display(self):
        """Set up display manager for each test."""
        self.state_manager = StateManager()
        self.display_config = DisplayConfig(
            virtual=True,
            vcom=-2.02,
            dimensions=(800, 600)
        )
        self.display_manager = create_display_manager(
            state_manager=self.state_manager,
            config=self.display_config
        )
        await self.display_manager.initialize()
        yield
        await self.display_manager.cleanup()

    @pytest.fixture
    def test_image(self):
        """Create a test image with a recognizable pattern."""
        img = self.create_test_image(size=(100, 50), color=255)
        # Add a diagonal line for orientation testing
        for i in range(min(img.size)):
            img.putpixel((i, i), 0)
        return img

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_rotation_0(self, test_image):
        """Test image display with no rotation."""
        await self.display_manager.display_image(
            test_image,
            {"rotation": 0}
        )

        displayed_image = self.display_manager.get_current_image()
        assert displayed_image.size == test_image.size
        assert self.compare_images(displayed_image, test_image)

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_rotation_90(self, test_image):
        """Test image display with 90-degree rotation."""
        await self.display_manager.display_image(
            test_image,
            {"rotation": 90}
        )

        displayed_image = self.display_manager.get_current_image()
        assert displayed_image.size == (test_image.size[1], test_image.size[0])

        # Convert to numpy arrays for comparison
        original = np.array(test_image)
        rotated = np.array(displayed_image)
        assert rotated.shape == (original.shape[1], original.shape[0])

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_rotation_180(self, test_image):
        """Test image display with 180-degree rotation."""
        await self.display_manager.display_image(
            test_image,
            {"rotation": 180}
        )

        displayed_image = self.display_manager.get_current_image()
        assert displayed_image.size == test_image.size

        # Convert to numpy arrays for comparison
        original = np.array(test_image)
        rotated = np.array(displayed_image)
        assert np.array_equal(rotated, np.flip(np.flip(original, 0), 1))

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_rotation_270(self, test_image):
        """Test image display with 270-degree rotation."""
        await self.display_manager.display_image(
            test_image,
            {"rotation": 270}
        )

        displayed_image = self.display_manager.get_current_image()
        assert displayed_image.size == (test_image.size[1], test_image.size[0])

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_invalid_rotation(self, test_image):
        """Test handling of invalid rotation angles."""
        with pytest.raises(ValueError, match="Rotation must be 0, 90, 180, or 270"):
            await self.display_manager.display_image(
                test_image,
                {"rotation": 45}
            )

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_rotation_sequence(self, test_image):
        """Test sequence of rotations."""
        rotations = [0, 90, 180, 270]
        for rotation in rotations:
            await self.display_manager.display_image(
                test_image,
                {"rotation": rotation}
            )
            await self.verify_display_state()

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_rotation_with_display_config(self, test_image):
        """Test rotation with specific display configuration."""
        config = DisplayConfig(
            virtual=True,
            dimensions=(800, 600),
            vcom=-2.02
        )

        display_manager = create_display_manager(
            state_manager=self.state_manager,
            config=config
        )
        await display_manager.initialize()

        try:
            await display_manager.display_image(
                test_image,
                {"rotation": 90}
            )

            displayed_image = display_manager.get_current_image()
            assert displayed_image.size == (test_image.size[1], test_image.size[0])
        finally:
            await display_manager.cleanup()
