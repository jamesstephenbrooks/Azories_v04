#!/usr/bin/env python3
"""
REPAIR SCRIPT: Regenerate 17 books with missing images
Using fal.ai FLUX (with valid key)
"""

import asyncio
import os
import sys
import shutil
import aiohttp
from pathlib import Path
from datetime import datetime
from bson import ObjectId

APP_DIR = Path(__file__).parent
BACKEND_DIR = APP_DIR / 'backend'
CONTENT_DIR = APP_DIR / 'content' / 'books' / 'completed'
PUBLIC_DIR = APP_DIR / 'frontend' / 'public' / 'book-assets'

from dotenv import load_dotenv
load_dotenv(BACKEND_DIR / '.env')

sys.path.insert(0, str(BACKEND_DIR))
from motor.motor_asyncio import AsyncIOMotorClient
from fal_service import generate_image_flux

MONGO_URL = os.environ.get('MONGO_URL')
DB_NAME = os.environ.get('DB_NAME', 'test_database')

images_generated = 0
estimated_cost = 0.0

# Templates for the 17 affected books
BOOK_TEMPLATES = {
    "The Unicorn's Rainbow Bridge": {
        "age_range": "3-6",
        "genre": "Fantasy",
        "art_style": "watercolour",
        "style_prompt": "Soft magical watercolour children's book illustration, unicorn theme, rainbow colors, dreamy atmosphere",
        "characters": {
            "main": "Starlight, a young unicorn with a shimmering white coat and a rainbow-colored mane"
        },
        "pages": [
            {"text": "The Unicorn's Rainbow Bridge\n\nA Magical Journey", "scene": "Title page: Beautiful unicorn standing before a rainbow bridge in clouds"},
            {"text": "Starlight was a young unicorn who lived in the Meadow of Dreams.", "scene": "Young white unicorn with rainbow mane in magical meadow"},
            {"text": "One day, she discovered a mysterious rainbow that touched the ground!", "scene": "Unicorn discovering rainbow touching ground in meadow"},
            {"text": "\"I wonder where it leads,\" Starlight said, stepping onto the colors.", "scene": "Unicorn stepping onto rainbow bridge, curious expression"},
            {"text": "The rainbow became a bridge! Each color felt different under her hooves.", "scene": "Unicorn walking on rainbow bridge through clouds"},
            {"text": "Red was warm like sunshine. Orange tickled like butterflies!", "scene": "Unicorn on red and orange sections of rainbow, playful"},
            {"text": "Yellow made her giggle. Green smelled like fresh grass.", "scene": "Unicorn on yellow and green, happy expressions"},
            {"text": "Blue was cool and calm. Purple sparkled with magic!", "scene": "Unicorn on blue and purple sections, magical sparkles"},
            {"text": "At the end, she found the Rainbow Kingdom - home of all unicorns!", "scene": "Unicorn arriving at magnificent Rainbow Kingdom with other unicorns"},
            {"text": "\"Welcome home, Starlight,\" they said. She had found where she belonged.\n\nThe End", "scene": "Unicorn being welcomed by family of unicorns, happy ending"}
        ]
    },
    
    "The Wizard's Apprentice": {
        "age_range": "3-6",
        "genre": "Fantasy",
        "art_style": "watercolour",
        "style_prompt": "Soft watercolour children's book illustration, magical wizard theme, warm purples and golds",
        "characters": {
            "main": "Finn, a young boy with messy red hair, wearing an oversized purple wizard robe"
        },
        "pages": [
            {"text": "The Wizard's Apprentice\n\nA Magical Story", "scene": "Title page: Young wizard apprentice in magical tower with floating books"},
            {"text": "Finn was the wizard's new helper. Everything was magical!", "scene": "Finn arriving at magical tower, eyes wide with wonder"},
            {"text": "His first task: sort the spell ingredients. But the jars were talking!", "scene": "Finn surrounded by talking magical jars with faces"},
            {"text": "\"Careful with the moon dust!\" POOF! Too late.", "scene": "Finn spilling sparkly moon dust everywhere"},
            {"text": "The broom started dancing! The cauldron began singing!", "scene": "Dancing broom and singing cauldron, Finn laughing"},
            {"text": "\"Magic is messy at first,\" the wizard smiled kindly.", "scene": "Kind old wizard smiling at the magical chaos"},
            {"text": "Together they cleaned up with a special spell!", "scene": "Finn casting cleaning spell, items floating back"},
            {"text": "\"Every great wizard started just like you,\" said the wizard.", "scene": "Wizard showing Finn old photos of his mistakes"},
            {"text": "Finn practiced every day. Some spells worked, some went SPLAT!", "scene": "Montage of Finn practicing magic"},
            {"text": "And that's how the smallest apprentice became the bravest wizard.\n\nThe End", "scene": "Finn proudly casting spell, wizard clapping"}
        ]
    },
    
    "Fairies of Moonlight Meadow": {
        "age_range": "3-6",
        "genre": "Fantasy",
        "art_style": "watercolour",
        "style_prompt": "Ethereal watercolour children's book illustration, fairy theme, silver moonlight, pastel flowers",
        "characters": {
            "main": "Luna, Dewdrop, and Sparkle - three tiny fairies with delicate wings"
        },
        "pages": [
            {"text": "Fairies of Moonlight Meadow\n\nA Bedtime Adventure", "scene": "Title page: Three tiny fairies dancing in moonlit meadow"},
            {"text": "When the moon rises, fairies come out to play in Moonlight Meadow.", "scene": "Beautiful meadow at night, fairies emerging"},
            {"text": "Luna lights the path with her silver glow.", "scene": "Luna fairy with silver wings creating light path"},
            {"text": "Dewdrop makes flowers sparkle with morning dew!", "scene": "Dewdrop fairy touching flowers, making them shimmer"},
            {"text": "Sparkle loves playing with fireflies!", "scene": "Sparkle fairy playing with fireflies, laughing"},
            {"text": "Tonight they found a lost baby bunny!", "scene": "Fairies discovering scared baby bunny"},
            {"text": "\"Don't worry, we'll help you find home.\"", "scene": "Luna comforting bunny, fairies gathering"},
            {"text": "They followed the moonbeams through the meadow.", "scene": "Fairies leading bunny through meadow"},
            {"text": "The bunny's family was waiting by the old oak!", "scene": "Joyful reunion with bunny family"},
            {"text": "The fairies flew home as the sun rose. Sweet dreams!\n\nThe End", "scene": "Fairies returning home at dawn"}
        ]
    },
    
    "Elves and the Magic Tree": {
        "age_range": "3-6",
        "genre": "Fantasy",
        "art_style": "watercolour",
        "style_prompt": "Enchanted forest watercolour children's book illustration, elves, rich greens and autumn colors",
        "characters": {
            "main": "Acorn and Maple, twin elves with pointed ears and green tunics"
        },
        "pages": [
            {"text": "Elves and the Magic Tree\n\nA Tale of the Forest", "scene": "Title page: Two elves before magnificent glowing tree"},
            {"text": "Twin elves Acorn and Maple lived in the Whispering Woods.", "scene": "Twin elves in cozy treehouse, forest morning"},
            {"text": "Their job was caring for the Great Magic Tree.", "scene": "Elves tending to enormous magical tree"},
            {"text": "One morning, the tree looked sick! Leaves were falling!", "scene": "Worried elves looking at wilting tree"},
            {"text": "\"We must find the Golden Acorn to heal it!\"", "scene": "Elves looking at old map"},
            {"text": "They searched high where the wise owl lived.", "scene": "Elves climbing branches, talking to owl"},
            {"text": "They searched low where mushrooms grew.", "scene": "Elves among colorful mushrooms"},
            {"text": "They found it in a squirrel's treasure collection!", "scene": "Elves discovering golden acorn"},
            {"text": "Golden light spread as they planted it!", "scene": "Magical golden light healing tree"},
            {"text": "The forest was saved!\n\nThe End", "scene": "Celebratory scene, healthy tree, happy creatures"}
        ]
    },
    
    "Pixie Dust Adventures": {
        "age_range": "3-6",
        "genre": "Fantasy",
        "art_style": "watercolour",
        "style_prompt": "Magical sparkly watercolour children's book illustration, pixie theme, pastels and glitter",
        "characters": {
            "main": "Pip, a tiny pixie with sparkling blue wings and wild purple hair with flowers"
        },
        "pages": [
            {"text": "Pixie Dust Adventures\n\nA Magical Tale", "scene": "Title page: Tiny pixie flying through magical forest with sparkles"},
            {"text": "Pip was the smallest pixie. Her wings sparkled blue.", "scene": "Pip in beautiful hollow with dewdrops and flowers"},
            {"text": "Every pixie had a job. But Pip didn't know hers yet.", "scene": "Other pixies working, Pip watching left out"},
            {"text": "\"I want to find my magic!\" Pip flew into the woods.", "scene": "Pip flying determinedly into mystical forest"},
            {"text": "She met a sad ladybug missing her spots. Pip sprinkled dust - spots appeared!", "scene": "Pip helping ladybug with pixie dust"},
            {"text": "A wilted flower begged for help. Pip's dust made it bloom!", "scene": "Pip making flower bloom magnificently"},
            {"text": "A grumpy toad's puddle turned into a sparkling pond!", "scene": "Pip transforming puddle, toad happy"},
            {"text": "\"I found my gift! I make things HAPPY!\"", "scene": "Pip flying excitedly, sparkle trail"},
            {"text": "The Queen Pixie smiled. \"The rarest gift of all.\"", "scene": "Queen crowning Pip with flower crown"},
            {"text": "Pip's dust made the whole forest smile!\n\nThe End", "scene": "Pip flying over happy magical forest"}
        ]
    },
    
    "The Enchanted Carousel": {
        "age_range": "3-6",
        "genre": "Fantasy",
        "art_style": "watercolour",
        "style_prompt": "Whimsical vintage watercolour children's book illustration, carousel, pastels and golden lights",
        "characters": {
            "main": "Mia, a 5-year-old girl with two dark braids and a vintage dress"
        },
        "pages": [
            {"text": "The Enchanted Carousel\n\nA Magical Ride", "scene": "Title page: Glowing carousel at twilight with magical horses"},
            {"text": "Mia found an old carousel in the park. It looked forgotten but beautiful.", "scene": "Mia discovering ornate carousel covered in vines"},
            {"text": "She climbed onto a white horse. The carousel began to spin!", "scene": "Mia on white carousel horse, lights glowing"},
            {"text": "The horse winked! \"Hold tight, we're going on an adventure!\"", "scene": "Carousel horse winking, magical sparkles"},
            {"text": "WHOOSH! They flew into the sky!", "scene": "Carousel lifting into starry sky, Mia amazed"},
            {"text": "They soared over candy mountains and starlight rivers.", "scene": "Flying over magical candy landscape"},
            {"text": "They raced through cloud animals and floating gardens.", "scene": "Flying through cloud animals, flower gardens"},
            {"text": "\"Time to go home,\" the horse said gently.", "scene": "Horse and Mia descending at sunrise"},
            {"text": "Mia stepped off with a magical flower in her hand.", "scene": "Mia holding glowing flower, amazed"},
            {"text": "\"Come back anytime,\" the horse whispered.\n\nThe End", "scene": "Mia waving at carousel at sunset"}
        ]
    },
    
    "Captain Compass and the Treasure Map": {
        "age_range": "6-8",
        "genre": "Adventure",
        "art_style": "realistic",
        "style_prompt": "Detailed adventure children's book illustration, expedition theme, sunset colors and ocean blues",
        "characters": {
            "main": "Captain Compass (Emma), a young adventurer with compass necklace and explorer hat"
        },
        "pages": [
            {"text": "Captain Compass and the Treasure Map\n\nAn Adventure Begins", "scene": "Title page: Young captain holding ancient map, ocean sunset"},
            {"text": "Emma found a dusty map in her grandmother's attic.", "scene": "Emma in attic discovering treasure map"},
            {"text": "\"I'm going to find that treasure!\"", "scene": "Emma with parrot, looking determined"},
            {"text": "She gathered her crew: Max, Sofia, and Leo.", "scene": "Four young adventurers preparing ship"},
            {"text": "They sailed through Whispering Waves.", "scene": "Ship sailing, dolphins alongside"},
            {"text": "\"Storm ahead!\" Emma steered them through.", "scene": "Emma steering through dramatic storm"},
            {"text": "The island appeared through the mist!", "scene": "Ship approaching mysterious island"},
            {"text": "They followed the map through jungle vines.", "scene": "Kids hiking through jungle"},
            {"text": "The X marked a hidden cave!", "scene": "Kids entering cave with flashlights"},
            {"text": "The real treasure was ancient books and artifacts!\n\nThe End", "scene": "Kids surrounded by glowing books, amazed"}
        ]
    },
    
    "The Jungle Explorers Club": {
        "age_range": "6-8",
        "genre": "Adventure",
        "art_style": "realistic",
        "style_prompt": "Detailed jungle expedition children's book illustration, lush greens, exotic animals",
        "characters": {
            "main": "The Jungle Explorers: Zara with binoculars, Kai the animal expert, Bella the plant specialist"
        },
        "pages": [
            {"text": "The Jungle Explorers Club\n\nInto the Wild", "scene": "Title page: Three kids in explorer gear at jungle entrance"},
            {"text": "The Jungle Explorers had one mission: discover something new!", "scene": "Kids in treehouse clubhouse, planning"},
            {"text": "Deep in the Amazon, they heard a strange sound.", "scene": "Kids in dense jungle, mysterious sound"},
            {"text": "Kai spotted jaguar tracks!", "scene": "Kids examining paw prints"},
            {"text": "Bella found glowing mushrooms!", "scene": "Bioluminescent mushrooms lighting path"},
            {"text": "Zara saw it first - a hidden waterfall!", "scene": "Zara pointing at distant waterfall"},
            {"text": "Behind the waterfall was a secret garden!", "scene": "Magical garden with color-changing flowers"},
            {"text": "A baby jaguar played among the flowers!", "scene": "Cute jaguar cub in magical garden"},
            {"text": "They promised to keep the secret.", "scene": "Kids making promise, jaguar watching"},
            {"text": "The greatest treasure: a secret worth keeping.\n\nThe End", "scene": "Kids leaving, looking back at waterfall"}
        ]
    },
    
    "Mountain Climbing Mice": {
        "age_range": "6-8",
        "genre": "Adventure",
        "art_style": "realistic",
        "style_prompt": "Detailed children's book illustration, tiny adventurous mice, majestic mountain scenery",
        "characters": {
            "main": "Marco and Mia, two brave mice in tiny climbing gear"
        },
        "pages": [
            {"text": "Mountain Climbing Mice\n\nA Tiny Big Adventure", "scene": "Title page: Two tiny mice at base of enormous mountain"},
            {"text": "Marco and Mia looked up at Cheese Peak.", "scene": "Two mice with climbing gear staring at peak"},
            {"text": "\"Mice CAN climb mountains!\" Mia declared.", "scene": "Determined mice beginning climb"},
            {"text": "First challenge: Crumb Canyon rope bridge!", "scene": "Mice crossing rope bridge over canyon"},
            {"text": "They climbed through the Forest of Giant Pines.", "scene": "Mice among enormous pine trees"},
            {"text": "A friendly eagle gave them a lift!", "scene": "Mice riding on eagle's back"},
            {"text": "The ice was slippery! They helped each other.", "scene": "Mice climbing icy cliff together"},
            {"text": "At last, the summit!", "scene": "Mice at mountain peak, triumphant"},
            {"text": "They planted a tiny flag: \"Mice CAN!\"", "scene": "Mice planting flag at sunrise"},
            {"text": "Size doesn't matter - only courage does.\n\nThe End", "scene": "Mice sliding down, village celebrating below"}
        ]
    },
    
    "Space Station School": {
        "age_range": "6-8",
        "genre": "Science Fiction",
        "art_style": "realistic",
        "style_prompt": "Futuristic space station children's book illustration, blue and silver, Earth view",
        "characters": {
            "main": "Nova, a 7-year-old with short black hair in a silver space suit"
        },
        "pages": [
            {"text": "Space Station School\n\nLearning Among the Stars", "scene": "Title page: Space station orbiting Earth, kids visible"},
            {"text": "Nova's classroom floated 250 miles above Earth!", "scene": "Futuristic classroom, kids floating"},
            {"text": "Math was fun calculating asteroid speeds!", "scene": "Nova doing math with floating asteroids"},
            {"text": "Science class: growing plants in zero gravity!", "scene": "Plants growing in all directions"},
            {"text": "Lunch: catching floating food globes!", "scene": "Kids catching food spheres, laughing"},
            {"text": "PE was zero-G soccer!", "scene": "Kids playing zero gravity soccer"},
            {"text": "Art class: painting Earth from above!", "scene": "Kids painting Earth at easels"},
            {"text": "Nova's favorite: astronaut training!", "scene": "Nova in training simulator"},
            {"text": "At night, watching shooting stars from bed.", "scene": "Kids watching meteors from pods"},
            {"text": "\"School in space is out of this world!\"\n\nThe End", "scene": "Nova writing in journal, stars twinkling"}
        ]
    },
    
    "The Friendly Martians": {
        "age_range": "3-6",
        "genre": "Science Fiction",
        "art_style": "watercolour",
        "style_prompt": "Fun space watercolour children's book illustration, Mars setting, friendly alien designs",
        "characters": {
            "main": "Ziggy and Zara, small green Martians with big friendly eyes and heart-shaped antennae"
        },
        "pages": [
            {"text": "The Friendly Martians\n\nA Story About Making Friends", "scene": "Title page: Cute green Martians waving from Mars"},
            {"text": "Ziggy and Zara lived on Mars. They had rocks but no friends.", "scene": "Martians looking lonely on red Mars"},
            {"text": "One day, a spaceship landed! Out came Luna.", "scene": "Spaceship landing, girl stepping out"},
            {"text": "The Martians were scared. Luna looked different!", "scene": "Martians hiding behind rocks"},
            {"text": "But Luna waved. \"Want to play?\"", "scene": "Luna waving friendly, Martians curious"},
            {"text": "They played hide and seek behind craters!", "scene": "Playing hide and seek on Mars"},
            {"text": "They built sandcastles from red dust!", "scene": "All three building Mars dust castles"},
            {"text": "They bounced high in low gravity!", "scene": "All bouncing high, laughing"},
            {"text": "\"Will you come back?\" asked Ziggy.", "scene": "Sad farewell at spaceship"},
            {"text": "\"Friends visit, no matter how far!\"\n\nThe End", "scene": "Luna waving from ship, Martians waving"}
        ]
    },
    
    "Gadget Girl and the Invention Fair": {
        "age_range": "6-8",
        "genre": "Science Fiction",
        "art_style": "cartoon",
        "style_prompt": "Bright STEM cartoon children's book illustration, inventions, workshop setting",
        "characters": {
            "main": "Gwen, an 8-year-old inventor with messy ponytail, goggles, and tool belt"
        },
        "pages": [
            {"text": "Gadget Girl and the Invention Fair\n\nA Story of Creativity", "scene": "Title page: Young inventor surrounded by colorful inventions"},
            {"text": "Gwen LOVED inventing! Her garage was full of gadgets.", "scene": "Gwen in messy workshop"},
            {"text": "The Invention Fair was next week! What to make?", "scene": "Gwen looking at fair poster"},
            {"text": "Flying toaster? CRASH! Too much power.", "scene": "Toaster flying chaotically"},
            {"text": "Homework robot? It ate the homework!", "scene": "Robot eating papers"},
            {"text": "Rocket shoes? UP but no DOWN!", "scene": "Gwen stuck on ceiling"},
            {"text": "Then she saw her brother struggling with his backpack.", "scene": "Watching brother struggle"},
            {"text": "IDEA! The Hover-Pack carries itself!", "scene": "Eureka moment, sketching"},
            {"text": "Kids LOVED it at the fair!", "scene": "Kids trying Hover-Pack"},
            {"text": "\"The best inventions help others.\"\n\nThe End", "scene": "Gwen with trophy, brother hugging her"}
        ]
    },
    
    "The Secret Code Club": {
        "age_range": "6-8",
        "genre": "Mystery",
        "art_style": "realistic",
        "style_prompt": "Detailed mystery children's book illustration, codes and ciphers, secret agent theme",
        "characters": {
            "main": "The Code Breakers: Sam, Lily, and Jake with decoder rings"
        },
        "pages": [
            {"text": "The Secret Code Club\n\nCracking the Mystery", "scene": "Title page: Three kids with coded messages floating"},
            {"text": "Sam, Lily, and Jake solved coded mysteries!", "scene": "Kids in tree house with code wheels"},
            {"text": "They found a strange note: GSRH RH GSV URMOW!", "scene": "Kids finding coded note in library"},
            {"text": "\"Substitution cipher!\" They decoded it.", "scene": "Kids working at table with wheels"},
            {"text": "THIS IS THE FIRST! More codes to find!", "scene": "Kids reading decoded message"},
            {"text": "They found codes all over town!", "scene": "Kids running around finding notes"},
            {"text": "Five clues led to the old clock tower!", "scene": "Kids approaching clock tower"},
            {"text": "Inside: a time capsule from 50 years ago!", "scene": "Opening old time capsule"},
            {"text": "Same club, same codes - 50 years earlier!", "scene": "Old photos and notes inside"},
            {"text": "They found their club's history!\n\nThe End", "scene": "Old club photo next to new one"}
        ]
    },
    
    "Detective Daisy's First Case": {
        "age_range": "6-8",
        "genre": "Mystery",
        "art_style": "realistic",
        "style_prompt": "Cozy mystery children's book illustration, detective theme, warm home setting",
        "characters": {
            "main": "Daisy, a curious 8-year-old with curly red hair and magnifying glass"
        },
        "pages": [
            {"text": "Detective Daisy's First Case\n\nThe Mystery Begins", "scene": "Title page: Girl detective with magnifying glass"},
            {"text": "Daisy dreamed of being a detective.", "scene": "Daisy writing in notebook, observing"},
            {"text": "Grandma's cookies vanished! A real mystery!", "scene": "Empty cookie jar, Grandma surprised"},
            {"text": "\"I'll take the case!\"", "scene": "Daisy putting on detective coat"},
            {"text": "Clue #1: Chocolate smudges to the living room!", "scene": "Following chocolate trail"},
            {"text": "Clue #2: A chocolate paw print on the couch!", "scene": "Examining paw print"},
            {"text": "But the dog was outside! Who else?", "scene": "Daisy thinking, dog in yard"},
            {"text": "Clue #3: Giggling from behind the curtains!", "scene": "Approaching curtains"},
            {"text": "Little brother with chocolate all over his face!", "scene": "Brother caught, chocolate beard"},
            {"text": "Case closed! Grandma made more cookies.\n\nThe End", "scene": "Family eating cookies together"}
        ]
    },
    
    "The Backwards Day": {
        "age_range": "4-7",
        "genre": "Humour",
        "art_style": "cartoon",
        "style_prompt": "Bright silly cartoon children's book illustration, backwards theme, bold colors",
        "characters": {
            "main": "Tommy, a 6-year-old with spiky brown hair and goofy grin"
        },
        "pages": [
            {"text": "The Backwards Day\n\nA Silly Story", "scene": "Title page: Boy walking backwards, everything reversed"},
            {"text": "Tommy woke up. His pillow was at his feet!", "scene": "Tommy upside down in bed"},
            {"text": "\"Good night!\" said Mom at breakfast.", "scene": "Mom saying goodnight at breakfast"},
            {"text": "Tommy put everything on backwards!", "scene": "Tommy dressed backwards, pleased"},
            {"text": "At school, everyone walked backwards!", "scene": "Classroom with everyone backwards"},
            {"text": "Dessert first, THEN vegetables!", "scene": "Tommy eating cake before broccoli"},
            {"text": "They ran the race backwards!", "scene": "Kids running backwards"},
            {"text": "Bell rang at START of school!", "scene": "Kids cheering at morning bell"},
            {"text": "\"Hello\" when leaving, \"Goodbye\" when arriving!", "scene": "Tommy confusing family"},
            {"text": "Would tomorrow be Upside-Down Day?\n\nThe End", "scene": "Tommy dreaming of upside-down world"}
        ]
    },
    
    "Pirate Pete's Bad Hair Day": {
        "age_range": "4-7",
        "genre": "Humour",
        "art_style": "cartoon",
        "style_prompt": "Bright pirate cartoon children's book illustration, ocean blues, silly expressions",
        "characters": {
            "main": "Pirate Pete, small pirate with eye patch and wild uncontrollable hair"
        },
        "pages": [
            {"text": "Pirate Pete's Bad Hair Day\n\nA Hairy Adventure", "scene": "Title page: Pirate with wild hair, crew laughing"},
            {"text": "Pirate Pete was tough. But today his hair was WILD!", "scene": "Pete looking at crazy hair in mirror"},
            {"text": "He tried to brush it. BOING! It popped back!", "scene": "Hair springing back, brush flying"},
            {"text": "Bandana? His hair ATE it!", "scene": "Hair swallowing bandana"},
            {"text": "Hat? POP! Into the ocean!", "scene": "Hat flying into ocean"},
            {"text": "\"Captain! We can't see the map!\"", "scene": "Crew blocked by Pete's hair"},
            {"text": "Seagulls got stuck! One, two, five!", "scene": "Seagulls trapped in hair"},
            {"text": "A little girl offered a scrunchie.", "scene": "Girl offering pink scrunchie"},
            {"text": "PERFECT! Magnificent ponytail!", "scene": "Pete with fabulous ponytail"},
            {"text": "The fanciest pirate ever!\n\nThe End", "scene": "Pete sailing away, fabulous hair"}
        ]
    },
    
    "Dinosaur Dentist": {
        "age_range": "3-6",
        "genre": "Humour",
        "art_style": "cartoon",
        "style_prompt": "Funny dinosaur cartoon children's book illustration, prehistoric setting, modern twist",
        "characters": {
            "main": "Dr. Dino, small friendly dinosaur in white coat with tiny glasses"
        },
        "pages": [
            {"text": "Dinosaur Dentist\n\nA Prehistoric Smile", "scene": "Title page: Small dentist dinosaur with big toothbrush next to T-Rex"},
            {"text": "Dr. Dino was the only dentist in Prehistoric Valley!", "scene": "Tiny dentist office with huge patients"},
            {"text": "First patient: T-Rex! That's a LOT of teeth!", "scene": "Dr. Dino climbing into T-Rex mouth"},
            {"text": "\"No more eating rocks, Rex!\"", "scene": "T-Rex looking guilty, rocks nearby"},
            {"text": "Triceratops had spinach in her horns. Wrong end!", "scene": "Dr. Dino checking wrong end"},
            {"text": "Brontosaurus needed a TALL ladder!", "scene": "Dr. Dino on super tall ladder"},
            {"text": "Stegosaurus kept wiggling! \"You're ticklish!\"", "scene": "Stegosaurus laughing, Dr. Dino bouncing"},
            {"text": "Pterodactyl: \"No cavities! You may fly!\"", "scene": "Pterodactyl in dental chair, happy"},
            {"text": "Everyone had sparkly clean teeth!", "scene": "All dinosaurs smiling, volcano too"},
            {"text": "\"Same time next millennium?\"\n\nThe End", "scene": "Dr. Dino waving goodbye at sunset"}
        ]
    },
}


