"""
Batch 2: Settings & Backgrounds Generator
Generates 50 scene/background images for the starter library
"""

import asyncio
import os
import base64
import json
from datetime import datetime, timezone
from dotenv import dotenv_values

env = dotenv_values('/app/backend/.env')
EMERGENT_LLM_KEY = env.get('EMERGENT_LLM_KEY')

from emergentintegrations.llm.openai.image_generation import OpenAIImageGeneration

# Batch 2: 50 Settings & Background Images
# Distribution: 13 Watercolour, 13 Realistic, 12 Comic, 12 Sketch
BATCH_2_SETTINGS = [
    # === WATERCOLOUR STYLE (13 images) ===
    # Fantasy Settings
    {"id": "scene_001", "name": "Enchanted Forest Glade", "category": "scene",
     "tags": ["forest", "enchanted", "magical", "fantasy", "watercolour"],
     "art_style": "watercolour",
     "prompt": "A magical forest glade with towering ancient trees, soft golden sunlight filtering through leaves, glowing fireflies, colorful mushrooms growing around mossy rocks, a gentle stream with stepping stones, peaceful and inviting atmosphere"},
    
    {"id": "scene_002", "name": "Fairy Tale Castle", "category": "scene",
     "tags": ["castle", "fairy tale", "fantasy", "kingdom", "watercolour"],
     "art_style": "watercolour",
     "prompt": "A beautiful fairy tale castle with tall spires and colorful flags, perched on a green hillside, surrounded by flowering gardens, a winding path leading to the grand entrance, fluffy white clouds in a blue sky, warm and welcoming"},
    
    {"id": "scene_003", "name": "Magical Treehouse Village", "category": "scene",
     "tags": ["treehouse", "village", "fantasy", "whimsical", "watercolour"],
     "art_style": "watercolour",
     "prompt": "A whimsical village of cozy treehouses connected by rope bridges and wooden walkways, lanterns hanging from branches, small gardens on platforms, smoke rising from tiny chimneys, warm evening light"},
    
    {"id": "scene_004", "name": "Peaceful Meadow", "category": "scene",
     "tags": ["meadow", "flowers", "peaceful", "nature", "watercolour"],
     "art_style": "watercolour",
     "prompt": "A beautiful sunlit meadow full of wildflowers in pink, purple, yellow and white, butterflies dancing in the air, a gentle hill with a single large oak tree, puffy clouds, peaceful summer day"},
    
    # Everyday Settings
    {"id": "scene_005", "name": "Cozy Library Corner", "category": "scene",
     "tags": ["library", "books", "cozy", "indoor", "watercolour"],
     "art_style": "watercolour",
     "prompt": "A warm cozy library corner with tall wooden bookshelves filled with colorful books, a comfortable reading nook with cushions by a window, soft afternoon light streaming in, a cup of tea on a small table"},
    
    {"id": "scene_006", "name": "Sunny Beach Cove", "category": "scene",
     "tags": ["beach", "ocean", "sunny", "tropical", "watercolour"],
     "art_style": "watercolour",
     "prompt": "A beautiful sandy beach cove with crystal clear turquoise water, palm trees swaying gently, colorful seashells on the shore, a wooden dock with a small sailboat, bright sunny day"},
    
    {"id": "scene_007", "name": "Autumn Park Path", "category": "scene",
     "tags": ["park", "autumn", "path", "nature", "watercolour"],
     "art_style": "watercolour",
     "prompt": "A charming park path covered in colorful fallen leaves in orange, red and gold, tall trees with autumn foliage on both sides, wooden benches, squirrels playing, warm afternoon light"},
    
    # Weather & Seasons
    {"id": "scene_008", "name": "Snowy Winter Cabin", "category": "scene",
     "tags": ["winter", "snow", "cabin", "cozy", "watercolour"],
     "art_style": "watercolour",
     "prompt": "A cozy wooden cabin in a snowy winter wonderland, smoke rising from the chimney, warm light glowing from windows, snow-covered pine trees all around, fresh snowfall, peaceful and inviting"},
    
    {"id": "scene_009", "name": "Rainbow After Rain", "category": "scene",
     "tags": ["rainbow", "rain", "sky", "magical", "watercolour"],
     "art_style": "watercolour",
     "prompt": "A stunning double rainbow arching across the sky after a rain shower, sun breaking through clouds, glistening wet grass and flowers, puddles reflecting the colors, hopeful and magical atmosphere"},
    
    {"id": "scene_010", "name": "Cherry Blossom Garden", "category": "scene",
     "tags": ["cherry blossom", "spring", "garden", "japan", "watercolour"],
     "art_style": "watercolour",
     "prompt": "A serene Japanese garden with cherry blossom trees in full bloom, pink petals floating on a gentle breeze, a small red bridge over a koi pond, stone lanterns, peaceful spring morning"},
    
    {"id": "scene_011", "name": "Starry Night Hilltop", "category": "scene",
     "tags": ["night", "stars", "hilltop", "peaceful", "watercolour"],
     "art_style": "watercolour",
     "prompt": "A peaceful hilltop under a magnificent starry night sky, the Milky Way visible, a single large tree silhouetted against the stars, fireflies glowing below, sense of wonder and magic"},
    
    {"id": "scene_012", "name": "Misty Mountain Valley", "category": "scene",
     "tags": ["mountain", "valley", "misty", "nature", "watercolour"],
     "art_style": "watercolour",
     "prompt": "A breathtaking mountain valley with morning mist rolling between peaks, a winding river below, evergreen forests on the slopes, soft golden sunrise light, majestic and peaceful"},
    
    {"id": "scene_013", "name": "Cottage Garden", "category": "scene",
     "tags": ["cottage", "garden", "flowers", "home", "watercolour"],
     "art_style": "watercolour",
     "prompt": "A charming English cottage with a thatched roof surrounded by a beautiful overgrown flower garden, roses climbing the walls, a picket fence, bees and butterflies, warm summer afternoon"},
    
    # === REALISTIC ILLUSTRATED STYLE (13 images) ===
    # Science Fiction
    {"id": "scene_014", "name": "Space Station Observatory", "category": "scene",
     "tags": ["space", "station", "scifi", "futuristic", "realistic"],
     "art_style": "realistic",
     "prompt": "A futuristic space station observation deck with large curved windows showing Earth below and stars beyond, holographic displays, comfortable seating areas, soft blue lighting, sleek modern design"},
    
    {"id": "scene_015", "name": "Alien Planet Landscape", "category": "scene",
     "tags": ["alien", "planet", "scifi", "landscape", "realistic"],
     "art_style": "realistic",
     "prompt": "An alien planet landscape with two moons in a purple sky, strange but beautiful crystalline rock formations, bioluminescent plants glowing softly, a distant futuristic colony, sense of wonder and discovery"},
    
    {"id": "scene_016", "name": "Futuristic City Skyline", "category": "scene",
     "tags": ["city", "futuristic", "scifi", "skyline", "realistic"],
     "art_style": "realistic",
     "prompt": "A gleaming futuristic city skyline with tall glass towers, flying vehicles, elevated gardens and walkways, clean energy technology visible, bright optimistic daytime, sustainable and advanced"},
    
    # Adventure Settings
    {"id": "scene_017", "name": "Ancient Temple Ruins", "category": "scene",
     "tags": ["temple", "ruins", "ancient", "adventure", "realistic"],
     "art_style": "realistic",
     "prompt": "Magnificent ancient temple ruins covered in vines and moss, tall stone columns and carved statues, shafts of golden sunlight piercing through the canopy, mysterious but beautiful, sense of history and discovery"},
    
    {"id": "scene_018", "name": "Desert Oasis", "category": "scene",
     "tags": ["desert", "oasis", "adventure", "tropical", "realistic"],
     "art_style": "realistic",
     "prompt": "A lush desert oasis with palm trees and crystal clear water, golden sand dunes in the background, colorful birds and butterflies, a small waterfall, refreshing and welcoming"},
    
    {"id": "scene_019", "name": "Jungle Waterfall", "category": "scene",
     "tags": ["jungle", "waterfall", "tropical", "adventure", "realistic"],
     "art_style": "realistic",
     "prompt": "A stunning jungle waterfall cascading into a turquoise pool, lush tropical vegetation, exotic flowers, colorful parrots and butterflies, mist rising, rays of sunlight through the canopy"},
    
    {"id": "scene_020", "name": "Crystal Cave", "category": "scene",
     "tags": ["cave", "crystal", "magical", "underground", "realistic"],
     "art_style": "realistic",
     "prompt": "A magnificent underground crystal cave with huge glowing crystals in purple, blue and pink, an underground lake reflecting the light, stalactites and stalagmites, magical and mysterious atmosphere"},
    
    # Everyday Settings
    {"id": "scene_021", "name": "Colorful Classroom", "category": "scene",
     "tags": ["classroom", "school", "education", "indoor", "realistic"],
     "art_style": "realistic",
     "prompt": "A bright colorful classroom with student desks, educational posters on walls, a friendly chalkboard with drawings, plants by windows, art supplies organized neatly, welcoming learning environment"},
    
    {"id": "scene_022", "name": "Cozy Bedroom", "category": "scene",
     "tags": ["bedroom", "cozy", "home", "indoor", "realistic"],
     "art_style": "realistic",
     "prompt": "A cozy child's bedroom with a comfortable bed with colorful blankets, bookshelves full of stories, toys organized neatly, fairy lights, a window seat for reading, warm and safe feeling"},
    
    {"id": "scene_023", "name": "Busy Kitchen", "category": "scene",
     "tags": ["kitchen", "cooking", "home", "indoor", "realistic"],
     "art_style": "realistic",
     "prompt": "A warm family kitchen with wooden counters, colorful fruits and vegetables, copper pots hanging, fresh baked goods cooling, herbs in pots by the window, inviting and homey"},
    
    # Underwater
    {"id": "scene_024", "name": "Coral Reef Kingdom", "category": "scene",
     "tags": ["underwater", "coral", "reef", "ocean", "realistic"],
     "art_style": "realistic",
     "prompt": "A vibrant coral reef teeming with colorful tropical fish, sea turtles, and friendly dolphins, sunlight filtering through blue water, beautiful coral formations in pink, orange and purple, magical underwater world"},
    
    {"id": "scene_025", "name": "Sunken Ship Garden", "category": "scene",
     "tags": ["underwater", "shipwreck", "ocean", "adventure", "realistic"],
     "art_style": "realistic",
     "prompt": "An old friendly sunken ship now covered in colorful coral and sea plants, fish swimming through portholes, treasure chest visible, shafts of sunlight from above, mysterious but inviting"},
    
    {"id": "scene_026", "name": "Northern Lights Sky", "category": "scene",
     "tags": ["aurora", "northern lights", "night", "magical", "realistic"],
     "art_style": "realistic",
     "prompt": "A spectacular aurora borealis dancing across the night sky in greens, purples and blues, reflected in a calm frozen lake, snow-covered mountains, a few stars visible, breathtaking natural wonder"},
    
    # === COMIC BOOK STYLE (12 images) ===
    {"id": "scene_027", "name": "Superhero City", "category": "scene",
     "tags": ["city", "superhero", "urban", "action", "comic"],
     "art_style": "comic",
     "prompt": "A dynamic cityscape with tall colorful buildings, rooftops perfect for superhero landings, dramatic clouds, city lights beginning to glow at sunset, exciting and full of possibility"},
    
    {"id": "scene_028", "name": "Robot Factory", "category": "scene",
     "tags": ["factory", "robot", "scifi", "futuristic", "comic"],
     "art_style": "comic",
     "prompt": "A colorful robot factory with assembly lines building friendly robots, conveyor belts, glowing control panels, robotic arms working, bright clean environment, exciting technology"},
    
    {"id": "scene_029", "name": "Racing Track", "category": "scene",
     "tags": ["racing", "track", "sports", "action", "comic"],
     "art_style": "comic",
     "prompt": "An exciting race track with colorful banners and flags, grandstands full of cheering crowd, dramatic curves and straightaways, checkered patterns, dynamic perspective, thrilling atmosphere"},
    
    {"id": "scene_030", "name": "Pirate Cove", "category": "scene",
     "tags": ["pirate", "cove", "adventure", "ocean", "comic"],
     "art_style": "comic",
     "prompt": "A hidden pirate cove with a wooden ship anchored, treasure maps and crates on the dock, palm trees, skull rock formation in background, exciting adventure atmosphere, bold colors"},
    
    {"id": "scene_031", "name": "Volcano Island", "category": "scene",
     "tags": ["volcano", "island", "adventure", "dramatic", "comic"],
     "art_style": "comic",
     "prompt": "A dramatic volcanic island with a smoking volcano, lush jungle vegetation, waterfalls, exotic birds flying, a rope bridge crossing a ravine, exciting adventure setting"},
    
    {"id": "scene_032", "name": "Space Battle Arena", "category": "scene",
     "tags": ["space", "battle", "arena", "scifi", "comic"],
     "art_style": "comic",
     "prompt": "A futuristic space arena floating among asteroids, colorful force fields, landing platforms for spaceships, holographic scoreboards, stars and nebulae in background, exciting sports venue"},
    
    {"id": "scene_033", "name": "Ninja Training Ground", "category": "scene",
     "tags": ["ninja", "training", "dojo", "action", "comic"],
     "art_style": "comic",
     "prompt": "A ninja training ground with wooden practice dummies, obstacle course elements, cherry blossom trees, traditional Japanese architecture, dramatic mountain backdrop, exciting atmosphere"},
    
    {"id": "scene_034", "name": "Monster Arena", "category": "scene",
     "tags": ["arena", "monster", "battle", "fantasy", "comic"],
     "art_style": "comic",
     "prompt": "A grand colosseum-style arena for friendly monster battles, colorful flags and banners, excited crowd in stands, dramatic spotlights, portal gates for monster entrances, exciting tournament venue"},
    
    {"id": "scene_035", "name": "Cyber City Street", "category": "scene",
     "tags": ["cyber", "city", "street", "neon", "comic"],
     "art_style": "comic",
     "prompt": "A vibrant cyberpunk street with neon signs in multiple colors, holographic advertisements, food stalls and shops, flying vehicles overhead, rain-slicked streets reflecting lights, exciting urban scene"},
    
    {"id": "scene_036", "name": "Dragon's Peak", "category": "scene",
     "tags": ["dragon", "mountain", "fantasy", "epic", "comic"],
     "art_style": "comic",
     "prompt": "A dramatic mountain peak shaped like a dragon, swirling clouds, ancient carved stairs leading up, glowing crystals embedded in rock, sunset colors, epic fantasy adventure setting"},
    
    {"id": "scene_037", "name": "Underground Base", "category": "scene",
     "tags": ["base", "underground", "secret", "scifi", "comic"],
     "art_style": "comic",
     "prompt": "A secret underground hero base with multiple levels, computer screens and control panels, vehicle hangar visible, training area, bright colorful lighting, exciting headquarters"},
    
    {"id": "scene_038", "name": "Dinosaur Valley", "category": "scene",
     "tags": ["dinosaur", "valley", "prehistoric", "adventure", "comic"],
     "art_style": "comic",
     "prompt": "A prehistoric valley with friendly dinosaurs grazing, giant ferns and palm trees, a river winding through, volcanic mountains in distance, pterodactyls flying, exciting adventure setting"},
    
    # === PENCIL SKETCH STYLE (12 images) ===
    {"id": "scene_039", "name": "Old Bookshop", "category": "scene",
     "tags": ["bookshop", "cozy", "books", "indoor", "sketch"],
     "art_style": "sketch",
     "prompt": "A charming old bookshop interior with floor-to-ceiling wooden shelves, rolling ladder, cozy reading chairs, stacks of books everywhere, warm lamplight, cat sleeping on cushion, inviting atmosphere"},
    
    {"id": "scene_040", "name": "Windmill Hill", "category": "scene",
     "tags": ["windmill", "hill", "countryside", "peaceful", "sketch"],
     "art_style": "sketch",
     "prompt": "A peaceful countryside scene with an old stone windmill on a grassy hill, wheat fields swaying in breeze, winding dirt path, fluffy clouds, birds flying, rustic and charming"},
    
    {"id": "scene_041", "name": "Fishing Village", "category": "scene",
     "tags": ["village", "fishing", "coastal", "boats", "sketch"],
     "art_style": "sketch",
     "prompt": "A quaint coastal fishing village with colorful boats in harbor, stone cottages, fishing nets drying, seagulls, lighthouse in distance, calm morning sea, peaceful and picturesque"},
    
    {"id": "scene_042", "name": "Secret Garden Gate", "category": "scene",
     "tags": ["garden", "gate", "secret", "mysterious", "sketch"],
     "art_style": "sketch",
     "prompt": "An old ornate iron gate overgrown with climbing roses, leading to a mysterious secret garden glimpsed beyond, cobblestone path, ivy-covered walls, dappled sunlight, magical and inviting"},
    
    {"id": "scene_043", "name": "Treehouse Hideaway", "category": "scene",
     "tags": ["treehouse", "hideaway", "tree", "cozy", "sketch"],
     "art_style": "sketch",
     "prompt": "A cozy wooden treehouse nestled in a large oak tree, rope ladder, small balcony with string lights, telescope for stargazing, surrounding branches with bird feeders, childhood dream hideaway"},
    
    {"id": "scene_044", "name": "Bakery Shop", "category": "scene",
     "tags": ["bakery", "shop", "cozy", "food", "sketch"],
     "art_style": "sketch",
     "prompt": "A charming French bakery interior with display cases of pastries and bread, copper pans on walls, checkered floor, morning light through windows, warm and inviting, smell of fresh bread"},
    
    {"id": "scene_045", "name": "Rainy Window View", "category": "scene",
     "tags": ["rain", "window", "cozy", "indoor", "sketch"],
     "art_style": "sketch",
     "prompt": "A cozy window seat looking out at a rainy day, raindrops on glass, blurred city lights beyond, warm blanket and hot cocoa, books stacked nearby, peaceful and contemplative"},
    
    {"id": "scene_046", "name": "Wishing Well", "category": "scene",
     "tags": ["well", "wishing", "magical", "garden", "sketch"],
     "art_style": "sketch",
     "prompt": "An old stone wishing well covered in moss in a quiet forest clearing, wildflowers growing around, soft magical sparkles rising from water, ancient and mysterious, sense of possibility"},
    
    {"id": "scene_047", "name": "Art Studio", "category": "scene",
     "tags": ["studio", "art", "creative", "indoor", "sketch"],
     "art_style": "sketch",
     "prompt": "A sunny artist studio with large windows, canvases and easels, paint tubes and brushes everywhere, comfortable worn couch, plants, half-finished paintings, creative and inspiring"},
    
    {"id": "scene_048", "name": "Train Platform", "category": "scene",
     "tags": ["train", "platform", "station", "travel", "sketch"],
     "art_style": "sketch",
     "prompt": "A charming old train platform with vintage steam locomotive, wooden benches, hanging clock, luggage carts, destination signs, sense of adventure and journey about to begin"},
    
    {"id": "scene_049", "name": "Moonlit Pond", "category": "scene",
     "tags": ["pond", "moon", "night", "peaceful", "sketch"],
     "art_style": "sketch",
     "prompt": "A serene pond under a full moon, lily pads floating, willow tree branches dipping into water, fireflies glowing, gentle ripples, peaceful night atmosphere, magical and calm"},
    
    {"id": "scene_050", "name": "Mountain Campsite", "category": "scene",
     "tags": ["camping", "mountain", "outdoor", "adventure", "sketch"],
     "art_style": "sketch",
     "prompt": "A cozy mountain campsite with tent, crackling campfire, logs for sitting, mountains silhouetted against starry sky, pine trees, hiking gear nearby, adventure and friendship"}
]

