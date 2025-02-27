# src/core/config.py
"""
Flexible configuration system for test and display settings.
"""
from typing import Dict, Any, List, Optional
import json
import os
import logging
from dataclasses import dataclass, field, asdict

logger = logging.getLogger(__name__)

@dataclass
class BarcodeConfig:
    """Configuration for a barcode type."""
    name: str
    patterns: List[str] = field(default_factory=list)
    directory: str = ""
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BarcodeConfig':
        return cls(
            name=data.get('name', ''),
            patterns=data.get('patterns', []),
            directory=data.get('directory', '')
        )

@dataclass
class DisplayConfig:
    """Configuration for display hardware."""
    virtual: bool = False
    vcom: float = -2.06
    dimensions: Optional[tuple] = None
    extra_params: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = asdict(self)
        result.update(self.extra_params)
        return result
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DisplayConfig':
        """Create from dictionary."""
        # Extract known fields
        virtual = data.get('virtual', False)
        vcom = data.get('vcom', -2.06)
        dimensions = data.get('dimensions')
        
        # Store remaining fields in extra_params
        extra = {k: v for k, v in data.items() 
                if k not in ['virtual', 'vcom', 'dimensions']}
        
        return cls(
            virtual=virtual,
            vcom=vcom,
            dimensions=dimensions,
            extra_params=extra
        )

@dataclass
class TestConfig:
    """Flexible test configuration."""
    barcode_type: str = "Code128"
    image_paths: List[str] = field(default_factory=list)
    delay_between_images: float = 0.5
    repetitions: int = 1
    transformations: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    extra_params: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = asdict(self)
        result.update(self.extra_params)
        return result
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TestConfig':
        """Create from dictionary."""
        # Extract known fields
        barcode_type = data.get('barcode_type', 'Code128')
        image_paths = data.get('image_paths', [])
        delay = data.get('delay_between_images', 0.5)
        repetitions = data.get('repetitions', 1)
        transformations = data.get('transformations', {})
        
        # Store remaining fields in extra_params
        extra = {k: v for k, v in data.items() 
                if k not in ['barcode_type', 'image_paths', 
                            'delay_between_images', 'repetitions', 
                            'transformations']}
        
        return cls(
            barcode_type=barcode_type,
            image_paths=image_paths,
            delay_between_images=delay,
            repetitions=repetitions,
            transformations=transformations,
            extra_params=extra
        )
    
    def add_transformation(self, transform_type: str, params: Dict[str, Any]) -> None:
        """Add a transformation to the configuration."""
        self.transformations[transform_type] = params