#!/usr/bin/env python3
"""
Generate 50 children's books with covers and page content.
This script runs in phases:
1. Create book records with metadata
2. Generate cover images
3. Create chapters and pages with text
4. Generate page images (optional - takes longest)

Run with: python3 scripts/generate_50_books.py --phase 1
"""

import asyncio
import os
import sys
import json
import base64
import argparse
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import uuid

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))

# 50 Children's Book Definitions
CHILDREN_BOOKS = [
    # Fantasy (10 books)
    {"title": "The Dragon's Secret Garden", "genre": "Fantasy", "age_rating": "All Ages", "description": "A young girl discovers a hidden garden where a friendly dragon tends magical flowers."},
    {"title": "The Unicorn's Rainbow Bridge", "genre": "Fantasy", "age_rating": "All Ages", "description": "A unicorn helps children cross a magical rainbow bridge to dreamland."},
    {"title": "Princess Penny's Pet Dragon", "genre": "Fantasy", "age_rating": "4-6", "description": "A princess befriends a tiny dragon who causes adorable chaos in the castle."},
    {"title": "The Wizard's Apprentice", "genre": "Fantasy", "age_rating": "7-9", "description": "A young boy learns magic from a forgetful but kind wizard."},
    {"title": "Fairies of Moonlight Meadow", "genre": "Fantasy", "age_rating": "All Ages", "description": "Tiny fairies work together to save their meadow from a grumpy troll."},
    {"title": "The Mermaid's Lost Pearl", "genre": "Fantasy", "age_rating": "5+", "description": "A mermaid princess searches the ocean depths for her grandmother's pearl."},
    {"title": "Elves and the Magic Tree", "genre": "Fantasy", "age_rating": "All Ages", "description": "Forest elves protect a tree that grants wishes to kind-hearted children."},
    {"title": "The Giant's Gentle Heart", "genre": "Fantasy", "age_rating": "4-6", "description": "A misunderstood giant just wants to make friends with the village children."},
    {"title": "Pixie Dust Adventures", "genre": "Fantasy", "age_rating": "All Ages", "description": "A pixie shares her magical dust to help children believe in themselves."},
    {"title": "The Enchanted Carousel", "genre": "Fantasy", "age_rating": "5+", "description": "A carousel comes alive at midnight, taking children on magical adventures."},
    
    # Adventure (10 books)
    {"title": "Captain Compass and the Treasure Map", "genre": "Adventure", "age_rating": "7-9", "description": "A young pirate captain follows an ancient map to find friendship, not gold."},
    {"title": "The Jungle Explorers Club", "genre": "Adventure", "age_rating": "5+", "description": "Three friends explore a backyard jungle and discover amazing creatures."},
    {"title": "Mountain Climbing Mice", "genre": "Adventure", "age_rating": "All Ages", "description": "Brave mice climb the tallest mountain to see the sunrise."},
    {"title": "The Underground City", "genre": "Adventure", "age_rating": "8+", "description": "Children discover a hidden city beneath their school playground."},
    {"title": "Sky Pirates of Cloudland", "genre": "Adventure", "age_rating": "7-9", "description": "Flying ships and brave children protect the cloud kingdoms."},
    {"title": "Safari Sam's Big Day", "genre": "Adventure", "age_rating": "4-6", "description": "A young photographer goes on his first safari adventure."},
    {"title": "The Lighthouse Keeper's Secret", "genre": "Adventure", "age_rating": "5+", "description": "A girl discovers her grandfather's lighthouse hides a wonderful secret."},
    {"title": "Desert Treasure Hunt", "genre": "Adventure", "age_rating": "7-9", "description": "Siblings search for ancient treasure in the sandy dunes."},
    {"title": "River Rafting Raccoons", "genre": "Adventure", "age_rating": "All Ages", "description": "Raccoon friends build a raft and explore down the river."},
    {"title": "The Arctic Expedition", "genre": "Adventure", "age_rating": "8+", "description": "Young scientists travel to the Arctic to study polar bears."},
    
    # Science Fiction (8 books)
    {"title": "Robot Best Friend", "genre": "Science Fiction", "age_rating": "5+", "description": "A girl builds a robot that becomes her best companion."},
    {"title": "Aliens at My School", "genre": "Science Fiction", "age_rating": "7-9", "description": "A new student turns out to be from another planet!"},
    {"title": "Journey to Planet Sparkle", "genre": "Science Fiction", "age_rating": "All Ages", "description": "A rocket ship takes children to a planet made of crystals."},
    {"title": "The Time Machine Treehouse", "genre": "Science Fiction", "age_rating": "8+", "description": "A treehouse that travels through time teaches history lessons."},
    {"title": "Space Station School", "genre": "Science Fiction", "age_rating": "5+", "description": "What's it like to go to school floating in space?"},
    {"title": "The Friendly Martians", "genre": "Science Fiction", "age_rating": "All Ages", "description": "Green Martians visit Earth and learn about human customs."},
    {"title": "Gadget Girl and the Invention Fair", "genre": "Science Fiction", "age_rating": "7-9", "description": "A young inventor creates a machine that solves everyone's problems."},
    {"title": "Astronaut Alex's Moon Mission", "genre": "Science Fiction", "age_rating": "4-6", "description": "A brave young astronaut plants the first flower on the moon."},
    
    # Mystery (7 books)
    {"title": "The Case of the Missing Cookies", "genre": "Mystery", "age_rating": "All Ages", "description": "Two kid detectives solve the mystery of the school cafeteria."},
    {"title": "Mystery at the Zoo", "genre": "Mystery", "age_rating": "7-9", "description": "Animals keep disappearing, but where do they go?"},
    {"title": "The Secret Code Club", "genre": "Mystery", "age_rating": "8+", "description": "Friends decode secret messages to find hidden treasure."},
    {"title": "Detective Daisy's First Case", "genre": "Mystery", "age_rating": "5+", "description": "A girl with a magnifying glass solves neighborhood mysteries."},
    {"title": "The Haunted Library Book", "genre": "Mystery", "age_rating": "7-9", "description": "A spooky library book leads to a not-so-scary ghost."},
    {"title": "Puzzle Palace Adventures", "genre": "Mystery", "age_rating": "8+", "description": "A palace filled with puzzles tests young minds."},
    {"title": "The Missing Birthday Present", "genre": "Mystery", "age_rating": "All Ages", "description": "Who took the birthday present? Follow the clues!"},
    
    # Humor (7 books)
    {"title": "Super Silly Superhero", "genre": "Humour", "age_rating": "All Ages", "description": "A superhero whose powers always go hilariously wrong."},
    {"title": "The Burping Dragon", "genre": "Humour", "age_rating": "4-6", "description": "A dragon who can only burp instead of breathe fire."},
    {"title": "Grandma's Wacky Inventions", "genre": "Humour", "age_rating": "5+", "description": "Grandma builds the silliest machines imaginable."},
    {"title": "The Backwards Day", "genre": "Humour", "age_rating": "All Ages", "description": "Everything happens backwards in this topsy-turvy tale!"},
    {"title": "Pirate Pete's Bad Hair Day", "genre": "Humour", "age_rating": "4-6", "description": "A pirate tries everything to fix his crazy hair."},
    {"title": "The Monster Who Was Scared of Kids", "genre": "Humour", "age_rating": "All Ages", "description": "A monster under the bed is actually terrified of children!"},
    {"title": "Dinosaur Dentist", "genre": "Humour", "age_rating": "5+", "description": "A T-Rex tries to brush all 60 of his teeth!"},
    
    # Educational/General (8 books)
    {"title": "Colors of the World", "genre": "General", "age_rating": "All Ages", "description": "A magical girl brings color to a gray world."},
    {"title": "Numbers Come Alive", "genre": "General", "age_rating": "4-6", "description": "Numbers become friends who teach counting through play."},
    {"title": "The Alphabet Zoo", "genre": "General", "age_rating": "All Ages", "description": "Animals teach the alphabet from A to Z."},
    {"title": "Seasons of the Magic Forest", "genre": "General", "age_rating": "5+", "description": "A forest changes through all four seasons."},
    {"title": "Kindness Kingdom", "genre": "General", "age_rating": "All Ages", "description": "A kingdom where kindness is the most powerful magic."},
    {"title": "Shapes in the City", "genre": "General", "age_rating": "4-6", "description": "Discover shapes hiding everywhere in the city."},
    {"title": "The Feelings Garden", "genre": "General", "age_rating": "All Ages", "description": "Flowers represent different emotions children can learn about."},
    {"title": "Bedtime in the Animal World", "genre": "General", "age_rating": "All Ages", "description": "How do different animals say goodnight?"},
]

