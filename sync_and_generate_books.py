#!/usr/bin/env python3
"""
Book Sync and Generation Script
1. First syncs any completed books that aren't in DB yet
2. Then generates new books in batches
"""

import asyncio
import os
import sys
from pathlib import Path
from datetime import datetime
from bson import ObjectId
import aiohttp

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

# Tracking
images_generated = 0
estimated_cost = 0.0

# Book templates for generation
BOOK_TEMPLATES = {
    # ===== PICTURE BOOKS (Ages 3-6) - Watercolor Style =====
    "The Wizard's Apprentice": {
        "age_range": "3-6",
        "genre": "Fantasy",
        "art_style": "watercolour",
        "style_prompt": "Soft watercolour children's book illustration, magical wizard theme, warm purples and golds, sparkly magical effects",
        "characters": {
            "main": "Finn, a young boy with messy red hair, big curious green eyes, wearing an oversized purple wizard robe and a crooked pointy hat"
        },
        "pages": [
            {"text": "The Wizard's Apprentice\n\nA Magical Story", "scene": "Title page: A young wizard apprentice in a magical tower surrounded by floating spell books and glowing potions"},
            {"text": "Finn was the wizard's new helper. Everything was new and magical!", "scene": "Finn arriving at a magical tower, eyes wide with wonder, spell books floating around"},
            {"text": "His first task: sort the spell ingredients. But the jars were talking!", "scene": "Finn surrounded by talking magical jars with faces, looking surprised"},
            {"text": "\"Careful with the moon dust!\" squeaked a tiny jar. POOF! Too late.", "scene": "Finn accidentally spilling sparkly moon dust everywhere, creating a mini galaxy"},
            {"text": "The broom started dancing! The cauldron began singing!", "scene": "Magical chaos with a dancing broom and singing cauldron, Finn laughing"},
            {"text": "\"Oh dear,\" said the wizard, but he was smiling. \"Magic is messy at first.\"", "scene": "Kind old wizard with long white beard smiling at the chaos, arm around Finn"},
            {"text": "Together they cleaned up, and Finn learned his first spell: Tidius Uppicus!", "scene": "Finn casting a cleaning spell, items floating back to their places"},
            {"text": "\"Every great wizard started just like you,\" the wizard said kindly.", "scene": "Wizard showing Finn old photos of himself making the same mistakes"},
            {"text": "Finn practiced every day. Some spells worked, some went SPLAT!", "scene": "Montage of Finn practicing, some successes and funny failures"},
            {"text": "And that's how the smallest apprentice became the bravest little wizard.\n\nThe End", "scene": "Finn proudly casting a beautiful spell, wizard clapping, magical celebration"}
        ]
    },
    
    "Fairies of Moonlight Meadow": {
        "age_range": "3-6",
        "genre": "Fantasy",
        "art_style": "watercolour",
        "style_prompt": "Soft watercolour children's book illustration, ethereal fairy mood, silver moonlight with pastel flowers, dreamy atmosphere",
        "characters": {
            "main": "Luna, Dewdrop, and Sparkle - three tiny fairies with delicate wings, Luna has silver hair, Dewdrop has blue hair, Sparkle has golden hair"
        },
        "pages": [
            {"text": "Fairies of Moonlight Meadow\n\nA Bedtime Adventure", "scene": "Title page: Three tiny fairies dancing in a moonlit meadow with glowing flowers"},
            {"text": "When the moon rises high, the fairies come out to play in Moonlight Meadow.", "scene": "Beautiful meadow at night, fairies emerging from flower homes"},
            {"text": "Luna lights the path with her silver glow. She's the oldest and wisest.", "scene": "Luna fairy with silver wings creating a path of light"},
            {"text": "Dewdrop makes the flowers sparkle with morning dew, even at night!", "scene": "Dewdrop fairy touching flowers, making them shimmer with dew drops"},
            {"text": "Sparkle, the youngest, loves to play with fireflies and giggle!", "scene": "Sparkle fairy playing tag with fireflies, laughing"},
            {"text": "Tonight was special - they found a lost baby bunny!", "scene": "Fairies discovering a tiny lost bunny looking scared"},
            {"text": "\"Don't worry, little one,\" Luna whispered. \"We'll help you find home.\"", "scene": "Luna comforting the bunny while other fairies gather around"},
            {"text": "They followed the moonbeams through the meadow, past the sleepy owls.", "scene": "Fairies leading bunny through meadow, friendly owls watching"},
            {"text": "At last! The bunny's family was waiting by the old oak tree!", "scene": "Joyful reunion with bunny family, fairies watching happily"},
            {"text": "The fairies flew home as the sun peeked over the hills. Sweet dreams!\n\nThe End", "scene": "Fairies returning to flower homes as dawn breaks, peaceful ending"}
        ]
    },
    
    "Elves and the Magic Tree": {
        "age_range": "3-6",
        "genre": "Fantasy",
        "art_style": "watercolour",
        "style_prompt": "Soft watercolour children's book illustration, enchanted forest mood, rich greens and autumn colors, magical tree theme",
        "characters": {
            "main": "Acorn and Maple, twin elves with pointed ears, matching green tunics with leaf patterns, Acorn has auburn hair, Maple has golden hair"
        },
        "pages": [
            {"text": "Elves and the Magic Tree\n\nA Tale of the Forest", "scene": "Title page: Two small elves standing before a magnificent glowing tree"},
            {"text": "Deep in the Whispering Woods lived two elf twins named Acorn and Maple.", "scene": "Twin elves in cozy treehouse home, forest morning"},
            {"text": "Their job was to care for the Great Magic Tree - the heart of the forest.", "scene": "Elves tending to enormous magical tree with glowing leaves"},
            {"text": "One morning, the tree looked sick. Its leaves were falling too soon!", "scene": "Worried elves looking at wilting magical tree, leaves dropping"},
            {"text": "\"We must find the Golden Acorn,\" said Maple. \"It will heal the tree!\"", "scene": "Elves looking at old map showing location of golden acorn"},
            {"text": "They searched high in the branches where the wise owl lived.", "scene": "Elves climbing high tree branches, talking to wise old owl"},
            {"text": "They searched low where the friendly mushrooms grew in circles.", "scene": "Elves among large colorful mushrooms, searching"},
            {"text": "Finally, they found it hidden in a squirrel's treasure collection!", "scene": "Elves discovering golden glowing acorn among squirrel's treasures"},
            {"text": "They planted it at the tree's roots. Golden light spread everywhere!", "scene": "Magical moment as golden light heals the tree, leaves regrow"},
            {"text": "The Great Tree bloomed brighter than ever. The forest was saved!\n\nThe End", "scene": "Celebratory scene with happy elves, healthy magical tree, forest creatures cheering"}
        ]
    },
    
    "Pixie Dust Adventures": {
        "age_range": "3-6",
        "genre": "Fantasy",
        "art_style": "watercolour",
        "style_prompt": "Soft watercolour children's book illustration, magical fairy mood, sparkly pastels and glitter effects",
        "characters": {
            "main": "Pip, a tiny pixie with sparkling blue wings, wild purple hair with flowers in it, wearing a dress made of rose petals"
        },
        "pages": [
            {"text": "Pixie Dust Adventures\n\nA Magical Tale", "scene": "Title page: A tiny pixie flying through a magical forest with sparkles everywhere"},
            {"text": "Pip was the smallest pixie in Dewdrop Hollow. Her wings sparkled blue like morning sky.", "scene": "Pip the tiny pixie in a beautiful hollow with dewdrops and flowers"},
            {"text": "Every pixie had a special job. Some grew flowers. Some painted butterflies. But Pip didn't know her gift yet.", "scene": "Other pixies doing magical jobs while Pip watches, feeling left out"},
            {"text": "\"I want to find my magic!\" Pip declared, and flew off into the Whispering Woods.", "scene": "Pip flying determinedly into a mystical forest with glowing plants"},
            {"text": "She met a sad ladybug who had lost her spots. Pip sprinkled some dust and - beautiful new spots appeared!", "scene": "Pip sprinkling pixie dust on a ladybug, spots magically appearing"},
            {"text": "A wilted flower begged for help. Pip's dust made it bloom brighter than ever before!", "scene": "Pip making a wilted flower bloom into a magnificent glowing flower"},
            {"text": "Even a grumpy toad smiled when Pip's dust turned his puddle into a sparkling pond!", "scene": "Pip transforming a muddy puddle into a beautiful sparkling pond, toad happy"},
            {"text": "Pip zoomed home. \"I found my gift! I make things HAPPY!\"", "scene": "Pip flying excitedly back home, trail of sparkles behind her"},
            {"text": "The Queen Pixie smiled. \"The rarest gift of all - spreading joy wherever you go.\"", "scene": "Queen Pixie crowning Pip with a tiny flower crown, other pixies cheering"},
            {"text": "And from that day on, Pip's pixie dust made the whole forest smile.\n\nThe End", "scene": "Pip flying over a happy magical forest, everything sparkling and joyful"}
        ]
    },
    
    "The Enchanted Carousel": {
        "age_range": "3-6",
        "genre": "Fantasy",
        "art_style": "watercolour",
        "style_prompt": "Soft watercolour children's book illustration, whimsical carnival mood, vintage pastels with golden lights",
        "characters": {
            "main": "Mia, a 5-year-old girl with two dark braids tied with ribbons, rosy cheeks, wearing a vintage-style dress"
        },
        "pages": [
            {"text": "The Enchanted Carousel\n\nA Magical Ride", "scene": "Title page: A beautiful glowing carousel at twilight with magical horses"},
            {"text": "Mia found an old carousel in the corner of the park. It looked forgotten, but still beautiful.", "scene": "Mia discovering an old ornate carousel covered in vines, evening light"},
            {"text": "She climbed onto a white horse with a golden mane. Suddenly, the carousel began to spin!", "scene": "Mia on a beautiful white carousel horse, lights starting to glow"},
            {"text": "The horse winked at her! \"Hold tight, little one. We're going on an adventure!\"", "scene": "The carousel horse winking at surprised Mia, magical sparkles"},
            {"text": "The carousel spun faster and faster until - WHOOSH! They flew into the sky!", "scene": "Carousel lifting off into starry sky, Mia holding on, amazed expression"},
            {"text": "They soared over candy-colored mountains and rivers made of starlight.", "scene": "Mia riding the horse through a magical landscape of candy mountains"},
            {"text": "They raced through clouds shaped like animals and picked flowers from floating gardens.", "scene": "Mia and horse flying through cloud animals and floating flower gardens"},
            {"text": "\"Time to go home,\" the horse said gently as the sun began to rise.", "scene": "Horse and Mia descending back toward the carousel, sunrise colors"},
            {"text": "The carousel slowed and Mia stepped off, a magical flower still in her hand.", "scene": "Mia stepping off carousel holding a glowing flower, looking amazed"},
            {"text": "\"Come back anytime,\" the horse whispered. And Mia knew she would.\n\nThe End", "scene": "Mia waving goodbye to the carousel at sunset, magical and warm"}
        ]
    },
    
    # ===== HUMOUR BOOKS =====
    "The Backwards Day": {
        "age_range": "4-7",
        "genre": "Humour",
        "art_style": "cartoon",
        "style_prompt": "Bright colorful cartoon children's book illustration, silly humorous mood, bold colors and exaggerated expressions",
        "characters": {
            "main": "Tommy, a 6-year-old boy with spiky brown hair, big goofy grin, wearing his clothes backwards"
        },
        "pages": [
            {"text": "The Backwards Day\n\nA Silly Story", "scene": "Title page: Boy walking backwards with everything around him reversed, funny expressions"},
            {"text": "Tommy woke up and something felt strange. His pillow was at his feet!", "scene": "Tommy waking up upside down in bed, confused expression"},
            {"text": "\"Good night, Tommy!\" said Mom at breakfast. Wait, that's not right!", "scene": "Mom serving breakfast but saying goodnight, Tommy looking confused"},
            {"text": "Tommy put on his shirt backwards, his pants backwards, even his socks backwards!", "scene": "Tommy dressed completely backwards, looking pleased with himself"},
            {"text": "At school, everyone walked backwards. The teacher wrote on the board from right to left!", "scene": "Funny classroom scene with everyone walking backwards"},
            {"text": "They had dessert first, THEN vegetables! Tommy didn't mind that part.", "scene": "Tommy happily eating cake before broccoli, lunchroom chaos"},
            {"text": "During P.E., they ran the race backwards! Tommy won by coming last!", "scene": "Kids running backwards on track, Tommy celebrating"},
            {"text": "The end-of-day bell rang at the START of school. Everyone cheered!", "scene": "Kids cheering at morning bell, school in background"},
            {"text": "At home, Tommy said \"Hello!\" when leaving and \"Goodbye!\" when arriving.", "scene": "Tommy at front door confusing his family with reversed greetings"},
            {"text": "As Tommy fell asleep, he wondered: would tomorrow be Upside-Down Day?\n\nThe End", "scene": "Tommy in bed dreaming of upside-down world, silly smile"}
        ]
    },
    
    "Pirate Pete's Bad Hair Day": {
        "age_range": "4-7",
        "genre": "Humour",
        "art_style": "cartoon",
        "style_prompt": "Bright colorful cartoon children's book illustration, pirate adventure mood, ocean blues with silly expressions",
        "characters": {
            "main": "Pirate Pete, a small pirate with an eye patch, big bushy beard, outrageous wild curly hair that won't behave"
        },
        "pages": [
            {"text": "Pirate Pete's Bad Hair Day\n\nA Hairy Adventure", "scene": "Title page: Pirate with hilariously wild hair on a ship, crew laughing"},
            {"text": "Pirate Pete was the toughest pirate on the seven seas. But today, his hair was WILD!", "scene": "Pete looking in mirror at his crazy hair, looking distressed"},
            {"text": "He tried to brush it down. BOING! It popped right back up!", "scene": "Pete's hair springing back up after brushing, brush flying away"},
            {"text": "He tried a bandana. His hair ate it! Gulp!", "scene": "Hair seemingly swallowing the bandana, Pete shocked"},
            {"text": "He tried his best pirate hat. POP! The hair pushed it off into the ocean!", "scene": "Hat flying off Pete's head into ocean, shark catching it"},
            {"text": "\"Captain! We can't see the map!\" cried the crew. His hair covered everything!", "scene": "Crew trying to read map but Pete's hair is in the way"},
            {"text": "A seagull got stuck in his hair! Then another! Then three more!", "scene": "Multiple seagulls trapped in Pete's huge hair, chaos"},
            {"text": "Finally, a little girl on an island said, \"Have you tried... a scrunchie?\"", "scene": "Small girl on island beach offering a pink scrunchie"},
            {"text": "PERFECT! The scrunchie tamed the wild hair into a magnificent ponytail!", "scene": "Pete's hair in a neat ponytail, looking proud and fabulous"},
            {"text": "\"Thank ye, tiny landlubber!\" Pete sailed away, the fanciest pirate ever.\n\nThe End", "scene": "Pete sailing away with fabulous hair, crew admiring, little girl waving"}
        ]
    },
    
    "Dinosaur Dentist": {
        "age_range": "3-6",
        "genre": "Humour",
        "art_style": "cartoon",
        "style_prompt": "Bright colorful cartoon children's book illustration, funny dinosaur theme, prehistoric setting with modern twist",
        "characters": {
            "main": "Dr. Dino, a small friendly dinosaur wearing a white coat and tiny glasses, carrying an oversized toothbrush"
        },
        "pages": [
            {"text": "Dinosaur Dentist\n\nA Prehistoric Smile", "scene": "Title page: Small dinosaur dentist with big toothbrush next to T-Rex with toothache"},
            {"text": "Dr. Dino was the only dentist in all of Prehistoric Valley. And boy, was he busy!", "scene": "Tiny dinosaur dentist office with huge dinosaur patients waiting"},
            {"text": "First patient: T-Rex! \"Open wide!\" That's a LOT of teeth to clean!", "scene": "Tiny Dr. Dino climbing into giant T-Rex mouth with toothbrush"},
            {"text": "\"No more eating rocks, Rex. That's bad for your enamel!\"", "scene": "T-Rex looking guilty, pile of rocks nearby"},
            {"text": "Next: Triceratops! She had spinach stuck between her horns. Wait, wrong end!", "scene": "Dr. Dino accidentally checking Triceratops horns, both laughing"},
            {"text": "Brontosaurus had the longest neck. Dr. Dino needed a ladder!", "scene": "Dr. Dino on super tall ladder reaching Brontosaurus mouth"},
            {"text": "Stegosaurus kept wiggling! \"Hold still, you're ticklish!\"", "scene": "Stegosaurus laughing and wiggling, Dr. Dino bouncing around"},
            {"text": "The Pterodactyl flew in for a checkup. \"No cavities! You may fly!\"", "scene": "Pterodactyl in dental chair getting checked, happy result"},
            {"text": "By sunset, everyone had sparkly clean teeth. Even the volcano smiled!", "scene": "All dinosaurs smiling with sparkly teeth, happy volcano in background"},
            {"text": "\"Same time next millennium?\" asked Dr. Dino with a wink.\n\nThe End", "scene": "Dr. Dino waving goodbye to happy dinosaur patients at sunset"}
        ]
    },
    
    # ===== ADVENTURE BOOKS =====
    "Captain Compass and the Treasure Map": {
        "age_range": "6-8",
        "genre": "Adventure",
        "art_style": "realistic",
        "style_prompt": "Detailed realistic children's book illustration, adventure expedition mood, warm sunset colors and oceanic blues",
        "characters": {
            "main": "Captain Compass, a young adventurous girl with a compass necklace, explorer hat, cargo pants, and a determined expression"
        },
        "pages": [
            {"text": "Captain Compass and the Treasure Map\n\nAn Adventure Begins", "scene": "Title page: Young girl captain holding ancient map on ship deck, ocean sunset"},
            {"text": "Emma found a dusty old map in her grandmother's attic. X marked a mysterious island!", "scene": "Emma in attic discovering old treasure map among dusty boxes"},
            {"text": "\"I'm going to find that treasure!\" she declared. Her parrot Patches agreed.", "scene": "Emma with parrot on shoulder, looking determined at the map"},
            {"text": "She gathered her crew: Max the navigator, Sofia the botanist, and Leo the chef.", "scene": "Four young adventurers together preparing their ship"},
            {"text": "They sailed through the Whispering Waves, where fish jumped and dolphins raced.", "scene": "Ship sailing through beautiful ocean, dolphins alongside"},
            {"text": "\"Storm ahead!\" cried Max. But Emma steered them through like a true captain.", "scene": "Dramatic storm scene, Emma steering confidently at the wheel"},
            {"text": "The island appeared through the mist - green, mysterious, and magical!", "scene": "Ship approaching lush mysterious island through misty waters"},
            {"text": "They followed the map through jungle vines and over bubbling streams.", "scene": "Kids hiking through jungle following map, exotic plants around"},
            {"text": "The X marked a hidden cave. Inside wasn't gold - but something better!", "scene": "Kids entering cave with flashlights, wonder on their faces"},
            {"text": "It was filled with ancient books and magical artifacts! The real treasure was knowledge.\n\nThe End", "scene": "Kids surrounded by glowing books and artifacts in cave, amazed expressions"}
        ]
    },
    
    "The Jungle Explorers Club": {
        "age_range": "6-8",
        "genre": "Adventure",
        "art_style": "realistic",
        "style_prompt": "Detailed realistic children's book illustration, jungle expedition mood, lush greens with exotic animals",
        "characters": {
            "main": "The Jungle Explorers: Zara (leader with binoculars), Kai (animal expert), and Bella (plant specialist)"
        },
        "pages": [
            {"text": "The Jungle Explorers Club\n\nInto the Wild", "scene": "Title page: Three kids in explorer gear at jungle entrance, exotic birds flying"},
            {"text": "The Jungle Explorers Club had one mission: discover something no one had ever seen!", "scene": "Three kids in treehouse clubhouse, planning with maps"},
            {"text": "Deep in the Amazon, they heard a sound no one could identify. \"Let's investigate!\"", "scene": "Kids in dense jungle, mysterious sound effects visualized"},
            {"text": "Kai spotted jaguar tracks! \"It's protecting something,\" he whispered.", "scene": "Kids examining large paw prints, Kai taking notes"},
            {"text": "Bella found glowing mushrooms that lit the path through the dark forest.", "scene": "Beautiful scene with bioluminescent mushrooms lighting the way"},
            {"text": "Zara used her binoculars and gasped. \"I see it! In that hidden waterfall!\"", "scene": "Zara pointing excitedly at distant waterfall through trees"},
            {"text": "Behind the waterfall was a secret garden with flowers that changed colors!", "scene": "Magical hidden garden with color-changing flowers"},
            {"text": "A baby jaguar played among the flowers. This was its secret home!", "scene": "Adorable jaguar cub playing in the magical garden"},
            {"text": "They promised to keep the secret and protect this magical place forever.", "scene": "Kids making a pinky promise, jaguar cub watching"},
            {"text": "The Jungle Explorers Club had found the greatest treasure: a secret worth keeping.\n\nThe End", "scene": "Kids leaving jungle, looking back at hidden waterfall, sunset"}
        ]
    },
    
    "Mountain Climbing Mice": {
        "age_range": "6-8",
        "genre": "Adventure",
        "art_style": "realistic",
        "style_prompt": "Detailed realistic children's book illustration with tiny adventurous mice, majestic mountain scenery, dramatic skies",
        "characters": {
            "main": "Marco and Mia, two brave mice wearing tiny climbing gear, backpacks, and determined expressions"
        },
        "pages": [
            {"text": "Mountain Climbing Mice\n\nA Tiny Big Adventure", "scene": "Title page: Two tiny mice at base of enormous mountain, looking up"},
            {"text": "Marco and Mia looked up at Cheese Peak, the tallest mountain no mouse had ever climbed.", "scene": "Two mice with climbing gear staring at massive snowy peak"},
            {"text": "\"Everyone says mice can't climb mountains,\" said Mia. \"Let's prove them wrong!\"", "scene": "Determined mice beginning their climb, village behind them"},
            {"text": "The first challenge: crossing the Crumb Canyon on a tiny rope bridge!", "scene": "Mice crossing rope bridge over deep canyon, wind blowing"},
            {"text": "They climbed through the Forest of Giant Pines, where pine cones were like boulders.", "scene": "Mice climbing among enormous pine trees and huge pine cones"},
            {"text": "A friendly eagle offered them a lift over the Windy Pass. \"Thank you, Mr. Eagle!\"", "scene": "Mice riding on a kind eagle's back, soaring over mountains"},
            {"text": "The ice was slippery! They used tiny crampons and helped each other up.", "scene": "Mice climbing icy cliff face, using teamwork"},
            {"text": "At last, they reached the summit! The world looked so small from up here!", "scene": "Mice at mountain peak, panoramic view, triumphant pose"},
            {"text": "They planted a tiny flag: \"Mice CAN do anything!\"", "scene": "Mice planting small flag at peak, sunrise in background"},
            {"text": "Marco and Mia proved that size doesn't matter - only courage does.\n\nThe End", "scene": "Mice sliding down happily, village celebrating their return below"}
        ]
    },
    
    # ===== SCIENCE FICTION =====
    "The Friendly Martians": {
        "age_range": "3-6",
        "genre": "Science Fiction",
        "art_style": "watercolour",
        "style_prompt": "Soft watercolour children's book illustration, fun space mood, reds and purples of Mars with friendly alien designs",
        "characters": {
            "main": "Ziggy and Zara, two small green Martians with big friendly eyes, antennae with heart shapes on top"
        },
        "pages": [
            {"text": "The Friendly Martians\n\nA Story About Making Friends", "scene": "Title page: Two cute green Martians waving from Mars with Earth in the sky"},
            {"text": "Ziggy and Zara lived on Mars. They had lots of rocks to play with, but no friends.", "scene": "Two Martians looking lonely on Mars landscape, surrounded by red rocks"},
            {"text": "One day, a spaceship landed nearby! Out came a little girl named Luna.", "scene": "Spaceship landing on Mars, Luna stepping out, Martians hiding and peeking"},
            {"text": "The Martians were scared. Luna looked so different! She had no antennae at all!", "scene": "Martians hiding behind rocks, looking nervously at Luna"},
            {"text": "But Luna smiled and waved. \"Hello! Do you want to play?\"", "scene": "Luna waving friendly, Martians starting to come out curiously"},
            {"text": "They played hide and seek behind craters. Ziggy was really good at hiding!", "scene": "Playing hide and seek on Mars, Ziggy hiding behind a crater"},
            {"text": "They made sand castles from red Mars dust. Zara built the tallest one!", "scene": "All three making Mars dust castles together, having fun"},
            {"text": "They bounced super high in the low gravity and giggled until their tummies hurt.", "scene": "Luna and Martians bouncing high on Mars, all laughing"},
            {"text": "When Luna had to go home, they all felt sad. \"Will you come back?\" asked Ziggy.", "scene": "Sad farewell scene at the spaceship, everyone looking emotional"},
            {"text": "\"Of course!\" Luna smiled. \"Friends visit each other, no matter how far!\"\n\nThe End", "scene": "Luna waving from spaceship window, Martians waving from Mars, hearts connecting them"}
        ]
    },
    
    "Space Station School": {
        "age_range": "6-8",
        "genre": "Science Fiction",
        "art_style": "realistic",
        "style_prompt": "Detailed realistic children's book illustration, futuristic space station setting, blue and silver tones, view of Earth",
        "characters": {
            "main": "Nova, a 7-year-old girl with short black hair, wearing a silver space suit with colorful patches"
        },
        "pages": [
            {"text": "Space Station School\n\nLearning Among the Stars", "scene": "Title page: Space station orbiting Earth, kids visible through windows"},
            {"text": "Nova's classroom floated 250 miles above Earth. Best. School. Ever!", "scene": "Futuristic classroom in space, kids floating at desks, Earth visible"},
            {"text": "Math was fun when you could calculate how fast asteroids zoom by!", "scene": "Nova doing math problems with asteroid visual aids floating around"},
            {"text": "In science class, they grew plants in zero gravity. They grew UP and DOWN!", "scene": "Kids observing plants growing in all directions in space lab"},
            {"text": "Lunch time meant catching floating food globes! Nova caught three!", "scene": "Kids catching floating food spheres in cafeteria, laughing"},
            {"text": "PE was wild - they played soccer in zero-G! The ball bounced off walls!", "scene": "Kids playing zero gravity soccer, ball bouncing everywhere"},
            {"text": "Art class let them paint Earth from above. Every painting was unique!", "scene": "Kids painting at easels, each showing Earth differently"},
            {"text": "Nova's favorite part was astronaut training. Someday she'd walk on Mars!", "scene": "Nova in training simulator, dreaming of Mars mission"},
            {"text": "At night, they watched shooting stars from their beds. Like personal fireworks!", "scene": "Kids in sleeping pods watching meteor shower through window"},
            {"text": "\"School in space is out of this world!\" Nova wrote in her journal.\n\nThe End", "scene": "Nova writing in glowing journal, smiling, stars twinkling outside"}
        ]
    },
    
    "Gadget Girl and the Invention Fair": {
        "age_range": "6-8",
        "genre": "Science Fiction",
        "art_style": "cartoon",
        "style_prompt": "Bright modern cartoon children's book illustration, STEM invention theme, colorful gadgets and workshop setting",
        "characters": {
            "main": "Gwen, a 8-year-old inventor with messy ponytail, safety goggles on head, tool belt, and grease-stained lab coat"
        },
        "pages": [
            {"text": "Gadget Girl and the Invention Fair\n\nA Story of Creativity", "scene": "Title page: Young girl inventor surrounded by colorful inventions and tools"},
            {"text": "Gwen LOVED inventing things! Her garage was full of fantastic gadgets.", "scene": "Gwen in messy garage workshop surrounded by inventions"},
            {"text": "The school Invention Fair was next week! But what should she make?", "scene": "Gwen looking at poster for Invention Fair, thinking hard"},
            {"text": "She tried a flying toaster. CRASH! Too much power.", "scene": "Toaster flying chaotically, Gwen ducking, bread everywhere"},
            {"text": "She built a homework robot. It did her homework... then ate it!", "scene": "Robot eating papers, Gwen looking dismayed"},
            {"text": "She made rocket shoes. She went UP but forgot to build DOWN!", "scene": "Gwen stuck on ceiling with smoking rocket shoes, oops"},
            {"text": "\"I'll never win,\" Gwen sighed. Then she saw her little brother struggling with his backpack.", "scene": "Gwen watching little brother struggle with heavy backpack"},
            {"text": "IDEA! She invented the Hover-Pack - a backpack that carries itself!", "scene": "Gwen having eureka moment, sketching floating backpack"},
            {"text": "At the fair, kids LOVED it! \"It helps people!\" the judge smiled.", "scene": "Kids trying Hover-Pack at fair, judges impressed"},
            {"text": "Gwen won first place! \"The best inventions help others,\" she realized.\n\nThe End", "scene": "Gwen with trophy, little brother hugging her, crowd cheering"}
        ]
    },
    
    # ===== MYSTERY =====
    "Detective Daisy's First Case": {
        "age_range": "6-8",
        "genre": "Mystery",
        "art_style": "realistic",
        "style_prompt": "Detailed realistic children's book illustration, cozy mystery mood, warm lighting with magnifying glass effects",
        "characters": {
            "main": "Daisy, a curious 8-year-old with curly red hair, wearing a detective coat and carrying a magnifying glass"
        },
        "pages": [
            {"text": "Detective Daisy's First Case\n\nThe Mystery Begins", "scene": "Title page: Young girl detective with magnifying glass, shadowy clues around her"},
            {"text": "Daisy dreamed of being a detective. Her notebook was full of observations!", "scene": "Daisy writing in notebook, observing everything around her"},
            {"text": "One morning, Grandma's famous blueberry pie disappeared! A real mystery!", "scene": "Empty pie plate on counter, Grandma looking surprised, Daisy excited"},
            {"text": "\"I'll take the case!\" Daisy announced. She grabbed her magnifying glass.", "scene": "Daisy putting on detective coat dramatically, ready for action"},
            {"text": "Clue #1: Blueberry footprints leading outside! Daisy followed them carefully.", "scene": "Daisy following purple footprints with magnifying glass"},
            {"text": "Clue #2: A trail of crumbs heading toward the garden shed.", "scene": "Daisy finding crumbs on path, pointing toward shed"},
            {"text": "Clue #3: Suspicious giggling coming from inside the shed!", "scene": "Daisy listening at shed door, hearing laughter inside"},
            {"text": "She opened the door and found... her little brother with a blueberry beard!", "scene": "Caught! Little brother with pie-stained face, looking guilty but cute"},
            {"text": "\"Case solved!\" But Daisy couldn't be mad - he looked so funny!", "scene": "Daisy laughing, brother laughing too, pie crumbs everywhere"},
            {"text": "Grandma made another pie, and this time everyone got a slice!\n\nThe End", "scene": "Family eating pie together, Daisy writing 'Case Closed' in notebook"}
        ]
    },
    
    "The Secret Code Club": {
        "age_range": "6-8",
        "genre": "Mystery",
        "art_style": "realistic",
        "style_prompt": "Detailed realistic children's book illustration, secret agent mood, hidden messages and code-breaking theme",
        "characters": {
            "main": "The Code Breakers: Sam (decoder), Lily (puzzle solver), and Jake (pattern finder)"
        },
        "pages": [
            {"text": "The Secret Code Club\n\nCracking the Mystery", "scene": "Title page: Three kids with coded messages floating around them"},
            {"text": "Sam, Lily, and Jake had a secret club where they solved coded mysteries!", "scene": "Three kids in tree house with code wheels and decoder rings"},
            {"text": "One day, they found a strange note in the library: GSRH RH GSV URMOW!", "scene": "Kids finding mysterious coded note in library book"},
            {"text": "\"It's a substitution cipher!\" Sam said. They got to work decoding.", "scene": "Kids working together at table with alphabet wheels"},
            {"text": "The message said: THIS IS THE FIRST! There was more to find!", "scene": "Kids excitedly reading decoded message"},
            {"text": "They found more codes hidden around town - in the park, the bakery, everywhere!", "scene": "Kids running around town finding hidden coded notes"},
            {"text": "Each code led to another until they had five clues total.", "scene": "Kids laying out five decoded messages, connecting clues"},
            {"text": "The final code led to... the old clock tower! Something was hidden there!", "scene": "Kids approaching mysterious clock tower, sunset"},
            {"text": "Inside was a time capsule from kids 50 years ago! Same club, same codes!", "scene": "Kids opening old time capsule, old photos and notes inside"},
            {"text": "The Secret Code Club had found the ultimate mystery - their club's history!\n\nThe End", "scene": "Kids holding up old club photo next to their new one, same pose"}
        ]
    },
}


