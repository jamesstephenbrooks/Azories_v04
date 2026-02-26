#!/usr/bin/env python3
"""
Export all books and their page text to a structured document.
Usage: python scripts/export_books.py [--output filename.json]
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient

async def export_all_books(output_file="books_export.json"):
    """Export all books with their chapters and page text"""
    
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    db_name = os.environ.get('DB_NAME', 'test_database')
    
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    print(f"Connecting to {db_name}...")
    
    # Get all books
    books_cursor = db.books.find({}, {'_id': 0})
    books = await books_cursor.to_list(length=None)
    
    print(f"Found {len(books)} books")
    
    export_data = {
        "export_date": datetime.now().isoformat(),
        "total_books": len(books),
        "books": []
    }
    
    total_pages = 0
    
    for book in books:
        book_id = book.get('id')
        title = book.get('title', 'Untitled')
        print(f"  Exporting: {title}")
        
        # Get chapters for this book
        chapters_cursor = db.chapters.find({"book_id": book_id}, {'_id': 0}).sort("order", 1)
        chapters = await chapters_cursor.to_list(length=None)
        
        book_export = {
            "id": book_id,
            "title": title,
            "author": book.get('author', ''),
            "description": book.get('description', ''),
            "genre": book.get('genre', ''),
            "age_range": book.get('age_range', ''),
            "cover_image": book.get('cover_image', ''),
            "status": book.get('status', ''),
            "chapters": []
        }
        
        book_page_count = 0
        
        for chapter in chapters:
            chapter_id = chapter.get('id')
            
            # Get pages for this chapter
            pages_cursor = db.pages.find({"chapter_id": chapter_id}, {'_id': 0}).sort("page_number", 1)
            pages = await pages_cursor.to_list(length=None)
            
            chapter_export = {
                "id": chapter_id,
                "title": chapter.get('title', ''),
                "order": chapter.get('order', 0),
                "pages": []
            }
            
            for page in pages:
                page_export = {
                    "id": page.get('id'),
                    "page_number": page.get('page_number', 0),
                    "text_content": page.get('text_content', ''),
                    "text_word_count": len(page.get('text_content', '').split()),
                    "image_url": page.get('image_url', ''),
                    "image_prompt": page.get('image_prompt', '')
                }
                chapter_export["pages"].append(page_export)
                book_page_count += 1
            
            book_export["chapters"].append(chapter_export)
        
        book_export["total_pages"] = book_page_count
        total_pages += book_page_count
        export_data["books"].append(book_export)
    
    export_data["total_pages"] = total_pages
    
    # Calculate stats
    word_counts = []
    for book in export_data["books"]:
        for chapter in book["chapters"]:
            for page in chapter["pages"]:
                word_counts.append(page["text_word_count"])
    
    if word_counts:
        export_data["stats"] = {
            "total_pages": total_pages,
            "avg_words_per_page": round(sum(word_counts) / len(word_counts), 1),
            "min_words_per_page": min(word_counts),
            "max_words_per_page": max(word_counts)
        }
    
    # Save to file
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(export_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Export complete!")
    print(f"   Books: {len(books)}")
    print(f"   Pages: {total_pages}")
    print(f"   File: {output_file}")
    if word_counts:
        print(f"   Avg words/page: {export_data['stats']['avg_words_per_page']}")
    
    client.close()
    return export_data

async def export_books_markdown(output_file="books_export.md"):
    """Export books in markdown format for easy editing"""
    
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    db_name = os.environ.get('DB_NAME', 'test_database')
    
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    books_cursor = db.books.find({}, {'_id': 0}).sort("title", 1)
    books = await books_cursor.to_list(length=None)
    
    md_content = f"# Azories Books Export\n\nExported: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\nTotal Books: {len(books)}\n\n---\n\n"
    
    for book in books:
        book_id = book.get('id')
        title = book.get('title', 'Untitled')
        
        md_content += f"## {title}\n\n"
        md_content += f"**Book ID:** `{book_id}`\n\n"
        md_content += f"**Status:** {book.get('status', 'unknown')}\n\n"
        
        # Get chapters
        chapters_cursor = db.chapters.find({"book_id": book_id}, {'_id': 0}).sort("order", 1)
        chapters = await chapters_cursor.to_list(length=None)
        
        for chapter in chapters:
            chapter_id = chapter.get('id')
            chapter_title = chapter.get('title', 'Untitled Chapter')
            
            md_content += f"### {chapter_title}\n\n"
            
            # Get pages
            pages_cursor = db.pages.find({"chapter_id": chapter_id}, {'_id': 0}).sort("page_number", 1)
            pages = await pages_cursor.to_list(length=None)
            
            for page in pages:
                page_num = page.get('page_number', 0)
                text = page.get('text_content', '')
                word_count = len(text.split())
                page_id = page.get('id')
                
                md_content += f"**Page {page_num}** (ID: `{page_id}`, {word_count} words)\n\n"
                md_content += f"{text}\n\n"
                md_content += "---\n\n"
        
        md_content += "\n---\n\n"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(md_content)
    
    print(f"✅ Markdown export: {output_file}")
    client.close()

if __name__ == "__main__":
    output = sys.argv[1] if len(sys.argv) > 1 else "books_export.json"
    
    if output.endswith('.md'):
        asyncio.run(export_books_markdown(output))
    else:
        asyncio.run(export_all_books(output))
