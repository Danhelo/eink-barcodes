#!/usr/bin/env python3
# File: scripts/test_integration.py
"""
Integration test for core components and UI.
"""
import sys
import os
import logging
import asyncio
import argparse
from PIL import Image
import tempfile

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.controller import TestController, TestState
from src.core.display import create_display
from src.core.image_transform import create_transform_pipeline
from src.core.config import TestConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def run_integration_test():
    """Run an integration test of core components."""
    print("Starting integration test...")
    
    # Create test images
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create test images
        image_paths = []
        for i in range(3):
            img = Image.new('L', (200, 100), 255)
            # Add some patterns
            for x in range(0, 200, 10):
                for y in range(100):
                    if (x + i * 10) % 30 < 10:
                        img.putpixel((x, y), 0)
            
            path = os.path.join(temp_dir, f'test_image_{i}.png')
            img.save(path)
            image_paths.append(path)
            print(f"Created test image: {path}")
        
        # Create controller
        controller = TestController()
        
        # Store state changes
        state_changes = []
        def state_observer(state, context):
            state_changes.append((state, context.get('progress', 0.0)))
            
        controller.register_observer(state_observer)
        
        try:
            # Initialize controller
            print("Initializing controller...")
            success = await controller.initialize(
                lambda: create_display({'virtual': True}),
                create_transform_pipeline
            )
            
            if not success:
                print("Failed to initialize controller")
                return False
                
            # Create test configuration
            config = TestConfig(
                barcode_type="Test",
                image_paths=image_paths,
                delay_between_images=0.1,
                transformations={
                    'rotation': {'angle': 90},
                    'scale': {'factor': 1.2},
                    'center': {'width': 800, 'height': 600}
                }
            )
            
            # Run test
            print("Running test...")
            results = await controller.run_test(config)
            
            # Verify results
            if not results['success']:
                print(f"Test failed: {results.get('error', 'Unknown error')}")
                return False
                
            print(f"Test completed successfully")
            print(f"  - Images processed: {results['successful_images']}/{results['total_images']}")
            
            # Verify state transitions
            expected_states = [TestState.IDLE, TestState.RUNNING, TestState.COMPLETED]
            actual_states = [s[0] for s in state_changes]
            
            print("State transitions:")
            for i, (state, progress) in enumerate(state_changes):
                print(f"  {i}: {state.name} ({progress:.1%})")
                
            # Check if we hit all expected states
            for expected in expected_states:
                if expected not in actual_states:
                    print(f"Missing expected state: {expected}")
                    return False
                    
            # Check progress reporting
            final_progress = state_changes[-1][1]
            if final_progress < 0.99:  # Allow some floating-point imprecision
                print(f"Final progress not reached: {final_progress:.1%}")
                return False
                
            return True
            
        finally:
            # Clean up
            await controller.cleanup()

if __name__ == "__main__":
    try:
        success = asyncio.run(run_integration_test())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\nTest interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)