import logging                                                                                            
import asyncio                                                                                            
from PIL import Image                                                                                     
import os                                                                                                 
from typing import Optional, List, Dict, Any, Union                                                       
                                                                                                        
from src.core.display import VirtualDisplay, AutoEPDDisplayWrapper
from .state_manager import StateManager, DisplayState
                                                                                                        
logger = logging.getLogger(__name__)                                                                      
                                                                                                        
class DisplayConfig:                                                                                      
    """Configuration for display operations."""                                                           
                                                                                                        
    def __init__(self,                                                                                    
                virtual: bool = False,                                                                   
                vcom: float = -2.06,                                                                     
                rotation: int = 0,                                                                       
                scale: float = 1.0,                                                                      
                mirror: bool = False):                                                                   
        """Initialize display configuration.                                                              
                                                                                                        
        Args:                                                                                             
            virtual: Whether to use virtual display                                                       
            vcom: VCOM value for e-ink display                                                            
            rotation: Rotation angle in degrees (0, 90, 180, 270)                                         
            scale: Scale factor for images                                                                
            mirror: Whether to mirror images horizontally                                                 
        """                                                                                               
        self.virtual = virtual                                                                            
        self.vcom = vcom                                                                                  
        self.rotation = rotation                                                                          
        self.scale = scale                                                                                
        self.mirror = mirror                                                                              
                                                                                                        
                                                                                                        
class BaseDisplayManager:                                                                                 
    """Base class for display managers."""                                                                
                                                                                                        
    async def initialize(self) -> bool:                                                                   
        """Initialize the display."""                                                                     
        raise NotImplementedError                                                                         
                                                                                                        
    async def display_image(self, image_path: str) -> bool:                                               
        """Display an image on the e-ink display."""                                                      
        raise NotImplementedError                                                                         
                                                                                                        
    async def clear(self) -> bool:                                                                        
        """Clear the display."""                                                                          
        raise NotImplementedError                                                                         
                                                                                                        
    async def cleanup(self) -> bool:                                                                      
        """Clean up resources."""                                                                         
        raise NotImplementedError                                                                         
                                                                                                        
                                                                                                        
