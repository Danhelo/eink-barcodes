# File: tests/test_transform.py
import pytest
from PIL import Image
import math

from src.core.image_transform import (
    create_transform_pipeline, 
    RotationTransformer,
    ScaleTransformer,
    CenteringTransformer,
    MirrorTransformer
)

def test_rotation_transformer(test_image):
    """Test the rotation transformer."""
    transformer = RotationTransformer()
    
    # Test 90 degree rotation
    rotated = transformer.transform(test_image, {'angle': 90})
    
    # For 90 degree rotation, width and height should be swapped
    assert rotated.width == test_image.height
    assert rotated.height == test_image.width

def test_scale_transformer(test_image):
    """Test the scale transformer."""
    transformer = ScaleTransformer()
    
    # Test scaling by factor of 2
    scaled = transformer.transform(test_image, {'factor': 2.0})
    
    assert scaled.width == test_image.width * 2
    assert scaled.height == test_image.height * 2
    
    # Test scaling by factor of 0.5
    scaled = transformer.transform(test_image, {'factor': 0.5})
    
    assert scaled.width == test_image.width // 2
    assert scaled.height == test_image.height // 2

def test_centering_transformer(test_image):
    """Test the centering transformer."""
    transformer = CenteringTransformer()
    
    # Center on a larger canvas
    canvas_width, canvas_height = 200, 200
    centered = transformer.transform(test_image, {
        'width': canvas_width,
        'height': canvas_height
    })
    
    assert centered.width == canvas_width
    assert centered.height == canvas_height

def test_mirror_transformer(test_image):
    """Test the mirror transformer."""
    transformer = MirrorTransformer()
    
    # Test horizontal mirroring
    mirrored = transformer.transform(test_image, {'horizontal': True})
    
    assert mirrored.width == test_image.width
    assert mirrored.height == test_image.height
    
    # Pixel values would be different but same size

def test_transform_pipeline(test_image):
    """Test the complete transformation pipeline."""
    pipeline = create_transform_pipeline()
    
    # Define a complex transformation sequence
    transformations = {
        'rotation': {'angle': 45},
        'scale': {'factor': 1.5},
        'center': {'width': 300, 'height': 300}
    }
    
    # Apply transformations
    result = pipeline.transform(test_image, transformations)
    
    # Verify final dimensions
    assert result.width == 300
    assert result.height == 300