async def generate_book_image(prompt: str, style_prompt: str, output_path: Path) -> bool:
    global images_generated, estimated_cost
    
    full_prompt = f"{style_prompt}. {prompt}. Professional children's book quality, high detail, kid-friendly, no text."
    
    try:
        print(f"    Generating...", end=" ", flush=True)
        result = await generate_image_flux(
            prompt=full_prompt,
            model="flux-dev",
            image_size="landscape_4_3",
            num_images=1
        )
        
        if result.get("success") and result.get("images"):
            image_url = result["images"][0]["url"] if isinstance(result["images"][0], dict) else result["images"][0]
            
            async with aiohttp.ClientSession() as session:
                async with session.get(image_url) as resp:
                    if resp.status == 200:
                        with open(output_path, 'wb') as f:
                            f.write(await resp.read())
                        images_generated += 1
                        estimated_cost += 0.025
                        print("OK")
                        return True
        print("FAILED")
        return False
    except Exception as e:
        print(f"FAILED - {str(e)[:60]}")
        return False


async def repair_single_book(book_id: str, title: str, template: dict, db):
    global estimated_cost
    
    print(f"\n{'='*60}")
    print(f"REPAIRING: {title}")
    print(f"{'='*60}")
    
    safe_title = title.lower().replace("'", "").replace(" ", "_").replace(":", "").strip()
    output_dir = CONTENT_DIR / safe_title
    output_dir.mkdir(parents=True, exist_ok=True)
    
    public_dir = PUBLIC_DIR / safe_title
    # Clear existing empty folder and recreate
    if public_dir.exists():
        shutil.rmtree(public_dir)
    public_dir.mkdir(parents=True, exist_ok=True)
    
    pages = []
    total = len(template["pages"])
    
    # Cover
    print(f"[Cover]", end=" ")
    cover_path = output_dir / "cover.png"
    cover_prompt = f"Children's book cover for '{title}'. {template['characters']['main']}."
    if await generate_book_image(cover_prompt, template["style_prompt"], cover_path):
        shutil.copy(cover_path, public_dir / "cover.png")
    
    # Pages
    for i, page in enumerate(template["pages"]):
        page_path = output_dir / f"page_{i+1:02d}.png"
        print(f"[Page {i+1}/{total}]", end=" ")
        scene_prompt = f"{page['scene']}. Character: {template['characters']['main']}"
        if await generate_book_image(scene_prompt, template["style_prompt"], page_path):
            shutil.copy(page_path, public_dir / f"page_{i+1:02d}.png")
        
        pages.append({
            "page_number": i + 1,
            "text": page["text"],
            "image_url": f"/book-assets/{safe_title}/page_{i+1:02d}.png",
            "layout": "full_spread" if i == 0 else "text_left_image_right"
        })
        
        await asyncio.sleep(0.3)
    
    # Back cover
    print("[Back]", end=" ")
    back_path = output_dir / "back_cover.png"
    back_prompt = f"Back cover for '{title}'. {template['characters']['main']} in peaceful scene."
    if await generate_book_image(back_prompt, template["style_prompt"], back_path):
        shutil.copy(back_path, public_dir / "back_cover.png")
    
    # Update DB
    await db.books.update_one(
        {"_id": ObjectId(book_id)},
        {"$set": {
            "pages": pages,
            "cover_image_url": f"/book-assets/{safe_title}/cover.png",
            "page_count": len(pages),
            "status": "published",
            "art_style": template["art_style"],
            "age_range": template["age_range"],
            "genre": template["genre"],
            "updated_at": datetime.utcnow().isoformat()
        }}
    )
    
    print(f"\n✓ REPAIRED! Cost: ${estimated_cost:.2f}")
    return True


