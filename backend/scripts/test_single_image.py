#!/usr/bin/env python3
"""
Test script to generate a single page image for The Wizard's Apprentice page 1
Uses fal.ai for image generation and Cloudinary for hosting
Uploads to a NEW unique filename (not overwriting existing)
"""

import os
import sys
import fal_client
import cloudinary
import cloudinary.uploader
import requests
from io import BytesIO

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Cloudinary config
cloudinary.config(
    cloud_name=os.environ.get('CLOUDINARY_CLOUD_NAME', 'dlbmjqmoy'),
    api_key=os.environ.get('CLOUDINARY_API_KEY'),
    api_secret=os.environ.get('CLOUDINARY_API_SECRET')
)

# FAL config
os.environ['FAL_KEY'] = os.environ.get('FAL_KEY', '')

def generate_image(prompt: str) -> str:
    """Generate an image using fal.ai flux model"""
    print(f"Generating image with prompt: {prompt[:100]}...")
    
    # Use flux-pro for high quality
    result = fal_client.subscribe(
        "fal-ai/flux-pro/v1.1",
        arguments={
            "prompt": prompt,
            "image_size": {
                "width": 768,
                "height": 1024  # Portrait orientation for book pages
            },
            "num_images": 1,
            "enable_safety_checker": True,
            "safety_tolerance": "2"
        }
    )
    
    if result and 'images' in result and len(result['images']) > 0:
        image_url = result['images'][0]['url']
        print(f"Image generated: {image_url[:80]}...")
        return image_url
    else:
        raise Exception(f"No image generated. Result: {result}")

def upload_to_cloudinary(image_url: str, public_id: str) -> str:
    """Upload image to Cloudinary with a specific public_id"""
    print(f"Uploading to Cloudinary as: {public_id}")
    
    # Download the image first
    response = requests.get(image_url)
    if response.status_code != 200:
        raise Exception(f"Failed to download image: {response.status_code}")
    
    # Upload to Cloudinary - NOT overwriting, using unique public_id
    result = cloudinary.uploader.upload(
        BytesIO(response.content),
        public_id=public_id,
        folder="",  # Already included in public_id
        overwrite=False,  # Do NOT overwrite existing files
        resource_type="image"
    )
    
    return result['secure_url']

def main():
    # The prompt for page 1 - based on the text content
    page_prompt = """Pixar-style 3D animated illustration for a children's fantasy book.
Scene: An elderly wizard with a long white beard and blue pointed hat opens his tower door wider to welcome a young girl named Mira who stands dripping wet in the rain on his doorstep.
The wizard looks curious and interested. The girl looks determined despite being soaked.
Setting: A cozy wizard's tower entrance on a rainy day, warm light spilling from inside.
Style: Pixar/Disney 3D animation style, warm lighting, cinematic composition, highly detailed, whimsical and magical atmosphere.
IMPORTANT: No text, no words, no letters, no writing of any kind in the image. Pure illustration only."""

    try:
        # Step 1: Generate the image
        print("=" * 50)
        print("STEP 1: Generating image with fal.ai")
        print("=" * 50)
        fal_image_url = generate_image(page_prompt)
        
        # Step 2: Upload to Cloudinary with NEW unique filename
        print("\n" + "=" * 50)
        print("STEP 2: Uploading to Cloudinary")
        print("=" * 50)
        
        # Use a unique public_id that does NOT overwrite the existing file
        new_public_id = "azories/books/the_wizards_apprentice/page_01_clean"
        
        cloudinary_url = upload_to_cloudinary(fal_image_url, new_public_id)
        
        print("\n" + "=" * 50)
        print("SUCCESS!")
        print("=" * 50)
        print(f"\nNEW CLOUDINARY URL:")
        print(cloudinary_url)
        print("\nPlease open this URL in your browser to verify the image is:")
        print("1. Clean Pixar-style (not watercolor)")
        print("2. Portrait orientation")
        print("3. No text/words baked in")
        
        return cloudinary_url
        
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