# Cover art prompts for image generation
def get_cover_prompt(book):
    title = book["title"]
    genre = book["genre"]
    desc = book["description"]
    
    base_prompt = f"Children's book cover illustration, {desc.lower()}"
    
    style_by_genre = {
        "Fantasy": "magical, enchanted, whimsical watercolor style, glowing elements, dreamy atmosphere",
        "Adventure": "exciting, dynamic, bold colors, action-packed, adventurous mood",
        "Science Fiction": "futuristic, space theme, colorful sci-fi, friendly robots and aliens, cosmic wonder",
        "Mystery": "mysterious, playful detective theme, clues and magnifying glasses, intriguing atmosphere",
        "Humour": "funny, cartoon style, exaggerated expressions, bright cheerful colors, silly and playful",
        "General": "warm, educational, friendly characters, soft colors, welcoming and inclusive"
    }
    
    style = style_by_genre.get(genre, "colorful, child-friendly illustration")
    return f"{base_prompt}, {style}, professional children's book art, vertical portrait orientation"

async def generate_cover_image(prompt, api_key):
    """Generate a cover image using AI"""
    try:
        from emergentintegrations.llm.openai.image_generation import OpenAIImageGeneration
        
        if not api_key:
            print("  [SKIP] No API key")
            return None
        
        image_gen = OpenAIImageGeneration(api_key=api_key)
        images = await image_gen.generate_images(
            prompt=prompt,
            model="gpt-image-1",
            number_of_images=1,
            quality="medium"
        )
        
        if images and len(images) > 0:
            image_base64 = base64.b64encode(images[0]).decode('utf-8')
            return f"data:image/png;base64,{image_base64}"
        return None
    except Exception as e:
        print(f"  [ERROR] Image generation failed: {e}")
        return None

