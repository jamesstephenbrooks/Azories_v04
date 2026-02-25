"""
Comprehensive Migration Script to convert ALL base64 images to fal.ai CDN URLs.
This handles: art_studio_generations, character_gallery, books, pages.

Run with: cd /app/backend && python scripts/migrate_all_images_to_cdn.py
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

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Rate limiting to avoid overwhelming fal.ai
BATCH_SIZE = 10
DELAY_BETWEEN_BATCHES = 2  # seconds


async def migrate_collection(db, collection_name: str, fields: list) -> dict:
    """
    Migrate base64 images in a collection to CDN URLs.
    
    Args:
        db: MongoDB database connection
        collection_name: Name of the collection
        fields: List of field names that may contain base64 images
    
    Returns:
        dict with migration stats
    """
    coll = db[collection_name]
    stats = {"migrated": 0, "failed": 0, "skipped": 0}
    
    for field in fields:
        # Find documents with base64 images in this field
        query = {field: {"$regex": "^data:image"}}
        docs = await coll.find(query, {"_id": 1, field: 1}).to_list(1000)
        
        if not docs:
            logger.info(f"  {collection_name}.{field}: No base64 images found")
            continue
        
        logger.info(f"  {collection_name}.{field}: Found {len(docs)} base64 images to migrate")
        
        for i, doc in enumerate(docs):
            doc_id = doc["_id"]
            base64_image = doc.get(field, "")
            
            if not base64_image or not base64_image.startswith("data:image"):
                stats["skipped"] += 1
                continue
            
            try:
                # Upload to CDN
                cdn_url = await upload_image_to_fal(base64_image)
                
                # Update the document
                await coll.update_one(
                    {"_id": doc_id},
                    {"$set": {field: cdn_url, f"{field}_migrated_from_base64": True}}
                )
                
                stats["migrated"] += 1
                
                if (i + 1) % 10 == 0:
                    logger.info(f"    Progress: {i + 1}/{len(docs)} migrated")
                
                # Rate limiting
                if (i + 1) % BATCH_SIZE == 0:
                    await asyncio.sleep(DELAY_BETWEEN_BATCHES)
                    
            except Exception as e:
                stats["failed"] += 1
                logger.error(f"    Failed to migrate doc {doc_id}: {e}")
    
    return stats


async def run_migration():
    """Run the full migration across all collections."""
    
    logger.info("=" * 60)
    logger.info("STARTING COMPREHENSIVE BASE64 TO CDN MIGRATION")
    logger.info("=" * 60)
    
    # Connect to MongoDB
    mongo_url = os.environ.get('MONGO_URL')
    db_name = os.environ.get('DB_NAME')
    
    if not mongo_url:
        logger.error("MONGO_URL not set!")
        return
    
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    # Test connection
    try:
        await db.command("ping")
        logger.info(f"Connected to MongoDB: {db_name}")
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        return
    
    # Collections and their image fields
    migrations = [
        ("art_studio_generations", ["image_url"]),
        ("character_gallery", ["image_url"]),
        ("books", ["cover_image", "back_cover_image"]),
        ("pages", ["image_url", "image_url_2", "image_url_3", "image_url_4"]),
        ("art_studio_gallery", ["image_url"]),  # In case any were missed
        ("pro_studio_characters", ["image_url", "source_image", "reference_image", "preview_url"]),
        ("pro_studio_scenes", ["image_url", "source_image"]),
    ]
    
    total_stats = {"migrated": 0, "failed": 0, "skipped": 0}
    
    for collection_name, fields in migrations:
        logger.info(f"\n--- Migrating {collection_name} ---")
        
        if collection_name not in await db.list_collection_names():
            logger.info(f"  Collection {collection_name} does not exist, skipping")
            continue
        
        stats = await migrate_collection(db, collection_name, fields)
        
        total_stats["migrated"] += stats["migrated"]
        total_stats["failed"] += stats["failed"]
        total_stats["skipped"] += stats["skipped"]
        
        logger.info(f"  {collection_name}: migrated={stats['migrated']}, failed={stats['failed']}, skipped={stats['skipped']}")
    
    logger.info("\n" + "=" * 60)
    logger.info("MIGRATION COMPLETE")
    logger.info("=" * 60)
    logger.info(f"Total migrated: {total_stats['migrated']}")
    logger.info(f"Total failed: {total_stats['failed']}")
    logger.info(f"Total skipped: {total_stats['skipped']}")
    
    client.close()


if __name__ == "__main__":
    asyncio.run(run_migration())
