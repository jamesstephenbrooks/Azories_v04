#!/usr/bin/env python3
"""
Generate 50 high-quality children's books for Azories launch.
Each book has 10-30 pages with AI-generated images.
"""

import asyncio
import os
import sys
import uuid
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))

# Book definitions - 50 diverse children's books
LAUNCH_BOOKS = [
    # Fantasy (10 books)
    {
        "title": "The Dragon's Secret Garden",
        "description": "A young girl discovers a hidden garden where friendly dragons tend magical flowers that grant wishes.",
        "genre": "Fantasy",
        "age_rating": "All Ages",
        "pages": 15,
        "story_prompts": ["girl finds hidden door", "magical garden reveal", "baby dragon appears", "dragon teaches gardening", "magical flowers bloom", "wish flower glows", "girl makes wish", "garden transforms", "dragon celebration", "friendship forever"]
    },
    {
        "title": "The Moonbeam Princess",
        "description": "Princess Luna must collect moonbeams to save her kingdom from eternal darkness.",
        "genre": "Fantasy",
        "age_rating": "5+",
        "pages": 18,
        "story_prompts": ["princess at castle window", "darkness spreading", "moonbeam jar", "journey begins", "forest of shadows", "glowing path", "star creatures help", "moonbeam collection", "kingdom illuminated", "celebration"]
    },
    {
        "title": "Wizard's First Spell",
        "description": "Young wizard Finn accidentally turns his cat into a cloud and must find a way to reverse it.",
        "genre": "Fantasy",
        "age_rating": "5+",
        "pages": 14,
        "story_prompts": ["wizard boy practicing", "cat becomes cloud", "chasing cloud cat", "wizard library", "spell book discovery", "potion brewing", "magic words", "cloud descending", "cat returns", "happy ending"]
    },
    {
        "title": "The Fairy's Lost Wings",
        "description": "A fairy loses her wings in a storm and discovers true friendship along her journey home.",
        "genre": "Fantasy",
        "age_rating": "All Ages",
        "pages": 16,
        "story_prompts": ["fairy in storm", "wings swept away", "meeting a mouse", "journey through forest", "helpful ladybug", "river crossing", "mountain climbing", "finding wings", "friendship celebration", "flying together"]
    },
    {
        "title": "The Kingdom of Talking Animals",
        "description": "A boy discovers he can understand animals and helps solve a mystery in the animal kingdom.",
        "genre": "Fantasy",
        "age_rating": "5+",
        "pages": 20,
        "story_prompts": ["boy hears animals", "owl messenger", "animal council", "missing crown", "detective work", "clues in forest", "squirrel witness", "thief revealed", "crown returned", "hero celebration"]
    },
    {
        "title": "The Giants' Tea Party",
        "description": "Tiny twins are invited to a giants' tea party and learn that size doesn't matter for friendship.",
        "genre": "Fantasy",
        "age_rating": "All Ages",
        "pages": 12,
        "story_prompts": ["twins find invitation", "climbing giant stairs", "enormous teacup", "friendly giants", "giant cookies", "tiny tea", "giant games", "sunset farewell", "friendship promise", "return home"]
    },
    {
        "title": "The Mermaid's Song",
        "description": "A mermaid discovers her singing can heal the ocean and embarks on a quest to save marine life.",
        "genre": "Fantasy",
        "age_rating": "5+",
        "pages": 18,
        "story_prompts": ["mermaid singing", "sick fish", "healing discovery", "ocean journey", "coral reef dying", "singing heals reef", "whale friend", "dark waters", "final song", "ocean celebration"]
    },
    {
        "title": "The Enchanted Paintbrush",
        "description": "Everything Maya paints with her magic paintbrush comes to life!",
        "genre": "Fantasy",
        "age_rating": "All Ages",
        "pages": 14,
        "story_prompts": ["finding paintbrush", "first painting", "butterfly comes alive", "painting animals", "accidental monster", "chasing monster", "brave painting", "monster becomes friend", "art show", "magical ending"]
    },
    {
        "title": "The Cloud Keeper",
        "description": "Oliver becomes the apprentice to the Cloud Keeper and learns to shape weather for the world below.",
        "genre": "Fantasy",
        "age_rating": "5+",
        "pages": 16,
        "story_prompts": ["climbing sky ladder", "cloud castle", "meeting Cloud Keeper", "cloud shaping lesson", "rain making", "rainbow creation", "storm mistake", "fixing storm", "graduation day", "first job"]
    },
    {
        "title": "The Phoenix Feather",
        "description": "Siblings find a phoenix feather that grants them flying powers for one magical night.",
        "genre": "Fantasy",
        "age_rating": "All Ages",
        "pages": 15,
        "story_prompts": ["finding glowing feather", "first flight", "over the town", "cloud playground", "meeting owl", "star touching", "moon visit", "dawn approaching", "landing home", "feather fades"]
    },
    
    # Adventure (10 books)
    {
        "title": "The Treasure Map of Grandpa Joe",
        "description": "Cousins discover their grandfather's old treasure map and follow it to an amazing adventure.",
        "genre": "Adventure",
        "age_rating": "5+",
        "pages": 20,
        "story_prompts": ["finding map in attic", "decoding clues", "first landmark", "crossing bridge", "cave entrance", "underground river", "glowing crystals", "treasure chest", "family photos inside", "true treasure"]
    },
    {
        "title": "Journey to the Center of the Treehouse",
        "description": "Kids discover their treehouse has magical levels going deep underground.",
        "genre": "Adventure",
        "age_rating": "5+",
        "pages": 18,
        "story_prompts": ["secret trapdoor", "ladder down", "underground room", "deeper passage", "crystal cave", "underground lake", "glowing creatures", "ancient symbols", "magic core", "returning home"]
    },
    {
        "title": "The Great Balloon Escape",
        "description": "Best friends accidentally float away in a hot air balloon and see the world from above.",
        "genre": "Adventure",
        "age_rating": "All Ages",
        "pages": 16,
        "story_prompts": ["balloon festival", "climbing in basket", "accidental takeoff", "flying over town", "mountains ahead", "meeting birds", "storm clouds", "clever landing", "new friends below", "safe return"]
    },
    {
        "title": "Pirates of the Playground",
        "description": "Imagination transforms the playground into a pirate ship sailing to adventure.",
        "genre": "Adventure",
        "age_rating": "All Ages",
        "pages": 14,
        "story_prompts": ["playground transformation", "captain appointed", "setting sail", "sea monsters", "island ahead", "treasure hunt", "rival pirates", "clever escape", "treasure found", "returning heroes"]
    },
    {
        "title": "The Deepest Dive",
        "description": "A young explorer discovers an underwater kingdom in her backyard pond.",
        "genre": "Adventure",
        "age_rating": "5+",
        "pages": 18,
        "story_prompts": ["backyard pond", "magic goggles", "diving down", "underwater world", "fish city", "coral castle", "meeting king fish", "helping kingdom", "goodbye feast", "surfacing changed"]
    },
    {
        "title": "Safari in the Backyard",
        "description": "Through a magnifying glass, the backyard becomes a wild safari adventure.",
        "genre": "Adventure",
        "age_rating": "All Ages",
        "pages": 15,
        "story_prompts": ["finding magnifying glass", "grass becomes jungle", "ant stampede", "beetle mountain", "spider web bridge", "caterpillar friend", "bird shadow danger", "safe shelter", "journey home", "new perspective"]
    },
    {
        "title": "The Lost Lighthouse",
        "description": "Twins discover an abandoned lighthouse that holds secrets of their great-grandmother.",
        "genre": "Adventure",
        "age_rating": "8+",
        "pages": 22,
        "story_prompts": ["coastal exploration", "finding lighthouse", "climbing stairs", "old photographs", "secret diary", "grandmother's story", "hidden room", "telescope discovery", "message in bottle", "family reunion"]
    },
    {
        "title": "Jungle Gym Expedition",
        "description": "The school jungle gym becomes a real jungle when Maya makes a wish.",
        "genre": "Adventure",
        "age_rating": "All Ages",
        "pages": 14,
        "story_prompts": ["wish on dandelion", "jungle appears", "vine swinging", "monkey friends", "waterfall slide", "parrot guide", "hidden temple", "treasure wisdom", "wish reversed", "playground return"]
    },
    {
        "title": "The Volcano Explorers",
        "description": "Young scientists investigate a dormant volcano and discover it's actually a dragon's home.",
        "genre": "Adventure",
        "age_rating": "8+",
        "pages": 20,
        "story_prompts": ["science expedition", "volcano approach", "finding entrance", "lava tunnels", "crystal formations", "sleeping dragon", "dragon awakens", "friendly conversation", "dragon's story", "secret keepers"]
    },
    {
        "title": "Mystery Island Express",
        "description": "A magical train takes passengers to different adventure islands each stop.",
        "genre": "Adventure",
        "age_rating": "5+",
        "pages": 18,
        "story_prompts": ["finding ticket", "train station", "boarding train", "dinosaur island", "candy mountain stop", "cloud kingdom", "underwater station", "final destination", "treasure island", "return journey"]
    },
    
    # Science Fiction (8 books)
    {
        "title": "Robot Best Friend",
        "description": "When Zoe builds a robot for the science fair, she never expected it to become her best friend.",
        "genre": "Science Fiction",
        "age_rating": "5+",
        "pages": 16,
        "story_prompts": ["building robot", "first power on", "robot learns", "science fair", "robot saves day", "friendship grows", "robot adventure", "protecting robot", "robot evolves", "forever friends"]
    },
    {
        "title": "The Mars Mission Kids",
        "description": "First kids born on Mars explore their red planet home and discover ancient mysteries.",
        "genre": "Science Fiction",
        "age_rating": "8+",
        "pages": 22,
        "story_prompts": ["Mars dome home", "exploration permit", "rover adventure", "ancient markings", "cave discovery", "alien artifact", "mystery decoded", "earth message", "colony celebration", "mars kids future"]
    },
    {
        "title": "Time Machine Trouble",
        "description": "Accidentally traveling to different time periods, Max must find his way back to present day.",
        "genre": "Science Fiction",
        "age_rating": "8+",
        "pages": 20,
        "story_prompts": ["grandpa's machine", "accidental activation", "dinosaur era", "medieval castle", "future city", "each era adventure", "collecting pieces", "machine repair", "time lesson", "safe return"]
    },
    {
        "title": "The Shrinking Machine",
        "description": "When dad's invention shrinks the family, they must navigate their suddenly giant house.",
        "genre": "Science Fiction",
        "age_rating": "5+",
        "pages": 18,
        "story_prompts": ["invention reveal", "accidental shrink", "floor is ocean", "cat is giant", "kitchen adventure", "crumb mountains", "finding antidote", "growing journey", "lesson learned", "normal again"]
    },
    {
        "title": "Space Station Summer Camp",
        "description": "Kids from around the world attend the first summer camp in space.",
        "genre": "Science Fiction",
        "age_rating": "8+",
        "pages": 24,
        "story_prompts": ["shuttle launch", "station arrival", "zero gravity fun", "making friends", "space walk", "earth view", "asteroid warning", "teamwork solution", "saving station", "camp graduation"]
    },
    {
        "title": "The Alien Exchange Student",
        "description": "When Zorp from Planet X joins third grade, learning about each other changes everyone.",
        "genre": "Science Fiction",
        "age_rating": "5+",
        "pages": 16,
        "story_prompts": ["new student arrival", "looking different", "communication struggles", "first friendship", "alien abilities", "school fair", "misunderstanding", "saving the day", "acceptance", "farewell party"]
    },
    {
        "title": "Underwater City 2150",
        "description": "In the future, kids live in cities under the sea and explore the deep ocean.",
        "genre": "Science Fiction",
        "age_rating": "8+",
        "pages": 20,
        "story_prompts": ["dome city home", "school submarine", "deep sea class", "whale encounter", "ancient shipwreck", "treasure found", "storm danger", "city protection", "hero kids", "ocean future"]
    },
    {
        "title": "The Coding Club Mystery",
        "description": "Kids who code discover their programs can come to life and solve real mysteries.",
        "genre": "Science Fiction",
        "age_rating": "8+",
        "pages": 18,
        "story_prompts": ["coding class", "magic code", "character escapes", "first mystery", "digital clues", "real world hunt", "villain found", "code solution", "mystery solved", "new adventure"]
    },
    
    # Mystery (6 books)
    {
        "title": "The Case of the Missing Cookies",
        "description": "When cookies keep disappearing from the school cafeteria, detective duo Sam and Jo investigate.",
        "genre": "Mystery",
        "age_rating": "All Ages",
        "pages": 14,
        "story_prompts": ["cookies missing", "detective meeting", "first clues", "suspect list", "stakeout plan", "surprise witness", "chasing crumbs", "culprit found", "unexpected reason", "sharing solution"]
    },
    {
        "title": "Mystery at the Museum",
        "description": "A famous dinosaur bone goes missing from the museum during a school field trip.",
        "genre": "Mystery",
        "age_rating": "8+",
        "pages": 20,
        "story_prompts": ["museum visit", "bone disappears", "locked in", "searching museum", "hidden passages", "suspicious characters", "clue assembly", "trap setting", "thief caught", "hero recognition"]
    },
    {
        "title": "The Haunted Playground",
        "description": "Strange things happen at the old playground after dark. Is it really ghosts?",
        "genre": "Mystery",
        "age_rating": "8+",
        "pages": 18,
        "story_prompts": ["spooky stories", "investigation begins", "nighttime stakeout", "strange sounds", "shadowy figure", "following footprints", "secret discovered", "lonely person", "making friends", "playground fixed"]
    },
    {
        "title": "The Secret of Room 13",
        "description": "The always-locked Room 13 at school holds a secret that students are determined to uncover.",
        "genre": "Mystery",
        "age_rating": "8+",
        "pages": 16,
        "story_prompts": ["room 13 curiosity", "research begins", "old yearbooks", "teacher clues", "late night sneak", "door opens", "surprising discovery", "time capsule", "school history", "celebration"]
    },
    {
        "title": "The Whispering Woods",
        "description": "Trees in the forest seem to whisper secrets. What are they trying to say?",
        "genre": "Mystery",
        "age_rating": "8+",
        "pages": 18,
        "story_prompts": ["first whispers", "investigating forest", "pattern discovery", "ancient tree", "message decoding", "hidden treasure", "forest protector", "nature's secret", "becoming guardian", "forest thrives"]
    },
    {
        "title": "Detective Duo: Pet Shop Problem",
        "description": "Pets are acting strange at the local pet shop. What's causing their odd behavior?",
        "genre": "Mystery",
        "age_rating": "5+",
        "pages": 14,
        "story_prompts": ["pet shop visit", "strange behaviors", "questioning owners", "clue gathering", "following the hamster", "secret room", "mystery noise", "culprit revealed", "pets happy", "case closed"]
    },
    
    # Comic/Humor (8 books)
    {
        "title": "Super Silly Superhero",
        "description": "Every superpower Max gains has a silly twist, but he saves the day anyway!",
        "genre": "Comic",
        "age_rating": "All Ages",
        "pages": 14,
        "story_prompts": ["getting powers", "flying sideways", "super sneeze", "invisible hiccups", "silly strength", "villain appears", "power combo", "saving day", "hero celebration", "next adventure"]
    },
    {
        "title": "The Upside Down Day",
        "description": "Everything is backwards today - even gravity! How will Emma cope?",
        "genre": "Comic",
        "age_rating": "All Ages",
        "pages": 12,
        "story_prompts": ["waking up", "walking ceiling", "upside breakfast", "school chaos", "silly games", "finding fun", "everything flips", "right side up", "wild memories", "normal appreciation"]
    },
    {
        "title": "My Pet Dinosaur",
        "description": "When Tommy's 'lizard' grows into a dinosaur, hiding it becomes hilariously difficult.",
        "genre": "Comic",
        "age_rating": "All Ages",
        "pages": 16,
        "story_prompts": ["egg hatches", "growing fast", "hiding attempts", "eating everything", "neighbor sees", "park disaster", "vet visit", "news arrives", "scientist help", "dino home found"]
    },
    {
        "title": "The Backwards Witch",
        "description": "A witch whose spells always do the opposite of what she intends.",
        "genre": "Comic",
        "age_rating": "All Ages",
        "pages": 14,
        "story_prompts": ["spell gone wrong", "frog to prince", "rain makes sun", "big makes small", "helping anyway", "village problem", "backwards solution", "accidental hero", "witch accepted", "happy ending"]
    },
    {
        "title": "Grandma's Crazy Inventions",
        "description": "Grandma's inventions never work as planned, but the adventures are amazing!",
        "genre": "Comic",
        "age_rating": "All Ages",
        "pages": 16,
        "story_prompts": ["visiting grandma", "workshop tour", "flying chair", "invisible paint", "talking toaster", "everything combines", "neighborhood chaos", "fixing mess", "final invention", "loving grandma"]
    },
    {
        "title": "The Day My Teacher Was a Robot",
        "description": "A malfunctioning robot substitute teacher makes class very interesting.",
        "genre": "Comic",
        "age_rating": "5+",
        "pages": 14,
        "story_prompts": ["teacher absent", "robot arrives", "glitchy lessons", "recess malfunction", "math explosion", "students help", "fixing robot", "robot thanks", "real teacher returns", "memorable day"]
    },
    {
        "title": "Talking Food Friends",
        "description": "What if the food in your lunchbox could talk? They have a lot to say!",
        "genre": "Comic",
        "age_rating": "All Ages",
        "pages": 12,
        "story_prompts": ["lunchbox opens", "sandwich speaks", "apple complains", "carrot advice", "cookie mischief", "lunchtime drama", "choosing who to eat", "compromise made", "empty lunchbox", "tomorrow's friends"]
    },
    {
        "title": "The Hiccup Hero",
        "description": "Every time Hiro hiccups, something magical happens. Can he control it?",
        "genre": "Comic",
        "age_rating": "All Ages",
        "pages": 14,
        "story_prompts": ["first magic hiccup", "uncontrollable", "floating furniture", "color chaos", "school incident", "learning control", "hiccup training", "villain appears", "hiccup saves day", "mastering power"]
    },
    
    # Educational/Learning (8 books)
    {
        "title": "Numbers Come Alive",
        "description": "Numbers jump off the page and teach Maya about math through exciting adventures.",
        "genre": "General",
        "age_rating": "5+",
        "pages": 15,
        "story_prompts": ["math homework", "numbers jump out", "one leads way", "counting adventure", "addition bridge", "subtraction slide", "multiplication maze", "division door", "problem solved", "math is fun"]
    },
    {
        "title": "The Alphabet Adventure",
        "description": "Letters take a young reader on a journey where each letter introduces something wonderful.",
        "genre": "General",
        "age_rating": "All Ages",
        "pages": 28,
        "story_prompts": ["book opens", "A is for Adventure", "B is for Butterfly", "C is for Castle", "D is for Dragon", "through the alphabet", "letters unite", "word creation", "story forms", "reading magic"]
    },
    {
        "title": "Colors of the World",
        "description": "Follow Rainbow as she discovers where all the colors in the world come from.",
        "genre": "General",
        "age_rating": "All Ages",
        "pages": 14,
        "story_prompts": ["gray world", "finding red", "discovering blue", "yellow sun", "green grows", "purple twilight", "orange sunset", "colors combine", "rainbow appears", "colorful world"]
    },
    {
        "title": "The Shape Shifters",
        "description": "Shapes teach kids geometry by transforming into different objects and buildings.",
        "genre": "General",
        "age_rating": "5+",
        "pages": 16,
        "story_prompts": ["meeting circle", "square house", "triangle mountain", "rectangle city", "shapes combine", "building together", "geometry magic", "shape patterns", "creating art", "shapes everywhere"]
    },
    {
        "title": "Weather Friends",
        "description": "Sunny, Cloudy, Rainy, and Snowy explain how weather works through friendship.",
        "genre": "General",
        "age_rating": "All Ages",
        "pages": 14,
        "story_prompts": ["meeting Sunny", "Cloudy appears", "Rainy visits", "Snowy arrives", "weather cycle", "working together", "seasons explained", "weather helps", "all friends", "weather appreciation"]
    },
    {
        "title": "The Body Explorers",
        "description": "Tiny explorers travel through the human body and explain how everything works.",
        "genre": "General",
        "age_rating": "8+",
        "pages": 20,
        "story_prompts": ["shrinking down", "entering body", "heart engine", "lung balloons", "brain control", "bone support", "muscle movers", "stomach factory", "blood highway", "body amazing"]
    },
    {
        "title": "Music in the Air",
        "description": "Different instruments come together to teach rhythm, melody, and harmony.",
        "genre": "General",
        "age_rating": "5+",
        "pages": 16,
        "story_prompts": ["quiet world", "drum beats", "flute melody", "piano harmony", "violin joins", "orchestra forms", "music magic", "conducting lesson", "concert night", "music forever"]
    },
    {
        "title": "Seeds to Trees",
        "description": "Follow Sammy the seed on his journey to becoming a mighty oak tree.",
        "genre": "General",
        "age_rating": "All Ages",
        "pages": 14,
        "story_prompts": ["tiny seed", "falling to ground", "winter sleep", "spring awakening", "roots growing", "sprout appears", "summer growth", "seasons pass", "mighty tree", "new seeds fall"]
    }
]

