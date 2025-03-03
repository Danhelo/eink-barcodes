# src/core/image_transform.py
"""
Flexible image transformation system supporting extension with custom transformations.
"""
from PIL import Image
from typing import Dict, Any, List, Callable, Protocol, Optional
import math
import logging

logger = logging.getLogger(__name__)

class ImageTransformer(Protocol):
    """Protocol defining the interface for image transformers."""
    def transform(self, image: Image.Image, params: Dict[str, Any]) -> Image.Image:
        """Transform an image according to parameters."""
        pass

class TransformationPipeline:
    """Pipeline for applying multiple transformations in sequence."""
    
    def __init__(self):
        self._transformers: Dict[str, ImageTransformer] = {}
        
    def register_transformer(self, name: str, transformer: ImageTransformer) -> None:
        """Register a transformer with the pipeline."""
        self._transformers[name] = transformer
        
    def transform(self, image: Image.Image, transform_config: Dict[str, Any]) -> Image.Image:
        """Apply transformations according to configuration."""
        result = image.copy()
        
        for transform_type, params in transform_config.items():
            if transform_type in self._transformers:
                try:
                    transformer = self._transformers[transform_type]
                    result = transformer.transform(result, params)
                    logger.debug(f"Applied {transform_type} transformation with params: {params}")
                except Exception as e:
                    logger.error(f"Error applying {transform_type} transformation: {e}")
                    
        return result

# Built-in transformers

class RotationTransformer:
    """Rotates an image by specified angle."""
    
    def transform(self, image: Image.Image, params: Dict[str, Any]) -> Image.Image:
        angle = params.get('angle', 0.0)
        background = params.get('background', 255)
        expand = params.get('expand', True)
        
        if angle == 0:
            return image
            
        return image.rotate(angle, resample=Image.BICUBIC, expand=expand, fillcolor=background)

class ScaleTransformer:
    """Scales an image by specified factor."""
    
    def transform(self, image: Image.Image, params: Dict[str, Any]) -> Image.Image:
        scale = params.get('factor', 1.0)
        
        if scale == 1.0:
            return image
            
        new_width = int(image.width * scale)
        new_height = int(image.height * scale)
        
        return image.resize((new_width, new_height), Image.BICUBIC)

class CenteringTransformer:
    """Centers an image on a canvas of specified size."""
    
    def transform(self, image: Image.Image, params: Dict[str, Any]) -> Image.Image:
        width = params.get('width')
        height = params.get('height')
        background = params.get('background', 255)
        
        if width is None or height is None:
            return image
            
        if image.width >= width and image.height >= height:
            return image
            
        canvas = Image.new(image.mode, (width, height), background)
        x = (width - image.width) // 2
        y = (height - image.height) // 2
        canvas.paste(image, (x, y))
        
        return canvas

class MirrorTransformer:
    """Mirrors an image horizontally or vertically."""
    
    def transform(self, image: Image.Image, params: Dict[str, Any]) -> Image.Image:
        horizontal = params.get('horizontal', False)
        vertical = params.get('vertical', False)
        
        if horizontal and vertical:
            return image.transpose(Image.ROTATE_180)
        elif horizontal:
            return image.transpose(Image.FLIP_LEFT_RIGHT)
        elif vertical:
            return image.transpose(Image.FLIP_TOP_BOTTOM)
            
        return image

# Factory function to create and configure the transformation pipeline
def create_transform_pipeline() -> TransformationPipeline:
    """Create and initialize transformation pipeline with built-in transformers."""
    pipeline = TransformationPipeline()
    
    # Register built-in transformers
    pipeline.register_transformer('rotation', RotationTransformer())
    pipeline.register_transformer('scale', ScaleTransformer())
    pipeline.register_transformer('center', CenteringTransformer())
    pipeline.register_transformer('mirror', MirrorTransformer())
    
    return pipeline