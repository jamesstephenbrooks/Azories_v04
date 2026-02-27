#!/usr/bin/env python3
"""
Batch 3B - Create pages with images for Captain Compass and Pixie Dust Adventures
Uses fal.ai for image generation with styles matching the book's aesthetic
"""

import asyncio
import os
import sys
import uuid
import logging
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

# Load environment variables from backend/.env
load_dotenv('/app/backend/.env')

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

# Add backend to path for imports
sys.path.insert(0, '/app/backend')
from fal_service import generate_image_flux

# Book data for the two books needing images
BOOKS_NEED_IMAGES = {
    "ed34dc96-9c78-4eb7-8707-90245371bea4": {
        "title": "Captain Compass and the Treasure Map",
        "art_style": "realistic",
        "genre": "Adventure",
        "style_prompt": "realistic painterly children's book illustration, nautical adventure theme, warm golden lighting, detailed ship and ocean scenes",
        "pages": [
            {"page_number": 1, "text": "Captain Compass had earned her name honestly. Her compass — a brass instrument that had belonged to her grandmother, and her grandmother's grandmother before that — pointed not just to magnetic north but, on certain days when the light was right and the wind had a particular quality, to something else entirely. Adventure, her grandmother had called it. Captain Compass had always thought this was poetic language. Then one grey morning the compass began spinning wildly on its own, pointing insistently northeast, and she understood that her grandmother had been entirely literal.", "image_prompt": "A weathered female sea captain in her 40s standing on the deck of a wooden sailing ship, holding an antique brass compass that glows mysteriously, grey morning sky, compass needle spinning"},
            {"page_number": 2, "text": "She followed the compass through three days of sailing to a harbour town she had never visited, full of narrow streets and the smell of salt and fish and old timber. The compass led her down an alley, around two corners, and into a shop so small and so full that there was barely room to stand. An old sailor sat behind the counter surrounded by the accumulated objects of a lifetime at sea. He looked at her compass without surprise. 'Been expecting you,' he said. 'Or someone like you. Bottom shelf, rolled up, tied with seaweed. Been waiting forty years.'", "image_prompt": "A tiny cramped antique shop filled with nautical treasures, brass instruments, old maps, ship models, an elderly bearded sailor behind the counter, warm dusty light through a small window"},
            {"page_number": 3, "text": "The map was large and old, drawn on something that felt like neither paper nor parchment but somewhere between the two. The coastlines were precise — she could identify real places in them — but the island marked with the red X had no name and appeared on none of the charts she carried. The turtle shape was unmistakable: a broad oval body, four stubby peninsulas, and a distinctive notch in the top right that could only be the turtle's head. She rolled it carefully back up. She paid the old sailor what he asked without negotiating. Some things were not worth haggling over.", "image_prompt": "Close-up of hands unrolling an ancient treasure map on a wooden table, showing a turtle-shaped island with a red X marked on it, intricate hand-drawn coastlines, candlelight"},
            {"page_number": 4, "text": "Planning the route took two weeks. The turtle island, triangulated from three separate landmarks shown on the map, placed it in a stretch of ocean she knew only by reputation: technically navigable but poorly charted, subject to unusual currents, and visited rarely enough that no reliable account of its conditions existed. She provisioned the ship carefully — more water than she thought she needed, twice the standard medical supplies, charts of every surrounding area. Her first mate, a cautious man named Boone, looked at the preparations and asked no questions. He had sailed with her long enough to know that questions would be answered in due course.", "image_prompt": "A ship's cabin with maps spread across a large table, Captain Compass studying charts with compass and navigation tools, supplies being loaded visible through the porthole, her first mate Boone watching"},
            {"page_number": 5, "text": "Twelve days at sea. Three genuine storms, each one different — the first short and violent, the second slow and wearing, the third disorienting in its fog and stillness. She navigated by the old map's landmarks, cross-referencing against her own instruments, finding her way through the poorly charted water with patience and precision. On the eleventh day, Boone called from the lookout. On the horizon, just visible, was a shape — low and broad, with exactly the distinctive outline she had spent twelve days trying to find. Turtle island, exactly as drawn, lying in the morning light like a geographical promise kept.", "image_prompt": "A sailing ship on the ocean at sunrise, a turtle-shaped island visible on the distant horizon, golden morning light, a sailor in the crow's nest pointing, dramatic sky"},
            {"page_number": 6, "text": "She rowed ashore in the ship's tender, alone, which Boone protested and she overruled. The beach was white sand, undisturbed except for bird tracks. The vegetation was dense but not impassable. She followed the map's instructions: find the oldest tree visible from the beach, walk toward it, count one hundred paces north from its base, then turn east and walk until you reach flat rock. The oldest tree was enormous, its trunk silver-grey with age. She counted carefully. At one hundred paces: flat rock, exactly as described, half-buried in vegetation, clearly undisturbed for a very long time.", "image_prompt": "A woman rowing a small boat toward a pristine white sand beach, dense tropical vegetation beyond, an enormous ancient silver-grey tree dominating the landscape, morning light"},
            {"page_number": 7, "text": "The dig was harder than she expected. The soil beneath the flat rock was dense and full of roots, and the chest was deeper than the map's markings had suggested — nearly a metre down, and heavy. It took two hours and left her thoroughly muddy. When the lid finally opened, she found it lined with oilskin that had kept the interior perfectly dry. Inside were not jewels or gold coins but something she had not expected: fifty maps, each carefully rolled and sealed with wax, each showing a different coastline with a different X, each in the same hand as the first map.", "image_prompt": "A muddy treasure chest being opened in a jungle clearing, revealing dozens of rolled-up maps inside, the captain's dirty hands lifting the lid, dappled sunlight through leaves"},
            {"page_number": 8, "text": "She sat on the beach for a long time, going through them. Each map was clearly genuine — precise coastlines, careful notation, the same quality of observation she had seen in the turtle island map. She recognised some of the coastlines. Others were unfamiliar. Some Xs were marked on islands. Some were on mainland coasts. One was underwater, marked with a depth notation that suggested an extraordinary dive. Each one was a different puzzle, a different journey, a different question waiting to be answered. Her compass, she noticed, had stopped spinning and was now pointing steadily and calmly, as if satisfied.", "image_prompt": "Captain Compass sitting on a white sand beach surrounded by unrolled maps spread around her, sunset light, her brass compass lying still and steady beside her, look of wonder on her face"},
            {"page_number": 9, "text": "She returned to the ship as the sun was setting, the chest of maps under her arm, still muddy from the dig. Boone looked at the chest and then at her face and understood without being told that she had found something significant. 'Worth the twelve days?' he asked. She thought about the maps spread around her on the beach — fifty new mysteries, fifty new destinations, a lifetime's worth of questions to answer. 'Worth considerably more than that,' she said. She went below to wash the mud off and start cataloguing. She worked through the night.", "image_prompt": "Captain Compass climbing aboard her ship at sunset carrying a treasure chest, her first mate Boone helping her aboard, warm orange sunset sky, she looks tired but elated"},
            {"page_number": 10, "text": "By morning she had sorted the maps into categories: coastal, island, underwater, inland. She had identified seventeen that she could navigate to immediately, using routes she already knew. The rest would require planning, new charts, possibly new expertise. The compass sat on the table beside her, pointing steadily northeast — not to any of the maps, she realised, but simply in the direction they had come from. It had done its job. Now the work was hers. She rolled the maps carefully, retied each one, and placed them back in the chest. Then she went on deck, called Boone, and said: 'Set course northeast. I'll explain when we're underway.' THE END", "image_prompt": "Dawn light in the captain's cabin, maps sorted into neat piles on the table, the brass compass pointing steadily, Captain Compass looking out the porthole at the horizon with determination, ready for new adventures"},
        ]
    },
    "56c45425-ba3b-421d-b17f-f13321c32f65": {
        "title": "Pixie Dust Adventures",
        "art_style": "watercolour",
        "genre": "Fantasy",
        "style_prompt": "soft watercolour children's book illustration, magical fantasy theme, gentle pastel colors with sparkles, whimsical fairy village aesthetic",
        "pages": [
            {"page_number": 1, "text": "Every pixie in the village of Thornhollow produced dust. It was as natural as breathing — a fine, sparkling substance that emerged from the fingertips during moments of focus or emotion, each pixie's dust unique in colour and quality and use. Gold dust from Bram made seeds germinate in hours. Blue dust from the sisters Willa and Nell calmed storms. Rose-pink dust from old Mosswick could find anything that had been lost. Fern's dust was a warm amber that smelled unmistakably of biscuits. Fern was seventeen and had been waiting for her dust to do something useful for three years. So far: biscuit smell.", "image_prompt": "A magical fairy village with tiny mushroom houses and flower homes, pixies flying with colorful sparkling dust trailing from their fingertips, a young pixie named Fern with amber-colored wings looking uncertain, warm amber sparkles around her hands"},
            {"page_number": 2, "text": "She practised every morning before the village woke, sitting cross-legged in the meadow, concentrating with the focused intensity that the dust-masters said was essential. Her fingers would glow. The amber light would build. And then: nothing useful. Just the warmth, and the smell, and the occasional small creature that wandered over apparently attracted by the scent, which Fern would acknowledge politely before sending it on its way. The dust-master Aldric said she was trying too hard. Her grandmother said the best things came when you stopped looking for them. Fern found this advice irritating in direct proportion to how frequently she heard it.", "image_prompt": "A young pixie girl sitting cross-legged in a dewy morning meadow, amber light glowing from her fingertips, small woodland creatures approaching curiously, soft watercolour morning mist"},
            {"page_number": 3, "text": "The Autumn Gathering required every pixie to contribute their dust to the communal reservoir — a great crystal vessel at the village centre that powered the enchantments keeping Thornhollow's crops frost-free through winter. Every pixie filled their allotted section. Fern's section was small, in recognition of her uncertain abilities, but it was still required. She spent the week before the Gathering in increasing anxiety, practising each morning, achieving amber warmth and biscuit smell, and returning home each evening to sit in her grandmother's kitchen feeling like the one broken thing in a world of functioning ones.", "image_prompt": "A beautiful glowing crystal vessel in the center of a pixie village square, pixies gathering around it with different colored dusts streaming from their hands, autumn leaves falling, magical atmosphere"},
            {"page_number": 4, "text": "Three nights before the Gathering she found the barn owl. It was in the ditch at the edge of the meadow — not injured in any obvious way, but clearly in distress, its feathers fluffed, its breathing laboured, its eyes half-closed. She crouched beside it. Owls were not, technically, her area; there were pixies whose dust worked specifically with birds. But it was the middle of the night and she was there and the owl was there and it needed something, and she knew what needing something looked like.", "image_prompt": "A small pixie girl crouching beside a distressed barn owl in tall moonlit grass, the owl's feathers fluffed up, gentle concerned expression on Fern's face, soft moonlight and stars"},
            {"page_number": 5, "text": "She did what she always did when she didn't know what else to do: she sat with it. She made herself still and calm and simply present, and she let the amber warmth build in her hands without trying to direct it, and held her palms near the owl without touching it, because touching a distressed wild creature is not helpful and she knew this. The warmth spread outward from her hands in slow pulses. The owl's breathing steadied. Its feathers relaxed fractionally. She stayed for two hours. By the time she left, the owl was alert and upright and watching her with the focused attention of a well owl.", "image_prompt": "Fern the pixie with her hands held near a barn owl, warm amber light radiating from her palms in gentle waves, the owl looking calmer and more alert, magical healing glow, night scene"},
            {"page_number": 6, "text": "She came back the next night. The owl was there — not in distress now, but waiting, she thought, though she told herself that was fanciful. She sat with it again. The amber warmth came easily, more easily than it ever had in the morning practice sessions — something about the darkness and the stillness and the specific purpose. She noticed that where the warmth touched the grass it grew denser and greener even in the cold. She noticed that the owl's feathers had the particular smooth quality of a creature in good health. She noticed that the biscuit smell was stronger than usual. She noticed that she felt, for the first time in years, like she was doing something exactly right.", "image_prompt": "Fern and the barn owl sitting together peacefully in a meadow at night, the grass around them growing greener and more vibrant where the amber light touches it, comfortable companionship"},
            {"page_number": 7, "text": "The night before the Gathering she found not one creature in need but three: a hedgehog that had been disturbed from its hibernation too early, cold and confused; a young fox with a thorn in its pad; and a field mouse that had fallen into a water butt and was exhausted from keeping itself afloat. She dealt with each one in turn — the hedgehog wrapped in warmth and guided to a new hibernation spot, the fox's thorn carefully removed while she maintained the calming presence, the mouse rescued and dried and set on its way. By the time she reached home, her hands were glowing so strongly the whole lane was lit amber.", "image_prompt": "Fern the pixie helping woodland creatures at night - a hedgehog, a small fox, and a mouse - her hands glowing bright amber, the entire forest lane lit up with her warm magical light"},
            {"page_number": 8, "text": "At the Gathering, when Fern approached the crystal vessel with her dust, something unexpected happened. The vessel, which received each pixie's contribution with a specific resonant tone corresponding to its power type, sang a note she had never heard before — a deep, warm, sustained chord that silenced the assembled pixies and brought Aldric from the back of the crowd at a run. He stood before the vessel and listened to it ring and then turned to look at Fern with an expression she had never seen on the dust-master's face before: surprise. 'Comfort dust,' he said. 'The vessel is singing comfort dust.'", "image_prompt": "The great crystal vessel singing and glowing with warm amber light as Fern contributes her dust, all the pixies in the village watching in amazement, an elderly pixie dust-master looking surprised and impressed"},
            {"page_number": 9, "text": "Aldric explained to the gathered pixies what comfort dust was — he had read about it but never seen it and had half-believed it was legend. It did not grow crops or find lost things or change the weather. It did something quieter and harder to measure: it found distress in living things and relieved it. In frightened creatures it produced calm. In sick creatures it supported recovery. In lonely creatures — and this was the part that made several older pixies look away — it produced the particular comfort of feeling not alone. The reservoir, Aldric said, had never held comfort dust before. The enchantments it would power over the coming winter would be different from any previous year.", "image_prompt": "Wise elderly pixie Aldric addressing a crowd of pixies around the glowing crystal vessel, explaining about comfort dust, Fern standing humbly nearby, magical sparkles in the air"},
            {"page_number": 10, "text": "The winter that followed was remembered in Thornhollow for a long time. The crops were fine, as they always were, but more than that: it was a winter in which, inexplicably, nothing seemed to go badly wrong. Animals found their way home. People who were ill recovered more quickly than expected. Children who were frightened became calm. Nobody could prove it was the dust. Nobody tried very hard to prove it wasn't, either. Fern spent the winter as she had always spent it, sitting in the meadow in the cold mornings, amber warmth building in her hands, smelling of biscuits, available to whatever needed her. She had stopped practising. She had started simply being present. It turned out those were not the same thing at all. THE END", "image_prompt": "Fern the pixie sitting peacefully in a snowy winter meadow, amber light glowing warmly from her hands, woodland creatures gathered around her, cozy magical winter scene, the pixie village visible in the background with warm lights in windows"},
        ]
    }
}


