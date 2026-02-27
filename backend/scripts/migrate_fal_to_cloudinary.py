"""
Migration script to copy all fal.ai images to Cloudinary permanent storage.
This script:
1. Finds all fal.ai image URLs in the books collection
2. Downloads and uploads each image to Cloudinary
3. Updates the database with new permanent URLs
4. Generates a migration report

Run with: python scripts/migrate_fal_to_cloudinary.py
"""

import asyncio
import os
import sys
import cloudinary
import cloudinary.uploader
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from datetime import datetime
import aiohttp
import json
import time

# Load environment variables
load_dotenv('/app/backend/.env')

# Configure Cloudinary
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
    secure=True
)

# MongoDB connection
MONGO_URL = os.environ.get('MONGO_URL')
DB_NAME = os.environ.get('DB_NAME')

# Migration stats
stats = {
    "total_fal_images": 0,
    "successfully_migrated": 0,
    "failed": 0,
    "already_cloudinary": 0,
    "errors": [],
    "migrated_urls": []
}


def is_fal_url(url: str) -> bool:
    """Check if URL is from fal.ai (temporary storage)"""
    if not url:
        return False
    return 'fal.media' in url or 'fal.ai' in url or 'fal-cdn' in url


def is_cloudinary_url(url: str) -> bool:
    """Check if URL is already from Cloudinary"""
    if not url:
        return False
    return 'cloudinary.com' in url or 'res.cloudinary.com' in url


