#!/usr/bin/env python3
"""
Generate story content for empty books using OpenAI via Emergent LLM key
"""

import asyncio
import os
import uuid
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv('/app/backend/.env')

# Import emergent integrations
from emergentintegrations.llm.chat import LlmChat, UserMessage

# Books that need content
EMPTY_BOOKS = [
    {
        "id": "730f7b9b-d2bb-47f4-a797-1337bc0d6980",
        "title": "The Jungle Explorers Club",
        "genre": "Adventure",
        "age": "5+"
    },
    {
        "id": "f6e35965-f823-4ed5-8b96-658a832daedd",
        "title": "Mountain Climbing Mice",
        "genre": "Adventure",
        "age": "All Ages"
    },
    {
        "id": "10b82c6e-6ccb-4466-a97a-ed0fa997196e",
        "title": "Space Station School",
        "genre": "Science Fiction",
        "age": "5+"
    },
    {
        "id": "d76924a2-eb27-4f7f-b9ae-5a7f9c922dad",
        "title": "The Friendly Martians",
        "genre": "Science Fiction",
        "age": "All Ages"
    },
    {
        "id": "967761b8-0efe-4b06-b80b-56102fe02255",
        "title": "Gadget Girl and the Invention Fair",
        "genre": "Science Fiction",
        "age": "7-9"
    },
    {
        "id": "bc4794ea-f46f-4e15-8d13-4f64ad413f93",
        "title": "The Secret Code Club",
        "genre": "Mystery",
        "age": "8+"
    },
    {
        "id": "4603101f-bfff-4254-ac0a-8c80a6bcd11f",
        "title": "Detective Daisy's First Case",
        "genre": "Mystery",
        "age": "5+"
    },
    {
        "id": "cf359d5f-473d-44de-8b7b-db2ccaba95a1",
        "title": "The Backwards Day",
        "genre": "Humour",
        "age": "All Ages"
    },
    {
        "id": "02f5b64a-4eed-4c69-8f48-f2e7b11e4c6a",
        "title": "Pirate Pete's Bad Hair Day",
        "genre": "Humour",
        "age": "4-6"
    },
    {
        "id": "d7bf28c1-dbe9-4579-8d83-2faa0ed1ad8f",
        "title": "Dinosaur Dentist",
        "genre": "Humour",
        "age": "5+"
    },
    {
        "id": "5826db64-5029-4729-9eed-8da4fae959d3",
        "title": "Kindness Kingdom",
        "genre": "General",
        "age": "All Ages"
    }
]

async def generate_story(book_info):
    """Generate a 10-page story for a book"""
    api_key = os.environ.get('EMERGENT_LLM_KEY')
    
    chat = LlmChat(
        api_key=api_key,
        session_id=f"story-gen-{book_info['id']}",
        system_message="""You are a professional children's book author. Write engaging, age-appropriate stories with:
- Rich, descriptive language that paints vivid pictures
- Clear narrative arc with beginning, middle, and end
- Relatable characters with distinct personalities
- Gentle lessons woven naturally into the story
- Each page should be a substantial paragraph (150-250 words)
- Write in a warm, engaging tone that captures young readers' attention"""
    ).with_model("openai", "gpt-4o")
    
    prompt = f"""Write a complete children's story titled "{book_info['title']}" for the {book_info['genre']} genre, suitable for ages {book_info['age']}.

The story should have exactly 10 pages. For each page, write a substantial paragraph (150-250 words) that advances the narrative.

Format your response EXACTLY like this:
PAGE 1:
[First page text here]

PAGE 2:
[Second page text here]

...continue for all 10 pages...

PAGE 10:
[Final page text with satisfying conclusion, ending with "THE END"]

Make the story engaging, imaginative, and appropriate for the target age group. Include vivid descriptions that would pair well with illustrations."""

    message = UserMessage(text=prompt)
    response = await chat.send_message(message)
    
    return response

def parse_story_response(response_text):
    """Parse the AI response into individual pages"""
    pages = []
    
    # Split by PAGE markers
    parts = response_text.split("PAGE ")
    
    for part in parts[1:]:  # Skip the first empty part
        # Extract page number and text
        lines = part.strip().split("\n", 1)
        if len(lines) >= 2:
            page_text = lines[1].strip()
            # Clean up the text
            page_text = page_text.replace("**", "").strip()
            if page_text:
                pages.append(page_text)
    
    return pages

async def save_book_content(db, book_id, pages):
    """Save generated pages to database"""
    embedded_pages = []
    
    for i, text in enumerate(pages, 1):
        page_id = str(uuid.uuid4())
        
        # Create page in pages collection
        new_page = {
            'id': page_id,
            'book_id': book_id,
            'page_number': i,
            'text_content': text,
            'image_url': None,
            'audio_url': None,
            'created_at': datetime.now(timezone.utc).isoformat(),
            'updated_at': datetime.now(timezone.utc).isoformat()
        }
        await db.pages.insert_one(new_page)
        
        # Also add to embedded pages
        embedded_pages.append({
            'id': page_id,
            'page_number': i,
            'text_content': text,
            'image_url': None,
            'audio_url': None
        })
    
    # Update book with embedded pages
    await db.books.update_one(
        {'id': book_id},
        {'$set': {'pages': embedded_pages}}
    )
    
    return len(pages)

async def main():
    client = AsyncIOMotorClient(os.environ.get('MONGO_URL'))
    db = client[os.environ.get('DB_NAME', 'test_database')]
    
    print("=" * 60)
    print(" Generating Story Content for Empty Books")
    print("=" * 60)
    
    total_pages = 0
    
    for i, book in enumerate(EMPTY_BOOKS, 1):
        print(f"\n[{i}/{len(EMPTY_BOOKS)}] Generating: {book['title']}...")
        
        try:
            # Generate story
            response = await generate_story(book)
            
            # Parse into pages
            pages = parse_story_response(response)
            
            if len(pages) < 10:
                print(f"  ⚠️ Only got {len(pages)} pages, padding...")
                # If we didn't get enough pages, the last page might have continuation
                while len(pages) < 10:
                    pages.append(f"[Page {len(pages)+1} content to be added]")
            
            # Truncate to 10 pages
            pages = pages[:10]
            
            # Save to database
            saved = await save_book_content(db, book['id'], pages)
            total_pages += saved
            
            print(f"  ✅ Saved {saved} pages")
            
        except Exception as e:
            print(f"  ❌ Error: {e}")
    
    print("\n" + "=" * 60)
    print(f" Complete! Generated {total_pages} pages for {len(EMPTY_BOOKS)} books")
    print("=" * 60)
    
    client.close()

if __name__ == "__main__":
    asyncio.run(main())
