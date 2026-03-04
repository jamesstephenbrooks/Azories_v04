"""
Print-Ready PDF Generator for Gelato Print on Demand
Generates high-resolution 8x8" (200x200mm) PDFs with bonus pages
"""

import io
import base64
import aiohttp
from datetime import datetime
from reportlab.lib.pagesizes import landscape, portrait
from reportlab.lib.units import mm, inch
from reportlab.lib.colors import Color, HexColor
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from PIL import Image as PILImage
import logging

logger = logging.getLogger(__name__)

# Page dimensions for 8x8" photobook (200mm x 200mm)
PAGE_SIZE = (200 * mm, 200 * mm)  # 8x8 inches
PAGE_WIDTH, PAGE_HEIGHT = PAGE_SIZE

# Bleed area (3mm on each side for print)
BLEED = 3 * mm
TRIM_SIZE = (PAGE_WIDTH + 2 * BLEED, PAGE_HEIGHT + 2 * BLEED)

# Brand colors
PURPLE_DARK = HexColor('#3F1461')
PURPLE_MID = HexColor('#6B4E8D')
PURPLE_LIGHT = HexColor('#9B7FC4')
GOLD = HexColor('#D4AF37')
GOLD_LIGHT = HexColor('#F4E4BC')
TEAL = HexColor('#2DD4BF')
CREAM = HexColor('#FDF8F3')
WHITE = HexColor('#FFFFFF')

# Official Azora mascot images from Cloudinary
AZORA_IMAGES = {
    # The End page - friendly goodbye wave
    "the_end": "https://res.cloudinary.com/dlbmjqmoy/image/upload/v1772279875/azories/mascot/azora_waving_hello.jpg",
    # About Azories page - confident professional pose
    "about": "https://res.cloudinary.com/dlbmjqmoy/image/upload/v1772279581/azories/mascot/azora_pose1_confident.jpg",
    # Story of Azora page - reading in library
    "story": "https://res.cloudinary.com/dlbmjqmoy/image/upload/v1772279589/azories/mascot/azora_pose3_reading.jpg",
    # Draw Your Scene - small corner icon
    "icon": "https://res.cloudinary.com/dlbmjqmoy/image/upload/v1772279877/azories/mascot/dragon_icon_solo.jpg",
    # What Happens Next - encouraging pointing pose
    "pointing": "https://res.cloudinary.com/dlbmjqmoy/image/upload/v1772280556/azories/mascot/azora_pointing_v2.jpg",
    # Reading Journal - cozy reading scene
    "reading_cozy": "https://res.cloudinary.com/dlbmjqmoy/image/upload/v1772279866/azories/mascot/azora_reading_cozy.jpg",
    # Your Turn! page - pointing at prompts
    "your_turn": "https://res.cloudinary.com/dlbmjqmoy/image/upload/v1772279592/azories/mascot/azora_pose4_pointing.jpg",
    # Back Cover - friendly brand image
    "back_cover": "https://res.cloudinary.com/dlbmjqmoy/image/upload/v1772279875/azories/mascot/azora_waving_hello.jpg",
    # Avatar for small uses
    "avatar": "https://res.cloudinary.com/dlbmjqmoy/image/upload/v1772279871/azories/mascot/azora_avatar_face.jpg"
}

# Cache for fetched images
_image_cache = {}


async def fetch_image(url: str) -> PILImage.Image:
    """Fetch image from URL or base64 and return PIL Image with caching."""
    if not url:
        return None
    
    if url in _image_cache:
        return _image_cache[url].copy()
    
    try:
        if url.startswith("data:image"):
            img_data = url.split(",")[1]
            img_bytes = base64.b64decode(img_data)
            img = PILImage.open(io.BytesIO(img_bytes))
            _image_cache[url] = img.copy()
            return img
        elif url.startswith("http"):
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                    if resp.status == 200:
                        img_bytes = await resp.read()
                        img = PILImage.open(io.BytesIO(img_bytes))
                        _image_cache[url] = img.copy()
                        return img
        return None
    except Exception as e:
        logger.warning(f"Failed to fetch image {url[:50]}...: {e}")
        return None