async def upload_to_cloudinary(image_url: str, folder: str, public_id: str) -> dict:
    """
    Upload an image from URL to Cloudinary.
    Returns the upload result with secure_url.
    """
    try:
        # Use cloudinary's upload from URL feature
        result = cloudinary.uploader.upload(
            image_url,
            folder=folder,
            public_id=public_id,
            resource_type="image",
            overwrite=True,
            unique_filename=False
        )
        return {
            "success": True,
            "url": result.get("secure_url"),
            "public_id": result.get("public_id"),
            "format": result.get("format"),
            "width": result.get("width"),
            "height": result.get("height")
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


async def migrate_book_images(db):
    """Migrate all book page images from fal.ai to Cloudinary"""
    
    print("\n" + "="*60)
    print("PHASE 1: Migrating Book Page Images")
    print("="*60)
    
    books = await db.books.find({}).to_list(None)
    print(f"Found {len(books)} books to process")
    
    for book in books:
        book_id = book.get('id', str(book.get('_id')))
        book_title = book.get('title', 'Unknown')
        pages = book.get('pages', [])
        
        if not pages:
            continue
            
        updates_needed = False
        updated_pages = []
        
        for page in pages:
            page_copy = dict(page)
            image_url = page.get('image_url', '')
            
            if is_fal_url(image_url):
                stats["total_fal_images"] += 1
                page_num = page.get('page_number', 0)
                
                # Create a clean public_id for Cloudinary
                safe_title = book_title.lower().replace(' ', '_').replace("'", '').replace('"', '')[:30]
                public_id = f"page_{page_num:02d}"
                folder = f"azories/books/{safe_title}"
                
                print(f"  Migrating: {book_title} - Page {page_num}...")
                
                result = await upload_to_cloudinary(image_url, folder, public_id)
                
                if result["success"]:
                    page_copy['image_url'] = result["url"]
                    page_copy['image_url_original_fal'] = image_url  # Keep backup
                    updates_needed = True
                    stats["successfully_migrated"] += 1
                    stats["migrated_urls"].append({
                        "book": book_title,
                        "page": page_num,
                        "old_url": image_url[:60] + "...",
                        "new_url": result["url"]
                    })
                    print(f"    ✅ Migrated to: {result['url'][:60]}...")
                else:
                    stats["failed"] += 1
                    stats["errors"].append({
                        "book": book_title,
                        "page": page_num,
                        "error": result["error"]
                    })
                    print(f"    ❌ Failed: {result['error'][:60]}")
                
                # Small delay to avoid rate limiting
                await asyncio.sleep(0.3)
                
            elif is_cloudinary_url(image_url):
                stats["already_cloudinary"] += 1
            
            updated_pages.append(page_copy)
        
        # Update the book document if any pages were migrated
        if updates_needed:
            await db.books.update_one(
                {'id': book_id},
                {'$set': {'pages': updated_pages}}
            )
            print(f"  📝 Updated database for: {book_title}")


async def migrate_cover_images(db):
    """Migrate book cover images from fal.ai to Cloudinary"""
    
    print("\n" + "="*60)
    print("PHASE 2: Migrating Book Cover Images")
    print("="*60)
    
    books = await db.books.find({}).to_list(None)
    
    for book in books:
        book_id = book.get('id', str(book.get('_id')))
        book_title = book.get('title', 'Unknown')
        cover_url = book.get('cover_image', '') or book.get('cover_image_url', '')
        
        if is_fal_url(cover_url):
            stats["total_fal_images"] += 1
            
            safe_title = book_title.lower().replace(' ', '_').replace("'", '').replace('"', '')[:30]
            public_id = "cover"
            folder = f"azories/books/{safe_title}"
            
            print(f"  Migrating cover: {book_title}...")
            
            result = await upload_to_cloudinary(cover_url, folder, public_id)
            
            if result["success"]:
                update_fields = {}
                if book.get('cover_image'):
                    update_fields['cover_image'] = result["url"]
                    update_fields['cover_image_original_fal'] = cover_url
                if book.get('cover_image_url'):
                    update_fields['cover_image_url'] = result["url"]
                    update_fields['cover_image_url_original_fal'] = cover_url
                
                if update_fields:
                    await db.books.update_one(
                        {'id': book_id},
                        {'$set': update_fields}
                    )
                
                stats["successfully_migrated"] += 1
                print(f"    ✅ Cover migrated: {result['url'][:60]}...")
            else:
                stats["failed"] += 1
                stats["errors"].append({
                    "book": book_title,
                    "type": "cover",
                    "error": result["error"]
                })
                print(f"    ❌ Failed: {result['error'][:60]}")
            
            await asyncio.sleep(0.3)


async def migrate_character_images(db):
    """Migrate character thumbnail/reference images from fal.ai to Cloudinary"""
    
    print("\n" + "="*60)
    print("PHASE 3: Migrating Character Images")
    print("="*60)
    
    characters = await db.characters.find({}).to_list(None)
    print(f"Found {len(characters)} characters to process")
    
    for char in characters:
        char_id = char.get('id', str(char.get('_id')))
        char_name = char.get('name', 'Unknown')
        
        updates = {}
        
        # Check thumbnail
        thumbnail = char.get('thumbnail', '')
        if is_fal_url(thumbnail):
            stats["total_fal_images"] += 1
            safe_name = char_name.lower().replace(' ', '_').replace("'", '')[:20]
            
            print(f"  Migrating thumbnail: {char_name}...")
            result = await upload_to_cloudinary(
                thumbnail, 
                f"azories/characters/{safe_name}", 
                "thumbnail"
            )
            
            if result["success"]:
                updates['thumbnail'] = result["url"]
                updates['thumbnail_original_fal'] = thumbnail
                stats["successfully_migrated"] += 1
                print(f"    ✅ Thumbnail migrated")
            else:
                stats["failed"] += 1
                print(f"    ❌ Failed: {result['error'][:60]}")
            
            await asyncio.sleep(0.3)
        
        # Check reference images
        ref_images = char.get('reference_images', [])
        if ref_images:
            updated_refs = []
            for i, ref_url in enumerate(ref_images):
                if is_fal_url(ref_url):
                    stats["total_fal_images"] += 1
                    safe_name = char_name.lower().replace(' ', '_').replace("'", '')[:20]
                    
                    result = await upload_to_cloudinary(
                        ref_url,
                        f"azories/characters/{safe_name}",
                        f"ref_{i:02d}"
                    )
                    
                    if result["success"]:
                        updated_refs.append(result["url"])
                        stats["successfully_migrated"] += 1
                    else:
                        updated_refs.append(ref_url)  # Keep original if failed
                        stats["failed"] += 1
                    
                    await asyncio.sleep(0.3)
                else:
                    updated_refs.append(ref_url)
            
            if updated_refs != ref_images:
                updates['reference_images'] = updated_refs
                updates['reference_images_original_fal'] = ref_images
        
        # Apply updates
        if updates:
            await db.characters.update_one(
                {'id': char_id},
                {'$set': updates}
            )
            print(f"  📝 Updated database for character: {char_name}")


async def main():
    """Main migration function"""
    
    print("\n" + "="*60)
    print("FAL.AI TO CLOUDINARY MIGRATION")
    print(f"Started at: {datetime.now().isoformat()}")
    print("="*60)
    
    # Verify Cloudinary config
    print(f"\nCloudinary Cloud Name: {os.getenv('CLOUDINARY_CLOUD_NAME')}")
    print(f"Cloudinary API Key: {os.getenv('CLOUDINARY_API_KEY')[:10]}...")
    
    # Connect to MongoDB
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    print(f"Connected to database: {DB_NAME}")
    
    # Run migrations
    await migrate_book_images(db)
    await migrate_cover_images(db)
    await migrate_character_images(db)
    
    # Print summary
    print("\n" + "="*60)
    print("MIGRATION COMPLETE - SUMMARY")
    print("="*60)
    print(f"Total fal.ai images found: {stats['total_fal_images']}")
    print(f"Successfully migrated: {stats['successfully_migrated']}")
    print(f"Failed migrations: {stats['failed']}")
    print(f"Already on Cloudinary: {stats['already_cloudinary']}")
    
    if stats["errors"]:
        print(f"\nErrors encountered ({len(stats['errors'])}):")
        for err in stats["errors"][:10]:
            print(f"  - {err}")
    
    # Save report
    report_path = f"/app/backend/scripts/migration_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_path, 'w') as f:
        json.dump(stats, f, indent=2)
    print(f"\nFull report saved to: {report_path}")
    
    # Close connection
    client.close()
    
    return stats


if __name__ == "__main__":
    asyncio.run(main())
