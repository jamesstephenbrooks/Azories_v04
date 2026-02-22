"""
fal.ai Service Module for Pro Studio Character Consistency

This module provides:
- Character LoRA Training (flux-lora-portrait-trainer)
- Consistent Character Generation (flux-lora)
- Face Swap / Identity Preservation (flux-pulid)
- High-quality Image Generation (flux/dev, nano-banana-pro)
"""

import os
import asyncio
import logging
from typing import Optional, List, Dict, Any
import fal_client
import base64
import aiohttp

logger = logging.getLogger(__name__)

# Set FAL_KEY from environment
FAL_KEY = os.environ.get('FAL_KEY')
if FAL_KEY:
    os.environ["FAL_KEY"] = FAL_KEY

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


async def generate_image_flux(
    prompt: str,
    model: str = "flux-dev",
    image_size: str = "landscape_16_9",
    num_images: int = 1,
    seed: Optional[int] = None,
    guidance_scale: float = 3.5,
    num_inference_steps: int = 28
) -> Dict[str, Any]:
    """
    Generate images using FLUX models
    
    Args:
        prompt: Text description of the image
        model: Model to use (flux-dev, flux-pro)
        image_size: Output size (square_hd, landscape_16_9, portrait_16_9, etc.)
        num_images: Number of images to generate
        seed: Random seed for reproducibility
        guidance_scale: How closely to follow the prompt
        num_inference_steps: Quality/speed tradeoff
    
    Returns:
        Dict with images list and metadata
    """
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
        handler = await fal_client.submit_async(model_id, arguments=arguments)
        result = await handler.get()
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
    seed: Optional[int] = None
) -> Dict[str, Any]:
    """
    Generate image while preserving face identity using PuLID
    
    This is the key function for consistent character generation.
    It takes a reference face image and generates new images
    that maintain the same facial identity.
    
    Args:
        prompt: Text description of the scene/pose
        reference_image_url: URL or base64 of the reference face image
        id_weight: Strength of identity preservation (0.0-1.0)
        image_size: Output image size
        seed: Random seed for reproducibility
    
    Returns:
        Dict with generated image and metadata
    """
    if not FAL_KEY:
        raise Exception("FAL_KEY not configured")
    
    # Convert base64 to URL if needed
    if reference_image_url.startswith('data:'):
        # For base64 images, we need to upload first or use as-is
        # fal.ai supports both URLs and base64
        pass
    
    arguments = {
        "prompt": prompt,
        "reference_images": [{"url": reference_image_url}] if not reference_image_url.startswith('data:') else [],
        "id_weight": id_weight,
        "image_size": image_size,
        "num_images": 1,
        "guidance_scale": 4.0,
        "num_inference_steps": 28
    }
    
    # Handle base64 reference
    if reference_image_url.startswith('data:'):
        if ',' in reference_image_url:
            base64_data = reference_image_url.split(',')[1]
        else:
            base64_data = reference_image_url
        arguments["reference_images"] = [{"image_base64": base64_data}]
    
    if seed is not None:
        arguments["seed"] = seed
    
    try:
        handler = await fal_client.submit_async("fal-ai/flux-pulid", arguments=arguments)
        result = await handler.get()
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
    """
    Train a custom LoRA model for a character
    
    This creates a persistent model that can generate the same
    character consistently across unlimited images.
    
    Args:
        character_name: Name for the character/model
        reference_images: List of image URLs or base64 strings (3-20 images)
        trigger_word: Word to use in prompts to activate the LoRA
        steps: Training steps (more = better quality but longer)
        webhook_url: URL to call when training completes
    
    Returns:
        Dict with job_id and status
    """
    if not FAL_KEY:
        raise Exception("FAL_KEY not configured")
    
    if len(reference_images) < 3:
        raise Exception("At least 3 reference images required")
    
    if len(reference_images) > 20:
        reference_images = reference_images[:20]
    
    # Prepare images in the correct format
    images_input = []
    for idx, img in enumerate(reference_images):
        if img.startswith('data:'):
            # Base64 image
            if ',' in img:
                base64_data = img.split(',')[1]
            else:
                base64_data = img
            images_input.append({"image_base64": base64_data})
        elif img.startswith('http'):
            # URL image
            images_input.append({"url": img})
        else:
            # Assume it's raw base64
            images_input.append({"image_base64": img})
    
    trigger = trigger_word or character_name.lower().replace(" ", "_")
    
    arguments = {
        "images": images_input,
        "trigger_word": trigger,
        "steps": min(steps, 2000),  # Cap at 2000 steps
        "create_masks": True,  # Auto-detect face regions
        "is_style": False,  # This is a character, not a style
    }
    
    if webhook_url:
        arguments["webhook_url"] = webhook_url
    
    try:
        handler = await fal_client.submit_async(
            "fal-ai/flux-lora-portrait-trainer",
            arguments=arguments
        )
        
        # For training, we return the job info immediately
        # The actual training takes 5-15 minutes
        return {
            "success": True,
            "job_id": handler.request_id,
            "status": "training",
            "trigger_word": trigger,
            "message": "LoRA training started. This typically takes 5-15 minutes."
        }
    except Exception as e:
        logger.error(f"LoRA training error: {str(e)}")
        raise Exception(f"LoRA training failed: {str(e)}")