async def phase1_create_books(db):
    """Phase 1: Create book records"""
    print("\n" + "="*60)
    print("PHASE 1: Creating Book Records")
    print("="*60)
    
    # Get existing book titles to avoid duplicates
    existing = await db.books.find({}, {"title": 1}).to_list(100)
    existing_titles = {b["title"] for b in existing}
    
    created = 0
    for book_data in CHILDREN_BOOKS:
        if book_data["title"] in existing_titles:
            print(f"  [SKIP] '{book_data['title']}' already exists")
            continue
        
        book = {
            "id": str(uuid.uuid4()),
            "title": book_data["title"],
            "description": book_data["description"],
            "genre": book_data["genre"],
            "age_rating": book_data["age_rating"],
            "author_id": "system",
            "author_name": "Azories Publishing",
            "is_published": True,
            "cover_image": "",
            "chapters": [],
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "read_count": 0,
            "is_library_book": True
        }
        
        await db.books.insert_one(book)
        print(f"  [CREATED] {book_data['title']}")
        created += 1
    
    print(f"\nPhase 1 Complete: Created {created} books")
    return created

async def phase2_generate_covers(db, api_key, limit=5):
    """Phase 2: Generate cover images"""
    print("\n" + "="*60)
    print(f"PHASE 2: Generating Cover Images (limit: {limit})")
    print("="*60)
    
    # Get books without covers
    books = await db.books.find(
        {"$or": [{"cover_image": ""}, {"cover_image": None}]},
        {"_id": 0, "id": 1, "title": 1, "genre": 1, "description": 1}
    ).limit(limit).to_list(limit)
    
    if not books:
        print("All books have covers!")
        return 0
    
    print(f"Found {len(books)} books needing covers")
    
    generated = 0
    for i, book in enumerate(books):
        print(f"\n[{i+1}/{len(books)}] Generating cover for: {book['title']}")
        
        book_data = next((b for b in CHILDREN_BOOKS if b["title"] == book["title"]), None)
        if not book_data:
            book_data = {"title": book["title"], "genre": book.get("genre", "General"), "description": book.get("description", book["title"])}
        
        prompt = get_cover_prompt(book_data)
        print(f"  Prompt: {prompt[:80]}...")
        
        cover_image = await generate_cover_image(prompt, api_key)
        
        if cover_image:
            await db.books.update_one(
                {"id": book["id"]},
                {"$set": {"cover_image": cover_image, "updated_at": datetime.now(timezone.utc).isoformat()}}
            )
            print(f"  [SUCCESS] Cover generated!")
            generated += 1
        else:
            print(f"  [FAILED] Could not generate cover")
        
        # Brief pause between generations
        await asyncio.sleep(1)
    
    print(f"\nPhase 2 Complete: Generated {generated} covers")
    return generated

async def main():
    parser = argparse.ArgumentParser(description='Generate 50 children\'s books')
    parser.add_argument('--phase', type=int, choices=[1, 2], required=True, 
                       help='Phase to run: 1=Create books, 2=Generate covers')
    parser.add_argument('--limit', type=int, default=5, 
                       help='Number of covers to generate in phase 2 (default: 5)')
    args = parser.parse_args()
    
    mongo_url = os.environ.get('MONGO_URL')
    db_name = os.environ.get('DB_NAME')
    api_key = os.environ.get('EMERGENT_LLM_KEY')
    
    if not mongo_url or not db_name:
        print("ERROR: MONGO_URL and DB_NAME required")
        return
    
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    if args.phase == 1:
        await phase1_create_books(db)
    elif args.phase == 2:
        if not api_key:
            print("ERROR: EMERGENT_LLM_KEY required for image generation")
            return
        await phase2_generate_covers(db, api_key, args.limit)

if __name__ == "__main__":
    asyncio.run(main())
