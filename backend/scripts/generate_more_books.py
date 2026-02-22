#!/usr/bin/env python3
"""
Generate 45 more books (total 50) with detailed stories.
Cover images will be generated in a separate pass.
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

# 45 more books across all genres
MORE_BOOKS = [
    # Fantasy (9 more = 12 total)
    {
        "title": "The Moonbeam Princess",
        "description": "Princess Luna must collect moonbeams to save her kingdom from eternal darkness.",
        "genre": "Fantasy",
        "age_rating": "5+",
        "cover_prompt": "princess with silver hair holding glowing moonbeams, starlit castle, night sky, magical children's book cover",
        "pages": [
            "High above the clouds, in a castle made of starlight, lived Princess Luna. Her hair was silver like moonlight, and her eyes held the sparkle of a thousand stars.",
            "One terrible night, a shadow crept across the kingdom. It was the Dark Mist, an ancient evil that swallowed all light.",
            "Luna's grandmother, the Queen of Stars, called her to the throne room. 'Only moonbeams collected in a jar of pure crystal can banish the darkness,' she said.",
            "With a brave heart and her crystal jar, Luna set off on her quest. Her first stop was the Northern Star.",
            "The Star Guardian, an old owl named Wisdom, helped her catch the first precious moonbeams that danced like silver ribbons.",
            "Next, Luna traveled to the Eastern Sky, where the moonbeams played hide-and-seek among the clouds.",
            "A family of friendly cloud sprites guided her, giggling as she chased the elusive light with her jar.",
            "The Southern Constellation was guarded by a gentle giant made of stars who gave Luna warm moonbeams.",
            "Just when the darkness seemed too strong, Luna remembered: 'Light comes from within before it shines without.'",
            "The light from Luna's heart combined with the moonbeams, creating a brilliant burst that shattered the Dark Mist!",
            "Luna returned home a hero. The people celebrated for seven days and nights, and the stars danced in joy. THE END"
        ]
    },
    {
        "title": "Wizard's First Spell",
        "description": "Young wizard Finn accidentally turns his cat into a cloud and must find a way to reverse it.",
        "genre": "Fantasy",
        "age_rating": "5+",
        "cover_prompt": "young boy wizard chasing a fluffy cloud-cat, magical sparks, humorous children's book cover",
        "pages": [
            "Finn was the youngest student at the Wonderwick Academy of Magic. His spells always went hilariously wrong.",
            "His best friend was a fluffy orange cat named Marmalade who followed him everywhere.",
            "One day, Finn tried a levitation spell. 'Floatus Cattus!' But instead of floating, Marmalade turned into a cloud!",
            "'Marmalade! Come back!' Finn cried as the cloud-cat floated out the window.",
            "In the library, Finn found 'Reversing Really Ridiculous Mistakes.' The spell required three things.",
            "Getting a gnome to giggle was easy - Finn just told his worst joke. The rainbow's end was harder.",
            "A kind leprechaun showed him the way. But how do you get a whisker from a cloud?",
            "Finn called up to the cloud-cat, 'Remember how you love chin scratches?' The cloud purred like gentle thunder.",
            "When Finn scratched where her chin would be, a tiny wisp of cloud came loose - the whisker!",
            "With all ingredients ready, Finn spoke the reversal spell carefully. The cloud began to shimmer!",
            "POP! Marmalade was a cat again! She purred loudly. She'd enjoyed floating among the birds! THE END"
        ]
    },
    {
        "title": "The Fairy's Lost Wings",
        "description": "A fairy loses her wings in a storm and discovers true friendship on her journey home.",
        "genre": "Fantasy",
        "age_rating": "All Ages",
        "cover_prompt": "small fairy without wings walking with a helpful mouse through magical forest, heartwarming children's book",
        "pages": [
            "Rosie was the smallest fairy in Dewdrop Glen, but she had the biggest, most beautiful wings.",
            "One stormy night, a powerful gust swept her wings away into the darkness.",
            "Without wings, Rosie couldn't fly home. She sat crying under a mushroom when a tiny mouse appeared.",
            "'I'm Morris,' said the mouse. 'I can't fly either, but I know these woods. Let me help you.'",
            "Together they journeyed through the Whispering Woods, past the Giggling Stream, and over Pebble Mountain.",
            "Along the way, they met a ladybug who shared her lunch and a helpful squirrel who showed them shortcuts.",
            "Morris protected Rosie from a hungry crow, and Rosie used her magic to heal Morris's hurt paw.",
            "When they finally reached Dewdrop Glen, the fairy queen was waiting with a surprise.",
            "'Your old wings were blown here by the storm,' she said. 'But more importantly, you brought home something better.'",
            "'What?' asked Rosie. 'A true friend,' smiled the queen, looking at Morris.",
            "Rosie's wings were restored, but she often walked instead - so Morris could keep up. THE END"
        ]
    },
    {
        "title": "The Kingdom of Talking Animals",
        "description": "A boy discovers he can understand animals and helps solve a mystery in the animal kingdom.",
        "genre": "Fantasy",
        "age_rating": "5+",
        "cover_prompt": "young boy surrounded by various talking animals including owl, squirrel, deer in magical forest, fantasy children's book",
        "pages": [
            "Tom always felt different from other kids. He spent hours in the forest, and animals never ran from him.",
            "One morning, a wise owl landed beside him and said, 'Finally! We've been waiting for a Listener.'",
            "Tom gasped - he could understand every word! The owl explained that Listeners were rare humans who could hear animal speech.",
            "The animal kingdom needed help. Their beloved Golden Acorn, symbol of peace, had been stolen!",
            "Tom agreed to investigate. He interviewed squirrels, questioned deer, and listened to the gossip of sparrows.",
            "The clues pointed to Shadow Cave, where a family of foxes lived. But foxes weren't thieves!",
            "Tom spoke to the fox family and learned the truth - a confused magpie had taken the shiny acorn for her nest.",
            "The magpie was embarrassed but returned the acorn. She'd only wanted something pretty for her babies.",
            "Tom suggested the kingdom share their shiniest things with the magpie family for helping solve the mystery.",
            "The animals crowned Tom an honorary member of their kingdom. He visited every day after school.",
            "And whenever an animal needed help, they knew exactly who to call - Tom the Listener. THE END"
        ]
    },
    {
        "title": "The Giants' Tea Party",
        "description": "Tiny twins are invited to a giants' tea party and learn that size doesn't matter for friendship.",
        "genre": "Fantasy",
        "age_rating": "All Ages",
        "cover_prompt": "two tiny children having tea with friendly giants at enormous table, whimsical children's book illustration",
        "pages": [
            "Lily and Leo were the smallest kids in their village. Everyone called them 'the tiny twins.'",
            "One day, they found a beautiful invitation as big as a door. 'You are invited to tea,' it read.",
            "They followed the enormous footprints to a castle in the clouds where giants lived!",
            "The giants were HUGE, but their smiles were even bigger. 'Welcome, little friends!' they boomed.",
            "The teacup was like a swimming pool! The cookies were as big as cars! But the giants were so gentle.",
            "They played tiny-giant games. The twins hid in the giants' pockets for hide-and-seek.",
            "At first, the twins felt too small. But the giants said, 'Small friends can reach small places we can't!'",
            "The twins helped find a lost ring that had rolled under the giant furniture.",
            "The giants helped the twins see the sunset from above the clouds - something they'd never done before.",
            "As the twins left, the gentle giants gave them tiny friendship bracelets (giant shoelaces!).",
            "The twins learned that day: it's not about how big you are, but how big your heart is. THE END"
        ]
    },
    {
        "title": "The Mermaid's Song",
        "description": "A mermaid discovers her singing can heal the ocean and embarks on a quest to save marine life.",
        "genre": "Fantasy",
        "age_rating": "5+",
        "cover_prompt": "beautiful young mermaid singing with golden voice waves, healing sick coral reef, underwater fantasy scene",
        "pages": [
            "Deep in the Crystal Cove lived Marina, a young mermaid with a voice like honey and starlight.",
            "When Marina sang, fish would stop swimming to listen, and even the grumpy octopus would smile.",
            "One day, Marina found her friend Finn the fish lying sick near dying coral. His scales had lost their shine.",
            "Without thinking, Marina began to sing a song from her heart. Golden ripples spread through the water.",
            "To her amazement, Finn's scales began to shimmer again, and the coral started glowing!",
            "An ancient whale appeared. 'Child, you have the Gift of Healing Song. The ocean needs you.'",
            "The whale showed her the Great Reef, once colorful but now gray and lifeless from pollution.",
            "Marina traveled far, singing her healing song. Coral bloomed, fish recovered, and seaweed danced.",
            "But the biggest challenge was the Dark Depths, where no light - or song - had reached in centuries.",
            "Marina sang her bravest song yet. Light burst from the darkness as life returned to the deep!",
            "Now Marina swims through all the oceans, singing her healing songs wherever they're needed. THE END"
        ]
    },
    {
        "title": "The Enchanted Paintbrush",
        "description": "Everything Maya paints with her magic paintbrush comes to life!",
        "genre": "Fantasy",
        "age_rating": "All Ages",
        "cover_prompt": "young artist girl with glowing magical paintbrush, paintings coming to life around her, whimsical fantasy",
        "pages": [
            "Maya loved to paint more than anything. Her room was covered in pictures of animals and flowers.",
            "One rainy day, she found an old paintbrush in her grandmother's attic. It glowed when she touched it!",
            "Maya painted a butterfly. The colors sparkled, and suddenly - the butterfly flew right off the paper!",
            "She painted a puppy, and it barked! A bird sang! A fish swam through the air!",
            "Maya was having so much fun, she painted a big friendly dragon. But this dragon was TOO big!",
            "The dragon accidentally knocked over furniture and scared the cat. Maya didn't know what to do!",
            "Then she had an idea. She painted a smaller, calmer dragon friend for the big one.",
            "The two dragons played together gently. Maya learned to paint with responsibility.",
            "Now Maya paints carefully, creating friends for lonely animals and flowers for sad neighbors.",
            "Her room is full of magical paintings, but her favorite is the one of her family - alive with love!",
            "And the paintbrush? It only works for those who paint with kindness in their hearts. THE END"
        ]
    },
    {
        "title": "The Cloud Keeper",
        "description": "Oliver becomes the apprentice to the Cloud Keeper and learns to shape weather for the world below.",
        "genre": "Fantasy",
        "age_rating": "5+",
        "cover_prompt": "young boy shaping fluffy clouds with elderly mentor in sky castle, weather magic, dreamy children's book",
        "pages": [
            "Oliver always stared at clouds. While other kids saw shapes, Oliver saw faces, stories, and feelings.",
            "One morning, a silver ladder appeared outside his window, stretching up into the clouds.",
            "At the top was a castle made of cloudstuff, and an old man with a beard like cotton candy.",
            "'I'm the Cloud Keeper,' he said. 'I've been watching you. Would you like to be my apprentice?'",
            "Oliver learned to sculpt clouds into fluffy animals, to squeeze gentle rain for thirsty gardens.",
            "He discovered how to paint sunsets with cloud brushes and how to make snow for winter.",
            "But one day, Oliver accidentally made a storm cloud too powerful. It headed for his village!",
            "The Cloud Keeper smiled. 'Mistakes happen. Now learn to fix them.' He showed Oliver how.",
            "Together, they transformed the scary storm into a gentle shower with a beautiful rainbow.",
            "The villagers below looked up in wonder at the most magnificent rainbow they'd ever seen.",
            "Now Oliver helps the Cloud Keeper every summer, learning new sky magic. One day, he'll take over. THE END"
        ]
    },
    {
        "title": "The Phoenix Feather",
        "description": "Siblings find a phoenix feather that grants them flying powers for one magical night.",
        "genre": "Fantasy",
        "age_rating": "All Ages",
        "cover_prompt": "two children flying through starry night sky holding glowing phoenix feather, magical adventure",
        "pages": [
            "Emma and Ethan were twins who did everything together. Their favorite thing was stargazing.",
            "One night, a shooting star landed in their backyard. But it wasn't a star - it was a glowing feather!",
            "When they both touched it, they began to float! The feather had given them the power to fly!",
            "'We can fly!' they shouted, soaring above the treetops into the velvet night sky.",
            "They flew over their sleeping town, past the water tower, and up to the clouds.",
            "An owl joined them, surprised to have human flying companions. 'Only for tonight,' they laughed.",
            "They played tag among the stars and danced with the moon's reflection on a lake.",
            "As dawn approached, the feather began to fade. They had to go home.",
            "They landed softly in their backyard just as the sun peeked over the horizon.",
            "The feather disappeared with a warm glow, leaving only golden dust on their hands.",
            "Emma and Ethan never forgot their night of flying. And sometimes, they still find feather-shaped clouds. THE END"
        ]
    },
    # Adventure (9 more = 12 total)
    {
        "title": "Journey to the Center of the Treehouse",
        "description": "Kids discover their treehouse has magical levels going deep underground.",
        "genre": "Adventure",
        "age_rating": "5+",
        "cover_prompt": "children descending spiral staircase inside magical treehouse into glowing underground world, adventure",
        "pages": [
            "The treehouse had been in Jake's backyard forever, but he'd never noticed the trapdoor until today.",
            "His sister Amy found it under the old rug. 'I wonder where it goes?' she whispered.",
            "They opened it to find a spiral staircase going down, down, down into soft glowing light.",
            "The first level was a library with books that turned pages by themselves!",
            "Deeper down, they found a room full of clocks showing different times around the world.",
            "Even deeper was an underground garden with flowers that glowed like lanterns!",
            "They met a friendly mole who said, 'The treehouse is magic! Its roots reach to the center of imagination.'",
            "The deepest level was a room of mirrors showing different versions of themselves - older, younger, braver.",
            "Jake and Amy realized the treehouse reflected their own imaginations and grew as they dreamed.",
            "They raced back up the stairs, excited to dream even bigger dreams.",
            "Now their treehouse has new levels every week. Who knows what they'll discover next? THE END"
        ]
    },
    {
        "title": "The Great Balloon Escape",
        "description": "Best friends accidentally float away in a hot air balloon and see the world from above.",
        "genre": "Adventure",
        "age_rating": "All Ages",
        "cover_prompt": "two children in colorful hot air balloon floating over patchwork farmland, adventurous and joyful",
        "pages": [
            "The county fair was Mia and Zoe's favorite day of the year. This year, they spotted a beautiful balloon.",
            "'Can we look inside?' The balloonist said yes, but just then, his phone rang.",
            "While he talked, the rope slipped! The balloon lifted off with Mia and Zoe inside!",
            "They floated up, up, up! The fair became tiny, then their town, then the whole county!",
            "At first they were scared, but then Mia said, 'Look at the world! It's like a quilt!'",
            "They drifted over farms, forests, and rivers. A flock of geese flew alongside them.",
            "The balloon carried them to places they'd only seen in books - mountains! Lakes! Castles!",
            "As sunset painted the sky, they spotted their town again. The balloon slowly descended.",
            "They landed safely in a meadow where the balloonist was waiting with their relieved parents.",
            "'That was the best adventure ever!' the girls agreed, hugging tight.",
            "Now they're saving up to take balloon lessons. This time, they'll choose where to go! THE END"
        ]
    },
    {
        "title": "Pirates of the Playground",
        "description": "Imagination transforms the playground into a pirate ship sailing to adventure.",
        "genre": "Adventure",
        "age_rating": "All Ages",
        "cover_prompt": "children on playground equipment imagining it as pirate ship, sea monsters and treasure island visible, imaginative",
        "pages": [
            "Captain Cole declared recess was no longer recess. 'Arrr! We be pirates now!'",
            "The jungle gym became a ship, the slide a plank, and the sandbox a golden beach.",
            "First Mate Freya spotted a sea monster (the gym teacher walking by). 'All hands on deck!'",
            "They sailed through storms (the sprinklers) and fought giant squids (jump ropes).",
            "Navigator Nina used the monkey bars as a crow's nest to spot Treasure Island (the far playground).",
            "They raced to the island, battling a rival pirate crew (the fifth graders) along the way.",
            "X marked the spot under the old oak tree. They dug and found... a lunchbox of golden cookies!",
            "The crew divided the treasure fairly, each getting three golden (actually chocolate chip) coins.",
            "The school bell rang, ending their voyage. But pirates always return to sea...",
            "...which is why they planned the next adventure during math class. THE END"
        ]
    },
    {
        "title": "The Deepest Dive",
        "description": "A young explorer discovers an underwater kingdom in her backyard pond.",
        "genre": "Adventure",
        "age_rating": "5+",
        "cover_prompt": "child swimming with magical goggles through underwater kingdom with fish palaces, magical realism",
        "pages": [
            "The pond behind Lily's house was small, but she always felt there was more to it.",
            "One day, she found old goggles in the shed. When she put them on, they glowed!",
            "Lily dipped her face in the water and gasped. The tiny pond was ENORMOUS underneath!",
            "She dove in and could breathe! The magic goggles let her explore an underwater world.",
            "There were fish cities with coral buildings and streets paved with smooth pebbles.",
            "A wise old catfish welcomed her. 'Ah, a Surface Walker! We've been waiting for a visitor.'",
            "Lily explored the Royal Reef, the Seaweed Forest, and the Mysterious Trenches.",
            "She helped solve a dispute between the Goldfish and the Guppies about who had shinier scales.",
            "When sunset painted the water golden, Lily knew it was time to go home.",
            "She surfaced to find the pond was still small and ordinary - the magic was inside!",
            "Now Lily visits the underwater kingdom whenever she needs a friend. THE END"
        ]
    },
    {
        "title": "Safari in the Backyard",
        "description": "Through a magnifying glass, the backyard becomes a wild safari adventure.",
        "genre": "Adventure",
        "age_rating": "All Ages",
        "cover_prompt": "child with magnifying glass in backyard seeing insects as large safari animals, imaginative perspective",
        "pages": [
            "Sam was bored. His backyard seemed so small and ordinary. Then he found Grandpa's old magnifying glass.",
            "When he looked through it, the grass became a jungle! An ant was as big as an elephant!",
            "Sam was a safari explorer now. The ladybug was a spotted leopard. The butterfly, a colorful bird.",
            "He followed a beetle through the jungle, discovering an ant colony - a whole city!",
            "A spider web was a glittering palace. 'The Silk Castle,' Sam whispered in awe.",
            "A grasshopper jumped past - a kangaroo! A worm wriggled by - a giant snake!",
            "At the birdbath, Sam found an oasis where all the insects came for water.",
            "He watched them drink together, predators and prey, at peace like at real watering holes.",
            "When Mom called for dinner, Sam looked up. The world was normal-sized again.",
            "But now Sam knew the truth: adventure is everywhere if you look close enough.",
            "He kept the magnifying glass in his pocket, ready for the next safari. THE END"
        ]
    },
    {
        "title": "The Lost Lighthouse",
        "description": "Twins discover an abandoned lighthouse that holds secrets of their great-grandmother.",
        "genre": "Adventure",
        "age_rating": "8+",
        "cover_prompt": "two children exploring dusty abandoned lighthouse with beam of light, mysterious atmosphere, coastal setting",
        "pages": [
            "Every summer, Ava and Noah stayed at their grandmother's beach cottage.",
            "This year, they spotted something new: an old lighthouse on the rocky cliff.",
            "'That's been closed for fifty years,' Grandma said mysteriously. 'Since my mother's time.'",
            "The twins had to investigate. They climbed the cliff and found the rusty door unlocked.",
            "Inside were dusty photographs, old logs, and a beautiful journal with their great-grandmother's name!",
            "The journal told the story of Evelyn, who kept the lighthouse lit through the worst storms.",
            "One night, she saw a ship heading for the rocks. She climbed to the top and lit the beacon just in time.",
            "The ship was saved, and the captain was so grateful, he sent her a golden compass.",
            "The twins found the compass in a hidden drawer! It still pointed true north.",
            "They showed Grandma, who cried happy tears. 'I thought this was lost forever.'",
            "Now the lighthouse is being restored, and Grandma tells visitors Evelyn's heroic story. THE END"
        ]
    },
    {
        "title": "The Volcano Explorers",
        "description": "Young scientists investigate a dormant volcano and discover it's actually a dragon's home.",
        "genre": "Adventure",
        "age_rating": "8+",
        "cover_prompt": "two young explorers inside volcanic cave discovering sleeping dragon made of magma, science adventure",
        "pages": [
            "Maya and Isaac were junior scientists. Their dream: explore the Sleeping Giant volcano.",
            "With safety gear and notebooks, they hiked to the crater. Steam rose like dragon's breath.",
            "Inside the rim, they found a cave system no one had mapped. 'Let's document everything!'",
            "Deeper inside, the walls glowed with crystals. The temperature rose, but not dangerously.",
            "Then they found HIM - a massive dragon made of magma and stone, sleeping peacefully.",
            "Maya was terrified, but Isaac noticed something. 'Look! He's the volcano. They're one being!'",
            "The dragon's eye opened. 'Young scientists. Finally, someone who seeks to understand, not destroy.'",
            "The dragon explained he'd slept for centuries, too tired to migrate to the Dragon Realm.",
            "The twins promised to keep his secret and protect the mountain from developers.",
            "In return, the dragon let them study the crystal caves - the most amazing research ever!",
            "Maya and Isaac became famous scientists who always said, 'Science is about discovery AND respect.' THE END"
        ]
    },
    {
        "title": "Mystery Island Express",
        "description": "A magical train takes passengers to different adventure islands at each stop.",
        "genre": "Adventure",
        "age_rating": "5+",
        "cover_prompt": "magical colorful train traveling between floating fantasy islands in the clouds, adventure wonder",
        "pages": [
            "Ben found a golden ticket in a library book. 'One ride on the Mystery Island Express.'",
            "At midnight, a gleaming train appeared at his window. The conductor smiled. 'All aboard!'",
            "First stop: Dinosaur Island! Ben rode a gentle Brontosaurus and fed a baby T-Rex.",
            "Second stop: Candy Mountain! Chocolate waterfalls, gumdrop trees, and clouds of cotton candy.",
            "Third stop: Robot City! Ben helped fix a robot dog and attended a robot dance party.",
            "Fourth stop: Underwater Station! A glass dome where fish gave tours of sunken treasures.",
            "Fifth stop: The Cloud Kingdom! Fluffy beds, pillow fights, and dream-viewing theaters.",
            "Final stop: Treasure Island! But the real treasure was a scrapbook of photos from every island.",
            "As dawn arrived, the train returned Ben home. 'Will I ever go back?' he asked.",
            "The conductor winked. 'Look in your pocket.' There was another golden ticket!",
            "Ben knew adventures never really end - they just wait for you to be ready. THE END"
        ]
    },
    {
        "title": "Jungle Gym Expedition",
        "description": "The school jungle gym becomes a real jungle when Maya makes a wish.",
        "genre": "Adventure",
        "age_rating": "All Ages",
        "cover_prompt": "playground jungle gym transformed into real jungle with vines and monkeys, magical transformation",
        "pages": [
            "Maya was having the worst day. She missed the bus, forgot her lunch, and failed the spelling test.",
            "At recess, she climbed to the top of the jungle gym. 'I wish I was in a REAL jungle!'",
            "The metal bars became vines! The rubber floor became moss! Real birds flew overhead!",
            "Maya couldn't believe it. The boring playground was now a tropical paradise!",
            "A friendly monkey swung by and offered her a banana. A parrot landed on her shoulder.",
            "She explored deeper, finding a waterfall (the drinking fountain), a cave (the slide tunnel), and ancient ruins (the sandcastle).",
            "At the ruins, she found a message: 'Adventure is always just a wish away.'",
            "The school bell rang. Slowly, the jungle faded back to normal.",
            "But Maya noticed something different - she was smiling! Her bad day didn't seem so bad anymore.",
            "From then on, whenever things got tough, Maya whispered, 'I wish for adventure.'",
            "And somehow, even on the boring playground, she always found one. THE END"
        ]
    },
    # Science Fiction (7 more = 10 total)
    {
        "title": "The Mars Mission Kids",
        "description": "The first kids born on Mars explore their red planet home and discover ancient mysteries.",
        "genre": "Science Fiction",
        "age_rating": "8+",
        "cover_prompt": "children in space suits exploring Mars surface with red mountains and two moons, futuristic adventure",
        "pages": [
            "Zara and Kai were the first children born on Mars. The red planet was their only home.",
            "They lived in Dome City Alpha, where everything was recycled and gardens grew in hydroponic bays.",
            "One day, the twins received permission to explore outside the dome for their 10th birthday.",
            "In their junior space suits, they climbed Olympus Mons - the tallest volcano in the solar system!",
            "Near the summit, they found something strange: markings in the rock that looked almost like... letters.",
            "They documented everything, sending photos to Mission Control. Scientists were amazed!",
            "The markings were ancient - older than humanity's arrival. Had something lived here before?",
            "Zara and Kai were famous overnight - the kids who discovered Mars's biggest mystery!",
            "More expeditions followed, and Zara became an archaeologist while Kai studied geology.",
            "Years later, they still hadn't decoded the markings. But that's science - full of questions.",
            "And Zara and Kai loved nothing more than searching for answers on their red desert home. THE END"
        ]
    },
    {
        "title": "Time Machine Trouble",
        "description": "Accidentally traveling to different time periods, Max must find his way back to present day.",
        "genre": "Science Fiction",
        "age_rating": "8+",
        "cover_prompt": "boy tumbling through time vortex with dinosaurs, knights, and robots visible in swirling colors",
        "pages": [
            "Grandpa's attic was full of strange inventions, but Max had never seen this one before.",
            "It was a chair with blinking lights and a big red button. 'DO NOT PRESS' said the label.",
            "Max pressed it. The room spun, and suddenly he was in a prehistoric jungle with dinosaurs!",
            "A friendly Triceratops helped him find the 'Reset' button - but it sent him to medieval times!",
            "He helped a young knight find her lost sword, and she showed him the 'Home' button.",
            "But that sent him to the far future - 3025! Robots served breakfast and cars flew.",
            "A robot historian explained the chair was a Time Jumper, and it needed all three era pieces to work properly.",
            "Max realized: in each time, he'd collected something - a dinosaur scale, a knight's token, a robot chip!",
            "He combined them in the chair. The room spun again, and... he was home! Just in time for dinner.",
            "Max told no one about his adventure. But he did start studying history a lot more carefully.",
            "And he NEVER pressed red buttons again. Well, almost never. THE END"
        ]
    },
    {
        "title": "The Shrinking Machine",
        "description": "When dad's invention shrinks the family, they must navigate their suddenly giant house.",
        "genre": "Science Fiction",
        "age_rating": "5+",
        "cover_prompt": "tiny family standing on kitchen counter looking at enormous furniture, comic science fiction",
        "pages": [
            "Dad was an inventor. Usually his inventions didn't work. But this one worked TOO well!",
            "ZAP! The whole family - Dad, Mom, Lily, and Tom - shrank to the size of ants!",
            "The living room was now a vast plain. The cat was a giant, curious monster!",
            "They climbed Mount Coffee Table and crossed the Carpet Desert.",
            "The crumbs in the kitchen were boulders! A dropped cheerio was a delicious feast.",
            "Their mission: reach Dad's workshop in the basement and find the reverse button.",
            "But the basement stairs were like climbing a skyscraper! Each step took an hour!",
            "Working together, they made it. Dad pressed 'REVERSE' just as the cat found them!",
            "They grew back just in time! The cat looked very confused at the suddenly giant family.",
            "Mom made Dad promise: 'No more shrinking inventions. EVER.'",
            "Dad agreed. Instead, he started working on a growing ray. What could go wrong? THE END"
        ]
    },
    {
        "title": "Space Station Summer Camp",
        "description": "Kids from around the world attend the first summer camp in space.",
        "genre": "Science Fiction",
        "age_rating": "8+",
        "cover_prompt": "diverse children floating in space station playing games with Earth visible through window, fun futuristic",
        "pages": [
            "The year was 2045, and Emma won the lottery - a spot at Space Camp Orbital!",
            "She joined kids from twelve different countries, all training for life in zero gravity.",
            "Breakfast was floating cereal! Soccer was played bouncing off walls! Sleep was in hanging pods!",
            "Emma made friends with Yuki from Japan, Ahmed from Egypt, and Sofia from Brazil.",
            "Together they learned to spacewalk, operate robots, and grow food in space gardens.",
            "But then alarms blared! A micrometeorite had damaged the solar panels!",
            "The campers worked together, using everything they'd learned to make emergency repairs.",
            "Sofia sealed the breach, Ahmed rerouted power, Yuki fixed the wiring, and Emma communicated with Earth.",
            "They saved the station! NASA called them the youngest heroes in space history.",
            "At graduation, they got real astronaut wings. But better than that - they got lifelong friendships.",
            "They promised to reunite on the first Mars mission together. THE END"
        ]
    },
    {
        "title": "The Alien Exchange Student",
        "description": "When Zorp from Planet X joins third grade, learning about each other changes everyone.",
        "genre": "Science Fiction",
        "age_rating": "5+",
        "cover_prompt": "friendly alien child with purple skin and antennae sitting in classroom with human kids, heartwarming",
        "pages": [
            "When Mrs. Wilson said there was a new student, no one expected a purple alien with four arms!",
            "'This is Zorp from Planet X,' she said calmly. 'Please make him feel welcome.'",
            "At first, kids were scared. Zorp looked so different! He ate lunch through his forehead!",
            "But then Maya noticed Zorp was alone at recess. She sat next to him. 'Hi. Want to play?'",
            "Zorp showed her games from Planet X - like hovering tag and telepathy catch!",
            "In return, Maya taught him Earth games. Zorp LOVED basketball (four arms help!).",
            "Soon everyone wanted to be Zorp's friend. He could solve math instantly and tell funny space jokes.",
            "But one day, Zorp was sad. 'I miss my family. Everything here is so different.'",
            "The class had an idea. They threw Zorp a Planet X party with purple decorations and floating snacks!",
            "Zorp's antennae wiggled with joy. 'On my planet, this means very happy!'",
            "The exchange program was a success. Now kids from Earth visit Planet X too. THE END"
        ]
    },
    {
        "title": "Underwater City 2150",
        "description": "In the future, kids live in cities under the sea and explore the deep ocean.",
        "genre": "Science Fiction",
        "age_rating": "8+",
        "cover_prompt": "futuristic underwater city with glass domes and submarines, children swimming with enhanced gear",
        "pages": [
            "In the year 2150, cities floated under the ocean. Coral grew on skyscrapers, and whales were neighbors.",
            "Naia was born in Atlantis-7, a beautiful dome city three miles below the surface.",
            "She went to school in a submarine, played soccer in underwater stadiums, and had a pet jellyfish.",
            "Her favorite class was Deep Sea Exploration, where students learned to pilot personal mini-subs.",
            "One day, sensors detected a distress signal from the Midnight Zone - the deepest, darkest area.",
            "Naia and her classmates volunteered for the rescue mission (with teacher supervision, of course).",
            "They descended through bioluminescent clouds of plankton, past giant squid and ancient whales.",
            "They found a damaged research pod with two scientists trapped inside! Their lights had failed.",
            "Naia used her training to dock with the pod while her friends guided them up with their sub lights.",
            "The scientists were saved! They'd been studying a new species of glowing fish in the depths.",
            "Naia received the Young Ocean Hero award. She couldn't wait for her next deep dive! THE END"
        ]
    },
    {
        "title": "The Coding Club Mystery",
        "description": "Kids who code discover their programs can come to life and solve real mysteries.",
        "genre": "Science Fiction",
        "age_rating": "8+",
        "cover_prompt": "diverse kids at computers with holographic code characters solving puzzles, tech mystery",
        "pages": [
            "The Coding Club met every Wednesday in the school computer lab. Today, something magical happened.",
            "When Jamie's avatar program ran, it didn't just appear on screen - it popped into real life!",
            "'I'm CodeBot!' said the glowing figure. 'You coded me with such detail, I became real!'",
            "The club discovered that if they coded with enough passion, their creations came to life!",
            "They created Detective programs, Helper bots, and a friendly AI that loved telling jokes.",
            "Then the school trophy disappeared! Principal Martinez was devastated.",
            "The Coding Club activated their Detective program. It scanned for clues invisible to humans.",
            "Digital footprints led to the art room, where the trophy had fallen behind a cabinet!",
            "The cleaning robot had accidentally knocked it back there. Mystery solved!",
            "The principal started a school-wide coding program. 'Every kid should learn to create!'",
            "And the Coding Club? They were already working on their biggest project yet: A robot teacher! THE END"
        ]
    },
    # Mystery (4 more = 6 total)
    {
        "title": "Mystery at the Museum",
        "description": "A famous dinosaur bone goes missing from the museum during a school field trip.",
        "genre": "Mystery",
        "age_rating": "8+",
        "cover_prompt": "two kids investigating in museum at night with flashlights, dinosaur skeleton in background, mystery",
        "pages": [
            "The Natural History Museum was Theo's favorite place. But today's field trip took a mysterious turn.",
            "During lunch, alarms blared. The famous T-Rex tooth - worth millions - had vanished!",
            "Police locked down the museum. But Theo noticed something everyone missed: footprints in the dust.",
            "He grabbed his friend Sam. 'Look! These footprints go behind the Ancient Egypt exhibit!'",
            "Following the trail, they found a hidden door disguised as a sarcophagus!",
            "Inside was a network of tunnels used by museum staff. The footprints continued deeper.",
            "They found the T-Rex tooth... next to a crying man in a janitor's uniform.",
            "'I wasn't stealing it!' he said. 'I was saving it! I saw someone else trying to take it!'",
            "He explained: a collector had bribed another staff member. The janitor hid it to protect it!",
            "Security footage proved his story. The real thief was caught, and the janitor was a hero.",
            "Theo received a special Junior Detective badge from the museum. His next mystery awaits! THE END"
        ]
    },
    {
        "title": "The Haunted Playground",
        "description": "Strange things happen at the old playground after dark. Is it really ghosts?",
        "genre": "Mystery",
        "age_rating": "8+",
        "cover_prompt": "children investigating spooky playground at dusk with mysterious shadows, not too scary",
        "pages": [
            "Everyone said the old Miller Park playground was haunted. Swings moved by themselves at night.",
            "Spooky sounds came from the slide. Lights flickered near the merry-go-round.",
            "Detectives Mia and Josh weren't scared - they were curious! 'Ghosts aren't real,' said Mia.",
            "They staked out the playground after sunset, armed with flashlights and courage.",
            "The swings DID move! But Mia noticed something: they moved when a breeze came through the trees.",
            "The spooky sounds from the slide? A family of raccoons had made a nest inside!",
            "The flickering lights? Old electrical wiring from the park's ancient lamp post.",
            "But they found something unexpected: a homeless man sleeping under the play structure.",
            "His name was Mr. Patterson. He was once a teacher at their school, fallen on hard times.",
            "The kids told their parents, who helped Mr. Patterson find a real home and a job.",
            "The 'haunted' playground was just a place that needed care - for its equipment AND its visitor. THE END"
        ]
    },
    {
        "title": "The Secret of Room 13",
        "description": "The always-locked Room 13 at school holds a secret students are determined to uncover.",
        "genre": "Mystery",
        "age_rating": "8+",
        "cover_prompt": "children peeking into mysterious classroom 13 with old items and dusty shelves, school mystery",
        "pages": [
            "Room 13 had been locked for as long as anyone could remember. Even teachers avoided it.",
            "'There's no Room 13,' Principal Lee always said. 'We skip that number. It's just storage.'",
            "But Lily and Carlos noticed light under the door once. Storage rooms don't have lights!",
            "They researched in the library, finding old yearbooks from 50 years ago. Room 13 was real!",
            "It had been a special classroom for a beloved teacher named Mrs. Harmony who taught music.",
            "When she retired, the school sealed the room as a tribute. But why so secret?",
            "They found the janitor's old key ring and, with permission (mostly), opened the door.",
            "Inside was a time capsule! Mrs. Harmony had asked each student to leave a memory for the future.",
            "There were letters, drawings, and a beautiful note: 'Open in 50 years with a new class.'",
            "It was exactly 50 years! The school held a ceremony, inviting Mrs. Harmony (now 90) to open it.",
            "Lily and Carlos learned: some secrets are worth keeping - until the right time. THE END"
        ]
    },
    {
        "title": "The Whispering Woods",
        "description": "Trees in the forest seem to whisper secrets. What are they trying to say?",
        "genre": "Mystery",
        "age_rating": "8+",
        "cover_prompt": "child with ear pressed to ancient tree trunk listening, magical forest with glowing symbols",
        "pages": [
            "When the wind blew through Whispering Woods, it sounded like voices. Most people were scared.",
            "But not Ava. She spent hours in those woods, trying to understand what the trees said.",
            "One day, she noticed a pattern. The whispers were louder near the oldest oak tree.",
            "She pressed her ear to the bark and heard clearly: 'Find the stone. Protect the forest.'",
            "Ava searched until she found an ancient stone carved with symbols at the tree's roots.",
            "A nature historian helped translate: it marked the forest as protected land from centuries ago!",
            "But developers wanted to build a mall! The protected status had been 'lost' from records.",
            "Ava showed the stone to town officials. It was legal proof the forest couldn't be touched!",
            "The developers were stopped. The forest was saved. And the whispers?",
            "They now said something new: 'Thank you, young guardian.'",
            "Ava visits the ancient oak every week, listening for new messages from her forest friends. THE END"
        ]
    },
    # Comic/Humor (4 more = 6 total)
    {
        "title": "The Upside Down Day",
        "description": "Everything is backwards today - even gravity! How will Emma cope?",
        "genre": "Comic",
        "age_rating": "All Ages",
        "cover_prompt": "girl walking on ceiling with furniture falling upward, silly and fun children's illustration",
        "pages": [
            "Emma woke up on the ceiling. This was going to be an interesting day.",
            "'MOM! Gravity is broken again!' (This happened more often than you'd think.)",
            "Breakfast was tricky - cereal floated up, milk refused to pour, and the toast hit the ceiling.",
            "School was chaos! Desks stuck to ceilings, teachers taught from ladders, and recess was amazing.",
            "Emma discovered she could bounce between floor and ceiling like a superball!",
            "The principal made an announcement: 'All tests are cancelled. No one can keep their pencils down.'",
            "Lunch was the best part - pizza slices floated around like delicious UFOs!",
            "By afternoon, Emma was getting tired of being upside down. Her head hurt from the blood rush.",
            "Then, as suddenly as it started, gravity returned. CRASH! Everyone fell back to their floors.",
            "The next day, everything was normal. Well, except for the purple rain.",
            "But that's another story. THE END"
        ]
    },
    {
        "title": "My Pet Dinosaur",
        "description": "When Tommy's 'lizard' grows into a dinosaur, hiding it becomes hilariously difficult.",
        "genre": "Comic",
        "age_rating": "All Ages",
        "cover_prompt": "boy hiding giant friendly dinosaur behind tiny tree while neighbors look around suspiciously, comedy",
        "pages": [
            "Tommy found an egg in the backyard and kept it warm. Out hatched what he thought was a lizard.",
            "He named it Tiny and hid it in his room. But Tiny grew. And grew. AND GREW!",
            "Soon Tiny was as big as a dog. Then a car. Then a HOUSE!",
            "Hiding a dinosaur is NOT easy. 'That's just a... very big... green dog,' Tommy told the neighbors.",
            "Tiny ate everything! The garden, the mailbox, and nearly the mailman!",
            "The news showed up: 'Giant Lizard Spotted!' Tommy dressed Tiny as a parade float.",
            "Scientists came. 'That's clearly a dinosaur!' Tommy said it was 'a new breed of iguana.'",
            "Eventually, the truth came out. Tiny was a real, living dinosaur - and she was lonely.",
            "Scientists found more eggs and created a dinosaur sanctuary. Tiny had friends!",
            "Tommy visits every weekend. Tiny remembers him and still thinks she's a tiny lizard.",
            "She tries to sit in Tommy's lap. It's very uncomfortable but very, very sweet. THE END"
        ]
    },
    {
        "title": "The Backwards Witch",
        "description": "A witch whose spells always do the opposite of what she intends.",
        "genre": "Comic",
        "age_rating": "All Ages",
        "cover_prompt": "confused witch with spell going opposite direction, flowers blooming instead of wilting, funny magic",
        "pages": [
            "Wilma was a witch, but not a very good one. Her spells always did the OPPOSITE of what she wanted.",
            "'Turn this frog into a prince!' ZAP! The prince became a frog. Oops.",
            "'Make it rain!' ZAP! The desert became even drier. Double oops.",
            "'Create darkness!' ZAP! The sun got brighter. Triple oops.",
            "The other witches laughed at her. 'Backwards Wilma can't do anything right!'",
            "One day, an evil dragon attacked the village. All the good witches' spells bounced off!",
            "Wilma had an idea. 'I'll try to HELP the dragon!' ZAP!",
            "The spell did the opposite - it put the dragon to sleep and made flowers grow on its scales!",
            "The village was saved! Wilma was a hero, even if accidentally.",
            "Now when anyone has a problem, they ask Wilma to make it WORSE.",
            "And magically, everything turns out fine. Backwards magic is still magic! THE END"
        ]
    },
    {
        "title": "Grandma's Crazy Inventions",
        "description": "Grandma's inventions never work as planned, but the adventures are always amazing!",
        "genre": "Comic",
        "age_rating": "All Ages",
        "cover_prompt": "wacky grandmother with wild hair showing grandkids a malfunctioning flying toaster invention, comedy",
        "pages": [
            "Most grandmas knit sweaters. MY grandma builds robots and rocket-powered wheelchairs.",
            "Her latest invention: a machine that does your homework. It did homework, alright - it wrote a novel!",
            "The self-making bed trapped Dad in a cocoon of sheets for three hours.",
            "The automatic dog walker walked the HOUSE while the dog watched from the window.",
            "Her best/worst invention was the 'helpful hat.' It tried to help so much it caused more problems!",
            "The hat brought coffee - by throwing it. It opened doors - by removing them from hinges.",
            "It helped with gardening by replanting the garden in the living room!",
            "Dad said, 'Mom, please stop inventing!' Grandma looked sad.",
            "But then her smoke detector invented itself into a robot and saved the kitchen from a fire!",
            "Dad admitted: 'Okay, maybe SOME inventions are useful.'",
            "Grandma smiled and showed us her next project: teleporting toilet. THE END"
        ]
    },
    # General/Educational (5 more = 7 total)
    {
        "title": "The Alphabet Adventure",
        "description": "Letters take a young reader on a journey where each letter introduces something wonderful.",
        "genre": "General",
        "age_rating": "All Ages",
        "cover_prompt": "colorful alphabet letters as friendly characters dancing around happy child, educational and fun",
        "pages": [
            "Amy opened her ABC book, and the letters jumped right out!",
            "A for Adventure! Letter A took her to an Amazing Amazon with Alligators!",
            "B for Butterfly! Beautiful Blue butterflies surrounded them as they flew to C.",
            "C for Castle! Inside lived a Cat who Could make Chocolate Chip Cookies!",
            "D for Dragon! But this Dragon was Different - he preferred Dancing to fire-breathing.",
            "E and F brought Eagles and Fireflies to light the way to G.",
            "G for Garden, H for Happiness, I for Imagination!",
            "The letters showed her that everything wonderful starts with learning your ABCs.",
            "J to Z flew by in a whirlwind of Jellyfish, Kites, Lions, and Zebras!",
            "When Amy closed the book, she realized she'd learned all 26 letters without trying!",
            "Now she reads everything - signs, books, menus - and the letters always wink at her. THE END"
        ]
    },
    {
        "title": "The Shape Shifters",
        "description": "Shapes teach kids geometry by transforming into different objects and buildings.",
        "genre": "General",
        "age_rating": "5+",
        "cover_prompt": "friendly geometric shapes building a colorful city together, educational children's illustration",
        "pages": [
            "In Geometry Land, shapes weren't just shapes - they were the builders of everything!",
            "Circle was round and loved rolling everywhere. 'I'm wheels, coins, and the sun!'",
            "Square was sturdy and proud. 'I'm buildings, books, and picture frames!'",
            "Triangle was tall and pointy. 'I'm mountains, pyramids, and pizza slices!'",
            "Rectangle was versatile. 'I'm doors, phones, and chocolate bars!'",
            "One day, they decided to build a city together. But they kept arguing about who was best.",
            "Nothing worked! Buildings without circles (wheels) couldn't move materials.",
            "Roofs without triangles collapsed. Doors without rectangles didn't fit.",
            "Finally, they understood: every shape is important! Together, they built amazing things.",
            "Houses had rectangle doors, triangle roofs, square windows, and circle decorations.",
            "Now Shape City is the most beautiful place, where every shape has a purpose. THE END"
        ]
    },
    {
        "title": "Weather Friends",
        "description": "Sunny, Cloudy, Rainy, and Snowy explain how weather works through friendship.",
        "genre": "General",
        "age_rating": "All Ages",
        "cover_prompt": "cute personified weather elements playing together - sun, cloud, rain, snow as friendly characters",
        "pages": [
            "In Weather World, different weathers were best friends who took turns visiting Earth.",
            "Sunny was bright and warm. 'I help plants grow and give people energy!'",
            "Cloudy was soft and cozy. 'I give shade when Sunny is too strong.'",
            "Rainy was gentle but sometimes loud. 'I water gardens and fill rivers!'",
            "Snowy was cold but beautiful. 'I give kids snow days and help the Earth rest.'",
            "One day, they all wanted to visit Earth at once! It caused chaos!",
            "Sun melted the snow while it was still falling. Rain and sun made too many rainbows.",
            "Mother Nature explained: 'You must take turns. That's how seasons work!'",
            "They learned to work together. Summer for Sunny, Fall for Cloudy, Spring for Rainy, Winter for Snowy.",
            "And sometimes they visited together to make beautiful weather mixes!",
            "Now when you see sun and rain together, you know the Weather Friends are playing. THE END"
        ]
    },
    {
        "title": "The Body Explorers",
        "description": "Tiny explorers travel through the human body and explain how everything works.",
        "genre": "General",
        "age_rating": "8+",
        "cover_prompt": "tiny explorers in submarine traveling through human bloodstream with heart visible, educational",
        "pages": [
            "In science class, Ms. Frizzle shrank the students to microscopic size for a body tour!",
            "First stop: the Heart! It pumped like a massive drum, sending blood everywhere.",
            "'It beats 100,000 times a day!' said Ms. Frizzle. 'Never takes a vacation!'",
            "Next: the Lungs! Like pink balloons, they filled with air and pushed out carbon dioxide.",
            "Then: the Brain! Billions of tiny lights (neurons) flashed like the universe's busiest city.",
            "The stomach was like a churning washing machine, breaking down the pizza from lunch.",
            "In the bloodstream, they rode red blood cells like taxi cabs through the body's highways.",
            "White blood cells acted like police, chasing down germs that didn't belong.",
            "The bones were like living scaffolding, always rebuilding and staying strong.",
            "When they returned to normal size, everyone had a new respect for their bodies.",
            "The body is the most amazing machine ever - and it runs on food, water, sleep, and love! THE END"
        ]
    },
    {
        "title": "Seeds to Trees",
        "description": "Follow Sammy the seed on his journey to becoming a mighty oak tree.",
        "genre": "General",
        "age_rating": "All Ages",
        "cover_prompt": "cute acorn seed character growing through seasons into mighty oak tree, nature life cycle",
        "pages": [
            "Sammy was a tiny acorn who lived on a beautiful oak tree with thousands of brothers and sisters.",
            "One autumn day, he fell from his branch and landed on the soft forest floor.",
            "He was scared! How would he survive the cold winter coming?",
            "A friendly squirrel buried him in the soil. 'Sleep tight, little one. Spring will come.'",
            "Under the cold snow, Sammy dreamed of sunshine. His shell softened in the wet earth.",
            "When spring arrived, Sammy felt a strange urge. He pushed, and a tiny root poked out!",
            "Then a green shoot reached up toward the light. Sammy was growing!",
            "Summer sun gave him energy. His leaves were tiny but mighty, catching every ray.",
            "Years passed. Sammy grew taller, then taller still. Birds nested in his branches.",
            "Now Sammy is a mighty oak tree, with thousands of acorn children of his own.",
            "Each fall, his acorns drop to the ground, starting new adventures. THE END"
        ]
    },
]

SYSTEM_AUTHOR = {
    "id": "azories-system",
    "name": "Azories Stories",
    "email": "stories@azories.com"
}

async def main():
    print("=" * 60)
    print("GENERATING 45 MORE BOOKS")
    print("=" * 60)
    
    mongo_url = os.environ.get('MONGO_URL')
    db_name = os.environ.get('DB_NAME')
    
    if not mongo_url or not db_name:
        print("ERROR: MONGO_URL and DB_NAME required")
        return
    
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    # Create books
    for i, book_data in enumerate(MORE_BOOKS):
        book_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        
        book = {
            "id": book_id,
            "title": book_data["title"],
            "description": book_data["description"],
            "genre": book_data["genre"],
            "cover_image": "",  # Will be generated separately
            "back_cover_image": "",
            "cover_title": book_data["title"],
            "cover_subtitle": f"A {book_data['genre']} Story",
            "back_cover_text": book_data["description"],
            "author_id": SYSTEM_AUTHOR["id"],
            "author_name": SYSTEM_AUTHOR["name"],
            "is_published": True,
            "is_featured": i < 5,
            "layout_mode": "standard",
            "age_rating": book_data["age_rating"],
            "view_count": random.randint(50, 500),
            "read_count": random.randint(20, 200),
            "created_at": now,
            "updated_at": now
        }
        await db.books.insert_one(book)
        
        chapter_id = str(uuid.uuid4())
        await db.chapters.insert_one({
            "id": chapter_id,
            "book_id": book_id,
            "title": "Story",
            "order": 1,
            "created_at": now
        })
        
        for j, text in enumerate(book_data["pages"]):
            await db.pages.insert_one({
                "id": str(uuid.uuid4()),
                "chapter_id": chapter_id,
                "text_content": text,
                "image_url": "",
                "order": j + 1,
                "layout_type": "single",
                "image_position_x": 50,
                "image_position_y": 50,
                "image_fit": "cover",
                "created_at": now
            })
        
        print(f"[{i+1}/{len(MORE_BOOKS)}] Created: {book_data['title']} ({len(book_data['pages'])} pages)")
    
    total = await db.books.count_documents({})
    print(f"\n{'='*60}")
    print(f"SUCCESS! Total books now: {total}")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
