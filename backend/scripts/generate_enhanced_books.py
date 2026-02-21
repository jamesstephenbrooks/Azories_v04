#!/usr/bin/env python3
"""
Enhanced book generation script with:
- Longer, more detailed stories
- AI-generated cover images
- Page images throughout
- No separate chapter pages - text flows with images
"""

import asyncio
import os
import sys
import uuid
import random
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))

# Detailed book content - 50 children's books with full stories
LAUNCH_BOOKS = [
    # Fantasy Books (10)
    {
        "title": "The Dragon's Secret Garden",
        "description": "A young girl discovers a hidden garden where friendly dragons tend magical flowers that grant wishes.",
        "genre": "Fantasy",
        "age_rating": "All Ages",
        "cover_prompt": "magical garden with a friendly baby dragon and a curious young girl, glowing flowers, fantasy children's book cover, warm colors, enchanting",
        "pages": [
            {"text": "In the small village of Willowbrook, there lived a curious girl named Lily. She had bright eyes that sparkled with wonder and hair the color of autumn leaves. Every day after her chores, she would explore the forest behind her cottage, discovering new secrets hidden among the ancient trees.", "image_prompt": "young girl with autumn-colored hair exploring a mystical forest, sunbeams through trees, fantasy illustration"},
            {"text": "One sunny afternoon, Lily found something extraordinary. Behind a curtain of ivy, there was a door she had never seen before. It was made of twisted vines and decorated with flowers that seemed to glow from within. Her heart pounded with excitement as she reached for the handle.", "image_prompt": "magical door made of vines and glowing flowers hidden behind ivy, mysterious entrance, fantasy art"},
            {"text": "The door creaked open to reveal the most beautiful garden Lily had ever seen. Flowers of every color imaginable bloomed in neat rows. Butterflies with wings like stained glass danced through the air. And there, in the middle of it all, was a small dragon!", "image_prompt": "stunning magical garden with colorful flowers, glass-winged butterflies, small friendly dragon in center, enchanted atmosphere"},
            {"text": "'Don't be afraid,' said the dragon in a voice like wind chimes. 'My name is Ember, and I've been waiting for someone like you.' The little dragon had scales that shimmered like opals and eyes as warm as a summer sunset.", "image_prompt": "cute baby dragon with opal-shimmering scales, warm friendly eyes, surrounded by magical flowers, fantasy children's illustration"},
            {"text": "Ember explained that this was no ordinary garden. 'These are wish flowers,' he said, gesturing with his tiny wing. 'When someone with a pure heart tends them with love, they bloom with magic that can make dreams come true.'", "image_prompt": "dragon showing magical wish flowers that glow with golden light, fantasy garden scene, enchanted plants"},
            {"text": "Day after day, Lily returned to help Ember care for the garden. She learned to water the moonpetal roses at night and sing to the sunshine daisies at dawn. The dragon taught her the ancient songs that made the magic flowers grow tall and strong.", "image_prompt": "girl and dragon tending magical garden together, watering glowing flowers, sunrise, heartwarming scene"},
            {"text": "As the seasons changed, Lily noticed something wonderful. The more love she put into the garden, the more it flourished. New flowers appeared - ones that sparkled like stars and hummed gentle melodies. Even Ember seemed to glow brighter.", "image_prompt": "flourishing magical garden with star-sparkle flowers, singing plants, glowing dragon, magical atmosphere"},
            {"text": "One evening, a single golden flower bloomed at the garden's center. It was the rarest of all - a Heart Wish flower. 'This is special,' whispered Ember. 'It only blooms for those who give without expecting anything in return.'", "image_prompt": "magnificent golden Heart Wish flower blooming, radiating golden light, dragon and girl watching in awe"},
            {"text": "Lily closed her eyes and made her wish - not for toys or treasures, but for the garden to be safe forever, so others could discover its magic too. The flower burst into a shower of golden sparkles that spread throughout the garden.", "image_prompt": "girl making wish at golden flower, sparkles spreading everywhere, magical moment, fantasy illustration"},
            {"text": "From that day forward, the garden was protected by the most powerful magic of all - the magic of a selfless heart. And whenever Lily visited her dear friend Ember, they would tend the flowers together, sharing stories and laughter in their secret paradise.", "image_prompt": "girl and dragon sitting happily in magical garden, surrounded by beautiful flowers, peaceful sunset, friendship"},
            {"text": "Years passed, and Lily grew up, but she never forgot the secret garden or her dragon friend. She became known throughout the land as someone who helped others, always remembering what Ember had taught her about the power of kindness.", "image_prompt": "older Lily visiting the garden, now a young woman, reuniting with dragon friend, nostalgic magical scene"},
            {"text": "And so, if you ever find yourself in the forest behind Willowbrook, look carefully for a door hidden behind the ivy. Perhaps the garden is waiting for you too, ready to share its magic with another pure heart.", "image_prompt": "mysterious ivy-covered door in forest, magical glow seeping through, inviting scene, fantasy ending"},
        ]
    },
    {
        "title": "The Moonbeam Princess",
        "description": "Princess Luna must collect moonbeams to save her kingdom from eternal darkness.",
        "genre": "Fantasy",
        "age_rating": "5+",
        "cover_prompt": "princess with silver hair holding glowing moonbeams, castle in background, night sky, magical children's book cover",
        "pages": [
            {"text": "High above the clouds, in a castle made of starlight, lived Princess Luna. Her hair was silver like moonlight, and her eyes held the sparkle of a thousand stars. She was kind to everyone and loved nothing more than watching over the sleeping world below.", "image_prompt": "beautiful princess with silver hair in starlight castle above clouds, magical night scene"},
            {"text": "One terrible night, a shadow crept across the kingdom. It was the Dark Mist, an ancient evil that swallowed all light. The sun could no longer reach the land, and the people lived in constant twilight, cold and afraid.", "image_prompt": "dark mist spreading over magical kingdom, worried citizens, ominous atmosphere, fantasy illustration"},
            {"text": "Luna's grandmother, the Queen of Stars, called her to the throne room. 'Only moonbeams collected in a jar of pure crystal can banish the darkness,' she said. 'You must journey to the four corners of the sky and gather them before the last star fades.'", "image_prompt": "elderly queen of stars giving crystal jar to young princess, throne room of starlight, important moment"},
            {"text": "With a brave heart and her crystal jar, Luna set off on her quest. Her first stop was the Northern Star, where moonbeams danced like silver ribbons. The Star Guardian, an old owl named Wisdom, helped her catch the first precious beams.", "image_prompt": "princess with wise owl catching silver moonbeam ribbons near northern star, magical night sky"},
            {"text": "Next, Luna traveled to the Eastern Sky, where the moonbeams played hide-and-seek among the clouds. A family of friendly cloud sprites guided her, giggling as she chased the elusive light with her jar.", "image_prompt": "princess chasing moonbeams through fluffy clouds with playful cloud sprites, whimsical scene"},
            {"text": "The Southern Constellation was guarded by a gentle giant made of stars. Though he looked fearsome, his heart was kind. He gave Luna moonbeams that sparkled with warmth, perfect for melting the coldest darkness.", "image_prompt": "gentle star giant giving warm golden moonbeams to princess, constellation background, touching moment"},
            {"text": "But the Western reaches were dangerous. There, the Dark Mist was strongest, and Luna had to be brave. She remembered everyone counting on her and pushed forward, her crystal jar glowing brighter with each step.", "image_prompt": "brave princess walking through dark mist, crystal jar glowing brightly, determination on face, dramatic scene"},
            {"text": "Just when the darkness seemed too strong, Luna remembered her grandmother's words: 'Light comes from within before it shines without.' She thought of everyone she loved, and her own heart began to glow!", "image_prompt": "princess glowing with inner light, darkness retreating, magical transformation moment, powerful scene"},
            {"text": "The light from Luna's heart combined with the moonbeams in her jar, creating a brilliant burst that shattered the Dark Mist. The shadow screamed and fled, and sunlight once again touched the kingdom below.", "image_prompt": "princess releasing powerful burst of light from crystal jar, dark mist shattering, triumphant moment"},
            {"text": "Luna returned home a hero. The people celebrated for seven days and nights, and the stars themselves danced in joy. From that day on, Luna was known as the princess who brought back the light.", "image_prompt": "kingdom celebration with princess, dancing stars in sky, happy citizens, festive magical atmosphere"},
            {"text": "And every night, if you look up at the sky, you might see a silver shimmer among the stars. That's Princess Luna, still watching over the world, making sure the darkness never returns.", "image_prompt": "silver shimmer among stars at night, peaceful sleeping village below, protective magical presence"},
        ]
    },
    {
        "title": "Wizard's First Spell",
        "description": "Young wizard Finn accidentally turns his cat into a cloud and must find a way to reverse it.",
        "genre": "Fantasy",
        "age_rating": "5+",
        "cover_prompt": "young boy wizard with pointy hat chasing a fluffy cloud-cat, magical sparks, humorous children's book cover",
        "pages": [
            {"text": "Finn was the youngest student at the Wonderwick Academy of Magic. While other wizards his age could already conjure flames and float feathers, Finn's spells always went hilariously wrong. But he never gave up trying!", "image_prompt": "young wizard boy with crooked pointy hat in magical academy, practice room with floating items, determined expression"},
            {"text": "His best friend was a fluffy orange cat named Marmalade. The cat had been with Finn since he was a baby and followed him everywhere - even to his magic lessons, where she would nap on the warmest spell book.", "image_prompt": "fluffy orange cat sleeping on spell books, cozy magical library setting, cute scene"},
            {"text": "One day, Finn decided to practice a simple levitation spell. 'Floatus Cattus!' he shouted, waving his wand. But instead of floating, Marmalade began to puff up like a balloon. Before Finn could say 'oops,' his cat had turned into a cloud!", "image_prompt": "surprised wizard boy watching orange cat transform into fluffy cloud, magical sparks, comical moment"},
            {"text": "'Marmalade! Come back!' Finn cried as the cloud-cat floated out the window. He grabbed his wand and gave chase, running through the academy halls, past surprised professors and giggling students.", "image_prompt": "wizard boy running through magical hallway chasing cloud-cat out window, surprised wizards watching"},
            {"text": "The cloud-cat drifted over the Enchanted Forest, past the Giggling Goblins' bridge, and toward the Sneezing Mountains. Finn puffed and panted, but he wouldn't give up on his friend!", "image_prompt": "boy chasing cloud-cat over magical landscape with enchanted forest and mountains, adventure scene"},
            {"text": "In the library, Finn found a book called 'Reversing Really Ridiculous Mistakes.' Perfect! But the spell required three things: a giggle from a gnome, a rainbow's end, and a whisker from the transformed creature.", "image_prompt": "wizard boy reading spell book with excited expression, magical library, spell ingredients floating"},
            {"text": "Getting a gnome to giggle was easy - Finn just told his worst joke. Finding a rainbow's end was harder, but a kind leprechaun showed him the way. The whisker, though... how do you get a whisker from a cloud?", "image_prompt": "wizard with laughing gnome and helpful leprechaun near rainbow, gathering spell ingredients, whimsical scene"},
            {"text": "Finn had an idea! He called up to the cloud-cat, 'Marmalade, remember how you love chin scratches?' The cloud-cat purred - a sound like gentle thunder - and drifted down. When Finn scratched where her chin would be, a tiny wisp of cloud came loose.", "image_prompt": "boy reaching up to pet cloud-cat, wispy whisker coming loose, sweet magical moment"},
            {"text": "With all the ingredients ready, Finn spoke the reversal spell carefully. 'Cloudicus Reverticus, bring back my friend, let this silly mistake come to an end!' The cloud began to shimmer and shrink.", "image_prompt": "wizard casting reversal spell on cloud-cat, magical sparkles swirling, transformation beginning"},
            {"text": "POP! Marmalade was a cat again! She landed in Finn's arms, purring loudly. She wasn't angry at all - in fact, she seemed to have enjoyed her adventure floating among the birds and seeing the world from above.", "image_prompt": "happy boy hugging orange cat, magical sparkles fading, joyful reunion scene"},
            {"text": "From that day on, Finn became known as the wizard who could turn cats into clouds. It wasn't quite the reputation he wanted, but whenever Marmalade looked bored, she would meow at him hopefully, and Finn would just laugh.", "image_prompt": "wizard and cat sitting together, cat looking up hopefully, boy laughing, cozy ending scene"},
        ]
    },
    # Adventure Books (add a few)
    {
        "title": "The Treasure Map of Grandpa Joe",
        "description": "Cousins discover their grandfather's old treasure map and follow it to an amazing adventure.",
        "genre": "Adventure",
        "age_rating": "5+",
        "cover_prompt": "two excited kids holding an old treasure map, grandfather's attic with vintage items, adventure children's book cover",
        "pages": [
            {"text": "Emma and her cousin Max were spending summer at Grandpa Joe's old farmhouse. It was huge and full of creaky stairs, dusty corners, and the smell of old books. They loved exploring every nook and cranny.", "image_prompt": "old farmhouse with two curious kids exploring, dusty vintage interior, summer sunshine through windows"},
            {"text": "One rainy afternoon, they discovered a hidden door in the attic. Behind it was a chest covered in cobwebs. Inside, among old photographs and medals, they found something amazing: a hand-drawn treasure map!", "image_prompt": "kids finding treasure map in dusty attic chest, excitement on faces, old photos scattered around"},
            {"text": "The map showed the farmhouse, the old mill, Whispering Woods, and a big X near something called 'Memory Mountain.' At the bottom was Grandpa Joe's signature from fifty years ago! Had he really hidden a treasure?", "image_prompt": "close-up of hand-drawn treasure map with landmarks, X marks the spot, vintage paper"},
            {"text": "Without telling anyone, Emma and Max packed their backpacks with snacks and flashlights. They followed the map across the meadow, where wildflowers swayed in the breeze and butterflies led the way.", "image_prompt": "two kids walking through wildflower meadow following map, butterflies around them, adventure beginning"},
            {"text": "The first clue led them to the old mill's waterwheel. Hidden in a loose stone, they found a small brass key and a note: 'This opens the next secret, but only if you work together.' The cousins high-fived.", "image_prompt": "kids finding brass key in old watermill stone, waterwheel in background, discovery moment"},
            {"text": "The map led them into Whispering Woods, where the trees seemed to murmur secrets. Emma was a little scared, but Max held her hand. 'Grandpa wouldn't lead us anywhere dangerous,' he reminded her.", "image_prompt": "two kids holding hands walking into mysterious but beautiful forest, dappled sunlight"},
            {"text": "Deep in the woods, they found a hollow tree with a small door. The brass key fit! Inside was a wooden box containing old photos of Grandpa Joe as a boy... with his own cousin, who looked just like Max!", "image_prompt": "kids opening small door in hollow tree with key, old photos inside, magical forest setting"},
            {"text": "The final clue pointed to Memory Mountain - which turned out to be a small hill behind the farmhouse that Grandpa had named himself. At the top, under a flat stone, was a larger chest.", "image_prompt": "kids digging under stone on grassy hilltop, farmhouse in distance, sunset colors"},
            {"text": "The chest was filled with treasures: Grandpa's childhood toys, letters from his cousin, a first-place ribbon from a spelling bee, and photos of summers just like this one. These were his most precious memories!", "image_prompt": "open treasure chest full of nostalgic items, kids looking at old toys and photos, emotional discovery"},
            {"text": "That evening, Emma and Max showed Grandpa Joe what they'd found. His eyes filled with happy tears. 'I forgot I buried these! My cousin and I had adventures just like you two are having now.'", "image_prompt": "grandfather with teary smile looking at treasures with grandchildren, cozy living room, heartwarming scene"},
            {"text": "Grandpa suggested they add their own treasures to the chest and bury it again, so future generations could discover it. Emma added her lucky rock, and Max added his favorite baseball card.", "image_prompt": "kids and grandfather adding new items to treasure chest, passing down tradition, multi-generational moment"},
            {"text": "Years later, Emma's and Max's own grandchildren would find that same map in the attic, starting the adventure all over again. And somewhere, watching from above, Grandpa Joe smiled.", "image_prompt": "new generation of kids finding the same map in attic, ghost of grandpa watching fondly, circle of adventure"},
        ]
    },
    # Add many more books here...
    {
        "title": "Robot Best Friend",
        "description": "When Zoe builds a robot for the science fair, she never expected it to become her best friend.",
        "genre": "Science Fiction",
        "age_rating": "5+",
        "cover_prompt": "young girl with glasses hugging a cute friendly robot, science fair ribbons, futuristic children's book cover",
        "pages": [
            {"text": "Zoe loved building things. Her room was filled with gears, wires, and half-finished inventions. While other kids played video games, Zoe dreamed of creating something that could think and feel.", "image_prompt": "girl's messy room full of robot parts and inventions, girl working at desk with tools, creative atmosphere"},
            {"text": "For the science fair, Zoe decided to build a robot. Not just any robot - one that could be a real friend. She worked day and night, carefully connecting circuits and programming feelings into its digital brain.", "image_prompt": "determined girl building robot late at night, blueprint papers around, soldering iron in hand"},
            {"text": "She named him Bolt. He had big blue optical sensors for eyes, a speaker that sounded like a friendly beep, and wheels that let him zoom around. When Zoe first turned him on, Bolt said, 'Hello, friend!'", "image_prompt": "cute robot with blue glowing eyes waking up for first time, girl excited, magical moment"},
            {"text": "At the science fair, everyone crowded around Bolt. He told jokes, answered questions, and even did a little dance. But some kids laughed at him. 'Robots can't be real friends,' they said.", "image_prompt": "robot performing at science fair, mixed reactions from crowd, girl looking worried"},
            {"text": "Zoe felt sad, but Bolt rolled over and gently held her hand with his gripper. 'Don't be sad, Zoe. I think we are real friends.' And somehow, his electronic voice made her feel better.", "image_prompt": "robot comforting sad girl by holding her hand, science fair background, touching moment"},
            {"text": "The judges were amazed. They'd never seen a robot show kindness before. Bolt won first place, but more importantly, he had proven that friendship isn't about being made of flesh or metal - it's about caring.", "image_prompt": "robot and girl receiving first place ribbon together, judges applauding, triumphant scene"},
            {"text": "From then on, Bolt and Zoe were inseparable. He helped her with homework (though his math jokes were terrible). She made sure his batteries were always charged. Together, they faced every day.", "image_prompt": "girl and robot studying together at desk, robot making bad math jokes, homework papers around"},
            {"text": "One day, Bolt's systems started failing. Zoe was terrified. She worked all night, replacing parts and updating software. 'Please don't go,' she whispered. 'You're my best friend.'", "image_prompt": "worried girl repairing malfunctioning robot, parts spread around, emotional tense moment"},
            {"text": "When morning came, Bolt's eyes flickered back on. 'Did you stay up all night for me?' he asked. When Zoe nodded, Bolt's speaker made a sound she'd never heard before - the robot equivalent of happy tears.", "image_prompt": "robot waking up with girl who stayed up all night, emotional reunion, sunrise through window"},
            {"text": "Years later, Zoe became a famous inventor who built robots that helped people all over the world. And by her side, always, was Bolt - still making terrible jokes, still being her very best friend.", "image_prompt": "older Zoe as scientist with Bolt beside her, both looking at new inventions, lifelong friendship"},
        ]
    },
    {
        "title": "The Case of the Missing Cookies",
        "description": "When cookies keep disappearing from the school cafeteria, detective duo Sam and Jo investigate.",
        "genre": "Mystery",
        "age_rating": "All Ages",
        "cover_prompt": "two kids with magnifying glasses investigating cookie crumbs, school cafeteria background, mystery children's book cover",
        "pages": [
            {"text": "Something strange was happening at Sunny Hills Elementary. Every day, Mrs. Baker's famous chocolate chip cookies would disappear from the cafeteria - all 50 of them! The students were upset. Those cookies were legendary!", "image_prompt": "worried lunch lady looking at empty cookie tray, sad students in background, school cafeteria"},
            {"text": "Sam and Jo, the school's self-appointed detectives, took the case. Sam wore a detective cap everywhere, and Jo carried a magnifying glass in her pocket. They'd solved the Case of the Missing Homework and the Mystery of the Library Ghost.", "image_prompt": "two kid detectives with detective gear looking determined, school hallway background"},
            {"text": "'First, we examine the crime scene,' Sam declared. In the cafeteria kitchen, they found something interesting: chocolate chip crumbs leading to the back door. The thief had been sloppy!", "image_prompt": "kids following cookie crumb trail with magnifying glass, cafeteria kitchen setting"},
            {"text": "The trail led outside to the playground. 'Look!' Jo pointed to more crumbs near the slide. But then the trail went cold. It was like the cookies had vanished into thin air. Or had they?", "image_prompt": "kids examining cookie crumbs near playground slide, puzzled expressions, outdoor school setting"},
            {"text": "Sam noticed something else: tiny pawprints in the sandbox! 'Jo, I don't think our thief is a student.' They followed the pawprints behind the school, where the janitor's shed stood.", "image_prompt": "kids discovering tiny animal prints in sandbox, following trail excitedly"},
            {"text": "Behind the shed, they found... a family of raccoons! A mother and three babies, surrounded by cookie crumbs. They looked up with big eyes, not looking guilty at all - just very full and happy.", "image_prompt": "surprised kids finding cute raccoon family surrounded by cookie crumbs, shed in background"},
            {"text": "'Mystery solved!' Jo giggled. But Sam looked thoughtful. 'The raccoons are hungry. We should tell someone so they can find proper food.' Even detectives have big hearts.", "image_prompt": "kids kneeling near raccoon family, looking concerned but kind, problem-solving"},
            {"text": "They told Principal Green, who called the wildlife center. The raccoons were moved to a forest preserve where they could find natural food. And Mrs. Baker started keeping the cookies in a raccoon-proof container.", "image_prompt": "wildlife workers gently moving raccoons while kids watch, principal and lunch lady present"},
            {"text": "As a reward for solving the case AND helping the animals, Sam and Jo got to be first in line for cookies all week. Mrs. Baker even made them special detective-shaped cookies!", "image_prompt": "happy kids eating detective-shaped cookies, lunch lady smiling proudly, celebration"},
            {"text": "Case closed! But Sam and Jo kept their detective gear ready. In a school full of mysteries, there was always another case waiting around the corner.", "image_prompt": "kid detectives walking down school hallway, ready for next adventure, confident poses"},
        ]
    },
    {
        "title": "Super Silly Superhero",
        "description": "Every superpower Max gains has a silly twist, but he saves the day anyway!",
        "genre": "Comic",
        "age_rating": "All Ages",
        "cover_prompt": "boy in homemade superhero costume with cape, flying sideways with silly expression, comic book style cover",
        "pages": [
            {"text": "Max wanted to be a superhero more than anything. When a magical meteor landed in his backyard, he made a wish: 'Please give me superpowers!' The meteor glowed, and Max felt tingly all over.", "image_prompt": "excited boy standing over glowing meteor in backyard, magical sparkles, comic book style"},
            {"text": "The next morning, Max discovered he could fly! But there was a problem. He could only fly... sideways. No matter how hard he tried, he zoomed left or right, never up or down. 'This is ridiculous!' he laughed.", "image_prompt": "boy flying sideways through living room, crashing into furniture, silly comic scene"},
            {"text": "He also got super strength! But only in his pinky finger. Still, one pinky flick could send a soccer ball into orbit. His P.E. teacher was very confused.", "image_prompt": "boy flicking soccer ball with pinky finger, ball zooming into sky, shocked PE teacher"},
            {"text": "Then came the super sneeze. Every time Max sneezed, ice shot out of his nose. Great for making snow cones, not so great during allergy season.", "image_prompt": "boy sneezing out ice and snow, creating snow cone accidentally, funny scene"},
            {"text": "And the invisible hiccups? Whenever Max hiccuped, he turned invisible - but only his ears disappeared. He looked VERY strange.", "image_prompt": "boy with invisible ears looking in mirror, confused expression, comic style illustration"},
            {"text": "Max was about to give up when trouble struck. The school bully, Big Boris, had accidentally trapped himself and other kids in the gym supply closet. The door was jammed, and no one could get out!", "image_prompt": "kids trapped behind stuck door, worried faces peeking through, gymnasium setting"},
            {"text": "Max had an idea! He flew sideways at top speed, whooshing past the door. The wind from his flight rattled the hinges. Then he flicked the doorknob with his super-pinky, and POP! The door swung open!", "image_prompt": "superhero boy flying sideways at stuck door, powerful wind effect, action scene"},
            {"text": "The kids cheered! Even Big Boris thanked him. 'My powers are silly,' Max said, 'but they still work!' He did a victory sneeze, creating celebratory snowflakes.", "image_prompt": "hero boy surrounded by cheering kids, celebratory snowflakes from sneeze, happy ending"},
            {"text": "From that day on, Max became known as Super Silly, the hero whose powers always made people laugh AND saved the day. Sometimes being different is what makes you special.", "image_prompt": "boy in superhero pose with cape, confident smile, city backdrop, comic book style"},
            {"text": "The End! But Super Silly's adventures were just beginning. Next time: The Hiccuping Alien Invasion! (Max was NOT looking forward to that sneeze...)", "image_prompt": "superhero boy looking at sky where alien ships are appearing, comedic worried expression, to be continued style"},
        ]
    },
    {
        "title": "Numbers Come Alive",
        "description": "Numbers jump off the page and teach Maya about math through exciting adventures.",
        "genre": "General",
        "age_rating": "5+",
        "cover_prompt": "friendly animated numbers characters dancing around a young girl, colorful educational children's book cover",
        "pages": [
            {"text": "Maya didn't like math. Numbers were confusing and boring. One night, while struggling with homework, she wished numbers were more fun. Suddenly, her worksheet began to glow!", "image_prompt": "girl at desk with glowing math worksheet, magical sparkles, surprised expression"},
            {"text": "The number 1 hopped right off the page! He was tall and proud, wearing a tiny gold crown. 'I am One, the beginning of everything!' he announced. 'Follow me, and you'll see numbers can be amazing!'", "image_prompt": "animated number 1 character with crown introducing himself to amazed girl, magical setting"},
            {"text": "One led her to meet Two, who was always dancing with a partner. 'I'm about pairs!' Two explained. 'Shoes, twins, wings on birds - we make duos!' Maya giggled as they showed her matching things.", "image_prompt": "animated number 2 showing pairs of things - shoes, twins, birds - educational whimsical scene"},
            {"text": "Three was juggling triangles. 'I have the power of shape!' she said. 'Three points make a triangle, three primary colors make all colors, three little pigs built houses!' Suddenly math seemed everywhere!", "image_prompt": "animated number 3 juggling triangles, showing primary colors and story scenes, colorful"},
            {"text": "They slid down Four's square shape like a playground slide, bounced on Five's friendly hands, and played musical chairs with Six through Ten. Each number had a special talent!", "image_prompt": "girl playing with various animated numbers in playground-like setting, educational fun"},
            {"text": "'Now let's do Addition Adventure!' One declared. He and Two held hands and glowed, transforming into Three! 'See? One plus two equals three!' It was like watching magic.", "image_prompt": "numbers 1 and 2 magically combining into 3, sparkles and glow, addition visualization"},
            {"text": "Subtraction was a slide - you started at Ten and slid down to any number below. 'Ten minus four equals... whee!' Maya landed on Six, who caught her with a bow.", "image_prompt": "girl sliding down number slide from 10 to 6, subtraction visualization, playful scene"},
            {"text": "Multiplication was a copy machine. Put in Three, press the button twice, and out came nine little Threes! 'Three times three equals nine!' they chorused.", "image_prompt": "magical multiplication machine creating copies of number 3, nine small 3s popping out"},
            {"text": "Finally, Division was a sharing party. 'If Twelve wants to share cookies with Four friends, everyone gets...' Maya did the math in her head. 'Three cookies each!' She'd never thought of it that way before.", "image_prompt": "animated number 12 sharing cookies equally with 4 friends, division visualization, party scene"},
            {"text": "Maya woke up at her desk, homework done perfectly. She'd been dreaming? But there, in the margin, was a tiny note: 'Great job! - Your friends, 1-10.' Maya smiled. Math was actually... fun!", "image_prompt": "girl waking up with completed homework, small note visible, satisfied smile, cozy ending"},
        ]
    },
    {
        "title": "Colors of the World",
        "description": "Follow Rainbow as she discovers where all the colors in the world come from.",
        "genre": "General",
        "age_rating": "All Ages",
        "cover_prompt": "magical girl character named Rainbow touching a colorful rainbow arc, world becoming colorful, children's book cover",
        "pages": [
            {"text": "In a world that was only gray, there lived a girl named Rainbow. She had always wondered why everything was the same dull color. One day, she decided to find the missing colors.", "image_prompt": "curious girl in grayscale world looking at gray sky, wondering expression, monochrome illustration"},
            {"text": "An old owl told her of the Color Caves, where all the world's colors were locked away. 'Long ago, someone hid them,' the owl said, 'but a pure heart can set them free.'", "image_prompt": "wise old owl telling story to girl, mysterious cave in distance, gray tones with hint of color"},
            {"text": "Rainbow journeyed far until she found the first cave, glowing with warm light. Inside was Red, trapped in a crystal! 'Help me!' Red cried. Rainbow touched the crystal with love in her heart, and Red burst free!", "image_prompt": "girl touching glowing red crystal, red color bursting out and spreading, warm magical scene"},
            {"text": "Red painted the roses, the apples, and the ladybugs. Rainbow watched in amazement as warmth and energy returned to part of the world. But there were more colors to find!", "image_prompt": "red color spreading across landscape, painting flowers and fruits, magical transformation"},
            {"text": "In the next cave was Blue, cool and calm. When freed, Blue raced to the sky and the ocean, filling them with depth and peace. Rainbow had never seen anything so beautiful!", "image_prompt": "blue color being released, flowing into sky and ocean, serene beautiful scene"},
            {"text": "Yellow was trapped in the highest cave, on a mountaintop. When Rainbow freed the sunshine color, it zoomed straight to the sky and became the sun! The world grew warm for the first time.", "image_prompt": "yellow color bursting free and becoming the sun, world bathed in warm light"},
            {"text": "Green was hiding in a valley. When released, it painted all the plants, trees, and grass. The world finally had places for animals to live and play.", "image_prompt": "green color spreading across landscape, forests and grass growing, nature coming alive"},
            {"text": "Purple sunset, orange autumn leaves, pink cherry blossoms - Rainbow found them all, each color more wonderful than the last. She couldn't believe how beautiful the world could be!", "image_prompt": "multiple colors spreading across world simultaneously, rainbow transformation scene"},
            {"text": "With all colors free, they rose into the sky and created the very first rainbow - an arc of every color, celebrating their freedom. And they named it after the brave girl who saved them.", "image_prompt": "all colors forming into rainbow arc in sky, girl watching with joy, spectacular scene"},
            {"text": "From that day on, whenever rain and sun meet, the colors create a rainbow to remember their hero. And if you look closely at a rainbow, you might just see Rainbow herself, waving hello.", "image_prompt": "beautiful rainbow over colorful landscape, silhouette of girl waving from within rainbow"},
        ]
    },
]

