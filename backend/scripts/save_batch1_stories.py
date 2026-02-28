"""
Save Batch 1 Story Content to Database
"""
from pymongo import MongoClient
from datetime import datetime

client = MongoClient("mongodb://localhost:27017")
db = client["test_database"]

print("=" * 80)
print("SAVING BATCH 1 STORY CONTENT TO DATABASE")
print("=" * 80)

# Book 1: Captain Compass - Expand pages 8, 9, 10 (indexes 7, 8, 9)
captain_compass_updates = {
    7: '''The crew worked together to solve the final clue. Captain Compass studied the ancient symbols carved into the rock face while Maya measured the shadows cast by the setting sun. Finn noticed something curious - tiny crystals embedded in the stone that sparkled in a specific pattern.

"Look!" he exclaimed, tracing the glittering path with his finger. "The crystals form an arrow!"

Following the sparkling trail, they discovered a hidden lever disguised as an ordinary stone. When Maya pulled it, a section of the cliff face rumbled and slowly swung open, revealing a cave entrance that had been sealed for centuries. Ancient torches flickered to life on their own, illuminating walls covered in paintings that told the story of the treasure's origins. The crew gasped in unison - they had found the legendary Chamber of Wonders that countless explorers had sought for generations.''',
    
    8: '''Inside the treasure chamber, gold coins weren't the only riches they found. There were maps to undiscovered islands, journals written by famous explorers of the past, and magical instruments that could predict the weather with perfect accuracy. But the greatest treasure was a golden compass that glowed with an inner light.

Captain Compass held it reverently, recognizing it immediately from her grandmother's bedtime stories. This was the Compass of Truth - said to guide its bearer not just to any destination, but to whatever they needed most in their heart. "This is worth more than all the gold in the world," she whispered.

The crew gathered around her, understanding that their adventure had given them something more valuable than riches: unshakeable friendship, courage they didn't know they had, and memories that would last forever.''',
    
    9: '''The journey home was filled with laughter and song. Captain Compass had learned that true treasure isn't measured in gold coins or precious gems, but in the friends who sail beside you through calm seas and stormy waters alike. She made a promise to her loyal crew that this was only the beginning of their adventures together.

As their ship sailed into the harbor at sunset, the townspeople gathered to welcome them home. The children listened with wide eyes as the crew told tales of their incredible journey. And every night thereafter, when young sailors gazed at the stars and dreamed of adventure, they would remember the legend of Captain Compass - the brave explorer who taught everyone that the greatest treasures in life are the ones you share with others.

The End.'''
}

book = db.books.find_one({"title": "Captain Compass and the Treasure Map"})
if book:
    pages = book.get('pages', [])
    for idx, new_text in captain_compass_updates.items():
        if idx < len(pages):
            pages[idx]['text_content'] = new_text
    db.books.update_one(
        {"title": "Captain Compass and the Treasure Map"},
        {"$set": {"pages": pages, "_batch1_updated": datetime.now().isoformat()}}
    )
    print("✓ Captain Compass and the Treasure Map - 3 pages expanded")

