"""
Migration Script: Generate thumbnails for existing gallery images.
This creates 300x300 thumbnails and 800px medium versions for all CDN images.

Run with: cd /app/backend && python scripts/generate_thumbnails.py
"""

import asyncio
import os
import sys
import logging
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
load_dotenv(env_path, override=True)

from motor.motor_asyncio import AsyncIOMotorClient
from fal_service import generate_thumbnails, is_fal_configured

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Rate limiting
BATCH_SIZE = 5
DELAY_BETWEEN_BATCHES = 3
DELAY_BETWEEN_ITEMS = 0.5


async def migrate_collection(db, collection_name: str) -> dict:
    """Generate thumbnails for images in a collection."""
    coll = db[collection_name]
    stats = {"processed": 0, "skipped": 0, "failed": 0, "already_done": 0}
    
    # Find images with CDN URLs but no thumbnails
    query = {
        "image_url": {"$regex": "^https://"},
        "$or": [
            {"thumbnail_url": {"$exists": False}},
            {"thumbnail_url": None}
        ]
    }
    
    # Exclude videos/animations
    if collection_name == "art_studio_gallery":
        query["type"] = {"$ne": "animation"}
    
    docs = await coll.find(query, {"_id": 1, "image_url": 1, "name": 1}).to_list(1000)
    
    if not docs:
        logger.info(f"  {collection_name}: No images need thumbnails")
        return stats
    
    logger.info(f"  {collection_name}: Found {len(docs)} images needing thumbnails")
    
    for i, doc in enumerate(docs):
        doc_id = doc["_id"]
        image_url = doc.get("image_url", "")
        name = doc.get("name", "Unknown")[:30]
        
        if not image_url.startswith("https://"):
            stats["skipped"] += 1
            continue
        
        try:
            # Generate thumbnails
            thumbnails = await generate_thumbnails(image_url)
            
            # Update document
            await coll.update_one(
                {"_id": doc_id},
                {"$set": {
                    "thumbnail_url": thumbnails["thumbnail_url"],
                    "medium_url": thumbnails["medium_url"],
                    "thumbnails_generated_at": datetime.utcnow()
                }}
            )
            
            stats["processed"] += 1
            logger.info(f"    ✓ [{i+1}/{len(docs)}] {name}: thumbnails generated")
            
            # Rate limiting
            await asyncio.sleep(DELAY_BETWEEN_ITEMS)
            if (i + 1) % BATCH_SIZE == 0:
                logger.info(f"    Pausing for rate limit... ({i+1}/{len(docs)} done)")
                await asyncio.sleep(DELAY_BETWEEN_BATCHES)
                
        except Exception as e:
            stats["failed"] += 1
            error_str = str(e).lower()
            if '401' in error_str or 'unauthorized' in error_str:
                logger.error(f"    ✗ AUTH ERROR: FAL_KEY may be invalid")
                if stats["failed"] >= 3:
                    logger.error("    Stopping due to repeated auth errors")
                    return stats
            else:
                logger.warning(f"    ✗ [{i+1}/{len(docs)}] {name}: {str(e)[:50]}")
    
    return stats


async def run_migration():
    """Run thumbnail generation for all collections."""
    
    logger.info("=" * 60)
    logger.info("THUMBNAIL GENERATION MIGRATION")
    logger.info("=" * 60)
    
    if not is_fal_configured():
        logger.error("FAL_KEY not configured!")
        return
    
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
        logger.error(f"Failed to connect: {e}")
        return
    
    # Get before stats
    logger.info("\n--- BEFORE STATS ---")
    for coll_name in ["art_studio_gallery", "character_gallery"]:
        if coll_name in await db.list_collection_names():
            total = await db[coll_name].count_documents({"image_url": {"$regex": "^https://"}})
            with_thumbs = await db[coll_name].count_documents({
                "image_url": {"$regex": "^https://"},
                "thumbnail_url": {"$regex": "^https://"}
            })
            logger.info(f"  {coll_name}: {with_thumbs}/{total} have thumbnails")
    
    # Collections to process
    collections = ["art_studio_gallery", "character_gallery"]
    
    total_stats = {"processed": 0, "skipped": 0, "failed": 0, "already_done": 0}
    
    for coll_name in collections:
        logger.info(f"\n--- Processing {coll_name} ---")
        
        if coll_name not in await db.list_collection_names():
            logger.info(f"  Collection does not exist, skipping")
            continue
        
        stats = await migrate_collection(db, coll_name)
        
        for key in total_stats:
            total_stats[key] += stats.get(key, 0)
        
        logger.info(f"  {coll_name}: processed={stats['processed']}, failed={stats['failed']}")
    
    # Get after stats
    logger.info("\n--- AFTER STATS ---")
    for coll_name in ["art_studio_gallery", "character_gallery"]:
        if coll_name in await db.list_collection_names():
            total = await db[coll_name].count_documents({"image_url": {"$regex": "^https://"}})
            with_thumbs = await db[coll_name].count_documents({
                "image_url": {"$regex": "^https://"},
                "thumbnail_url": {"$regex": "^https://"}
            })
            logger.info(f"  {coll_name}: {with_thumbs}/{total} have thumbnails")
    
    logger.info("\n" + "=" * 60)
    logger.info("MIGRATION COMPLETE")
    logger.info("=" * 60)
    logger.info(f"Total processed: {total_stats['processed']}")
    logger.info(f"Total failed: {total_stats['failed']}")
    logger.info(f"Total skipped: {total_stats['skipped']}")
    
    client.close()


if __name__ == "__main__":
    asyncio.run(run_migration())
