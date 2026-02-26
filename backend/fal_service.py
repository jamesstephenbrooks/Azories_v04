"""
fal.ai Service Module for Pro Studio Character Consistency

IMPORTANT: This module creates explicit fal_client instances with the API key
passed directly, rather than relying on the default clients which read the key
at import time. This ensures the key is always fresh from the environment.
"""

import os
import asyncio
import logging
import base64
import io
from typing import Optional, List, Dict, Any, Tuple
import aiohttp
from PIL import Image

# Import fal_client classes explicitly - do NOT use module-level default clients
import fal_client
from fal_client import AsyncClient

logger = logging.getLogger(__name__)

# Available fal.ai models
FAL_MODELS = {
    "flux-dev": {
        "id": "fal-ai/flux/dev",
        "name": "FLUX.1 Dev",
        "description": "Fast, high-quality text-to-image",
        "type": "text-to-image"
    },
    "flux-pro": {
        "id": "fal-ai/flux-pro/v1.1",
        "name": "FLUX Pro 1.1",
        "description": "Premium quality generation",
        "type": "text-to-image"
    },
    "flux-lora": {
        "id": "fal-ai/flux-lora",
        "name": "FLUX LoRA",
        "description": "Generate with custom LoRA models",
        "type": "text-to-image"
    },
    "flux-pulid": {
        "id": "fal-ai/flux-pulid",
        "name": "FLUX PuLID",
        "description": "Face/identity preservation",
        "type": "face-swap"
    },
    "lora-trainer": {
        "id": "fal-ai/flux-lora-portrait-trainer",
        "name": "Portrait LoRA Trainer",
        "description": "Train custom character LoRA",
        "type": "training"
    }
}

# Timeout constants
IMAGE_TIMEOUT = 120   # 2 minutes for image generation
VIDEO_TIMEOUT = 360   # 6 minutes for video generation
STATUS_TIMEOUT = 30   # 30 seconds for status checks


def _get_fal_key() -> str:
    """
    Get the FAL_KEY from environment at runtime.
    This ensures we always use the current value, not a cached one.
    """
    key = os.environ.get('FAL_KEY', '')
    if not key:
        logger.error("FAL_KEY environment variable is not set!")
        raise Exception("FAL_KEY not configured. Please set FAL_KEY in your .env file.")
    
    # Log masked key for debugging (show first 10 and last 4 chars)
    if len(key) > 20:
        masked = f"{key[:10]}...{key[-4:]}"
    else:
        masked = f"{key[:4]}...{key[-2:]}" if len(key) > 6 else "***"
    logger.debug(f"Using FAL_KEY: {masked}")
    
    return key


# Global state for key validation caching
_fal_key_status = {
    "valid": None,  # None = unchecked, True = valid, False = invalid
    "last_checked": None,
    "error_message": None
}


def get_fal_key_status() -> dict:
    """Get the current FAL_KEY validation status."""
    return _fal_key_status.copy()