# Book 2: Colors of the World - Full new story (10 pages)
colors_story = [
    '''In a world painted entirely in shades of gray, there lived a curious young girl named Iris. Her grandmother often told her stories of a time long ago when the sky blazed with brilliant blues, flowers bloomed in every shade imaginable, and rainbows arched across the heavens after summer storms. But Iris had never seen color herself - not a single drop of red, splash of yellow, or whisper of green.

Every morning, Iris would climb the tallest hill near her village and watch the gray sunrise, wondering what it must have looked like when the world still held its colors. "Where did all the colors go?" she asked the wind, but the wind only sighed and swept past without answering.

One day, her grandmother handed her a small, peculiar compass. "This belonged to my grandmother, and her grandmother before her," she said with a knowing smile. "It doesn't point north. It points to what your heart truly seeks."''',
    
    '''The compass needle spun wildly at first, then settled, pointing toward the Whispering Mountains that loomed at the edge of the world. Iris knew immediately what she had to do - she would find the lost colors and bring them home.

She packed her small satchel with bread, cheese, and her grandmother's favorite blanket for warmth. As she left the village, neighbors shook their heads in worry. "No one returns from the Whispering Mountains," they warned. But Iris felt something different in her heart - not fear, but hope.

The journey took many days. She crossed the Gray River, climbed the Ash-colored Cliffs, and traveled through the Pale Forest where the trees stood like frozen ghosts. Through it all, the compass needle remained steady, urging her forward with its quiet, confident pointing.''',
    
    '''Deep within the Whispering Mountains, Iris discovered something extraordinary - a cave entrance that sparkled even in the gray light. As she stepped inside, she felt warmth wash over her like sunshine, though she had never truly felt the sun's warmth before.

The cave opened into a magnificent chamber, and there, floating in crystal prisons throughout the vast space, were the colors themselves! Red pulsed like a beating heart. Blue swirled like ocean waves. Yellow glowed like captured starlight. Each color seemed alive, waiting, hoping to be freed.

An ancient guardian made of living stone rose before her. "Who dares enter the Chamber of Colors?" its voice rumbled like distant thunder. Iris stood tall, though her knees trembled. "I am Iris, and I've come to bring the colors back to the world. Everyone deserves to see their beauty."''',
    
    '''The stone guardian studied her with eyes that had watched centuries pass. "Many have come seeking the colors for themselves - to own them, to control them, to sell them to the highest bidder. Why should I believe you are different?"

Iris thought carefully before answering. "I don't want to own the colors. I want to free them. Colors don't belong trapped in caves - they belong in a child's painting, in a mother's garden, in the sky at sunrise. Colors are meant to be shared, not hoarded."

The guardian was silent for a long moment. Then, slowly, its stone face softened into something that might have been a smile. "In all my centuries of guarding, no one has ever asked to free them. They only wanted to possess them. You, little one, have a colorful heart."''',
    
    '''The guardian showed Iris how to release each color from its crystal prison. First came Red, who leaped out with fierce joy and painted the roses that had been waiting in gray gardens across the world. Sunsets suddenly blazed with passionate fire, and cardinals burst into visibility, their songs somehow sweeter now that their feathers could be seen.

Red embraced Iris gratefully before zooming away to color apples, strawberries, ladybugs, and autumn leaves. Wherever Red went, warmth and energy followed. Children pointed and laughed with delight as they saw their first red balloon, their first ripe tomato, their first beating heart drawn in sidewalk chalk.

"Thank you," Red whispered on the wind. "I've been waiting so long to dance again."''',
    
    '''Next came Blue, cool and calm like a peaceful dream. Blue flowed from the cave and swept across the sky, finally giving it depth and wonder. The oceans turned from gray to deep sapphire and turquoise. Blueberries appeared on bushes, bluejays sang from newly-blue branches, and cornflowers dotted the meadows.

Blue pooled in lakes and rivers, bringing a sense of tranquility wherever it settled. Children discovered they could finally tell the difference between the sky and the sea, and sailors wept with joy at the beauty of the horizon. Blue even colored the sadness in people's hearts, making it somehow easier to feel and to heal.

"Peace," Blue murmured as it painted the delicate forget-me-nots. "I bring peace wherever I go."''',
    
    '''Yellow bounded out next with the energy of pure sunshine. It raced straight to the sun and set it blazing with warmth and light. Suddenly, daffodils and sunflowers burst into bloom, turning their faces toward the golden sky. Bananas ripened to cheerful yellow, and lemons added a tart brightness to kitchen windowsills everywhere.

Yellow colored the baby chicks that peeped in farmyards, the school buses that carried children to new adventures, and the happy faces of smiley stickers. Even people's moods seemed to lift as yellow spread across the world. "Joy!" Yellow sang as it painted a path of marigolds. "I am joy, and joy is meant to be shared!"

Iris laughed as Yellow tickled her nose with pollen from a freshly-colored daisy.''',
    
    '''Green emerged gently, flowing like a river into the world's plants and trees. Grass transformed from gray stubble into soft emerald carpets. Forests breathed deeply as their leaves finally showed their true nature. Frogs hopped happily, newly visible on their lily pads, and parakeets discovered the beauty of their own feathers.

Green brought with it the feeling of growth and new beginnings. Seeds that had waited in the gray earth finally found the courage to sprout. Gardeners cried happy tears as their vegetables revealed themselves in shades of brilliant green. The whole world seemed to exhale with relief.

"Growth," Green hummed, painting the ivy that climbed castle walls. "Where there is green, there is always hope for something new to grow."''',
    
    '''One by one, Iris freed the remaining colors - Orange burst forth like autumn's final celebration, painting pumpkins, tigers, and the wings of monarch butterflies. Purple arrived like royalty, coloring violets, eggplants, and the majestic mountains at twilight. Pink emerged softly, blessing flamingos, cherry blossoms, and the first blush of dawn.

As the last colors danced into the world, something magical happened. They began to mix and blend, creating new shades no one had ever imagined. Sunsets became masterpieces of orange, pink, and purple. Spring meadows exploded with every possible combination. The world became more beautiful than even Iris's grandmother remembered.

Together, the colors rose into the sky and wove themselves into a magnificent arc - the world's first rainbow in a thousand years. It stretched from horizon to horizon, a promise of beauty everlasting.''',
    
    '''Iris returned home a hero, but she refused to take credit for the colors' return. "They were always there," she told everyone. "They were just waiting for someone to set them free."

Her grandmother held her tight, tears streaming down her wrinkled cheeks - tears that finally reflected the light in beautiful, colorful prisms. "You saw what others couldn't," she whispered. "You saw that colors belong to everyone."

From that day on, whenever rain and sun met in the sky, the colors would gather and create a rainbow - their way of saying thank you to the brave girl who freed them. And whenever children asked where colors came from, their grandparents would tell them the story of Iris, the girl with a colorful heart who brought beauty back to the world.

The End.'''
]

