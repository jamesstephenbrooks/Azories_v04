"""
Print PDF Generator - Creates print-ready PDFs for Gelato Print on Demand

PDF Specifications (8x10 Portrait Format):
- Page size: 8x10 inches (203.2mm x 254mm)
- Resolution: 300 DPI
- Pixel dimensions: 2400 x 3000 pixels per page
- Format: PDF for Gelato photobook

Layout: Spread format like the Azories app
- Left page: Full illustration
- Right page: Story text

Page Order:
1. Front Cover
2. Inside front (blank or dedication)
3. Welcome Page
4. Dedication Page  
5-24. Story Spreads (image left, text right)
25-31. Bonus pages (The End, Thank You, Certificate, About, Meet Azora)
32+. Filler pages with mascot images
Last. Back Cover
"""

import os
import io
import asyncio
import aiohttp
from datetime import datetime, timezone
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from reportlab.lib.pagesizes import inch
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
import tempfile
import logging

logger = logging.getLogger(__name__)

# Page dimensions for 8x10 inch PORTRAIT at 300 DPI
PAGE_WIDTH_INCHES = 8
PAGE_HEIGHT_INCHES = 10
DPI = 300
PAGE_WIDTH_PX = int(PAGE_WIDTH_INCHES * DPI)   # 2400 pixels
PAGE_HEIGHT_PX = int(PAGE_HEIGHT_INCHES * DPI)  # 3000 pixels

# ReportLab uses points (72 points = 1 inch)
PAGE_WIDTH_PT = PAGE_WIDTH_INCHES * inch   # 576 points
PAGE_HEIGHT_PT = PAGE_HEIGHT_INCHES * inch  # 720 points

# Bonus page mascot images
BONUS_IMAGES = {
    'welcome': 'https://customer-assets.emergentagent.com/job_5f7e2b9e-d2a4-4bf3-b6c6-aac66cbef904/artifacts/60k2xrwp_Azora%20Mascot%20Main.jpg',
    'dedication': 'https://customer-assets.emergentagent.com/job_5f7e2b9e-d2a4-4bf3-b6c6-aac66cbef904/artifacts/ve63p3ok_Azora%20Mascot%202.jpg',
    'the_end': 'https://customer-assets.emergentagent.com/job_5f7e2b9e-d2a4-4bf3-b6c6-aac66cbef904/artifacts/k0b04d29_Azora%20Mascot%201.jpg',
    'thank_you': 'https://res.cloudinary.com/dlbmjqmoy/image/upload/e_background_removal/v1772279875/azories/mascot/azora_waving_hello.png',
    'about': 'https://customer-assets.emergentagent.com/job_5f7e2b9e-d2a4-4bf3-b6c6-aac66cbef904/artifacts/dlulgnzy_Azora_Mascot.jpg',
    'certificate': 'https://customer-assets.emergentagent.com/job_5f7e2b9e-d2a4-4bf3-b6c6-aac66cbef904/artifacts/e45x5iez_azora%20library.png',
    'meet_azora': 'https://customer-assets.emergentagent.com/job_5f7e2b9e-d2a4-4bf3-b6c6-aac66cbef904/artifacts/o1xvfgto_azora%20librbary%201.png',
    # Filler page images - best mascot images
    'filler_1': 'https://customer-assets.emergentagent.com/job_5f7e2b9e-d2a4-4bf3-b6c6-aac66cbef904/artifacts/60k2xrwp_Azora%20Mascot%20Main.jpg',
    'filler_2': 'https://customer-assets.emergentagent.com/job_5f7e2b9e-d2a4-4bf3-b6c6-aac66cbef904/artifacts/e45x5iez_azora%20library.png',
    'filler_3': 'https://customer-assets.emergentagent.com/job_5f7e2b9e-d2a4-4bf3-b6c6-aac66cbef904/artifacts/o1xvfgto_azora%20librbary%201.png',
}


