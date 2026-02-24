"""
Migration script to convert base64 images in gallery to fal.ai CDN URLs
This will improve gallery loading performance significantly
"""

import asyncio
import os
import sys
import logging
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))

from fal_service import upload_image_to_fal

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def migrate_gallery_images():
    """Convert base64 images to CDN URLs"""
    
    client = AsyncIOMotorClient(os.environ.get('MONGO_URL'))
    db = client[os.environ.get('DB_NAME')]
    
    # Find all items with base64 images
    base64_items = await db.art_studio_gallery.find({
        'image_url': {'$regex': '^data:image'}
    }).to_list(1000)
    
    logger.info(f"Found {len(base64_items)} items with base64 images to migrate")
    
    migrated = 0
    failed = 0
    
    for item in base64_items:
        try:
            item_id = item['_id']
            image_url = item.get('image_url', '')
            name = item.get('name', 'Unknown')
            
            if not image_url.startswith('data:image'):
                continue
            
            logger.info(f"Migrating: {name} ({len(image_url)} chars)")
            
            # Upload to fal.ai CDN
            cdn_url = await upload_image_to_fal(image_url)
            
            # Update the database record
            await db.art_studio_gallery.update_one(
                {'_id': item_id},
                {'$set': {'image_url': cdn_url, 'migrated_from_base64': True}}
            )
            
            migrated += 1
            logger.info(f"✓ Migrated {name} to: {cdn_url[:60]}...")
            
        except Exception as e:
            failed += 1
            logger.error(f"✗ Failed to migrate {item.get('name', 'Unknown')}: {e}")
    
    logger.info(f"\n=== Migration Complete ===")
    logger.info(f"Migrated: {migrated}")
    logger.info(f"Failed: {failed}")
    logger.info(f"Total: {len(base64_items)}")

if __name__ == "__main__":
    asyncio.run(migrate_gallery_images())