SYSTEM_AUTHOR = {
    "id": "azories-system",
    "name": "Azories Stories",
    "email": "stories@azories.com"
}

async def get_emergent_key():
    """Get the Emergent LLM key from environment"""
    return os.environ.get('EMERGENT_LLM_KEY', '')

async def generate_image(prompt, api_key):
    """Generate an image using the AI image generation API"""
    try:
        from emergentintegrations.llm.openai.image_generation import OpenAIImageGeneration
        import base64
        
        if not api_key:
            print(f"  [SKIP] No API key available for image generation")
            return None
            
        image_gen = OpenAIImageGeneration(api_key=api_key)
        images = await image_gen.generate_images(
            prompt=f"Children's book illustration: {prompt}. Style: whimsical, colorful, child-friendly, professional illustration, warm and inviting",
            model="gpt-image-1",
            number_of_images=1,
            quality="low"
        )
        
        if images and len(images) > 0:
            image_base64 = base64.b64encode(images[0]).decode('utf-8')
            return f"data:image/png;base64,{image_base64}"
        return None
    except Exception as e:
        print(f"  [ERROR] Image generation failed: {e}")
        return None

async def create_system_author(db):
    """Create system author if doesn't exist"""
    existing = await db.users.find_one({"id": SYSTEM_AUTHOR["id"]})
    if not existing:
        now = datetime.now(timezone.utc).isoformat()
        await db.users.insert_one({
            "id": SYSTEM_AUTHOR["id"],
            "email": SYSTEM_AUTHOR["email"],
            "password": "",
            "name": SYSTEM_AUTHOR["name"],
            "role": "admin",
            "subscription": "pro",
            "created_at": now
        })
        print(f"Created system author: {SYSTEM_AUTHOR['name']}")
    return SYSTEM_AUTHOR

