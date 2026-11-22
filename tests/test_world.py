"""Map integrity tests for signal_lost.world.

Every test name starts with the requirement it checks (R1-R9), and
its docstring names the acceptance criterion from spec.md Section 6.
"""

import unittest
from collections import deque

from signal_lost.world import (
    DIRECTIONS,
    ESCAPE_ROOM,
    HAZARD_ROOMS,
    MAP_GRID,
    START_ROOM,
    Room,
    build_ship,
)

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


# Grid step for each direction: (row change, column change). spec.md 3.7.
GRID_STEP = {"north": (-1, 0), "south": (1, 0), "east": (0, 1), "west": (0, -1)}


class ShipMapLayoutTests(unittest.TestCase):
    """R4: the grid positions the map is drawn from (spec.md 3.7)."""

    def setUp(self):
        self.rooms = build_ship()

    def test_R4_every_room_has_a_grid_position(self):
        """R4 (AC-R4.8): MAP_GRID has a position for exactly the rooms on the ship."""
        self.assertEqual(set(MAP_GRID), set(self.rooms))

    def test_R4_grid_positions_are_unique_and_inside_a_4_by_4_grid(self):
        """R4 (AC-R4.8): no two rooms share a cell, and all cells fit 4 x 4."""
        positions = list(MAP_GRID.values())
        self.assertEqual(len(positions), len(set(positions)))
        for room_id, (row, col) in MAP_GRID.items():
            with self.subTest(room=room_id):
                self.assertIn(row, range(4))
                self.assertIn(col, range(4))

    def test_R4_every_exit_joins_rooms_that_are_neighbors_on_the_grid(self):
        """R4 (AC-R4.8): an east exit leads one column right, south one row down, etc."""
        for room in self.rooms.values():
            row, col = MAP_GRID[room.id]
            for direction, destination in room.exits.items():
                with self.subTest(room=room.id, direction=direction):
                    d_row, d_col = GRID_STEP[direction]
                    self.assertEqual(MAP_GRID[destination], (row + d_row, col + d_col))


class RoomClueTests(unittest.TestCase):
    """R5: every room carries its own scanner clue (spec.md 3.8)."""

    def setUp(self):
        self.rooms = build_ship()

    def test_R5_every_room_has_a_non_empty_clue(self):
        """R5 (AC-R5.2): each room's clue is a non-empty string."""
        for room in self.rooms.values():
            with self.subTest(room=room.id):
                self.assertIsInstance(room.clue, str)
                self.assertTrue(room.clue.strip())

    def test_R5_every_room_has_a_different_clue(self):
        """R5 (AC-R5.2): no two rooms share a clue."""
        clues = [room.clue for room in self.rooms.values()]
        self.assertEqual(len(clues), len(set(clues)))

    def test_R5_clue_is_not_just_the_room_description(self):
        """R5 (AC-R5.2): the scanner tells the player something new."""
        for room in self.rooms.values():
            with self.subTest(room=room.id):
                self.assertNotEqual(room.clue, room.description)
                self.assertNotIn(room.clue, room.description)

    def test_R5_clues_are_short_plain_ascii(self):
        """R5 (AC-R5.2, AC-R5.6): clues are one or two sentences of plain ASCII."""
        for room in self.rooms.values():
            with self.subTest(room=room.id):
                self.assertTrue(room.clue.isascii())
                sentences = [s for s in room.clue.split(". ") if s.strip()]
                self.assertTrue(1 <= len(sentences) <= 2, room.clue)


# Starting item placement from spec.md Section 3.9.
EXPECTED_ITEMS = {
    "cryo_bay": ("flashlight",),
    "medical_bay": ("medkit",),
    "bridge": ("keycard",),
    "engineering": ("repair kit",),
}