class DisplayManager(BaseDisplayManager):                                                                 
    """Manages the e-ink display and image processing."""                                                 
                                                                                                        
    def __init__(self, state_manager: Optional[StateManager] = None, config: Optional[DisplayConfig] = None):
        """Initialize the display manager.                                                                
                                                                                                        
        Args:                                                                                             
            state_manager: Optional state manager for updating display state
            config: Optional display configuration
        """                                                                                               
        self.config = config or DisplayConfig()
        self.state_manager = state_manager
        self.display = None                                                                               
        self.initialized = False                                                                          
        logger.info(f"EPD Display Manager initialized with VCOM {self.config.vcom}")
                                                                                                        
    async def initialize(self) -> bool:                                                                   
        """Initialize the display.                                                                        
                                                                                                        
        Returns:                                                                                          
            bool: True if initialization was successful                                                   
        """                                                                                               
        if self.initialized:                                                                              
            return True                                                                                   

        if self.state_manager:
            self.state_manager.update_display_state(DisplayState.INITIALIZING)
                                                                                                        
        try:                                                                                              
            if self.config.virtual:
                self.display = VirtualDisplay()                                                           
            else:                                                                                         
                try:                                                                                      
                    from IT8951.display import AutoEPDDisplay                                             
                    epd = AutoEPDDisplay(vcom=self.config.vcom)
                    self.display = AutoEPDDisplayWrapper(epd)                                             
                except ImportError:                                                                       
                    logger.warning("IT8951 module not found, falling back to virtual display")            
                    self.display = VirtualDisplay()                                                       
                except Exception as e:                                                                    
                    logger.error(f"Failed to initialize hardware display: {e}")                           
                    logger.warning("Falling back to virtual display")                                     
                    self.display = VirtualDisplay()                                                       
                                                                                                        
            self.initialized = True                                                                       
            logger.info(f"Display initialized successfully: {self.display.width}x{self.display.height}")

            if self.state_manager:
                self.state_manager.update_display_state(DisplayState.READY)

            return True                                                                                   
        except Exception as e:                                                                            
            logger.error(f"Failed to initialize display: {e}")

            if self.state_manager:
                self.state_manager.update_display_state(DisplayState.ERROR)

            return False                                                                                  
                                                                                                        
    async def display_image(self, image_path: str) -> bool:                                               
        """Display an image on the e-ink display.                                                         
                                                                                                        
        Args:                                                                                             
            image_path: Path to the image file                                                            
                                                                                                        
        Returns:                                                                                          
            bool: True if display was successful                                                          
        """                                                                                               
        if not self.initialized:                                                                          
            if not await self.initialize():                                                               
                logger.error("Failed to initialize display")                                              
                return False                                                                              

        if self.state_manager:
            self.state_manager.update_display_state(DisplayState.BUSY)
                                                                                                        
        try:                                                                                              
            # Check if file exists                                                                        
            if not os.path.exists(image_path):                                                            
                logger.error(f"Image file not found: {image_path}")

                if self.state_manager:
                    self.state_manager.update_display_state(DisplayState.ERROR)

                return False                                                                              
                                                                                                        
            # Load and process image                                                                      
            image = Image.open(image_path).convert('L')  # Convert to grayscale                           
            logger.info(f"Loaded image {image_path}: {image.width}x{image.height}")                       
                                                                                                        
            # Display the image                                                                           
            result = self.display.display_image(image)                                                    
            if not result:                                                                                
                logger.error(f"Failed to display image: {image_path}")

                if self.state_manager:
                    self.state_manager.update_display_state(DisplayState.ERROR)

                return False                                                                              

            if self.state_manager:
                self.state_manager.update_display_state(DisplayState.READY)
                                                                                                        
            return True                                                                                   
        except Exception as e:                                                                            
            logger.error(f"Error displaying image: {e}")

            if self.state_manager:
                self.state_manager.update_display_state(DisplayState.ERROR)

            return False                                                                                  
                                                                                                        
    async def clear(self) -> bool:                                                                        
        """Clear the display.                                                                             
                                                                                                        
        Returns:                                                                                          
            bool: True if clearing was successful                                                         
        """                                                                                               
        if not self.initialized:                                                                          
            logger.warning("Display not initialized, nothing to clear")                                   
            return False                                                                                  

        if self.state_manager:
            self.state_manager.update_display_state(DisplayState.BUSY)
                                                                                                        
        try:                                                                                              
            result = self.display.clear()

            if self.state_manager:
                self.state_manager.update_display_state(DisplayState.READY)

            return result                                                                                 
        except Exception as e:                                                                            
            logger.error(f"Error clearing display: {e}")

            if self.state_manager:
                self.state_manager.update_display_state(DisplayState.ERROR)

            return False                                                                                  
                                                                                                        
    async def cleanup(self) -> bool:                                                                      
        """Clean up resources.                                                                            
                                                                                                        
        Returns:                                                                                          
            bool: True if cleanup was successful                                                          
        """                                                                                               
        if not self.initialized:                                                                          
            return True                                                                                   
                                                                                                        
        try:                                                                                              
            # Clear the display before cleanup                                                            
            await self.clear()                                                                            
                                                                                                        
            # No specific cleanup needed for our display classes                                          
            self.initialized = False

            if self.state_manager:
                self.state_manager.update_display_state(DisplayState.DISCONNECTED)

            logger.info("Display cleaned up successfully")                                                
            return True                                                                                   
        except Exception as e:                                                                            
            logger.error(f"Error during display cleanup: {e}")

            if self.state_manager:
                self.state_manager.update_display_state(DisplayState.ERROR)

            return False                                                                                  
                                                                                                        
    @classmethod                                                                                          
    async def create(cls, state_manager: Optional[StateManager] = None,
                    config: Optional[DisplayConfig] = None):
        """Factory method to create and initialize a display manager.                                     
                                                                                                        
        Args:                                                                                             
            state_manager: Optional state manager for updating display state
            config: Optional display configuration
                                                                                                        
        Returns:                                                                                          
            DisplayManager: Initialized display manager                                                   
        """
        # Handle backward compatibility with old create method signature
        if isinstance(state_manager, bool):  # Old 'virtual' parameter
            virtual = state_manager
            vcom = config if isinstance(config, float) else -2.06
            config = DisplayConfig(virtual=virtual, vcom=vcom)
            state_manager = None

        manager = cls(state_manager=state_manager, config=config)
        await manager.initialize()                                                                        
        return manager
