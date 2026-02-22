#!/usr/bin/env python3
"""
Optimize book cover images by converting to compressed JPEG.
This reduces image size from ~3MB to ~100-200KB.
"""

import asyncio
import os
import base64
import io
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from PIL import Image

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))

def optimize_image(base64_data: str, max_size: int = 800, quality: int = 75) -> str:
    """Compress and resize an image to reduce size."""
    try:
        # Extract the base64 data after the prefix
        if ',' in base64_data:
            header, data = base64_data.split(',', 1)
        else:
            data = base64_data
            header = 'data:image/jpeg;base64'
        
        # Decode the image
        img_bytes = base64.b64decode(data)
        img = Image.open(io.BytesIO(img_bytes))
        
        # Convert RGBA to RGB if needed (for JPEG)
        if img.mode in ('RGBA', 'P'):
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
            img = background
        elif img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Resize if larger than max_size
        width, height = img.size
        if max(width, height) > max_size:
            if width > height:
                new_width = max_size
                new_height = int(height * (max_size / width))
            else:
                new_height = max_size
                new_width = int(width * (max_size / height))
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Save as JPEG with compression
        buffer = io.BytesIO()
        img.save(buffer, format='JPEG', quality=quality, optimize=True)
        compressed_data = base64.b64encode(buffer.getvalue()).decode('utf-8')
        
        return f"data:image/jpeg;base64,{compressed_data}"
    except Exception as e:
        print(f"Error optimizing image: {e}")
        return base64_data  # Return original if optimization fails

async def optimize_all_covers():
    mongo_url = os.environ.get('MONGO_URL')
    db_name = os.environ.get('DB_NAME')
    
    if not mongo_url or not db_name:
        print("ERROR: MONGO_URL and DB_NAME required")
        return
    
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    # Get all books with covers
    books = await db.books.find(
        {'cover_image': {'$regex': '^data:image'}},
        {'_id': 0, 'id': 1, 'title': 1, 'cover_image': 1}
    ).to_list(100)
    
    print(f"Found {len(books)} books with covers to optimize\n")
    
    optimized = 0
    total_saved = 0
    
    for i, book in enumerate(books):
        original_size = len(book['cover_image']) / 1024
        
        # Skip if already optimized (small size)
        if original_size < 300:
            print(f"[{i+1}/{len(books)}] {book['title'][:30]}... - Already optimized ({original_size:.0f}KB)")
            continue
        
        print(f"[{i+1}/{len(books)}] {book['title'][:30]}... - Original: {original_size:.0f}KB", end='')
        
        # Optimize
        optimized_cover = optimize_image(book['cover_image'])
        new_size = len(optimized_cover) / 1024
        saved = original_size - new_size
        
        print(f" -> {new_size:.0f}KB (saved {saved:.0f}KB)")
        
        # Update in database
        await db.books.update_one(
            {'id': book['id']},
            {'$set': {'cover_image': optimized_cover}}
        )
        
        optimized += 1
        total_saved += saved
    
    print(f"\n✅ Optimized {optimized} covers, saved {total_saved/1024:.1f}MB total")

if __name__ == "__main__":
    asyncio.run(optimize_all_covers())