async def generate_book_image(prompt: str, style_prompt: str, output_path: Path) -> bool:
    """Generate a single image using fal.ai"""
    global images_generated, estimated_cost
    
    full_prompt = f"{style_prompt}. {prompt}. Professional children's book quality, high detail."
    
    try:
        result = await generate_image_flux(
            prompt=full_prompt,
            model="flux-dev",
            image_size="landscape_4_3",
            num_images=1
        )
        
        if result.get("success") and result.get("images"):
            image_info = result["images"][0]
            image_url = image_info["url"] if isinstance(image_info, dict) else image_info
            
            async with aiohttp.ClientSession() as session:
                async with session.get(image_url) as resp:
                    if resp.status == 200:
                        with open(output_path, 'wb') as f:
                            f.write(await resp.read())
                        images_generated += 1
                        estimated_cost += 0.03  # Approximate cost per image
                        return True
        return False
    except Exception as e:
        error = str(e).lower()
        if "balance" in error or "budget" in error or "insufficient" in error:
            raise Exception("BUDGET_EXHAUSTED")
        print(f"    ERROR: {str(e)[:100]}")
        return False


async def sync_completed_book_to_db(title: str, db):
    """Sync a completed book folder to database"""
    safe_title = title.lower().replace("'", "").replace(" ", "_").replace(":", "")
    content_path = CONTENT_DIR / safe_title
    
    if not content_path.exists():
        return False
    
    # Check if images exist
    images = list(content_path.glob("*.png"))
    if len(images) < 5:  # Need at least cover + some pages
        return False
    
    # Get book from database
    book = await db.books.find_one({"title": title})
    if not book:
        return False
    
    # Already has pages?
    if book.get("pages") and len(book.get("pages", [])) > 0:
        return True  # Already synced
    
    # Count page images
    page_images = sorted([p for p in images if p.name.startswith("page_")])
    
    # Build pages array
    pages = []
    for i, page_img in enumerate(page_images):
        pages.append({
            "page_number": i + 1,
            "text": f"Page {i + 1}",  # Placeholder text
            "image_url": f"/book-assets/{safe_title}/{page_img.name}",
            "layout": "full_spread" if i == 0 else "text_left_image_right"
        })
    
    # Update database
    await db.books.update_one(
        {"_id": book["_id"]},
        {"$set": {
            "pages": pages,
            "cover_image_url": f"/book-assets/{safe_title}/cover.png",
            "page_count": len(pages),
            "status": "published",
            "updated_at": datetime.utcnow().isoformat()
        }}
    )
    
    print(f"  Synced: {title} ({len(pages)} pages)")
    return True


