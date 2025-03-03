#!/usr/bin/env python3
# File: scripts/run_cli.py
"""
Command-line interface for E-ink Barcode Testing without the UI.
"""
import sys
import os
import logging
import asyncio
import argparse

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.controller import TestController, TestState
from src.core.config import TestConfig
from src.core.display import create_display
from src.core.image_transform import create_transform_pipeline

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s'
)
logger = logging.getLogger(__name__)

class CommandLineTester:
    """Command-line test runner."""
    
    def __init__(self, use_virtual=False):
        """Initialize test runner."""
        self.use_virtual = use_virtual
        self.controller = TestController()
        self.controller.register_observer(self.on_state_change)
        
    def on_state_change(self, state, context):
        """Handle state changes."""
        if state == TestState.RUNNING:
            progress = context.get('progress', 0.0)
            status = context.get('status', '')
            bar = self._create_progress_bar(progress)
            print(f"\r{state.name}: {bar} {progress:.1%} - {status}", end="", flush=True)
        else:
            print(f"\n{state.name}: {context.get('status', '')}")

    def _create_progress_bar(self, progress, width=30):
        """Create a text-based progress bar.
        
        Args:
            progress: Progress value (0.0-1.0)
            width: Width of the progress bar
            
        Returns:
            str: Text-based progress bar
        """
        filled = int(width * progress)
        bar = f"[{'#' * filled}{' ' * (width - filled)}]"
        return bar
        
    async def initialize(self):
        """Initialize the controller."""
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
        logger.info(f"Initializing with {'virtual' if self.use_virtual else 'hardware'} display...")
        return await self.controller.initialize(display_factory, transform_factory)
        
    def find_images(self, directory='examples'):
        """Find images in the directory.
        
        Args:
            directory: Directory to search
            
        Returns:
            list: Paths to found images
        """
        images = []
        
        if not os.path.exists(directory):
            logger.warning(f"Directory not found: {directory}")
            return images
            
        for file in os.listdir(directory):
            if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                images.append(os.path.join(directory, file))
                
        images.sort()  # Sort for consistent order
        
        if not images:
            logger.warning(f"No images found in {directory}")
            
        return images
        
    async def run_test(self, args):
        """Run a test with the given arguments.
        
        Args:
            args: Command line arguments
            
        Returns:
            dict: Test results
        """
        # Find images
        if args.files:
            # Use provided files
            image_paths = args.files
        else:
            # Find images in directory
            image_paths = self.find_images(args.dir)
            
        if not image_paths:
            logger.error("No images found for testing")
            return {"success": False, "error": "No images found"}
            
        logger.info(f"Found {len(image_paths)} images for testing")
        
        # Create transformations
        transformations = {
            'rotation': {'angle': args.rotate},
            'scale': {'factor': args.scale}
        }
        
        if args.center:
            transformations['center'] = {'width': 800, 'height': 600}
            
        if args.mirror:
            transformations['mirror'] = {'horizontal': True}
            
        # Create test configuration
        config = TestConfig(
            barcode_type=args.type,
            image_paths=image_paths,
            delay_between_images=args.delay,
            transformations=transformations
        )
        
        # Print test info
        print(f"\nRunning test with the following settings:")
        print(f"  - {len(image_paths)} images")
        print(f"  - Type: {args.type}")
        print(f"  - Rotation: {args.rotate}°")
        print(f"  - Scale: {args.scale}x")
        print(f"  - Delay: {args.delay} seconds")
        print(f"  - Using {'virtual' if self.use_virtual else 'hardware'} display")
        
        # Run test
        return await self.controller.run_test(config)
        
    async def cleanup(self):
        """Clean up resources."""
        await self.controller.cleanup()

async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='E-ink Barcode Testing Command Line Interface'
    )
    
    # Display options
    parser.add_argument('--virtual', action='store_true',
                      help='Use virtual display instead of hardware (default: use hardware)')
    
    # Test parameters
    parser.add_argument('--dir', type=str, default='examples',
                      help='Directory containing test images (default: examples)')
    parser.add_argument('--files', type=str, nargs='+',
                      help='Specific image files to test (overrides --dir)')
    parser.add_argument('--type', type=str, default='Standard',
                      help='Barcode type name (default: Standard)')
    parser.add_argument('--rotate', type=float, default=0,
                      help='Rotation angle in degrees (default: 0)')
    parser.add_argument('--scale', type=float, default=1.0,
                      help='Scale factor (default: 1.0)')
    parser.add_argument('--delay', type=float, default=1.0,
                      help='Delay between images in seconds (default: 1.0)')
    parser.add_argument('--center', action='store_true',
                      help='Auto-center images on display (default: False)')
    parser.add_argument('--mirror', action='store_true',
                      help='Mirror images horizontally (default: False)')
    
    args = parser.parse_args()
    
    # Create tester
    tester = CommandLineTester(use_virtual=args.virtual)
    
    try:
        # Initialize
        logger.info("Initializing...")
        if not await tester.initialize():
            logger.error("Initialization failed")
            return 1
            
        # Run test
        logger.info("Running test...")
        results = await tester.run_test(args)
        
        # Print results
        if results['success']:
            print(f"\nTest completed successfully")
            print(f"  - Images processed: {results['successful_images']}/{results['total_images']}")
            print(f"  - Elapsed time: {results.get('elapsed_time', 0):.1f} seconds")
            return 0
        else:
            print(f"\nTest failed: {results.get('error', 'Unknown error')}")
            return 1
            
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
        return 1
        
    except Exception as e:
        logger.error(f"Error: {e}")
        return 1
        
    finally:
        # Ensure cleanup
        await tester.cleanup()

if __name__ == "__main__":
    try:
        sys.exit(asyncio.run(main()))
    except KeyboardInterrupt:
        print("\nExiting...")
        sys.exit(1)