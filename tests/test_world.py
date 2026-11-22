"""Map integrity tests for signal_lost.world.

Every test name starts with the requirement it checks (R1, R2, or R3), and
its docstring names the acceptance criterion from spec.md Section 6.
"""

import unittest
from collections import deque

from signal_lost.world import DIRECTIONS, ESCAPE_ROOM, START_ROOM, Room, build_ship

OPPOSITE = {"north": "south", "south": "north", "east": "west", "west": "east"}

# The exact room table from spec.md Section 3.2.
EXPECTED_EXITS = {
    "cryo_bay": {"north": "medical_bay"},
    "medical_bay": {"south": "cryo_bay", "east": "central_corridor"},
    "central_corridor": {
        "west": "medical_bay",
        "north": "bridge",
        "east": "mess_hall",
        "south": "engineering",
    },
    "bridge": {"south": "central_corridor", "east": "comms_array"},
    "comms_array": {"west": "bridge", "south": "mess_hall"},
    "mess_hall": {"west": "central_corridor", "north": "comms_array"},
    "engineering": {
        "north": "central_corridor",
        "east": "reactor_core",
        "south": "cargo_hold",
    },
    "reactor_core": {"west": "engineering", "south": "airlock_junction"},
    "cargo_hold": {"north": "engineering", "east": "airlock_junction"},
    "airlock_junction": {
        "west": "cargo_hold",
        "north": "reactor_core",
        "east": "escape_pod",
    },
    "escape_pod": {"west": "airlock_junction"},
}


def bfs_distances(rooms, start):
    """Return {room_id: fewest moves from start} for every reachable room."""
    distances = {start: 0}
    queue = deque([start])
    while queue:
        current = queue.popleft()
        for destination in rooms[current].exits.values():
            if destination not in distances:
                distances[destination] = distances[current] + 1
                queue.append(destination)
    return distances


class ShipMapTests(unittest.TestCase):
    def setUp(self):
        self.rooms = build_ship()

    # ----- R1: Room Navigation ---------------------------------------------

    def test_R1_room_table_matches_spec(self):
        """R1 (AC-R1.1, AC-R1.8): the exits match spec.md Section 3.2 exactly."""
        actual = {room_id: dict(room.exits) for room_id, room in self.rooms.items()}
        self.assertEqual(actual, EXPECTED_EXITS)

    def test_R1_every_exit_leads_to_an_existing_room(self):
        """R1 (AC-R1.8): no exit points at a room that does not exist."""
        for room in self.rooms.values():
            for direction, destination in room.exits.items():
                with self.subTest(room=room.id, direction=direction):
                    self.assertIn(destination, self.rooms)

    def test_R1_every_exit_has_a_matching_return_exit(self):
        """R1 (AC-R1.8): if A's east leads to B, then B's west leads back to A."""
        for room in self.rooms.values():
            for direction, destination in room.exits.items():
                with self.subTest(room=room.id, direction=direction):
                    back = self.rooms[destination].exits.get(OPPOSITE[direction])
                    self.assertEqual(back, room.id)

    def test_R1_every_room_is_reachable_from_cryo_bay(self):
        """R1 (AC-R1.8): BFS from the Cryo Bay reaches all 11 rooms."""
        reachable = bfs_distances(self.rooms, START_ROOM)
        self.assertEqual(set(reachable), set(self.rooms))

    def test_R1_exits_only_use_the_four_compass_directions(self):
        """R1 (AC-R1.1): every exit direction is north, east, south, or west."""
        self.assertEqual(DIRECTIONS, ("north", "east", "south", "west"))
        for room in self.rooms.values():
            with self.subTest(room=room.id):
                self.assertTrue(set(room.exits) <= set(DIRECTIONS))

    # ----- R2: Room Information --------------------------------------------

    def test_R2_map_has_eleven_rooms_including_start_and_escape_pod(self):
        """R2 (AC-R2.6): the ship has 11 rooms; START_ROOM and ESCAPE_ROOM exist."""
        self.assertEqual(len(self.rooms), 11)
        self.assertIn(START_ROOM, self.rooms)
        self.assertIn(ESCAPE_ROOM, self.rooms)

    def test_R2_every_room_has_name_description_and_an_exit(self):
        """R2 (AC-R2.6): non-empty name, non-empty description, at least one exit."""
        for room in self.rooms.values():
            with self.subTest(room=room.id):
                self.assertIsInstance(room, Room)
                self.assertTrue(room.name.strip())
                self.assertTrue(room.description.strip())
                self.assertGreaterEqual(len(room.exits), 1)

    def test_R2_room_ids_match_their_dictionary_keys(self):
        """R2 (AC-R2.6): each room is stored under its own id."""
        for room_id, room in self.rooms.items():
            with self.subTest(room=room_id):
                self.assertEqual(room.id, room_id)

    def test_R2_room_names_are_unique(self):
        """R2 (AC-R2.2): every room has a different name so the player can tell them apart."""
        names = [room.name for room in self.rooms.values()]
        self.assertEqual(len(names), len(set(names)))

    def test_R2_descriptions_are_one_to_three_sentences(self):
        """R2 (AC-R2.3): descriptions are short (spec.md Section 3.2: 1-3 sentences)."""
        for room in self.rooms.values():
            with self.subTest(room=room.id):
                sentences = [s for s in room.description.replace("!", ".").split(". ") if s.strip()]
                self.assertTrue(1 <= len(sentences) <= 3, room.description)

    # ----- R3: Oxygen and Escaping -----------------------------------------

    def test_R3_start_is_cryo_bay_and_goal_is_escape_pod(self):
        """R3: the game starts in the Cryo Bay and the goal is the Escape Pod."""
        self.assertEqual(START_ROOM, "cryo_bay")
        self.assertEqual(ESCAPE_ROOM, "escape_pod")

    def test_R3_shortest_route_to_escape_pod_is_six_moves(self):
        """R3 (AC-R3.8): the fewest moves from Cryo Bay to Escape Pod is 6."""
        distances = bfs_distances(self.rooms, START_ROOM)
        self.assertEqual(distances[ESCAPE_ROOM], 6)

    def test_R3_map_is_bipartite_so_pod_is_only_reached_on_even_moves(self):
        """R3 (AC-R3.6 setup): every exit joins rooms of opposite parity (spec 3.3)."""
        distances = bfs_distances(self.rooms, START_ROOM)
        for room in self.rooms.values():
            for destination in room.exits.values():
                with self.subTest(room=room.id, destination=destination):
                    self.assertNotEqual(distances[room.id] % 2, distances[destination] % 2)


if __name__ == "__main__":
    unittest.main()