# Style suffixes for prompts
STYLE_SUFFIXES = {
    "watercolour": ", painted in soft watercolour style with gentle washes and flowing colors, delicate brushstrokes, professional children's book illustration, vibrant, age-appropriate, safe for children",
    "realistic": ", realistic illustrated style with detailed rendering, professional children's book illustration quality, vibrant colors, age-appropriate, safe for children",
    "comic": ", dynamic comic book style with bold outlines, vibrant colors, expressive details, professional children's book illustration, age-appropriate, safe for children",
    "sketch": ", pencil sketch style with detailed line work, crosshatching for shadows, artistic shading on cream paper, professional children's book illustration, age-appropriate, safe for children"
}


async def generate_batch_2():
    """Generate all 50 settings/background images for Batch 2"""
    image_gen = OpenAIImageGeneration(api_key=EMERGENT_LLM_KEY)
    
    results = []
    failed = []
    
    for i, scene in enumerate(BATCH_2_SETTINGS):
        print(f"\nGenerating {i+1}/50: {scene['name']} ({scene['art_style']})...")
        
        # Build full prompt with style suffix
        full_prompt = scene['prompt'] + STYLE_SUFFIXES[scene['art_style']]
        
        try:
            images = await image_gen.generate_images(
                prompt=full_prompt,
                model='gpt-image-1',
                number_of_images=1
            )
            
            if images and len(images) > 0:
                # Save image to file
                filename = f"/tmp/batch2_{scene['id']}_{scene['art_style']}.png"
                with open(filename, 'wb') as f:
                    f.write(images[0])
                
                result = {
                    "id": scene['id'],
                    "name": scene['name'],
                    "category": scene['category'],
                    "tags": scene['tags'],
                    "art_style": scene['art_style'],
                    "filename": filename
                }
                results.append(result)
                print(f"  ✓ Saved: {filename}")
            else:
                failed.append(scene['name'])
                print(f"  ✗ Failed: No image generated")
                
        except Exception as e:
            failed.append(scene['name'])
            print(f"  ✗ Error: {str(e)[:80]}")
        
        # Small delay to avoid rate limiting
        await asyncio.sleep(0.5)
    
    print(f"\n{'='*60}")
    print(f"BATCH 2 COMPLETE")
    print(f"{'='*60}")
    print(f"Generated: {len(results)}/50")
    print(f"Failed: {len(failed)}")
    if failed:
        print(f"Failed items: {failed}")
    
    # Save results to JSON
    with open('/tmp/batch2_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to /tmp/batch2_results.json")
    
    return results, failed


if __name__ == "__main__":
    print("Starting Batch 2: Settings & Backgrounds Generation")
    print("=" * 60)
    results, failed = asyncio.run(generate_batch_2())
