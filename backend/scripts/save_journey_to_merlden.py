"""
Save The Journey to Merlden - 6 new pages and publish
"""
from pymongo import MongoClient
from datetime import datetime, timezone

client = MongoClient("mongodb://localhost:27017")
db = client["test_database"]

# The 6 new pages content
new_pages = {
    2: '''Ariza traced the map's winding paths with her finger. Each route glowed faintly when touched, as if the parchment itself were alive and eager to guide them.

"Look here," she whispered, pointing to a small inscription near the bottom. It read: To those who seek with open hearts, Merlden reveals its truest parts.

Dax leaned closer, studying the intricate details. Mountains rose like dragon spines, rivers coiled like silver serpents, and tiny illustrations of creatures they'd never seen decorated the margins—winged rabbits, trees with faces, flowers that seemed to bloom before their eyes.

"This is no ordinary map," Dax said, his voice hushed with wonder.

"No," Ariza agreed, carefully rolling the parchment. "It's an invitation."

They shared a look that needed no words. Both knew what they must do. Tomorrow, at first light, they would leave everything familiar behind and follow the map to Merlden—wherever that magical place might be.

That night, neither could sleep. They lay in their beds, hearts racing with anticipation, imagining what adventures awaited beyond the hills they had always called home.''',

    4: '''Ariza closed her eyes and listened—not with fear, but with patience. Slowly, beneath the confusing chorus of whispers, she heard something else. A rhythm. A pattern.

"Dax, wait!" she said suddenly. "The voices aren't trying to confuse us. They're testing us!"

She began to hum a gentle melody, one her mother used to sing when she was small. The whispers paused, as if surprised. Then, impossibly, they joined in—harmonizing with her tune, transforming from eerie warnings into a beautiful, guiding song.

The mist parted before them like curtains on a stage, revealing a narrow stone bridge that hadn't been visible before. Flowers bloomed along its edges, and fireflies emerged to light their way.

"You figured it out," Dax breathed, amazed.

"The marsh wasn't our enemy," Ariza smiled. "It just wanted to be sure we'd face our fears with kindness instead of force."

Together, they crossed the bridge. Behind them, the marsh's whispers transformed into gentle well-wishes: "Safe travels... Brave hearts... Find what you seek..."''',

    5: '''Beyond the marsh rose the Ember Peaks—mountains that glowed like smoldering coals against the twilight sky. The air grew warm as they climbed, and the rocks beneath their feet pulsed with heat.

"According to the map, there's a passage through these mountains," Dax said, wiping sweat from his brow. "But I don't see any opening."

As if answering his words, a deep rumble shook the ground. From behind a massive boulder emerged a creature neither had expected—a phoenix, its feathers flickering with orange and gold flames.

They stumbled back in alarm, but the phoenix didn't attack. Instead, it tilted its head curiously and spoke in a voice like crackling fire.

"Few travelers reach the Ember Peaks," it said. "Fewer still have hearts pure enough to see me. Why do you seek Merlden?"

Ariza stepped forward bravely. "We're looking for answers. And for adventure. We want to see what lies beyond everything we've ever known."

The phoenix studied them for a long moment, then spread its magnificent wings. "Then follow me. I will show you the way."''',

    7: '''After days of traveling through landscapes more wondrous than their wildest dreams, Ariza and Dax finally reached the Forest of Glass Leaves. True to its name, every tree sparkled with leaves made of colored crystal—ruby reds, sapphire blues, and emerald greens that chimed like tiny bells in the breeze.

"It's like walking through a dream," Ariza whispered, reaching up to touch a delicate amethyst leaf.

The forest was filled with gentle creatures who watched them pass with curious, friendly eyes. Deer made of starlight grazed in clearings, while squirrels with jeweled tails chattered greetings from the branches above.

But as beautiful as it was, Dax noticed something troubling. "Ariza, look—the path splits here."

Three trails wound through the crystal trees, each leading in a different direction. And for the first time since they'd begun their journey, the map offered no guidance. The routes remained dark, unglowing.

"We have to choose for ourselves," Ariza realized.

Dax nodded slowly. "Which means we have to trust our instincts."''',

    8: '''They chose the middle path—the one that felt right in their hearts, even though it was the least impressive of the three. It didn't sparkle or promise treasures. It simply wound forward, honest and unadorned.

As they walked, the crystal forest gradually transformed into ordinary woodland, then into rolling meadows dotted with wildflowers. The temperature softened, the air sweetened, and somewhere ahead, they heard the sound of distant laughter and music.

"We're close," Dax said, his voice thick with emotion. "I can feel it."

Ariza squeezed his hand. They had been through so much together—the marsh's riddles, the phoenix's test, the forest's impossible choice. Each challenge had taught them something about themselves, about courage, about trust.

The path crested a small hill, and there, spread below them in a valley bathed in golden afternoon light, was their destination.

An archway of living vines marked the entrance, and carved into its wooden frame were words that made their hearts soar:

"Welcome to Merlden—where all journeys find their meaning."''',

    9: '''Years later, Ariza and Dax would tell their own children about the journey to Merlden. They'd speak of the Whispering Marsh and how kindness conquered fear, of the phoenix who valued pure hearts over powerful ones, of the Forest of Glass Leaves and the courage it took to trust themselves.

But the part of the story they loved telling most was this: Merlden wasn't just waiting for them at the end of a map. Merlden was in every step they took, every challenge they faced together, every moment they chose wonder over worry.

The map still hung on Ariza's wall, now faded and ordinary-looking. But sometimes, on quiet evenings when the wind rustled just right, her children swore they could see tiny golden flecks dancing across its surface.

"Does that mean the magic is still there?" they would ask.

And Ariza would smile, just as her parents had smiled at her long ago.

"The magic was never in the map," she'd say. "It was always in you. You just have to be brave enough to find it."

The End.'''
}

# Get the book
book = db.books.find_one({"title": "The Journey to Merlden"})
if book:
    pages = book.get('pages', [])
    
    # Update the 6 empty pages (indexes 2, 4, 5, 7, 8, 9)
    for idx, text in new_pages.items():
        if idx < len(pages):
            pages[idx]['text_content'] = text
    
    # Update database with new content and publish
    db.books.update_one(
        {"title": "The Journey to Merlden"},
        {"$set": {
            "pages": pages,
            "is_published": True,
            "publish_status": "published",
            "hidden": False,
            "status": "published",
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "_batch_updated": "journey_to_merlden_6pages"
        }}
    )
    
    # Verify
    updated = db.books.find_one({"title": "The Journey to Merlden"})
    total_words = sum(len((p.get('text_content', '') or '').split()) for p in updated.get('pages', []))
    
    print("=" * 60)
    print("THE JOURNEY TO MERLDEN - SAVED AND PUBLISHED")
    print("=" * 60)
    print(f"Total words: {total_words}")
    print(f"is_published: {updated.get('is_published')}")
    print(f"publish_status: {updated.get('publish_status')}")
    print(f"hidden: {updated.get('hidden')}")
    print("\n✓ Book is now LIVE in the library!")