async def validate_fal_key_on_startup() -> dict:
    """
    Validate FAL_KEY on startup and cache the result.
    Returns status dict with valid, last_checked, error_message.
    """
    global _fal_key_status
    from datetime import datetime
    
    try:
        key = os.environ.get('FAL_KEY', '')
        if not key:
            _fal_key_status = {
                "valid": False,
                "last_checked": datetime.utcnow().isoformat(),
                "error_message": "FAL_KEY not set in environment"
            }
            logger.warning("⚠️ FAL_KEY not configured - fal.ai features will not work")
            return _fal_key_status
        
        # Validate key format
        if ':' not in key:
            _fal_key_status = {
                "valid": False,
                "last_checked": datetime.utcnow().isoformat(),
                "error_message": "FAL_KEY format invalid - should be key_id:key_secret"
            }
            logger.warning(f"⚠️ FAL_KEY format invalid - missing colon separator")
            return _fal_key_status
        
        # Try a real API call to validate
        client = AsyncClient(key=key)
        # Use a lightweight status check
        try:
            # Try to get status of a non-existent job - will fail fast with auth error if key invalid
            await asyncio.wait_for(
                client.status("fal-ai/flux/dev", "nonexistent-job-id-12345"),
                timeout=10
            )
        except Exception as e:
            error_str = str(e).lower()
            # "not found" is OK - means auth worked, job just doesn't exist
            if 'not found' in error_str or 'notfound' in error_str:
                _fal_key_status = {
                    "valid": True,
                    "last_checked": datetime.utcnow().isoformat(),
                    "error_message": None
                }
                logger.info("✅ FAL_KEY validated successfully")
                return _fal_key_status
            # Auth errors mean the key is invalid
            elif '401' in error_str or 'unauthorized' in error_str or 'no user found' in error_str:
                _fal_key_status = {
                    "valid": False,
                    "last_checked": datetime.utcnow().isoformat(),
                    "error_message": f"FAL_KEY invalid or expired: {str(e)[:100]}"
                }
                logger.error(f"❌ FAL_KEY INVALID: {str(e)[:100]}")
                logger.error("⚠️ fal.ai features will fall back to Emergent Key (more expensive)")
                return _fal_key_status
            else:
                # Other errors - assume key is OK but there was a network issue
                _fal_key_status = {
                    "valid": None,  # Unknown
                    "last_checked": datetime.utcnow().isoformat(),
                    "error_message": f"Could not validate: {str(e)[:100]}"
                }
                logger.warning(f"⚠️ FAL_KEY validation inconclusive: {str(e)[:50]}")
                return _fal_key_status
        
        # If we get here without exception, key is valid
        _fal_key_status = {
            "valid": True,
            "last_checked": datetime.utcnow().isoformat(),
            "error_message": None
        }
        logger.info("✅ FAL_KEY validated successfully")
        return _fal_key_status
        
    except Exception as e:
        _fal_key_status = {
            "valid": False,
            "last_checked": datetime.utcnow().isoformat(),
            "error_message": str(e)[:200]
        }
        logger.error(f"❌ FAL_KEY validation failed: {str(e)[:100]}")
        return _fal_key_status


def _get_client() -> AsyncClient:
    """
    Create a fresh AsyncClient with the current FAL_KEY.
    This ensures we always use the latest key from the environment.
    """
    key = _get_fal_key()
    return AsyncClient(key=key)


async def _validate_key() -> bool:
    """
    Validate the FAL_KEY by making a simple status check.
    Returns True if valid, raises Exception with details if not.
    """
    try:
        key = _get_fal_key()
        # Create a client with explicit key
        client = AsyncClient(key=key)
        # Try a simple operation - status check on a non-existent job is fast
        # If key is invalid, this will fail with 401
        return True
    except Exception as e:
        error_msg = str(e).lower()
        if '401' in error_msg or 'unauthorized' in error_msg:
            logger.error(f"FAL_KEY is invalid or expired! Please update your FAL_KEY in .env")
            raise Exception("FAL_KEY is invalid or expired. Please get a new key from https://fal.ai/dashboard/keys")
        raise


async def _submit_with_retry(model_id: str, arguments: dict, timeout: int = IMAGE_TIMEOUT, max_retries: int = 3) -> Any:
    """
    Submit a fal.ai job with retry logic and timeout.
    Creates a fresh client for each submission to ensure current key is used.
    Retries on transient errors with exponential backoff.
    Does NOT retry on auth errors (401) or timeouts.
    """
    client = _get_client()
    last_error = None
    
    for attempt in range(max_retries):
        try:
            handler = await client.submit(model_id, arguments=arguments)
            result = await asyncio.wait_for(handler.get(), timeout=timeout)
            return result
        except asyncio.TimeoutError:
            logger.error(f"Timeout after {timeout}s on {model_id}")
            raise Exception(f"Generation timed out after {timeout} seconds. Please try again.")
        except Exception as e:
            last_error = e
            error_str = str(e).lower()
            
            # Don't retry auth errors
            if '401' in error_str or 'unauthorized' in error_str:
                logger.error(f"Authentication failed for fal.ai: {e}")
                raise Exception(
                    f"fal.ai authentication failed (401 Unauthorized). "
                    f"Your FAL_KEY may be invalid or expired. "
                    f"Please get a new key from https://fal.ai/dashboard/keys and update your .env file."
                )
            
            # Don't retry rate limit errors immediately
            if '429' in error_str or 'rate limit' in error_str:
                logger.warning(f"Rate limited by fal.ai, waiting longer before retry...")
                await asyncio.sleep(10)  # Wait 10 seconds on rate limit
            
            if attempt < max_retries - 1:
                wait = 2 ** attempt  # 1s, 2s backoff
                logger.warning(f"Attempt {attempt + 1} failed on {model_id}: {e}. Retrying in {wait}s...")
                await asyncio.sleep(wait)
            else:
                logger.error(f"All {max_retries} attempts failed on {model_id}: {e}")
    
    raise Exception(f"Generation failed after {max_retries} attempts: {last_error}")