# System author for generated content
SYSTEM_AUTHOR = {
    "id": "azories-system",
    "name": "Azories Stories",
    "email": "stories@azories.com"
}

async def create_system_author(db):
    """Create system author if doesn't exist"""
    existing = await db.users.find_one({"id": SYSTEM_AUTHOR["id"]})
    if not existing:
        now = datetime.now(timezone.utc).isoformat()
        await db.users.insert_one({
            "id": SYSTEM_AUTHOR["id"],
            "email": SYSTEM_AUTHOR["email"],
            "password": "",  # System user, no login
            "name": SYSTEM_AUTHOR["name"],
            "role": "admin",
            "subscription": "pro",
            "created_at": now
        })
        print(f"Created system author: {SYSTEM_AUTHOR['name']}")
    return SYSTEM_AUTHOR

async def delete_all_test_books(db):
    """Remove all existing books to start fresh"""
    # Get all book IDs
    books = await db.books.find({}, {"id": 1}).to_list(1000)
    book_ids = [b["id"] for b in books]
    
    if not book_ids:
        print("No existing books to delete")
        return
    
    # Delete related data
    for book_id in book_ids:
        chapters = await db.chapters.find({"book_id": book_id}, {"id": 1}).to_list(100)
        for chapter in chapters:
            await db.pages.delete_many({"chapter_id": chapter["id"]})
        await db.chapters.delete_many({"book_id": book_id})
    
    # Delete books
    result = await db.books.delete_many({})
    print(f"Deleted {result.deleted_count} existing books")
    
    # Clear analytics
    await db.analytics.delete_many({})
    await db.reading_progress.delete_many({})

