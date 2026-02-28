#!/usr/bin/env python3
"""
Generate long-form story text for books with short placeholder text.
Uses OpenAI GPT-4o via Emergent LLM integration.
"""

import os
import asyncio
import json
from datetime import datetime
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv('/app/backend/.env')

from emergentintegrations.llm.chat import LlmChat, UserMessage

# Config
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'test_database')
EMERGENT_KEY = os.environ.get('EMERGENT_LLM_KEY')

client = MongoClient(MONGO_URL)
db = client[DB_NAME]

# Books with short text that need expansion
SHORT_TEXT_BOOKS = [
    "Aliens at My School",
    "Astronaut Alex's Moon Mission",
    "Bedtime in the Animal World",
    "Desert Treasure Hunt",
    "Elves and the Magic Tree",
    "Fairies of Moonlight Meadow",
    "Guardians of Tomorrow",
    "Mystery at the Zoo",
    "Princess Penny's Pet Dragon",
    "Puzzle Palace Adventures",
    "River Rafting Raccoons",
    "Safari Sam's Big Day",
    "Seasons of the Magic Forest",
    "Shapes in the City",
    "The Dragon's Secret Garden",
    "The Haunted Library Book",
    "The Mermaid's Lost Pearl",
    "The Missing Birthday Present",
    "The Monster Who Was Scared of Kids"
]

LOG_FILE = '/tmp/text_generation.log'
PROGRESS_FILE = '/tmp/text_gen_progress.json'

def log(msg):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {msg}"
    print(line)
    with open(LOG_FILE, 'a') as f:
        f.write(line + '\n')

def save_progress(progress):
    with open(PROGRESS_FILE, 'w') as f:
        json.dump(progress, f, indent=2)

async def generate_story_text(book_title: str, page_num: int, current_text: str, total_pages: int) -> str:
    """Generate expanded story text for a page"""
    
    chat = LlmChat(
        api_key=EMERGENT_KEY,
        session_id=f"story-gen-{book_title.replace(' ', '-')}-{page_num}",
        system_message="""You are a children's book author writing engaging stories for ages 5-10. 
Your writing style is warm, imaginative, and age-appropriate. 
You write in a narrative style that parents enjoy reading aloud.
Keep sentences varied in length but easy to follow.
Include sensory details and emotions to bring the story to life."""
    ).with_model("openai", "gpt-4o")
    
    prompt = f"""Expand this short placeholder text into a full paragraph for a children's picture book.

Book Title: "{book_title}"
Page: {page_num} of {total_pages}
Current short text: "{current_text}"

Requirements:
- Write exactly 100-150 words
- Maintain the same story point/scene as the original text
- Use simple vocabulary appropriate for ages 5-10
- Include sensory details (what characters see, hear, feel)
- Add character emotions and reactions
- Make it engaging for read-aloud
- DO NOT include any dialogue in quotation marks for page 1 (title pages)
- Keep the narrative flowing naturally

Write ONLY the expanded paragraph, nothing else."""

    user_message = UserMessage(text=prompt)
    response = await chat.send_message(user_message)
    return response.strip()

async def process_book(book_title: str, progress: dict):
    """Process a single book - expand all page texts"""
    
    book = db.books.find_one({"title": book_title})
    if not book:
        log(f"  Book not found: {book_title}")
        return False
    
    book_id = book.get('id')
    pages = book.get('pages', [])
    
    if not pages:
        log(f"  No pages found for: {book_title}")
        return False
    
    log(f"  Processing {len(pages)} pages...")
    
    updated_pages = []
    for i, page in enumerate(pages):
        page_num = i + 1
        current_text = page.get('text_content', page.get('text', ''))
        
        # Skip if already has long text (> 80 words)
        if current_text and len(current_text.split()) > 80:
            log(f"    Page {page_num}: Already has long text, skipping")
            updated_pages.append(page)
            continue
        
        log(f"    Page {page_num}: Generating expanded text...")
        
        try:
            new_text = await generate_story_text(book_title, page_num, current_text, len(pages))
            page['text_content'] = new_text
            log(f"    Page {page_num}: Generated {len(new_text.split())} words")
        except Exception as e:
            log(f"    Page {page_num}: ERROR - {e}")
            # Keep original text on error
        
        updated_pages.append(page)
        await asyncio.sleep(0.5)  # Rate limiting
    
    # Update database
    db.books.update_one(
        {"id": book_id},
        {"$set": {"pages": updated_pages, "updated_at": datetime.utcnow().isoformat()}}
    )
    
    return True

async def main():
    log("=" * 60)
    log("LONG-FORM TEXT GENERATION - 19 BOOKS")
    log("=" * 60)
    
    progress = {
        "started_at": datetime.now().isoformat(),
        "completed": 0,
        "failed": 0,
        "total": len(SHORT_TEXT_BOOKS),
        "done_list": [],
        "failed_list": []
    }
    save_progress(progress)
    
    for i, book_title in enumerate(SHORT_TEXT_BOOKS):
        log(f"\n[{i+1}/{len(SHORT_TEXT_BOOKS)}] {book_title}")
        log("-" * 40)
        
        try:
            success = await process_book(book_title, progress)
            if success:
                progress['completed'] += 1
                progress['done_list'].append(book_title)
                log(f"  ✅ SUCCESS")
            else:
                progress['failed'] += 1
                progress['failed_list'].append(book_title)
                log(f"  ❌ FAILED")
        except Exception as e:
            log(f"  ❌ ERROR: {e}")
            progress['failed'] += 1
            progress['failed_list'].append(book_title)
        
        save_progress(progress)
    
    log("\n" + "=" * 60)
    log("GENERATION COMPLETE!")
    log("=" * 60)
    log(f"Completed: {progress['completed']}/{progress['total']}")
    log(f"Failed: {progress['failed']}")
    
    if progress['failed_list']:
        log(f"\nFailed books: {', '.join(progress['failed_list'])}")

if __name__ == "__main__":
    asyncio.run(main())
