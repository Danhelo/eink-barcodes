# src/utils/reorganize_barcodes.py
"""
Utility functions for reorganizing barcode files from API downloads.

This module helps reorganize nested barcode directories created by the API
into standard directory structures that can be discovered by quick_test page.
"""
import os
import shutil
import logging
import glob
import re

logger = logging.getLogger(__name__)

def reorganize_barcode_directories(extract_to: str = 'examples') -> None:
    """
    Reorganize barcode directories by moving barcode files from nested API-generated 
    folders to their standard locations in the examples directory.

    Args:
        extract_to: Base directory where barcodes are extracted, typically 'examples'
    """
    try:
        # Check if extract_to directory exists
        if not os.path.exists(extract_to):
            logger.warning(f"Directory does not exist: {extract_to}")
            return

        # Look for API-generated directories (folders starting with "Barcode")
        api_dirs = []
        for item in os.listdir(extract_to):
            if item.startswith("Barcode") and os.path.isdir(os.path.join(extract_to, item)):
                api_dirs.append(os.path.join(extract_to, item))

        if not api_dirs:
            logger.info(f"No API-generated barcode directories found in {extract_to}")
            return

        # Process each API-generated directory
        for api_dir in api_dirs:
            logger.info(f"Processing API directory: {api_dir}")
            
            # Check subdirectories for barcode type folders
            for barcode_type_dir in _get_barcode_type_dirs(api_dir):
                barcode_type_name = os.path.basename(barcode_type_dir).lower()
                logger.info(f"Found barcode type: {barcode_type_name}")
                
                # Create the standard directory if it doesn't exist
                standard_dir = os.path.join(extract_to, barcode_type_name)
                _ensure_dir_exists(standard_dir)
                
                # Move files to standard directory
                files_moved = _move_barcode_files(barcode_type_dir, standard_dir)
                logger.info(f"Moved {files_moved} files from {barcode_type_dir} to {standard_dir}")
            
            # After moving all files, remove the empty API directory if possible
            if _is_dir_empty(api_dir):
                try:
                    os.rmdir(api_dir)
                    logger.info(f"Removed empty directory: {api_dir}")
                except OSError as e:
                    logger.warning(f"Could not remove directory {api_dir}: {e}")

    except Exception as e:
        logger.error(f"Error reorganizing barcode directories: {e}")

def _get_barcode_type_dirs(api_dir: str) -> list:
    """
    Get list of all barcode type subdirectories in the API-generated directory.
    
    Args:
        api_dir: Path to API-generated directory
        
    Returns:
        list: List of paths to barcode type directories
    """
    barcode_types = []
    
    # Common barcode type folder names (case insensitive)
    barcode_type_patterns = [
        "code128", "upca", "upce", "datamatrix", "qr code", 
        "ean13", "ean8", "code39"
    ]
    
    # Find directories that match any of the barcode type patterns
    for item in os.listdir(api_dir):
        item_path = os.path.join(api_dir, item)
        if os.path.isdir(item_path):
            # Check if this directory name matches any of our barcode types
            if any(re.match(f"^{pattern}$", item, re.IGNORECASE) for pattern in barcode_type_patterns):
                barcode_types.append(item_path)
    
    return barcode_types

def _ensure_dir_exists(directory: str) -> None:
    """
    Ensure a directory exists, creating it if necessary.
    
    Args:
        directory: Path to directory
    """
    if not os.path.exists(directory):
        os.makedirs(directory)
        logger.info(f"Created directory: {directory}")

def _move_barcode_files(source_dir: str, target_dir: str) -> int:
    """
    Move barcode image files from source to target directory,
    handling potential filename conflicts.
    
    Args:
        source_dir: Source directory containing barcode images
        target_dir: Target directory where images should be moved
        
    Returns:
        int: Number of files moved
    """
    files_moved = 0
    
    # Create target directory if it doesn't exist
    _ensure_dir_exists(target_dir)
    
    # Find all image files in source directory
    for img_file in glob.glob(os.path.join(source_dir, "*.[pj][np]*[g]")):  # Match png, jpg, jpeg
        img_filename = os.path.basename(img_file)
        target_path = os.path.join(target_dir, img_filename)
        
        # Handle filename conflict by finding a unique name
        if os.path.exists(target_path):
            base_name, ext = os.path.splitext(img_filename)
            counter = 1
            while os.path.exists(target_path):
                new_name = f"{base_name}_{counter}{ext}"
                target_path = os.path.join(target_dir, new_name)
                counter += 1
        
        # Move the file
        try:
            shutil.move(img_file, target_path)
            files_moved += 1
        except Exception as e:
            logger.error(f"Error moving file {img_file} to {target_path}: {e}")
    
    return files_moved

def _is_dir_empty(directory: str) -> bool:
    """
    Check if a directory is empty.
    
    Args:
        directory: Path to directory
        
    Returns:
        bool: True if directory is empty, False otherwise
    """
    return len(os.listdir(directory)) == 0