async def check_training_status(job_id: str) -> Dict[str, Any]:
    """
    Check the status of a LoRA training job
    
    Args:
        job_id: The job ID returned from train_character_lora
    
    Returns:
        Dict with status and lora_url when complete
    """
    if not FAL_KEY:
        raise Exception("FAL_KEY not configured")
    
    try:
        result = await fal_client.status_async(
            "fal-ai/flux-lora-portrait-trainer",
            job_id,
            with_logs=True
        )
        
        status = result.get("status", "unknown")
        
        if status == "COMPLETED":
            # Get the result to extract the LoRA URL
            final_result = await fal_client.result_async(
                "fal-ai/flux-lora-portrait-trainer",
                job_id
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
    """
    Generate image using a trained character LoRA
    
    This produces highly consistent character images once
    the LoRA has been trained.
    
    Args:
        prompt: Full prompt (should include trigger_word)
        lora_url: URL to the trained LoRA model
        trigger_word: The trigger word used during training
        lora_scale: Strength of the LoRA effect (0.0-1.0)
        image_size: Output image size
        seed: Random seed for reproducibility
        guidance_scale: How closely to follow the prompt
    
    Returns:
        Dict with generated image and metadata
    """
    if not FAL_KEY:
        raise Exception("FAL_KEY not configured")
    
    # Ensure trigger word is in prompt
    if trigger_word.lower() not in prompt.lower():
        prompt = f"{trigger_word}, {prompt}"
    
    arguments = {
        "prompt": prompt,
        "loras": [
            {
                "path": lora_url,
                "scale": lora_scale
            }
        ],
        "image_size": image_size,
        "num_images": 1,
        "guidance_scale": guidance_scale,
        "num_inference_steps": 28,
        "enable_safety_checker": True
    }
    
    if seed is not None:
        arguments["seed"] = seed
    
    try:
        handler = await fal_client.submit_async("fal-ai/flux-lora", arguments=arguments)
        result = await handler.get()
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
    Swap face from target onto source image
    
    Args:
        source_image_url: Image to modify (scene/pose)
        target_face_url: Face to insert
        strength: How strongly to apply the swap
    
    Returns:
        Dict with swapped image
    """
    if not FAL_KEY:
        raise Exception("FAL_KEY not configured")
    
    arguments = {
        "base_image_url": source_image_url,
        "swap_image_url": target_face_url,
        "strength": strength
    }
    
    try:
        # Note: fal.ai face swap might be under a different endpoint
        # This is a placeholder - we'll use PuLID for face consistency instead
        handler = await fal_client.submit_async("fal-ai/face-swap", arguments=arguments)
        result = await handler.get()
        return {
            "success": True,
            "image": result.get("image", {}),
        }
    except Exception as e:
        logger.error(f"Face swap error: {str(e)}")
        # Fallback: Use PuLID for face swap
        raise Exception(f"Face swap failed: {str(e)}")


# Utility function to convert base64 to URL via fal.ai storage
async def upload_image_to_fal(base64_image: str) -> str:
    """
    Upload a base64 image to fal.ai storage and get a URL
    
    Args:
        base64_image: Base64 encoded image (with or without data URI prefix)
    
    Returns:
        URL to the uploaded image
    """
    if not FAL_KEY:
        raise Exception("FAL_KEY not configured")
    
    # Remove data URI prefix if present
    if base64_image.startswith('data:'):
        if ',' in base64_image:
            base64_image = base64_image.split(',')[1]
    
    # Decode base64 to bytes
    image_bytes = base64.b64decode(base64_image)
    
    try:
        # Use fal_client's upload functionality
        url = await fal_client.upload_async(image_bytes, content_type="image/png")
        return url
    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        raise Exception(f"Failed to upload image: {str(e)}")


# Export available models for frontend
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
