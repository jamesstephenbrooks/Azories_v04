#!/usr/bin/env python3
"""
Script to create sample books with quality content, images, and covers
for the Azories platform.
"""
import asyncio
import aiohttp
import json
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

API_URL = os.environ.get('API_URL', 'https://character-gen-11.preview.emergentagent.com')

# Sample book ideas for different genres
BOOK_IDEAS = [
    {
        "idea": "A curious young astronaut discovers a friendly alien civilization on a distant moon made of rainbow crystals",
        "genre": "Sci-Fi",
        "age_rating": "5+",
        "num_pages": 6,
        "image_style": "3d-render"
    },
    {
        "idea": "A shy forest fairy learns to make friends with woodland creatures and discovers her unique magical gift of talking to flowers",
        "genre": "Fantasy",
        "age_rating": "All Ages",
        "num_pages": 5,
        "image_style": "watercolor"
    },
    {
        "idea": "A young detective and her loyal robot dog solve the mystery of the missing golden cookies at the neighborhood bakery",
        "genre": "Mystery",
        "age_rating": "8+",
        "num_pages": 6,
        "image_style": "cartoon"
    },
    {
        "idea": "A brave little pirate captain and her crew of misfit animals search for the legendary treasure of Kindness Island",
        "genre": "Adventure",
        "age_rating": "5+",
        "num_pages": 6,
        "image_style": "illustration"
    },
    {
        "idea": "A young artist discovers that her paintings come to life at night, and she must help her painted friends find their way home",
        "genre": "Fantasy",
        "age_rating": "All Ages",
        "num_pages": 5,
        "image_style": "storybook"
    },
    {
        "idea": "A team of young superheroes with powers based on emotions learn that working together is more powerful than any single ability",
        "genre": "Adventure",
        "age_rating": "8+",
        "num_pages": 6,
        "image_style": "comic"
    }
]

async def login(session, email, password):
    """Login and get token"""
    async with session.post(
        f"{API_URL}/api/auth/login",
        json={"email": email, "password": password}
    ) as resp:
        data = await resp.json()
        return data.get('access_token')

async def add_credits(session, token, amount):
    """Add credits to account"""
    async with session.post(
        f"{API_URL}/api/credits/add?amount={amount}",
        headers={"Authorization": f"Bearer {token}"}
    ) as resp:
        data = await resp.json()
        return data.get('new_balance', 0)

async def generate_story(session, token, book_idea):
    """Generate a story from an idea"""
    async with session.post(
        f"{API_URL}/api/ai/generate-story",
        json={
            "idea": book_idea["idea"],
            "genre": book_idea["genre"],
            "age_rating": book_idea["age_rating"],
            "num_pages": book_idea["num_pages"],
            "generate_images": False,
            "media_type": "none",
            "image_style": book_idea["image_style"]
        },
        headers={"Authorization": f"Bearer {token}"}
    ) as resp:
        if resp.status == 200:
            return await resp.json()
        else:
            error = await resp.text()
            print(f"Error generating story: {error}")
            return None

async def generate_cover_image(session, token, title, genre, style):
    """Generate a cover image for a book"""
    prompt = f"Book cover illustration for '{title}', {genre} genre, {style} style, vibrant colors, eye-catching design, child-friendly, professional book cover art"
    
    async with session.post(
        f"{API_URL}/api/fal/generate",
        json={
            "prompt": prompt,
            "model": "flux-dev",
            "image_size": "portrait_16_9",
            "num_images": 1
        },
        headers={"Authorization": f"Bearer {token}"}
    ) as resp:
        if resp.status == 200:
            data = await resp.json()
            if data.get("images"):
                return data["images"][0].get("url")
        return None

async def generate_page_image(session, token, image_prompt, style):
    """Generate an image for a page"""
    full_prompt = f"{image_prompt}, {style} style, children's book illustration, vibrant and colorful"
    
    async with session.post(
        f"{API_URL}/api/fal/generate",
        json={
            "prompt": full_prompt,
            "model": "flux-dev",
            "image_size": "landscape_16_9",
            "num_images": 1
        },
        headers={"Authorization": f"Bearer {token}"}
    ) as resp:
        if resp.status == 200:
            data = await resp.json()
            if data.get("images"):
                return data["images"][0].get("url")
        return None