async def complete_single_book(book_id: str, title: str, template: dict, db):
    """Complete a single book with images and database update"""
    global estimated_cost
    
    print(f"\n{'='*60}")
    print(f"GENERATING: {title}")
    print(f"Style: {template['art_style']}, Age: {template['age_range']}")
    print(f"{'='*60}")
    
    safe_title = title.lower().replace("'", "").replace(" ", "_").replace(":", "")
    output_dir = CONTENT_DIR / safe_title
    output_dir.mkdir(parents=True, exist_ok=True)
    
    public_dir = PUBLIC_DIR / safe_title
    public_dir.mkdir(parents=True, exist_ok=True)
    
    pages = []
    total = len(template["pages"])
    
    # Generate cover
    cover_path = output_dir / "cover.png"
    if not cover_path.exists():
        print(f"[Cover] Generating...")
        cover_prompt = f"Children's book cover for '{title}'. {template['characters']['main']}. Beautiful title space at top."
        if await generate_book_image(cover_prompt, template["style_prompt"], cover_path):
            print(f"    OK - Cover saved")
            import shutil
            shutil.copy(cover_path, public_dir / "cover.png")
    else:
        print(f"[Cover] Already exists")
    
    # Generate pages
    for i, page in enumerate(template["pages"]):
        page_path = output_dir / f"page_{i+1:02d}.png"
        
        if not page_path.exists():
            print(f"[Page {i+1}/{total}] Generating...", end=" ")
            scene_prompt = f"{page['scene']}. Character: {template['characters']['main']}"
            if await generate_book_image(scene_prompt, template["style_prompt"], page_path):
                print("OK")
                import shutil
                shutil.copy(page_path, public_dir / f"page_{i+1:02d}.png")
            else:
                print("FAILED")
        else:
            print(f"[Page {i+1}/{total}] Already exists")
        
        pages.append({
            "page_number": i + 1,
            "text": page["text"],
            "image_url": f"/book-assets/{safe_title}/page_{i+1:02d}.png",
            "layout": "full_spread" if i == 0 else "text_left_image_right"
        })
        
        await asyncio.sleep(0.3)  # Small delay between images
    
    # Generate back cover
    back_path = output_dir / "back_cover.png"
    if not back_path.exists():
        print("[Back] Generating...", end=" ")
        back_prompt = f"Back cover for children's book. {template['characters']['main']} in peaceful scene."
        if await generate_book_image(back_prompt, template["style_prompt"], back_path):
            print("OK")
            import shutil
            shutil.copy(back_path, public_dir / "back_cover.png")
    else:
        print("[Back] Already exists")
    
    # Update database
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
    
    print(f"\nBook Complete! Estimated cost so far: ${estimated_cost:.2f}")
    return True


