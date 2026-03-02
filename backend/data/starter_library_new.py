# New Starter Library - 50 AI-Generated Images
# Categories: Characters, Scenes, Objects, Actions
# Art Styles: Watercolour, Cartoon/Pixar, Realistic Illustrated, Storybook Classic

STARTER_LIBRARY_PROMPTS = [
    # === CHARACTERS (15 images) ===
    # Watercolour style characters (4)
    {"id": "char_001", "name": "Adventure Girl Maya", "category": "character", "art_style": "watercolour",
     "prompt": "watercolour illustration of a cheerful young girl with curly brown hair, wearing explorer outfit with backpack, bright curious eyes, soft pastel colors, children's book style, white background"},
    {"id": "char_002", "name": "Friendly Dragon Pip", "category": "character", "art_style": "watercolour",
     "prompt": "watercolour illustration of a small cute baby dragon with green scales, big friendly eyes, tiny wings, playful expression, soft watercolor washes, children's book illustration, white background"},
    {"id": "char_003", "name": "Wise Owl Oliver", "category": "character", "art_style": "watercolour",
     "prompt": "watercolour illustration of a wise owl wearing tiny round glasses, soft brown feathers, kind expression, perched on branch, gentle watercolor style, children's book art, white background"},
    {"id": "char_004", "name": "Princess Lily", "category": "character", "art_style": "watercolour",
     "prompt": "watercolour illustration of a young princess with flowing golden hair, sparkly tiara, pink flowing dress, gentle smile, soft dreamy watercolors, fairy tale style, white background"},
    
    # Cartoon/Pixar style characters (4)
    {"id": "char_005", "name": "Robot Buddy Bolt", "category": "character", "art_style": "cartoon",
     "prompt": "3D Pixar style illustration of a friendly small robot with big expressive eyes, shiny blue metal body, cute antenna, warm smile, vibrant colors, children's animation style, white background"},
    {"id": "char_006", "name": "Superhero Sam", "category": "character", "art_style": "cartoon",
     "prompt": "3D Pixar style illustration of a young boy superhero with red cape, blue suit, confident heroic pose, big bright eyes, colorful and fun, children's animation style, white background"},
    {"id": "char_007", "name": "Magical Unicorn Star", "category": "character", "art_style": "cartoon",
     "prompt": "3D Pixar style illustration of a cute magical unicorn with rainbow mane, sparkly horn, big dreamy eyes, pastel colors, whimsical and magical, children's animation style, white background"},
    {"id": "char_008", "name": "Pirate Captain Penny", "category": "character", "art_style": "cartoon",
     "prompt": "3D Pixar style illustration of a young girl pirate captain with pirate hat, eye patch, confident smile, adventurous pose, vibrant colors, children's animation style, white background"},
    
    # Realistic illustrated characters (4)
    {"id": "char_009", "name": "Young Astronaut Alex", "category": "character", "art_style": "realistic",
     "prompt": "detailed realistic illustration of a young child astronaut in white spacesuit, helmet under arm, dreamy starry-eyed expression, soft lighting, inspiring and hopeful, children's book quality, white background"},
    {"id": "char_010", "name": "Forest Fairy Fern", "category": "character", "art_style": "realistic",
     "prompt": "detailed realistic illustration of a tiny forest fairy with delicate wings, green leafy dress, sitting on mushroom, magical glow, detailed fantasy art, children's book illustration, white background"},
    {"id": "char_011", "name": "Brave Knight Kit", "category": "character", "art_style": "realistic",
     "prompt": "detailed realistic illustration of a young knight in shining silver armor, holding small sword, brave determined expression, medieval fantasy style, children's book quality, white background"},
    {"id": "char_012", "name": "Ocean Mermaid Marina", "category": "character", "art_style": "realistic",
     "prompt": "detailed realistic illustration of a young mermaid with flowing aqua hair, shimmering tail, friendly wave, underwater magical feeling, detailed fantasy art, children's book style, white background"},
    
    # Storybook classic characters (3)
    {"id": "char_013", "name": "Teddy Bear Theodore", "category": "character", "art_style": "storybook",
     "prompt": "classic storybook illustration of a cuddly brown teddy bear with button eyes, red bow tie, soft fuzzy texture, warm nostalgic feel, vintage children's book style, white background"},
    {"id": "char_014", "name": "Bunny Rabbit Bella", "category": "character", "art_style": "storybook",
     "prompt": "classic storybook illustration of a sweet white bunny rabbit with pink ears, wearing blue dress, holding carrot, Beatrix Potter style, vintage children's book art, white background"},
    {"id": "char_015", "name": "Little Red Riding Hood", "category": "character", "art_style": "storybook",
     "prompt": "classic storybook illustration of Little Red Riding Hood, young girl in red hooded cape, carrying basket, innocent expression, fairy tale style, vintage children's book art, white background"},
    
    # === SCENES/SETTINGS (15 images) ===
    # Watercolour scenes (4)
    {"id": "scene_001", "name": "Enchanted Forest", "category": "scene", "art_style": "watercolour",
     "prompt": "watercolour illustration of an enchanted forest with tall magical trees, soft sunlight filtering through, glowing mushrooms, fairy lights, dreamy atmosphere, children's book background, soft colors"},
    {"id": "scene_002", "name": "Cozy Treehouse", "category": "scene", "art_style": "watercolour",
     "prompt": "watercolour illustration of a cozy wooden treehouse nestled in big oak tree, rope ladder, small windows with curtains, warm inviting glow, children's book style, soft pastel colors"},
    {"id": "scene_003", "name": "Sunny Beach", "category": "scene", "art_style": "watercolour",
     "prompt": "watercolour illustration of a beautiful sunny beach with soft waves, sandcastle, seashells, palm trees, bright cheerful day, children's book background, soft watercolor washes"},
    {"id": "scene_004", "name": "Magical Garden", "category": "scene", "art_style": "watercolour",
     "prompt": "watercolour illustration of a magical flower garden with oversized colorful flowers, butterflies, winding path, sparkles in air, whimsical children's book style, soft dreamy colors"},
    
    # Cartoon/Pixar scenes (4)
    {"id": "scene_005", "name": "Space Station", "category": "scene", "art_style": "cartoon",
     "prompt": "3D Pixar style illustration of a colorful space station interior, round windows showing stars, control panels with blinking lights, futuristic but friendly, children's animation background"},
    {"id": "scene_006", "name": "Underwater Kingdom", "category": "scene", "art_style": "cartoon",
     "prompt": "3D Pixar style illustration of magical underwater kingdom with coral castle, colorful fish, bubbles, seaweed gardens, bright vibrant colors, children's animation style background"},
    {"id": "scene_007", "name": "Candy Land", "category": "scene", "art_style": "cartoon",
     "prompt": "3D Pixar style illustration of whimsical candy land with lollipop trees, chocolate river, gummy bear mountains, cotton candy clouds, bright sugary colors, children's animation background"},
    {"id": "scene_008", "name": "Dinosaur Valley", "category": "scene", "art_style": "cartoon",
     "prompt": "3D Pixar style illustration of prehistoric valley with volcanoes, palm trees, dinosaur footprints, warm sunset colors, adventure feeling, children's animation style background"},
    
    # Realistic illustrated scenes (4)
    {"id": "scene_009", "name": "Castle Kingdom", "category": "scene", "art_style": "realistic",
     "prompt": "detailed realistic illustration of a grand fairy tale castle on hilltop, towers with flags, beautiful gardens, blue sky with fluffy clouds, fantasy kingdom, children's book quality background"},
    {"id": "scene_010", "name": "Winter Wonderland", "category": "scene", "art_style": "realistic",
     "prompt": "detailed realistic illustration of magical winter wonderland, snow-covered pine trees, frozen lake, northern lights in sky, cozy cottage with smoke from chimney, children's book style"},
    {"id": "scene_011", "name": "Pirate Ship", "category": "scene", "art_style": "realistic",
     "prompt": "detailed realistic illustration of a wooden pirate ship on sparkling ocean, billowing sails, treasure map flag, adventure awaits feeling, children's book quality, vibrant colors"},
    {"id": "scene_012", "name": "Jungle Adventure", "category": "scene", "art_style": "realistic",
     "prompt": "detailed realistic illustration of lush tropical jungle, ancient temple ruins, vines and exotic flowers, parrots in trees, adventure atmosphere, children's book background"},
    
    # Storybook classic scenes (3)
    {"id": "scene_013", "name": "Cozy Cottage", "category": "scene", "art_style": "storybook",
     "prompt": "classic storybook illustration of a cozy thatched cottage with flower garden, picket fence, smoking chimney, warm sunset, nostalgic fairy tale feeling, vintage children's book style"},
    {"id": "scene_014", "name": "Village Square", "category": "scene", "art_style": "storybook",
     "prompt": "classic storybook illustration of charming village square with cobblestones, market stalls, clock tower, friendly atmosphere, vintage children's book art, warm colors"},
    {"id": "scene_015", "name": "Grandma's Kitchen", "category": "scene", "art_style": "storybook",
     "prompt": "classic storybook illustration of warm cozy kitchen with wood stove, pie cooling on windowsill, checkered curtains, homey feeling, vintage children's book style, nostalgic"},
    
    # === OBJECTS (10 images) ===
    {"id": "obj_001", "name": "Magic Wand", "category": "object", "art_style": "cartoon",
     "prompt": "3D Pixar style illustration of a sparkly magic wand with glowing star tip, magical sparkles around it, purple and gold colors, children's animation style, white background"},
    {"id": "obj_002", "name": "Treasure Chest", "category": "object", "art_style": "realistic",
     "prompt": "detailed realistic illustration of an open wooden treasure chest overflowing with gold coins, jewels, sparkling gems, pirate treasure, children's book quality, white background"},
    {"id": "obj_003", "name": "Flying Carpet", "category": "object", "art_style": "watercolour",
     "prompt": "watercolour illustration of a magical flying carpet with intricate patterns, tassels, floating in air with sparkles, Arabian nights style, children's book art, white background"},
    {"id": "obj_004", "name": "Crystal Ball", "category": "object", "art_style": "realistic",
     "prompt": "detailed realistic illustration of a mystical crystal ball on ornate stand, swirling magical mist inside, purple glow, fortune teller style, children's book quality, white background"},
    {"id": "obj_005", "name": "Enchanted Book", "category": "object", "art_style": "storybook",
     "prompt": "classic storybook illustration of an ancient magical book with glowing pages, floating letters, leather bound with gold clasps, mysterious and wonderful, vintage style, white background"},
    {"id": "obj_006", "name": "Rocket Ship", "category": "object", "art_style": "cartoon",
     "prompt": "3D Pixar style illustration of a colorful cartoon rocket ship with round windows, fins, ready for launch, red and silver colors, children's animation style, white background"},
    {"id": "obj_007", "name": "Magic Potion", "category": "object", "art_style": "watercolour",
     "prompt": "watercolour illustration of a bubbling magic potion in glass bottle, purple liquid, cork stopper, magical steam rising, witch's brew style, children's book art, white background"},
    {"id": "obj_008", "name": "Golden Crown", "category": "object", "art_style": "realistic",
     "prompt": "detailed realistic illustration of a royal golden crown with sparkling jewels, rubies and diamonds, velvet cushion, fairy tale royalty, children's book quality, white background"},
    {"id": "obj_009", "name": "Pirate Map", "category": "object", "art_style": "storybook",
     "prompt": "classic storybook illustration of an old treasure map with X marks the spot, compass rose, sea monsters drawn in corners, aged parchment, vintage style, white background"},
    {"id": "obj_010", "name": "Magic Lamp", "category": "object", "art_style": "cartoon",
     "prompt": "3D Pixar style illustration of a golden genie lamp with magical smoke coming out, sparkles, Arabian style, wish-granting feel, children's animation style, white background"},
    
    # === ACTIONS/POSES (10 images) ===
    {"id": "act_001", "name": "Child Reading Book", "category": "action", "art_style": "watercolour",
     "prompt": "watercolour illustration of a happy child sitting cross-legged reading a colorful book, lost in imagination, soft lighting, peaceful scene, children's book style, white background"},
    {"id": "act_002", "name": "Kids Playing Together", "category": "action", "art_style": "cartoon",
     "prompt": "3D Pixar style illustration of diverse group of kids playing together, holding hands in circle, joyful expressions, friendship theme, bright colors, children's animation style, white background"},
    {"id": "act_003", "name": "Flying Through Clouds", "category": "action", "art_style": "realistic",
     "prompt": "detailed realistic illustration of a child flying through fluffy clouds with arms spread wide, pure joy expression, magical flying scene, dreamy atmosphere, children's book quality"},
    {"id": "act_004", "name": "Sleeping Under Stars", "category": "action", "art_style": "storybook",
     "prompt": "classic storybook illustration of a child peacefully sleeping under starry night sky, cozy blanket, crescent moon, peaceful bedtime scene, vintage children's book style"},
    {"id": "act_005", "name": "Dancing in Rain", "category": "action", "art_style": "watercolour",
     "prompt": "watercolour illustration of a joyful child dancing in rain with umbrella, splashing in puddles, rainbow in background, pure happiness, children's book art, soft colors"},
    {"id": "act_006", "name": "Hugging Pet", "category": "action", "art_style": "cartoon",
     "prompt": "3D Pixar style illustration of a child lovingly hugging a fluffy dog, both with happy expressions, heartwarming moment, warm colors, children's animation style, white background"},
    {"id": "act_007", "name": "Climbing Tree", "category": "action", "art_style": "realistic",
     "prompt": "detailed realistic illustration of an adventurous child climbing a big tree, determined expression, dappled sunlight, outdoor adventure, children's book quality illustration"},
    {"id": "act_008", "name": "Painting Art", "category": "action", "art_style": "watercolour",
     "prompt": "watercolour illustration of a creative child painting on easel, colorful paint splatters, artistic mess, focused happy expression, children's book style, soft colors"},
    {"id": "act_009", "name": "Blowing Bubbles", "category": "action", "art_style": "storybook",
     "prompt": "classic storybook illustration of a child blowing soap bubbles, rainbow bubbles floating in air, wonder and delight expression, vintage children's book style, soft lighting"},
    {"id": "act_010", "name": "Making Wish", "category": "action", "art_style": "cartoon",
     "prompt": "3D Pixar style illustration of a child blowing on dandelion seeds, eyes closed making wish, magical sparkles, hopeful moment, children's animation style, white background"},
]

# Will be populated with actual Cloudinary URLs after generation
STARTER_LIBRARY_GENERATED = []
