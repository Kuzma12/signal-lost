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