async def main():
    global estimated_cost
    
    print("="*60)
    print("BOOK SYNC AND GENERATION")
    print("="*60)
    
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    # Phase 1: Sync any existing completed books
    print("\n--- PHASE 1: Syncing existing completed books ---")
    completed_folders = [f.name for f in CONTENT_DIR.iterdir() if f.is_dir()]
    
    for folder in completed_folders:
        # Convert folder name back to title
        title_variants = [
            folder.replace("_", " ").title(),
            folder.replace("_", "'").replace(" S ", "'s ").title(),
        ]
        
        for title in title_variants:
            await sync_completed_book_to_db(title, db)
    
    # Phase 2: Get empty books that have templates
    print("\n--- PHASE 2: Finding books to generate ---")
    
    # Get all empty books
    cursor = db.books.find({
        "$or": [{"pages": {"$exists": False}}, {"pages": []}]
    }, {"title": 1, "_id": 1})
    
    books_to_generate = []
    async for book in cursor:
        title = book.get("title")
        if title in BOOK_TEMPLATES:
            books_to_generate.append({
                "id": str(book["_id"]),
                "title": title
            })
    
    print(f"Found {len(books_to_generate)} books with templates ready to generate")
    
    if not books_to_generate:
        print("No books to generate!")
        return
    
    # Phase 3: Generate books
    print("\n--- PHASE 3: Generating books ---")
    
    completed = 0
    BUDGET_LIMIT = 8.0  # Stop before exhausting budget
    
    for book_info in books_to_generate:
        if estimated_cost > BUDGET_LIMIT:
            print(f"\n BUDGET WARNING: ${estimated_cost:.2f} spent. Stopping to preserve budget.")
            break
        
        try:
            await complete_single_book(
                book_info["id"],
                book_info["title"],
                BOOK_TEMPLATES[book_info["title"]],
                db
            )
            completed += 1
        except Exception as e:
            if "BUDGET" in str(e):
                print(f"\n BUDGET EXHAUSTED")
                break
            print(f"Error with {book_info['title']}: {e}")
    
    # Summary
    print("\n" + "="*60)
    print("GENERATION COMPLETE")
    print("="*60)
    print(f"Books completed this session: {completed}")
    print(f"Images generated: {images_generated}")
    print(f"Estimated cost: ${estimated_cost:.2f}")
    
    # Count remaining
    remaining = await db.books.count_documents({
        "$or": [{"pages": {"$exists": False}}, {"pages": []}]
    })
    print(f"Books still empty: {remaining}")


if __name__ == "__main__":
    asyncio.run(main())