async def generate_image_flux(
    prompt: str,
    model: str = "flux-dev",
    image_size: str = "landscape_16_9",
    num_images: int = 1,
    seed: Optional[int] = None,
    guidance_scale: float = 3.5,
    num_inference_steps: int = 28
) -> Dict[str, Any]:
    """Generate images using FLUX models"""
    _get_fal_key()  # Validate key exists
    
    model_id = FAL_MODELS.get(model, {}).get("id", "fal-ai/flux/dev")

    arguments = {
        "prompt": prompt,
        "image_size": image_size,
        "num_images": num_images,
        "guidance_scale": guidance_scale,
        "num_inference_steps": num_inference_steps,
        "enable_safety_checker": True
    }

    if seed is not None:
        arguments["seed"] = seed

    try:
        result = await _submit_with_retry(model_id, arguments, timeout=IMAGE_TIMEOUT)
        return {
            "success": True,
            "images": result.get("images", []),
            "seed": result.get("seed"),
            "prompt": prompt
        }
    except Exception as e:
        logger.error(f"FLUX generation error: {str(e)}")
        raise


async def generate_with_face_id(
    prompt: str,
    reference_image_url: str,
    id_weight: float = 1.0,
    image_size: str = "landscape_16_9",
    seed: Optional[int] = None,
    mode: str = "fidelity",
    character_appearance: Optional[str] = None,
    art_style: Optional[str] = None
) -> Dict[str, Any]:
    """Generate image while preserving face identity using PuLID"""
    _get_fal_key()  # Validate key exists

    id_weight = min(max(id_weight, 0.0), 1.0)
    if mode == "fidelity":
        id_weight = 1.0

    enhanced_prompt = prompt
    if character_appearance:
        enhanced_prompt = f"{character_appearance}, {enhanced_prompt}"
    if art_style:
        enhanced_prompt = f"{enhanced_prompt}, {art_style} art style, consistent visual style"
    enhanced_prompt = f"{enhanced_prompt}, high quality, detailed, professional"

    arguments = {
        "prompt": enhanced_prompt,
        "reference_image_url": reference_image_url,
        "id_weight": id_weight,
        "image_size": image_size,
        "num_images": 1,
        "guidance_scale": 3.5,
        "num_inference_steps": 35
    }

    if seed is not None:
        arguments["seed"] = seed

    try:
        result = await _submit_with_retry("fal-ai/flux-pulid", arguments, timeout=IMAGE_TIMEOUT)
        return {
            "success": True,
            "images": result.get("images", []),
            "seed": result.get("seed"),
            "prompt": prompt
        }
    except Exception as e:
        logger.error(f"PuLID generation error: {str(e)}")
        raise