async def get_azora_image(key: str) -> PILImage.Image:
    """Get a pre-generated Azora image by key."""
    url = AZORA_IMAGES.get(key)
    if url:
        return await fetch_image(url)
    return None


def draw_image_cover(c, pil_img, x, y, width, height):
    """Draw image filling the entire specified area with crop (object-fit: cover)."""
    if pil_img is None:
        c.setFillColor(PURPLE_DARK)
        c.rect(x, y, width, height, fill=1, stroke=0)
        return
    
    # Convert to RGB if needed
    if pil_img.mode in ('RGBA', 'LA', 'P'):
        background = PILImage.new('RGB', pil_img.size, (255, 255, 255))
        if pil_img.mode == 'P':
            pil_img = pil_img.convert('RGBA')
        if pil_img.mode == 'RGBA':
            background.paste(pil_img, mask=pil_img.split()[-1])
        else:
            background.paste(pil_img)
        pil_img = background
    
    # Calculate crop to fill target area
    img_width, img_height = pil_img.size
    target_ratio = width / height
    img_ratio = img_width / img_height
    
    if img_ratio > target_ratio:
        new_width = int(img_height * target_ratio)
        left = (img_width - new_width) // 2
        pil_img = pil_img.crop((left, 0, left + new_width, img_height))
    else:
        new_height = int(img_width / target_ratio)
        top = 0
        pil_img = pil_img.crop((0, top, img_width, top + new_height))
    
    # Save to buffer at high quality
    img_buffer = io.BytesIO()
    pil_img.save(img_buffer, format='JPEG', quality=95, dpi=(300, 300))
    img_buffer.seek(0)
    
    c.drawImage(ImageReader(img_buffer), x, y, width=width, height=height, preserveAspectRatio=False)


def draw_image_contain(c, pil_img, x, y, max_width, max_height):
    """Draw image within bounds preserving aspect ratio (object-fit: contain)."""
    if pil_img is None:
        return
    
    if pil_img.mode in ('RGBA', 'LA', 'P'):
        background = PILImage.new('RGB', pil_img.size, (255, 255, 255))
        if pil_img.mode == 'P':
            pil_img = pil_img.convert('RGBA')
        if pil_img.mode == 'RGBA':
            background.paste(pil_img, mask=pil_img.split()[-1])
        else:
            background.paste(pil_img)
        pil_img = background
    
    img_width, img_height = pil_img.size
    img_ratio = img_width / img_height
    target_ratio = max_width / max_height
    
    if img_ratio > target_ratio:
        # Width limited
        draw_width = max_width
        draw_height = max_width / img_ratio
    else:
        # Height limited
        draw_height = max_height
        draw_width = max_height * img_ratio
    
    # Center in the available space
    draw_x = x + (max_width - draw_width) / 2
    draw_y = y + (max_height - draw_height) / 2
    
    img_buffer = io.BytesIO()
    pil_img.save(img_buffer, format='JPEG', quality=95, dpi=(300, 300))
    img_buffer.seek(0)
    
    c.drawImage(ImageReader(img_buffer), draw_x, draw_y, width=draw_width, height=draw_height)


def draw_wrapped_text(c, text, x, y, max_width, font_name="Helvetica", font_size=12, line_height=None, align="left"):
    """Draw text with word wrapping."""
    if not text:
        return y
    
    if line_height is None:
        line_height = font_size * 1.4
    
    c.setFont(font_name, font_size)
    words = text.split()
    lines = []
    current_line = ""
    
    for word in words:
        test_line = current_line + (" " if current_line else "") + word
        if c.stringWidth(test_line, font_name, font_size) < max_width:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
            current_line = word
    if current_line:
        lines.append(current_line)
    
    for line in lines:
        if align == "center":
            c.drawCentredString(x + max_width / 2, y, line)
        elif align == "right":
            c.drawRightString(x + max_width, y, line)
        else:
            c.drawString(x, y, line)
        y -= line_height
    
    return y


