"""
Print PDF Generator - Creates print-ready PDFs for Gelato Print on Demand

PDF Specifications:
- Page size: 8x8 inches (204.12mm x 204.12mm)
- Resolution: 300 DPI
- Pixel dimensions: 2400 x 2400 pixels per page
- Bleed: 3mm on all sides (optional)
- Format: PDF/X-1a compatible

Page Order:
1. Front Cover (from book)
2. Welcome Page (bonus)
3. Dedication Page (bonus)
4. Story Content Pages (from book)
5. The End Page (bonus)
6. Thank You Page (bonus)
7. Certificate Page (bonus)
8. About Azories Page (bonus)
9. Meet Azora Page (bonus)
10. Back Cover (from book, if exists)
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
from reportlab.lib.colors import HexColor, Color
import tempfile
import logging

logger = logging.getLogger(__name__)

# Page dimensions for 8x8 inch at 300 DPI
PAGE_WIDTH_INCHES = 8
PAGE_HEIGHT_INCHES = 8
DPI = 300
PAGE_WIDTH_PX = int(PAGE_WIDTH_INCHES * DPI)  # 2400 pixels
PAGE_HEIGHT_PX = int(PAGE_HEIGHT_INCHES * DPI)  # 2400 pixels

# ReportLab uses points (72 points = 1 inch)
PAGE_WIDTH_PT = PAGE_WIDTH_INCHES * inch  # 576 points
PAGE_HEIGHT_PT = PAGE_HEIGHT_INCHES * inch  # 576 points

# Bonus page mascot images
BONUS_IMAGES = {
    'welcome': 'https://customer-assets.emergentagent.com/job_5f7e2b9e-d2a4-4bf3-b6c6-aac66cbef904/artifacts/60k2xrwp_Azora%20Mascot%20Main.jpg',
    'dedication': 'https://customer-assets.emergentagent.com/job_5f7e2b9e-d2a4-4bf3-b6c6-aac66cbef904/artifacts/ve63p3ok_Azora%20Mascot%202.jpg',
    'the_end': 'https://customer-assets.emergentagent.com/job_5f7e2b9e-d2a4-4bf3-b6c6-aac66cbef904/artifacts/k0b04d29_Azora%20Mascot%201.jpg',
    'thank_you': 'https://res.cloudinary.com/dlbmjqmoy/image/upload/e_background_removal/v1772279875/azories/mascot/azora_waving_hello.png',
    'about': 'https://customer-assets.emergentagent.com/job_5f7e2b9e-d2a4-4bf3-b6c6-aac66cbef904/artifacts/dlulgnzy_Azora_Mascot.jpg',
    'certificate': 'https://customer-assets.emergentagent.com/job_5f7e2b9e-d2a4-4bf3-b6c6-aac66cbef904/artifacts/e45x5iez_azora%20library.png',
    'meet_azora': 'https://customer-assets.emergentagent.com/job_5f7e2b9e-d2a4-4bf3-b6c6-aac66cbef904/artifacts/o1xvfgto_azora%20librbary%201.png',
}

# Colors
PURPLE_PRIMARY = '#7c3aed'
PURPLE_LIGHT = '#a78bfa'
PINK_LIGHT = '#f9a8d4'
AMBER_PRIMARY = '#d97706'
AMBER_LIGHT = '#fde68a'


class PrintPDFGenerator:
    """Generates print-ready PDFs for photobooks"""
    
    def __init__(self):
        self.image_cache = {}
        
    async def download_image(self, url: str) -> Image.Image:
        """Download and cache an image from URL"""
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
                            center_x: int, center_y: int, radius: int,
                            border_color: tuple = None, border_width: int = 0):
        """Draw an image in a circular frame"""
        # Resize image to fit circle
        img = img.resize((radius * 2, radius * 2), Image.Resampling.LANCZOS)
        
        # Create circular mask
        mask = Image.new('L', (radius * 2, radius * 2), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.ellipse((0, 0, radius * 2 - 1, radius * 2 - 1), fill=255)
        
        # Apply mask to image
        circular_img = Image.new('RGBA', (radius * 2, radius * 2), (255, 255, 255, 0))
        circular_img.paste(img, (0, 0))
        circular_img.putalpha(mask)
        
        # Draw border if specified
        if border_color and border_width > 0:
            draw = ImageDraw.Draw(base)
            draw.ellipse(
                (center_x - radius - border_width, center_y - radius - border_width,
                 center_x + radius + border_width, center_y + radius + border_width),
                fill=border_color
            )
        
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
        
        # Fallback to default
        return ImageFont.load_default()
    
    async def create_welcome_page(self, book_title: str, child_name: str) -> Image.Image:
        """Create the Welcome bonus page"""
        # Create gradient background
        img = self.create_gradient_background(
            PAGE_WIDTH_PX, PAGE_HEIGHT_PX,
            (250, 245, 255),  # Light purple
            (255, 250, 253)   # Light pink
        )
        draw = ImageDraw.Draw(img)
        
        # Decorative corner flourishes
        corner_color = (196, 181, 253)  # Purple-300
        line_width = 12
        corner_size = 200
        
        # Top-left
        draw.line([(60, 60), (60, 60 + corner_size)], fill=corner_color, width=line_width)
        draw.line([(60, 60), (60 + corner_size, 60)], fill=corner_color, width=line_width)
        # Top-right
        draw.line([(PAGE_WIDTH_PX - 60, 60), (PAGE_WIDTH_PX - 60 - corner_size, 60)], fill=corner_color, width=line_width)
        draw.line([(PAGE_WIDTH_PX - 60, 60), (PAGE_WIDTH_PX - 60, 60 + corner_size)], fill=corner_color, width=line_width)
        # Bottom-left
        draw.line([(60, PAGE_HEIGHT_PX - 60), (60, PAGE_HEIGHT_PX - 60 - corner_size)], fill=corner_color, width=line_width)
        draw.line([(60, PAGE_HEIGHT_PX - 60), (60 + corner_size, PAGE_HEIGHT_PX - 60)], fill=corner_color, width=line_width)
        # Bottom-right
        draw.line([(PAGE_WIDTH_PX - 60, PAGE_HEIGHT_PX - 60), (PAGE_WIDTH_PX - 60 - corner_size, PAGE_HEIGHT_PX - 60)], fill=corner_color, width=line_width)
        draw.line([(PAGE_WIDTH_PX - 60, PAGE_HEIGHT_PX - 60), (PAGE_WIDTH_PX - 60, PAGE_HEIGHT_PX - 60 - corner_size)], fill=corner_color, width=line_width)
        
        # Header text
        font_small = self.get_font(48)
        font_title = self.get_font(96, bold=True)
        font_medium = self.get_font(56)
        font_name = self.get_font(72, bold=True)
        
        self.draw_text_centered(draw, "A MAGICAL STORY", 200, font_small, '#7c3aed', PAGE_WIDTH_PX)
        
        # Book title
        self.draw_text_centered(draw, book_title or "Your Story", 280, font_title, '#1f2937', PAGE_WIDTH_PX)
        
        # Created for text
        self.draw_text_centered(draw, "Created especially for", 420, font_medium, '#a855f7', PAGE_WIDTH_PX)
        self.draw_text_centered(draw, child_name or "You", 500, font_name, '#7c3aed', PAGE_WIDTH_PX)
        
        # Download and draw mascot image in circular frame
        mascot_img = await self.download_image(BONUS_IMAGES['welcome'])
        if mascot_img:
            center_x = PAGE_WIDTH_PX // 2
            center_y = 1050
            radius = 320
            
            # Draw border circle
            draw.ellipse(
                (center_x - radius - 20, center_y - radius - 20,
                 center_x + radius + 20, center_y + radius + 20),
                fill=(196, 181, 253)
            )
            draw.ellipse(
                (center_x - radius - 10, center_y - radius - 10,
                 center_x + radius + 10, center_y + radius + 10),
                fill=(244, 194, 194)
            )
            
            self.draw_circular_image(img, mascot_img, center_x, center_y, radius)
        
        # Sparkle decorations
        sparkle_font = self.get_font(64)
        draw.text((PAGE_WIDTH_PX - 300, 150), "✦", fill='#fbbf24', font=sparkle_font)
        draw.text((200, 250), "✦", fill='#a855f7', font=sparkle_font)
        draw.text((PAGE_WIDTH_PX - 350, 1500), "✨", fill='#fbbf24', font=sparkle_font)
        
        # Footer
        font_footer = self.get_font(36)
        self.draw_text_centered(draw, "Made with love on Azories.com", PAGE_HEIGHT_PX - 150, font_footer, '#9ca3af', PAGE_WIDTH_PX)
        
        return img
    
    async def create_dedication_page(self, child_name: str, dedication_message: str = None) -> Image.Image:
        """Create the Dedication bonus page"""
        # Cream/amber gradient background
        img = self.create_gradient_background(
            PAGE_WIDTH_PX, PAGE_HEIGHT_PX,
            (254, 252, 232),  # Amber-50
            (255, 255, 255)
        )
        draw = ImageDraw.Draw(img)
        
        # Decorative border
        border_color = (253, 230, 138)  # Amber-200
        draw.rectangle([(80, 80), (PAGE_WIDTH_PX - 80, PAGE_HEIGHT_PX - 80)], outline=border_color, width=8)
        draw.rectangle([(120, 120), (PAGE_WIDTH_PX - 120, PAGE_HEIGHT_PX - 120)], outline=(254, 243, 199), width=4)
        
        # Header ornament
        ornament_color = '#d97706'
        font_ornament = self.get_font(72)
        self.draw_text_centered(draw, "❦", 200, font_ornament, ornament_color, PAGE_WIDTH_PX)
        
        # Title text
        font_subtitle = self.get_font(56)
        font_name = self.get_font(96, bold=True)
        
        self.draw_text_centered(draw, "This book belongs to", 320, font_subtitle, '#4b5563', PAGE_WIDTH_PX)
        self.draw_text_centered(draw, child_name or "________________", 440, font_name, '#b45309', PAGE_WIDTH_PX)
        
        # Download and draw mascot image in rounded frame
        mascot_img = await self.download_image(BONUS_IMAGES['dedication'])
        if mascot_img:
            # Draw white frame background
            frame_x = (PAGE_WIDTH_PX - 500) // 2
            frame_y = 600
            frame_size = 500
            
            draw.rounded_rectangle(
                [(frame_x - 15, frame_y - 15), (frame_x + frame_size + 15, frame_y + frame_size + 15)],
                radius=30, fill=(255, 255, 255)
            )
            
            # Resize and paste image
            mascot_img = mascot_img.resize((frame_size, frame_size), Image.Resampling.LANCZOS)
            img.paste(mascot_img, (frame_x, frame_y))
        
        # Dedication message
        font_quote = self.get_font(44)
        message = dedication_message or '"May every page bring you joy, and every story spark your imagination."'
        # Word wrap for long messages
        max_width = PAGE_WIDTH_PX - 400
        words = message.split()
        lines = []
        current_line = []
        for word in words:
            test_line = ' '.join(current_line + [word])
            bbox = draw.textbbox((0, 0), test_line, font=font_quote)
            if bbox[2] - bbox[0] <= max_width:
                current_line.append(word)
            else:
                lines.append(' '.join(current_line))
                current_line = [word]
        if current_line:
            lines.append(' '.join(current_line))
        
        y_offset = 1200
        for line in lines:
            self.draw_text_centered(draw, line, y_offset, font_quote, '#4b5563', PAGE_WIDTH_PX)
            y_offset += 60
        
        # Footer ornament
        self.draw_text_centered(draw, "✦", PAGE_HEIGHT_PX - 200, font_ornament, '#fbbf24', PAGE_WIDTH_PX)
        
        return img
    
    async def create_the_end_page(self, book_title: str) -> Image.Image:
        """Create The End bonus page"""
        # Sky to purple gradient
        img = self.create_gradient_background(
            PAGE_WIDTH_PX, PAGE_HEIGHT_PX,
            (240, 249, 255),  # Sky-50
            (250, 245, 255)   # Purple-50
        )
        draw = ImageDraw.Draw(img)
        
        # Main heading
        font_title = self.get_font(144, bold=True)
        self.draw_text_centered(draw, "The End", 300, font_title, '#7c3aed', PAGE_WIDTH_PX)
        
        # Decorative stars
        font_stars = self.get_font(48)
        self.draw_text_centered(draw, "✦    ✦    ✦", 480, font_stars, '#a855f7', PAGE_WIDTH_PX)
        
        # Download and draw mascot image
        mascot_img = await self.download_image(BONUS_IMAGES['the_end'])
        if mascot_img:
            frame_x = (PAGE_WIDTH_PX - 600) // 2
            frame_y = 600
            frame_size = 600
            
            # White border
            draw.rounded_rectangle(
                [(frame_x - 20, frame_y - 20), (frame_x + frame_size + 20, frame_y + frame_size + 20)],
                radius=40, fill=(255, 255, 255)
            )
            
            mascot_img = mascot_img.resize((frame_size, frame_size), Image.Resampling.LANCZOS)
            img.paste(mascot_img, (frame_x, frame_y))
            
            # Trail sparkles
            draw.text((frame_x - 80, frame_y + 300), "✨", fill='#fbbf24', font=font_stars)
            draw.text((frame_x - 120, frame_y + 200), "✦", fill='#a855f7', font=self.get_font(32))
        
        # Closing message
        font_message = self.get_font(52)
        self.draw_text_centered(draw, "But remember, every ending is just", 1350, font_message, '#4b5563', PAGE_WIDTH_PX)
        self.draw_text_centered(draw, "the beginning of a new adventure!", 1420, font_message, '#4b5563', PAGE_WIDTH_PX)
        
        # Book title
        font_small = self.get_font(36)
        self.draw_text_centered(draw, book_title or "", PAGE_HEIGHT_PX - 150, font_small, '#a855f7', PAGE_WIDTH_PX)
        
        return img
    
    async def create_thank_you_page(self, child_name: str) -> Image.Image:
        """Create Thank You bonus page"""
        # Pink gradient
        img = self.create_gradient_background(
            PAGE_WIDTH_PX, PAGE_HEIGHT_PX,
            (253, 242, 248),  # Pink-50
            (250, 245, 255)   # Purple-50
        )
        draw = ImageDraw.Draw(img)
        
        # Heart decorations
        font_heart = self.get_font(64)
        draw.text((200, 150), "♥", fill='#f9a8d4', font=font_heart)
        draw.text((PAGE_WIDTH_PX - 280, 250), "♥", fill='#c4b5fd', font=font_heart)
        draw.text((300, PAGE_HEIGHT_PX - 300), "♥", fill='#fecdd3', font=font_heart)
        
        # Title
        font_title = self.get_font(96, bold=True)
        font_subtitle = self.get_font(64)
        
        self.draw_text_centered(draw, "Thank You", 250, font_title, '#7c3aed', PAGE_WIDTH_PX)
        self.draw_text_centered(draw, "for reading!", 370, font_subtitle, '#ec4899', PAGE_WIDTH_PX)
        
        # Waving Azora in circular frame
        mascot_img = await self.download_image(BONUS_IMAGES['thank_you'])
        if mascot_img:
            center_x = PAGE_WIDTH_PX // 2
            center_y = 850
            radius = 300
            
            # Gradient border
            draw.ellipse(
                (center_x - radius - 15, center_y - radius - 15,
                 center_x + radius + 15, center_y + radius + 15),
                fill=(244, 194, 194)
            )
            draw.ellipse(
                (center_x - radius - 8, center_y - radius - 8,
                 center_x + radius + 8, center_y + radius + 8),
                fill=(196, 181, 253)
            )
            
            self.draw_circular_image(img, mascot_img, center_x, center_y, radius)
            
            # Wave emoji
            wave_font = self.get_font(72)
            draw.text((center_x + radius - 50, center_y - radius + 50), "👋", font=wave_font)
        
        # Message
        font_message = self.get_font(52)
        name_text = f"{child_name}, you're" if child_name else "You're"
        self.draw_text_centered(draw, name_text, 1300, font_message, '#4b5563', PAGE_WIDTH_PX)
        self.draw_text_centered(draw, "an amazing reader!", 1370, font_message, '#4b5563', PAGE_WIDTH_PX)
        
        font_cta = self.get_font(48)
        self.draw_text_centered(draw, "Come back soon for more adventures!", 1480, font_cta, '#a855f7', PAGE_WIDTH_PX)
        
        # Footer
        font_footer = self.get_font(36)
        self.draw_text_centered(draw, "Made with ♥ on Azories.com", PAGE_HEIGHT_PX - 150, font_footer, '#9ca3af', PAGE_WIDTH_PX)
        
        return img
    
    async def create_certificate_page(self, child_name: str, book_title: str) -> Image.Image:
        """Create Certificate of Achievement page"""
        # Amber/gold background
        img = self.create_gradient_background(
            PAGE_WIDTH_PX, PAGE_HEIGHT_PX,
            (254, 252, 232),  # Amber-50
            (254, 249, 195)   # Yellow-100
        )
        draw = ImageDraw.Draw(img)
        
        # Ornate triple border
        amber_dark = (217, 119, 6)
        amber_mid = (251, 191, 36)
        amber_light = (253, 230, 138)
        
        draw.rectangle([(60, 60), (PAGE_WIDTH_PX - 60, PAGE_HEIGHT_PX - 60)], outline=amber_dark, width=12)
        draw.rectangle([(90, 90), (PAGE_WIDTH_PX - 90, PAGE_HEIGHT_PX - 90)], outline=amber_mid, width=6)
        draw.rectangle([(115, 115), (PAGE_WIDTH_PX - 115, PAGE_HEIGHT_PX - 115)], outline=amber_light, width=3)
        
        # Corner ornaments
        font_ornament = self.get_font(72)
        ornament = "❧"
        draw.text((130, 130), ornament, fill='#d97706', font=font_ornament)
        draw.text((PAGE_WIDTH_PX - 200, 130), ornament, fill='#d97706', font=font_ornament)
        draw.text((130, PAGE_HEIGHT_PX - 200), ornament, fill='#d97706', font=font_ornament)
        draw.text((PAGE_WIDTH_PX - 200, PAGE_HEIGHT_PX - 200), ornament, fill='#d97706', font=font_ornament)
        
        # Certificate text
        font_small = self.get_font(36)
        font_title = self.get_font(96, bold=True)
        font_medium = self.get_font(48)
        font_name = self.get_font(80, bold=True)
        font_book = self.get_font(56)
        
        self.draw_text_centered(draw, "CERTIFICATE OF", 220, font_small, '#92400e', PAGE_WIDTH_PX)
        self.draw_text_centered(draw, "Achievement", 300, font_title, '#92400e', PAGE_WIDTH_PX)
        
        self.draw_text_centered(draw, "This certifies that", 450, font_medium, '#4b5563', PAGE_WIDTH_PX)
        self.draw_text_centered(draw, child_name or "________________", 540, font_name, '#b45309', PAGE_WIDTH_PX)
        
        # Underline for name
        name_width = len(child_name or "________________") * 40
        line_x = (PAGE_WIDTH_PX - name_width) // 2
        draw.line([(line_x, 640), (line_x + name_width, 640)], fill='#d97706', width=4)
        
        self.draw_text_centered(draw, "has successfully completed reading", 700, font_medium, '#4b5563', PAGE_WIDTH_PX)
        self.draw_text_centered(draw, f'"{book_title or "This Wonderful Story"}"', 780, font_book, '#7c3aed', PAGE_WIDTH_PX)
        
        # Small mascot image
        mascot_img = await self.download_image(BONUS_IMAGES['certificate'])
        if mascot_img:
            center_x = PAGE_WIDTH_PX // 2
            center_y = 1020
            radius = 150
            
            # Border
            draw.ellipse(
                (center_x - radius - 10, center_y - radius - 10,
                 center_x + radius + 10, center_y + radius + 10),
                fill=(251, 191, 36)
            )
            
            self.draw_circular_image(img, mascot_img, center_x, center_y, radius)
        
        # Date
        date_str = datetime.now().strftime("%B %d, %Y")
        self.draw_text_centered(draw, date_str, 1280, font_small, '#6b7280', PAGE_WIDTH_PX)
        
        # Star rating
        stars = "★  ★  ★  ★  ★"
        font_stars = self.get_font(64)
        self.draw_text_centered(draw, stars, 1380, font_stars, '#fbbf24', PAGE_WIDTH_PX)
        
        return img
    
    async def create_about_azories_page(self) -> Image.Image:
        """Create About Azories page"""
        # Purple gradient
        img = self.create_gradient_background(
            PAGE_WIDTH_PX, PAGE_HEIGHT_PX,
            (109, 40, 217),   # Purple-600
            (79, 70, 229)     # Indigo-600
        )
        draw = ImageDraw.Draw(img)
        
        # Background pattern (subtle stars)
        font_star = self.get_font(120)
        draw.text((150, 150), "✦", fill='#ffffff20', font=font_star)
        draw.text((PAGE_WIDTH_PX - 350, 300), "✦", fill='#ffffff15', font=self.get_font(80))
        draw.text((200, PAGE_HEIGHT_PX - 500), "✦", fill='#ffffff20', font=self.get_font(100))
        draw.text((PAGE_WIDTH_PX - 400, PAGE_HEIGHT_PX - 600), "✦", fill='#ffffff15', font=self.get_font(60))
        
        # Title
        font_small = self.get_font(72, bold=True)
        font_title = self.get_font(120, bold=True)
        
        self.draw_text_centered(draw, "About", 200, font_small, '#ffffff', PAGE_WIDTH_PX)
        self.draw_text_centered(draw, "Azories", 300, font_title, '#ffffff', PAGE_WIDTH_PX)
        
        # Mascot image
        mascot_img = await self.download_image(BONUS_IMAGES['about'])
        if mascot_img:
            frame_x = (PAGE_WIDTH_PX - 480) // 2
            frame_y = 500
            frame_size = 480
            
            # White/semi-transparent border
            draw.rounded_rectangle(
                [(frame_x - 15, frame_y - 15), (frame_x + frame_size + 15, frame_y + frame_size + 15)],
                radius=30, fill=(255, 255, 255, 50)
            )
            
            mascot_img = mascot_img.resize((frame_size, frame_size), Image.Resampling.LANCZOS)
            img.paste(mascot_img, (frame_x, frame_y))
        
        # Description
        font_desc = self.get_font(44)
        desc_lines = [
            "Azories creates personalized AI-powered",
            "stories that bring imagination to life.",
            "Every story is unique, just like you!"
        ]
        y_offset = 1100
        for line in desc_lines:
            self.draw_text_centered(draw, line, y_offset, font_desc, '#e9d5ff', PAGE_WIDTH_PX)
            y_offset += 60
        
        # Features
        font_features = self.get_font(36)
        self.draw_text_centered(draw, "✦ AI-Powered    ✦ Personalized    ✦ Magical", 1350, font_features, '#c4b5fd', PAGE_WIDTH_PX)
        
        # Website
        font_url = self.get_font(40)
        self.draw_text_centered(draw, "www.azories.com", PAGE_HEIGHT_PX - 150, font_url, '#a5b4fc', PAGE_WIDTH_PX)
        
        return img
    
    async def create_meet_azora_page(self) -> Image.Image:
        """Create Meet Azora page"""
        # Rose/purple gradient
        img = self.create_gradient_background(
            PAGE_WIDTH_PX, PAGE_HEIGHT_PX,
            (255, 241, 242),  # Rose-50
            (250, 245, 255)   # Purple-50
        )
        draw = ImageDraw.Draw(img)
        
        # Top ornament
        font_ornament = self.get_font(48)
        ornament_y = 120
        draw.line([(PAGE_WIDTH_PX // 2 - 300, ornament_y), (PAGE_WIDTH_PX // 2 - 80, ornament_y)], fill='#fda4af', width=3)
        self.draw_text_centered(draw, "✦", ornament_y - 20, font_ornament, '#fb7185', PAGE_WIDTH_PX)
        draw.line([(PAGE_WIDTH_PX // 2 + 80, ornament_y), (PAGE_WIDTH_PX // 2 + 300, ornament_y)], fill='#fda4af', width=3)
        
        # Title
        font_meet = self.get_font(72, bold=True)
        font_name = self.get_font(120, bold=True)
        
        self.draw_text_centered(draw, "Meet", 220, font_meet, '#7c3aed', PAGE_WIDTH_PX)
        self.draw_text_centered(draw, "Azora", 340, font_name, '#db2777', PAGE_WIDTH_PX)
        
        # Mascot image in fancy frame
        mascot_img = await self.download_image(BONUS_IMAGES['meet_azora'])
        if mascot_img:
            frame_x = (PAGE_WIDTH_PX - 550) // 2
            frame_y = 500
            frame_size = 550
            
            # Gradient border effect
            draw.rounded_rectangle(
                [(frame_x - 15, frame_y - 15), (frame_x + frame_size + 15, frame_y + frame_size + 15)],
                radius=30, fill=(253, 164, 175)  # Rose-300
            )
            draw.rounded_rectangle(
                [(frame_x - 8, frame_y - 8), (frame_x + frame_size + 8, frame_y + frame_size + 8)],
                radius=25, fill=(196, 181, 253)  # Purple-300
            )
            draw.rounded_rectangle(
                [(frame_x, frame_y), (frame_x + frame_size, frame_y + frame_size)],
                radius=20, fill=(255, 255, 255)
            )
            
            mascot_img = mascot_img.resize((frame_size - 20, frame_size - 20), Image.Resampling.LANCZOS)
            img.paste(mascot_img, (frame_x + 10, frame_y + 10))
            
            # Sparkle accents
            draw.text((frame_x - 50, frame_y - 40), "✨", fill='#fbbf24', font=self.get_font(56))
            draw.text((frame_x + frame_size - 20, frame_y + frame_size - 50), "✦", fill='#a855f7', font=self.get_font(48))
        
        # Description
        font_desc = self.get_font(46)
        desc_lines = [
            "Hi! I'm Azora, your magical story guide.",
            "I love helping kids discover amazing adventures",
            "through the power of imagination and reading!"
        ]
        y_offset = 1150
        for line in desc_lines:
            self.draw_text_centered(draw, line, y_offset, font_desc, '#4b5563', PAGE_WIDTH_PX)
            y_offset += 60
        
        # CTA
        font_cta = self.get_font(40)
        self.draw_text_centered(draw, "Ready for your next adventure?", 1400, font_cta, '#a855f7', PAGE_WIDTH_PX)
        
        # Footer ornament
        draw.line([(PAGE_WIDTH_PX // 2 - 300, PAGE_HEIGHT_PX - 150), (PAGE_WIDTH_PX // 2 - 80, PAGE_HEIGHT_PX - 150)], fill='#c4b5fd', width=3)
        self.draw_text_centered(draw, "♥", PAGE_HEIGHT_PX - 170, font_ornament, '#a855f7', PAGE_WIDTH_PX)
        draw.line([(PAGE_WIDTH_PX // 2 + 80, PAGE_HEIGHT_PX - 150), (PAGE_WIDTH_PX // 2 + 300, PAGE_HEIGHT_PX - 150)], fill='#c4b5fd', width=3)
        
        return img
    
    async def create_story_page(self, page_data: dict, page_number: int) -> Image.Image:
        """Create a story content page with image and text"""
        # Cream paper background
        img = Image.new('RGB', (PAGE_WIDTH_PX, PAGE_HEIGHT_PX), (253, 251, 247))
        draw = ImageDraw.Draw(img)
        
        image_url = page_data.get('image_url')
        text_content = page_data.get('text_content', '')
        chapter_title = page_data.get('chapterTitle')
        is_first_of_chapter = page_data.get('isFirstOfChapter', False)
        
        # Calculate layout
        margin = 100
        content_width = PAGE_WIDTH_PX - (margin * 2)
        
        y_offset = margin
        
        # Chapter header if applicable
        if chapter_title and is_first_of_chapter:
            font_chapter_label = self.get_font(32)
            font_chapter_title = self.get_font(56, bold=True)
            
            chapter_num = page_data.get('chapterNumber', '')
            if chapter_num:
                self.draw_text_centered(draw, f"Chapter {chapter_num}", y_offset, font_chapter_label, '#9ca3af', PAGE_WIDTH_PX)
                y_offset += 50
            
            self.draw_text_centered(draw, chapter_title, y_offset, font_chapter_title, '#1f2937', PAGE_WIDTH_PX)
            y_offset += 100
            
            # Decorative line
            line_width = 200
            draw.line(
                [(PAGE_WIDTH_PX // 2 - line_width // 2, y_offset),
                 (PAGE_WIDTH_PX // 2 + line_width // 2, y_offset)],
                fill='#d1d5db', width=3
            )
            y_offset += 50
        
        # Image section
        if image_url:
            story_img = await self.download_image(image_url)
            if story_img:
                # Image takes up ~55% of page height
                img_height = int((PAGE_HEIGHT_PX - margin * 2) * 0.55)
                img_width = content_width
                
                # Maintain aspect ratio
                aspect = story_img.width / story_img.height
                if aspect > (img_width / img_height):
                    new_width = img_width
                    new_height = int(img_width / aspect)
                else:
                    new_height = img_height
                    new_width = int(img_height * aspect)
                
                story_img = story_img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
                # Center image
                img_x = (PAGE_WIDTH_PX - new_width) // 2
                img.paste(story_img, (img_x, y_offset))
                
                y_offset += new_height + 40
        
        # Text section
        if text_content:
            font_text = self.get_font(42)
            
            # Word wrap text
            max_text_width = content_width - 40
            words = text_content.split()
            lines = []
            current_line = []
            
            for word in words:
                test_line = ' '.join(current_line + [word])
                bbox = draw.textbbox((0, 0), test_line, font=font_text)
                if bbox[2] - bbox[0] <= max_text_width:
                    current_line.append(word)
                else:
                    if current_line:
                        lines.append(' '.join(current_line))
                    current_line = [word]
            if current_line:
                lines.append(' '.join(current_line))
            
            # Draw text lines
            text_x = margin + 20
            line_height = 58
            
            for line in lines:
                if y_offset + line_height > PAGE_HEIGHT_PX - margin - 50:
                    break  # Don't overflow page
                draw.text((text_x, y_offset), line, fill='#1f2937', font=font_text)
                y_offset += line_height
        
        # Page number
        font_page_num = self.get_font(32)
        page_num_text = str(page_number)
        bbox = draw.textbbox((0, 0), page_num_text, font=font_page_num)
        page_num_width = bbox[2] - bbox[0]
        draw.text(
            (PAGE_WIDTH_PX - margin - page_num_width, PAGE_HEIGHT_PX - margin),
            page_num_text, fill='#9ca3af', font=font_page_num
        )
        
        return img
    
    async def create_cover_page(self, book: dict, is_back: bool = False) -> Image.Image:
        """Create front or back cover page"""
        img = Image.new('RGB', (PAGE_WIDTH_PX, PAGE_HEIGHT_PX), (255, 255, 255))
        draw = ImageDraw.Draw(img)
        
        if is_back:
            # Back cover
            cover_url = book.get('back_cover_image')
            gradient_start = book.get('cover_gradient_start', '#667eea')
            gradient_end = book.get('cover_gradient_end', '#764ba2')
            
            if cover_url:
                cover_img = await self.download_image(cover_url)
                if cover_img:
                    cover_img = cover_img.resize((PAGE_WIDTH_PX, PAGE_HEIGHT_PX), Image.Resampling.LANCZOS)
                    img.paste(cover_img, (0, 0))
            else:
                # Gradient background
                start_rgb = self.hex_to_rgb(gradient_start)
                end_rgb = self.hex_to_rgb(gradient_end)
                img = self.create_gradient_background(PAGE_WIDTH_PX, PAGE_HEIGHT_PX, end_rgb, start_rgb)
                draw = ImageDraw.Draw(img)
                
                # Back cover text
                font_desc = self.get_font(44)
                description = book.get('back_cover_text') or book.get('description', 'Thank you for reading!')
                
                # Word wrap
                max_width = PAGE_WIDTH_PX - 400
                words = description.split()
                lines = []
                current_line = []
                for word in words:
                    test_line = ' '.join(current_line + [word])
                    bbox = draw.textbbox((0, 0), test_line, font=font_desc)
                    if bbox[2] - bbox[0] <= max_width:
                        current_line.append(word)
                    else:
                        lines.append(' '.join(current_line))
                        current_line = [word]
                if current_line:
                    lines.append(' '.join(current_line))
                
                y_offset = PAGE_HEIGHT_PX // 2 - (len(lines) * 60) // 2
                for line in lines:
                    self.draw_text_centered(draw, line, y_offset, font_desc, '#ffffff', PAGE_WIDTH_PX)
                    y_offset += 60
                
                # Age rating
                if book.get('age_rating'):
                    font_small = self.get_font(36)
                    self.draw_text_centered(draw, book['age_rating'], PAGE_HEIGHT_PX - 200, font_small, '#ffffffcc', PAGE_WIDTH_PX)
        else:
            # Front cover
            cover_url = book.get('cover_image')
            
            if cover_url:
                cover_img = await self.download_image(cover_url)
                if cover_img:
                    cover_img = cover_img.resize((PAGE_WIDTH_PX, PAGE_HEIGHT_PX), Image.Resampling.LANCZOS)
                    img.paste(cover_img, (0, 0))
            else:
                # Gradient with title
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
        """
        Generate a complete print-ready PDF
        
        Args:
            book: Book data including title, cover, etc.
            pages: List of story pages
            child_name: Name for personalization
            dedication_message: Custom dedication
            output_path: Where to save the PDF
            
        Returns:
            Path to the generated PDF
        """
        if not output_path:
            output_path = tempfile.mktemp(suffix='.pdf')
        
        # Create PDF canvas
        c = canvas.Canvas(output_path, pagesize=(PAGE_WIDTH_PT, PAGE_HEIGHT_PT))
        
        book_title = book.get('title', 'My Story')
        child_name = child_name or book.get('main_character_name') or book.get('child_name') or 'Little Reader'
        
        all_images = []
        
        logger.info("Generating print PDF...")
        
        # 1. Front Cover
        logger.info("Creating front cover...")
        cover_img = await self.create_cover_page(book, is_back=False)
        all_images.append(('Front Cover', cover_img))
        
        # 2. Welcome Page
        logger.info("Creating welcome page...")
        welcome_img = await self.create_welcome_page(book_title, child_name)
        all_images.append(('Welcome', welcome_img))
        
        # 3. Dedication Page
        logger.info("Creating dedication page...")
        dedication_img = await self.create_dedication_page(child_name, dedication_message)
        all_images.append(('Dedication', dedication_img))
        
        # 4. Story Content Pages
        story_pages = [p for p in pages if not p.get('isBackCover')]
        for i, page in enumerate(story_pages):
            logger.info(f"Creating story page {i + 1}/{len(story_pages)}...")
            story_img = await self.create_story_page(page, i + 1)
            all_images.append((f'Page {i + 1}', story_img))
        
        # 5. The End Page
        logger.info("Creating 'The End' page...")
        end_img = await self.create_the_end_page(book_title)
        all_images.append(('The End', end_img))
        
        # 6. Thank You Page
        logger.info("Creating thank you page...")
        thanks_img = await self.create_thank_you_page(child_name)
        all_images.append(('Thank You', thanks_img))
        
        # 7. Certificate Page
        logger.info("Creating certificate page...")
        cert_img = await self.create_certificate_page(child_name, book_title)
        all_images.append(('Certificate', cert_img))
        
        # 8. About Azories Page
        logger.info("Creating about page...")
        about_img = await self.create_about_azories_page()
        all_images.append(('About Azories', about_img))
        
        # 9. Meet Azora Page
        logger.info("Creating meet Azora page...")
        meet_img = await self.create_meet_azora_page()
        all_images.append(('Meet Azora', meet_img))
        
        # 10. Back Cover
        logger.info("Creating back cover...")
        back_cover_img = await self.create_cover_page(book, is_back=True)
        all_images.append(('Back Cover', back_cover_img))
        
        # Add all images to PDF
        for name, img in all_images:
            # Convert PIL image to bytes
            img_buffer = io.BytesIO()
            img.save(img_buffer, format='JPEG', quality=95, dpi=(DPI, DPI))
            img_buffer.seek(0)
            
            # Add to PDF
            c.drawImage(
                ImageReader(img_buffer),
                0, 0,
                width=PAGE_WIDTH_PT,
                height=PAGE_HEIGHT_PT
            )
            c.showPage()
        
        # Save PDF
        c.save()
        
        logger.info(f"PDF generated successfully: {output_path}")
        logger.info(f"Total pages: {len(all_images)}")
        
        return output_path


# Singleton instance
pdf_generator = PrintPDFGenerator()


async def generate_test_pdf(book_id: str, db) -> dict:
    """
    Generate a test PDF for a specific book
    
    Returns dict with:
    - path: Path to generated PDF
    - pages: Number of pages
    - size_bytes: File size
    """
    # Fetch book data
    book = await db.books.find_one({"id": book_id}, {"_id": 0})
    if not book:
        raise ValueError(f"Book not found: {book_id}")
    
    # Fetch book pages
    pages_cursor = db.pages.find({"book_id": book_id}, {"_id": 0}).sort("sequence", 1)
    pages = await pages_cursor.to_list(length=100)
    
    # Generate PDF
    output_path = f"/tmp/print_test_{book_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    
    await pdf_generator.generate_print_pdf(
        book=book,
        pages=pages,
        output_path=output_path
    )
    
    # Get file info
    file_size = os.path.getsize(output_path)
    
    return {
        "path": output_path,
        "filename": os.path.basename(output_path),
        "size_bytes": file_size,
        "size_mb": round(file_size / (1024 * 1024), 2),
        "book_title": book.get('title'),
        "total_story_pages": len(pages),
        "total_pdf_pages": len(pages) + 10  # +10 for bonus pages and covers
    }