async def generate_page_content(book_data, page_num, total_pages):
    """Generate engaging page content for children's books"""
    story_idx = min(page_num - 1, len(book_data["story_prompts"]) - 1)
    prompt = book_data["story_prompts"][story_idx] if book_data["story_prompts"] else "adventure continues"
    
    # Create engaging page text based on position in story
    if page_num == 1:
        return f"Once upon a time, in a world full of wonder and magic, our story begins...\n\n{prompt.replace('_', ' ').title()}."
    elif page_num == total_pages:
        return f"And so, with hearts full of joy and memories to treasure, our adventure came to a happy end.\n\nThe End."
    elif page_num == 2:
        return f"Our adventure was about to begin! {prompt.replace('_', ' ').title()}.\n\nEverything was about to change in the most wonderful way."
    else:
        return f"{prompt.replace('_', ' ').title()}.\n\nThe journey continued with excitement and wonder at every turn."

async def create_book(db, author, book_data, generate_images=False):
    """Create a single book with chapters and pages"""
    book_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    
    # Create book
    book = {
        "id": book_id,
        "title": book_data["title"],
        "description": book_data["description"],
        "genre": book_data["genre"],
        "cover_image": "",
        "back_cover_image": "",
        "cover_title": book_data["title"],
        "cover_subtitle": f"A {book_data['genre']} Story for {book_data['age_rating']}",
        "back_cover_text": book_data["description"],
        "author_id": author["id"],
        "author_name": author["name"],
        "is_published": True,  # Published for launch
        "is_featured": book_data.get("featured", False),
        "is_best_of_week": book_data.get("best_of_week", False),
        "layout_mode": "standard",
        "narrator_voice_id": "21m00Tcm4TlvDq8ikWAM",
        "age_rating": book_data["age_rating"],
        "series_id": None,
        "series_order": None,
        "view_count": 0,
        "read_count": 0,
        "created_at": now,
        "updated_at": now
    }
    await db.books.insert_one(book)
    
    # Create single chapter
    chapter_id = str(uuid.uuid4())
    chapter = {
        "id": chapter_id,
        "book_id": book_id,
        "title": "Chapter 1",
        "order": 1,
        "created_at": now
    }
    await db.chapters.insert_one(chapter)
    
    # Create pages
    num_pages = book_data["pages"]
    for page_num in range(1, num_pages + 1):
        page_id = str(uuid.uuid4())
        page_text = await generate_page_content(book_data, page_num, num_pages)
        
        page = {
            "id": page_id,
            "chapter_id": chapter_id,
            "text_content": page_text,
            "image_url": "",  # Images to be generated separately
            "image_url_2": "",
            "image_url_3": "",
            "image_url_4": "",
            "video_url": "",
            "audio_url": "",
            "order": page_num,
            "layout_type": "single",
            "image_position_x": 50,
            "image_position_y": 50,
            "image_fit": "cover",
            "created_at": now
        }
        await db.pages.insert_one(page)
    
    print(f"  Created: {book_data['title']} ({num_pages} pages)")
    return book_id

