#!/usr/bin/env python3
# File: app.py
"""
Central entry point for E-ink Barcode Testing application.
Provides access to both GUI and CLI modes.

Examples:
    # Run GUI mode
    python app.py
    
    # Run CLI mode with quick test
    python app.py quick-test --type code128 --rotate 45
    
    # Run CLI mode with custom test
    python app.py custom-test --files examples/Code128/*.png --mirror
    
    # Run CLI mode to generate barcodes
    python app.py generate --type code128 --quantity 10
"""
import sys
import os
import logging
import argparse
import asyncio
import traceback

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s'
)
logger = logging.getLogger(__name__)

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='E-ink Barcode Testing Application'
    )
    
    # Common arguments
    parser.add_argument('--virtual', action='store_true',
                      help='Use virtual display instead of hardware (default: use hardware)')
    
    # Create subparsers for commands
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Add GUI command
    gui_parser = subparsers.add_parser(
        'gui', 
        help='Run in GUI mode (default if no command is specified)'
    )
    
    # Import CLI parsers
    # We do the import here to avoid circular imports
    # and to keep the CLI logic in scripts/run_cli.py
    sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
    from scripts.run_cli import (
        add_quick_test_parser,
        add_custom_test_parser, 
        add_generate_parser
    )
    
    # Add CLI command parsers
    add_quick_test_parser(subparsers)
    add_custom_test_parser(subparsers)
    add_generate_parser(subparsers)
    
    return parser.parse_args()

async def run_cli_command(args):
    """Run a CLI command."""
    from scripts.run_cli import CommandLineTester
    
    # Create tester
    tester = CommandLineTester(use_virtual=args.virtual)
    
    try:
        # Initialize for test commands
        if args.command in ['quick-test', 'custom-test']:
            logger.info("Initializing...")
            if not await tester.initialize():
                logger.error("Initialization failed")
                return 1
        
        # Run appropriate command
        if args.command == 'quick-test':
            results = await tester.run_quick_test(args)
        elif args.command == 'custom-test':
            results = await tester.run_custom_test(args)
        elif args.command == 'generate':
            results = await tester.run_barcode_generation(args)
        else:
            logger.error(f"Unknown command: {args.command}")
            return 1
        
        # Print results
        if results['success']:
            if args.command == 'generate':
                print(f"\nBarcode generation completed successfully")
                print(f"  - Output location: {results['output_dir']}")
                print(f"  - {results['message']}")
            else:
                print(f"\nTest completed successfully")
                print(f"  - Images processed: {results['successful_images']}/{results['total_images']}")
                print(f"  - Elapsed time: {results.get('elapsed_time', 0):.1f} seconds")
            return 0
        else:
            print(f"\nOperation failed: {results.get('error', 'Unknown error')}")
            return 1
            
    except KeyboardInterrupt:
        print("\nOperation interrupted by user")
        return 1
        
    except Exception as e:
        logger.error(f"Error: {e}")
        logger.debug(traceback.format_exc())
        return 1
        
    finally:
        # Ensure cleanup for test commands
        if args.command in ['quick-test', 'custom-test']:
            await tester.cleanup()

def run_gui_mode(args):
    """Run the application in GUI mode."""
    from scripts.run_app import Application
    
    # Create and run the application
    app = Application(use_virtual=args.virtual)
    return app.run()

def main():
    """Main entry point."""
    args = parse_arguments()
    
    # Default to GUI if no command specified
    if not args.command:
        args.command = 'gui'
    
    try:
        if args.command == 'gui':
            # Run GUI mode
            return run_gui_mode(args)
        else:
            # Run CLI mode
            return asyncio.run(run_cli_command(args))
    except KeyboardInterrupt:
        print("\nExiting...")
        return 1
    except Exception as e:
        logger.error(f"Application error: {e}")
        logger.debug(traceback.format_exc())
        return 1

if __name__ == "__main__":
    sys.exit(main())
