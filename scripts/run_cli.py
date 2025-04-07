#!/usr/bin/env python3
# File: scripts/run_cli.py
"""
Command-line interface for E-ink Barcode Testing without the UI.
Provides full CLI functionality equivalent to all UI features:
- Quick Test: Simple testing with basic options
- Custom Test: Advanced testing with detailed configuration
- Generate: Create and download barcodes using AWS API
"""
import sys
import os
import logging
import asyncio
import argparse
import json
from typing import Dict, Any, List, Optional

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.controller import TestController, TestState
from src.core.config import TestConfig
from src.core.display import create_display
from src.core.image_transform import create_transform_pipeline
from src.utils.barcode_api import generate_barcodes
from src.utils.download import download_and_unzip_s3_file

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s'
)
logger = logging.getLogger(__name__)

class CommandLineTester:
    """Command-line test runner with full UI feature equivalence."""
    
    def __init__(self, use_virtual=False):
        """Initialize test runner.
        
        Args:
            use_virtual (bool): Whether to use virtual display instead of hardware
        """
        self.use_virtual = use_virtual
        self.controller = TestController()
        self.controller.register_observer(self.on_state_change)
        
    def on_state_change(self, state, context):
        """Handle state changes.
        
        Args:
            state: Current test state
            context: Context data for the state
        """
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
        """Initialize the controller.
        
        Returns:
            bool: True if initialization was successful
        """
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
        
    def find_images(self, directory='examples', barcode_type=None):
        """Find images in the directory with optional barcode type filtering.
        
        Args:
            directory: Directory to search
            barcode_type: Optional barcode type for filtering (e.g., code128, datamatrix)
            
        Returns:
            list: Paths to found images
        """
        images = []
        
        if not os.path.exists(directory):
            logger.warning(f"Directory not found: {directory}")
            return images

        # Define directory mapping for different barcode types (similar to QuickTestPage)
        dir_mapping = {
            "code128": ["code128", "Code128"],
            "upca": ["upca", "UPCA"],
            "upce": ["upce", "UPCE"],
            "datamatrix": ["datamatrix", "DataMatrix"],
            "qrcode": ["qrcode", "QR Code", "QR_Code"]
        }
        
        # If barcode_type is specified, try to find images in the corresponding subdirectory
        if barcode_type and barcode_type.lower() in dir_mapping:
            for dir_name in dir_mapping[barcode_type.lower()]:
                dir_path = os.path.join(directory, dir_name)
                if os.path.exists(dir_path):
                    # Found the directory, use it instead
                    directory = dir_path
                    break
                    
        # Find images recursively in the directory
        for root, _, files in os.walk(directory):
            for file in files:
                if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                    images.append(os.path.join(root, file))
                    
        images.sort()  # Sort for consistent order
        
        if not images:
            logger.warning(f"No images found in {directory}")
            
        return images
    
    async def run_quick_test(self, args):
        """Run a quick test with the given arguments (similar to QuickTestPage).
        
        Args:
            args: Command line arguments
            
        Returns:
            dict: Test results
        """
        # Find images based on barcode type
        image_paths = self.find_images(args.directory, args.type)
            
        if not image_paths:
            logger.error("No images found for testing")
            return {"success": False, "error": "No images found"}
            
        logger.info(f"Found {len(image_paths)} images for testing")
        
        # Create transformations
        transformations = {
            'rotation': {'angle': args.rotate},
        }
        
        # Handle scaling options
        if args.scale_type == 'relative':
            transformations['scale'] = {'factor': args.scale_factor / 100.0}  # Convert % to factor
        else:  # absolute
            transformations['scale'] = {'width_mm': args.scale_width}
        
        # Always add center transformation like in the UI
        transformations['center'] = {'width': 800, 'height': 600}
            
        # Create test configuration
        config = TestConfig(
            barcode_type=args.type,
            image_paths=image_paths,
            delay_between_images=args.delay,
            transformations=transformations
        )
        
        # Print test info
        print(f"\nRunning Quick Test with the following settings:")
        print(f"  - Barcode Type: {args.type}")
        print(f"  - {len(image_paths)} images from {args.directory}")
        print(f"  - Rotation: {args.rotate}°")
        if args.scale_type == 'relative':
            print(f"  - Scale: {args.scale_factor}%")
        else:
            print(f"  - Scale: {args.scale_width}mm (width)")
        print(f"  - Delay: {args.delay} seconds")
        print(f"  - Using {'virtual' if self.use_virtual else 'hardware'} display")
        
        # Run test
        return await self.controller.run_test(config)
        
    async def run_custom_test(self, args):
        """Run a custom test with the given arguments (similar to CustomTestPage).
        
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
            image_paths = self.find_images(args.directory)
            
        if not image_paths:
            logger.error("No images found for testing")
            return {"success": False, "error": "No images found"}
            
        logger.info(f"Found {len(image_paths)} images for testing")
        
        # Repeat images if requested
        if args.repetitions > 1:
            original_paths = image_paths.copy()
            for _ in range(args.repetitions - 1):
                image_paths.extend(original_paths)
        
        # Create transformations
        transformations = {
            'rotation': {'angle': args.rotate},
        }
        
        # Handle scaling options
        if args.scale_type == 'relative':
            transformations['scale'] = {'factor': args.scale_factor}
        else:  # absolute
            transformations['scale'] = {'width_mm': args.scale_width}
            
        # Add mirror if requested
        if args.mirror:
            transformations['mirror'] = {'horizontal': True}
            
        # Add center if requested
        if args.center:
            transformations['center'] = {'width': 800, 'height': 600}
            
        # Create test configuration
        config = TestConfig(
            barcode_type="Custom",
            image_paths=image_paths,
            delay_between_images=args.delay,
            transformations=transformations
        )
        
        # Print test info
        print(f"\nRunning Custom Test with the following settings:")
        print(f"  - {len(image_paths)} images")
        print(f"  - Rotation: {args.rotate}°")
        if args.scale_type == 'relative':
            print(f"  - Scale: {args.scale_factor}x")
        else:
            print(f"  - Scale: {args.scale_width}mm (width)")
        print(f"  - Mirror: {'Yes' if args.mirror else 'No'}")
        print(f"  - Auto-center: {'Yes' if args.center else 'No'}")
        print(f"  - Delay: {args.delay} seconds")
        print(f"  - Repetitions: {args.repetitions}")
        print(f"  - Using {'virtual' if self.use_virtual else 'hardware'} display")
        
        # Run test
        return await self.controller.run_test(config)
    
    async def run_barcode_generation(self, args):
        """Run barcode generation with the given arguments (similar to BarcodeGeneratePage).
        
        Args:
            args: Command line arguments
            
        Returns:
            dict: Operation results
        """
        config = []
        
        if args.multi_types:
            # Handle multi-type generation
            for type_spec in args.multi_types:
                try:
                    # Split type:quantity format
                    parts = type_spec.split(':')
                    if len(parts) != 2:
                        raise ValueError(f"Invalid format for type spec: {type_spec}. Expected format: type:quantity")
                        
                    barcode_type = parts[0].lower()
                    quantity = int(parts[1])
                    
                    config.append({
                        "img_amount": quantity,
                        "symbology_type": barcode_type,
                        "prefix": args.prefix if args.prefix else "none",
                        "transformation": args.transform
                    })
                except ValueError as e:
                    logger.error(f"Error parsing type specification: {e}")
                    return {"success": False, "error": str(e)}
        else:
            # Handle single type generation
            config.append({
                "img_amount": args.quantity,
                "symbology_type": args.type.lower(),
                "prefix": args.prefix if args.prefix else "none",
                "transformation": args.transform
            })
            
        # Print generation info
        print(f"\nGenerating barcodes with the following settings:")
        for cfg in config:
            print(f"  - {cfg['img_amount']}x {cfg['symbology_type']} barcodes")
            if cfg['prefix'] != "none":
                print(f"    - Prefix: {cfg['prefix']}")
        print(f"  - Transformation: {args.transform}")
        print(f"  - DPI: {args.dpi}")
        print(f"  - Output directory: {args.output_dir}")
        
        try:
            # Show API request
            request_json = json.dumps(config, indent=2)
            logger.info(f"API Request: {request_json}")
            
            # Update progress
            print("Generating barcodes...")
            
            # Call the API service
            s3_url = await generate_barcodes(config)
            
            if s3_url:
                # Download and extract
                print("Downloading generated barcodes...")
                
                success, message = download_and_unzip_s3_file(s3_url, args.output_dir)
                
                if success:
                    print("Barcodes downloaded successfully")
                    return {
                        "success": True, 
                        "message": f"Barcodes generated and downloaded successfully.\n{message}",
                        "output_dir": args.output_dir
                    }
                else:
                    raise RuntimeError(message)
            else:
                print("Failed to get download URL from API")
                return {
                    "success": False, 
                    "error": "Failed to get download URL from API service."
                }
                
        except Exception as e:
            logger.error(f"Error generating barcodes: {e}")
            return {
                "success": False, 
                "error": f"Failed to generate barcodes: {str(e)}"
            }
        
    async def cleanup(self):
        """Clean up resources."""
        await self.controller.cleanup()


def add_quick_test_parser(subparsers):
    """Add a parser for the quick-test command."""
    parser = subparsers.add_parser(
        'quick-test',
        help='Run a quick test with simplified controls',
        description='Quick test mode with simplified barcode testing options'
    )
    
    # Barcode type
    parser.add_argument('--type', type=str, default='code128',
                       choices=['code128', 'upca', 'upce', 'datamatrix', 'qrcode'],
                       help='Barcode type to test')
    
    # Directory
    parser.add_argument('--directory', type=str, default='examples',
                       help='Directory containing test images (default: examples)')
    
    # Rotation
    parser.add_argument('--rotate', type=float, default=0,
                       help='Rotation angle in degrees (default: 0)')
    
    # Scale options
    parser.add_argument('--scale-type', type=str, default='relative',
                       choices=['relative', 'absolute'],
                       help='Scaling type: relative (%) or absolute (mm)')
    
    parser.add_argument('--scale-factor', type=float, default=100,
                       help='Scale factor in percent (default: 100%)')
    
    parser.add_argument('--scale-width', type=float, default=20,
                       help='Width in mm for absolute scaling (default: 20mm)')
    
    # Delay
    parser.add_argument('--delay', type=float, default=0.5,
                       help='Delay between images in seconds (default: 0.5)')

    return parser


def add_custom_test_parser(subparsers):
    """Add a parser for the custom-test command."""
    parser = subparsers.add_parser(
        'custom-test',
        help='Run a custom test with advanced options',
        description='Custom test mode with advanced barcode testing options'
    )
    
    # Image selection
    input_group = parser.add_mutually_exclusive_group()
    input_group.add_argument('--files', type=str, nargs='+',
                           help='Specific image files to test')
    input_group.add_argument('--directory', type=str, default='examples',
                           help='Directory containing test images (default: examples)')
    
    # Transformations
    parser.add_argument('--rotate', type=float, default=0,
                       help='Rotation angle in degrees (default: 0)')
    
    parser.add_argument('--scale-type', type=str, default='relative',
                       choices=['relative', 'absolute'],
                       help='Scaling type: relative (factor) or absolute (mm)')
    
    parser.add_argument('--scale-factor', type=float, default=1.0,
                       help='Scale factor for relative scaling (default: 1.0)')
    
    parser.add_argument('--scale-width', type=float, default=20,
                       help='Width in mm for absolute scaling (default: 20mm)')
    
    parser.add_argument('--mirror', action='store_true',
                       help='Mirror images horizontally')
    
    parser.add_argument('--center', action='store_true',
                       help='Auto-center images on display (default: False)')
    
    # Execution
    parser.add_argument('--delay', type=float, default=1.0,
                       help='Delay between images in seconds (default: 1.0)')
    
    parser.add_argument('--repetitions', type=int, default=1,
                       help='Number of repetitions (default: 1)')

    return parser


def add_generate_parser(subparsers):
    """Add a parser for the generate command."""
    parser = subparsers.add_parser(
        'generate',
        help='Generate barcodes using AWS API',
        description='Generate barcodes with various options'
    )
    
    # Barcode configuration
    generation_group = parser.add_mutually_exclusive_group(required=True)
    
    # Single type
    generation_group.add_argument('--type', type=str,
                               choices=['code128', 'upca', 'upce', 'datamatrix'],
                               help='Barcode type for single type generation')
    
    # Multiple types
    generation_group.add_argument('--multi-types', type=str, nargs='+',
                               metavar='TYPE:QUANTITY',
                               help='Multiple barcode types with quantities (e.g. code128:10 datamatrix:5)')
    
    # Single type quantity
    parser.add_argument('--quantity', type=int, default=10,
                       help='Number of barcodes to generate for single type (default: 10)')
    
    # Common options
    parser.add_argument('--prefix', type=str,
                       help='Prefix for barcode values')
    
    parser.add_argument('--transform', type=str, default='none',
                       choices=['none', 'blur'],
                       help='Transformation effect (default: none)')
    
    parser.add_argument('--dpi', type=int, default=300,
                       choices=[72, 150, 300, 600],
                       help='DPI for generated barcodes (default: 300)')
    
    parser.add_argument('--output-dir', type=str, default='examples',
                       help='Output directory for generated barcodes (default: examples)')

    return parser


async def main():
    """Main entry point."""
    # Create main parser
    parser = argparse.ArgumentParser(
        description='E-ink Barcode Testing Command Line Interface'
    )
    
    # Common arguments for all commands
    parser.add_argument('--virtual', action='store_true',
                      help='Use virtual display instead of hardware (default: use hardware)')
    
    # Create subparsers for commands
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Add parsers for each command
    add_quick_test_parser(subparsers)
    add_custom_test_parser(subparsers)
    add_generate_parser(subparsers)
    
    args = parser.parse_args()
    
    # If no command is provided, show help
    if not args.command:
        parser.print_help()
        return 1
    
    # Create tester
    tester = CommandLineTester(use_virtual=args.virtual)
    
    try:
        # Initialize (only for test commands, not needed for generate)
        if args.command in ['quick-test', 'custom-test']:
            logger.info("Initializing...")
            if not await tester.initialize():
                logger.error("Initialization failed")
                return 1
            
        # Run appropriate command
        if args.command == 'quick-test':
            results = await tester.run_quick_test(args)
            
            # Print results
            if results['success']:
                print(f"\nQuick test completed successfully")
                print(f"  - Images processed: {results['successful_images']}/{results['total_images']}")
                print(f"  - Elapsed time: {results.get('elapsed_time', 0):.1f} seconds")
                return 0
            else:
                print(f"\nTest failed: {results.get('error', 'Unknown error')}")
                return 1
                
        elif args.command == 'custom-test':
            results = await tester.run_custom_test(args)
            
            # Print results
            if results['success']:
                print(f"\nCustom test completed successfully")
                print(f"  - Images processed: {results['successful_images']}/{results['total_images']}")
                print(f"  - Elapsed time: {results.get('elapsed_time', 0):.1f} seconds")
                return 0
            else:
                print(f"\nTest failed: {results.get('error', 'Unknown error')}")
                return 1
                
        elif args.command == 'generate':
            results = await tester.run_barcode_generation(args)
            
            # Print results
            if results['success']:
                print(f"\nBarcode generation completed successfully")
                print(f"  - Output location: {results['output_dir']}")
                print(f"  - {results['message']}")
                return 0
            else:
                print(f"\nGeneration failed: {results.get('error', 'Unknown error')}")
                return 1
                
        return 0
            
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
        return 1
        
    except Exception as e:
        logger.error(f"Error: {e}")
        return 1
        
    finally:
        # Ensure cleanup for test commands
        if args.command in ['quick-test', 'custom-test'] and tester:
            await tester.cleanup()

if __name__ == "__main__":
    try:
        sys.exit(asyncio.run(main()))
    except KeyboardInterrupt:
        print("\nExiting...")
        sys.exit(1)
