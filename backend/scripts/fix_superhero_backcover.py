#!/usr/bin/env python3
"""
Fix the back cover summary for Super Silly Superhero
"""
import os
import sys
sys.path.insert(0, '/app/backend')

from pymongo import MongoClient
from PIL import Image, ImageDraw, ImageFont
import requests
from io import BytesIO
import cloudinary
import cloudinary.uploader

# Configure Cloudinary
cloudinary.config(
    cloud_name="dlbmjqmoy",
    api_key=os.environ.get("CLOUDINARY_API_KEY", ""),
    api_secret=os.environ.get("CLOUDINARY_API_SECRET", ""),
    secure=True
)

# MongoDB connection
MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "test_database")
client = MongoClient(MONGO_URL)
db = client[DB_NAME]

def create_back_cover(book_id, title, summary, author="Young Author"):
    """Create a professional back cover image"""
    
    # Design dimensions (portrait aspect ratio)
    width, height = 800, 1200
    
    # Colors
    bg_gradient_start = (26, 10, 46)  # Deep purple
    bg_gradient_end = (45, 20, 80)    # Lighter purple
    
    # Create image with gradient
    img = Image.new('RGB', (width, height), bg_gradient_start)
    
    # Add gradient effect
    for y in range(height):
        ratio = y / height
        r = int(bg_gradient_start[0] + (bg_gradient_end[0] - bg_gradient_start[0]) * ratio)
        g = int(bg_gradient_start[1] + (bg_gradient_end[1] - bg_gradient_start[1]) * ratio)
        b = int(bg_gradient_start[2] + (bg_gradient_end[2] - bg_gradient_start[2]) * ratio)
        for x in range(width):
            img.putpixel((x, y), (r, g, b))
    
    draw = ImageDraw.Draw(img)
    
    # Load Azora mascot
    azora_url = "https://res.cloudinary.com/dlbmjqmoy/image/upload/v1772278966/azories/mascot/azora_with_dragon_transparent.png"
    try:
        response = requests.get(azora_url)
        azora_img = Image.open(BytesIO(response.content)).convert("RGBA")
        # Resize Azora
        azora_size = (300, 300)
        azora_img = azora_img.resize(azora_size, Image.Resampling.LANCZOS)
        # Position at bottom right
        azora_x = width - azora_size[0] - 30
        azora_y = height - azora_size[1] - 50
        img.paste(azora_img, (azora_x, azora_y), azora_img)
    except Exception as e:
        print(f"Could not load Azora: {e}")
    
    # Try to load fonts
    try:
        title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 42)
        summary_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
        brand_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 32)
        tagline_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Oblique.ttf", 18)
    except:
        title_font = ImageFont.load_default()
        summary_font = ImageFont.load_default()
        brand_font = ImageFont.load_default()
        tagline_font = ImageFont.load_default()
    
    # Draw decorative elements - stars
    star_color = (255, 215, 0, 180)  # Gold
    for pos in [(50, 100), (750, 150), (100, 900), (700, 850)]:
        draw.text(pos, "✦", fill=star_color[:3], font=summary_font)
    
    # Draw Azories logo/brand at top
    draw.text((width//2, 60), "Azories", fill=(255, 255, 255), font=brand_font, anchor="mm")
    
    # Draw title
    draw.text((width//2, 180), title, fill=(255, 255, 255), font=title_font, anchor="mm")
    
    # Draw author
    draw.text((width//2, 240), f"by {author}", fill=(200, 200, 200), font=tagline_font, anchor="mm")
    
    # Draw summary - wrapped text
    summary_y = 320
    max_width = width - 100
    words = summary.split()
    lines = []
    current_line = []
    
    for word in words:
        current_line.append(word)
        test_line = ' '.join(current_line)
        bbox = draw.textbbox((0, 0), test_line, font=summary_font)
        if bbox[2] > max_width:
            if len(current_line) > 1:
                current_line.pop()
                lines.append(' '.join(current_line))
                current_line = [word]
            else:
                lines.append(test_line)
                current_line = []
    if current_line:
        lines.append(' '.join(current_line))
    
    for line in lines:
        draw.text((width//2, summary_y), line, fill=(230, 230, 230), font=summary_font, anchor="mm")
        summary_y += 36
    
    # Draw tagline at bottom
    draw.text((width//2, height - 30), "Where every child is the hero of their own story", 
              fill=(180, 180, 180), font=tagline_font, anchor="mm")
    
    # Save to BytesIO
    img_bytes = BytesIO()
    img.save(img_bytes, format='PNG', quality=95)
    img_bytes.seek(0)
    
    # Upload to Cloudinary
    safe_title = title.lower().replace(' ', '_').replace("'", "")[:30]
    public_id = f"azories/back_covers/{safe_title}_back"
    
    result = cloudinary.uploader.upload(
        img_bytes,
        public_id=public_id,
        overwrite=True,
        resource_type="image"
    )
    
    return result['secure_url']


def main():
    book_id = "ba53b445-c96f-4d4e-bd6a-c92828e99fe6"
    
    # New summary based on actual story content
    new_summary = "Max always dreamed of being a superhero, but his powers had other plans! With sideways flying, invisible hiccups, and super sneezes, Max learns that even the silliest powers can save the day."
    
    print(f"Updating Super Silly Superhero...")
    print(f"New summary: {new_summary}")
    
    # Update summary in database
    result = db.books.update_one(
        {"id": book_id},
        {"$set": {"summary": new_summary}}
    )
    print(f"Updated summary in database: {result.modified_count} document(s)")
    
    # Generate new back cover
    book = db.books.find_one({"id": book_id})
    if book:
        back_cover_url = create_back_cover(
            book_id,
            book.get('title', 'Super Silly Superhero'),
            new_summary,
            book.get('author_name', 'Young Author')
        )
        
        # Update back cover URL
        db.books.update_one(
            {"id": book_id},
            {"$set": {"back_cover_image": back_cover_url}}
        )
        print(f"New back cover: {back_cover_url}")
    else:
        print("Book not found!")


if __name__ == "__main__":
    main()
