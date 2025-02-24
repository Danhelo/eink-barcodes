import logging                                                                                           
import asyncio                                                                                           
import os                                                                                                
from typing import List, Dict, Any, Optional, Union, Callable
from PIL import Image                                                                                    
import time                                                                                              
                                                                                                        
from .display_manager import BaseDisplayManager, DisplayManager
from .state_manager import StateManager, TestState, TestContext
from .test_config import TestConfig                                                                      
                                                                                                        
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  # Set to DEBUG level to see progress updates
                                                                                                        
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
                                                                                                        
    def set_progress_callback(self, callback: Callable[[float, str], None]):
        """Set a callback function to be called when progress updates.

        Args:
            callback: Function that takes progress (0.0-1.0) and current image path
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
        self.current_test = config                                                                       

        # Create test context
        test_context = TestContext(
            test_id=f"test_{int(time.time())}",
            config=vars(config),
            total_images=len(config.image_paths) if hasattr(config, 'image_paths') else 0
        )
        self.state_manager.set_context(test_context)
        self.state_manager.transition_to(TestState.RUNNING)

        # Initial progress update (0%)
        if self.progress_callback:
            self.progress_callback(0.0, "Starting test...")
            # Add a small delay to ensure UI updates
            await asyncio.sleep(0.1)
                                                                                                        
        try:                                                                                             
            logger.info(f"Starting test with config: {config}")                                          
                                                                                                        
            # Process each image                                                                         
            results = []
            image_paths = config.image_paths if hasattr(config, 'image_paths') else []
            total_images = len(image_paths)

            logger.debug(f"Processing {total_images} images")

            for i, image_path in enumerate(image_paths):
                # Calculate progress (0.0 to 1.0)
                # Use i instead of i+1 to show progress before processing the current image
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

                # Call progress callback if set
                if self.progress_callback:
                    logger.debug(f"Calling progress callback with {progress:.2f}")
                    self.progress_callback(progress, image_path)
                    # Add a small delay to ensure UI updates
                    await asyncio.sleep(0.05)

                # Process the image
                result = await self._process_image(image_path)
                results.append(result)                                                                   
                                                                                                        
                # Add delay between images if specified                                                  
                if hasattr(config, 'delay_between_images') and config.delay_between_images > 0:
                    delay = config.delay_between_images
                    logger.debug(f"Delaying for {delay} seconds between images")
                    await asyncio.sleep(delay)

                # Update progress after processing (for smoother progress updates)
                progress = (i + 1) / total_images if total_images > 0 else 1.0
                if self.progress_callback:
                    logger.debug(f"Calling progress callback with {progress:.2f} after processing")
                    self.progress_callback(progress, f"Processed {image_path}")
                    # Add a small delay to ensure UI updates
                    await asyncio.sleep(0.05)
                                                                                                        
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

            # Call progress callback with completion
            if self.progress_callback:
                logger.debug("Calling progress callback with completion (1.0)")
                self.progress_callback(1.0, "Complete")
                # Add a small delay to ensure UI updates
                await asyncio.sleep(0.1)
                                                                                                        
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
                                                                                                        
        self.test_running = False                                                                        
        self.state_manager.transition_to(TestState.STOPPED)                                                  
        logger.info("Test stopped by user")                                                              
        return True                                                                                      
                                                                                                        
    async def cleanup(self) -> bool:                                                                     
        """Clean up resources.                                                                           
                                                                                                        
        Returns:                                                                                         
            bool: True if cleanup was successful                                                         
        """                                                                                              
        try:
            if self.display_manager:
                await self.display_manager.cleanup()
            return True
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
            return False