def draw_decorative_border(c, margin=15*mm, color=PURPLE_LIGHT):
    """Draw a decorative border around the page."""
    c.setStrokeColor(color)
    c.setLineWidth(2)
    c.roundRect(margin, margin, PAGE_WIDTH - 2*margin, PAGE_HEIGHT - 2*margin, 10*mm, stroke=1, fill=0)
    
    # Corner decorations
    c.setFillColor(GOLD)
    for corner_x, corner_y in [(margin, margin), (PAGE_WIDTH - margin, margin), 
                                (margin, PAGE_HEIGHT - margin), (PAGE_WIDTH - margin, PAGE_HEIGHT - margin)]:
        c.circle(corner_x, corner_y, 3*mm, fill=1, stroke=0)


def draw_stars(c, count=15):
    """Draw decorative stars scattered on page."""
    c.setFillColor(GOLD)
    star_positions = [
        (30*mm, 170*mm), (170*mm, 175*mm), (25*mm, 40*mm), (175*mm, 35*mm),
        (50*mm, 160*mm), (150*mm, 165*mm), (40*mm, 55*mm), (160*mm, 50*mm),
        (100*mm, 180*mm), (100*mm, 20*mm), (20*mm, 100*mm), (180*mm, 100*mm),
        (60*mm, 140*mm), (140*mm, 145*mm), (70*mm, 60*mm)
    ]
    for i, (sx, sy) in enumerate(star_positions[:count]):
        size = 2*mm if i % 3 == 0 else 1.5*mm
        c.saveState()
        c.translate(sx, sy)
        c.setFillColor(GOLD if i % 2 == 0 else GOLD_LIGHT)
        path = c.beginPath()
        path.moveTo(0, size)
        path.lineTo(size*0.3, size*0.3)
        path.lineTo(size, 0)
        path.lineTo(size*0.3, -size*0.3)
        path.lineTo(0, -size)
        path.lineTo(-size*0.3, -size*0.3)
        path.lineTo(-size, 0)
        path.lineTo(-size*0.3, size*0.3)
        path.close()
        c.drawPath(path, fill=1, stroke=0)
        c.restoreState()


# ============== BONUS PAGES ==============

async def draw_bonus_page_the_end(c, book_title=""):
    """Page B1 - 'The End' - Azora waving goodbye."""
    # Purple background
    c.setFillColor(PURPLE_DARK)
    c.rect(0, 0, PAGE_WIDTH, PAGE_HEIGHT, fill=1, stroke=0)
    
    # Lighter purple circle in center
    c.setFillColor(PURPLE_MID)
    c.circle(PAGE_WIDTH/2, PAGE_HEIGHT/2 + 10*mm, 65*mm, fill=1, stroke=0)
    
    # Draw stars
    draw_stars(c, 12)
    
    # "The End" title at top
    c.setFillColor(GOLD)
    c.setFont("Helvetica-Bold", 36)
    c.drawCentredString(PAGE_WIDTH/2, PAGE_HEIGHT - 35*mm, "The End")
    
    # Decorative line
    c.setStrokeColor(GOLD)
    c.setLineWidth(2)
    c.line(50*mm, PAGE_HEIGHT - 45*mm, PAGE_WIDTH - 50*mm, PAGE_HEIGHT - 45*mm)
    
    # Azora waving image in center
    azora_img = await get_azora_image("the_end")
    if azora_img:
        draw_image_contain(c, azora_img, PAGE_WIDTH/2 - 40*mm, PAGE_HEIGHT/2 - 50*mm, 80*mm, 90*mm)
    
    # Book title at bottom
    if book_title:
        c.setFillColor(Color(0.2, 0.1, 0.3, alpha=0.8))
        c.rect(0, 0, PAGE_WIDTH, 35*mm, fill=1, stroke=0)
        c.setFillColor(GOLD_LIGHT)
        c.setFont("Helvetica-Oblique", 13)
        c.drawCentredString(PAGE_WIDTH/2, 15*mm, f'"{book_title}"')
    
    c.showPage()


