#!/usr/bin/env python3
"""
Generate story content for empty books - processes one book at a time
"""

import asyncio
import os
import uuid
import re
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from emergentintegrations.llm.chat import LlmChat, UserMessage

load_dotenv('/app/backend/.env')

EMPTY_BOOKS = [
    {"id": "730f7b9b-d2bb-47f4-a797-1337bc0d6980", "title": "The Jungle Explorers Club", "genre": "Adventure", "age": "5+"},
    {"id": "f6e35965-f823-4ed5-8b96-658a832daedd", "title": "Mountain Climbing Mice", "genre": "Adventure", "age": "All Ages"},
    {"id": "10b82c6e-6ccb-4466-a97a-ed0fa997196e", "title": "Space Station School", "genre": "Science Fiction", "age": "5+"},
    {"id": "d76924a2-eb27-4f7f-b9ae-5a7f9c922dad", "title": "The Friendly Martians", "genre": "Science Fiction", "age": "All Ages"},
    {"id": "967761b8-0efe-4b06-b80b-56102fe02255", "title": "Gadget Girl and the Invention Fair", "genre": "Science Fiction", "age": "7-9"},
    {"id": "bc4794ea-f46f-4e15-8d13-4f64ad413f93", "title": "The Secret Code Club", "genre": "Mystery", "age": "8+"},
    {"id": "4603101f-bfff-4254-ac0a-8c80a6bcd11f", "title": "Detective Daisy's First Case", "genre": "Mystery", "age": "5+"},
    {"id": "cf359d5f-473d-44de-8b7b-db2ccaba95a1", "title": "The Backwards Day", "genre": "Humour", "age": "All Ages"},
    {"id": "02f5b64a-4eed-4c69-8f48-f2e7b11e4c6a", "title": "Pirate Pete's Bad Hair Day", "genre": "Humour", "age": "4-6"},
    {"id": "d7bf28c1-dbe9-4579-8d83-2faa0ed1ad8f", "title": "Dinosaur Dentist", "genre": "Humour", "age": "5+"},
    {"id": "5826db64-5029-4729-9eed-8da4fae959d3", "title": "Kindness Kingdom", "genre": "General", "age": "All Ages"},
]

def parse_pages(response):
    """Parse AI response into pages"""
    pages = []
    # Match PAGE N: followed by content
    pattern = r'(?:\*\*)?PAGE\s*(\d+)(?:\*\*)?[:\s]*\n?(.*?)(?=(?:\*\*)?PAGE\s*\d+|$)'
    matches = re.findall(pattern, response, re.DOTALL | re.IGNORECASE)
    
    for num, text in matches:
        cleaned = text.strip().replace('**', '').strip()
        if cleaned:
            pages.append(cleaned)
    
    return pages

async def generate_and_save(db, book, index, total):
    """Generate content for one book and save it"""
    api_key = os.environ.get('EMERGENT_LLM_KEY')
    
    print(f"[{index}/{total}] {book['title']}...", end=" ", flush=True)
    
    chat = LlmChat(
        api_key=api_key,
        session_id=f"gen-{book['id'][:8]}",
        system_message="You are a children's book author. Write engaging, imaginative stories."
    ).with_model("openai", "gpt-4o")
    
    prompt = f"""Write a 10-page children's story: "{book['title']}" ({book['genre']}, ages {book['age']}).
Each page: 100-150 words. Format exactly as:
PAGE 1:
[text]

PAGE 2:
[text]
...through PAGE 10 (end with THE END)"""

    message = UserMessage(text=prompt)
    response = await chat.send_message(message)
    
    pages = parse_pages(response)
    
    if len(pages) < 10:
        print(f"⚠️ Only {len(pages)} pages")
        return 0
    
    # Save to DB
    pages = pages[:10]
    embedded = []
    
    for i, text in enumerate(pages, 1):
        page_id = str(uuid.uuid4())
        await db.pages.insert_one({
            'id': page_id,
            'book_id': book['id'],
            'page_number': i,
            'text_content': text,
            'image_url': None,
            'audio_url': None,
            'created_at': datetime.now(timezone.utc).isoformat(),
            'updated_at': datetime.now(timezone.utc).isoformat()
        })
        embedded.append({
            'id': page_id,
            'page_number': i,
            'text_content': text,
            'image_url': None,
            'audio_url': None
        })
    
    await db.books.update_one({'id': book['id']}, {'$set': {'pages': embedded}})
    print(f"✅ 10 pages")
    return 10

async def main():
    client = AsyncIOMotorClient(os.environ.get('MONGO_URL'))
    db = client[os.environ.get('DB_NAME', 'test_database')]
    
    # Check which books still need content
    books_to_process = []
    for book in EMPTY_BOOKS:
        count = await db.pages.count_documents({'book_id': book['id']})
        if count == 0:
            books_to_process.append(book)
    
    print(f"Books needing content: {len(books_to_process)}")
    
    total = 0
    for i, book in enumerate(books_to_process, 1):
        try:
            pages = await generate_and_save(db, book, i, len(books_to_process))
            total += pages
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print(f"\nTotal pages generated: {total}")
    client.close()

if __name__ == "__main__":
    asyncio.run(main())