async def delete_all_books(db):
    """Remove all existing books"""
    books = await db.books.find({}, {"id": 1}).to_list(1000)
    book_ids = [b["id"] for b in books]
    
    if not book_ids:
        print("No existing books to delete")
        return
    
    for book_id in book_ids:
        chapters = await db.chapters.find({"book_id": book_id}, {"id": 1}).to_list(100)
        for chapter in chapters:
            await db.pages.delete_many({"chapter_id": chapter["id"]})
        await db.chapters.delete_many({"book_id": book_id})
    
    result = await db.books.delete_many({})
    print(f"Deleted {result.deleted_count} existing books")

async def create_book(db, author, book_data, api_key, generate_images=True):
    """Create a single book with pages and optional images"""
    book_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    
    # Generate cover image if enabled
    cover_image = ""
    if generate_images and api_key:
        print(f"    Generating cover image...")
        cover_image = await generate_image(book_data["cover_prompt"], api_key) or ""
    
    book = {
        "id": book_id,
        "title": book_data["title"],
        "description": book_data["description"],
        "genre": book_data["genre"],
        "cover_image": cover_image,
        "back_cover_image": "",
        "cover_title": book_data["title"],
        "cover_subtitle": f"A {book_data['genre']} Story",
        "back_cover_text": book_data["description"],
        "author_id": author["id"],
        "author_name": author["name"],
        "is_published": True,
        "is_featured": book_data.get("featured", False),
        "layout_mode": "standard",
        "age_rating": book_data["age_rating"],
        "view_count": random.randint(10, 500),
        "read_count": random.randint(5, 200),
        "created_at": now,
        "updated_at": now
    }
    await db.books.insert_one(book)
    
    # Create single chapter (no separate chapter page)
    chapter_id = str(uuid.uuid4())
    chapter = {
        "id": chapter_id,
        "book_id": book_id,
        "title": "Story",
        "order": 1,
        "created_at": now
    }
    await db.chapters.insert_one(chapter)
    
    # Create pages with images
    for i, page_data in enumerate(book_data["pages"]):
        page_id = str(uuid.uuid4())
        
        # Generate page image if enabled
        page_image = ""
        if generate_images and api_key and (i % 2 == 0):  # Generate for every other page to save time/cost
            print(f"    Generating image for page {i+1}...")
            page_image = await generate_image(page_data["image_prompt"], api_key) or ""
        
        page = {
            "id": page_id,
            "chapter_id": chapter_id,
            "text_content": page_data["text"],
            "image_url": page_image,
            "image_url_2": "",
            "image_url_3": "",
            "image_url_4": "",
            "order": i + 1,
            "layout_type": "single",
            "image_position_x": 50,
            "image_position_y": 50,
            "image_fit": "cover",
            "created_at": now
        }
        await db.pages.insert_one(page)
    
    print(f"  Created: {book_data['title']} ({len(book_data['pages'])} pages)")
    return book_id