async def draw_bonus_page_about_azories(c):
    """Page B2 - About Azories with confident Azora pose."""
    c.setFillColor(CREAM)
    c.rect(0, 0, PAGE_WIDTH, PAGE_HEIGHT, fill=1, stroke=0)
    
    # Header
    c.setFillColor(PURPLE_DARK)
    c.rect(0, PAGE_HEIGHT - 35*mm, PAGE_WIDTH, 35*mm, fill=1, stroke=0)
    c.setFillColor(GOLD)
    c.setFont("Helvetica-Bold", 24)
    c.drawCentredString(PAGE_WIDTH/2, PAGE_HEIGHT - 25*mm, "About Azories")
    
    # Azora confident pose on left
    azora_img = await get_azora_image("about")
    if azora_img:
        draw_image_contain(c, azora_img, 8*mm, PAGE_HEIGHT/2 - 45*mm, 65*mm, 85*mm)
    
    # Text on right
    text_x = 78*mm
    text_width = 105*mm
    about_text = """Azories is a magical world of stories where every child is the hero of their own adventure.

Founded with a simple dream, Azories was created to give every child access to beautiful, imaginative stories — completely free, forever.

Azora the dragon is our guide through thousands of magical tales, always ready to lead young readers on their next adventure.

Visit us at azories.com"""
    
    c.setFillColor(PURPLE_DARK)
    y_pos = PAGE_HEIGHT - 55*mm
    for para in about_text.split('\n\n'):
        y_pos = draw_wrapped_text(c, para.strip(), text_x, y_pos, text_width, "Helvetica", 10)
        y_pos -= 6*mm
    
    # Footer
    c.setFillColor(PURPLE_LIGHT)
    c.rect(0, 0, PAGE_WIDTH, 18*mm, fill=1, stroke=0)
    c.setFillColor(WHITE)
    c.setFont("Helvetica-Bold", 9)
    c.drawCentredString(PAGE_WIDTH/2, 7*mm, "Where every child is the hero of their own story")
    
    c.showPage()


async def draw_bonus_page_azora_story(c):
    """Page B3 - The Story of Azora with reading pose."""
    c.setFillColor(PURPLE_DARK)
    c.rect(0, 0, PAGE_WIDTH, PAGE_HEIGHT, fill=1, stroke=0)
    
    # Title
    c.setFillColor(GOLD)
    c.setFont("Helvetica-Bold", 20)
    c.drawCentredString(PAGE_WIDTH/2, PAGE_HEIGHT - 28*mm, "The Story of Azora")
    c.setStrokeColor(GOLD)
    c.setLineWidth(1)
    c.line(50*mm, PAGE_HEIGHT - 34*mm, PAGE_WIDTH - 50*mm, PAGE_HEIGHT - 34*mm)
    
    # Azora reading illustration
    azora_img = await get_azora_image("story")
    if azora_img:
        draw_image_contain(c, azora_img, PAGE_WIDTH/2 - 35*mm, PAGE_HEIGHT - 105*mm, 70*mm, 65*mm)
    
    # Story text
    story_text = """Azora is a small but mighty dragon who lives in the Grand Library — a magical place where every book ever written floats on golden shelves that stretch up to the clouds.

Azora's job is the best job in the world: to find the perfect story for every child who visits.

With a flick of her glowing tail and a sprinkle of story dust, Azora can bring any book to life — filling the air with characters, adventures and magic.

She believes that every child deserves a story that belongs to them. And she never stops searching until she finds it."""
    
    c.setFillColor(CREAM)
    y_pos = PAGE_HEIGHT - 115*mm
    text_margin = 22*mm
    for para in story_text.split('\n\n'):
        y_pos = draw_wrapped_text(c, para.strip(), text_margin, y_pos, PAGE_WIDTH - 2*text_margin, "Helvetica", 9, align="center")
        y_pos -= 5*mm
    
    draw_stars(c, 10)
    c.showPage()


