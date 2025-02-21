"""
Unit tests for test controller functionality.
"""
import unittest
from unittest.mock import Mock, patch, AsyncMock
import asyncio
from pathlib import Path
import tempfile
import json
from datetime import datetime

from src.core.test_controller import TestController
from src.core.test_config import TestConfig
from src.core.display_manager import DisplayManager

class TestTestController(unittest.TestCase):
    """Test suite for TestController class."""

    def setUp(self):
        """Set up test environment."""
        self.test_dir = Path(tempfile.mkdtemp())
        self.config_path = self.test_dir / 'test_config.json'
        self.create_test_config()

    def create_test_config(self):
        """Create test configuration."""
        config = {
            'test_name': 'Test Suite 1',
            'barcode_type': 'Code128',
            'transformations': [
                {'rotation': 0, 'scale': 1.0},
                {'rotation': 90, 'scale': 1.0},
                {'rotation': 180, 'scale': 1.0}
            ],
            'display_mode': 'GC16',
            'update_interval': 1.0
        }

        with open(self.config_path, 'w') as f:
            json.dump(config, f)

    async def async_setup(self):
        """Async setup for tests requiring initialization."""
        # Mock display manager
        self.display_manager = AsyncMock(spec=DisplayManager)
        self.display_manager.initialize = AsyncMock(return_value=True)
        self.display_manager.display_image = AsyncMock(return_value=True)
        self.display_manager.cleanup = AsyncMock()

        # Create controller
        self.controller = TestController(self.display_manager)
        await self.controller.initialize()

    async def async_teardown(self):
        """Async teardown for cleanup."""
        if hasattr(self, 'controller'):
            await self.controller.cleanup()

    def test_initialization(self):
        """Test controller initialization."""
        async def run_test():
            controller = TestController(self.display_manager)

            # Test successful initialization
            self.assertTrue(await controller.initialize())
            self.assertTrue(controller.is_ready)

            # Test double initialization
            self.assertTrue(await controller.initialize())

            await controller.cleanup()

        asyncio.run(run_test())

    def test_config_loading(self):
        """Test configuration loading."""
        async def run_test():
            await self.async_setup()

            # Load valid config
            config = await self.controller.load_config(self.config_path)
            self.assertIsInstance(config, TestConfig)
            self.assertEqual(config.test_name, 'Test Suite 1')
            self.assertEqual(config.barcode_type, 'Code128')

            # Test invalid config path
            with self.assertRaises(FileNotFoundError):
                await self.controller.load_config('nonexistent.json')

            # Test invalid config format
            invalid_config = self.test_dir / 'invalid.json'
            with open(invalid_config, 'w') as f:
                f.write('invalid json')

            with self.assertRaises(json.JSONDecodeError):
                await self.controller.load_config(invalid_config)

            await self.async_teardown()

        asyncio.run(run_test())

    def test_test_execution(self):
        """Test basic test execution flow."""
        async def run_test():
            await self.async_setup()

            # Load and validate config
            config = await self.controller.load_config(self.config_path)
            self.assertTrue(await self.controller.validate_config(config))

            # Start test
            self.assertTrue(await self.controller.start_test(config))
            self.assertTrue(self.controller.is_running)

            # Wait for completion
            while self.controller.is_running:
                await asyncio.sleep(0.1)

            # Verify results
            results = self.controller.get_results()
            self.assertIsNotNone(results)
            self.assertEqual(len(results['transformations']), 3)

            await self.async_teardown()

        asyncio.run(run_test())

    def test_test_cancellation(self):
        """Test test cancellation."""
        async def run_test():
            await self.async_setup()

            # Start test
            config = await self.controller.load_config(self.config_path)
            self.assertTrue(await self.controller.start_test(config))

            # Cancel test
            await self.controller.stop_test()
            self.assertFalse(self.controller.is_running)

            # Verify partial results
            results = self.controller.get_results()
            self.assertIsNotNone(results)
            self.assertTrue(results['cancelled'])

            await self.async_teardown()

        asyncio.run(run_test())

    def test_error_handling(self):
        """Test error handling during test execution."""
        async def run_test():
            await self.async_setup()

            # Simulate display error
            self.display_manager.display_image.side_effect = Exception('Display error')

            # Start test
            config = await self.controller.load_config(self.config_path)
            self.assertTrue(await self.controller.start_test(config))

            # Wait for completion
            while self.controller.is_running:
                await asyncio.sleep(0.1)

            # Verify error handling
            results = self.controller.get_results()
            self.assertTrue(results['error'])
            self.assertIn('Display error', results['error_message'])

            await self.async_teardown()

        asyncio.run(run_test())

    def test_progress_tracking(self):
        """Test progress tracking during test execution."""
        async def run_test():
            await self.async_setup()

            progress_updates = []

            def progress_callback(progress):
                progress_updates.append(progress)

            # Register progress callback
            self.controller.register_progress_callback(progress_callback)

            # Start test
            config = await self.controller.load_config(self.config_path)
            self.assertTrue(await self.controller.start_test(config))

            # Wait for completion
            while self.controller.is_running:
                await asyncio.sleep(0.1)

            # Verify progress updates
            self.assertGreater(len(progress_updates), 0)
            self.assertEqual(progress_updates[-1], 100)

            await self.async_teardown()

        asyncio.run(run_test())

    def test_concurrent_operations(self):
        """Test concurrent test operations."""
        async def run_test():
            await self.async_setup()

            # Try to start multiple tests
            config = await self.controller.load_config(self.config_path)
            self.assertTrue(await self.controller.start_test(config))

            # Second test should fail while first is running
            with self.assertRaises(RuntimeError):
                await self.controller.start_test(config)

            await self.controller.stop_test()
            await self.async_teardown()

        asyncio.run(run_test())

    def test_results_management(self):
        """Test test results management."""
        async def run_test():
            await self.async_setup()

            # Run test
            config = await self.controller.load_config(self.config_path)
            await self.controller.start_test(config)

            # Wait for completion
            while self.controller.is_running:
                await asyncio.sleep(0.1)

            # Get results
            results = self.controller.get_results()

            # Verify result structure
            self.assertIn('test_name', results)
            self.assertIn('start_time', results)
            self.assertIn('end_time', results)
            self.assertIn('transformations', results)
            self.assertIn('success', results)

            # Verify timestamps
            self.assertIsInstance(datetime.fromisoformat(results['start_time']), datetime)
            self.assertIsInstance(datetime.fromisoformat(results['end_time']), datetime)

            # Clear results
            self.controller.clear_results()
            self.assertIsNone(self.controller.get_results())

            await self.async_teardown()

        asyncio.run(run_test())

    def test_config_validation(self):
        """Test configuration validation."""
        async def run_test():
            await self.async_setup()

            # Test valid config
            config = await self.controller.load_config(self.config_path)
            self.assertTrue(await self.controller.validate_config(config))

            # Test invalid barcode type
            config.barcode_type = 'InvalidType'
            self.assertFalse(await self.controller.validate_config(config))

            # Test invalid rotation
            config = await self.controller.load_config(self.config_path)
            config.transformations[0]['rotation'] = 45
            self.assertFalse(await self.controller.validate_config(config))

            # Test invalid scale
            config = await self.controller.load_config(self.config_path)
            config.transformations[0]['scale'] = 0.0
            self.assertFalse(await self.controller.validate_config(config))

            await self.async_teardown()

        asyncio.run(run_test())

    def test_state_transitions(self):
        """Test controller state transitions."""
        async def run_test():
            await self.async_setup()

            # Initial state
            self.assertFalse(self.controller.is_running)

            # Start test
            config = await self.controller.load_config(self.config_path)
            self.assertTrue(await self.controller.start_test(config))
            self.assertTrue(self.controller.is_running)

            # Stop test
            await self.controller.stop_test()
            self.assertFalse(self.controller.is_running)

            # Cleanup
            await self.controller.cleanup()
            self.assertFalse(self.controller.is_ready)

            await self.async_teardown()

        asyncio.run(run_test())

    def tearDown(self):
        """Clean up test environment."""
        # Remove test files
        for path in self.test_dir.glob('*.json'):
            path.unlink()
        self.test_dir.rmdir()
