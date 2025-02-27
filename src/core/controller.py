# src/core/controller.py
"""
Unified test controller with integrated state management.
"""
import asyncio
import logging
import time
from enum import Enum, auto
from typing import Dict, Any, List, Optional, Callable, Set
from PIL import Image
import os

from .config import TestConfig, DisplayConfig

logger = logging.getLogger(__name__)

class TestState(Enum):
    """Test states with clear, simple progression."""
    IDLE = auto()         # No test running
    RUNNING = auto()      # Test in progress
    COMPLETED = auto()    # Test finished successfully
    ERROR = auto()        # Test encountered an error
    STOPPED = auto()      # Test stopped by user

class TestController:
    """
    Unified controller managing test execution and state.
    
    This controller follows the observer pattern, allowing multiple UI components
    to register for state updates. It maintains internal state and provides a 
    simple API for test execution.
    """
    
    def __init__(self):
        self._state = TestState.IDLE
        self._context = {}  # Current execution context
        self._observers: Set[Callable[[TestState, Dict[str, Any]], None]] = set()
        self._display = None
        self._transform_pipeline = None
        self._running = False
        self._cancel_requested = False
        
    def register_observer(self, observer: Callable[[TestState, Dict[str, Any]], None]) -> None:
        """Register an observer to receive state updates."""
        self._observers.add(observer)
        
        # Send current state immediately to new observer
        observer(self._state, self._context)
        
    def unregister_observer(self, observer: Callable[[TestState, Dict[str, Any]], None]) -> None:
        """Unregister an observer."""
        if observer in self._observers:
            self._observers.remove(observer)
    
    def get_state(self) -> TestState:
        """Get current test state."""
        return self._state
        
    def get_context(self) -> Dict[str, Any]:
        """Get current execution context."""
        return self._context.copy()
        
    def _update_state(self, state: TestState, context_update: Optional[Dict[str, Any]] = None) -> None:
        """Update state and notify observers."""
        old_state = self._state
        self._state = state
        
        # Update context
        if context_update:
            self._context.update(context_update)
            
        # Log state change
        logger.debug(f"State transition: {old_state} -> {state}")
        
        # Notify observers
        for observer in self._observers:
            try:
                observer(state, self._context)
            except Exception as e:
                logger.error(f"Error notifying observer: {e}")
    
    async def initialize(self, display_factory, transform_factory) -> bool:
        """
        Initialize the controller with factories for display and transformations.
        
        Args:
            display_factory: Factory function for creating display
            transform_factory: Factory function for creating transform pipeline
            
        Returns:
            bool: True if initialization succeeded
        """
        try:
            self._update_state(TestState.IDLE, {"status": "Initializing..."})
            
            # Create display
            self._display = display_factory()
            
            # Create transform pipeline
            self._transform_pipeline = transform_factory()
            
            self._update_state(TestState.IDLE, {"status": "Ready"})
            return True
            
        except Exception as e:
            logger.error(f"Initialization error: {e}")
            self._update_state(TestState.ERROR, {
                "status": "Initialization failed",
                "error": str(e)
            })
            return False
    
    async def run_test(self, config: TestConfig) -> Dict[str, Any]:
        """
        Run a test with the given configuration.
        
        Args:
            config: Test configuration
            
        Returns:
            Dict: Test results
        """
        if self._running:
            return {"success": False, "error": "Test already running"}
            
        if not self._display or not self._transform_pipeline:
            return {"success": False, "error": "Controller not initialized"}
            
        self._running = True
        self._cancel_requested = False
        
        # Reset and update context
        self._context = {}
        self._update_state(TestState.RUNNING, {
            "status": "Starting test",
            "config": config.to_dict(),
            "progress": 0.0,
            "start_time": time.time()
        })
        
        try:
            image_paths = config.image_paths
            total_images = len(image_paths)
            
            if total_images == 0:
                raise ValueError("No images specified in test configuration")
                
            results = []
            
            for i, image_path in enumerate(image_paths):
                # Check for cancellation
                if self._cancel_requested:
                    self._update_state(TestState.STOPPED, {
                        "status": "Test stopped by user",
                        "progress": i / total_images
                    })
                    return {
                        "success": False, 
                        "error": "Test cancelled",
                        "completed": i,
                        "total": total_images
                    }
                
                # Update progress
                progress = i / total_images
                self._update_state(TestState.RUNNING, {
                    "status": f"Processing image {i+1}/{total_images}: {os.path.basename(image_path)}",
                    "progress": progress,
                    "current_image": image_path
                })
                
                # Process image
                result = await self._process_image(image_path, config.transformations)
                results.append(result)
                
                # Add delay between images
                if i < total_images - 1 and config.delay_between_images > 0:
                    # Update state to "waiting"
                    self._update_state(TestState.RUNNING, {
                        "status": f"Waiting ({config.delay_between_images}s)...",
                        "progress": (i + 0.5) / total_images
                    })
                    
                    # Split delay into smaller chunks for better responsiveness
                    chunks = min(10, int(config.delay_between_images * 2))
                    for j in range(chunks):
                        if self._cancel_requested:
                            break
                        await asyncio.sleep(config.delay_between_images / chunks)
                        # Intermediate progress update
                        intermediate_progress = (i + 0.5 + (0.5 * j / chunks)) / total_images
                        self._update_state(TestState.RUNNING, {
                            "progress": intermediate_progress
                        })
            
            # Calculate results
            success_count = sum(1 for r in results if r.get("success", False))
            elapsed_time = time.time() - self._context.get("start_time", time.time())
            
            test_results = {
                "success": True,
                "total_images": total_images,
                "successful_images": success_count,
                "elapsed_time": elapsed_time,
                "image_results": results
            }
            
            self._update_state(TestState.COMPLETED, {
                "status": "Test completed successfully",
                "progress": 1.0,
                "results": test_results
            })
            
            return test_results
            
        except Exception as e:
            logger.error(f"Test execution error: {e}")
            self._update_state(TestState.ERROR, {
                "status": f"Error: {str(e)}",
                "error": str(e),
                "progress": self._context.get("progress", 0.0)
            })
            return {"success": False, "error": str(e)}
            
        finally:
            self._running = False
    
    async def _process_image(self, image_path: str, transformations: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Process a single image for display."""
        start_time = time.time()
        
        try:
            # Load image
            if not os.path.exists(image_path):
                raise FileNotFoundError(f"Image not found: {image_path}")
                
            image = Image.open(image_path).convert('L')  # Convert to grayscale
            
            # Apply transformations
            transformed = self._transform_pipeline.transform(image, transformations)
            
            # Display the image
            if not self._display.display_image(transformed):
                raise RuntimeError(f"Failed to display image: {image_path}")
                
            # Record result
            return {
                "success": True,
                "image_path": image_path,
                "processing_time": time.time() - start_time
            }
            
        except Exception as e:
            logger.error(f"Failed to process image {image_path}: {e}")
            return {
                "success": False,
                "image_path": image_path,
                "error": str(e)
            }
    
    async def stop_test(self) -> bool:
        """Stop the current test."""
        if not self._running:
            return False
            
        self._cancel_requested = True
        
        # Allow time for test to handle cancellation
        await asyncio.sleep(0.1)
        
        return True
    
    async def cleanup(self) -> bool:
        """Clean up resources."""
        try:
            if self._running:
                await self.stop_test()
                
            if self._display:
                self._display.cleanup()
                
            self._update_state(TestState.IDLE, {"status": "Cleaned up"})
            return True
            
        except Exception as e:
            logger.error(f"Cleanup error: {e}")
            self._update_state(TestState.ERROR, {
                "status": "Error during cleanup",
                "error": str(e)
            })
            return False