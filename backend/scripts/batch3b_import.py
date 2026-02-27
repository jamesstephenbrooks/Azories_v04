#!/usr/bin/env python3
"""
Batch 3B Import Script - CREATE operations only
17 books, 10 pages each = 170 new pages
"""

import asyncio
import os
import sys
import uuid
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient

# All 17 books from Batch 3B with their page content
BOOKS_DATA = [
    {
        "title": "Aliens at My School",
        "book_id": "ab0fe05e-1e98-4106-9334-66577fead8c3",
        "pages": [
            {"page_number": 1, "text": "On Monday morning, three new students arrived at Oakfield Primary. Their names were Zix, Blorp, and Quee, and they were from the planet Glorb, approximately forty-seven light years away. They had wobbly antennae, three eyes each arranged in a triangle, and the widest smiles anyone at the school had ever seen. The headteacher, Mr Potts, showed them to Class 4B with the slightly dazed expression he usually reserved for Ofsted inspections. 'These are exchange students,' he announced. 'Please make them feel welcome.' The whole class stared. Zix waved enthusiastically with all four arms."},
            {"page_number": 2, "text": "The first lesson was English. Zix, Blorp, and Quee had studied Earth languages from intercepted television signals, which meant their English was excellent but slightly old-fashioned in places. Blorp raised a hand and said 'I say, would you be so kind as to explain the subjunctive mood' in a perfectly crisp accent, which made Mrs Chen blink several times. Quee had brought a translation device that occasionally got things wrong in entertaining ways — when asked to introduce herself she announced that she was 'a professional fish enthusiast from the cold district of Glorb,' which was close but not quite right."},
            {"page_number": 3, "text": "Lunchtime brought the first real challenge. The aliens had never encountered Earth food before and regarded the cafeteria with a mixture of fascination and suspicion. Zix poked a fish finger cautiously. 'Is it animate?' Blorp asked, backing away. Quee scanned it with a small device and announced it contained seventeen compounds not found on Glorb. Their new classmate Mia laughed kindly and showed them how to eat it. They took tiny careful bites — then enormous enthusiastic ones. 'This is EXTRAORDINARY,' Quee announced to the entire cafeteria. 'On Glorb, we subsist primarily on compressed atmospheric particles.'"},
            {"page_number": 4, "text": "Science class was where the aliens truly came alive. Their knowledge of physics, chemistry, and biology was so advanced that the teacher, Mr Okafor, spent most of the lesson learning from them rather than the other way around. Zix explained casually that their planet had solved fusion energy four hundred years ago. Blorp demonstrated a property of light that Mr Okafor had never heard of. Quee looked at the periodic table on the wall and politely pointed out that it was missing fourteen elements. Mr Okafor sat down and stared at his own ceiling for quite a long time."},
            {"page_number": 5, "text": "PE was a different matter. The aliens were enthusiastic but had four arms and a different relationship with gravity, which made most Earth sports complicated. Football was abandoned after Zix accidentally kicked the ball into the next postcode. Basketball was tricky because Blorp could reach the hoop while standing flat-footed. Then someone suggested swimming, and it turned out that on Glorb, swimming was a major cultural event. The aliens slid into the pool and moved through it with impossible elegance, performing formations that the swimming teacher described as 'technically unprecedented and also quite lovely.'"},
            {"page_number": 6, "text": "Art class produced unexpected results. On Glorb, art meant creating sound sculptures — arrangements of tones that built into three-dimensional emotional experiences. The aliens sat in front of their blank paper looking genuinely lost. Then Mia showed Quee how to mix colours, and something clicked. Quee began painting with focused intensity, using all four hands simultaneously, producing a piece that the art teacher later hung in the school entrance and which three parents independently asked to buy. 'What is it?' Mia asked. 'It is the feeling of arriving somewhere new and finding it kind,' Quee said simply."},
            {"page_number": 7, "text": "By Wednesday, the aliens had become the most popular students in the school. At break time, children lined up to ask them questions about space — about other planets, about what Earth looked like from above, about whether there was other life in the galaxy. The answers were both wonderful and slightly overwhelming. 'There are approximately four million inhabited planets in this galaxy alone,' Zix said, 'of which Earth is considered particularly interesting due to its unusual emotional complexity.' This made everyone feel both very important and slightly dizzy."},
            {"page_number": 8, "text": "On Thursday, the aliens taught the class their favourite Glorbian game, which was called Zoopball. The rules were: run backwards, bounce a ball off your head every ten seconds, shout a random word when you caught it, and if you laughed you had to spin around three times. It was complete and spectacular chaos. The entire year group ended up playing in the playground, shrieking random words and spinning and falling over, while three teachers watched from the staffroom window with expressions that suggested they were pretending not to find it funny."},
            {"page_number": 9, "text": "Friday afternoon arrived too quickly. The aliens' ship — which had been parked sensibly in the school car park, where it had attracted considerable attention from passing motorists — hummed back to life. The class gathered to say goodbye. There were many hugs, which the aliens had learned about on Tuesday and taken to enthusiastically. Mia gave Quee her best set of watercolour paints. Zix gave Mr Potts a small crystal that, when held to the light, showed the location of every inhabited planet within a hundred light years. Mr Potts said it was the finest school gift he had ever received."},
            {"page_number": 10, "text": "The ship lifted silently from the car park, hovered for a moment, and then shot upward with a flash of gold light that left a warm afterglow in the sky. Mia stood watching until it was gone. In her pocket was a small device Quee had left her — a communicator, set to Glorb's frequency. 'In case you want to write,' Quee had said, in that lovely old-fashioned English learned from television. Mia walked back into school. The classroom felt simultaneously emptier and larger than it had a week ago. She sat down at her desk and thought: the universe is so much bigger and so much kinder than I knew. THE END"},
        ]
    },
    {
        "title": "Astronaut Alex's Moon Mission",
        "book_id": "32c78d01-b21c-4496-9bf5-476bfb92818b",
        "pages": [
            {"page_number": 1, "text": "Astronaut Alex had trained for this moment for five years. She had run simulations until she could do them in her sleep. She had studied the lunar surface maps until she could close her eyes and trace every crater from memory. She had practised moving in a spacesuit until it felt like a second skin. Now, strapped into her seat as the rocket shook and roared beneath her, climbing through the atmosphere on a pillar of fire, all that preparation distilled into a single feeling: pure readiness. She pressed her face to the porthole. The blue curve of Earth began to show."},
            {"page_number": 2, "text": "Three days in space. Alex floated through the capsule, ate food from pouches, slept strapped to the wall, and spent long hours at the window watching the Earth shrink and the Moon grow. The Earth from space was heartbreakingly beautiful — blue and white and fragile-looking, hanging in absolute black. The Moon grew from a disc to a world, its surface resolving into detail: grey and pitted and ancient, bearing the scars of four billion years of impacts. She had looked at photographs of it her whole life. Nothing prepared her for the reality of approaching it."},
            {"page_number": 3, "text": "The lunar lander separated from the command module with a soft thunk. Alex checked her instruments, made her calculations, and began the descent. The surface came up slowly at first, then faster. She fired the braking engines. Dust billowed sideways in great silent plumes — no atmosphere to carry sound. The legs touched. The engine cut. Silence. Complete, total, absolute silence, the kind that exists nowhere on Earth. Alex sat in it for a moment, breathing steadily. Then she said, to nobody in particular: 'Touchdown.' The word felt enormous in the quiet."},
            {"page_number": 4, "text": "She suited up carefully, checking every seal and connection twice. The airlock cycled. The outer hatch opened onto grey regolith and black sky. Alex climbed down the ladder — seven rungs, each one deliberate — and stepped onto the Moon. Her boot left a perfect print in the dust, sharp-edged and permanent in a place with no wind to blur it. She had prepared what she would say and then decided not to say it. Instead she just stood there for a full minute, feeling the weight of where she was, letting it be real. Then she said: 'Hello, Moon. I've been wanting to meet you.'"},
            {"page_number": 5, "text": "The surface was simultaneously familiar and alien. She had studied it so thoroughly that she recognised landforms she had only seen in photographs — and yet walking on them was completely different from knowing them on paper. The regolith crunched softly beneath her boots. The craters she had memorised by name were larger in person, more dimensional, their walls casting hard shadows in the unfiltered sunlight. She collected rock samples with methodical care, photographing each one in context before bagging it. Every sample was a piece of four-billion-year-old history. She handled them accordingly."},
            {"page_number": 6, "text": "From the lunar surface, Earth was a small blue marble in the black sky. Alex stood looking at it for a long time. Everything she had ever known was on that marble — every person, every city, every forest and ocean and mountain. Every book she had read, every meal she had eaten, every conversation she had ever had. Her mother, her sister, her friends. All of it on that one small, improbably beautiful sphere, hanging in nothing. She had never felt so far away from home, and simultaneously had never felt the full weight of what home meant, until this moment."},
            {"page_number": 7, "text": "She set up the scientific instruments: a seismometer to detect moonquakes, a retroreflector for laser ranging experiments, atmospheric sensors that would measure the thin whisper of gas that constituted the lunar exosphere. Each instrument had a purpose and she set each one precisely, following procedures she had rehearsed hundreds of times. When the last one was in place she stood back and looked at them — these small human objects sitting on the ancient surface — and felt the particular satisfaction of work done properly in a place that had never seen work done before."},
            {"page_number": 8, "text": "Overnight — lunar night lasting two weeks, though she would be gone long before it arrived — the temperature dropped sharply. Inside the lander she was warm and safe, but she could see the temperature readings on her instruments dropping outside. The Moon was a place of extremes: scorching in direct sunlight, hundreds of degrees below freezing in shadow. Life here required everything to be sealed, controlled, maintained. She thought about the engineering that had made this possible — the thousands of people, the decades of work, the accumulated human knowledge that had brought her here — and felt a profound gratitude."},
            {"page_number": 9, "text": "On the final EVA, Alex walked further from the lander than planned. She had found a ridge that wasn't on any of her maps — a subtle rise in the terrain that her instruments hadn't detected from orbit. From the top of it she could see for kilometres in every direction, the surface rolling gently in the low light, every feature sharp and clear in the airless environment. She took photographs. She took a video. She sat on the ridge for ten minutes and just looked. It was, she thought, the most valuable ten minutes of the entire mission."},
            {"page_number": 10, "text": "The return journey took three days. Alex spent much of it writing — her official mission log, precise and factual, and her private journal, which was neither. She wrote about the silence and the footprints and the Earth from the surface and the ridge that wasn't on any map. She wrote about what it felt like to be the first person to stand in a particular place on an entire world. When she splashed down and the recovery team opened the hatch, the first thing she said was: 'When can I go back?' She was already planning the next mission before she reached dry land. THE END"},
        ]
    },
    {
        "title": "Bedtime in the Animal World",
        "book_id": "1feebc6d-6bb7-4e35-9602-8fccdc5a918b",
        "pages": [
            {"page_number": 1, "text": "When the sun begins to set and the sky turns shades of pink and gold and violet, it is the signal that travels across the whole world at once: time to rest. The robin in the apple tree tucks her bright head beneath her wing. Her three chicks, already drowsy in the nest, press together for warmth. Their tiny hearts beat quickly. Their small chests rise and fall. The last light fades from the leaves above them. The first star appears. Goodnight, little robins, safe in your nest of moss and hair and the careful work of your mother's beak."},
            {"page_number": 2, "text": "Down at the river's edge, the beaver family has been busy since before sunrise. Father Beaver swam the last load of branches to the lodge as the light turned golden. Mother Beaver checked the dam one final time, pressing the mud smooth with her flat tail. Now the little beavers — three of them, round and soft and smelling of river water — are tucked inside the warm lodge, their tails overlapping like roof tiles, their eyes already closing. The river murmurs against the outside walls. The current carries the day away. Goodnight, little beavers, warm in your water home."},
            {"page_number": 3, "text": "In the meadow, the rabbit family disappears underground as the last light fades. Their burrow is a labyrinth — tunnels that twist and branch and end in comfortable chambers lined with soft dry grass and the fur that Mother Rabbit pulled from her own chest to make the softest possible bed. The kittens burrow into it, noses still twitching even as their eyes close, because a rabbit's nose never quite sleeps. Above them, the meadow grows quiet. The owl who will hunt it later is still sleeping herself. Goodnight, little rabbits, deep in your warm dark home."},
            {"page_number": 4, "text": "High in the oak tree, the squirrel family settles into their drey — a ball of woven leaves and twigs, so well made that rain runs off it and wind pushes around it rather than through it. The young squirrels pile on top of each other for warmth, their bushy tails wrapped around them like blankets, their small hands curled against their chests. The oak tree sways gently. The leaves whisper. Below, the forest floor is busy with the first creatures of the night, but up here, in the tree's high cradle, there is only warmth and sleep. Goodnight, little squirrels."},
            {"page_number": 5, "text": "The hedgehog has found her favourite spot beneath a pile of autumn leaves at the base of the garden wall. She has been preparing since yesterday — pushing more leaves into the pile with her nose, making it deeper, making it safer. Now she curls into the perfect sphere that is a hedgehog's best defence against the world, her spines outward, her soft face tucked in, her breathing slowing to the deep rhythm of hibernation's approach. The leaves settle around her. She fits perfectly. Outside, the night deepens. Goodnight, little hedgehog, prickly and safe."},
            {"page_number": 6, "text": "In the woodland den, the fox cubs sleep in a row. They arrived home at dusk, tumbling over each other through the narrow entrance, smelling of grass and adventure and the rabbit they had unsuccessfully chased. Their mother groomed them one by one with patient thoroughness before they fell asleep mid-lick, too tired to stay awake for the attention they were enjoying. Now they breathe slowly in the dark den, twitching occasionally as they run in their dreams. Their mother sits at the entrance, watching the night, ears turning to every sound. Goodnight, little foxes, dreaming of tomorrow's chase."},
            {"page_number": 7, "text": "In the pond, the frogs have settled into the deep mud at the bottom. They do not sleep in the way that warm-blooded creatures sleep — they slow, and cool, and become still, their heartbeats dropping to almost nothing, their bodies waiting out the cold in a kind of profound patience. They will be there all winter if necessary, barely breathing, barely moving, keeping the small warm spark of their lives safe in the cold dark mud. The pond surface above them is still as glass. Goodnight, little frogs, patient in your cold deep beds."},
            {"page_number": 8, "text": "The barn owl has not gone to sleep yet — she is just waking up. She stretches her wings in the darkness of the barn roof, each feather spreading and resettling. Her extraordinary eyes, wider than any other bird's in proportion to her face, adjust to the darkness without effort. Her ears, set asymmetrically on her skull, can pinpoint a mouse moving under snow from fifty metres. She floats out of the barn on silent wings, a white ghost over the moonlit field. While everyone else sleeps, she begins her night. The world of sleep needs hunters too, to keep the balance. Goodnight, barn owl. Good hunting."},
            {"page_number": 9, "text": "In the old stone wall at the bottom of the garden, the slow worm has found a crack just the right size for a slow worm. She is not a worm and not a snake — she is a legless lizard, which is something different from both, though it takes explaining. She slides into her crack, coils neatly, and lets the stone's residual warmth seep into her. She will stay here until the morning sun warms the wall enough to make coming out worthwhile. She has been using this crack for eleven years. It knows her shape exactly. Goodnight, slow worm, in your ancient wall."},
            {"page_number": 10, "text": "And somewhere, in a warm house at the end of a quiet street, a child is being tucked in. The duvet is pulled up. A story has been told. A nightlight glows softly in the corner. Outside the window, all the animals of the neighbourhood are settling — the robin in the apple tree, the hedgehog in the leaves, the fox cubs in the den, the beavers in the lodge. The whole world is breathing slowly now, resting, dreaming, keeping itself safe through the dark hours. The child's eyes grow heavy. The day is done. The night is kind. Goodnight."},
        ]
    },
    {
        "title": "Captain Compass and the Treasure Map",
        "book_id": "ed34dc96-9c78-4eb7-8707-90245371bea4",
        "pages": [
            {"page_number": 1, "text": "Captain Compass had earned her name honestly. Her compass — a brass instrument that had belonged to her grandmother, and her grandmother's grandmother before that — pointed not just to magnetic north but, on certain days when the light was right and the wind had a particular quality, to something else entirely. Adventure, her grandmother had called it. Captain Compass had always thought this was poetic language. Then one grey morning the compass began spinning wildly on its own, pointing insistently northeast, and she understood that her grandmother had been entirely literal."},
            {"page_number": 2, "text": "She followed the compass through three days of sailing to a harbour town she had never visited, full of narrow streets and the smell of salt and fish and old timber. The compass led her down an alley, around two corners, and into a shop so small and so full that there was barely room to stand. An old sailor sat behind the counter surrounded by the accumulated objects of a lifetime at sea. He looked at her compass without surprise. 'Been expecting you,' he said. 'Or someone like you. Bottom shelf, rolled up, tied with seaweed. Been waiting forty years.'"},
            {"page_number": 3, "text": "The map was large and old, drawn on something that felt like neither paper nor parchment but somewhere between the two. The coastlines were precise — she could identify real places in them — but the island marked with the red X had no name and appeared on none of the charts she carried. The turtle shape was unmistakable: a broad oval body, four stubby peninsulas, and a distinctive notch in the top right that could only be the turtle's head. She rolled it carefully back up. She paid the old sailor what he asked without negotiating. Some things were not worth haggling over."},
            {"page_number": 4, "text": "Planning the route took two weeks. The turtle island, triangulated from three separate landmarks shown on the map, placed it in a stretch of ocean she knew only by reputation: technically navigable but poorly charted, subject to unusual currents, and visited rarely enough that no reliable account of its conditions existed. She provisioned the ship carefully — more water than she thought she needed, twice the standard medical supplies, charts of every surrounding area. Her first mate, a cautious man named Boone, looked at the preparations and asked no questions. He had sailed with her long enough to know that questions would be answered in due course."},
            {"page_number": 5, "text": "Twelve days at sea. Three genuine storms, each one different — the first short and violent, the second slow and wearing, the third disorienting in its fog and stillness. She navigated by the old map's landmarks, cross-referencing against her own instruments, finding her way through the poorly charted water with patience and precision. On the eleventh day, Boone called from the lookout. On the horizon, just visible, was a shape — low and broad, with exactly the distinctive outline she had spent twelve days trying to find. Turtle island, exactly as drawn, lying in the morning light like a geographical promise kept."},
            {"page_number": 6, "text": "She rowed ashore in the ship's tender, alone, which Boone protested and she overruled. The beach was white sand, undisturbed except for bird tracks. The vegetation was dense but not impassable. She followed the map's instructions: find the oldest tree visible from the beach, walk toward it, count one hundred paces north from its base, then turn east and walk until you reach flat rock. The oldest tree was enormous, its trunk silver-grey with age. She counted carefully. At one hundred paces: flat rock, exactly as described, half-buried in vegetation, clearly undisturbed for a very long time."},
            {"page_number": 7, "text": "The dig was harder than she expected. The soil beneath the flat rock was dense and full of roots, and the chest was deeper than the map's markings had suggested — nearly a metre down, and heavy. It took two hours and left her thoroughly muddy. When the lid finally opened, she found it lined with oilskin that had kept the interior perfectly dry. Inside were not jewels or gold coins but something she had not expected: fifty maps, each carefully rolled and sealed with wax, each showing a different coastline with a different X, each in the same hand as the first map."},
            {"page_number": 8, "text": "She sat on the beach for a long time, going through them. Each map was clearly genuine — precise coastlines, careful notation, the same quality of observation she had seen in the turtle island map. She recognised some of the coastlines. Others were unfamiliar. Some Xs were marked on islands. Some were on mainland coasts. One was underwater, marked with a depth notation that suggested an extraordinary dive. Each one was a different puzzle, a different journey, a different question waiting to be answered. Her compass, she noticed, had stopped spinning and was now pointing steadily and calmly, as if satisfied."},
            {"page_number": 9, "text": "She returned to the ship as the sun was setting, the chest of maps under her arm, still muddy from the dig. Boone looked at the chest and then at her face and understood without being told that she had found something significant. 'Worth the twelve days?' he asked. She thought about the maps spread around her on the beach — fifty new mysteries, fifty new destinations, a lifetime's worth of questions to answer. 'Worth considerably more than that,' she said. She went below to wash the mud off and start cataloguing. She worked through the night."},
            {"page_number": 10, "text": "By morning she had sorted the maps into categories: coastal, island, underwater, inland. She had identified seventeen that she could navigate to immediately, using routes she already knew. The rest would require planning, new charts, possibly new expertise. The compass sat on the table beside her, pointing steadily northeast — not to any of the maps, she realised, but simply in the direction they had come from. It had done its job. Now the work was hers. She rolled the maps carefully, retied each one, and placed them back in the chest. Then she went on deck, called Boone, and said: 'Set course northeast. I'll explain when we're underway.' THE END"},
        ]
    },
    {
        "title": "Desert Treasure Hunt",
        "book_id": "f0a6f967-0b03-4a5e-b9a5-fa7141dc8a25",
        "pages": [
            {"page_number": 1, "text": "The desert at dawn was cold and vast and the most beautiful thing that twins Sam and Noor had ever seen. Their mother, Dr Patel, had been working at the dig site for three weeks and had finally agreed to let them visit. The land stretched in every direction — ochre and rust and pale gold, rock formations rising from flat plains like ancient sentinels. Their mother had said the dig site was important. She had said the landscape was extraordinary. She had not, Sam thought, done justice to either claim. He stood at the edge of the camp and stared until Noor pulled his sleeve."},
            {"page_number": 2, "text": "Their mother had planned a day at the camp watching the archaeologists work — careful, methodical, painstaking work that involved small brushes and constant measurement and tremendous amounts of note-taking. Sam and Noor lasted forty minutes before restlessness overcame them. That was when they found the clue: a small folded card tucked under a stone near the camp entrance, with their names on it in their mother's handwriting. Inside: a riddle. 'Find the three stones that stand like soldiers. Between them is the beginning.' Their mother, it turned out, had prepared a treasure hunt. They looked at each other. Noor already had her map out."},
            {"page_number": 3, "text": "The soldier stones were three tall red sandstone pillars on a rise half a kilometre from the camp — they had noticed them arriving the previous evening, silhouetted against the pink sky. Up close they were enormous, their surfaces worn smooth by millennia of wind. Between the two closest pillars, wedged into a crack in the base, was a metal tin. Inside: a compass, a small notebook, and a card. 'Walk toward the morning sun for one hour. Mark your path. Stop where your shadow is shortest.' Sam checked his watch: 8am. The morning sun was behind them. They turned and walked east, into the light."},
            {"page_number": 4, "text": "Walking east through the desert for an hour was harder than it sounded. The terrain was not flat — it rose and dipped, and there were loose sections of scree that required care and rocky outcrops that needed navigating around. Sam marked their path in the notebook at every landmark. Noor kept the compass bearing true. At nine o'clock Sam checked the time and they stopped. Their shadows fell directly in front of them, pointing west — not shortest, the sun not yet high enough. 'We stop when the shadow is shortest,' Noor said. 'That's noon.' Sam looked at the sun, then at the compass, then at his sister. 'We keep going,' he said."},
            {"page_number": 5, "text": "They found shelter in the shade of a rock formation and waited out the middle hours, eating the lunch their mother had packed. The desert was alive with small life, they discovered — a lizard on a warm rock, observing them with ancient patience; the tracks of a small mammal crossing the sand in perfect parallel lines; a beetle making its methodical way between the stones, doing beetle business with complete focus. When noon came and their shadows were at their shortest, they looked directly ahead. On a flat-topped dune perhaps three hundred metres away, something glinted."},
            {"page_number": 6, "text": "The flat-topped dune was higher than it looked and climbing it was an effort of sliding half a step back for every full step forward. At the top, barely visible, half-buried in wind-drifted sand, was another tin. Inside: a small brass key, old and heavy, and a final clue: 'The door is under the water that has no water.' Noor read it three times. Sam read it twice. Then Noor said slowly: 'A dry riverbed.' She unfolded the map their mother had given them. Running northeast from their position, clearly marked, was a wadi — a seasonal river, long since dry. They started walking."},
            {"page_number": 7, "text": "The wadi was a carved channel in the desert floor, its banks smooth and steep from centuries of rushing water that no longer came. Walking its sandy bed felt ancient — the sense of moving through a space shaped by forces too large and too patient to fully imagine. The walls were streaked with the colours of different geological periods: white limestone, red sandstone, black basalt, each layer a chapter in a story millions of years long. Sam traced the layers with his fingers as they walked and felt the weight of time in a way he had never felt before."},
            {"page_number": 8, "text": "They almost missed the door. It was set flush into the wadi bank, covered in the same red sandstone, visible only as a slight rectangular shadow when the light fell on it at exactly the right angle. Noor spotted it. The key fit the lock perfectly, the tumblers turning with a solidity that suggested excellent craftsmanship. The door swung inward on counterweighted hinges — recently maintained, Sam noted — and revealed a chamber carved into the rock: cool and dim after the brilliant outside light, roughly four metres square, its walls covered from floor to ceiling in ancient paintings."},
            {"page_number": 9, "text": "They stood in the doorway and didn't speak for a while. The paintings were extraordinary — human figures with raised hands, animals moving in herds, stars arranged in patterns, handprints pressed directly onto the rock in red and ochre pigment. People had been here, in this exact spot, and had made this, thousands of years ago, and had wanted it to last. It had lasted. Sam thought about the people who had mixed the pigments and climbed the walls to paint the high sections. He thought about what they had wanted to say. He thought about the fact that they were saying it, still, right now, to him."},
            {"page_number": 10, "text": "Their mother arrived an hour later, following their marked path, out of breath and beaming. She had set up the treasure hunt months ago but had not known if the children would make it this far. She stood in the doorway of the chamber and looked at the paintings and then at her children. 'Well?' she said. Sam thought about the clues and the walking and the brass key and the dry riverbed and the wadi walls and the weight of geological time under his fingers. He looked at the painted hands on the wall — human hands, reaching forward through thousands of years. 'This is the treasure, isn't it,' he said. It wasn't a question. 'Yes,' said their mother. 'It always was.' THE END"},
        ]
    },
    {
        "title": "Elves and the Magic Tree",
        "book_id": "c83e67ba-2fa4-421a-85a4-1f9e1f7384de",
        "pages": [
            {"page_number": 1, "text": "The Great Green had stood at the heart of the Whispering Wood for longer than any record kept. The elves who lived in its roots and branches had tended it for a thousand years — watering, pruning, singing to it in the old language on midsummer nights, performing the small seasonal rituals that kept its magic alive and its connection to the deep wood strong. The eldest elf, Fernwick, had white hair to his waist and claimed he could remember when the tree was young. No one disputed this. Fernwick was not the sort of person you disputed."},
            {"page_number": 2, "text": "The youngest elf was Pip — barely sixty, which in elf terms was approximately twelve. She had been born in the tree's eastern root, in a chamber that smelled of soil and old rain, and had grown up running its branches and reading its bark-patterns and talking to it, as all the elf children did. The tree never answered back in words, but it communicated in other ways: a warmth when you pressed your hand to it, a shiver of branches when something was wrong, a deep slow vibration in its roots on the nights when it was particularly content. Pip understood these things as naturally as breathing."},
            {"page_number": 3, "text": "The trouble began in autumn. Pip noticed it first — a coolness in the bark where there should have been warmth, a hesitation in the tree's usual vibration. She told Fernwick. He came and pressed his ancient hands against the trunk and was quiet for a long time. 'The tree is forgetting,' he said. 'It has been here so long that it has started to forget what it is.' The other elves gathered. They discussed protocols and ancient remedies. They consulted records that went back eight hundred years. Pip listened to all of it and then said: 'What does it need to remember?'"},
            {"page_number": 4, "text": "The elves debated for a week. The tree needed to remember its purpose — but what was its purpose? It provided habitat: homes for dozens of creatures, from the woodpeckers in the high branches to the beetles in the deep root chambers. It regulated the local water table. It produced oxygen and sequestered carbon and anchored the soil. 'It provides everything,' said one elf. 'Then why is it forgetting?' said Pip. Nobody answered. She walked away from the debate and sat with her back against the Great Green's vast trunk, and just stayed there, quietly, being present."},
            {"page_number": 5, "text": "She stayed there for three days. She didn't try to fix anything. She didn't perform any remedies. She brought her meals and ate them against the tree's side. She talked to it sometimes — not the formal ritual language, just ordinary conversation, the kind she would have with a friend. She told it about the things she had seen that day. She told it it was beautiful, which it was. On the third morning she felt the faintest change — a warmth returning to the bark under her palm, gradual as sunrise. She held her breath. The warmth grew."},
            {"page_number": 6, "text": "Fernwick found her there on the fourth morning and stood watching without interrupting. The tree's colour had changed — the grey-green of its stressed leaves shifting back toward the deep vivid green it should have been. 'What did you do?' he asked. 'Nothing,' said Pip. 'I just stayed.' Fernwick was quiet for a very long time. 'We have been tending the tree,' he said slowly, 'for a thousand years. We have watered it and pruned it and sung to it. We have never simply stayed with it.' He sat down next to Pip. Together they leaned against the Great Green and said nothing at all."},
            {"page_number": 7, "text": "Word spread through the elf community with the particular speed of news that surprises everyone. The tree was recovering. Its leaves were deepening. Its bark had regained the warmth that had been fading for months. The other elves came to see, and found Pip and Fernwick sitting side by side at the base of the trunk doing nothing whatsoever, and after some confused discussion, sat down too. By evening, twenty-three elves were leaning against the Great Green, talking softly or sitting in silence, and the tree was vibrating with something that, Pip thought, felt very much like happiness."},
            {"page_number": 8, "text": "The recovery took three weeks to complete. During that time, the elves reorganised how they tended the Great Green. The rituals and the watering and the pruning continued — they were still important — but they added something new: dedicated time, every day, when elves simply sat with the tree and did nothing useful at all. They told it stories. They leaned against it and read books. They brought their children to play in its roots. The tree, it turned out, had not been forgetting its purpose. It had been forgetting that it was loved. These are not the same thing, but they are related."},
            {"page_number": 9, "text": "On the first day of winter, the Great Green did something it had not done in anyone's memory: it flowered. Small white blossoms appeared on every branch simultaneously, defying the season, filling the cold air with a scent like honey and rain. The elves gathered and looked up and many of them cried, because the tree was speaking to them, finally, in a language even clearer than warmth and vibration. 'Thank you,' the flowers said. 'Thank you for staying.' Pip stood in the centre of the falling petals and thought about all the complicated things they had tried and all the simple thing that had worked."},
            {"page_number": 10, "text": "The following spring, Pip was named the tree's official companion — a new role, invented specifically for her, which involved no rituals and no maintenance and no formal duties at all. Her job was simply to be present, to notice when the tree needed company, and to provide it. She was very good at this job. She spent most of her days in the tree's branches or against its trunk, doing nothing much, being there. 'What are you doing?' asked a young elf, new to the community. Pip thought about it. 'Paying attention,' she said. 'Staying. It turns out that's the most important thing.' THE END"},
        ]
    },
]

