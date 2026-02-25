"""
fal.ai Service Module for Pro Studio Character Consistency
"""

import os
import asyncio
import logging
from typing import Optional, List, Dict, Any
import fal_client
import base64
import aiohttp

logger = logging.getLogger(__name__)

# Validate FAL_KEY at startup
FAL_KEY = os.environ.get('FAL_KEY')
if not FAL_KEY:
    logger.error("FAL_KEY environment variable is not set — AI generation will fail")

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


async def _submit_with_retry(model_id: str, arguments: dict, timeout: int = IMAGE_TIMEOUT, max_retries: int = 3) -> Any:
    """
    Submit a fal.ai job with retry logic and timeout.
    Retries on transient errors with exponential backoff.
    Does NOT retry on timeouts.
    """
    last_error = None
    for attempt in range(max_retries):
        try:
            handler = await fal_client.submit_async(model_id, arguments=arguments)
            result = await asyncio.wait_for(handler.get(), timeout=timeout)
            return result
        except asyncio.TimeoutError:
            logger.error(f"Timeout after {timeout}s on {model_id}")
            raise Exception(f"Generation timed out after {timeout} seconds. Please try again.")
        except Exception as e:
            last_error = e
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
    if not FAL_KEY:
        raise Exception("FAL_KEY not configured")

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
        raise Exception(f"Image generation failed: {str(e)}")


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
    if not FAL_KEY:
        raise Exception("FAL_KEY not configured")

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
        "guidance_scale": 3.5,   # Fixed: was 2.5 which caused blurry output
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
        raise Exception(f"Face ID generation failed: {str(e)}")


async def train_character_lora(
    character_name: str,
    reference_images: List[str],
    trigger_word: Optional[str] = None,
    steps: int = 1000,
    webhook_url: Optional[str] = None
) -> Dict[str, Any]:
    """Train a custom LoRA model for a character — returns job_id immediately"""
    if not FAL_KEY:
        raise Exception("FAL_KEY not configured")

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
        # Submit and return immediately — do NOT call handler.get() for training
        handler = await fal_client.submit_async(
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
        logger.error(f"LoRA training error: {str(e)}")
        raise Exception(f"LoRA training failed: {str(e)}")


async def check_training_status(job_id: str) -> Dict[str, Any]:
    """Check the status of a LoRA training job"""
    if not FAL_KEY:
        raise Exception("FAL_KEY not configured")

    try:
        result = await asyncio.wait_for(
            fal_client.status_async(
                "fal-ai/flux-lora-portrait-trainer",
                job_id,
                with_logs=True
            ),
            timeout=STATUS_TIMEOUT
        )

        status = result.get("status", "unknown")

        if status == "COMPLETED":
            final_result = await asyncio.wait_for(
                fal_client.result_async("fal-ai/flux-lora-portrait-trainer", job_id),
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
                "error": result.get("error", "Training failed")
            }
        else:
            return {
                "success": True,
                "status": "in_progress",
                "logs": result.get("logs", [])[-5:] if result.get("logs") else []
            }
    except asyncio.TimeoutError:
        return {"success": False, "status": "timeout", "error": "Status check timed out"}
    except Exception as e:
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
    if not FAL_KEY:
        raise Exception("FAL_KEY not configured")

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
        raise Exception(f"LoRA generation failed: {str(e)}")


async def face_swap(
    source_image_url: str,
    target_face_url: str,
    strength: float = 0.8
) -> Dict[str, Any]:
    """
    Swap face from target onto source image.
    Uses PuLID as the implementation since it's more reliable than
    dedicated face-swap endpoints.
    """
    if not FAL_KEY:
        raise Exception("FAL_KEY not configured")

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
        raise Exception(f"Face swap failed: {str(e)}")


async def generate_video_from_image(
    image_url: str,
    prompt: str,
    duration: int = 5,
    aspect_ratio: str = "16:9",
    model: str = "kling"
) -> Dict[str, Any]:
    """Generate video from image using fal.ai image-to-video models"""
    if not FAL_KEY:
        raise Exception("FAL_KEY not configured")

    # Only re-upload if NOT already on fal.ai CDN
    # fal.ai URLs don't need re-uploading — this was adding 5-30s unnecessarily
    FAL_CDN_PREFIXES = (
        "https://fal.run",
        "https://storage.googleapis.com/fal",
        "https://fal-cdn",
        "https://fal.media",
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
                        image_url = await fal_client.upload_async(image_bytes, content_type="image/png")
                        logger.info("Re-uploaded external image to fal.ai CDN")
                    else:
                        logger.warning(f"Could not download image for re-upload: HTTP {resp.status}")
        except Exception as e:
            logger.warning(f"Could not re-upload image: {e}, using original URL")
    # else: already on fal.ai CDN — use directly, no re-upload needed

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
        raise Exception(f"Video generation failed: {str(e)}")


async def upload_image_to_fal(base64_image: str) -> str:
    """Upload a base64 image to fal.ai storage and get a URL"""
    if not FAL_KEY:
        raise Exception("FAL_KEY not configured")

    # Detect content type from data URI
    content_type = "image/png"
    if base64_image.startswith('data:'):
        if 'image/jpeg' in base64_image or 'image/jpg' in base64_image:
            content_type = "image/jpeg"
        elif 'image/webp' in base64_image:
            content_type = "image/webp"
        if ',' in base64_image:
            base64_image = base64_image.split(',')[1]

    image_bytes = base64.b64decode(base64_image)

    try:
        url = await fal_client.upload_async(image_bytes, content_type=content_type)
        return url
    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        raise Exception(f"Failed to upload image: {str(e)}")


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
