#!/usr/bin/env python3
"""
Script to add images to pages of existing books
"""
import asyncio
import aiohttp
import json

API_URL = 'https://book-content-update.preview.emergentagent.com'

# List of book IDs to update with images
BOOK_IDS = [
    "e407351d-6474-4917-935f-df4c009de967",  # Luna's Rainbow Adventure
    "a0b23e67-5b1a-4ec7-9098-9c7a2aa397be",  # Lila and the Whispering Blossoms
    "d3d3c5b2-9052-4b17-84f8-95ddd0d27f4d",  # The Great Golden Cookie Caper
    "94a0503a-e3bc-4c10-abfb-f5182dba9725",  # Captain Clara and the Kindness Quest
    "cb1254c5-63fa-479d-9b29-db771ddde5ba",  # The Midnight Brush
    "2844ed0e-1440-4be6-b7a8-8b48046ea96c",  # The Emotion Squad
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

async def get_book_full(session, token, book_id):
    """Get full book with pages"""
    async with session.get(
        f"{API_URL}/api/books/{book_id}/full",
        headers={"Authorization": f"Bearer {token}"}
    ) as resp:
        if resp.status == 200:
            return await resp.json()
        return None

async def generate_page_image(session, token, image_prompt, style="illustration"):
    """Generate an image for a page"""
    full_prompt = f"{image_prompt}, {style} style, children's book illustration, vibrant and colorful, high quality"
    
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
        else:
            error = await resp.text()
            print(f"   Error generating image: {error[:100]}")
        return None

async def update_page_image(session, token, page_id, image_url):
    """Update a page with an image using the correct endpoint"""
    async with session.put(
        f"{API_URL}/api/pages/{page_id}",
        json={"image_url": image_url},
        headers={"Authorization": f"Bearer {token}"}
    ) as resp:
        if resp.status == 200:
            return True
        else:
            error = await resp.text()
            print(f"   Error updating page: {error[:100]}")
        return False

async def add_images_to_books():
    """Add images to all book pages"""
    print("=" * 60)
    print("Adding Images to Book Pages")
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
        balance = await add_credits(session, token, 500)
        print(f"   Credit balance: {balance}")
        
        # Process each book
        for book_id in BOOK_IDS:
            print(f"\n{'-' * 40}")
            print(f"Processing Book: {book_id[:8]}...")
            print(f"{'-' * 40}")
            
            # Get book details
            book = await get_book_full(session, token, book_id)
            if not book:
                print("   Book not found, skipping...")
                continue
            
            print(f"   Title: {book.get('title')}")
            
            # Get genre for style
            genre = book.get('genre', 'Fantasy').lower()
            if 'sci' in genre:
                style = "3d render, futuristic"
            elif 'mystery' in genre:
                style = "cartoon, detective"
            elif 'adventure' in genre:
                style = "colorful illustration"
            else:
                style = "watercolor illustration"
            
            # Process pages
            for chapter in book.get('chapters', []):
                for page in chapter.get('pages', []):
                    page_id = page['id']
                    page_order = page.get('order', 0)
                    existing_image = page.get('image_url')
                    
                    if existing_image:
                        print(f"   Page {page_order}: Already has image, skipping")
                        continue
                    
                    # Use stored image_prompt or text content
                    image_prompt = page.get('image_prompt') or page.get('text_content', '')[:300]
                    
                    if not image_prompt:
                        print(f"   Page {page_order}: No prompt available, skipping")
                        continue
                    
                    print(f"   Page {page_order}: Generating image...")
                    image_url = await generate_page_image(session, token, image_prompt, style)
                    
                    if image_url:
                        success = await update_page_image(session, token, page_id, image_url)
                        if success:
                            print(f"   Page {page_order}: Image added!")
                        else:
                            print(f"   Page {page_order}: Failed to update")
                    else:
                        print(f"   Page {page_order}: Failed to generate image")
                    
                    # Delay to avoid rate limiting
                    await asyncio.sleep(1)
            
            print(f"   Book '{book.get('title')}' updated!")
        
        print("\n" + "=" * 60)
        print("COMPLETE - All book pages have been updated with images!")
        print("=" * 60)

if __name__ == "__main__":
    asyncio.run(add_images_to_books())