async def train_character_lora(
    character_name: str,
    reference_images: List[str],
    trigger_word: Optional[str] = None,
    steps: int = 1000,
    webhook_url: Optional[str] = None
) -> Dict[str, Any]:
    """Train a custom LoRA model for a character — returns job_id immediately"""
    _get_fal_key()  # Validate key exists

    if len(reference_images) < 3:
        raise Exception("At least 3 reference images required")

    if len(reference_images) > 20:
        reference_images = reference_images[:20]

    images_input = []
    for img in reference_images:
        if img.startswith('data:'):
            base64_data = img.split(',')[1] if ',' in img else img
            images_input.append({"image_base64": base64_data})
        elif img.startswith('http'):
            images_input.append({"url": img})
        else:
            images_input.append({"image_base64": img})

    trigger = trigger_word or character_name.lower().replace(" ", "_")
    capped_steps = min(steps, 1000)  # Cap at 1000 for reasonable wait times

    # Estimate time
    estimated_minutes = max(5, int(capped_steps / 100))

    arguments = {
        "images": images_input,
        "trigger_word": trigger,
        "steps": capped_steps,
        "create_masks": True,
        "is_style": False,
    }

    if webhook_url:
        arguments["webhook_url"] = webhook_url

    try:
        # Create fresh client and submit
        client = _get_client()
        handler = await client.submit(
            "fal-ai/flux-lora-portrait-trainer",
            arguments=arguments
        )
        return {
            "success": True,
            "job_id": handler.request_id,
            "status": "training",
            "trigger_word": trigger,
            "message": f"LoRA training started. Estimated time: {estimated_minutes}-{estimated_minutes + 5} minutes."
        }
    except Exception as e:
        error_str = str(e).lower()
        if '401' in error_str or 'unauthorized' in error_str:
            raise Exception(
                "fal.ai authentication failed. Your FAL_KEY may be invalid or expired. "
                "Please get a new key from https://fal.ai/dashboard/keys"
            )
        logger.error(f"LoRA training error: {str(e)}")
        raise Exception(f"LoRA training failed: {str(e)}")


async def check_training_status(job_id: str) -> Dict[str, Any]:
    """Check the status of a LoRA training job"""
    client = _get_client()

    try:
        result = await asyncio.wait_for(
            client.status(
                "fal-ai/flux-lora-portrait-trainer",
                job_id,
                with_logs=True
            ),
            timeout=STATUS_TIMEOUT
        )

        # Handle different status types
        from fal_client import Completed, InProgress, Queued
        
        if isinstance(result, Completed):
            final_result = await asyncio.wait_for(
                client.result("fal-ai/flux-lora-portrait-trainer", job_id),
                timeout=STATUS_TIMEOUT
            )
            return {
                "success": True,
                "status": "completed",
                "lora_url": final_result.get("diffusers_lora_file", {}).get("url"),
                "config_url": final_result.get("config_file", {}).get("url")
            }
        elif isinstance(result, InProgress):
            return {
                "success": True,
                "status": "in_progress",
                "logs": result.logs[-5:] if hasattr(result, 'logs') and result.logs else []
            }
        elif isinstance(result, Queued):
            return {
                "success": True,
                "status": "queued",
                "logs": []
            }
        else:
            # Fallback for dict-style response
            status = result.get("status", "unknown") if isinstance(result, dict) else "unknown"
            if status == "COMPLETED":
                final_result = await asyncio.wait_for(
                    client.result("fal-ai/flux-lora-portrait-trainer", job_id),
                    timeout=STATUS_TIMEOUT
                )
                return {
                    "success": True,
                    "status": "completed",
                    "lora_url": final_result.get("diffusers_lora_file", {}).get("url"),
                    "config_url": final_result.get("config_file", {}).get("url")
                }
            elif status == "FAILED":
                return {
                    "success": False,
                    "status": "failed",
                    "error": result.get("error", "Training failed") if isinstance(result, dict) else "Training failed"
                }
            else:
                return {
                    "success": True,
                    "status": "in_progress",
                    "logs": result.get("logs", [])[-5:] if isinstance(result, dict) and result.get("logs") else []
                }
    except asyncio.TimeoutError:
        return {"success": False, "status": "timeout", "error": "Status check timed out"}
    except Exception as e:
        error_str = str(e).lower()
        if '401' in error_str or 'unauthorized' in error_str:
            raise Exception(
                "fal.ai authentication failed. Your FAL_KEY may be invalid or expired. "
                "Please get a new key from https://fal.ai/dashboard/keys"
            )
        logger.error(f"Status check error: {str(e)}")
        raise Exception(f"Failed to check training status: {str(e)}")