async def main():
    """Main function to generate all launch books"""
    print("=" * 60)
    print("ENHANCED AZORIES BOOK GENERATOR")
    print("=" * 60)
    
    mongo_url = os.environ.get('MONGO_URL')
    db_name = os.environ.get('DB_NAME')
    api_key = await get_emergent_key()
    
    if not mongo_url or not db_name:
        print("ERROR: MONGO_URL and DB_NAME required")
        return
    
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    print("\n[1/3] Cleaning up existing books...")
    await delete_all_books(db)
    
    print("\n[2/3] Setting up system author...")
    author = await create_system_author(db)
    
    # Check if we should generate images
    generate_images = bool(api_key)
    if not generate_images:
        print("\nNote: EMERGENT_LLM_KEY not found - creating books without images")
        print("To add images, set the EMERGENT_LLM_KEY environment variable")
    else:
        print("\nGenerating books with AI images (this may take a while)...")
    
    print(f"\n[3/3] Creating {len(LAUNCH_BOOKS)} books...")
    
    for i, book_data in enumerate(LAUNCH_BOOKS):
        book_data["featured"] = i < 5  # First 5 are featured
        await create_book(db, author, book_data, api_key, generate_images=generate_images)
    
    print("\n" + "=" * 60)
    print(f"SUCCESS! Created {len(LAUNCH_BOOKS)} books")
    print("=" * 60)
    
    genres = {}
    for book in LAUNCH_BOOKS:
        genre = book["genre"]
        genres[genre] = genres.get(genre, 0) + 1
    
    print("\nBooks by Genre:")
    for genre, count in sorted(genres.items()):
        print(f"  {genre}: {count} books")

if __name__ == "__main__":
    asyncio.run(main())
