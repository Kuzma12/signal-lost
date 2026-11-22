# Problem

Some people enjoy adventure games but don't always want to play something too complicated. I want to make a simple space adventure game where the player is stuck inside a damaged spaceship and has to find a way to escape before running out of oxygen.

The player should be able to explore different rooms, figure out where to go, and make decisions while trying to survive. I also want the game to be easy to understand but still have some challenges so it doesn't feel too easy or boring.

# Initial requirements

R1: Room Navigation

The player should be able to move around the spaceship by typing directions like north, south, east, or west. If they try going somewhere that isn't possible, the game should tell them and keep them in the same room without using oxygen.

R2: Room Information

Every time the player enters a room, the game should show the name of the room, a short description of what is there, and which directions they can go. This way the player knows where they are and what they can do next.

R3: Oxygen and Escaping

The player starts with 12 oxygen points and loses one every time they successfully move to another room. The goal is to find the escape pod before running out of oxygen. If they reach the escape pod while they still have oxygen, they win. If their oxygen reaches zero before escaping, they lose. The game should show a message telling them whether they won or lost.


## Round 2 requirements


R4: Ship Map

I want the player to be able to see a map of the spaceship by typing "map". The map should show the rooms they have already visited and which room they are currently in. Rooms they haven't explored yet should stay hidden so the player still has to figure out where to go. Using the map shouldn't take away any oxygen.

R5: Room Scanner

I want to add a scanner so the player can explore the spaceship a little more. When they type "scan", the game should give them a clue about the room they are in. Each room should have its own clue, like something important to notice or information that might help the player escape. Scanning a room shouldn't use any oxygen, and the player should be able to scan the same room more than once.

## Round 3 requirements

R6: Collecting Items

I want the player to be able to find different items around the spaceship, like a keycard, a repair kit, or other useful things. When the player enters a room, they should be able to see which items are there. They can type "take" followed by the item's name to pick it up. Once they collect something, it should be removed from that room and added to their inventory. If they try taking something that isn't there, the game should tell them. Picking up items shouldn't use any oxygen.

R7: Inventory System

I want the player to be able to check what they are carrying by typing "inventory". The game should show all the items they collected, and if they don't have anything, it should tell them their inventory is empty. I also want the player to be able to drop an item in the room they are currently in. That item should stay there until they pick it up again. Checking inventory or dropping items shouldn't use oxygen.