async def draw_bonus_page_draw_scene(c):
    """Page B4 - Draw Your Favourite Scene activity with dragon icon."""
    c.setFillColor(CREAM)
    c.rect(0, 0, PAGE_WIDTH, PAGE_HEIGHT, fill=1, stroke=0)
    draw_decorative_border(c, 12*mm, PURPLE_MID)
    
    # Title
    c.setFillColor(PURPLE_DARK)
    c.setFont("Helvetica-Bold", 18)
    c.drawCentredString(PAGE_WIDTH/2, PAGE_HEIGHT - 26*mm, "Draw Your Favourite Scene")
    
    # Drawing box
    box_margin = 22*mm
    box_top = PAGE_HEIGHT - 42*mm
    box_bottom = 35*mm
    
    c.setStrokeColor(PURPLE_LIGHT)
    c.setLineWidth(2)
    c.setFillColor(WHITE)
    c.roundRect(box_margin, box_bottom, PAGE_WIDTH - 2*box_margin, box_top - box_bottom, 4*mm, fill=1, stroke=1)
    
    # Corner flourishes
    c.setStrokeColor(GOLD)
    c.setLineWidth(2)
    for bx, by, dx, dy in [(box_margin, box_top, 1, -1), (PAGE_WIDTH - box_margin, box_top, -1, -1),
                           (box_margin, box_bottom, 1, 1), (PAGE_WIDTH - box_margin, box_bottom, -1, 1)]:
        c.line(bx, by, bx + dx*8*mm, by)
        c.line(bx, by, bx, by + dy*8*mm)
    
    # Small dragon icon in corner
    icon_img = await get_azora_image("icon")
    if icon_img:
        draw_image_contain(c, icon_img, PAGE_WIDTH - 45*mm, PAGE_HEIGHT - 40*mm, 25*mm, 25*mm)
    
    # Prompt
    c.setFillColor(PURPLE_MID)
    c.setFont("Helvetica-Oblique", 10)
    c.drawCentredString(PAGE_WIDTH/2, 22*mm, "What was your favourite part of the story?")
    
    c.showPage()


async def draw_bonus_page_what_happens_next(c):
    """Page B5 - What Happens Next? writing activity with pointing Azora."""
    c.setFillColor(CREAM)
    c.rect(0, 0, PAGE_WIDTH, PAGE_HEIGHT, fill=1, stroke=0)
    draw_decorative_border(c, 12*mm, TEAL)
    
    c.setFillColor(PURPLE_DARK)
    c.setFont("Helvetica-Bold", 18)
    c.drawCentredString(PAGE_WIDTH/2, PAGE_HEIGHT - 26*mm, "What Happens Next?")
    
    c.setFillColor(PURPLE_MID)
    c.setFont("Helvetica-Oblique", 11)
    c.drawCentredString(PAGE_WIDTH/2, PAGE_HEIGHT - 40*mm, "Continue the story in your own words...")
    
    # Lines
    line_x = 22*mm
    line_end = PAGE_WIDTH - 22*mm
    y = PAGE_HEIGHT - 55*mm
    c.setStrokeColor(PURPLE_LIGHT)
    c.setLineWidth(0.5)
    for _ in range(13):
        c.line(line_x, y, line_end, y)
        y -= 9*mm
    
    # Azora pointing in corner
    azora_img = await get_azora_image("pointing")
    if azora_img:
        draw_image_contain(c, azora_img, PAGE_WIDTH - 55*mm, 8*mm, 38*mm, 45*mm)
    
    c.showPage()


