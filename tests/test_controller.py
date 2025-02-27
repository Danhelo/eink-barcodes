# File: tests/test_controller.py
import pytest
import asyncio
import os
from PIL import Image

from src.core.controller import TestController, TestState
from src.core.config import TestConfig

@pytest.mark.asyncio
async def test_controller_init():
    """Test controller initialization."""
    controller = TestController()
    
    # Define factories
    def display_factory():
        from src.core.display import VirtualDisplay
        return VirtualDisplay(800, 600)
        
    def transform_factory():
        from src.core.image_transform import create_transform_pipeline
        return create_transform_pipeline()
    
    # Initialize controller
    success = await controller.initialize(display_factory, transform_factory)
    
    assert success is True
    assert controller.get_state() == TestState.IDLE

@pytest.mark.asyncio
async def test_controller_state_observers():
    """Test controller state observers."""
    controller = TestController()
    
    # Track observed states
    observed_states = []
    observed_contexts = []
    
    def observer(state, context):
        observed_states.append(state)
        observed_contexts.append(context)
    
    # Register observer
    controller.register_observer(observer)
    
    # Initialize should trigger state update
    def display_factory():
        from src.core.display import VirtualDisplay
        return VirtualDisplay(800, 600)
        
    def transform_factory():
        from src.core.image_transform import create_transform_pipeline
        return create_transform_pipeline()
    
    await controller.initialize(display_factory, transform_factory)
    
    # Should have received at least two states: initial + after init
    assert len(observed_states) >= 2
    assert observed_states[-1] == TestState.IDLE

@pytest.mark.asyncio
async def test_run_test(test_image):
    """Test running a complete test."""
    controller = TestController()
    
    # Define factories
    def display_factory():
        from src.core.display import VirtualDisplay
        return VirtualDisplay(800, 600)
        
    def transform_factory():
        from src.core.image_transform import create_transform_pipeline
        return create_transform_pipeline()
    
    # Initialize controller
    await controller.initialize(display_factory, transform_factory)
    
    # Save test image to temp file
    os.makedirs('examples', exist_ok=True)
    test_path = os.path.join('examples', 'test_run.png')
    test_image.save(test_path)
    
    # Create test config
    config = TestConfig(
        barcode_type="Test",
        image_paths=[test_path],
        delay_between_images=0.1,
        transformations={
            'rotation': {'angle': 90},
            'scale': {'factor': 1.2}
        }
    )
    
    # Run test
    results = await controller.run_test(config)
    
    # Verify success
    assert results['success'] is True
    assert results['total_images'] == 1
    assert results['successful_images'] == 1
    assert controller.get_state() == TestState.COMPLETED
    
    # Clean up
    if os.path.exists(test_path):
        os.remove(test_path)

@pytest.mark.asyncio
async def test_stop_test(test_image):
    """Test stopping a running test."""
    controller = TestController()
    
    # Define factories
    def display_factory():
        from src.core.display import VirtualDisplay
        return VirtualDisplay(800, 600)
        
    def transform_factory():
        from src.core.image_transform import create_transform_pipeline
        return create_transform_pipeline()
    
    # Initialize controller
    await controller.initialize(display_factory, transform_factory)
    
    # Create a longer test with multiple images
    os.makedirs('examples', exist_ok=True)
    test_paths = []
    for i in range(5):  # Create 5 test images
        path = os.path.join('examples', f'test_stop_{i}.png')
        test_image.save(path)
        test_paths.append(path)
    
    # Create test config with longer delay
    config = TestConfig(
        barcode_type="Test",
        image_paths=test_paths,
        delay_between_images=0.5  # Long enough to call stop
    )
    
    # Start the test
    async def run_test():
        return await controller.run_test(config)
    
    # Start test in background
    task = asyncio.create_task(run_test())
    
    # Wait a bit and then stop
    await asyncio.sleep(0.3)
    stopped = await controller.stop_test()
    
    # Verify test was stopped
    assert stopped is True
    result = await task
    assert result['success'] is False
    assert "cancelled" in result['error'].lower()
    assert controller.get_state() == TestState.STOPPED
    
    # Clean up
    for path in test_paths:
        if os.path.exists(path):
            os.remove(path)