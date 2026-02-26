#!/usr/bin/env python3
"""
Picture Book Image Generator - Batch 1 (5 Books)
Generates consistent character images using fal.ai FLUX
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from datetime import datetime

# Set up paths
APP_DIR = Path(__file__).parent
BACKEND_DIR = APP_DIR / 'backend'

# Load environment variables from backend .env
from dotenv import load_dotenv
load_dotenv(BACKEND_DIR / '.env')

# Verify FAL_KEY is loaded
fal_key = os.environ.get('FAL_KEY', '')
if not fal_key:
    print("ERROR: FAL_KEY not found in environment")
    sys.exit(1)
print(f"FAL_KEY loaded: {fal_key[:15]}...{fal_key[-4:]}")

# Add backend to path for imports
sys.path.insert(0, str(BACKEND_DIR))
from fal_service import generate_image_flux

OUTPUT_BASE = APP_DIR / 'content/books/batch1_picture_books'

# Book 1: Luna and the Moonbeam
BOOK1_PROMPTS = {
    "book_id": "book1_luna_moonbeam",
    "title": "Luna and the Moonbeam",
    "style_base": "Soft watercolour children's book illustration, dreamy and calming mood, gentle watercolor washes, soft moonlit glow, pale lavender and midnight blue color palette",
    "character_base": "Luna, a 5-year-old girl with long wavy dark brown hair, big round hazel eyes with long eyelashes, rosy cheeks, light olive skin, wearing soft lavender pajamas with tiny silver stars, holding a cream stuffed bunny named Mr. Hops",
    "images": [
        {"id": "cover_front", "prompt": "Luna floating among twinkling stars reaching out to touch a small glowing golden-silver orb (Moonbeam) with a gentle face, dreamy night sky background with large friendly crescent moon, magical sparkles, space at top for title"},
        {"id": "cover_back", "prompt": "Luna peacefully sleeping in her cozy bed with white wooden frame and lavender quilt with moon patterns, small glowing Moonbeam orb resting on pillow beside her, soft warm glow illuminating the scene, fairy lights visible"},
        {"id": "page_01", "prompt": "Luna sitting in her cozy bedroom on a white wooden bed with lavender quilt, yawning sleepily, moonlight streaming through window, fairy lights above bed, stuffed toys on shelves, pink walls"},
        {"id": "page_02", "prompt": "A tiny glowing golden-silver light orb with a gentle smiling face appearing at Luna's bedroom window, Luna looking surprised and delighted from her bed, moonlit room"},
        {"id": "page_03", "prompt": "The glowing Moonbeam orb with kind eyes and warm smile floating into Luna's bedroom leaving sparkle trail, Luna reaching out her hand to touch it, wonder on her face"},
        {"id": "page_04", "prompt": "Luna and the glowing Moonbeam floating together through soft fluffy lavender and silver clouds, twinkling stars all around them, Luna looking amazed and joyful"},
        {"id": "page_05", "prompt": "Luna sitting on a fluffy cloud with Mr. Hops the stuffed bunny and the glowing Moonbeam, a large friendly smiling crescent moon in background, stars twinkling"},
        {"id": "page_06", "prompt": "Luna yawning contentedly being gently carried back to her bed surrounded by Moonbeam's soft golden glow, dreamy peaceful expression"},
        {"id": "page_07", "prompt": "Luna peacefully asleep in her cozy bed tucked under lavender quilt, Mr. Hops beside her, small glowing Moonbeam resting on pillow, soft magical glow around them"}
    ]
}

# Book 2: Pip the Brave Little Penguin
BOOK2_PROMPTS = {
    "book_id": "book2_pip_penguin", 
    "title": "Pip the Brave Little Penguin",
    "style_base": "Soft watercolour children's book illustration, adventurous and warm mood, gentle watercolor washes, icy blues and warm oranges, snowy Antarctic setting",
    "character_base": "Pip, a small fluffy Emperor penguin chick with soft grey downy feathers, white belly, black head with yellow-orange patches on neck sides, big round expressive dark eyes, small tuft of fluffy down sticking up on head",
    "images": [
        {"id": "cover_front", "prompt": "Pip the small penguin chick diving joyfully into sparkling Antarctic water mid-splash, ice cliffs in background, golden sunlight reflecting on water, splashes and sparkles, space at top for title"},
        {"id": "cover_back", "prompt": "Pip and Otto a friendly brown sea otter with round face and whiskers floating together in calm Antarctic water at sunset, warm orange light, looking friendly at viewer"},
        {"id": "page_01", "prompt": "Pip the small penguin chick standing among much bigger adult Emperor penguins in Antarctic colony, ice and snowy mountains in background, Pip looking small and uncertain"},
        {"id": "page_02", "prompt": "Pip standing nervously at edge of ice cliff looking down at deep blue water, Mama penguin (tall elegant Emperor penguin with golden neck patches) standing nearby supportively"},
        {"id": "page_03", "prompt": "Pip meeting Otto a friendly brown sea otter floating on his back in the water waving, Otto has round face whiskers and lighter brown chest, playful friendly interaction"},
        {"id": "page_04", "prompt": "Pip at edge of ice taking a deep breath, Otto the otter in the water below encouraging and smiling, bright Antarctic daylight"},
        {"id": "page_05", "prompt": "Pip jumping into the water with a small splash, eyes squeezed shut, brave moment, Antarctic ice and blue sky background"},
        {"id": "page_06", "prompt": "Pip swimming underwater with eyes wide with wonder, colorful fish swimming around, crystal clear blue water with light shafts from above, ice visible at surface"},
        {"id": "page_07", "prompt": "Pip and Otto swimming happily together underwater, other penguins joining them, joyful underwater scene with fish"},
        {"id": "page_08", "prompt": "Pip diving gracefully into golden sunset-lit Antarctic water, looking confident and happy, beautiful orange sunset reflecting on ice"}
    ]
}

# Book 3: The Magic Garden
BOOK3_PROMPTS = {
    "book_id": "book3_magic_garden",
    "title": "The Magic Garden", 
    "style_base": "Lush watercolour children's book illustration, whimsical and colorful mood, rich botanical watercolors, warm golden sunlight, vibrant garden colors",
    "character_base": "Maya, a 4-year-old girl with curly black hair in two puffs with colorful hair ties, warm brown skin, bright curious dark brown eyes, gap-toothed smile, round cheeks, wearing yellow sundress with green leaf pattern, green rubber boots, floppy straw sun hat with pink ribbon, carrying small red watering can",
    "images": [
        {"id": "cover_front", "prompt": "Maya standing in lush colorful garden reaching up toward giant sunflower taller than her, surrounded by colorful flowers roses tulips, butterflies flying, magical golden dappled sunlight, space at top for title"},
        {"id": "cover_back", "prompt": "Close-up of Maya holding a pink flower smiling, large iridescent butterfly Flutter with purple-blue-pink wings resting on her straw hat, soft blurred garden background"},
        {"id": "page_01", "prompt": "Maya standing at wooden garden gate looking in with wonder at beautiful colorful garden full of flowers, stone path leading in, butterflies and bees visible"},
        {"id": "page_02", "prompt": "Maya walking through garden with Grandma Rose (warm plump elderly woman with silver-grey hair bun, brown skin, round glasses, floral apron), surrounded by colorful flowers, both smiling"},
        {"id": "page_03", "prompt": "Grandma Rose gently placing a tiny brown seed in Maya's open palm, Maya looking at it with wonder and curiosity, garden background"},
        {"id": "page_04", "prompt": "Maya kneeling digging a small hole in dark rich soil with her hands, Flutter the large iridescent purple-blue-pink butterfly watching nearby, garden setting"},
        {"id": "page_05", "prompt": "Maya watering a patch of soil with her small red watering can, hopeful expression on face, garden around her, waiting for something to grow"},
        {"id": "page_06", "prompt": "Maya looking sad at empty soil patch where nothing has grown yet, Grandma Rose kneeling beside her with comforting arm around her shoulder"},
        {"id": "page_07", "prompt": "Maya gasping with joy discovering a tiny green sprout emerging from soil, Flutter butterfly circling excitedly above, morning light"},
        {"id": "page_08", "prompt": "Maya standing proudly next to a tall beautiful sunflower much taller than her, multiple colorful butterflies around, magical golden light, triumphant happy expression"}
    ]
}

# Book 4: Rosie's Rainbow Day
BOOK4_PROMPTS = {
    "book_id": "book4_rosie_rainbow",
    "title": "Rosie's Rainbow Day",
    "style_base": "Expressive watercolour children's book illustration, emotionally warm mood, expressive watercolor washes with colors reflecting emotions, warm and validating atmosphere",
    "character_base": "Rosie, a 5-year-old girl with straight red bob haircut with bangs, fair freckled skin with freckles across nose and cheeks, big expressive green eyes, small upturned nose, very expressive face, wearing soft grey t-shirt dress with rainbow stripes at bottom, white leggings, red sneakers with white laces",
    "images": [
        {"id": "cover_front", "prompt": "Rosie dancing joyfully with arms outstretched under bright rainbow in sky, colorful emotion splashes and swirls around her, puddles reflecting rainbow colors, joyful expression, space at top for title"},
        {"id": "cover_back", "prompt": "Rosie hugging herself contentedly with soft peaceful smile, pastel rainbow colors softly glowing in background, calm and happy expression"},
        {"id": "page_01", "prompt": "Rosie lying in bed looking grumpy and grey, small grey cloud floating above her head, morning light through window, uncertain expression"},
        {"id": "page_02", "prompt": "Rosie's tower of colorful blocks crashing down, her face turning red with frustration, red swirls and splashes surrounding her, angry expression"},
        {"id": "page_03", "prompt": "Rosie sitting by rainy window looking out sadly, blue tears on her cheeks, blue tones throughout the scene, rain streaking down glass"},
        {"id": "page_04", "prompt": "Mama (wavy auburn hair, fair freckled skin, cream sweater) hugging Rosie on cozy couch, soft pink and warm loving colors surrounding them"},
        {"id": "page_05", "prompt": "Rosie sitting cross-legged taking deep breaths with peaceful expression, soft green calm color spreading around her like gentle waves"},
        {"id": "page_06", "prompt": "Rosie at window as sun comes out, rainbow visible in sky, yellow happiness and joy lighting up her face, excited expression"},
        {"id": "page_07", "prompt": "Rosie dancing and splashing in rain puddles outside, rainbow arching overhead, all colors swirling joyfully around her, laughing happily"},
        {"id": "page_08", "prompt": "Rosie sitting at table painting a rainbow with watercolors, looking at viewer with knowing wise smile, colorful art supplies around her"}
    ]
}

# Book 5: Oliver the Curious Owl
BOOK5_PROMPTS = {
    "book_id": "book5_oliver_owl",
    "title": "Oliver the Curious Owl",
    "style_base": "Rich watercolour children's book illustration, curious woodland mood, detailed forest watercolors, warm dappled light, rich greens and browns, cozy woodland atmosphere",
    "character_base": "Oliver, a small fluffy barn owl with distinctive heart-shaped white face, large round amber-golden curious eyes, speckled brown and cream feathers on body, small ear tufts, tiny talons, head often tilted curiously to one side",
    "images": [
        {"id": "cover_front", "prompt": "Oliver the small barn owl perched on gnarled oak branch with wings slightly spread, surrounded by floating question marks, woodland creatures (squirrel bee firefly) around him, twilight forest background with purple-orange sky, space at top for title"},
        {"id": "cover_back", "prompt": "Oliver sleeping peacefully curled up in cozy tree hollow, Grandpa Oak (large great horned owl with tufted ears and tiny round spectacles) watching over him, soft moonlight, warm cozy scene"},
        {"id": "page_01", "prompt": "Oliver in cozy hollow of ancient gnarled oak tree with Grandpa Oak beside him, Oliver's eyes wide with curiosity, head tilted, forest visible through opening"},
        {"id": "page_02", "prompt": "Oliver perched on branch watching a friendly bumblebee on a flower, head tilted curiously, Grandpa Oak in background smiling wisely, forest setting"},
        {"id": "page_03", "prompt": "Grandpa Oak great horned owl wearing tiny round spectacles speaking wisely from his perch, Oliver listening intently with wide eyes, dappled forest light"},
        {"id": "page_04", "prompt": "Oliver flying low over mossy forest floor discovering mushrooms and soft green moss, curious red squirrel with fluffy tail watching him, dappled sunlight"},
        {"id": "page_05", "prompt": "Oliver in twilight forest surrounded by glowing fireflies with soft green-yellow lights, Oliver looking amazed, purple-orange dusk sky visible through trees"},
        {"id": "page_06", "prompt": "Oliver back in oak tree excitedly flapping wings telling Grandpa Oak about discoveries, animated and energetic, warm amber evening light"},
        {"id": "page_07", "prompt": "Oliver and Grandpa Oak perched together on oak branch watching golden sunrise through forest trees, peaceful wise moment, warm orange and golden light"}
    ]
}

ALL_BOOKS = [BOOK1_PROMPTS, BOOK2_PROMPTS, BOOK3_PROMPTS, BOOK4_PROMPTS, BOOK5_PROMPTS]

async def generate_book_images(book_data: dict):
    """Generate all images for a single book"""
    book_id = book_data["book_id"]
    output_dir = OUTPUT_BASE / book_id
    covers_dir = output_dir / "covers"
    pages_dir = output_dir / "pages"
    
    covers_dir.mkdir(parents=True, exist_ok=True)
    pages_dir.mkdir(parents=True, exist_ok=True)
    
    results = []
    total = len(book_data["images"])
    
    print(f"\n{'='*60}")
    print(f"Generating: {book_data['title']}")
    print(f"{'='*60}")
    
    for i, img_data in enumerate(book_data["images"]):
        img_id = img_data["id"]
        
        # Determine output directory
        if "cover" in img_id:
            out_dir = covers_dir
        else:
            out_dir = pages_dir
        
        filepath = out_dir / f"{img_id}.png"
        
        # Skip if already exists
        if filepath.exists():
            print(f"[{i+1}/{total}] Skipping {img_id} (exists)")
            results.append({"id": img_id, "status": "skipped", "path": str(filepath)})
            continue
        
        # Build full prompt with style and character
        full_prompt = f"{book_data['style_base']}. {img_data['prompt']}. Character description: {book_data['character_base']}. Professional children's book illustration quality, consistent character appearance."
        
        print(f"[{i+1}/{total}] Generating {img_id}...")
        
        try:
            result = await generate_image_flux(
                prompt=full_prompt,
                model="flux-dev",
                image_size="landscape_16_9" if "cover" in img_id else "landscape_4_3",
                num_images=1
            )
            
            if result.get("success") and result.get("images"):
                # Get the URL from the image dict
                image_info = result["images"][0]
                image_url = image_info["url"] if isinstance(image_info, dict) else image_info
                
                # Download and save image
                import aiohttp
                async with aiohttp.ClientSession() as session:
                    async with session.get(image_url) as resp:
                        if resp.status == 200:
                            image_bytes = await resp.read()
                            with open(filepath, 'wb') as f:
                                f.write(image_bytes)
                            print(f"    Saved: {filepath.name}")
                            results.append({"id": img_id, "status": "success", "path": str(filepath)})
                        else:
                            print(f"    ERROR: Failed to download (HTTP {resp.status})")
                            results.append({"id": img_id, "status": "error", "error": f"Download failed: {resp.status}"})
            else:
                print(f"    ERROR: Generation failed - {result}")
                results.append({"id": img_id, "status": "error", "error": str(result)})
                
        except Exception as e:
            print(f"    ERROR: {str(e)[:100]}")
            results.append({"id": img_id, "status": "error", "error": str(e)[:100]})
        
        # Small delay between requests
        await asyncio.sleep(1)
    
    # Save results
    with open(output_dir / "generation_results.json", 'w') as f:
        json.dump({
            "book_id": book_id,
            "title": book_data["title"],
            "generated_at": datetime.now().isoformat(),
            "results": results
        }, f, indent=2)
    
    success_count = sum(1 for r in results if r["status"] in ["success", "skipped"])
    print(f"\n{book_data['title']}: {success_count}/{total} images complete")
    
    return results

async def generate_all_books():
    """Generate images for all 5 books"""
    print("\n" + "="*70)
    print("PICTURE BOOK BATCH 1 - GENERATING 5 BOOKS")
    print("="*70)
    
    all_results = {}
    
    for book in ALL_BOOKS:
        results = await generate_book_images(book)
        all_results[book["book_id"]] = results
    
    # Summary
    print("\n" + "="*70)
    print("GENERATION COMPLETE - SUMMARY")
    print("="*70)
    
    total_success = 0
    total_images = 0
    
    for book_id, results in all_results.items():
        success = sum(1 for r in results if r["status"] in ["success", "skipped"])
        total = len(results)
        total_success += success
        total_images += total
        print(f"  {book_id}: {success}/{total}")
    
    print(f"\nTOTAL: {total_success}/{total_images} images")
    
    return all_results

if __name__ == "__main__":
    asyncio.run(generate_all_books())