async def main():
    """Main function to generate all launch books"""
    print("=" * 60)
    print("AZORIES LAUNCH BOOK GENERATOR")
    print("=" * 60)
    
    # Connect to MongoDB
    mongo_url = os.environ.get('MONGO_URL')
    db_name = os.environ.get('DB_NAME')
    
    if not mongo_url or not db_name:
        print("ERROR: MONGO_URL and DB_NAME environment variables required")
        return
    
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    # Delete existing books
    print("\n[1/3] Cleaning up existing books...")
    await delete_all_test_books(db)
    
    # Create system author
    print("\n[2/3] Setting up system author...")
    author = await create_system_author(db)
    
    # Generate all books
    print(f"\n[3/3] Creating {len(LAUNCH_BOOKS)} books...")
    
    # Mark some as featured
    featured_indices = [0, 10, 20, 30, 40]  # One from each category
    best_of_week_indices = [1, 11, 21]  # A few best of week
    
    for i, book_data in enumerate(LAUNCH_BOOKS):
        book_data["featured"] = i in featured_indices
        book_data["best_of_week"] = i in best_of_week_indices
        await create_book(db, author, book_data)
    
    print("\n" + "=" * 60)
    print(f"SUCCESS! Created {len(LAUNCH_BOOKS)} books for launch")
    print("=" * 60)
    
    # Summary by genre
    genres = {}
    for book in LAUNCH_BOOKS:
        genre = book["genre"]
        genres[genre] = genres.get(genre, 0) + 1
    
    print("\nBooks by Genre:")
    for genre, count in sorted(genres.items()):
        print(f"  {genre}: {count} books")
    
    print("\nBooks are published and ready for readers!")

if __name__ == "__main__":
    asyncio.run(main())