async def draw_bonus_page_reading_journal(c):
    """Page B6 - My Reading Journal with cozy reading Azora."""
    c.setFillColor(CREAM)
    c.rect(0, 0, PAGE_WIDTH, PAGE_HEIGHT, fill=1, stroke=0)
    draw_decorative_border(c, 12*mm, GOLD)
    
    c.setFillColor(PURPLE_DARK)
    c.setFont("Helvetica-Bold", 20)
    c.drawCentredString(PAGE_WIDTH/2, PAGE_HEIGHT - 28*mm, "My Reading Journal")
    
    # Cozy reading Azora in top right corner
    azora_img = await get_azora_image("reading_cozy")
    if azora_img:
        draw_image_contain(c, azora_img, PAGE_WIDTH - 52*mm, PAGE_HEIGHT - 55*mm, 35*mm, 40*mm)
    
    fields = [
        ("I read this book on:", 22*mm),
        ("I read it with:", 22*mm),
        ("My favourite character was:", 22*mm),
        ("This story made me feel:", 22*mm),
        ("I would recommend this to:", 22*mm)
    ]
    
    y = PAGE_HEIGHT - 52*mm
    margin = 22*mm
    c.setFillColor(PURPLE_DARK)
    for label, spacing in fields:
        c.setFont("Helvetica-Bold", 10)
        c.drawString(margin, y, label)
        c.setStrokeColor(PURPLE_LIGHT)
        c.setLineWidth(0.8)
        c.line(margin, y - 10*mm, PAGE_WIDTH - margin - 40*mm, y - 10*mm)
        y -= spacing
    
    # Star rating
    y -= 5*mm
    c.setFont("Helvetica-Bold", 10)
    c.drawString(margin, y, "I give this story:")
    star_x = margin + 50*mm
    c.setStrokeColor(GOLD)
    c.setFillColor(GOLD_LIGHT)
    for i in range(5):
        c.circle(star_x + i * 12*mm, y, 4*mm, fill=1, stroke=1)
    c.setFillColor(PURPLE_MID)
    c.setFont("Helvetica", 8)
    c.drawString(star_x + 65*mm, y - 2*mm, "(circle your rating)")
    
    c.showPage()


async def draw_bonus_page_create_story(c):
    """Page B7 - Your Turn! Create your own story with pointing Azora."""
    c.setFillColor(CREAM)
    c.rect(0, 0, PAGE_WIDTH, PAGE_HEIGHT, fill=1, stroke=0)
    
    # Purple header
    c.setFillColor(PURPLE_DARK)
    c.rect(0, PAGE_HEIGHT - 42*mm, PAGE_WIDTH, 42*mm, fill=1, stroke=0)
    
    c.setFillColor(GOLD)
    c.setFont("Helvetica-Bold", 22)
    c.drawCentredString(PAGE_WIDTH/2, PAGE_HEIGHT - 24*mm, "Your Turn!")
    
    c.setFillColor(CREAM)
    c.setFont("Helvetica-Oblique", 11)
    c.drawCentredString(PAGE_WIDTH/2, PAGE_HEIGHT - 38*mm, "Every great author started with one idea. What's yours?")
    
    # Prompts with boxes
    prompts = ["My story is called:", "My main character is:", "The adventure begins when:"]
    y = PAGE_HEIGHT - 60*mm
    margin = 22*mm
    
    c.setFillColor(PURPLE_DARK)
    for prompt in prompts:
        c.setFont("Helvetica-Bold", 10)
        c.drawString(margin, y, prompt)
        c.setStrokeColor(PURPLE_LIGHT)
        c.setFillColor(WHITE)
        c.roundRect(margin, y - 20*mm, PAGE_WIDTH - 2*margin, 16*mm, 2*mm, fill=1, stroke=1)
        y -= 32*mm
    
    # CTA
    c.setFillColor(PURPLE_DARK)
    c.setFont("Helvetica-Bold", 9)
    c.drawCentredString(PAGE_WIDTH/2, 28*mm, "Visit azories.com to turn your idea into a real illustrated book!")
    
    # Azora pointing at the prompts
    azora_img = await get_azora_image("your_turn")
    if azora_img:
        draw_image_contain(c, azora_img, PAGE_WIDTH - 58*mm, 5*mm, 45*mm, 55*mm)
    
    c.showPage()


