from dataclasses import dataclass
from typing import Optional, List, Dict, Any

@dataclass
class TestConfig:
    """Configuration class for test parameters."""
    barcode_type: str = "Code128"
    scale: float = 1.0
    rotation: int = 0
    count: int = 1
    refresh_rate: float = 1.0
    auto_center: bool = True
    barcode_path: Optional[str] = None
    image_paths: List[str] = None
    delay_between_images: float = 0.5
    transformations: Dict[str, Any] = None

    def __post_init__(self):
        if self.image_paths is None:
            self.image_paths = []
        if self.transformations is None:
            self.transformations = {}