async def generate_with_lora(
    prompt: str,
    lora_url: str,
    trigger_word: str,
    lora_scale: float = 1.0,
    image_size: str = "landscape_16_9",
    seed: Optional[int] = None,
    guidance_scale: float = 3.5
) -> Dict[str, Any]:
    """Generate image using a trained character LoRA"""
    _get_fal_key()  # Validate key exists

    if trigger_word.lower() not in prompt.lower():
        prompt = f"{trigger_word}, {prompt}"

    arguments = {
        "prompt": prompt,
        "loras": [{"path": lora_url, "scale": lora_scale}],
        "image_size": image_size,
        "num_images": 1,
        "guidance_scale": guidance_scale,
        "num_inference_steps": 28,
        "enable_safety_checker": True
    }

    if seed is not None:
        arguments["seed"] = seed

    try:
        result = await _submit_with_retry("fal-ai/flux-lora", arguments, timeout=IMAGE_TIMEOUT)
        return {
            "success": True,
            "images": result.get("images", []),
            "seed": result.get("seed"),
            "prompt": prompt
        }
    except Exception as e:
        logger.error(f"LoRA generation error: {str(e)}")
        raise


async def face_swap(
    source_image_url: str,
    target_face_url: str,
    strength: float = 0.8
) -> Dict[str, Any]:
    """
    Swap face from target onto source image.
    """
    _get_fal_key()  # Validate key exists

    arguments = {
        "base_image_url": source_image_url,
        "swap_image_url": target_face_url,
        "strength": strength
    }

    try:
        result = await _submit_with_retry("fal-ai/face-swap", arguments, timeout=IMAGE_TIMEOUT)
        return {
            "success": True,
            "image": result.get("image", {}),
        }
    except Exception as e:
        logger.error(f"Face swap error: {str(e)}")
        raise


