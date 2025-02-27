#!/usr/bin/env python3
# File: run_core_test.py
"""
Test script for core components integration using existing images.
Default to hardware display with virtual fallback.
"""
import asyncio
import logging
import argparse
import os
import sys
from PIL import Image
import time

# Add src to path for imports
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.core.controller import TestController, TestState
from src.core.config import TestConfig
from src.core.display import create_display
from src.core.image_transform import create_transform_pipeline

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class CoreTester:
    """Simple application to test core components."""
    
    def __init__(self, use_virtual: bool = False):  # Changed default to False (use hardware)
        self.controller = TestController()
        self.use_virtual = use_virtual
        
        # Register for state updates
        self.controller.register_observer(self.on_state_change)
        
    def on_state_change(self, state: TestState, context):
        """Handle state changes."""
        status = context.get('status', '')
        if state == TestState.RUNNING:
            progress = context.get('progress', 0.0)
            progress_bar = self._create_progress_bar(progress)
            print(f"\r{state.name}: {progress_bar} {progress:.1%} - {status}", end="")
        else:
            print(f"\n{state.name}: {status}")
            
    def _create_progress_bar(self, progress: float, width: int = 20) -> str:
        """Create a text-based progress bar."""
        filled = int(width * progress)
        return f"[{'█' * filled}{' ' * (width - filled)}]"
        
    async def initialize(self):
        """Initialize the tester."""
        # Create factory for display
        def display_factory():
            display_config = {
                'virtual': self.use_virtual,
                'dimensions': (800, 600),
                'vcom': -2.06,
                'spi_hz': 24000000
            }
            display = create_display(display_config)
            logger.info(f"Using {'virtual' if self.use_virtual else 'hardware'} display")
            return display
            
        # Create factory for transform pipeline
        def transform_factory():
            return create_transform_pipeline()
            
        # Initialize controller
        success = await self.controller.initialize(display_factory, transform_factory)
        
        if not success:
            logger.error("Failed to initialize controller")
            return False
            
        logger.info("Core tester initialized successfully")
        return True
        
    def find_images(self, directory='examples'):
        """Find all image files in the directory."""
        if not os.path.exists(directory):
            logger.warning(f"Directory not found: {directory}")
            return []
            
        image_paths = []
        for file in os.listdir(directory):
            if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                path = os.path.join(directory, file)
                image_paths.append(path)
                logger.info(f"Found image: {path}")
                
        if not image_paths:
            logger.warning(f"No images found in {directory}")
            
        return sorted(image_paths)  # Sort for consistent order
        
    async def run_test(self, rotation: float = 0, scale: float = 1.0, delay: float = 1.0, directory: str = 'examples'):
        """Run a test with the specified parameters."""
        # Find existing images
        image_paths = self.find_images(directory)
        
        if not image_paths:
            print(f"\nNo images found in {directory} directory. Please add some image files.")
            return {"success": False, "error": "No image files found"}
        
        # Create test configuration
        config = TestConfig(
            barcode_type="Test",
            image_paths=image_paths,
            delay_between_images=delay,
            transformations={
                'rotation': {'angle': rotation},
                'scale': {'factor': scale},
                'center': {'width': 800, 'height': 600}
            }
        )
        
        print(f"\nRunning test with:")
        print(f"  - {len(image_paths)} images from {directory}")
        print(f"  - Rotation: {rotation}°")
        print(f"  - Scale: {scale}")
        print(f"  - Delay: {delay}s")
        print(f"  - Using {'virtual' if self.use_virtual else 'hardware'} display")
        
        # Run the test
        results = await self.controller.run_test(config)
        
        # Print results
        if results['success']:
            print(f"\nTest completed: {results['successful_images']}/{results['total_images']} images successful")
        else:
            print(f"\nTest failed: {results.get('error', 'Unknown error')}")
            
        return results
        
    async def stop_example(self, directory: str = 'examples'):
        """Example of stopping a test."""
        # Find existing images
        image_paths = self.find_images(directory)
        
        if not image_paths:
            print(f"\nNo images found in {directory} directory. Please add some image files.")
            return {"success": False, "error": "No image files found"}
        
        # Create test configuration with long delay
        config = TestConfig(
            barcode_type="Test",
            image_paths=image_paths,
            delay_between_images=2.0  # Long delay to allow stopping
        )
        
        print("\nRunning test that will be stopped after 3 seconds...")
        
        # Start test
        task = asyncio.create_task(self.controller.run_test(config))
        
        # Wait 3 seconds then stop
        await asyncio.sleep(3)
        print("\nStopping test...")
        await self.controller.stop_test()
        
        # Wait for test to finish
        results = await task
        
        # Should show as stopped/cancelled
        print(f"\nTest was stopped: {results}")
        
    async def cleanup(self):
        """Clean up resources."""
        await self.controller.cleanup()

async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Test core components')
    # Changed from --hardware to --virtual with inverted meaning
    parser.add_argument('--virtual', action='store_true', 
                        help='Use virtual display instead of hardware')
    parser.add_argument('--rotation', type=float, default=0, 
                        help='Rotation angle in degrees')
    parser.add_argument('--scale', type=float, default=1.0, 
                        help='Scale factor')
    parser.add_argument('--delay', type=float, default=1.0, 
                        help='Delay between images')
    parser.add_argument('--stop-example', action='store_true', 
                        help='Run the stopping example')
    parser.add_argument('--dir', type=str, default='examples', 
                        help='Directory containing image files')
    
    args = parser.parse_args()
    
    # Changed to use args.virtual
    tester = CoreTester(use_virtual=args.virtual)
    
    try:
        # Initialize
        if await tester.initialize():
            if args.stop_example:
                await tester.stop_example(directory=args.dir)
            else:
                await tester.run_test(
                    rotation=args.rotation,
                    scale=args.scale,
                    delay=args.delay,
                    directory=args.dir
                )
    finally:
        # Ensure cleanup
        await tester.cleanup()

if __name__ == "__main__":
    asyncio.run(main())