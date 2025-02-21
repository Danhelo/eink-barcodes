from dataclasses import dataclass
from typing import Optional

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