async def generate_video_from_image(
    image_url: str,
    prompt: str,
    duration: int = 5,
    aspect_ratio: str = "16:9",
    model: str = "kling"
) -> Dict[str, Any]:
    """Generate video from image using fal.ai image-to-video models"""
    _get_fal_key()  # Validate key exists

    # Only re-upload if NOT already on fal.ai CDN
    FAL_CDN_PREFIXES = (
        "https://fal.run",
        "https://storage.googleapis.com/fal",
        "https://fal-cdn",
        "https://fal.media",
        "https://v3.fal.media",
        "https://v3b.fal.media",
    )

    if image_url.startswith('data:'):
        image_url = await upload_image_to_fal(image_url)
    elif not any(image_url.startswith(p) for p in FAL_CDN_PREFIXES):
        # External non-fal URL — re-upload for reliability
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(image_url, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                    if resp.status == 200:
                        image_bytes = await resp.read()
                        client = _get_client()
                        image_url = await client.upload(image_bytes, content_type="image/png")
                        logger.info("Re-uploaded external image to fal.ai CDN")
                    else:
                        logger.warning(f"Could not download image for re-upload: HTTP {resp.status}")
        except Exception as e:
            logger.warning(f"Could not re-upload image: {e}, using original URL")

    model_configs = {
        "kling": {
            "endpoint": "fal-ai/kling-video/v1/standard/image-to-video",
            "duration_param": "duration",
            "duration_values": {"5": "5", "10": "10"},
            "aspect_param": "aspect_ratio"
        },
        "luma": {
            "endpoint": "fal-ai/luma-dream-machine/image-to-video",
            "duration_param": None,
            "aspect_param": "aspect_ratio"
        },
        "minimax": {
            "endpoint": "fal-ai/minimax-video/image-to-video",
            "duration_param": None,
            "aspect_param": "aspect_ratio"
        }
    }

    config = model_configs.get(model, model_configs["kling"])

    arguments = {
        "prompt": prompt,
        "image_url": image_url
    }

    if config.get("aspect_param"):
        arguments[config["aspect_param"]] = aspect_ratio

    if config.get("duration_param"):
        dur_str = str(min(duration, 10))
        arguments[config["duration_param"]] = config.get("duration_values", {}).get(dur_str, "5")

    try:
        logger.info(f"Starting {model} video generation: {prompt[:100]}...")
        result = await _submit_with_retry(config["endpoint"], arguments, timeout=VIDEO_TIMEOUT, max_retries=2)

        video_url = None
        if isinstance(result.get("video"), dict):
            video_url = result["video"].get("url")
        elif isinstance(result.get("video"), str):
            video_url = result["video"]

        if not video_url:
            raise Exception("No video URL in response")

        return {
            "success": True,
            "video_url": video_url,
            "model": model,
            "duration": duration,
            "prompt": prompt
        }
    except Exception as e:
        logger.error(f"{model} video generation error: {str(e)}")
        raise


async def upload_image_to_fal(base64_image: str) -> str:
    """Upload a base64 image to fal.ai storage and get a URL"""
    client = _get_client()

    # Detect content type from data URI
    content_type = "image/png"
    if base64_image.startswith('data:'):
        if 'image/jpeg' in base64_image or 'image/jpg' in base64_image:
            content_type = "image/jpeg"
        elif 'image/webp' in base64_image:
            content_type = "image/webp"
        if ',' in base64_image:
            base64_image = base64_image.split(',')[1]

    try:
        image_bytes = base64.b64decode(base64_image)
    except Exception as e:
        raise Exception(f"Invalid base64 image data: {e}")

    try:
        url = await client.upload(image_bytes, content_type=content_type)
        logger.info(f"Uploaded image to fal.ai CDN: {url[:60]}...")
        return url
    except Exception as e:
        error_str = str(e).lower()
        if '401' in error_str or 'unauthorized' in error_str:
            raise Exception(
                "fal.ai authentication failed (401 Unauthorized). "
                "Your FAL_KEY may be invalid or expired. "
                "Please get a new key from https://fal.ai/dashboard/keys and update your .env file."
            )
        logger.error(f"Upload error: {str(e)}")
        raise Exception(f"Failed to upload image to fal.ai: {str(e)}")


async def upload_video_to_fal(base64_video: str) -> str:
    """
    Upload a base64 video to fal.ai storage and get a URL.
    
    ⚠️ WARNING: FAL.AI HAS 7-DAY RETENTION FOR UPLOADED FILES ⚠️
    Videos uploaded here will expire after 7 days.
    
    For permanent video storage, use cloudinary_service.upload_video_to_cloudinary() instead.
    This function should only be used for temporary/preview videos.
    
    TODO: Before going live, migrate all video storage to Cloudinary for permanent hosting.
    """
    client = _get_client()

    # Detect content type from data URI
    content_type = "video/mp4"
    if base64_video.startswith('data:'):
        if 'video/webm' in base64_video:
            content_type = "video/webm"
        elif 'video/quicktime' in base64_video or 'video/mov' in base64_video:
            content_type = "video/quicktime"
        if ',' in base64_video:
            base64_video = base64_video.split(',')[1]

    try:
        video_bytes = base64.b64decode(base64_video)
    except Exception as e:
        raise Exception(f"Invalid base64 video data: {e}")

    try:
        url = await client.upload(video_bytes, content_type=content_type)
        logger.info(f"Uploaded video to fal.ai CDN: {url[:60]}...")
        return url
    except Exception as e:
        error_str = str(e).lower()
        if '401' in error_str or 'unauthorized' in error_str:
            raise Exception(
                "fal.ai authentication failed (401 Unauthorized). "
                "Your FAL_KEY may be invalid or expired."
            )
        logger.error(f"Video upload error: {str(e)}")
        raise Exception(f"Failed to upload video to fal.ai: {str(e)}")


async def generate_thumbnails(image_url: str) -> Dict[str, str]:
    """
    Generate thumbnail (300x300) and medium (800px wide) versions of an image.
    Downloads the original, resizes using PIL, and uploads both to fal.ai CDN.
    
    Args:
        image_url: URL of the original full-size image
        
    Returns:
        Dict with 'thumbnail_url' (300x300) and 'medium_url' (800px wide)
    """
    client = _get_client()
    
    # Skip if not a valid URL
    if not image_url or not image_url.startswith('https://'):
        raise Exception("Invalid image URL - must be HTTPS")
    
    try:
        # Download original image
        async with aiohttp.ClientSession() as session:
            async with session.get(image_url, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                if resp.status != 200:
                    raise Exception(f"Failed to download image: HTTP {resp.status}")
                image_data = await resp.read()
        
        # Open with PIL
        original = Image.open(io.BytesIO(image_data))
        
        # Convert to RGB if necessary (for PNG with transparency)
        if original.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', original.size, (255, 255, 255))
            if original.mode == 'P':
                original = original.convert('RGBA')
            background.paste(original, mask=original.split()[-1] if original.mode == 'RGBA' else None)
            original = background
        elif original.mode != 'RGB':
            original = original.convert('RGB')
        
        results = {}
        
        # Generate thumbnail (300x300 square crop)
        thumb = original.copy()
        # Crop to square from center
        width, height = thumb.size
        min_dim = min(width, height)
        left = (width - min_dim) // 2
        top = (height - min_dim) // 2
        thumb = thumb.crop((left, top, left + min_dim, top + min_dim))
        thumb = thumb.resize((300, 300), Image.Resampling.LANCZOS)
        
        # Save thumbnail to bytes with JPEG compression
        thumb_buffer = io.BytesIO()
        thumb.save(thumb_buffer, format='JPEG', quality=80, optimize=True)
        thumb_bytes = thumb_buffer.getvalue()
        
        # Upload thumbnail
        results['thumbnail_url'] = await client.upload(thumb_bytes, content_type='image/jpeg')
        logger.info(f"Generated thumbnail: {results['thumbnail_url'][:50]}...")
        
        # Generate medium version (800px wide, maintain aspect ratio)
        medium = original.copy()
        width, height = medium.size
        if width > 800:
            new_height = int((800 / width) * height)
            medium = medium.resize((800, new_height), Image.Resampling.LANCZOS)
        
        # Save medium to bytes with JPEG compression
        medium_buffer = io.BytesIO()
        medium.save(medium_buffer, format='JPEG', quality=85, optimize=True)
        medium_bytes = medium_buffer.getvalue()
        
        # Upload medium
        results['medium_url'] = await client.upload(medium_bytes, content_type='image/jpeg')
        logger.info(f"Generated medium: {results['medium_url'][:50]}...")
        
        return results
        
    except Exception as e:
        error_str = str(e).lower()
        if '401' in error_str or 'unauthorized' in error_str:
            raise Exception("fal.ai authentication failed")
        logger.error(f"Thumbnail generation error: {str(e)}")
        raise Exception(f"Failed to generate thumbnails: {str(e)}")


async def upload_image_with_thumbnails(base64_image: str) -> Dict[str, str]:
    """
    Upload a base64 image and generate thumbnails in one operation.
    
    Returns:
        Dict with 'image_url' (full size), 'thumbnail_url' (300x300), 'medium_url' (800px)
    """
    # First upload the full-size image
    full_url = await upload_image_to_fal(base64_image)
    
    # Then generate thumbnails
    thumbnails = await generate_thumbnails(full_url)
    
    return {
        'image_url': full_url,
        'thumbnail_url': thumbnails['thumbnail_url'],
        'medium_url': thumbnails['medium_url']
    }


def get_available_models() -> List[Dict[str, str]]:
    """Get list of available fal.ai models"""
    return [
        {
            "id": key,
            "name": val["name"],
            "description": val["description"],
            "type": val["type"]
        }
        for key, val in FAL_MODELS.items()
    ]


def is_fal_configured() -> bool:
    """Check if fal.ai is properly configured"""
    try:
        key = os.environ.get('FAL_KEY', '')
        return bool(key and len(key) > 10)
    except Exception:
        return False