book = db.books.find_one({"title": "Colors of the World"})
if book:
    pages = book.get('pages', [])
    for i, text in enumerate(colors_story):
        if i < len(pages):
            pages[i]['text_content'] = text
    db.books.update_one(
        {"title": "Colors of the World"},
        {"$set": {"pages": pages, "_batch1_updated": datetime.now().isoformat()}}
    )
    print("✓ Colors of the World - 10 pages written")

# Book 3: Cooking Adventures with Chef Cat - Expand pages 1, 4, 8 (indexes 0, 3, 7)
cooking_updates = {
    0: '''In the cozy town of Whisker Valley, there lived an orange tabby cat named Chef Clementine who ran the most unusual restaurant anyone had ever seen. The Purrfect Plate served dishes that made taste buds dance and hearts warm, but what made it truly special wasn't just the food - it was the love Chef Clementine put into every single recipe.

Chef Clementine had learned to cook from her grandmother, a legendary chef who believed that the most important ingredient in any dish was kindness. "Food made with love tastes better than any gourmet meal made with indifference," Grandmother always said. Clementine took this lesson to heart.

Every morning, Chef Clementine would put on her crisp white chef's hat, tie her red apron strings into a perfect bow, and begin her culinary adventures. Today was extra special - she was about to teach the young kittens of Whisker Valley their very first cooking lesson.''',
    
    3: '''"First, we'll make something simple but wonderful," Chef Clementine announced, gathering the eager kittens around her large wooden table. "Friendship Cookies! The recipe has been in my family for generations, but the secret ingredient isn't in any cookbook."

The kittens watched with wide eyes as she measured flour, sugar, and butter. Little Mittens, the smallest kitten with white paws, stood on her tiptoes to see. "What's the secret ingredient?" she asked, her whiskers quivering with excitement.

Chef Clementine smiled mysteriously. "You'll discover it yourself by the time we're done." She showed them how to crack eggs without getting shells in the bowl, how to measure precisely, and how to mix the dough with gentle, circular motions. "Cooking isn't just about following recipes," she explained. "It's about putting your heart into every stir, every taste, every presentation."''',
    
    7: '''Something magical happened when the cookies came out of the oven. They weren't just delicious - they seemed to glow with a warm, golden light. The kittens gasped in amazement. These were the most beautiful cookies they had ever seen.

"But we followed the same recipe," said Whiskers, scratching his head with a confused paw. "Why do they look so special?"

Chef Clementine gathered the kittens close. "Because you made them together, with kindness in your hearts. You shared the work, you encouraged each other, you laughed together when Mittens got flour on her nose. That's the secret ingredient I mentioned - friendship and love. No recipe book can teach you that."

The kittens understood now. As they bit into their Friendship Cookies, they tasted not just butter and sugar, but the joy of creating something beautiful together.'''
}

