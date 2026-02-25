"""
Cloudinary Service Module for Permanent Video Storage

This module handles video uploads to Cloudinary for permanent storage.
Unlike fal.ai which has 7-day retention, Cloudinary provides permanent CDN hosting.

Use this for:
- User-generated videos that need to persist
- Animation exports from Pro Studio
- Any video content that must be permanently accessible
"""

import os
import logging
import base64
import asyncio
from typing import Optional, Dict, Any
import aiohttp

import cloudinary
import cloudinary.uploader
import cloudinary.api

logger = logging.getLogger(__name__)

# Initialize Cloudinary configuration
def _init_cloudinary():
    """Initialize Cloudinary with environment credentials."""
    cloud_name = os.environ.get('CLOUDINARY_CLOUD_NAME')
    api_key = os.environ.get('CLOUDINARY_API_KEY')
    api_secret = os.environ.get('CLOUDINARY_API_SECRET')
    
    if not all([cloud_name, api_key, api_secret]):
        logger.warning("Cloudinary credentials not fully configured")
        return False
    
    cloudinary.config(
        cloud_name=cloud_name,
        api_key=api_key,
        api_secret=api_secret,
        secure=True
    )
    return True


def is_cloudinary_configured() -> bool:
    """Check if Cloudinary is properly configured."""
    return all([
        os.environ.get('CLOUDINARY_CLOUD_NAME'),
        os.environ.get('CLOUDINARY_API_KEY'),
        os.environ.get('CLOUDINARY_API_SECRET')
    ])


async def upload_video_to_cloudinary(
    video_data: str,
    folder: str = "azories/videos",
    public_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Upload a video to Cloudinary for permanent storage.
    
    Args:
        video_data: Either a base64 string (data:video/mp4;base64,...) or a URL
        folder: Cloudinary folder path for organization
        public_id: Optional custom public ID for the video
        
    Returns:
        Dict with 'url' (secure URL), 'public_id', 'duration', 'format'
    """
    if not is_cloudinary_configured():
        raise Exception("Cloudinary is not configured. Please set CLOUDINARY_* environment variables.")
    
    _init_cloudinary()
    
    try:
        upload_options = {
            "resource_type": "video",
            "folder": folder,
            "overwrite": True,
            "invalidate": True,
        }
        
        if public_id:
            upload_options["public_id"] = public_id
        
        # Handle different input types
        if video_data.startswith('data:'):
            # Base64 encoded video
            logger.info("Uploading base64 video to Cloudinary...")
            result = cloudinary.uploader.upload(video_data, **upload_options)
        elif video_data.startswith('http'):
            # URL - Cloudinary will fetch and store it
            logger.info(f"Uploading video from URL to Cloudinary: {video_data[:50]}...")
            result = cloudinary.uploader.upload(video_data, **upload_options)
        else:
            raise Exception("Invalid video data - must be base64 or URL")
        
        secure_url = result.get('secure_url')
        logger.info(f"Video uploaded to Cloudinary: {secure_url}")
        
        return {
            "url": secure_url,
            "public_id": result.get('public_id'),
            "duration": result.get('duration'),
            "format": result.get('format'),
            "width": result.get('width'),
            "height": result.get('height'),
            "bytes": result.get('bytes'),
            "resource_type": "video"
        }
        
    except cloudinary.exceptions.Error as e:
        logger.error(f"Cloudinary upload error: {e}")
        raise Exception(f"Failed to upload video to Cloudinary: {str(e)}")
    except Exception as e:
        logger.error(f"Video upload error: {e}")
        raise Exception(f"Failed to upload video: {str(e)}")


async def migrate_video_from_fal_to_cloudinary(
    fal_url: str,
    folder: str = "azories/videos/migrated"
) -> Dict[str, Any]:
    """
    Migrate a video from fal.ai temporary storage to Cloudinary permanent storage.
    
    ⚠️ IMPORTANT: fal.ai has 7-day retention. Videos must be migrated before expiry.
    
    Args:
        fal_url: The fal.ai CDN URL of the video
        folder: Cloudinary folder for migrated videos
        
    Returns:
        Dict with Cloudinary URL and metadata
    """
    if not fal_url.startswith('https://'):
        raise Exception("Invalid fal.ai URL")
    
    logger.info(f"Migrating video from fal.ai to Cloudinary: {fal_url[:50]}...")
    
    # Upload to Cloudinary (it will fetch from the URL)
    result = await upload_video_to_cloudinary(fal_url, folder=folder)
    
    logger.info(f"Migration complete: {result['url']}")
    return result


async def delete_video_from_cloudinary(public_id: str) -> bool:
    """
    Delete a video from Cloudinary.
    
    Args:
        public_id: The Cloudinary public_id of the video
        
    Returns:
        True if deleted successfully
    """
    if not is_cloudinary_configured():
        raise Exception("Cloudinary is not configured")
    
    _init_cloudinary()
    
    try:
        result = cloudinary.uploader.destroy(
            public_id,
            resource_type="video",
            invalidate=True
        )
        return result.get('result') == 'ok'
    except Exception as e:
        logger.error(f"Failed to delete video: {e}")
        return False


def get_cloudinary_video_url(public_id: str, transformations: Optional[str] = None) -> str:
    """
    Get a Cloudinary video URL with optional transformations.
    
    Args:
        public_id: The Cloudinary public_id
        transformations: Optional transformation string (e.g., "w_720,q_auto")
        
    Returns:
        The secure CDN URL
    """
    _init_cloudinary()
    
    cloud_name = os.environ.get('CLOUDINARY_CLOUD_NAME')
    
    if transformations:
        return f"https://res.cloudinary.com/{cloud_name}/video/upload/{transformations}/{public_id}"
    else:
        return f"https://res.cloudinary.com/{cloud_name}/video/upload/{public_id}"
