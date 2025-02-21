"""Barcode loading and management utilities."""
import os
from typing import List, Optional
from src.config.constants import KNOWN_BARCODES_DIR, BARCODE_CONFIGS

def load_barcodes(barcode_type: str) -> List[str]:
    """Load barcodes of the specified type from known_barcode directory."""
    barcodes = []

    config = BARCODE_CONFIGS.get(barcode_type)
    if not config:
        return []

    try:
        # Check main directory
        if not os.path.exists(KNOWN_BARCODES_DIR):
            return []

        # Check type-specific subdirectory
        type_dir = os.path.join(KNOWN_BARCODES_DIR, config["dir"])
        if os.path.exists(type_dir):
            # Look in type-specific subdirectory first
            for file in os.listdir(type_dir):
                if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                    if any(pattern.lower() in file.lower() for pattern in config["patterns"]):
                        barcodes.append(os.path.join(type_dir, file))

        # Also look in main directory as fallback
        for file in os.listdir(KNOWN_BARCODES_DIR):
            if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                if any(pattern.lower() in file.lower() for pattern in config["patterns"]):
                    full_path = os.path.join(KNOWN_BARCODES_DIR, file)
                    if full_path not in barcodes:  # Avoid duplicates
                        barcodes.append(full_path)

        return sorted(barcodes)

    except Exception as e:
        print(f"Error loading barcodes: {str(e)}")
        return []