book = db.books.find_one({"title": "Cooking Adventures with Chef Cat"})
if book:
    pages = book.get('pages', [])
    for idx, new_text in cooking_updates.items():
        if idx < len(pages):
            pages[idx]['text_content'] = new_text
    db.books.update_one(
        {"title": "Cooking Adventures with Chef Cat"},
        {"$set": {"pages": pages, "_batch1_updated": datetime.now().isoformat()}}
    )
    print("✓ Cooking Adventures with Chef Cat - 3 pages expanded")

# Book 4: Dinosaur Dentist - Expand pages 2, 5, 6 (indexes 1, 4, 5)
dinosaur_updates = {
    1: '''Dr. Flossy's waiting room was unlike any dental office you've ever seen. Instead of regular chairs, there were giant cushioned nests for the bigger dinosaurs and cozy leaf-lined seats for the smaller ones. The magazine rack held copies of "Prehistoric Smiles Monthly" and "Healthy Herbivore Teeth Today."

Young Rexy, a nervous Tyrannosaurus, sat in the corner trying to hide behind a fern plant. His mother had finally convinced him to visit after weeks of complaining about a toothache. "What if it hurts?" he whispered, his tiny arms shaking.

A friendly Triceratops named Trixie waddled over. "Don't worry," she said kindly, showing off her polished horns and gleaming smile. "Dr. Flossy is the gentlest dentist in all of Dinoland. She fixed my tooth last week, and I didn't feel a thing! She even gave me a prehistoric popsicle afterward."''',
    
    4: '''Dr. Flossy gently examined Rexy's enormous mouth with her specially designed tools - a mirror the size of a satellite dish and a pick that looked more like a garden rake. "Ah-ha!" she exclaimed, peering at a back molar. "I see the problem. You have a little cavity, probably from too many honey-covered pinecones."

Rexy's eyes went wide with worry, but Dr. Flossy patted his snout reassuringly. "It's a tiny fix, I promise. We'll clean it out, fill it up, and you'll be chomping again in no time."

True to her word, the procedure was quick and completely painless. Dr. Flossy used her special gentle-touch technique, developed specifically for nervous dinosaurs. She even told Rexy funny jokes about why Stegosauruses make terrible comedians (their jokes are too sharp!) to keep his mind off the work.''',
    
    5: '''After the filling was complete, Dr. Flossy taught Rexy the proper way to brush his 60 teeth. "It's all about technique," she explained, demonstrating on a giant model tooth. "Gentle circles, two minutes, twice a day. And don't forget to floss between those big chompers!"

She handed him a custom-made toothbrush with extra-long handles perfect for tiny T-Rex arms, and a special floss holder designed just for carnivores. "These are my inventions," Dr. Flossy said proudly. "Every dinosaur deserves to have tools that work for their unique body."

Rexy felt his confidence growing. Maybe dental care wasn't so scary after all. He practiced brushing right there in the office, and Dr. Flossy cheered him on with each successful stroke. "You're a natural!" she exclaimed.'''
}