class PrintPDFGenerator:
    """Generates print-ready PDFs for photobooks in portrait 8x10 format"""
    
    def __init__(self):
        self.image_cache = {}
        
    async def download_image(self, url: str) -> Image.Image:
        """Download and cache an image from URL"""
        if not url:
            return None
            
        if url in self.image_cache:
            return self.image_cache[url].copy()
            
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=30) as response:
                    if response.status == 200:
                        data = await response.read()
                        img = Image.open(io.BytesIO(data))
                        # Convert to RGB if necessary (for JPEG compatibility)
                        if img.mode in ('RGBA', 'P'):
                            background = Image.new('RGB', img.size, (255, 255, 255))
                            if img.mode == 'RGBA':
                                background.paste(img, mask=img.split()[3])
                            else:
                                background.paste(img)
                            img = background
                        elif img.mode != 'RGB':
                            img = img.convert('RGB')
                        self.image_cache[url] = img
                        return img.copy()
        except Exception as e:
            logger.error(f"Failed to download image {url}: {e}")
        return None
    
    def create_gradient_background(self, width: int, height: int, 
                                   color1: tuple, color2: tuple, 
                                   direction: str = 'vertical') -> Image.Image:
        """Create a gradient background image"""
        img = Image.new('RGB', (width, height))
        draw = ImageDraw.Draw(img)
        
        for i in range(height if direction == 'vertical' else width):
            ratio = i / (height if direction == 'vertical' else width)
            r = int(color1[0] + (color2[0] - color1[0]) * ratio)
            g = int(color1[1] + (color2[1] - color1[1]) * ratio)
            b = int(color1[2] + (color2[2] - color1[2]) * ratio)
            
            if direction == 'vertical':
                draw.line([(0, i), (width, i)], fill=(r, g, b))
            else:
                draw.line([(i, 0), (i, height)], fill=(r, g, b))
        
        return img
    
    def hex_to_rgb(self, hex_color: str) -> tuple:
        """Convert hex color to RGB tuple"""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    def draw_text_centered(self, draw: ImageDraw.Draw, text: str, 
                           y: int, font, color: str, width: int):
        """Draw centered text"""
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        x = (width - text_width) // 2
        draw.text((x, y), text, fill=color, font=font)
    
    def draw_circular_image(self, base: Image.Image, img: Image.Image,
                            center_x: int, center_y: int, radius: int):
        """Draw an image in a circular frame"""
        # Resize image to fit circle
        size = radius * 2
        img = img.resize((size, size), Image.Resampling.LANCZOS)
        
        # Create circular mask
        mask = Image.new('L', (size, size), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.ellipse((0, 0, size - 1, size - 1), fill=255)
        
        # Apply mask to image
        circular_img = Image.new('RGBA', (size, size), (255, 255, 255, 0))
        circular_img.paste(img, (0, 0))
        circular_img.putalpha(mask)
        
        # Paste the circular image
        paste_x = center_x - radius
        paste_y = center_y - radius
        base.paste(circular_img, (paste_x, paste_y), circular_img)
    
    def get_font(self, size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
        """Get a font - try system fonts, fall back to default"""
        font_paths = [
            '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf' if bold else '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
            '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf' if bold else '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf',
            '/usr/share/fonts/truetype/freefont/FreeSansBold.ttf' if bold else '/usr/share/fonts/truetype/freefont/FreeSans.ttf',
        ]
        
        for path in font_paths:
            if os.path.exists(path):
                try:
                    return ImageFont.truetype(path, size)
                except:
                    pass
        
        return ImageFont.load_default()
    
    def word_wrap_text(self, draw: ImageDraw.Draw, text: str, font, max_width: int) -> list:
        """Wrap text to fit within max_width"""
        words = text.split()
        lines = []
        current_line = []
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            bbox = draw.textbbox((0, 0), test_line, font=font)
            if bbox[2] - bbox[0] <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
        if current_line:
            lines.append(' '.join(current_line))
        
        return lines

    # ============================================
    # STORY SPREAD PAGES (Image Left, Text Right)
    # ============================================
    
    async def create_story_image_page(self, page_data: dict) -> Image.Image:
        """Create LEFT page of spread - Full illustration"""
        # Cream/warm paper background
        img = Image.new('RGB', (PAGE_WIDTH_PX, PAGE_HEIGHT_PX), (253, 251, 247))
        draw = ImageDraw.Draw(img)
        
        image_url = page_data.get('image_url')
        
        if image_url:
            story_img = await self.download_image(image_url)
            if story_img:
                # Calculate size to fill page with margins
                margin = 80
                available_width = PAGE_WIDTH_PX - (margin * 2)
                available_height = PAGE_HEIGHT_PX - (margin * 2)
                
                # Maintain aspect ratio and fit within available space
                img_aspect = story_img.width / story_img.height
                page_aspect = available_width / available_height
                
                if img_aspect > page_aspect:
                    # Image is wider - fit to width
                    new_width = available_width
                    new_height = int(available_width / img_aspect)
                else:
                    # Image is taller - fit to height
                    new_height = available_height
                    new_width = int(available_height * img_aspect)
                
                story_img = story_img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
                # Center the image on the page
                x = (PAGE_WIDTH_PX - new_width) // 2
                y = (PAGE_HEIGHT_PX - new_height) // 2
                
                # Add subtle shadow effect
                shadow = Image.new('RGB', (new_width + 20, new_height + 20), (230, 228, 224))
                img.paste(shadow, (x + 10, y + 10))
                
                img.paste(story_img, (x, y))
        else:
            # No image - show decorative placeholder
            self.draw_text_centered(draw, "✦", PAGE_HEIGHT_PX // 2, self.get_font(120), '#d1d5db', PAGE_WIDTH_PX)
        
        return img
    
    async def create_story_text_page(self, page_data: dict, page_number: int) -> Image.Image:
        """Create RIGHT page of spread - Story text"""
        # Cream/warm paper background
        img = Image.new('RGB', (PAGE_WIDTH_PX, PAGE_HEIGHT_PX), (253, 251, 247))
        draw = ImageDraw.Draw(img)
        
        text_content = page_data.get('text_content') or page_data.get('text') or page_data.get('content', '')
        
        margin = 150
        content_width = PAGE_WIDTH_PX - (margin * 2)
        
        # Decorative header ornament
        ornament_y = 200
        draw.line([(margin, ornament_y), (margin + 150, ornament_y)], fill='#d1d5db', width=2)
        font_ornament = self.get_font(36)
        draw.text((PAGE_WIDTH_PX // 2 - 15, ornament_y - 18), "✦", fill='#c4b5fd', font=font_ornament)
        draw.line([(PAGE_WIDTH_PX - margin - 150, ornament_y), (PAGE_WIDTH_PX - margin, ornament_y)], fill='#d1d5db', width=2)
        
        # Story text
        if text_content:
            font_text = self.get_font(52)
            lines = self.word_wrap_text(draw, text_content, font_text, content_width)
            
            # Calculate vertical centering
            line_height = 72
            total_text_height = len(lines) * line_height
            start_y = max(300, (PAGE_HEIGHT_PX - total_text_height) // 2)
            
            y_offset = start_y
            for line in lines:
                if y_offset + line_height > PAGE_HEIGHT_PX - 200:
                    break
                # Center each line
                bbox = draw.textbbox((0, 0), line, font=font_text)
                line_width = bbox[2] - bbox[0]
                x = (PAGE_WIDTH_PX - line_width) // 2
                draw.text((x, y_offset), line, fill='#1f2937', font=font_text)
                y_offset += line_height
        
        # Decorative footer ornament
        footer_y = PAGE_HEIGHT_PX - 200
        draw.line([(margin, footer_y), (margin + 150, footer_y)], fill='#d1d5db', width=2)
        draw.text((PAGE_WIDTH_PX // 2 - 15, footer_y - 18), "✦", fill='#c4b5fd', font=font_ornament)
        draw.line([(PAGE_WIDTH_PX - margin - 150, footer_y), (PAGE_WIDTH_PX - margin, footer_y)], fill='#d1d5db', width=2)
        
        # Page number
        font_page_num = self.get_font(32)
        page_str = str(page_number)
        bbox = draw.textbbox((0, 0), page_str, font=font_page_num)
        draw.text((PAGE_WIDTH_PX - margin - (bbox[2] - bbox[0]), PAGE_HEIGHT_PX - 120), 
                  page_str, fill='#9ca3af', font=font_page_num)
        
        return img

    # ============================================
    # BONUS PAGES
    # ============================================
    
    async def create_welcome_page(self, book_title: str, child_name: str) -> Image.Image:
        """Create Welcome page - personalized title page"""
        img = self.create_gradient_background(
            PAGE_WIDTH_PX, PAGE_HEIGHT_PX,
            (250, 245, 255), (255, 250, 253)
        )
        draw = ImageDraw.Draw(img)
        
        # Decorative corners
        corner_color = (196, 181, 253)
        line_width = 12
        corner_size = 200
        
        # Draw corners
        for pos in [(60, 60, 1, 1), (PAGE_WIDTH_PX-60, 60, -1, 1), 
                    (60, PAGE_HEIGHT_PX-60, 1, -1), (PAGE_WIDTH_PX-60, PAGE_HEIGHT_PX-60, -1, -1)]:
            x, y, dx, dy = pos
            draw.line([(x, y), (x, y + corner_size * dy)], fill=corner_color, width=line_width)
            draw.line([(x, y), (x + corner_size * dx, y)], fill=corner_color, width=line_width)
        
        # Decorative top ornament
        font_ornament = self.get_font(72)
        self.draw_text_centered(draw, "✦  ✦  ✦", 350, font_ornament, '#e9d5ff', PAGE_WIDTH_PX)
        
        # Text - centered vertically
        font_small = self.get_font(52)
        font_title = self.get_font(100, bold=True)
        font_medium = self.get_font(60)
        font_name = self.get_font(90, bold=True)
        
        self.draw_text_centered(draw, "A MAGICAL STORY", 550, font_small, '#7c3aed', PAGE_WIDTH_PX)
        
        # Word wrap the title if it's long
        title = book_title or "Your Story"
        if len(title) > 20:
            # Split into two lines
            words = title.split()
            mid = len(words) // 2
            line1 = ' '.join(words[:mid])
            line2 = ' '.join(words[mid:])
            self.draw_text_centered(draw, line1, 700, font_title, '#1f2937', PAGE_WIDTH_PX)
            self.draw_text_centered(draw, line2, 820, font_title, '#1f2937', PAGE_WIDTH_PX)
            next_y = 1000
        else:
            self.draw_text_centered(draw, title, 750, font_title, '#1f2937', PAGE_WIDTH_PX)
            next_y = 950
        
        # Decorative divider
        divider_y = next_y + 50
        draw.line([(PAGE_WIDTH_PX // 2 - 300, divider_y), (PAGE_WIDTH_PX // 2 - 80, divider_y)], fill='#c4b5fd', width=4)
        self.draw_text_centered(draw, "❦", divider_y - 20, font_ornament, '#a855f7', PAGE_WIDTH_PX)
        draw.line([(PAGE_WIDTH_PX // 2 + 80, divider_y), (PAGE_WIDTH_PX // 2 + 300, divider_y)], fill='#c4b5fd', width=4)
        
        # "For" section
        self.draw_text_centered(draw, "Created especially for", divider_y + 150, font_medium, '#6b7280', PAGE_WIDTH_PX)
        self.draw_text_centered(draw, child_name or "You", divider_y + 270, font_name, '#7c3aed', PAGE_WIDTH_PX)
        
        # Underline for the name
        name_width = len(child_name or "You") * 45
        name_x = (PAGE_WIDTH_PX - name_width) // 2
        draw.line([(name_x, divider_y + 370), (name_x + name_width, divider_y + 370)], fill='#c4b5fd', width=4)
        
        # Sparkles decorations
        sparkle_font = self.get_font(48)
        draw.text((300, 500), "✨", fill='#fbbf24', font=sparkle_font)
        draw.text((PAGE_WIDTH_PX - 380, 600), "✨", fill='#fbbf24', font=sparkle_font)
        draw.text((250, divider_y + 200), "✦", fill='#e9d5ff', font=sparkle_font)
        draw.text((PAGE_WIDTH_PX - 330, divider_y + 250), "✦", fill='#e9d5ff', font=sparkle_font)
        
        # Footer
        font_footer = self.get_font(36)
        self.draw_text_centered(draw, "Made with love on Azories.com", PAGE_HEIGHT_PX - 150, font_footer, '#9ca3af', PAGE_WIDTH_PX)
        
        return img
    
    async def create_dedication_page(self, child_name: str, dedication_message: str = None) -> Image.Image:
        """Create Dedication page - 'This book belongs to' page"""
        img = self.create_gradient_background(
            PAGE_WIDTH_PX, PAGE_HEIGHT_PX,
            (254, 252, 232), (255, 255, 255)
        )
        draw = ImageDraw.Draw(img)
        
        # Decorative border
        draw.rectangle([(80, 80), (PAGE_WIDTH_PX - 80, PAGE_HEIGHT_PX - 80)], outline=(253, 230, 138), width=8)
        draw.rectangle([(120, 120), (PAGE_WIDTH_PX - 120, PAGE_HEIGHT_PX - 120)], outline=(254, 243, 199), width=4)
        
        # Top ornament
        font_ornament = self.get_font(72)
        self.draw_text_centered(draw, "❦", 300, font_ornament, '#d97706', PAGE_WIDTH_PX)
        
        # Main text
        font_subtitle = self.get_font(64)
        font_name = self.get_font(100, bold=True)
        
        self.draw_text_centered(draw, "This book belongs to", 550, font_subtitle, '#4b5563', PAGE_WIDTH_PX)
        
        # Name with underline
        name_text = child_name or "________________"
        self.draw_text_centered(draw, name_text, 720, font_name, '#b45309', PAGE_WIDTH_PX)
        
        # Underline
        name_width = max(len(name_text) * 50, 600)
        name_x = (PAGE_WIDTH_PX - name_width) // 2
        draw.line([(name_x, 850), (name_x + name_width, 850)], fill='#d97706', width=4)
        
        # Decorative divider
        divider_y = 1000
        draw.line([(PAGE_WIDTH_PX // 2 - 200, divider_y), (PAGE_WIDTH_PX // 2 - 50, divider_y)], fill='#fcd34d', width=3)
        self.draw_text_centered(draw, "✦", divider_y - 18, self.get_font(48), '#fbbf24', PAGE_WIDTH_PX)
        draw.line([(PAGE_WIDTH_PX // 2 + 50, divider_y), (PAGE_WIDTH_PX // 2 + 200, divider_y)], fill='#fcd34d', width=3)
        
        # Dedication message
        font_quote = self.get_font(48)
        message = dedication_message or '"May every page bring you joy, and every story spark your imagination."'
        lines = self.word_wrap_text(draw, message, font_quote, PAGE_WIDTH_PX - 400)
        
        y_offset = 1200
        for line in lines:
            self.draw_text_centered(draw, line, y_offset, font_quote, '#4b5563', PAGE_WIDTH_PX)
            y_offset += 70
        
        # Signature line for gifter
        font_small = self.get_font(40)
        self.draw_text_centered(draw, "With love from", y_offset + 100, font_small, '#9ca3af', PAGE_WIDTH_PX)
        
        # Line for writing
        sig_width = 500
        sig_x = (PAGE_WIDTH_PX - sig_width) // 2
        draw.line([(sig_x, y_offset + 220), (sig_x + sig_width, y_offset + 220)], fill='#d1d5db', width=2)
        
        # Date line
        self.draw_text_centered(draw, "Date", y_offset + 300, font_small, '#9ca3af', PAGE_WIDTH_PX)
        date_width = 300
        date_x = (PAGE_WIDTH_PX - date_width) // 2
        draw.line([(date_x, y_offset + 400), (date_x + date_width, y_offset + 400)], fill='#d1d5db', width=2)
        
        # Bottom ornament
        self.draw_text_centered(draw, "✦", PAGE_HEIGHT_PX - 200, font_ornament, '#fbbf24', PAGE_WIDTH_PX)
        
        return img
    
    async def create_the_end_page(self, book_title: str) -> Image.Image:
        """Create The End page"""
        img = self.create_gradient_background(
            PAGE_WIDTH_PX, PAGE_HEIGHT_PX,
            (240, 249, 255), (250, 245, 255)
        )
        draw = ImageDraw.Draw(img)
        
        font_title = self.get_font(160, bold=True)
        self.draw_text_centered(draw, "The End", 350, font_title, '#7c3aed', PAGE_WIDTH_PX)
        
        font_stars = self.get_font(48)
        self.draw_text_centered(draw, "✦    ✦    ✦", 550, font_stars, '#a855f7', PAGE_WIDTH_PX)
        
        mascot_img = await self.download_image(BONUS_IMAGES['the_end'])
        if mascot_img:
            frame_size = 700
            frame_x = (PAGE_WIDTH_PX - frame_size) // 2
            frame_y = 700
            
            draw.rounded_rectangle(
                [(frame_x - 20, frame_y - 20), (frame_x + frame_size + 20, frame_y + frame_size + 20)],
                radius=40, fill=(255, 255, 255)
            )
            mascot_img = mascot_img.resize((frame_size, frame_size), Image.Resampling.LANCZOS)
            img.paste(mascot_img, (frame_x, frame_y))
            
            draw.text((frame_x - 80, frame_y + 350), "✨", fill='#fbbf24', font=font_stars)
        
        font_message = self.get_font(52)
        self.draw_text_centered(draw, "But remember, every ending is just", 1550, font_message, '#4b5563', PAGE_WIDTH_PX)
        self.draw_text_centered(draw, "the beginning of a new adventure!", 1630, font_message, '#4b5563', PAGE_WIDTH_PX)
        
        font_small = self.get_font(36)
        self.draw_text_centered(draw, book_title or "", PAGE_HEIGHT_PX - 150, font_small, '#a855f7', PAGE_WIDTH_PX)
        
        return img
    
    async def create_thank_you_page(self, child_name: str) -> Image.Image:
        """Create Thank You page"""
        img = self.create_gradient_background(
            PAGE_WIDTH_PX, PAGE_HEIGHT_PX,
            (253, 242, 248), (250, 245, 255)
        )
        draw = ImageDraw.Draw(img)
        
        font_heart = self.get_font(64)
        draw.text((200, 200), "♥", fill='#f9a8d4', font=font_heart)
        draw.text((PAGE_WIDTH_PX - 280, 350), "♥", fill='#c4b5fd', font=font_heart)
        draw.text((300, PAGE_HEIGHT_PX - 400), "♥", fill='#fecdd3', font=font_heart)
        
        font_title = self.get_font(96, bold=True)
        font_subtitle = self.get_font(64)
        
        self.draw_text_centered(draw, "Thank You", 300, font_title, '#7c3aed', PAGE_WIDTH_PX)
        self.draw_text_centered(draw, "for reading!", 420, font_subtitle, '#ec4899', PAGE_WIDTH_PX)
        
        mascot_img = await self.download_image(BONUS_IMAGES['thank_you'])
        if mascot_img:
            center_x = PAGE_WIDTH_PX // 2
            center_y = 1050
            radius = 350
            
            draw.ellipse((center_x - radius - 15, center_y - radius - 15,
                         center_x + radius + 15, center_y + radius + 15), fill=(244, 194, 194))
            draw.ellipse((center_x - radius - 8, center_y - radius - 8,
                         center_x + radius + 8, center_y + radius + 8), fill=(196, 181, 253))
            self.draw_circular_image(img, mascot_img, center_x, center_y, radius)
            
            wave_font = self.get_font(72)
            draw.text((center_x + radius - 50, center_y - radius + 50), "👋", font=wave_font)
        
        font_message = self.get_font(52)
        name_text = f"{child_name}, you're" if child_name else "You're"
        self.draw_text_centered(draw, name_text, 1550, font_message, '#4b5563', PAGE_WIDTH_PX)
        self.draw_text_centered(draw, "an amazing reader!", 1630, font_message, '#4b5563', PAGE_WIDTH_PX)
        
        font_cta = self.get_font(48)
        self.draw_text_centered(draw, "Come back soon for more adventures!", 1750, font_cta, '#a855f7', PAGE_WIDTH_PX)
        
        font_footer = self.get_font(36)
        self.draw_text_centered(draw, "Made with ♥ on Azories.com", PAGE_HEIGHT_PX - 150, font_footer, '#9ca3af', PAGE_WIDTH_PX)
        
        return img
    
    async def create_certificate_page(self, child_name: str, book_title: str) -> Image.Image:
        """Create Certificate page - personalized achievement certificate"""
        img = self.create_gradient_background(
            PAGE_WIDTH_PX, PAGE_HEIGHT_PX,
            (254, 252, 232), (254, 249, 195)
        )
        draw = ImageDraw.Draw(img)
        
        # Ornate borders
        draw.rectangle([(60, 60), (PAGE_WIDTH_PX - 60, PAGE_HEIGHT_PX - 60)], outline=(217, 119, 6), width=12)
        draw.rectangle([(90, 90), (PAGE_WIDTH_PX - 90, PAGE_HEIGHT_PX - 90)], outline=(251, 191, 36), width=6)
        draw.rectangle([(115, 115), (PAGE_WIDTH_PX - 115, PAGE_HEIGHT_PX - 115)], outline=(253, 230, 138), width=3)
        
        # Corner ornaments
        font_ornament = self.get_font(72)
        draw.text((130, 130), "❧", fill='#d97706', font=font_ornament)
        draw.text((PAGE_WIDTH_PX - 200, 130), "❧", fill='#d97706', font=font_ornament)
        draw.text((130, PAGE_HEIGHT_PX - 200), "❧", fill='#d97706', font=font_ornament)
        draw.text((PAGE_WIDTH_PX - 200, PAGE_HEIGHT_PX - 200), "❧", fill='#d97706', font=font_ornament)
        
        font_small = self.get_font(40)
        font_title = self.get_font(100, bold=True)
        font_medium = self.get_font(52)
        font_name = self.get_font(85, bold=True)
        font_book = self.get_font(56)
        
        # Header
        self.draw_text_centered(draw, "CERTIFICATE OF", 300, font_small, '#92400e', PAGE_WIDTH_PX)
        self.draw_text_centered(draw, "Achievement", 420, font_title, '#92400e', PAGE_WIDTH_PX)
        
        # Stars decoration
        font_stars_small = self.get_font(48)
        self.draw_text_centered(draw, "★  ★  ★", 550, font_stars_small, '#fbbf24', PAGE_WIDTH_PX)
        
        # Main content
        self.draw_text_centered(draw, "This certifies that", 680, font_medium, '#4b5563', PAGE_WIDTH_PX)
        self.draw_text_centered(draw, child_name or "________________", 800, font_name, '#b45309', PAGE_WIDTH_PX)
        
        # Underline for name
        name_width = max(len(child_name or "________________") * 45, 600)
        line_x = (PAGE_WIDTH_PX - name_width) // 2
        draw.line([(line_x, 910), (line_x + name_width, 910)], fill='#d97706', width=4)
        
        self.draw_text_centered(draw, "has successfully completed reading", 1000, font_medium, '#4b5563', PAGE_WIDTH_PX)
        
        # Book title with quotes
        title_text = f'"{book_title or "This Wonderful Story"}"'
        if len(title_text) > 30:
            # Smaller font for long titles
            font_book_small = self.get_font(48)
            self.draw_text_centered(draw, title_text, 1110, font_book_small, '#7c3aed', PAGE_WIDTH_PX)
        else:
            self.draw_text_centered(draw, title_text, 1100, font_book, '#7c3aed', PAGE_WIDTH_PX)
        
        # Achievement message
        font_achievement = self.get_font(44)
        self.draw_text_centered(draw, "and has demonstrated wonderful", 1250, font_achievement, '#6b7280', PAGE_WIDTH_PX)
        self.draw_text_centered(draw, "reading skills and imagination!", 1320, font_achievement, '#6b7280', PAGE_WIDTH_PX)
        
        # Date
        date_str = datetime.now().strftime("%B %d, %Y")
        self.draw_text_centered(draw, date_str, 1480, font_small, '#6b7280', PAGE_WIDTH_PX)
        
        # Signature line
        sig_label_font = self.get_font(32)
        self.draw_text_centered(draw, "Presented by", 1600, sig_label_font, '#9ca3af', PAGE_WIDTH_PX)
        sig_width = 500
        sig_x = (PAGE_WIDTH_PX - sig_width) // 2
        draw.line([(sig_x, 1720), (sig_x + sig_width, 1720)], fill='#d1d5db', width=2)
        
        # Stars at bottom
        font_stars = self.get_font(64)
        self.draw_text_centered(draw, "★  ★  ★  ★  ★", 1850, font_stars, '#fbbf24', PAGE_WIDTH_PX)
        
        return img
    
    async def create_about_azories_page(self) -> Image.Image:
        """Create About Azories page"""
        img = self.create_gradient_background(
            PAGE_WIDTH_PX, PAGE_HEIGHT_PX,
            (109, 40, 217), (79, 70, 229)
        )
        draw = ImageDraw.Draw(img)
        
        font_star = self.get_font(120)
        draw.text((150, 200), "✦", fill='#ffffff20', font=font_star)
        draw.text((PAGE_WIDTH_PX - 350, 400), "✦", fill='#ffffff15', font=self.get_font(80))
        draw.text((200, PAGE_HEIGHT_PX - 600), "✦", fill='#ffffff20', font=self.get_font(100))
        
        font_small = self.get_font(72, bold=True)
        font_title = self.get_font(120, bold=True)
        
        self.draw_text_centered(draw, "About", 300, font_small, '#ffffff', PAGE_WIDTH_PX)
        self.draw_text_centered(draw, "Azories", 420, font_title, '#ffffff', PAGE_WIDTH_PX)
        
        mascot_img = await self.download_image(BONUS_IMAGES['about'])
        if mascot_img:
            frame_size = 550
            frame_x = (PAGE_WIDTH_PX - frame_size) // 2
            frame_y = 650
            
            draw.rounded_rectangle(
                [(frame_x - 15, frame_y - 15), (frame_x + frame_size + 15, frame_y + frame_size + 15)],
                radius=30, fill=(255, 255, 255, 50)
            )
            mascot_img = mascot_img.resize((frame_size, frame_size), Image.Resampling.LANCZOS)
            img.paste(mascot_img, (frame_x, frame_y))
        
        font_desc = self.get_font(44)
        desc_lines = [
            "Azories creates personalized AI-powered",
            "stories that bring imagination to life.",
            "Every story is unique, just like you!"
        ]
        y_offset = 1350
        for line in desc_lines:
            self.draw_text_centered(draw, line, y_offset, font_desc, '#e9d5ff', PAGE_WIDTH_PX)
            y_offset += 65
        
        font_features = self.get_font(36)
        self.draw_text_centered(draw, "✦ AI-Powered    ✦ Personalized    ✦ Magical", 1600, font_features, '#c4b5fd', PAGE_WIDTH_PX)
        
        font_url = self.get_font(40)
        self.draw_text_centered(draw, "www.azories.com", PAGE_HEIGHT_PX - 150, font_url, '#a5b4fc', PAGE_WIDTH_PX)
        
        return img
    
    async def create_meet_azora_page(self) -> Image.Image:
        """Create Meet Azora page"""
        img = self.create_gradient_background(
            PAGE_WIDTH_PX, PAGE_HEIGHT_PX,
            (255, 241, 242), (250, 245, 255)
        )
        draw = ImageDraw.Draw(img)
        
        font_ornament = self.get_font(48)
        ornament_y = 150
        draw.line([(PAGE_WIDTH_PX // 2 - 300, ornament_y), (PAGE_WIDTH_PX // 2 - 80, ornament_y)], fill='#fda4af', width=3)
        self.draw_text_centered(draw, "✦", ornament_y - 20, font_ornament, '#fb7185', PAGE_WIDTH_PX)
        draw.line([(PAGE_WIDTH_PX // 2 + 80, ornament_y), (PAGE_WIDTH_PX // 2 + 300, ornament_y)], fill='#fda4af', width=3)
        
        font_meet = self.get_font(72, bold=True)
        font_name = self.get_font(120, bold=True)
        
        self.draw_text_centered(draw, "Meet", 280, font_meet, '#7c3aed', PAGE_WIDTH_PX)
        self.draw_text_centered(draw, "Azora", 410, font_name, '#db2777', PAGE_WIDTH_PX)
        
        mascot_img = await self.download_image(BONUS_IMAGES['meet_azora'])
        if mascot_img:
            frame_size = 650
            frame_x = (PAGE_WIDTH_PX - frame_size) // 2
            frame_y = 600
            
            draw.rounded_rectangle(
                [(frame_x - 15, frame_y - 15), (frame_x + frame_size + 15, frame_y + frame_size + 15)],
                radius=30, fill=(253, 164, 175)
            )
            draw.rounded_rectangle(
                [(frame_x - 8, frame_y - 8), (frame_x + frame_size + 8, frame_y + frame_size + 8)],
                radius=25, fill=(196, 181, 253)
            )
            draw.rounded_rectangle(
                [(frame_x, frame_y), (frame_x + frame_size, frame_y + frame_size)],
                radius=20, fill=(255, 255, 255)
            )
            
            mascot_img = mascot_img.resize((frame_size - 20, frame_size - 20), Image.Resampling.LANCZOS)
            img.paste(mascot_img, (frame_x + 10, frame_y + 10))
            
            draw.text((frame_x - 50, frame_y - 40), "✨", fill='#fbbf24', font=self.get_font(56))
        
        font_desc = self.get_font(46)
        desc_lines = [
            "Hi! I'm Azora, your magical story guide.",
            "I love helping kids discover amazing adventures",
            "through the power of imagination and reading!"
        ]
        y_offset = 1400
        for line in desc_lines:
            self.draw_text_centered(draw, line, y_offset, font_desc, '#4b5563', PAGE_WIDTH_PX)
            y_offset += 65
        
        font_cta = self.get_font(40)
        self.draw_text_centered(draw, "Ready for your next adventure?", 1650, font_cta, '#a855f7', PAGE_WIDTH_PX)
        
        draw.line([(PAGE_WIDTH_PX // 2 - 300, PAGE_HEIGHT_PX - 150), (PAGE_WIDTH_PX // 2 - 80, PAGE_HEIGHT_PX - 150)], fill='#c4b5fd', width=3)
        self.draw_text_centered(draw, "♥", PAGE_HEIGHT_PX - 170, font_ornament, '#a855f7', PAGE_WIDTH_PX)
        draw.line([(PAGE_WIDTH_PX // 2 + 80, PAGE_HEIGHT_PX - 150), (PAGE_WIDTH_PX // 2 + 300, PAGE_HEIGHT_PX - 150)], fill='#c4b5fd', width=3)
        
        return img
    
    async def create_filler_page(self, image_key: str) -> Image.Image:
        """Create a filler page with mascot image"""
        img = self.create_gradient_background(
            PAGE_WIDTH_PX, PAGE_HEIGHT_PX,
            (250, 245, 255), (255, 250, 253)
        )
        draw = ImageDraw.Draw(img)
        
        mascot_img = await self.download_image(BONUS_IMAGES.get(image_key, BONUS_IMAGES['filler_1']))
        if mascot_img:
            # Large centered image
            margin = 150
            available_width = PAGE_WIDTH_PX - (margin * 2)
            available_height = PAGE_HEIGHT_PX - (margin * 2)
            
            img_aspect = mascot_img.width / mascot_img.height
            page_aspect = available_width / available_height
            
            if img_aspect > page_aspect:
                new_width = available_width
                new_height = int(available_width / img_aspect)
            else:
                new_height = available_height
                new_width = int(available_height * img_aspect)
            
            mascot_img = mascot_img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            x = (PAGE_WIDTH_PX - new_width) // 2
            y = (PAGE_HEIGHT_PX - new_height) // 2
            
            # Subtle frame
            draw.rounded_rectangle(
                [(x - 15, y - 15), (x + new_width + 15, y + new_height + 15)],
                radius=20, fill=(255, 255, 255)
            )
            img.paste(mascot_img, (x, y))
        
        # Small branding
        font_footer = self.get_font(32)
        self.draw_text_centered(draw, "Azories.com", PAGE_HEIGHT_PX - 100, font_footer, '#c4b5fd', PAGE_WIDTH_PX)
        
        return img
    
    async def create_blank_page(self, page_num: int, total_blank: int) -> Image.Image:
        """Create a blank page for notes/drawings with subtle decoration"""
        # Cream paper background
        img = Image.new('RGB', (PAGE_WIDTH_PX, PAGE_HEIGHT_PX), (253, 251, 247))
        draw = ImageDraw.Draw(img)
        
        # Subtle decorative border
        margin = 100
        border_color = (230, 228, 224)
        draw.rectangle(
            [(margin, margin), (PAGE_WIDTH_PX - margin, PAGE_HEIGHT_PX - margin)],
            outline=border_color, width=2
        )
        
        # Corner decorations
        corner_size = 40
        corners = [
            (margin, margin),
            (PAGE_WIDTH_PX - margin - corner_size, margin),
            (margin, PAGE_HEIGHT_PX - margin - corner_size),
            (PAGE_WIDTH_PX - margin - corner_size, PAGE_HEIGHT_PX - margin - corner_size)
        ]
        for cx, cy in corners:
            draw.line([(cx, cy), (cx + corner_size, cy)], fill='#c4b5fd', width=3)
            draw.line([(cx, cy), (cx, cy + corner_size)], fill='#c4b5fd', width=3)
        
        # Add subtle lines for writing (optional - like notebook paper)
        line_start_y = 400
        line_spacing = 80
        line_color = (240, 238, 234)
        
        y = line_start_y
        while y < PAGE_HEIGHT_PX - 300:
            draw.line([(margin + 50, y), (PAGE_WIDTH_PX - margin - 50, y)], fill=line_color, width=1)
            y += line_spacing
        
        # Header text based on page number
        font_header = self.get_font(48)
        font_small = self.get_font(32)
        
        if page_num == 1:
            self.draw_text_centered(draw, "My Notes & Drawings", 200, font_header, '#9ca3af', PAGE_WIDTH_PX)
            self.draw_text_centered(draw, "Draw your favorite scene or write about the story!", 280, font_small, '#c4b5fd', PAGE_WIDTH_PX)
        elif page_num == 2:
            self.draw_text_centered(draw, "More Adventures", 200, font_header, '#9ca3af', PAGE_WIDTH_PX)
            self.draw_text_centered(draw, "What happens next? Write your own ending!", 280, font_small, '#c4b5fd', PAGE_WIDTH_PX)
        else:
            # Decorative star
            font_star = self.get_font(64)
            self.draw_text_centered(draw, "✦", 200, font_star, '#e9d5ff', PAGE_WIDTH_PX)
        
        # Small footer
        font_footer = self.get_font(28)
        self.draw_text_centered(draw, "Azories.com", PAGE_HEIGHT_PX - 80, font_footer, '#d1d5db', PAGE_WIDTH_PX)
        
        return img
    
    async def create_cover_page(self, book: dict, is_back: bool = False) -> Image.Image:
        """Create front or back cover page"""
        img = Image.new('RGB', (PAGE_WIDTH_PX, PAGE_HEIGHT_PX), (255, 255, 255))
        draw = ImageDraw.Draw(img)
        
        if is_back:
            cover_url = book.get('back_cover_image')
            gradient_start = book.get('cover_gradient_start', '#667eea')
            gradient_end = book.get('cover_gradient_end', '#764ba2')
            
            if cover_url:
                cover_img = await self.download_image(cover_url)
                if cover_img:
                    cover_img = cover_img.resize((PAGE_WIDTH_PX, PAGE_HEIGHT_PX), Image.Resampling.LANCZOS)
                    img.paste(cover_img, (0, 0))
            else:
                start_rgb = self.hex_to_rgb(gradient_start)
                end_rgb = self.hex_to_rgb(gradient_end)
                img = self.create_gradient_background(PAGE_WIDTH_PX, PAGE_HEIGHT_PX, end_rgb, start_rgb)
                draw = ImageDraw.Draw(img)
                
                font_desc = self.get_font(44)
                description = book.get('back_cover_text') or book.get('description', 'Thank you for reading!')
                lines = self.word_wrap_text(draw, description, font_desc, PAGE_WIDTH_PX - 400)
                
                y_offset = PAGE_HEIGHT_PX // 2 - (len(lines) * 60) // 2
                for line in lines:
                    self.draw_text_centered(draw, line, y_offset, font_desc, '#ffffff', PAGE_WIDTH_PX)
                    y_offset += 60
                
                if book.get('age_rating'):
                    font_small = self.get_font(36)
                    self.draw_text_centered(draw, book['age_rating'], PAGE_HEIGHT_PX - 200, font_small, '#ffffffcc', PAGE_WIDTH_PX)
        else:
            cover_url = book.get('cover_image')
            
            if cover_url:
                cover_img = await self.download_image(cover_url)
                if cover_img:
                    cover_img = cover_img.resize((PAGE_WIDTH_PX, PAGE_HEIGHT_PX), Image.Resampling.LANCZOS)
                    img.paste(cover_img, (0, 0))
            else:
                gradient_start = book.get('cover_gradient_start', '#667eea')
                gradient_end = book.get('cover_gradient_end', '#764ba2')
                start_rgb = self.hex_to_rgb(gradient_start)
                end_rgb = self.hex_to_rgb(gradient_end)
                img = self.create_gradient_background(PAGE_WIDTH_PX, PAGE_HEIGHT_PX, start_rgb, end_rgb)
                draw = ImageDraw.Draw(img)
                
                font_title = self.get_font(96, bold=True)
                font_author = self.get_font(48)
                
                self.draw_text_centered(draw, book.get('title', 'My Story'), PAGE_HEIGHT_PX // 2 - 100, font_title, '#ffffff', PAGE_WIDTH_PX)
                self.draw_text_centered(draw, book.get('author_name', ''), PAGE_HEIGHT_PX // 2 + 50, font_author, '#ffffffcc', PAGE_WIDTH_PX)
        
        return img

    async def generate_print_pdf(self, book: dict, pages: list, 
                                  child_name: str = None, 
                                  dedication_message: str = None,
                                  output_path: str = None) -> str:
        """Generate complete print-ready PDF with spread layout
        
        Simplified structure (personalizable pages only):
        1. Front Cover
        2. Welcome Page (personalized with child name & book title)
        3. Dedication Page (personalized "This book belongs to...")
        4. Story Spreads (image left, text right)
        5. Certificate Page (personalized achievement certificate)
        6. Blank pages (for notes/drawings if needed)
        7. Back Cover
        """
        if not output_path:
            output_path = tempfile.mktemp(suffix='.pdf')
        
        c = canvas.Canvas(output_path, pagesize=(PAGE_WIDTH_PT, PAGE_HEIGHT_PT))
        
        book_title = book.get('title', 'My Story')
        child_name = child_name or book.get('main_character_name') or book.get('child_name') or 'Little Reader'
        
        all_images = []
        
        logger.info("Generating print PDF (8x10 portrait with spreads)...")
        
        # 1. Front Cover
        logger.info("Creating front cover...")
        cover_img = await self.create_cover_page(book, is_back=False)
        all_images.append(('Front Cover', cover_img))
        
        # 2. Welcome Page (personalized)
        logger.info("Creating welcome page...")
        welcome_img = await self.create_welcome_page(book_title, child_name)
        all_images.append(('Welcome', welcome_img))
        
        # 3. Dedication Page (personalized)
        logger.info("Creating dedication page...")
        dedication_img = await self.create_dedication_page(child_name, dedication_message)
        all_images.append(('Dedication', dedication_img))
        
        # 4. Story Spreads (Left = Image, Right = Text)
        story_pages = [p for p in pages if not p.get('isBackCover')]
        for i, page in enumerate(story_pages):
            logger.info(f"Creating story spread {i + 1}/{len(story_pages)}...")
            
            # Left page - Image
            img_page = await self.create_story_image_page(page)
            all_images.append((f'Story {i+1} Image', img_page))
            
            # Right page - Text
            text_page = await self.create_story_text_page(page, i + 1)
            all_images.append((f'Story {i+1} Text', text_page))
        
        # 5. Certificate Page (personalized)
        logger.info("Creating certificate page...")
        cert_img = await self.create_certificate_page(child_name, book_title)
        all_images.append(('Certificate', cert_img))
        
        # 6. Calculate blank pages needed for even count (minimum 24 for binding)
        current_count = len(all_images) + 1  # +1 for back cover
        
        # Need even page count, minimum 24 for perfect binding
        target_pages = max(24, current_count)
        if target_pages % 2 != 0:
            target_pages += 1
        
        blank_needed = target_pages - current_count
        logger.info(f"Adding {blank_needed} blank pages for notes/drawings...")
        
        for i in range(blank_needed):
            blank_img = await self.create_blank_page(i + 1, blank_needed)
            all_images.append((f'Notes {i+1}', blank_img))
        
        # 7. Back Cover (last page)
        logger.info("Creating back cover...")
        back_cover_img = await self.create_cover_page(book, is_back=True)
        all_images.append(('Back Cover', back_cover_img))
        
        # Add all images to PDF
        for name, img in all_images:
            img_buffer = io.BytesIO()
            img.save(img_buffer, format='JPEG', quality=95, dpi=(DPI, DPI))
            img_buffer.seek(0)
            
            c.drawImage(
                ImageReader(img_buffer),
                0, 0,
                width=PAGE_WIDTH_PT,
                height=PAGE_HEIGHT_PT
            )
            c.showPage()
        
        c.save()
        
        logger.info(f"PDF generated successfully: {output_path}")
        logger.info(f"Total pages: {len(all_images)}")
        
        return output_path


# Singleton instance
pdf_generator = PrintPDFGenerator()


async def generate_test_pdf(book_id: str, db) -> dict:
    """Generate a test PDF for a specific book"""
    book = await db.books.find_one({"id": book_id}, {"_id": 0})
    if not book:
        raise ValueError(f"Book not found: {book_id}")
    
    pages = book.get('pages', [])
    if not pages:
        pages_cursor = db.pages.find({"book_id": book_id}, {"_id": 0}).sort("sequence", 1)
        pages = await pages_cursor.to_list(length=100)
    
    output_path = f"/tmp/print_test_{book_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    
    await pdf_generator.generate_print_pdf(
        book=book,
        pages=pages,
        output_path=output_path
    )
    
    file_size = os.path.getsize(output_path)
    story_pages = len([p for p in pages if not p.get('isBackCover')])
    
    # Calculate total: cover + welcome + dedication + (story_pages * 2 for spreads) + 5 bonus + fillers + back cover
    base_pages = 1 + 1 + 1 + (story_pages * 2) + 5 + 1  # 29 for 10 stories
    total_pages = max(24, base_pages)
    if total_pages % 2 != 0:
        total_pages += 1
    
    return {
        "path": output_path,
        "filename": os.path.basename(output_path),
        "size_bytes": file_size,
        "size_mb": round(file_size / (1024 * 1024), 2),
        "book_title": book.get('title'),
        "total_story_pages": story_pages,
        "total_pdf_pages": total_pages,
        "format": "8x10 Portrait",
        "layout": "Spread (Image left, Text right)"
    }