async def main():
    print("="*60)
    print("REPAIR SCRIPT: Regenerating 17 books with missing images")
    print("Using: fal.ai FLUX")
    print("="*60)
    
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    # Get books needing repair (reset to empty pages)
    cursor = db.books.find({
        "$or": [{"pages": {"$exists": False}}, {"pages": []}],
        "title": {"$in": list(BOOK_TEMPLATES.keys())}
    }, {"title": 1, "_id": 1})
    
    books_to_repair = []
    async for book in cursor:
        title = book.get("title")
        if title in BOOK_TEMPLATES:
            books_to_repair.append({
                "id": str(book["_id"]),
                "title": title
            })
    
    print(f"\nBooks to repair: {len(books_to_repair)}")
    for b in books_to_repair:
        print(f"  - {b['title']}")
    
    # Repair each book
    repaired = 0
    for book_info in books_to_repair:
        try:
            await repair_single_book(
                book_info["id"],
                book_info["title"],
                BOOK_TEMPLATES[book_info["title"]],
                db
            )
            repaired += 1
        except Exception as e:
            print(f"Error: {e}")
    
    print("\n" + "="*60)
    print("REPAIR COMPLETE")
    print("="*60)
    print(f"Books repaired: {repaired}")
    print(f"Images generated: {images_generated}")
    print(f"Est. cost: ${estimated_cost:.2f}")


if __name__ == "__main__":
    asyncio.run(main())
