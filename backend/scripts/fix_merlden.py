#!/usr/bin/env python3
"""
Fix The Journey to Merlden:
1. Replace short placeholder pages (3, 5, 6, 8, 9, 10) with full content
2. Set is_published=True and hidden=False
"""
from pymongo import MongoClient

# Full content for the pages that have short placeholders
NEW_PAGE_CONTENT = {
    3: """Ariza closed her eyes and listened. Each voice said something different—warnings, invitations, riddles—and she realized that was the trick. The marsh wanted to see if they would panic, if they would doubt themselves. She took a slow breath and looked at the map. The golden flecks still drifted gently across its surface. "Don't listen to the words," she said to Dax. "Listen to the map." Dax nodded, and together they walked forward, ignoring the whispering voices. With every step, the mist thinned and the voices faded, until they emerged on the other side beneath a sky full of brilliant stars. Behind them, the marsh had gone silent. "The first test," Dax said softly. "The first of many," Ariza replied.""",
    
    5: """The Ember Peaks rose like jagged teeth against the orange sky. Heat shimmered from the rocks, and rivers of molten lava carved glowing paths down the mountainsides. At the base of the highest peak, an old stone bridge stretched across a chasm—the Bridge of Stars, the map called it. But when they arrived, there was no bridge. Only empty air and a drop so deep they couldn't see the bottom. "It only appears at twilight," Ariza read from the map's margin, squinting at the tiny golden letters. They waited as the sun sank lower, painting the sky in shades of violet and rose. And then, precisely as the last sliver of light touched the horizon, the bridge appeared—shimmering stones materializing one by one, suspended in nothing, leading across the impossible gap.""",
    
    6: """The Crystal Caves were everything the stories promised and more. Walls of translucent stone caught the torchlight and scattered it into a thousand rainbows. Colors danced across every surface—deep blues, fiery reds, greens like summer leaves. Ariza and Dax walked in awed silence until they heard the soft rumble of breathing. Around a bend in the passage sat a dragon. But this dragon was small—no larger than a large dog—with scales that shimmered like opals and eyes that sparkled with gentle curiosity. "Lost travelers?" the dragon asked. "Or seekers of Merlden?" "Seekers," Dax replied. The dragon smiled, showing small pearly teeth. "Then follow me. The caves shift and change, but I know every path. My name is Glimmer, and I will guide you through." And so they did.""",
    
    8: """The final stretch of their journey led them through the Valley of Echoes, where every word they spoke came back to them multiplied—not as mockery, but as encouragement. "You're almost there," their own voices whispered from the canyon walls. And then, at last, they saw it: Merlden. A great stone archway stood at the entrance, carved with symbols neither of them recognized but both somehow understood. The symbols spoke of welcome, of rest, of journeys ended and friendships forged. Beyond the arch, colorful tents dotted the valley floor, and the sound of music and laughter drifted on the breeze. Ariza took Dax's hand, and together they stepped through the archway into the place they had dreamed of for so long.""",
    
    9: """In the weeks that followed, Ariza and Dax discovered that Merlden was not a destination but a gathering—a place where travelers from every corner of the world came to share what they had learned. They met sailors who had crossed seas made of clouds, scholars who read languages written in starlight, and children who had tamed wild winds and ridden them like horses. Each person had a story, and each story was a gift. Ariza realized that the magic of Merlden wasn't in the place itself, but in the people who found their way there. Everyone who arrived brought something precious: not gold or jewels, but experiences, kindnesses, and the courage to share them.""",
    
    10: """The morning they left, the old woman from the archway gave them each a small stone that felt warm in their hands. "These will remind you," she said, "that home is not a place you leave behind. It travels with you, in your heart, wherever you go." The walk home was different from the journey out. The path seemed shorter, the obstacles fewer. Perhaps they had simply grown, Ariza thought. Perhaps they had become the kind of people who could face anything. When they finally crested the last hill and saw their village below—the wooden houses, the silver river, the smoke curling from familiar chimneys—they stood together in silence. Then Ariza smiled. "Same time next year?" she asked. Dax grinned. "Same time next year." THE END"""
}

def main():
    client = MongoClient('mongodb://localhost:27017')
    db = client['test_database']
    
    # Find the book
    book = db.books.find_one({'title': 'The Journey to Merlden'})
    if not book:
        print("ERROR: Book 'The Journey to Merlden' not found!")
        return
    
    print(f"Found book: {book['title']}")
    print(f"Current status: is_published={book.get('is_published')}, hidden={book.get('hidden')}")
    print(f"Pages: {len(book.get('pages', []))}")
    
    # Update the pages with new content
    pages = book.get('pages', [])
    for page_num, new_text in NEW_PAGE_CONTENT.items():
        if page_num <= len(pages):
            old_text = pages[page_num - 1].get('text', '')
            old_word_count = len(old_text.split()) if old_text else 0
            new_word_count = len(new_text.split())
            print(f"\nPage {page_num}: {old_word_count} words -> {new_word_count} words")
            pages[page_num - 1]['text'] = new_text
    
    # Update the database
    result = db.books.update_one(
        {'_id': book['_id']},
        {
            '$set': {
                'pages': pages,
                'is_published': True,
                'hidden': False,
                'status': 'published'
            }
        }
    )
    
    if result.modified_count > 0:
        print("\n" + "="*50)
        print("SUCCESS! The Journey to Merlden has been updated!")
        print("- 6 pages updated with full content")
        print("- is_published: True")
        print("- hidden: False")
        print("="*50)
        
        # Verify
        updated_book = db.books.find_one({'_id': book['_id']})
        print("\nVerification:")
        for i, page in enumerate(updated_book.get('pages', [])):
            text = page.get('text', '')
            word_count = len(text.split()) if text else 0
            print(f"  Page {i+1}: {word_count} words")
    else:
        print("ERROR: No changes were made!")

if __name__ == '__main__':
    main()
