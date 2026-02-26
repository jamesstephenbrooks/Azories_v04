#!/usr/bin/env python3
"""
Import/update book text from a JSON export file.
Usage: python scripts/import_books.py books_export.json [--dry-run]
"""

import asyncio
import json
import os
import sys
from motor.motor_asyncio import AsyncIOMotorClient

async def import_book_text(input_file, dry_run=False):
    """Update page text content from export file"""
    
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    db_name = os.environ.get('DB_NAME', 'test_database')
    
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    # Load the import file
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"{'DRY RUN - ' if dry_run else ''}Importing from {input_file}")
    print(f"Books in file: {len(data.get('books', []))}")
    
    updates_made = 0
    errors = 0
    
    for book in data.get('books', []):
        book_title = book.get('title', 'Unknown')
        print(f"\n  Processing: {book_title}")
        
        for chapter in book.get('chapters', []):
            for page in chapter.get('pages', []):
                page_id = page.get('id')
                new_text = page.get('text_content', '')
                
                if not page_id:
                    print(f"    ⚠️ Skipping page without ID")
                    continue
                
                # Get current page text
                current_page = await db.pages.find_one({"id": page_id})
                if not current_page:
                    print(f"    ⚠️ Page {page_id} not found in database")
                    errors += 1
                    continue
                
                current_text = current_page.get('text_content', '')
                
                # Only update if text has changed
                if current_text != new_text:
                    if dry_run:
                        print(f"    Would update page {page.get('page_number')}: {len(current_text)} -> {len(new_text)} chars")
                    else:
                        result = await db.pages.update_one(
                            {"id": page_id},
                            {"$set": {"text_content": new_text}}
                        )
                        if result.modified_count > 0:
                            print(f"    ✅ Updated page {page.get('page_number')}: {len(current_text)} -> {len(new_text)} chars")
                            updates_made += 1
    
    print(f"\n{'DRY RUN - ' if dry_run else ''}Import complete!")
    print(f"  Updates: {updates_made}")
    print(f"  Errors: {errors}")
    
    client.close()

async def update_single_page(page_id, new_text):
    """Update a single page's text content"""
    
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    db_name = os.environ.get('DB_NAME', 'test_database')
    
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    result = await db.pages.update_one(
        {"id": page_id},
        {"$set": {"text_content": new_text}}
    )
    
    if result.modified_count > 0:
        print(f"✅ Updated page {page_id}")
    else:
        print(f"⚠️ Page {page_id} not found or no change")
    
    client.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python import_books.py <input_file.json> [--dry-run]")
        print("       python import_books.py --page <page_id> 'new text content'")
        sys.exit(1)
    
    if sys.argv[1] == '--page':
        if len(sys.argv) < 4:
            print("Usage: python import_books.py --page <page_id> 'new text content'")
            sys.exit(1)
        asyncio.run(update_single_page(sys.argv[2], sys.argv[3]))
    else:
        input_file = sys.argv[1]
        dry_run = '--dry-run' in sys.argv
        asyncio.run(import_book_text(input_file, dry_run))