async def draw_bonus_page_back_cover(c, book_title="", book_summary="", author_name=""):
    """Page B8 - Back cover with waving Azora and full branding."""
    # Purple background
    c.setFillColor(PURPLE_DARK)
    c.rect(0, 0, PAGE_WIDTH, PAGE_HEIGHT, fill=1, stroke=0)
    
    # Lighter circle
    c.setFillColor(PURPLE_MID)
    c.circle(PAGE_WIDTH/2, PAGE_HEIGHT/2 + 20*mm, 55*mm, fill=1, stroke=0)
    
    # Azories logo at top
    c.setFillColor(GOLD)
    c.setFont("Helvetica-Bold", 32)
    c.drawCentredString(PAGE_WIDTH/2, PAGE_HEIGHT - 30*mm, "Azories")
    
    # Tagline
    c.setFillColor(CREAM)
    c.setFont("Helvetica-Oblique", 10)
    c.drawCentredString(PAGE_WIDTH/2, PAGE_HEIGHT - 43*mm, "Where every child is the hero of their own story")
    
    # Decorative line
    c.setStrokeColor(GOLD)
    c.setLineWidth(1)
    c.line(45*mm, PAGE_HEIGHT - 50*mm, PAGE_WIDTH - 45*mm, PAGE_HEIGHT - 50*mm)
    
    # Azora waving in center
    azora_img = await get_azora_image("back_cover")
    if azora_img:
        draw_image_contain(c, azora_img, PAGE_WIDTH/2 - 40*mm, PAGE_HEIGHT/2 - 35*mm, 80*mm, 90*mm)
    
    # Book info at bottom
    c.setFillColor(Color(0.15, 0.08, 0.25, alpha=0.9))
    c.rect(0, 0, PAGE_WIDTH, 55*mm, fill=1, stroke=0)
    
    if book_title:
        c.setFillColor(GOLD)
        c.setFont("Helvetica-Bold", 13)
        c.drawCentredString(PAGE_WIDTH/2, 42*mm, f'"{book_title}"')
    
    if author_name:
        c.setFillColor(CREAM)
        c.setFont("Helvetica-Oblique", 10)
        c.drawCentredString(PAGE_WIDTH/2, 32*mm, f"by {author_name}")
    
    # Website
    c.setFillColor(GOLD)
    c.setFont("Helvetica-Bold", 11)
    c.drawCentredString(PAGE_WIDTH/2, 18*mm, "azories.com")
    
    c.setFillColor(PURPLE_LIGHT)
    c.setFont("Helvetica", 7)
    c.drawCentredString(PAGE_WIDTH/2, 8*mm, f"Created with Azories | {datetime.now().year}")
    
    # Draw stars
    draw_stars(c, 8)
    
    c.showPage()


def draw_blank_decorated_page(c):
    """Blank page with Azories decorative border for padding."""
    c.setFillColor(CREAM)
    c.rect(0, 0, PAGE_WIDTH, PAGE_HEIGHT, fill=1, stroke=0)
    draw_decorative_border(c, 15*mm, PURPLE_LIGHT)
    draw_stars(c, 6)
    c.showPage()


async def generate_print_preview_pdf(output_path: str = "/tmp/print_preview.pdf"):
    """Generate a preview PDF with all bonus pages."""
    pdf_buffer = io.BytesIO()
    c = canvas.Canvas(pdf_buffer, pagesize=PAGE_SIZE)
    
    book_title = "The Adventures of Luna"
    author_name = "A Young Author"
    book_summary = "Join Luna on a magical journey through enchanted forests and sparkling seas."
    
    # Draw all bonus pages
    await draw_bonus_page_the_end(c, book_title)
    await draw_bonus_page_about_azories(c)
    await draw_bonus_page_azora_story(c)
    await draw_bonus_page_draw_scene(c)
    await draw_bonus_page_what_happens_next(c)
    await draw_bonus_page_reading_journal(c)
    await draw_bonus_page_create_story(c)
    await draw_bonus_page_back_cover(c, book_title, book_summary, author_name)
    
    c.save()
    pdf_buffer.seek(0)
    
    with open(output_path, 'wb') as f:
        f.write(pdf_buffer.read())
    
    return output_path


