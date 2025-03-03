# src/utils/download.py
"""
Utilities for downloading and extracting files.
"""
import requests
import zipfile
import io
import logging
import os
from typing import Tuple, List
import time

logger = logging.getLogger(__name__)

def download_and_unzip_s3_file(s3_url: str, extract_to: str = '.') -> Tuple[bool, str]:
    """
    Downloads a ZIP file from an S3 URL and extracts its contents.

    Args:
        s3_url: The URL of the ZIP file on S3.
        extract_to: The directory to extract the contents to.

    Returns:
        Tuple[bool, str]: (success, message)
    """
    try:
        logger.info(f"Downloading file from: {s3_url}")
        
        # Download the file with retry logic
        max_retries = 3
        retry_delay = 1  # seconds
        
        for attempt in range(max_retries):
            try:
                response = requests.get(s3_url, timeout=30)
                response.raise_for_status()
                break
            except (requests.RequestException, requests.Timeout) as e:
                if attempt < max_retries - 1:
                    logger.warning(f"Download attempt {attempt + 1} failed: {e}. Retrying in {retry_delay}s...")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    raise
        
        # Create extract directory if it doesn't exist
        os.makedirs(extract_to, exist_ok=True)
        
        # Extract the zip file
        with zipfile.ZipFile(io.BytesIO(response.content)) as zip_ref:
            # Extract all the contents into the specified directory
            file_list = zip_ref.namelist()
            zip_ref.extractall(extract_to)
            
        # Verify extraction
        extracted_files: List[str] = []
        for root, _, files in os.walk(extract_to):
            for file in files:
                if file.endswith(('.png', '.jpg', '.jpeg')):
                    relative_path = os.path.relpath(os.path.join(root, file), extract_to)
                    extracted_files.append(relative_path)
        
        logger.info(f"Successfully extracted {len(extracted_files)} barcode images to {extract_to}")
        return True, f"Successfully downloaded and extracted {len(extracted_files)} new barcode images."
        
    except requests.RequestException as e:
        logger.error(f"Download error: {e}")
        return False, f"Error downloading file: {str(e)}"
        
    except zipfile.BadZipFile as e:
        logger.error(f"Bad zip file: {e}")
        return False, "The downloaded file is not a valid ZIP archive."
        
    except Exception as e:
        logger.error(f"Error extracting contents: {e}")
        return False, f"Error extracting contents: {str(e)}"