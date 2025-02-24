"""Unit tests for test controller functionality."""
import pytest
import asyncio
from pathlib import Path
import tempfile
import json
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock

from src.core.test_controller import TestController
from src.core.test_config import TestConfig
from src.core.display_manager import DisplayManager

@pytest.mark.asyncio
class TestTestController:
    """Test suite for TestController class."""

    @pytest.fixture(autouse=True)
    async def setup_test(self, test_dir, config_path, display_manager):
        """Set up test environment."""
        self.test_dir = test_dir
        self.config_path = config_path
        self.display_manager = display_manager
        self.controller = TestController(self.display_manager)
        await self.controller.initialize()
        yield
        await self.controller.cleanup()

    async def test_initialization(self):
        """Test controller initialization."""
        controller = TestController(self.display_manager)

        # Test successful initialization
        assert await controller.initialize()
        assert controller.is_ready

        # Test double initialization
        assert await controller.initialize()

        await controller.cleanup()

    async def test_config_loading(self):
        """Test configuration loading."""
        # Load valid config
        config = await self.controller.load_config(self.config_path)
        assert isinstance(config, TestConfig)
        assert config.test_name == 'Test Suite 1'
        assert config.barcode_type == 'Code128'

        # Test invalid config path
        with pytest.raises(FileNotFoundError):
            await self.controller.load_config('nonexistent.json')

        # Test invalid config format
        invalid_config = self.test_dir / 'invalid.json'
        with open(invalid_config, 'w') as f:
            f.write('invalid json')

        with pytest.raises(json.JSONDecodeError):
            await self.controller.load_config(invalid_config)

    async def test_test_execution(self):
        """Test basic test execution flow."""
        # Load and validate config
        config = await self.controller.load_config(self.config_path)
        assert await self.controller.validate_config(config)

        # Start test
        assert await self.controller.start_test(config)
        assert self.controller.is_running

        # Wait for completion
        while self.controller.is_running:
            await asyncio.sleep(0.1)

        # Verify results
        results = self.controller.get_results()
        assert results is not None
        assert len(results['transformations']) == 3

    async def test_test_cancellation(self):
        """Test test cancellation."""
        # Start test
        config = await self.controller.load_config(self.config_path)
        assert await self.controller.start_test(config)

        # Cancel test
        await self.controller.stop_test()
        assert not self.controller.is_running

        # Verify partial results
        results = self.controller.get_results()
        assert results is not None
        assert results['cancelled']

    async def test_error_handling(self):
        """Test error handling during test execution."""
        # Simulate display error
        self.display_manager.display_image.side_effect = Exception('Display error')

        # Start test
        config = await self.controller.load_config(self.config_path)
        assert await self.controller.start_test(config)

        # Wait for completion
        while self.controller.is_running:
            await asyncio.sleep(0.1)

        # Verify error handling
        results = self.controller.get_results()
        assert results['error']
        assert 'Display error' in results['error_message']

    async def test_progress_tracking(self):
        """Test progress tracking during test execution."""
        progress_updates = []

        def progress_callback(progress):
            progress_updates.append(progress)

        # Register progress callback
        self.controller.register_progress_callback(progress_callback)

        # Start test
        config = await self.controller.load_config(self.config_path)
        assert await self.controller.start_test(config)

        # Wait for completion
        while self.controller.is_running:
            await asyncio.sleep(0.1)

        # Verify progress updates
        assert len(progress_updates) > 0
        assert progress_updates[-1] == 100

    async def test_concurrent_operations(self):
        """Test concurrent test operations."""
        # Try to start multiple tests
        config = await self.controller.load_config(self.config_path)
        assert await self.controller.start_test(config)

        # Second test should fail while first is running
        with pytest.raises(RuntimeError):
            await self.controller.start_test(config)

        await self.controller.stop_test()

    async def test_results_management(self):
        """Test test results management."""
        # Run test
        config = await self.controller.load_config(self.config_path)
        await self.controller.start_test(config)

        # Wait for completion
        while self.controller.is_running:
            await asyncio.sleep(0.1)

        # Get results
        results = self.controller.get_results()

        # Verify result structure
        assert 'test_name' in results
        assert 'start_time' in results
        assert 'end_time' in results
        assert 'transformations' in results
        assert 'success' in results

        # Verify timestamps
        assert isinstance(datetime.fromisoformat(results['start_time']), datetime)
        assert isinstance(datetime.fromisoformat(results['end_time']), datetime)

        # Clear results
        self.controller.clear_results()
        assert self.controller.get_results() is None

    async def test_config_validation(self):
        """Test configuration validation."""
        # Test valid config
        config = await self.controller.load_config(self.config_path)
        assert await self.controller.validate_config(config)

        # Test invalid barcode type
        config.barcode_type = 'InvalidType'
        assert not await self.controller.validate_config(config)

        # Test invalid rotation
        config = await self.controller.load_config(self.config_path)
        config.transformations[0]['rotation'] = 45
        assert not await self.controller.validate_config(config)

        # Test invalid scale
        config = await self.controller.load_config(self.config_path)
        config.transformations[0]['scale'] = 0.0
        assert not await self.controller.validate_config(config)

    async def test_state_transitions(self):
        """Test controller state transitions."""
        # Initial state
        assert not self.controller.is_running

        # Start test
        config = await self.controller.load_config(self.config_path)
        assert await self.controller.start_test(config)
        assert self.controller.is_running

        # Stop test
        await self.controller.stop_test()
        assert not self.controller.is_running

        # Cleanup
        await self.controller.cleanup()
        assert not self.controller.is_ready