book = db.books.find_one({"title": "Dinosaur Dentist"})
if book:
    pages = book.get('pages', [])
    for idx, new_text in dinosaur_updates.items():
        if idx < len(pages):
            pages[idx]['text_content'] = new_text
    db.books.update_one(
        {"title": "Dinosaur Dentist"},
        {"$set": {"pages": pages, "_batch1_updated": datetime.now().isoformat()}}
    )
    print("✓ Dinosaur Dentist - 3 pages expanded")

# Book 5: Flame's Courageous Journey - Full new story (10 pages)
flame_story = [
    '''In the heart of the Ember Mountains, where lava rivers flowed like ribbons of gold and fire flowers bloomed year-round, there lived a small dragon named Flame. Unlike the other dragons who breathed roaring torrents of fire, Flame could only produce tiny sparks and little puffs of smoke. The bigger dragons often laughed at his efforts.

"Look at Flame trying to light a campfire!" they would tease. "A candle could do better!"

Flame would hang his head and retreat to his favorite cave, where he'd watch his reflection in a pool of cooled lava. His scales were a beautiful sunset orange with ruby red tips, and his eyes sparkled like embers. But none of that mattered when he couldn't do the one thing dragons were supposed to do best.

"Maybe I'm just a broken dragon," he whispered to himself.''',
    
    '''One morning, Flame's grandmother, the wise Elder Ember, called him to her ancient cave at the mountain's peak. Her scales had turned silver with age, but her fire still burned bright and strong. "Little one," she said gently, "I see the sadness in your eyes. Tell me what troubles you."

Flame poured out his heart - how the other dragons made fun of him, how he felt useless, how he wished he could breathe fire like everyone else. Elder Ember listened patiently, her tail curled around him protectively.

"Flame," she said when he finished, "the biggest flames don't always come from the biggest dragons. True courage isn't measured in fire power - it's measured in the size of your heart. I'm sending you on a journey to discover what makes you truly special."

She pressed an ancient map into his claws, one that showed a path to the Valley of Mists.''',
    
    '''The Valley of Mists was a mysterious place where no dragon had ventured for generations. The elders said it was too cold for dragon fire, too wet, too dangerous. But the map showed something at the valley's center - the Heartstone, a legendary gem said to reveal one's true power.

With a deep breath (and a small puff of smoke), Flame set off on his journey. The path down from the Ember Mountains was steep and winding. For the first time in his life, Flame left the warmth of volcanic ground and felt cool grass beneath his claws.

It was strange and wonderful at the same time. Flowers he'd never seen before dotted the meadows - they weren't fire flowers, but they were beautiful in their own way. Butterflies danced around his head, curious about this small orange visitor.''',
    
    '''As Flame traveled deeper into the lowlands, he encountered his first challenge. A family of rabbits was trapped on a ledge, their burrow having collapsed behind them. The mother rabbit clutched her babies, too frightened to move.

"Please help us!" she cried when she saw Flame approaching. But then she noticed he was a dragon and cowered back in fear. "Oh no, a dragon! He'll burn us all!"

Flame felt hurt, but he understood their fear. "I won't hurt you," he said softly. "I'm not very good at breathing fire anyway. Let me help." 

Using his small but nimble claws, Flame carefully dug through the debris, creating a safe path for the rabbit family. It took hours of patient work, but finally they were free. The mother rabbit's eyes filled with grateful tears. "Thank you, kind dragon. You saved us."''',
    
    '''Word of the helpful dragon spread through the forest. As Flame continued his journey, more animals approached him for help - not because of his fire, but because of his gentle nature and willing heart. He helped a family of deer cross a rushing stream by creating stepping stones from loose rocks. He used his wings to shelter baby birds from a sudden rainstorm.

"You're not like other dragons," a wise old owl observed, watching Flame carefully place the last bird back in its nest. "You don't destroy - you protect. That's a rare gift."

Flame had never thought of it that way. All his life, he'd focused on what he couldn't do. He'd never considered that what he could do might be just as valuable - maybe even more so.''',
    
    '''The Valley of Mists lived up to its name. Thick fog rolled through the narrow canyon, so dense that Flame could barely see his own tail. The cold seeped into his scales, making him shiver. He understood now why dragons avoided this place - it was the opposite of everything they were used to.

But Flame pressed on. Somewhere in this fog was the Heartstone, and he was determined to find it. He moved slowly, carefully, using his keen hearing to navigate when his eyes failed him. Strange sounds echoed through the mist - dripping water, rustling leaves, and something else... a cry for help.

Following the sound, Flame discovered a young phoenix trapped beneath a fallen tree branch. Her usually brilliant feathers were dim and cold, her fire extinguished by the valley's dampness.''',
    
    '''"I can't reignite my flames," the phoenix cried, her voice weak. "Without my fire, I'll fade away completely. I've been trapped here for days."

Flame looked at the phoenix, then at his own tiny spark. He'd always thought his fire was useless, too small to matter. But maybe... just maybe... it was exactly what she needed.

He concentrated harder than he ever had before, focusing all his energy into his chest. Instead of a weak puff of smoke, he managed to produce a small but steady flame - not much bigger than a candle, but burning with all the warmth of his caring heart.

Gently, he touched his flame to the phoenix's feathers. At first nothing happened. Then, slowly, a spark caught. Then another. The phoenix's feathers began to glow, first orange, then gold, then brilliant white.''',
    
    '''With a burst of magnificent fire, the phoenix rose from the ground, her flames dancing brilliantly in the misty valley. She was more beautiful than anything Flame had ever seen. The fog around them actually retreated from her warmth.

"You saved me!" she exclaimed, circling Flame joyfully. "That tiny flame of yours was exactly what I needed - not a roaring blaze that would have overwhelmed my weakened spirit, but a gentle spark to reignite my own fire. You have a gift, young dragon."

Together, they flew through the valley, the phoenix's light guiding the way through the mist. And there, at the center of the valley, stood the Heartstone - a crystal that seemed to glow with inner fire, reflecting every color imaginable.''',
    
    '''Flame approached the Heartstone nervously. What would it reveal about him? Would it confirm what he'd always feared - that he was just a broken dragon?

As his claw touched the crystal surface, images swirled within. But they weren't images of fire and destruction. Instead, he saw himself - helping the rabbits, sheltering the birds, saving the phoenix. He saw the grateful faces of every creature he'd helped along the way.

"The Heartstone shows your true power," the phoenix explained softly. "Your gift isn't breathing fire, Flame. Your gift is compassion. While other dragons use their fire to destroy, you use your gentle heart to heal. That makes you the most powerful dragon of all."

For the first time in his life, Flame felt proud of exactly who he was.''',
    
    '''When Flame returned to the Ember Mountains, he was different. Not because he could suddenly breathe great flames - he still couldn't. But he walked with his head high and his eyes bright, no longer ashamed of his small spark.

The other dragons noticed the change immediately. "What happened to you?" they asked, amazed by his new confidence. Flame just smiled and told them about his journey, about the creatures he'd helped, about the phoenix he'd saved with his tiny flame.

From that day forward, Flame became known throughout the land not as the dragon who couldn't breathe fire, but as Flame the Brave - the dragon with the biggest heart. And whenever young dragons felt different or broken, they would seek out Flame, who would remind them that sometimes, our greatest weaknesses become our greatest strengths.

The End.'''
]

book = db.books.find_one({"title": "Flame's Courageous Journey"})
if book:
    pages = book.get('pages', [])
    for i, text in enumerate(flame_story):
        if i < len(pages):
            pages[i]['text_content'] = text
    db.books.update_one(
        {"title": "Flame's Courageous Journey"},
        {"$set": {"pages": pages, "_batch1_updated": datetime.now().isoformat()}}
    )
    print("✓ Flame's Courageous Journey - 10 pages written")

print("\n" + "=" * 80)
print("BATCH 1 SAVED SUCCESSFULLY!")
print("=" * 80)
