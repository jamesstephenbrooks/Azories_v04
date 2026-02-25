"""
Batch 3: Objects & Props Generator
Generates 50 object/prop images for the starter library
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

# Batch 3: 50 Objects & Props Images
# Distribution: 13 Watercolour, 13 Realistic, 12 Comic, 12 Sketch
BATCH_3_OBJECTS = [
    # === WATERCOLOUR STYLE (13 images) ===
    # Magical Items
    {"id": "obj_001", "name": "Enchanted Spell Book", "category": "object",
     "tags": ["book", "magic", "spell", "enchanted", "watercolour"],
     "art_style": "watercolour",
     "prompt": "An ancient spell book with a worn leather cover decorated with gold symbols, pages glowing with soft magical light, mysterious runes visible, floating sparkles around it, on a wooden table"},
    
    {"id": "obj_002", "name": "Colorful Potion Bottles", "category": "object",
     "tags": ["potion", "bottles", "magic", "colorful", "watercolour"],
     "art_style": "watercolour",
     "prompt": "A collection of beautiful glass potion bottles in various shapes, filled with glowing liquids in pink, blue, green and purple, bubbles rising inside, cork stoppers, on a wooden shelf"},
    
    {"id": "obj_003", "name": "Golden Treasure Chest", "category": "object",
     "tags": ["treasure", "chest", "gold", "pirate", "watercolour"],
     "art_style": "watercolour",
     "prompt": "An ornate wooden treasure chest with gold trim, lid open revealing sparkling gold coins, jewels, and pearls inside, soft magical glow emanating from within"},
    
    {"id": "obj_004", "name": "Crystal Ball", "category": "object",
     "tags": ["crystal", "ball", "magic", "fortune", "watercolour"],
     "art_style": "watercolour",
     "prompt": "A beautiful crystal ball on an ornate golden stand, swirling mist inside with hints of images forming, soft purple and blue glow, mysterious and magical"},
    
    {"id": "obj_005", "name": "Fairy Lantern", "category": "object",
     "tags": ["lantern", "fairy", "light", "magical", "watercolour"],
     "art_style": "watercolour",
     "prompt": "A delicate glass lantern with intricate metalwork, containing soft glowing fairy lights inside, warm golden glow, hanging from a decorative hook, magical atmosphere"},
    
    # Everyday Objects Reimagined
    {"id": "obj_006", "name": "Magical Teapot", "category": "object",
     "tags": ["teapot", "magic", "whimsical", "cute", "watercolour"],
     "art_style": "watercolour",
     "prompt": "A whimsical teapot with a friendly face, decorated with painted flowers, steam rising in the shape of hearts and stars, matching teacups nearby, cozy and magical"},
    
    {"id": "obj_007", "name": "Enchanted Music Box", "category": "object",
     "tags": ["music box", "enchanted", "beautiful", "magical", "watercolour"],
     "art_style": "watercolour",
     "prompt": "A beautiful antique music box with mother of pearl inlay, lid open showing a tiny ballerina figure, musical notes floating in the air as sparkles, delicate and precious"},
    
    {"id": "obj_008", "name": "Magic Garden Tools", "category": "object",
     "tags": ["garden", "tools", "magic", "nature", "watercolour"],
     "art_style": "watercolour",
     "prompt": "A set of charming garden tools with wooden handles wrapped in vines, small flowers growing from them, a watering can with butterflies, trowel and gloves, magical garden theme"},
    
    {"id": "obj_009", "name": "Wishing Coins", "category": "object",
     "tags": ["coins", "wishing", "gold", "magic", "watercolour"],
     "art_style": "watercolour",
     "prompt": "A pile of shimmering golden wishing coins with star symbols engraved, soft magical sparkles rising from them, velvet pouch nearby, sense of wishes and dreams"},
    
    {"id": "obj_010", "name": "Storybook Collection", "category": "object",
     "tags": ["books", "storybook", "reading", "colorful", "watercolour"],
     "art_style": "watercolour",
     "prompt": "A stack of beautiful storybooks with colorful illustrated covers showing fairy tales, castles, dragons and princesses, bookmarks with ribbons, inviting to read"},
    
    {"id": "obj_011", "name": "Artist Paint Set", "category": "object",
     "tags": ["paint", "art", "creative", "colorful", "watercolour"],
     "art_style": "watercolour",
     "prompt": "A beautiful wooden paint box with watercolor paints in rainbow colors, brushes of various sizes, a palette with mixed colors, water jar, creative and inspiring"},
    
    {"id": "obj_012", "name": "Magical Compass", "category": "object",
     "tags": ["compass", "navigation", "adventure", "brass", "watercolour"],
     "art_style": "watercolour",
     "prompt": "An ornate brass compass with intricate engravings, the needle glowing with soft golden light, ancient symbols around the edge, leather case nearby, sense of adventure"},
    
    {"id": "obj_013", "name": "Dream Catcher", "category": "object",
     "tags": ["dream catcher", "dreams", "magical", "feathers", "watercolour"],
     "art_style": "watercolour",
     "prompt": "A beautiful dream catcher with an intricate web pattern, decorated with colorful feathers and beads, soft magical glow, floating sparkles caught in the web, peaceful"},
    
    # === REALISTIC ILLUSTRATED STYLE (13 images) ===
    # Vehicles
    {"id": "obj_014", "name": "Vintage Spaceship", "category": "object",
     "tags": ["spaceship", "vintage", "scifi", "rocket", "realistic"],
     "art_style": "realistic",
     "prompt": "A retro-futuristic spaceship with a sleek silver body, round portholes, colorful fins, sitting on a launch pad with steam venting, stars visible in background, exciting adventure awaits"},
    
    {"id": "obj_015", "name": "Pirate Ship", "category": "object",
     "tags": ["ship", "pirate", "sailing", "adventure", "realistic"],
     "art_style": "realistic",
     "prompt": "A magnificent wooden pirate ship with billowing sails, jolly roger flag, ornate carved stern, cannons visible, floating on calm blue water, sunset colors in sky"},
    
    {"id": "obj_016", "name": "Hot Air Balloon", "category": "object",
     "tags": ["balloon", "hot air", "flying", "colorful", "realistic"],
     "art_style": "realistic",
     "prompt": "A beautiful hot air balloon with colorful striped pattern in red, yellow and blue, wicker basket below, floating among fluffy white clouds, birds flying nearby, sense of freedom"},
    
    {"id": "obj_017", "name": "Submarine Explorer", "category": "object",
     "tags": ["submarine", "underwater", "explorer", "scifi", "realistic"],
     "art_style": "realistic",
     "prompt": "A friendly yellow submarine with round windows showing lights inside, propeller and periscope, fish swimming around it, underwater bubbles, ready for ocean adventure"},
    
    {"id": "obj_018", "name": "Magic Carpet", "category": "object",
     "tags": ["carpet", "magic", "flying", "arabian", "realistic"],
     "art_style": "realistic",
     "prompt": "A beautiful ornate magic carpet with intricate Persian patterns in red, gold and blue, tasseled edges, floating in the air with magical sparkles underneath, ready for adventure"},
    
    # Tools & Equipment
    {"id": "obj_019", "name": "Explorer Backpack", "category": "object",
     "tags": ["backpack", "explorer", "adventure", "gear", "realistic"],
     "art_style": "realistic",
     "prompt": "A well-worn leather explorer backpack with many pockets, rope and canteen attached, map poking out, compass hanging from strap, ready for adventure"},
    
    {"id": "obj_020", "name": "Treasure Map", "category": "object",
     "tags": ["map", "treasure", "pirate", "adventure", "realistic"],
     "art_style": "realistic",
     "prompt": "An aged parchment treasure map with hand-drawn islands, dotted path leading to X marks the spot, sea monsters illustrated in corners, compass rose, rolled edges"},
    
    {"id": "obj_021", "name": "Scientist Equipment", "category": "object",
     "tags": ["science", "equipment", "laboratory", "experiment", "realistic"],
     "art_style": "realistic",
     "prompt": "A collection of colorful science equipment including beakers, test tubes with bubbling liquids, microscope, magnifying glass, notebook with sketches, exciting experiments"},
    
    {"id": "obj_022", "name": "Knight's Shield", "category": "object",
     "tags": ["shield", "knight", "medieval", "heraldry", "realistic"],
     "art_style": "realistic",
     "prompt": "A noble knight's shield with a golden lion emblem on blue background, polished metal edges, leather straps on back, battle-ready but honorable, medieval castle background"},
    
    {"id": "obj_023", "name": "Telescope", "category": "object",
     "tags": ["telescope", "astronomy", "stars", "exploration", "realistic"],
     "art_style": "realistic",
     "prompt": "A beautiful brass telescope on a wooden tripod, pointed at a starry night sky, notebook with constellation drawings nearby, sense of wonder and discovery"},
    
    {"id": "obj_024", "name": "Camping Gear Set", "category": "object",
     "tags": ["camping", "outdoor", "adventure", "gear", "realistic"],
     "art_style": "realistic",
     "prompt": "A complete camping set with a colorful tent, sleeping bag, flashlight, binoculars, thermos, and campfire supplies, arranged neatly, ready for outdoor adventure"},
    
    {"id": "obj_025", "name": "Art Supplies", "category": "object",
     "tags": ["art", "supplies", "creative", "colorful", "realistic"],
     "art_style": "realistic",
     "prompt": "A beautiful arrangement of art supplies including colored pencils in rainbow order, sketchbook, erasers, sharpener, and inspirational reference photos, creative workspace"},
    
    {"id": "obj_026", "name": "Musical Instruments", "category": "object",
     "tags": ["music", "instruments", "guitar", "creative", "realistic"],
     "art_style": "realistic",
     "prompt": "A collection of child-friendly musical instruments including a small guitar, tambourine, recorder, xylophone, and maracas, arranged colorfully, ready to make music"},
    
    # === COMIC BOOK STYLE (12 images) ===
    {"id": "obj_027", "name": "Super Power Gauntlet", "category": "object",
     "tags": ["gauntlet", "power", "superhero", "tech", "comic"],
     "art_style": "comic",
     "prompt": "A high-tech superhero gauntlet glowing with energy, sleek design with glowing power cores, energy crackling around it, floating against dramatic background"},
    
    {"id": "obj_028", "name": "Robot Pet", "category": "object",
     "tags": ["robot", "pet", "cute", "tech", "comic"],
     "art_style": "comic",
     "prompt": "An adorable robot pet dog with glowing eyes, metallic body with colorful panels, wagging antenna tail, small propeller ears, friendly and loyal expression"},
    
    {"id": "obj_029", "name": "Racing Hoverboard", "category": "object",
     "tags": ["hoverboard", "racing", "future", "cool", "comic"],
     "art_style": "comic",
     "prompt": "A sleek racing hoverboard with neon light trails, aerodynamic design, glowing repulsors underneath, speed lines around it, futuristic and exciting"},
    
    {"id": "obj_030", "name": "Hero Communicator", "category": "object",
     "tags": ["communicator", "hero", "tech", "gadget", "comic"],
     "art_style": "comic",
     "prompt": "A wrist-mounted hero communicator device with holographic display, multiple buttons and screens, glowing indicators, sleek superhero tech design"},
    
    {"id": "obj_031", "name": "Energy Sword", "category": "object",
     "tags": ["sword", "energy", "scifi", "weapon", "comic"],
     "art_style": "comic",
     "prompt": "A glowing energy blade with a high-tech handle, bright blue plasma blade, electrical sparks along the edge, dramatic lighting, heroic weapon"},
    
    {"id": "obj_032", "name": "Jetpack", "category": "object",
     "tags": ["jetpack", "flying", "tech", "adventure", "comic"],
     "art_style": "comic",
     "prompt": "A colorful jetpack with twin thrusters, control handles, fuel gauge, flames shooting from engines, straps visible, ready for flight adventure"},
    
    {"id": "obj_033", "name": "Power Crystals", "category": "object",
     "tags": ["crystals", "power", "magical", "energy", "comic"],
     "art_style": "comic",
     "prompt": "A collection of glowing power crystals in different colors - red, blue, green, yellow, each emanating different energy patterns, floating and rotating"},
    
    {"id": "obj_034", "name": "Monster Ball", "category": "object",
     "tags": ["ball", "monster", "capture", "game", "comic"],
     "art_style": "comic",
     "prompt": "A high-tech capture sphere device with red and white coloring, glowing center button, energy swirling around it, ready to capture friendly creatures"},
    
    {"id": "obj_035", "name": "Time Watch", "category": "object",
     "tags": ["watch", "time", "gadget", "adventure", "comic"],
     "art_style": "comic",
     "prompt": "A special wristwatch with multiple dials and buttons, glowing display showing different time zones, small portal effect around it, time travel device"},
    
    {"id": "obj_036", "name": "Grappling Hook", "category": "object",
     "tags": ["grappling", "hook", "hero", "gadget", "comic"],
     "art_style": "comic",
     "prompt": "A sleek grappling hook device with motorized reel, strong cable, magnetic hook head, belt attachment, hero gadget for swinging between buildings"},
    
    {"id": "obj_037", "name": "Transformation Badge", "category": "object",
     "tags": ["badge", "transform", "hero", "magical", "comic"],
     "art_style": "comic",
     "prompt": "A glowing transformation badge with star emblem in center, energy radiating outward, floating magical particles, ready to transform the wearer into a hero"},
    
    {"id": "obj_038", "name": "Dragon Egg", "category": "object",
     "tags": ["egg", "dragon", "fantasy", "precious", "comic"],
     "art_style": "comic",
     "prompt": "A magnificent dragon egg with iridescent scales pattern, glowing warmly from within, cracks showing inner light, sitting in a nest of gems, precious and magical"},
    
    # === PENCIL SKETCH STYLE (12 images) ===
    {"id": "obj_039", "name": "Antique Key Collection", "category": "object",
     "tags": ["keys", "antique", "mystery", "collection", "sketch"],
     "art_style": "sketch",
     "prompt": "A collection of ornate antique keys in various sizes, intricate designs with hearts, stars, and scrollwork, hanging on an old wooden board, mysterious and inviting"},
    
    {"id": "obj_040", "name": "Vintage Camera", "category": "object",
     "tags": ["camera", "vintage", "photography", "nostalgic", "sketch"],
     "art_style": "sketch",
     "prompt": "A charming vintage camera with leather case, brass fittings, accordion lens, old photographs scattered nearby, nostalgic and artistic atmosphere"},
    
    {"id": "obj_041", "name": "Apothecary Jars", "category": "object",
     "tags": ["jars", "apothecary", "herbs", "magical", "sketch"],
     "art_style": "sketch",
     "prompt": "A collection of glass apothecary jars with handwritten labels, filled with dried herbs, flowers, and mysterious ingredients, wooden shelf, old world charm"},
    
    {"id": "obj_042", "name": "Sewing Kit", "category": "object",
     "tags": ["sewing", "craft", "vintage", "creative", "sketch"],
     "art_style": "sketch",
     "prompt": "A vintage sewing basket with colorful thread spools, pin cushion, measuring tape, fabric swatches, silver thimble, scissors, creative and cozy"},
    
    {"id": "obj_043", "name": "Letter Writing Set", "category": "object",
     "tags": ["letters", "writing", "vintage", "romantic", "sketch"],
     "art_style": "sketch",
     "prompt": "An elegant letter writing set with fountain pen, ink bottle, wax seal with stamp, beautiful stationery, dried flowers, feather quill, romantic and timeless"},
    
    {"id": "obj_044", "name": "Pocket Watch", "category": "object",
     "tags": ["watch", "pocket", "vintage", "time", "sketch"],
     "art_style": "sketch",
     "prompt": "An ornate pocket watch with gold case open showing intricate clockwork inside, delicate chain, roman numerals on face, elegant and precious"},
    
    {"id": "obj_045", "name": "Baking Supplies", "category": "object",
     "tags": ["baking", "kitchen", "cooking", "sweet", "sketch"],
     "art_style": "sketch",
     "prompt": "A charming collection of baking supplies including mixing bowls, wooden spoons, cookie cutters in fun shapes, flour sifter, rolling pin, recipe cards"},
    
    {"id": "obj_046", "name": "Pressed Flower Book", "category": "object",
     "tags": ["flowers", "pressed", "nature", "book", "sketch"],
     "art_style": "sketch",
     "prompt": "An open journal with beautifully pressed flowers arranged on pages, handwritten notes about each flower, pressed leaves, nature collection book"},
    
    {"id": "obj_047", "name": "Knitting Basket", "category": "object",
     "tags": ["knitting", "craft", "cozy", "yarn", "sketch"],
     "art_style": "sketch",
     "prompt": "A woven basket overflowing with colorful yarn balls, wooden knitting needles, a partially finished cozy scarf, pattern book, warm and creative"},
    
    {"id": "obj_048", "name": "Shell Collection", "category": "object",
     "tags": ["shells", "beach", "collection", "nature", "sketch"],
     "art_style": "sketch",
     "prompt": "A beautiful collection of seashells arranged in a shadow box, various shapes and sizes, sand dollars, starfish, sea glass pieces, beach memories"},
    
    {"id": "obj_049", "name": "Magnifying Glass Set", "category": "object",
     "tags": ["magnifying", "detective", "explore", "discovery", "sketch"],
     "art_style": "sketch",
     "prompt": "A detective's magnifying glass with brass handle, alongside a small notebook, pencil, and collection of clues - footprint cast, mysterious note, exciting investigation"},
    
    {"id": "obj_050", "name": "Butterfly Collection", "category": "object",
     "tags": ["butterfly", "collection", "nature", "display", "sketch"],
     "art_style": "sketch",
     "prompt": "A beautiful display case of illustrated butterflies in various colors and patterns, labels with names, mounted on pins, scientific but beautiful, nature study"}
]

# Style suffixes for prompts
STYLE_SUFFIXES = {
    "watercolour": ", painted in soft watercolour style with gentle washes and flowing colors, delicate brushstrokes, professional children's book illustration, vibrant, age-appropriate, safe for children",
    "realistic": ", realistic illustrated style with detailed rendering, professional children's book illustration quality, vibrant colors, age-appropriate, safe for children",
    "comic": ", dynamic comic book style with bold outlines, vibrant colors, expressive details, professional children's book illustration, age-appropriate, safe for children",
    "sketch": ", pencil sketch style with detailed line work, crosshatching for shadows, artistic shading on cream paper, professional children's book illustration, age-appropriate, safe for children"
}


async def generate_batch_3():
    """Generate all 50 object/prop images for Batch 3"""
    image_gen = OpenAIImageGeneration(api_key=EMERGENT_LLM_KEY)
    
    results = []
    failed = []
    
    for i, obj in enumerate(BATCH_3_OBJECTS):
        print(f"\nGenerating {i+1}/50: {obj['name']} ({obj['art_style']})...")
        
        # Build full prompt with style suffix
        full_prompt = obj['prompt'] + STYLE_SUFFIXES[obj['art_style']]
        
        try:
            images = await image_gen.generate_images(
                prompt=full_prompt,
                model='gpt-image-1',
                number_of_images=1
            )
            
            if images and len(images) > 0:
                # Save image to file
                filename = f"/tmp/batch3_{obj['id']}_{obj['art_style']}.png"
                with open(filename, 'wb') as f:
                    f.write(images[0])
                
                result = {
                    "id": obj['id'],
                    "name": obj['name'],
                    "category": obj['category'],
                    "tags": obj['tags'],
                    "art_style": obj['art_style'],
                    "filename": filename
                }
                results.append(result)
                print(f"  ✓ Saved: {filename}")
            else:
                failed.append(obj['name'])
                print(f"  ✗ Failed: No image generated")
                
        except Exception as e:
            failed.append(obj['name'])
            print(f"  ✗ Error: {str(e)[:80]}")
        
        # Small delay to avoid rate limiting
        await asyncio.sleep(0.5)
    
    print(f"\n{'='*60}")
    print(f"BATCH 3 COMPLETE")
    print(f"{'='*60}")
    print(f"Generated: {len(results)}/50")
    print(f"Failed: {len(failed)}")
    if failed:
        print(f"Failed items: {failed}")
    
    # Save results to JSON
    with open('/tmp/batch3_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to /tmp/batch3_results.json")
    
    return results, failed


if __name__ == "__main__":
    print("Starting Batch 3: Objects & Props Generation")
    print("=" * 60)
    results, failed = asyncio.run(generate_batch_3())