async def create_book_pages_with_images(db, book_id: str, book_data: dict, dry_run: bool = True):
    """Create pages and generate images for a book"""
    
    title = book_data["title"]
    style_prompt = book_data["style_prompt"]
    pages = book_data["pages"]
    
    logger.info(f"\n{'='*60}")
    logger.info(f"📚 {title}")
    logger.info(f"   Style: {book_data['art_style']}, Genre: {book_data['genre']}")
    logger.info(f"{'='*60}")
    
    if dry_run:
        for page in pages:
            logger.info(f"   Page {page['page_number']}: {len(page['text'])} chars text, will generate image")
        logger.info(f"\n   Total: {len(pages)} pages to create with images")
        return len(pages)
    
    # Actually create pages and generate images
    embedded_pages = []
    created_count = 0
    
    for page in pages:
        page_num = page["page_number"]
        text = page["text"]
        image_prompt = page.get("image_prompt", text[:200])
        page_id = str(uuid.uuid4())
        
        # Generate full prompt with style
        full_prompt = f"{style_prompt}, {image_prompt}, high quality, detailed"
        
        logger.info(f"\n   Page {page_num}: Generating image...")
        
        image_url = None
        try:
            result = await generate_image_flux(
                prompt=full_prompt,
                model="flux-dev",
                image_size="landscape_16_9",
                num_images=1,
                guidance_scale=3.5,
                num_inference_steps=28
            )
            
            if result.get("success") and result.get("images"):
                image_url = result["images"][0].get("url")
                logger.info(f"   ✅ Page {page_num} image generated")
            else:
                logger.warning(f"   ⚠️ Page {page_num} image failed - no URL returned")
        except Exception as e:
            logger.error(f"   ❌ Page {page_num} image error: {e}")
        
        # Create page document
        new_page = {
            "id": page_id,
            "book_id": book_id,
            "page_number": page_num,
            "text_content": text,
            "image_url": image_url,
            "audio_url": None,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        # Insert into pages collection
        await db.pages.insert_one(new_page)
        
        # Add to embedded pages
        embedded_pages.append({
            "id": page_id,
            "page_number": page_num,
            "text_content": text,
            "image_url": image_url,
            "audio_url": None
        })
        
        created_count += 1
        
        # Small delay between generations to avoid rate limits
        await asyncio.sleep(1)
    
    # Update book with embedded pages
    await db.books.update_one(
        {"id": book_id},
        {"$set": {"pages": embedded_pages}}
    )
    
    logger.info(f"\n   ✅ {title}: {created_count} pages created with images")
    return created_count


async def main(dry_run: bool = True):
    """Main function"""
    
    mongo_url = os.environ.get('MONGO_URL')
    db_name = os.environ.get('DB_NAME', 'test_database')
    
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    mode = "DRY RUN" if dry_run else "APPLYING"
    logger.info(f"\n{'#'*60}")
    logger.info(f" {mode} - Create Pages with Images")
    logger.info(f" Books: Captain Compass, Pixie Dust Adventures")
    logger.info(f" Total: 20 pages, 20 images to generate via fal.ai")
    logger.info(f"{'#'*60}")
    
    total_created = 0
    
    for book_id, book_data in BOOKS_NEED_IMAGES.items():
        # Verify book exists
        book = await db.books.find_one({"id": book_id})
        if not book:
            logger.error(f"❌ Book not found: {book_data['title']}")
            continue
        
        # Check if pages already exist
        existing_pages = await db.pages.count_documents({"book_id": book_id})
        if existing_pages > 0:
            # Check if images exist
            pages_without_images = await db.pages.count_documents({"book_id": book_id, "image_url": None})
            if pages_without_images > 0:
                logger.info(f"⚠️ {book_data['title']} has {existing_pages} pages but {pages_without_images} need images - will generate")
                # Delete existing pages to recreate with images
                await db.pages.delete_many({"book_id": book_id})
                await db.books.update_one({"id": book_id}, {"$set": {"pages": []}})
                logger.info(f"   Cleared existing pages to regenerate with images")
            else:
                logger.info(f"⚠️ {book_data['title']} already has {existing_pages} pages with images - skipping")
                continue
        
        created = await create_book_pages_with_images(db, book_id, book_data, dry_run)
        total_created += created
    
    logger.info(f"\n{'#'*60}")
    logger.info(f" {mode} COMPLETE")
    logger.info(f" Pages created: {total_created}")
    logger.info(f"{'#'*60}\n")
    
    client.close()


if __name__ == "__main__":
    dry_run = "--apply" not in sys.argv
    asyncio.run(main(dry_run))