async def generate_print_ready_pdf(
    book: dict,
    pages: list,
    output_buffer: io.BytesIO = None
) -> io.BytesIO:
    """
    Generate a print-ready PDF for Gelato.
    
    Args:
        book: Book document with title, author, cover_image, etc.
        pages: List of page documents with image_url and text_content
    
    Returns:
        BytesIO buffer containing the PDF
    """
    if output_buffer is None:
        output_buffer = io.BytesIO()
    
    c = canvas.Canvas(output_buffer, pagesize=PAGE_SIZE)
    
    book_title = book.get("title", "Untitled")
    author_name = book.get("author_name", "")
    book_summary = book.get("description", "")
    
    # ============== FRONT COVER ==============
    cover_img = await fetch_image(book.get("cover_image", ""))
    draw_image_cover(c, cover_img, 0, 0, PAGE_WIDTH, PAGE_HEIGHT)
    
    # Title overlay
    c.setFillColor(Color(0, 0, 0, alpha=0.5))
    c.rect(0, 0, PAGE_WIDTH, 45*mm, fill=1, stroke=0)
    c.setFillColor(WHITE)
    c.setFont("Helvetica-Bold", 18)
    c.drawCentredString(PAGE_WIDTH/2, 28*mm, book_title)
    if author_name:
        c.setFont("Helvetica-Oblique", 11)
        c.drawCentredString(PAGE_WIDTH/2, 15*mm, f"by {author_name}")
    c.showPage()
    
    # ============== STORY PAGES ==============
    for page_num, page in enumerate(pages):
        image_url = page.get("image_url", "") or page.get("illustration_url", "")
        text_content = page.get("text_content", "") or page.get("text", "") or page.get("content", "")
        
        page_img = await fetch_image(image_url)
        draw_image_cover(c, page_img, 0, 0, PAGE_WIDTH, PAGE_HEIGHT)
        
        if text_content:
            c.setFillColor(Color(1, 1, 1, alpha=0.88))
            c.roundRect(12*mm, 8*mm, PAGE_WIDTH - 24*mm, 40*mm, 4*mm, fill=1, stroke=0)
            c.setFillColor(PURPLE_DARK)
            draw_wrapped_text(c, text_content, 16*mm, 40*mm, PAGE_WIDTH - 32*mm, "Helvetica", 10)
        
        # Page number
        c.setFillColor(Color(0.3, 0.3, 0.3, alpha=0.6))
        c.setFont("Helvetica", 7)
        c.drawCentredString(PAGE_WIDTH/2, 3*mm, f"— {page_num + 1} —")
        c.showPage()
    
    # ============== BONUS PAGES ==============
    await draw_bonus_page_the_end(c, book_title)
    await draw_bonus_page_about_azories(c)
    await draw_bonus_page_azora_story(c)
    await draw_bonus_page_draw_scene(c)
    await draw_bonus_page_what_happens_next(c)
    await draw_bonus_page_reading_journal(c)
    await draw_bonus_page_create_story(c)
    await draw_bonus_page_back_cover(c, book_title, book_summary, author_name)
    
    # Count total pages
    total_pages = 1 + len(pages) + 8  # cover + story + bonus
    
    # ============== PADDING TO 28 PAGES ==============
    while total_pages < 28:
        draw_blank_decorated_page(c)
        total_pages += 1
    
    # Ensure even page count
    if total_pages % 2 != 0:
        draw_blank_decorated_page(c)
    
    c.save()
    output_buffer.seek(0)
    return output_buffer


if __name__ == "__main__":
    import asyncio
    asyncio.run(generate_print_preview_pdf("/tmp/bonus_pages_preview.pdf"))
    print("Preview PDF generated at /tmp/bonus_pages_preview.pdf")
