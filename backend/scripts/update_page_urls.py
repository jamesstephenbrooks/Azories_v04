#!/usr/bin/env python3
"""
Update all page image URLs in the database via API
Uses the new admin/books/{book_id}/bulk-page-images endpoint
"""

import os
import sys
import json
import requests
from datetime import datetime

API_URL = "https://kids-mode-demo.preview.emergentagent.com"

# 25 books that had pages regenerated
BOOKS = [
    ("5ebe3908-18f9-4947-b049-7248c2700fa4", "The Unicorn's Rainbow Bridge", "the_unicorns_rainbow_bridge"),
    ("67b40688-b6cb-431b-a0c6-8baa1c28542c", "The Wizard's Apprentice", "the_wizards_apprentice"),
    ("51c242bc-99a4-4456-b4dc-1821c2a75138", "The Giant's Gentle Heart", "the_giants_gentle_heart"),
    ("56c45425-ba3b-421d-b17f-f13321c32f65", "Pixie Dust Adventures", "pixie_dust_adventures"),
    ("efdc724b-18b0-4901-a22f-e211836d76c2", "The Enchanted Carousel", "the_enchanted_carousel"),
    ("ed34dc96-9c78-4eb7-8707-90245371bea4", "Captain Compass and the Treasure Map", "captain_compass_and_the_treasure_map"),
    ("730f7b9b-d2bb-47f4-a797-1337bc0d6980", "The Jungle Explorers Club", "the_jungle_explorers_club"),
    ("f6e35965-f823-4ed5-8b96-658a832daedd", "Mountain Climbing Mice", "mountain_climbing_mice"),
    ("61dced03-0e50-4d76-826a-640b9ffa0f19", "The Underground City", "the_underground_city"),
    ("af46591e-445e-4190-9e02-b68e895c6403", "Sky Pirates of Cloudland", "sky_pirates_of_cloudland"),
    ("f10ecfac-d2e8-4725-b28e-fee429e5c8ab", "The Lighthouse Keeper's Secret", "the_lighthouse_keepers_secret"),
    ("875cb08c-5634-4304-ae34-07fb0c446afe", "The Arctic Expedition", "the_arctic_expedition"),
    ("134d15cb-7824-4e33-a5d8-31f81e8b185f", "The Time Machine Treehouse", "the_time_machine_treehouse"),
    ("10b82c6e-6ccb-4466-a97a-ed0fa997196e", "Space Station School", "space_station_school"),
    ("d76924a2-eb27-4f7f-b9ae-5a7f9c922dad", "The Friendly Martians", "the_friendly_martians"),
    ("967761b8-0efe-4b06-b80b-56102fe02255", "Gadget Girl and the Invention Fair", "gadget_girl_and_the_invention_fair"),
    ("bc4794ea-f46f-4e15-8d13-4f64ad413f93", "The Secret Code Club", "the_secret_code_club"),
    ("4603101f-bfff-4254-ac0a-8c80a6bcd11f", "Detective Daisy's First Case", "detective_daisys_first_case"),
    ("b5cf1707-7930-4e72-a01c-8d21d052b693", "The Burping Dragon", "the_burping_dragon"),
    ("cf359d5f-473d-44de-8b7b-db2ccaba95a1", "The Backwards Day", "the_backwards_day"),
    ("02f5b64a-4eed-4c69-8f48-f2e7b11e4c6a", "Pirate Pete's Bad Hair Day", "pirate_petes_bad_hair_day"),
    ("d7bf28c1-dbe9-4579-8d83-2faa0ed1ad8f", "Dinosaur Dentist", "dinosaur_dentist"),
    ("1eb994a4-e00c-4ac6-a47f-d22544493608", "The Alphabet Zoo", "the_alphabet_zoo"),
    ("5826db64-5029-4729-9eed-8da4fae959d3", "Kindness Kingdom", "kindness_kingdom"),
    ("40fde406-1757-4185-ab62-eb97264784e9", "The Feelings Garden", "the_feelings_garden"),
]

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")
    sys.stdout.flush()

def get_token():
    resp = requests.post(f"{API_URL}/api/auth/login", json={
        "email": "jamesstephenbrooks@outlook.com",
        "password": "test123"
    })
    return resp.json().get('access_token')

def get_book_page_count(book_id, token):
    """Get the number of pages in a book"""
    resp = requests.get(
        f"{API_URL}/api/books/{book_id}/full",
        headers={"Authorization": f"Bearer {token}"}
    )
    data = resp.json()
    chapters = data.get('chapters', [])
    pages = data.get('pages', [])
    
    if chapters and chapters[0].get('pages'):
        return len(chapters[0]['pages']), 'chapters'
    elif pages:
        return len(pages), 'pages'
    return 0, None

def main():
    log("="*60)
    log("UPDATING PAGE IMAGE URLs VIA API")
    log("="*60)
    
    token = get_token()
    total_updated = 0
    total_failed = 0
    
    for book_id, title, slug in BOOKS:
        log(f"\n{title}")
        
        # Get page count
        page_count, source = get_book_page_count(book_id, token)
        if not source:
            log(f"  ERROR: Could not determine page source")
            total_failed += 1
            continue
        
        log(f"  Pages: {page_count}, Source: {source}")
        
        # Build updates for all pages
        updates = []
        for i in range(page_count):
            new_url = f"https://res.cloudinary.com/dlbmjqmoy/image/upload/azories/books/{slug}/page_{i+1:02d}_v2.jpg"
            updates.append({
                "page_index": i,
                "image_url": new_url,
                "chapter_index": 0,
                "source": source
            })
        
        # Call bulk update API for BOTH sources
        # First update pages array
        resp_pages = requests.put(
            f"{API_URL}/api/admin/books/{book_id}/bulk-page-images",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            },
            json=[{**u, "source": "pages"} for u in updates]
        )
        
        # Then update chapters array
        resp_chapters = requests.put(
            f"{API_URL}/api/admin/books/{book_id}/bulk-page-images",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            },
            json=[{**u, "source": "chapters"} for u in updates]
        )
        
        pages_count = 0
        chapters_count = 0
        
        if resp_pages.status_code == 200:
            pages_count = resp_pages.json().get('updated_count', 0)
        if resp_chapters.status_code == 200:
            chapters_count = resp_chapters.json().get('updated_count', 0)
        
        log(f"  Updated: pages={pages_count}, chapters={chapters_count}")
        total_updated += max(pages_count, chapters_count)
    
    log(f"\n{'='*60}")
    log(f"UPDATE COMPLETE")
    log(f"  Total pages updated: {total_updated}")
    log(f"  Books with errors: {total_failed}")
    log(f"{'='*60}")

if __name__ == "__main__":
    main()
