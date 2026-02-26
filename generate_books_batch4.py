#!/usr/bin/env python3
"""
Book Generation Script - Batch 4 (Using fal.ai - cheaper!)
Remaining 19 books to complete
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

# Templates for remaining 19 books
BOOK_TEMPLATES = {
    "Flame's Courageous Journey": {
        "age_range": "6-8",
        "genre": "Fantasy",
        "art_style": "watercolour",
        "style_prompt": "Warm watercolour children's book illustration, baby dragon theme, adventure with heart",
        "characters": {
            "main": "Flame, a small orange dragon who's afraid of fire but learns to be brave"
        },
        "pages": [
            {"text": "Flame's Courageous Journey\n\nA Dragon's Tale", "scene": "Title page: Small cute orange dragon looking nervous but hopeful"},
            {"text": "Flame was a dragon who was afraid of fire. Yes, his OWN fire!", "scene": "Baby dragon hiccuping tiny flame and looking scared"},
            {"text": "Other dragons breathed big flames. But Flame? Only little sparks came out.", "scene": "Other dragons breathing impressive flames while Flame produces tiny spark"},
            {"text": "\"I'm not a real dragon,\" Flame sighed. \"I can't do anything right.\"", "scene": "Sad Flame sitting alone on a rock, other dragons flying in background"},
            {"text": "One day, a village needed help. A flood was coming!", "scene": "Flame seeing village below with rising water threatening it"},
            {"text": "Big dragons couldn't help - their fire made steam that made things worse!", "scene": "Big dragon fire creating steam clouds, villagers worried"},
            {"text": "But Flame had an idea! His tiny sparks could light the warning beacons!", "scene": "Flame carefully lighting small beacon torches with precise tiny flames"},
            {"text": "One by one, Flame lit every beacon. The village was warned in time!", "scene": "Chain of lit beacons across mountains, villagers evacuating safely"},
            {"text": "\"You saved us all!\" the villagers cheered. Flame stood tall with pride.", "scene": "Villagers celebrating Flame, other dragons watching proudly"},
            {"text": "Flame learned that being different isn't bad - it's what makes you special!\n\nThe End", "scene": "Flame confidently producing beautiful small flame, happy ending"}
        ]
    },
    
    "Friendship Island": {
        "age_range": "6-8",
        "genre": "Adventure",
        "art_style": "cartoon",
        "style_prompt": "Bright tropical cartoon children's book illustration, island adventure, friendship theme",
        "characters": {
            "main": "Sunny the crab, Splash the dolphin, and Breeze the seagull - unlikely friends"
        },
        "pages": [
            {"text": "Friendship Island\n\nWhere Friends are Found", "scene": "Title page: Tropical island with crab, dolphin, and seagull together"},
            {"text": "On a tiny island lived Sunny the crab. She had lots of shells but no friends.", "scene": "Lonely crab on beach surrounded by beautiful shells"},
            {"text": "Splash the dolphin swam by every day. \"Want to play?\" But Sunny was too shy.", "scene": "Friendly dolphin waving fin, crab hiding in shell"},
            {"text": "Breeze the seagull landed nearby. \"Hello!\" Sunny scuttled away nervously.", "scene": "Seagull landing, crab sideways-walking away"},
            {"text": "One stormy day, Sunny's shell collection washed away!", "scene": "Storm scene with shells being swept out to sea, crab distressed"},
            {"text": "Splash dove deep to find the shells. Breeze flew high to spot them!", "scene": "Dolphin diving, seagull searching from above"},
            {"text": "Together they brought back every single shell!", "scene": "Dolphin and seagull delivering shells to grateful crab"},
            {"text": "\"You did that... for ME?\" Sunny couldn't believe it.", "scene": "Crab looking at pile of recovered shells, friends smiling"},
            {"text": "\"That's what friends do,\" Splash smiled. Sunny smiled back.", "scene": "Three friends together on beach, sunset"},
            {"text": "Now the island isn't lonely anymore. It's Friendship Island!\n\nThe End", "scene": "Three friends playing together, island looking happy and alive"}
        ]
    },
    
    "The Lighthouse Keeper's Secret": {
        "age_range": "6-8",
        "genre": "Adventure",
        "art_style": "realistic",
        "style_prompt": "Detailed atmospheric children's book illustration, coastal lighthouse theme, mystery and wonder",
        "characters": {
            "main": "Old Captain Eli and young Maya who discovers his magical secret"
        },
        "pages": [
            {"text": "The Lighthouse Keeper's Secret\n\nA Seaside Mystery", "scene": "Title page: Old lighthouse at dusk with mysterious glow"},
            {"text": "Maya loved visiting the old lighthouse. Captain Eli always had stories to tell.", "scene": "Young girl visiting elderly lighthouse keeper, cozy interior"},
            {"text": "But one stormy night, Maya saw something strange - the light was PURPLE!", "scene": "Maya watching purple light beam from lighthouse in storm"},
            {"text": "\"What was that?\" she asked. Captain Eli smiled mysteriously.", "scene": "Eli with knowing smile, Maya curious"},
            {"text": "\"Come,\" he said. \"It's time you knew the secret.\"", "scene": "Eli leading Maya up spiral lighthouse stairs"},
            {"text": "At the top, the light wasn't just a light - it was a portal to the stars!", "scene": "Magical star portal in lighthouse lamp room"},
            {"text": "\"I guide lost sailors AND lost star-travelers,\" Eli explained.", "scene": "Eli showing Maya tiny glowing star beings"},
            {"text": "Maya helped guide a lost star-child back to its constellation!", "scene": "Maya and Eli helping small glowing being return to stars"},
            {"text": "\"Will you keep the secret?\" Eli asked. \"And help me someday?\"", "scene": "Eli and Maya looking at stars together, meaningful moment"},
            {"text": "Maya promised. The lighthouse would always have a keeper.\n\nThe End", "scene": "Maya waving from lighthouse, stars twinkling approvingly"}
        ]
    },
    
    "The Time Machine Treehouse": {
        "age_range": "6-8",
        "genre": "Science Fiction",
        "art_style": "cartoon",
        "style_prompt": "Colorful adventurous cartoon children's book illustration, time travel theme, steampunk treehouse",
        "characters": {
            "main": "Twins Max and Mia who discover their treehouse can travel through time"
        },
        "pages": [
            {"text": "The Time Machine Treehouse\n\nAdventures Through Time", "scene": "Title page: Amazing treehouse with gears and clocks, time swirling around"},
            {"text": "Max and Mia's treehouse was special. Grandpa had built it with a SECRET.", "scene": "Twins in elaborate treehouse, discovering hidden control panel"},
            {"text": "\"Is that a... time dial?\" Mia gasped. Max accidentally pressed a button!", "scene": "Twins looking at mysterious dial, Max reaching for button"},
            {"text": "WHOOOOSH! Suddenly they were in dinosaur times!", "scene": "Treehouse materializing in prehistoric jungle, dinosaurs visible"},
            {"text": "\"Don't worry, we're invisible to them!\" the treehouse spoke!", "scene": "Twins watching dinosaurs safely from treehouse, amazed"},
            {"text": "They visited ancient Egypt and watched pyramids being built!", "scene": "Treehouse hovering near pyramids under construction"},
            {"text": "They saw knights in castles and ships exploring new lands!", "scene": "Medieval scene with knights and castles, twins watching"},
            {"text": "\"Time to go home,\" Max said. They turned the dial back to NOW.", "scene": "Twins adjusting dial, treehouse glowing"},
            {"text": "Back in their yard, everything looked the same. But they were different!", "scene": "Treehouse back in normal yard, twins with knowing smiles"},
            {"text": "They had seen wonders! And the treehouse was ready for more adventures.\n\nThe End", "scene": "Twins planning next trip, map of time periods spread out"}
        ]
    },
    
    "Mystery at the Zoo": {
        "age_range": "6-8",
        "genre": "Mystery",
        "art_style": "realistic",
        "style_prompt": "Detailed mystery children's book illustration, zoo animals, detective adventure",
        "characters": {
            "main": "Detective twins Zoe and Zack who solve animal mysteries"
        },
        "pages": [
            {"text": "Mystery at the Zoo\n\nThe Case of the Missing Bananas", "scene": "Title page: Twin detectives at zoo entrance with magnifying glasses"},
            {"text": "Someone was stealing bananas from the monkey house! Zoe and Zack were on the case.", "scene": "Twins examining empty banana bin, monkeys looking confused"},
            {"text": "\"Look for clues!\" said Zoe. They found yellow peels leading away...", "scene": "Twins following trail of banana peels through zoo"},
            {"text": "Past the lions (who looked innocent). Past the zebras (who were busy eating grass).", "scene": "Twins passing various animals, looking for suspect"},
            {"text": "The trail led to... the elephant house?", "scene": "Twins arriving at elephant enclosure, surprised"},
            {"text": "But elephants don't eat bananas! Or do they?", "scene": "Twins looking at elephant suspiciously"},
            {"text": "\"AHA!\" Zack spotted a baby elephant hiding behind its mother - with banana stash!", "scene": "Baby elephant caught with pile of bananas"},
            {"text": "The baby elephant was lonely and wanted the monkeys to visit!", "scene": "Baby elephant looking sad, bananas were just to make friends"},
            {"text": "They arranged a playdate! Now the baby elephant and monkeys are best friends.", "scene": "Monkeys and baby elephant playing together happily"},
            {"text": "Case closed! Sometimes thieves just want friends.\n\nThe End", "scene": "Twins taking photos of new animal friendships"}
        ]
    },
    
    "The Haunted Library Book": {
        "age_range": "6-8",
        "genre": "Mystery",
        "art_style": "watercolour",
        "style_prompt": "Atmospheric watercolour children's book illustration, friendly spooky library theme",
        "characters": {
            "main": "Bookworm Billy who discovers a book that's haunted by a friendly ghost author"
        },
        "pages": [
            {"text": "The Haunted Library Book\n\nA Not-So-Scary Story", "scene": "Title page: Boy holding glowing book in cozy library"},
            {"text": "Billy loved the library. One day, he found a dusty book that GLOWED.", "scene": "Boy discovering glowing book on high shelf"},
            {"text": "When he opened it, the pages turned by themselves!", "scene": "Book pages flipping magically, Billy amazed"},
            {"text": "\"Hello!\" said a friendly voice. A ghost appeared - the book's author!", "scene": "Friendly transparent ghost appearing from book"},
            {"text": "\"I'm Penelope. I wrote this book 100 years ago, but no one reads it anymore.\"", "scene": "Ghost author looking sad, pointing at forgotten book"},
            {"text": "Billy read the whole book. It was AMAZING! Adventures, dragons, heroes!", "scene": "Billy reading excitedly, story scenes floating around him"},
            {"text": "\"This deserves to be read!\" Billy told the librarian about his discovery.", "scene": "Billy showing book to kind librarian"},
            {"text": "The librarian made it the 'Book of the Month'! Everyone wanted to read it!", "scene": "Book displayed prominently, kids lining up to borrow"},
            {"text": "Penelope's ghost smiled. \"Thank you, Billy. My story lives on!\"", "scene": "Ghost fading happily as more kids read the book"},
            {"text": "Billy learned that every book has a story - even books about books!\n\nThe End", "scene": "Billy in library surrounded by glowing happy books"}
        ]
    },
    
    "Puzzle Palace Adventures": {
        "age_range": "6-8",
        "genre": "Mystery",
        "art_style": "cartoon",
        "style_prompt": "Colorful puzzle-themed cartoon children's book illustration, palace with riddles",
        "characters": {
            "main": "Princess Petra who loves puzzles more than parties"
        },
        "pages": [
            {"text": "Puzzle Palace Adventures\n\nThe Princess Who Loved Riddles", "scene": "Title page: Princess surrounded by puzzles and riddles in colorful palace"},
            {"text": "Princess Petra didn't like fancy dresses or balls. She loved PUZZLES!", "scene": "Princess ignoring fancy things, doing puzzles instead"},
            {"text": "Her father, the King, turned the whole palace into a puzzle adventure!", "scene": "King revealing palace transformed into puzzle maze"},
            {"text": "\"Solve the puzzles to find the treasure!\" he announced.", "scene": "Petra excitedly looking at first puzzle challenge"},
            {"text": "Room 1: A riddle! \"I have hands but cannot clap.\" A clock!", "scene": "Petra solving clock riddle, door opening"},
            {"text": "Room 2: A maze of mirrors! Petra found the real path using logic.", "scene": "Petra navigating mirror maze cleverly"},
            {"text": "Room 3: A code to crack! Letters and numbers swirled. Petra solved it!", "scene": "Petra working on cipher puzzle"},
            {"text": "The final door opened. Inside wasn't gold, but something better...", "scene": "Petra opening ornate final door"},
            {"text": "It was a library full of puzzle books from around the world!", "scene": "Amazing room filled with puzzle books, Petra overjoyed"},
            {"text": "\"Best treasure ever!\" Petra became known as the Puzzle Princess.\n\nThe End", "scene": "Petra sharing puzzles with kingdom children"}
        ]
    },
    
    "The Missing Birthday Present": {
        "age_range": "6-8",
        "genre": "Mystery",
        "art_style": "cartoon",
        "style_prompt": "Bright fun cartoon children's book illustration, birthday party mystery theme",
        "characters": {
            "main": "Tommy whose birthday present mysteriously disappears before he can open it"
        },
        "pages": [
            {"text": "The Missing Birthday Present\n\nA Birthday Mystery", "scene": "Title page: Boy looking under table for wrapped present"},
            {"text": "It was Tommy's birthday! His big present sat wrapped under the table.", "scene": "Birthday party setup with large wrapped present"},
            {"text": "But when it was time to open presents - the big one was GONE!", "scene": "Tommy and friends looking shocked at empty spot"},
            {"text": "\"Who took my present?\" Tommy became a birthday detective!", "scene": "Tommy with detective hat investigating"},
            {"text": "Clue 1: Glitter trail leading to the backyard!", "scene": "Tommy following glitter trail outside"},
            {"text": "Clue 2: A ribbon caught on the fence! Someone went OVER!", "scene": "Ribbon piece on fence, Tommy climbing to see"},
            {"text": "Clue 3: Giggling from the old playhouse!", "scene": "Tommy approaching playhouse, hearing giggles"},
            {"text": "Inside was... Dad! Setting up an even BIGGER surprise!", "scene": "Dad revealed decorating with amazing present"},
            {"text": "The present was moved to make room for a PUPPY!", "scene": "Tommy seeing adorable puppy with bow"},
            {"text": "Best birthday mystery ever! Tommy named the puppy 'Clue'!\n\nThe End", "scene": "Tommy hugging puppy at party, everyone happy"}
        ]
    },
    
    "Luna's Rainbow Adventure": {
        "age_range": "3-6",
        "genre": "Sci-Fi",
        "art_style": "watercolour",
        "style_prompt": "Dreamy watercolour children's book illustration, space rainbow theme, soft magical colors",
        "characters": {
            "main": "Luna, a little girl who rides rainbows between planets"
        },
        "pages": [
            {"text": "Luna's Rainbow Adventure\n\nA Colorful Space Journey", "scene": "Title page: Girl riding rainbow through starry space"},
            {"text": "Luna discovered that rainbows are really bridges to other worlds!", "scene": "Luna stepping onto rainbow after rain, discovering secret"},
            {"text": "She slid down a red rainbow to the Red Planet - Mars!", "scene": "Luna sliding on red rainbow toward Mars"},
            {"text": "On Mars, she met robots who loved to dance!", "scene": "Luna dancing with friendly Mars robots"},
            {"text": "An orange rainbow took her to a planet of friendly giants!", "scene": "Luna with gentle giants on orange planet"},
            {"text": "Yellow led to a sunny world where flowers sang!", "scene": "Luna among singing flowers on yellow planet"},
            {"text": "Green took her to a jungle planet with talking trees!", "scene": "Luna chatting with wise talking trees"},
            {"text": "Blue brought her to an ocean world with flying fish!", "scene": "Luna swimming with flying fish in blue ocean world"},
            {"text": "Purple led to a quiet world where dreams are made.", "scene": "Luna in dreamy purple world with floating dreams"},
            {"text": "Home on the full rainbow! Luna knew she'd visit again.\n\nThe End", "scene": "Luna returning home on complete rainbow, waving"}
        ]
    },
    
    "Lila and the Whispering Blossoms": {
        "age_range": "3-6",
        "genre": "Fantasy",
        "art_style": "watercolour",
        "style_prompt": "Delicate watercolour children's book illustration, enchanted garden theme, soft pinks and greens",
        "characters": {
            "main": "Lila, a gentle girl who can hear flowers speak"
        },
        "pages": [
            {"text": "Lila and the Whispering Blossoms\n\nA Garden Secret", "scene": "Title page: Girl listening to flowers in magical garden"},
            {"text": "Lila had a special gift. She could hear flowers whisper!", "scene": "Lila with ear close to flower, listening intently"},
            {"text": "The roses told her secrets. The daisies told her jokes!", "scene": "Lila laughing with daisies, roses looking dignified"},
            {"text": "But one day, all the flowers were sad. \"The Queen Blossom is wilting!\"", "scene": "Worried flowers, Lila concerned"},
            {"text": "Lila found the Queen Blossom - a magnificent flower, looking weak.", "scene": "Lila approaching large wilting flower"},
            {"text": "\"What do you need?\" Lila whispered. \"Someone to sing to me.\"", "scene": "Queen Blossom speaking weakly to Lila"},
            {"text": "Lila sang her grandmother's lullaby, soft and sweet.", "scene": "Lila singing beautifully, notes floating like butterflies"},
            {"text": "The Queen Blossom stood tall again! Her petals glowed!", "scene": "Queen Blossom blooming magnificently"},
            {"text": "\"Thank you, little one. Music heals the soul - even flower souls.\"", "scene": "Grateful Queen Blossom blessing Lila"},
            {"text": "Now Lila sings to her garden every day. And it sings back!\n\nThe End", "scene": "Lila in thriving garden, flowers and girl singing together"}
        ]
    },
    
    "The Midnight Brush": {
        "age_range": "6-8",
        "genre": "Fantasy",
        "art_style": "watercolour",
        "style_prompt": "Magical nighttime watercolour children's book illustration, art coming to life theme",
        "characters": {
            "main": "Milo, a young artist whose paintbrush brings his paintings to life at midnight"
        },
        "pages": [
            {"text": "The Midnight Brush\n\nWhen Art Comes Alive", "scene": "Title page: Boy with glowing paintbrush, paintings coming alive"},
            {"text": "Milo got an old paintbrush from a mysterious antique shop.", "scene": "Milo receiving ancient brush from wise shopkeeper"},
            {"text": "That night at midnight, his painted cat WALKED OUT of the canvas!", "scene": "Painted cat stepping out of painting, Milo amazed"},
            {"text": "\"The Midnight Brush!\" the cat explained. \"Whatever you paint lives at midnight!\"", "scene": "Cat talking to Milo, explaining magic"},
            {"text": "Milo painted a friend - a boy just like him! They played until dawn.", "scene": "Milo playing with painted friend"},
            {"text": "He painted a dragon - friendly, of course! They flew over the town.", "scene": "Milo riding friendly painted dragon"},
            {"text": "But then he painted something sad - a lonely monster.", "scene": "Sad monster emerging from painting"},
            {"text": "\"I don't want to be scary,\" it cried. So Milo painted it a friend!", "scene": "Milo painting friend for monster"},
            {"text": "He learned: what you create affects others. Paint with kindness!", "scene": "Milo surrounded by happy creations"},
            {"text": "Now Milo only paints joy. And every midnight, his room fills with friends.\n\nThe End", "scene": "Room full of wonderful living paintings"}
        ]
    },
    
    "The Emotion Squad: Power of Unity": {
        "age_range": "6-8",
        "genre": "Adventure",
        "art_style": "cartoon",
        "style_prompt": "Bold colorful cartoon children's book illustration, emotions as superheroes",
        "characters": {
            "main": "Joy, Sadness, Anger, Fear, and Calm - emotion heroes who work together"
        },
        "pages": [
            {"text": "The Emotion Squad: Power of Unity\n\nFeelings Are Superpowers", "scene": "Title page: Five emotion superheroes posing together"},
            {"text": "Inside everyone lives the Emotion Squad - feelings that help us every day!", "scene": "Five cute emotion characters introducing themselves"},
            {"text": "Joy makes us smile and gives us energy to play!", "scene": "Yellow Joy character spreading happiness"},
            {"text": "Sadness helps us heal and lets others know we need hugs.", "scene": "Blue Sadness character being comforted"},
            {"text": "Anger protects us when something isn't fair!", "scene": "Red Anger character standing up for someone"},
            {"text": "Fear keeps us safe from danger - it's like an alarm!", "scene": "Purple Fear character warning of danger"},
            {"text": "Calm helps us breathe and think clearly.", "scene": "Green Calm character bringing peace"},
            {"text": "One day, a big problem came. Each emotion tried alone - but failed!", "scene": "Each emotion trying solo, not working"},
            {"text": "\"Together!\" said Joy. They combined their powers!", "scene": "Emotions joining hands, power combining"},
            {"text": "All emotions matter. Together, they make us complete!\n\nThe End", "scene": "Emotion Squad united, rainbow of feelings"}
        ]
    },
    
    "The Robot Who Wanted Friends": {
        "age_range": "6-8",
        "genre": "Science Fiction",
        "art_style": "cartoon",
        "style_prompt": "Warm cartoon children's book illustration, friendly robot theme, learning friendship",
        "characters": {
            "main": "Rusty, a robot built for tasks who discovers he wants friends"
        },
        "pages": [
            {"text": "The Robot Who Wanted Friends\n\nA Heart of Gears", "scene": "Title page: Cute robot looking at children playing"},
            {"text": "Rusty was built to do chores. Clean, cook, organize. That's all.", "scene": "Robot doing household tasks efficiently"},
            {"text": "But Rusty noticed something - children laughing together. What was THAT?", "scene": "Rusty watching kids play, curious"},
            {"text": "\"That is friendship,\" the computer said. \"Robots don't need it.\"", "scene": "Rusty asking computer, receiving cold answer"},
            {"text": "But Rusty WANTED it! He tried to play but didn't know how.", "scene": "Rusty awkwardly trying to join game"},
            {"text": "He brought toys - too many! He talked - too loud! Everything was wrong.", "scene": "Rusty trying too hard, scaring kids away"},
            {"text": "Sad Rusty sat alone. A little girl came up. \"Are you okay?\"", "scene": "Kind girl approaching sad robot"},
            {"text": "\"I want friends but I don't know how,\" Rusty admitted.", "scene": "Rusty being honest with the girl"},
            {"text": "\"Just be yourself,\" she smiled. \"And listen. That's how friendship starts.\"", "scene": "Girl teaching Rusty about friendship"},
            {"text": "Rusty learned to listen, share, and care. Now he has more friends than circuits!\n\nThe End", "scene": "Rusty surrounded by children friends"}
        ]
    },
    
    "Princess and the Enchanted Forest": {
        "age_range": "3-6",
        "genre": "Fairy Tales",
        "art_style": "watercolour",
        "style_prompt": "Classic fairytale watercolour children's book illustration, enchanted forest magic",
        "characters": {
            "main": "Princess Ivy who prefers exploring the forest to living in a castle"
        },
        "pages": [
            {"text": "Princess and the Enchanted Forest\n\nA Different Kind of Princess", "scene": "Title page: Princess in boots exploring magical forest"},
            {"text": "Princess Ivy didn't like sitting still. She loved the forest!", "scene": "Princess sneaking away from boring royal duties"},
            {"text": "Her parents worried. \"The forest is dangerous!\" But Ivy knew better.", "scene": "King and Queen worried, Ivy determined"},
            {"text": "The trees were her friends. They whispered secrets of the kingdom.", "scene": "Ivy talking with friendly trees"},
            {"text": "The animals trusted her. She helped lost fawns find their mothers.", "scene": "Ivy helping baby deer in forest"},
            {"text": "One day, a drought threatened the kingdom. The crops were dying!", "scene": "Worried kingdom with dry fields"},
            {"text": "Ivy asked the forest for help. The trees knew where hidden springs were!", "scene": "Trees showing Ivy secret water sources"},
            {"text": "She led her people to fresh water! The kingdom was saved!", "scene": "Ivy showing villagers the springs, celebration"},
            {"text": "The King understood now. \"The forest is your gift, Ivy.\"", "scene": "King praising Ivy, accepting her nature"},
            {"text": "Princess Ivy became the Forest Guardian - the kingdom's greatest treasure.\n\nThe End", "scene": "Ivy as beloved guardian of forest and kingdom"}
        ]
    },
    
    "The Dinosaur Time Machine": {
        "age_range": "6-8",
        "genre": "Adventure",
        "art_style": "cartoon",
        "style_prompt": "Exciting cartoon children's book illustration, dinosaurs and time travel adventure",
        "characters": {
            "main": "Dino-expert Danny who accidentally travels back to dinosaur times"
        },
        "pages": [
            {"text": "The Dinosaur Time Machine\n\nBack to the Jurassic!", "scene": "Title page: Boy with dinosaur toys suddenly surrounded by real ones"},
            {"text": "Danny knew EVERYTHING about dinosaurs. He wished he could see them for real.", "scene": "Danny reading dinosaur books in bedroom"},
            {"text": "His toy T-Rex started glowing! \"Your wish is granted!\" WHOOOOSH!", "scene": "Toy glowing, time portal opening"},
            {"text": "Danny landed in a prehistoric jungle. Real dinosaurs everywhere!", "scene": "Danny amazed by real dinosaurs"},
            {"text": "A friendly Triceratops let him ride! \"This is AMAZING!\"", "scene": "Danny riding Triceratops through ferns"},
            {"text": "He watched Pterodactyls fly and Brachiosaurus eat from tall trees.", "scene": "Danny observing various dinosaurs"},
            {"text": "But then - THUMP THUMP - a T-Rex appeared!", "scene": "Scary T-Rex approaching"},
            {"text": "Danny remembered: T-Rex has bad eyesight! He stood very still.", "scene": "Danny freezing, T-Rex sniffing confused"},
            {"text": "The T-Rex walked away! Danny's knowledge saved him!", "scene": "T-Rex leaving, Danny relieved"},
            {"text": "Back home, Danny knew: learning isn't just fun - it's powerful!\n\nThe End", "scene": "Danny back home, hugging his dinosaur books"}
        ]
    },
    
    "Ocean Wonders": {
        "age_range": "3-6",
        "genre": "Educational",
        "art_style": "watercolour",
        "style_prompt": "Beautiful underwater watercolour children's book illustration, ocean education theme",
        "characters": {
            "main": "Coral the mermaid who teaches children about ocean life"
        },
        "pages": [
            {"text": "Ocean Wonders\n\nA Dive into the Deep", "scene": "Title page: Friendly mermaid welcoming readers underwater"},
            {"text": "\"Come explore the ocean with me!\" said Coral the mermaid.", "scene": "Mermaid inviting children into underwater world"},
            {"text": "The coral reef is like an underwater city! Fish live in every corner.", "scene": "Colorful coral reef teeming with life"},
            {"text": "Clownfish hide in anemones. They're best friends who protect each other!", "scene": "Clownfish in anemone, both happy"},
            {"text": "Sea turtles are ancient travelers. They swim thousands of miles!", "scene": "Majestic sea turtle swimming"},
            {"text": "Dolphins are the ocean's playful puppies. They talk with clicks!", "scene": "Playful dolphins doing tricks"},
            {"text": "Even the scary-looking sharks keep the ocean healthy!", "scene": "Friendly shark explained as ocean helper"},
            {"text": "The deep sea has creatures that GLOW! Like underwater stars!", "scene": "Bioluminescent deep sea creatures"},
            {"text": "\"The ocean needs our help,\" Coral said. \"Keep it clean and wonderful!\"", "scene": "Mermaid showing importance of clean ocean"},
            {"text": "Now you know ocean secrets! Go share them with the world!\n\nThe End", "scene": "Mermaid waving goodbye, ocean creatures waving"}
        ]
    },
    
    "Cooking Adventures with Chef Cat": {
        "age_range": "3-6",
        "genre": "Educational",
        "art_style": "cartoon",
        "style_prompt": "Fun colorful cartoon children's book illustration, cooking and food education",
        "characters": {
            "main": "Chef Whiskers, a cat who teaches healthy cooking to kids"
        },
        "pages": [
            {"text": "Cooking Adventures with Chef Cat\n\nYummy and Healthy!", "scene": "Title page: Cat chef with tall hat surrounded by fruits and veggies"},
            {"text": "\"Welcome to my kitchen!\" said Chef Whiskers. \"Let's cook healthy and fun!\"", "scene": "Cat chef in colorful kitchen welcoming kids"},
            {"text": "\"First, wash your hands and paws! Clean cooking is happy cooking!\"", "scene": "Cat washing paws, demonstrating hygiene"},
            {"text": "\"Fruits are nature's candy!\" Whiskers made a rainbow fruit salad.", "scene": "Cat making colorful fruit salad"},
            {"text": "\"Vegetables give us power!\" He made funny veggie faces on plates.", "scene": "Cat arranging veggies into fun face on plate"},
            {"text": "\"Whole grains keep us running!\" They baked yummy wheat muffins.", "scene": "Cat and kids baking healthy muffins"},
            {"text": "\"Milk makes bones strong!\" Whiskers made a banana smoothie. DELICIOUS!", "scene": "Cat making smoothie, kids excited"},
            {"text": "\"The secret ingredient is always LOVE,\" Chef Whiskers purred.", "scene": "Cat adding heart-shaped ingredient"},
            {"text": "They had a feast! Everything was healthy AND tasty!", "scene": "Table full of colorful healthy food"},
            {"text": "\"Now YOU can be a chef! Cook with love and eat your colors!\"\n\nThe End", "scene": "Kids wearing chef hats, proud of their food"}
        ]
    },
    
    "The Haunted Treehouse": {
        "age_range": "6-8",
        "genre": "Mystery",
        "art_style": "cartoon",
        "style_prompt": "Spooky-fun cartoon children's book illustration, friendly haunted treehouse",
        "characters": {
            "main": "Brave Emma who discovers the \"ghost\" in her treehouse isn't scary at all"
        },
        "pages": [
            {"text": "The Haunted Treehouse\n\nA Not-So-Spooky Mystery", "scene": "Title page: Girl approaching treehouse with glowing windows"},
            {"text": "Everyone said Emma's new treehouse was haunted. Strange sounds came from it!", "scene": "Kids running away from treehouse, Emma curious"},
            {"text": "\"I'm not scared!\" said Emma. She climbed up with her flashlight.", "scene": "Emma climbing ladder bravely"},
            {"text": "Creak! The floor groaned. \"Who's there?\" Emma called.", "scene": "Emma inside dark treehouse, shining light"},
            {"text": "Something moved in the corner! Emma pointed her light...", "scene": "Dramatic moment, light pointing at corner"},
            {"text": "It was a family of raccoons! They had made the treehouse their home!", "scene": "Cute raccoon family revealed, looking startled"},
            {"text": "The \"spooky sounds\" were just babies playing at night!", "scene": "Baby raccoons tumbling and playing"},
            {"text": "\"You can stay,\" Emma smiled. She built them a special corner.", "scene": "Emma making cozy spot for raccoons"},
            {"text": "Now Emma and the raccoons share the treehouse! Best roommates ever!", "scene": "Emma and raccoons hanging out together"},
            {"text": "The \"haunted\" treehouse became the coolest clubhouse in town!\n\nThe End", "scene": "Kids visiting Emma's treehouse with raccoon friends"}
        ]
    },
    
    "Galaxy Racers": {
        "age_range": "6-8",
        "genre": "Science Fiction",
        "art_style": "cartoon",
        "style_prompt": "Dynamic space cartoon children's book illustration, spaceship racing theme",
        "characters": {
            "main": "Star, a young pilot who dreams of winning the Galaxy Grand Prix"
        },
        "pages": [
            {"text": "Galaxy Racers\n\nThe Ultimate Space Race", "scene": "Title page: Colorful spaceships racing through asteroid field"},
            {"text": "Star dreamed of being a Galaxy Racer - the fastest pilots in space!", "scene": "Young pilot looking at posters of famous racers"},
            {"text": "She built her own ship from scraps. It wasn't fancy, but it was FAST!", "scene": "Star working on homemade spaceship"},
            {"text": "Race day! Ships from every planet lined up. Star was nervous.", "scene": "Diverse ships at starting line, Star in her ship"},
            {"text": "The race went through asteroid belts, around moons, and through star gates!", "scene": "Exciting race through space obstacles"},
            {"text": "Star was behind! But she knew a shortcut through the Nebula Cloud!", "scene": "Star making risky decision toward nebula"},
            {"text": "The clouds were thick, but Star trusted her instincts.", "scene": "Star navigating through colorful nebula"},
            {"text": "She shot out of the nebula - in FIRST PLACE!", "scene": "Star emerging ahead of everyone"},
            {"text": "Crossing the finish line, the crowd went wild! Star had WON!", "scene": "Victory celebration, Star's ship crossing finish"},
            {"text": "\"Dream big, fly fast, never give up!\" Star told young fans.\n\nThe End", "scene": "Star with trophy, inspiring young pilots"}
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
                        estimated_cost += 0.025  # fal.ai is cheaper
                        print("OK")
                        return True
        print("FAILED")
        return False
    except Exception as e:
        error = str(e).lower()
        if "balance" in error or "budget" in error or "insufficient" in error:
            raise Exception("BUDGET_EXHAUSTED")
        print(f"FAILED - {str(e)[:60]}")
        return False


async def complete_single_book(book_id: str, title: str, template: dict, db):
    global estimated_cost
    
    print(f"\n{'='*60}")
    print(f"GENERATING: {title}")
    print(f"Style: {template['art_style']}, Age: {template['age_range']}")
    print(f"{'='*60}")
    
    safe_title = title.lower().replace("'", "").replace(" ", "_").replace(":", "").strip()
    output_dir = CONTENT_DIR / safe_title
    output_dir.mkdir(parents=True, exist_ok=True)
    
    public_dir = PUBLIC_DIR / safe_title
    public_dir.mkdir(parents=True, exist_ok=True)
    
    pages = []
    total = len(template["pages"])
    
    # Cover
    cover_path = output_dir / "cover.png"
    if not cover_path.exists():
        print(f"[Cover]", end=" ")
        cover_prompt = f"Children's book cover for '{title}'. {template['characters']['main']}. Title space at top."
        if await generate_book_image(cover_prompt, template["style_prompt"], cover_path):
            shutil.copy(cover_path, public_dir / "cover.png")
    else:
        print(f"[Cover] Exists")
    
    # Pages
    for i, page in enumerate(template["pages"]):
        page_path = output_dir / f"page_{i+1:02d}.png"
        
        if not page_path.exists():
            print(f"[Page {i+1}/{total}]", end=" ")
            scene_prompt = f"{page['scene']}. Character: {template['characters']['main']}"
            if await generate_book_image(scene_prompt, template["style_prompt"], page_path):
                shutil.copy(page_path, public_dir / f"page_{i+1:02d}.png")
        else:
            print(f"[Page {i+1}/{total}] Exists")
        
        pages.append({
            "page_number": i + 1,
            "text": page["text"],
            "image_url": f"/book-assets/{safe_title}/page_{i+1:02d}.png",
            "layout": "full_spread" if i == 0 else "text_left_image_right"
        })
        
        await asyncio.sleep(0.3)
    
    # Back cover
    back_path = output_dir / "back_cover.png"
    if not back_path.exists():
        print("[Back]", end=" ")
        back_prompt = f"Back cover for children's book. {template['characters']['main']} in peaceful scene."
        if await generate_book_image(back_prompt, template["style_prompt"], back_path):
            shutil.copy(back_path, public_dir / "back_cover.png")
    else:
        print("[Back] Exists")
    
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
    
    print(f"\n✓ Complete! Cost so far: ${estimated_cost:.2f}")
    return True


async def main():
    global estimated_cost
    
    print("="*60)
    print("BOOK GENERATION - BATCH 4")
    print("Using: fal.ai FLUX (cheaper!)")
    print("="*60)
    
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    # Get empty books with templates
    cursor = db.books.find({
        "$or": [{"pages": {"$exists": False}}, {"pages": []}]
    }, {"title": 1, "_id": 1})
    
    books_to_generate = []
    async for book in cursor:
        title = book.get("title")
        if title and title.strip() in BOOK_TEMPLATES:
            books_to_generate.append({
                "id": str(book["_id"]),
                "title": title.strip()
            })
    
    print(f"\nFound {len(books_to_generate)} books to generate:")
    for i, b in enumerate(books_to_generate):
        print(f"  {i+1}. {b['title']}")
    
    if not books_to_generate:
        print("\nNo matching books!")
        return
    
    # Generate
    print("\n--- GENERATING ---")
    
    completed = 0
    
    for book_info in books_to_generate:
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
                print(f"\n🚨 BUDGET EXHAUSTED")
                break
            print(f"Error: {e}")
    
    # Summary
    print("\n" + "="*60)
    print("BATCH COMPLETE")
    print("="*60)
    print(f"Books completed: {completed}")
    print(f"Images generated: {images_generated}")
    print(f"Est. cost: ${estimated_cost:.2f}")
    
    remaining = await db.books.count_documents({
        "$or": [{"pages": {"$exists": False}}, {"pages": []}]
    })
    print(f"Books still empty: {remaining}")


if __name__ == "__main__":
    asyncio.run(main())