async def update_book(session, token, book_id, updates):
    """Update a book with cover image, etc."""
    async with session.put(
        f"{API_URL}/api/books/{book_id}",
        json=updates,
        headers={"Authorization": f"Bearer {token}"}
    ) as resp:
        return resp.status == 200

async def update_page(session, token, book_id, chapter_id, page_id, image_url):
    """Update a page with an image"""
    async with session.put(
        f"{API_URL}/api/books/{book_id}/chapters/{chapter_id}/pages/{page_id}",
        json={"image_url": image_url},
        headers={"Authorization": f"Bearer {token}"}
    ) as resp:
        return resp.status == 200

async def get_book_pages(session, token, book_id):
    """Get all pages for a book"""
    async with session.get(
        f"{API_URL}/api/books/{book_id}/full",
        headers={"Authorization": f"Bearer {token}"}
    ) as resp:
        if resp.status == 200:
            data = await resp.json()
            return data
        return None

async def publish_book(session, token, book_id):
    """Publish a book"""
    async with session.put(
        f"{API_URL}/api/books/{book_id}",
        json={"is_published": True},
        headers={"Authorization": f"Bearer {token}"}
    ) as resp:
        return resp.status == 200

async def create_sample_books():
    """Main function to create sample books"""
    print("=" * 60)
    print("Creating Sample Books for Azories")
    print("=" * 60)
    
    async with aiohttp.ClientSession() as session:
        # Login
        print("\n1. Logging in...")
        token = await login(session, "test@test.com", "test123")
        if not token:
            print("Failed to login!")
            return
        print("   Logged in successfully")
        
        # Add credits
        print("\n2. Adding credits...")
        balance = await add_credits(session, token, 1000)
        print(f"   Credit balance: {balance}")
        
        # Create books
        created_books = []
        for i, book_idea in enumerate(BOOK_IDEAS):
            print(f"\n{'-' * 40}")
            print(f"Creating Book {i+1}/{len(BOOK_IDEAS)}: {book_idea['genre']}")
            print(f"{'-' * 40}")
            
            # Generate story
            print("   Generating story...")
            story = await generate_story(session, token, book_idea)
            if not story or not story.get("success"):
                print(f"   Failed to generate story")
                continue
            
            book_id = story["book_id"]
            title = story["title"]
            print(f"   Title: {title}")
            print(f"   Book ID: {book_id}")
            print(f"   Pages: {story['pages_created']}")
            
            # Generate cover image
            print("   Generating cover image...")
            cover_url = await generate_cover_image(session, token, title, book_idea["genre"], book_idea["image_style"])
            if cover_url:
                await update_book(session, token, book_id, {"cover_image": cover_url})
                print("   Cover image generated!")
            else:
                print("   Warning: Could not generate cover image")
            
            # Get book pages for image generation
            print("   Getting book pages...")
            book_data = await get_book_pages(session, token, book_id)
            
            if book_data and book_data.get("chapters"):
                # Generate images for each page
                for chapter in book_data["chapters"]:
                    chapter_id = chapter["id"]
                    for page in chapter.get("pages", []):
                        page_id = page["id"]
                        # Use the stored image_prompt if available
                        image_prompt = page.get("image_prompt") or page.get("text_content", "")[:200]
                        
                        print(f"   Generating image for page {page.get('order', '?')}...")
                        page_image_url = await generate_page_image(session, token, image_prompt, book_idea["image_style"])
                        
                        if page_image_url:
                            await update_page(session, token, book_id, chapter_id, page_id, page_image_url)
                        
                        # Small delay to avoid rate limiting
                        await asyncio.sleep(1)
            
            # Publish the book
            print("   Publishing book...")
            await publish_book(session, token, book_id)
            
            created_books.append({
                "id": book_id,
                "title": title,
                "genre": book_idea["genre"]
            })
            
            print(f"   Book '{title}' created and published!")
            
            # Delay between books
            await asyncio.sleep(2)
        
        # Summary
        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)
        print(f"Created {len(created_books)} books:")
        for book in created_books:
            print(f"  - {book['title']} ({book['genre']})")
        print("\nAll books are published and ready to read!")

if __name__ == "__main__":
    asyncio.run(create_sample_books())
