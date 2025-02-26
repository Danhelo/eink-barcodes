"""
Test controller module for managing test execution and display updates.
"""
import logging                                                                                           
import asyncio                                                                                           
import os                                                                                                
import time                                                                              
from typing import List, Dict, Any, Optional, Union, Callable
from PIL import Image                                                                                    
                                                                                                        
from .display_manager import BaseDisplayManager, DisplayManager
from .state_manager import StateManager, TestState, TestContext
from .test_config import TestConfig                                                                      
                                                                                                        
logger = logging.getLogger(__name__)
# Use standard logging level from configuration
                                                                                                        
class TestController:                                                                                    
    """Controls test execution and manages display."""                                                   
                                                                                                        
    def __init__(self, state_manager: Optional[StateManager] = None,
                 display_manager: Optional[BaseDisplayManager] = None):
        """Initialize test controller.                                                                   
                                                                                                        
        Args:                                                                                            
            state_manager: Optional state manager instance
            display_manager: Optional display manager instance                                           
        """                                                                                              
        self.display_manager = display_manager                                                           
        self.state_manager = state_manager or StateManager()
        self.current_test = None                                                                         
        self.test_running = False                                                                        
        self.test_results = {}
        self.progress_callback = None
        self._cancel_requested = False
                                                                                                        
    def set_progress_callback(self, callback: Callable[[float, str], None]):
        """Set a callback function to be called when progress updates.

        Args:
            callback: Function that takes progress (0.0-1.0) and current status message
        """
        self.progress_callback = callback
        logger.debug(f"Progress callback set: {callback}")

    async def initialize(self, virtual: bool = False, vcom: float = -2.06) -> bool:                      
        """Initialize the test controller.                                                               
                                                                                                        
        Args:                                                                                            
            virtual: Whether to use virtual display                                                      
            vcom: VCOM value for e-ink display                                                           
                                                                                                        
        Returns:                                                                                         
            bool: True if initialization was successful                                                  
        """                                                                                              
        try:
            self.state_manager.transition_to(TestState.INITIALIZING)

            if self.display_manager is None:
                self.display_manager = await DisplayManager.create(virtual=virtual, vcom=vcom)
                                                                                                        
            self.state_manager.transition_to(TestState.READY)
            return True
        except Exception as e:
            logger.error(f"Failed to initialize test controller: {e}")
            self.state_manager.transition_to(TestState.ERROR)
            return False
                                                                                                        
    async def run_test(self, config: TestConfig) -> Dict[str, Any]:                                      
        """Run a test with the given configuration.                                                      
                                                                                                        
        Args:                                                                                            
            config: Test configuration                                                                   
                                                                                                        
        Returns:                                                                                         
            Dict[str, Any]: Test results                                                                 
        """                                                                                              
        if self.test_running:                                                                            
            logger.warning("Test already running, cannot start another")                                 
            return {"success": False, "error": "Test already running"}                                   
                                                                                                        
        self.test_running = True
        self._cancel_requested = False
        self.current_test = config                                                                       

        # Create test context with unique ID
        test_id = f"test_{int(time.time())}"
        test_context = TestContext(
            test_id=test_id,
            config=vars(config),
            total_images=len(config.image_paths) if hasattr(config, 'image_paths') and config.image_paths else 0
        )
        self.state_manager.set_context(test_context)
        self.state_manager.transition_to(TestState.RUNNING)

        # Initial progress update (0%)
        self._update_progress(0.0, "Starting test...")
                                                                                                        
        try:                                                                                             
            logger.info(f"Starting test with config: {config}")                                          
                                                                                                        
            # Process each image                                                                         
            results = []
            image_paths = config.image_paths if hasattr(config, 'image_paths') else []
            total_images = len(image_paths)

            logger.debug(f"Processing {total_images} images")

            for i, image_path in enumerate(image_paths):
                # Check if test was cancelled
                if self._cancel_requested:
                    logger.info("Test cancelled by user")
                    return {"success": False, "error": "Test cancelled by user", "completed": i}
                
                # Calculate progress (0.0 to 1.0)
                progress = i / total_images if total_images > 0 else 0

                logger.debug(f"Processing image {i+1}/{total_images}: {image_path}")

                # Update context with current progress
                self.state_manager.update_state(
                    TestState.RUNNING,
                    {
                        "current_image": image_path,
                        "processed_images": i,
                        "progress": progress
                    }
                )

                # Update progress with current image
                self._update_progress(progress, f"Starting {image_path}")
                
                # CRITICAL FIX: Longer sleep for better UI responsiveness
                await asyncio.sleep(0.15)  # Increased from 0.05

                # Process the image - measure progress during processing
                start_process = time.time()
                
                # Before processing, send another progress update
                self._update_progress(progress + 0.04/total_images, f"Loading {image_path}")
                # CRITICAL FIX: Longer sleep for better UI responsiveness
                await asyncio.sleep(0.15)  # Increased from 0.05
                
                # ADDED: Extra progress update before processing
                self._update_progress(progress + 0.08/total_images, f"Preparing {image_path}")
                await asyncio.sleep(0.1)
                
                # Process the image
                result = await self._process_image(image_path)
                results.append(result)
                
                # Update progress after image processing completes
                process_time = time.time() - start_process
                
                # Calculate intermediate progress value
                interm_progress = (i + 0.5) / total_images if total_images > 0 else 0.5
                self._update_progress(interm_progress, f"Processing {image_path}")
                
                # CRITICAL FIX: Longer sleep for better UI responsiveness
                await asyncio.sleep(0.2)  # Increased from 0.1
                                                                                                        
                # Add delay between images if specified                                                  
                if hasattr(config, 'delay_between_images') and config.delay_between_images > 0:
                    delay = config.delay_between_images
                    logger.debug(f"Delaying for {delay} seconds between images")
                    
                    # If delay is substantial, provide intermediate progress updates
                    if delay > 1.0:
                        steps = min(int(delay), 5)  # Max 5 updates during delay
                        for step in range(steps):
                            await asyncio.sleep(delay / steps)
                            step_progress = (i + 0.5 + (0.5 * (step + 1) / steps)) / total_images
                            self._update_progress(step_progress, f"Waiting between images ({step+1}/{steps})")
                    else:
                        await asyncio.sleep(delay)

                # Update progress after processing (for smoother progress updates)
                progress = (i + 1) / total_images if total_images > 0 else 1.0
                self._update_progress(progress, f"Processed {image_path}")
                                                                                                        
            # Compile results                                                                            
            success_count = sum(1 for r in results if r.get("success", False))                           
            test_results = {                                                                             
                "success": True,                                                                         
                "total_images": total_images,
                "successful_images": success_count,                                                      
                "image_results": results,                                                                
                "config": vars(config)
            }                                                                                            
                                                                                                        
            self.test_results = test_results

            # Update context with final progress
            self.state_manager.update_state(
                TestState.COMPLETED,
                {
                    "processed_images": total_images,
                    "progress": 1.0
                }
            )

            # Final progress update
            self._update_progress(1.0, "Complete")
                                                                                                        
            logger.info(f"Test completed: {success_count}/{total_images} images successful")

            return test_results                                                                          
                                                                                                        
        except Exception as e:                                                                           
            logger.error(f"Test execution failed: {e}")

            # Update context with error
            self.state_manager.update_state(
                TestState.ERROR,
                {"error": str(e)}
            )

            return {"success": False, "error": str(e)}                                                   
        finally:                                                                                         
            self.test_running = False
            self._cancel_requested = False
                                                                                                        
    def _update_progress(self, progress: float, message: str = ""):
        """Update progress using callback and ensure state is consistent.
        
        Args:
            progress: Progress value (0.0-1.0)
            message: Status message
        """
        try:
            # Call progress callback if set
            if self.progress_callback:
                logger.debug(f"Triggering progress update: {progress:.2f} - {message}")
                # Force immediate progress update through callback
                self.progress_callback(progress, message)
                
                # Also update the state manager context for consistency
                # But don't trigger a state change which could cause conflicts
                # just silently update the context data
                if self.state_manager and hasattr(self.state_manager, 'get_context') and self.state_manager.get_context():
                    context = self.state_manager.get_context()
                    context.progress = progress
                    if message:
                        context.current_image = message
            
            # Log detailed information about this update
            logger.info(f"Progress update: {progress:.2f} - {message}")
        except Exception as e:
            logger.error(f"Error updating progress: {e}")
                                                                                                        
    async def _process_image(self, image_path: str) -> Dict[str, Any]:                                   
        """Process a single image.                                                                       
                                                                                                        
        Args:                                                                                            
            image_path: Path to the image file                                                           
                                                                                                        
        Returns:                                                                                         
            Dict[str, Any]: Result for this image                                                        
        """                                                                                              
        start_time = time.time()                                                                         
                                                                                                        
        try:                                                                                             
            # Display the image                                                                          
            success = await self.display_manager.display_image(image_path)                               
            if not success:                                                                              
                raise Exception(f"Failed to display image: {image_path}")                                
                                                                                                        
            # Record result                                                                              
            end_time = time.time()                                                                       
            return {                                                                                     
                "success": True,                                                                         
                "image_path": image_path,                                                                
                "processing_time": end_time - start_time                                                 
            }                                                                                            
        except Exception as e:                                                                           
            logger.error(f"Failed to process image {image_path}: {e}")                                   
            return {                                                                                     
                "success": False,                                                                        
                "image_path": image_path,                                                                
                "error": str(e)                                                                          
            }                                                                                            
                                                                                                        
    async def stop_test(self) -> bool:                                                                   
        """Stop the current test.                                                                        
                                                                                                        
        Returns:                                                                                         
            bool: True if test was stopped                                                               
        """                                                                                              
        if not self.test_running:                                                                        
            return False

        # Set cancel flag to stop processing
        self._cancel_requested = True
        
        # Update state immediately
        self.state_manager.transition_to(TestState.STOPPED)
        
        # Wait briefly for operations to complete
        await asyncio.sleep(0.1)
        
        # Reset flags
        self.test_running = False
        
        logger.info("Test stopped by user")                                                              
        return True
                                                                                      
    async def cleanup(self) -> bool:                                                                     
        """Clean up resources.                                                                           
                                                                                                        
        Returns:                                                                                         
            bool: True if cleanup was successful                                                         
        """                                                                                              
        try:
            # First make sure any running test is stopped
            if self.test_running:
                await self.stop_test()
                
            # Then clean up display manager
            if self.display_manager:
                await self.display_manager.cleanup()
                
            # Reset state
            self.progress_callback = None
            self.current_test = None
            self.test_results = {}
            
            return True
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
            return False
            
    def get_test_results(self) -> Dict[str, Any]:
        """Get results from the most recent test.
        
        Returns:
            Dict[str, Any]: Test results or empty dict if no test run
        """
        return self.test_results.copy() if self.test_results else {}