class ItemPlacementTests(unittest.TestCase):
    def setUp(self):
        self.rooms = build_ship()

    def test_R6_starting_items_are_in_the_rooms_the_spec_lists(self):
        """R6 (AC-R6.2): flashlight, medkit, keycard, repair kit start where 3.9 says."""
        for room in self.rooms.values():
            with self.subTest(room=room.id):
                self.assertEqual(room.items, EXPECTED_ITEMS.get(room.id, ()))

    def test_R6_escape_pod_starts_with_no_items(self):
        """R6 (AC-R6.2): the Escape Pod holds nothing."""
        self.assertEqual(self.rooms[ESCAPE_ROOM].items, ())

    def test_R6_item_names_are_unique_lower_case_and_single_spaced(self):
        """R6 (AC-R6.2, AC-R6.7): names can be matched after normalizing input."""
        names = [item for room in self.rooms.values() for item in room.items]
        self.assertEqual(len(names), 4)
        self.assertEqual(len(names), len(set(names)))
        for name in names:
            with self.subTest(item=name):
                self.assertTrue(name.isascii())
                self.assertEqual(name, " ".join(name.lower().split()))

    def test_R6_room_items_are_an_immutable_tuple(self):
        """R6 (AC-R6.2): the starting placement can't be changed by play."""
        for room in self.rooms.values():
            with self.subTest(room=room.id):
                self.assertIsInstance(room.items, tuple)

    def test_R6_room_without_items_argument_has_no_items(self):
        """R6 (AC-R6.2): a Room built without items holds nothing."""
        room = Room("x", "X", "A room.", {"north": "y"}, "A clue.")
        self.assertEqual(room.items, ())


def routes_to_pod(rooms, max_moves):
    """Every simple path (no room twice) from the start to the Escape Pod
    with at most ``max_moves`` moves, as lists of room ids after the start."""
    found = []

    def walk(room_id, path):
        if room_id == ESCAPE_ROOM:
            found.append(path)
            return
        if len(path) == max_moves:
            return
        for destination in rooms[room_id].exits.values():
            if destination != START_ROOM and destination not in path:
                walk(destination, path + [destination])

    walk(START_ROOM, [])
    return found


class HazardTests(unittest.TestCase):
    def setUp(self):
        self.rooms = build_ship()

    def test_R8_only_reactor_core_and_cargo_hold_are_hazards(self):
        """R8 (AC-R8.3): exactly these two rooms hurt the player."""
        hazards = {room.id for room in self.rooms.values() if room.hazard}
        self.assertEqual(hazards, {"reactor_core", "cargo_hold"})

    def test_R8_hazard_rooms_constant_matches_room_flags(self):
        """R8 (AC-R8.3): HAZARD_ROOMS and Room.hazard agree."""
        for room in self.rooms.values():
            with self.subTest(room=room.id):
                self.assertEqual(room.hazard, room.id in HAZARD_ROOMS)

    def test_R8_start_and_escape_pod_are_safe(self):
        """R8 (AC-R8.3): neither the Cryo Bay nor the Escape Pod is a hazard."""
        self.assertFalse(self.rooms[START_ROOM].hazard)
        self.assertFalse(self.rooms[ESCAPE_ROOM].hazard)

    def test_R8_room_without_hazard_argument_is_safe(self):
        """R8 (AC-R8.3): a Room built without the hazard flag is safe."""
        room = Room("x", "X", "A room.", {"north": "y"}, "A clue.")
        self.assertFalse(room.hazard)

    def test_R8_every_route_to_the_pod_passes_a_hazard(self):
        """R8 (AC-R8.8): any escape costs at least 2 health."""
        routes = routes_to_pod(self.rooms, 12)
        self.assertTrue(routes)
        for route in routes:
            with self.subTest(route=route):
                self.assertTrue(any(self.rooms[r].hazard for r in route))

    def test_R8_shortest_routes_enter_exactly_one_hazard(self):
        """R8 (AC-R8.8): both 6-move routes cost only 2 health, so no healing is needed."""
        shortest = [r for r in routes_to_pod(self.rooms, 6) if len(r) == 6]
        self.assertEqual(len(shortest), 2)
        for route in shortest:
            with self.subTest(route=route):
                self.assertEqual(sum(self.rooms[r].hazard for r in route), 1)


if __name__ == "__main__":
    unittest.main()