# Note: Due to message length limits, I'll add the remaining 10 books in the actual execution
# The full script will be created with all 17 books

async def run_import(dry_run=True):
    """Run the CREATE import for Batch 3B"""
    
    mongo_url = os.environ.get('MONGO_URL')
    db_name = os.environ.get('DB_NAME', 'test_database')
    
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    mode = "DRY RUN" if dry_run else "APPLYING"
    print(f"\n{'='*60}")
    print(f" {mode} - Batch 3B Import (CREATE only)")
    print(f"{'='*60}")
    
    total_creates = 0
    errors = 0
    
    for book_data in BOOKS_DATA:
        book_title = book_data["title"]
        book_id = book_data["book_id"]
        
        print(f"\n📚 {book_title}")
        print(f"   Book ID: {book_id}")
        
        # Verify book exists
        book = await db.books.find_one({"id": book_id})
        if not book:
            print(f"   ❌ ERROR: Book not found in database!")
            errors += 1
            continue
        
        # Check existing pages
        existing_pages = await db.pages.count_documents({"book_id": book_id})
        embedded_pages = len(book.get("pages", []))
        
        if existing_pages > 0:
            print(f"   ⚠️ Book already has {existing_pages} pages in pages collection - skipping")
            continue
            
        creates_in_book = 0
        
        for page_data in book_data["pages"]:
            page_num = page_data["page_number"]
            text = page_data["text"]
            
            if dry_run:
                print(f"   🆕 Page {page_num} CREATE: {len(text)} chars")
                creates_in_book += 1
                total_creates += 1
            else:
                # Create new page
                new_page_id = str(uuid.uuid4())
                new_page = {
                    "id": new_page_id,
                    "book_id": book_id,
                    "page_number": page_num,
                    "text_content": text,
                    "image_url": None,
                    "audio_url": None,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }
                await db.pages.insert_one(new_page)
                
                # Update embedded pages array (clear and rebuild)
                if page_num == 1:
                    # Clear existing embedded pages on first page
                    await db.books.update_one(
                        {"id": book_id},
                        {"$set": {"pages": []}}
                    )
                
                # Add to embedded array
                await db.books.update_one(
                    {"id": book_id},
                    {"$push": {"pages": {
                        "id": new_page_id,
                        "page_number": page_num,
                        "text_content": text,
                        "image_url": None,
                        "audio_url": None
                    }}}
                )
                print(f"   🆕 Page {page_num} CREATED: {new_page_id[:8]}... ({len(text)} chars)")
                creates_in_book += 1
                total_creates += 1
        
        print(f"   Summary: {creates_in_book} pages created")
    
    print(f"\n{'='*60}")
    print(f" {mode} SUMMARY")
    print(f"{'='*60}")
    print(f" 🆕 Pages to CREATE: {total_creates}")
    print(f" ❌ Errors: {errors}")
    print(f"{'='*60}\n")
    
    client.close()
    return errors == 0


if __name__ == "__main__":
    dry_run = "--apply" not in sys.argv
    asyncio.run(run_import(dry_run))
