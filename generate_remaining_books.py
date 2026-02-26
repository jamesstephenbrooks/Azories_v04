#!/usr/bin/env python3
"""
Picture Book Image Generator - Using GPT-Image-1 (Emergent Key)
Continues generation for remaining books
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from datetime import datetime

APP_DIR = Path(__file__).parent
BACKEND_DIR = APP_DIR / 'backend'

from dotenv import load_dotenv
load_dotenv(BACKEND_DIR / '.env')

from emergentintegrations.llm.openai.image_generation import OpenAIImageGeneration

EMERGENT_KEY = os.environ.get('EMERGENT_LLM_KEY')
print(f"Using Emergent Key: {EMERGENT_KEY[:20]}...")

OUTPUT_BASE = APP_DIR / 'content/books/batch1_picture_books'

# Book 3: The Magic Garden (remaining pages)
BOOK3_PROMPTS = {
    "book_id": "book3_magic_garden",
    "title": "The Magic Garden", 
    "style_base": "Lush watercolour children's book illustration, whimsical and colorful mood, rich botanical watercolors, warm golden sunlight, vibrant garden colors",
    "character_base": "Maya, a 4-year-old girl with curly black hair in two puffs with colorful hair ties, warm brown skin, bright curious dark brown eyes, gap-toothed smile, round cheeks, wearing yellow sundress with green leaf pattern, green rubber boots, floppy straw sun hat with pink ribbon, carrying small red watering can",
    "images": [
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

REMAINING_BOOKS = [BOOK3_PROMPTS, BOOK4_PROMPTS, BOOK5_PROMPTS]

async def generate_book_images(book_data: dict):
    """Generate remaining images for a book using GPT-Image-1"""
    book_id = book_data["book_id"]
    output_dir = OUTPUT_BASE / book_id
    covers_dir = output_dir / "covers"
    pages_dir = output_dir / "pages"
    
    covers_dir.mkdir(parents=True, exist_ok=True)
    pages_dir.mkdir(parents=True, exist_ok=True)
    
    results = []
    total = len(book_data["images"])
    
    image_gen = OpenAIImageGeneration(api_key=EMERGENT_KEY)
    
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
        
        # Build full prompt
        full_prompt = f"{book_data['style_base']}. {img_data['prompt']}. Character: {book_data['character_base']}. Professional children's book illustration, consistent character design."
        
        print(f"[{i+1}/{total}] Generating {img_id}...")
        
        try:
            images = await image_gen.generate_images(
                prompt=full_prompt,
                model="gpt-image-1",
                number_of_images=1,
                quality="medium"
            )
            
            if images and len(images) > 0:
                with open(filepath, 'wb') as f:
                    f.write(images[0])
                print(f"    Saved: {filepath.name}")
                results.append({"id": img_id, "status": "success", "path": str(filepath)})
            else:
                print(f"    ERROR: No image returned")
                results.append({"id": img_id, "status": "error", "error": "No image"})
                
        except Exception as e:
            print(f"    ERROR: {str(e)[:100]}")
            results.append({"id": img_id, "status": "error", "error": str(e)[:100]})
        
        await asyncio.sleep(0.5)
    
    # Save results
    with open(output_dir / "generation_results_gpt.json", 'w') as f:
        json.dump({
            "book_id": book_id,
            "title": book_data["title"],
            "generated_at": datetime.now().isoformat(),
            "model": "gpt-image-1",
            "results": results
        }, f, indent=2)
    
    success_count = sum(1 for r in results if r["status"] in ["success", "skipped"])
    print(f"\n{book_data['title']}: {success_count}/{total} images complete")
    
    return results

async def generate_remaining():
    """Generate remaining images for books 3-5"""
    print("\n" + "="*70)
    print("CONTINUING GENERATION WITH GPT-IMAGE-1")
    print("="*70)
    
    all_results = {}
    
    for book in REMAINING_BOOKS:
        results = await generate_book_images(book)
        all_results[book["book_id"]] = results
    
    print("\n" + "="*70)
    print("GENERATION COMPLETE")
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

if __name__ == "__main__":
    asyncio.run(generate_remaining())
