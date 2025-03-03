# src/utils/barcode_api.py
"""
Utilities for interacting with the barcode generation API.
"""
import boto3
import logging
import json
import re
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

# API Gateway configuration
REST_API_ID = 'c4o2v0x7ra'
RESOURCE_ID = 'w0er4g'
HTTP_METHOD = 'POST'

async def generate_barcodes(config: List[Dict[str, Any]]) -> Optional[str]:
    """
    Generate barcodes by calling the barcode generation API.
    
    Args:
        config: List of barcode configuration objects
    
    Returns:
        Optional[str]: S3 URL if successful, None otherwise
    """
    try:
        logger.info(f"Sending barcode generation request: {json.dumps(config)}")
        
        # Create API Gateway client
        client = boto3.client('apigateway')
        
        # Convert config to JSON string for the body
        body = json.dumps(config)
        
        # Make the API call
        response = client.test_invoke_method(
            restApiId=REST_API_ID,
            resourceId=RESOURCE_ID,
            httpMethod=HTTP_METHOD,
            body=body
        )
        
        # Check the response status
        status_code = response.get('status')
        if status_code != 200:
            logger.error(f"API returned status {status_code}: {response.get('body')}")
            return None
        
        # Parse the response body
        try:
            response_body = json.loads(response.get('body', '{}'))
            
            # Get the S3 URL from the response
            presigned_url = response_body.get('Presigned URL')
            if not presigned_url:
                logger.error("No Presigned URL in API response")
                return None
                
            # Remove the trailing backslash if present
            if presigned_url.endswith('\\'):
                presigned_url = presigned_url[:-1]
                
            # Handle any escaped characters in the URL
            presigned_url = presigned_url.replace('\\/', '/')
                
            logger.info(f"Successfully retrieved presigned URL: {presigned_url}")
            return presigned_url
            
        except json.JSONDecodeError:
            logger.error(f"Error parsing API response body: {response.get('body')}")
            return None
            
    except Exception as e:
        logger.error(f"Unexpected error calling API: {e}")
        return None