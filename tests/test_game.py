"""Game rule tests for signal_lost.game.

Every test name starts with the requirement it checks (R1-R9), and
its docstring names the acceptance criterion from spec.md Section 6.
Each test builds a fresh Game, so no state is shared between tests.
"""

import unittest
from collections import deque

from signal_lost.game import (
    HAZARD_DAMAGE,
    MEDKIT,
    MEDKIT_HEALING,
    OXYGEN_PER_MOVE,
    STARTING_HEALTH,
    STARTING_OXYGEN,
    Game,
    Outcome,
    Status,
    TurnResult,
)
from signal_lost.parser import Command
from signal_lost.world import DIRECTIONS, ESCAPE_ROOM, START_ROOM, build_ship

# Scripted paths from spec.md Section 7.2.
SHORTEST_ROUTE = ["north", "east", "south", "south", "east", "east"]
REACTOR_ROUTE = ["north", "east", "south", "east", "south", "east"]
TEN_MOVE_WIN = ["north", "south", "north", "south", "north", "east", "south", "south", "east", "east"]
TWELVE_MOVE_POD = [
    "north", "south", "north", "south", "north", "south",
    "north", "east", "south", "south", "east", "east",
]
WANDER_LOSS = ["north", "south"] * 6


def move(direction):
    return Command("move", direction)


def play(game, directions):
    """Send each direction to the game and return the list of TurnResults."""
    return [game.handle(move(direction)) for direction in directions]


def path_to(room_id):
    """Shortest list of directions from START_ROOM to room_id."""
    rooms = build_ship()
    paths = {START_ROOM: []}
    queue = deque([START_ROOM])
    while queue:
        current = queue.popleft()
        for direction, destination in rooms[current].exits.items():
            if destination not in paths:
                paths[destination] = paths[current] + [direction]
                queue.append(destination)
    return paths[room_id]


class NewGameTests(unittest.TestCase):
    def test_R3_new_game_starts_with_12_oxygen(self):
        """R3 (AC-R3.1): a new game has exactly 12 oxygen."""
        self.assertEqual(STARTING_OXYGEN, 12)
        self.assertEqual(OXYGEN_PER_MOVE, 1)
        self.assertEqual(Game().oxygen, 12)

    def test_R3_new_game_starts_in_cryo_bay_and_is_playing(self):
        """R3 (AC-R3.1): a new game is in the Cryo Bay with status PLAYING."""
        game = Game()
        self.assertEqual(game.room.id, START_ROOM)
        self.assertEqual(game.status, Status.PLAYING)
        self.assertFalse(game.is_over)


class MovementTests(unittest.TestCase):
    def test_R1_valid_move_changes_room(self):
        """R1 (AC-R1.1): 'north' from the Cryo Bay enters the Medical Bay."""
        game = Game()
        result = game.handle(move("north"))
        self.assertIsInstance(result, TurnResult)
        self.assertEqual(result.outcome, Outcome.MOVED)
        self.assertEqual(game.room.id, "medical_bay")
        self.assertEqual(result.room.id, "medical_bay")

    def test_R1_moving_back_returns_to_previous_room(self):
        """R1 (AC-R1.1, AC-R1.8): north then south returns to the Cryo Bay."""
        game = Game()
        play(game, ["north", "south"])
        self.assertEqual(game.room.id, "cryo_bay")

    def test_R1_every_exit_on_the_shortest_route_moves_the_player(self):
        """R1 (AC-R1.1): each step of the shortest route lands in the expected room."""
        game = Game()
        expected = ["medical_bay", "central_corridor", "engineering",
                    "cargo_hold", "airlock_junction", "escape_pod"]
        for direction, room_id in zip(SHORTEST_ROUTE, expected):
            with self.subTest(direction=direction, room=room_id):
                game.handle(move(direction))
                self.assertEqual(game.room.id, room_id)

    def test_R3_valid_move_costs_exactly_one_oxygen(self):
        """R3 (AC-R3.2): one successful move lowers oxygen from 12 to 11."""
        game = Game()
        result = game.handle(move("north"))
        self.assertEqual(result.oxygen_used, 1)
        self.assertEqual(result.oxygen, 11)
        self.assertEqual(game.oxygen, 11)

    def test_R3_each_successful_move_costs_exactly_one_oxygen(self):
        """R3 (AC-R3.2): oxygen counts down 11, 10, 9, ... one per move."""
        game = Game()
        for step, direction in enumerate(TEN_MOVE_WIN[:-1], start=1):
            with self.subTest(step=step):
                result = game.handle(move(direction))
                self.assertEqual(result.oxygen_used, 1)
                self.assertEqual(game.oxygen, STARTING_OXYGEN - step)


class BlockedAndInvalidTests(unittest.TestCase):
    def test_R1_blocked_move_reports_blocked(self):
        """R1 (AC-R1.4): 'east' from the Cryo Bay is BLOCKED."""
        result = Game().handle(move("east"))
        self.assertEqual(result.outcome, Outcome.BLOCKED)

    def test_R1_blocked_move_keeps_player_in_same_room(self):
        """R1 (AC-R1.5): after a blocked move the room is unchanged."""
        game = Game()
        result = game.handle(move("west"))
        self.assertEqual(game.room.id, START_ROOM)
        self.assertEqual(result.room.id, START_ROOM)

    def test_R1_blocked_move_uses_no_oxygen(self):
        """R1 (AC-R1.6, AC-R3.3): after a blocked move oxygen is unchanged."""
        game = Game()
        result = game.handle(move("south"))
        self.assertEqual(result.oxygen_used, 0)
        self.assertEqual(game.oxygen, STARTING_OXYGEN)

    def test_R1_every_missing_exit_in_every_room_is_blocked_for_free(self):
        """R1 (AC-R1.4 to AC-R1.6): every direction a room lacks is blocked and free."""
        for room in build_ship().values():
            if room.id == ESCAPE_ROOM:
                continue  # entering the pod ends the game
            for direction in DIRECTIONS:
                if direction in room.exits:
                    continue
                with self.subTest(room=room.id, direction=direction):
                    game = Game()
                    play(game, path_to(room.id))
                    oxygen_before = game.oxygen
                    result = game.handle(move(direction))
                    self.assertEqual(result.outcome, Outcome.BLOCKED)
                    self.assertEqual(game.room.id, room.id)
                    self.assertEqual(game.oxygen, oxygen_before)

    def test_R1_unknown_command_changes_nothing(self):
        """R1 (AC-R1.7, AC-R3.3): an unknown command is INVALID and free."""
        game = Game()
        result = game.handle(Command("unknown", "fly"))
        self.assertEqual(result.outcome, Outcome.INVALID)
        self.assertEqual(result.oxygen_used, 0)
        self.assertEqual(game.room.id, START_ROOM)
        self.assertEqual(game.oxygen, STARTING_OXYGEN)
        self.assertEqual(game.status, Status.PLAYING)

    def test_R1_empty_input_changes_nothing(self):
        """R1 (AC-R1.7): empty input is EMPTY and free."""
        game = Game()
        result = game.handle(Command("empty", None))
        self.assertEqual(result.outcome, Outcome.EMPTY)
        self.assertEqual(game.room.id, START_ROOM)
        self.assertEqual(game.oxygen, STARTING_OXYGEN)

    def test_R1_move_with_unrecognized_direction_is_invalid(self):
        """R1 (AC-R1.7): a move command with a non-compass direction never crashes."""
        game = Game()
        result = game.handle(move("up"))
        self.assertEqual(result.outcome, Outcome.INVALID)
        self.assertEqual(game.oxygen, STARTING_OXYGEN)

    def test_R2_look_returns_current_room_without_using_oxygen(self):
        """R2 (spec 3.5) and R3 (AC-R3.3): 'look' reports the room and is free."""
        game = Game()
        game.handle(move("north"))
        result = game.handle(Command("look", None))
        self.assertEqual(result.outcome, Outcome.LOOKED)
        self.assertEqual(result.room.id, "medical_bay")
        self.assertEqual(result.oxygen_used, 0)
        self.assertEqual(game.oxygen, 11)

    def test_R3_help_uses_no_oxygen(self):
        """R3 (AC-R3.3): 'help' is free and changes nothing."""
        game = Game()
        result = game.handle(Command("help", None))
        self.assertEqual(result.outcome, Outcome.HELP)
        self.assertEqual(result.oxygen_used, 0)
        self.assertEqual(game.room.id, START_ROOM)
        self.assertEqual(game.oxygen, STARTING_OXYGEN)

    def test_R3_eleven_blocked_moves_then_one_real_move_leaves_11_oxygen(self):
        """R3 (AC-R1.6, AC-R3.3): blocked moves are free; only the real move costs."""
        game = Game()
        blocked = ["east", "south", "west"] * 3 + ["east", "west"]
        self.assertEqual(len(blocked), 11)
        for result in play(game, blocked):
            self.assertEqual(result.outcome, Outcome.BLOCKED)
        game.handle(move("north"))
        self.assertEqual(game.oxygen, 11)
        self.assertEqual(game.status, Status.PLAYING)


class WinningTests(unittest.TestCase):
    def test_R3_shortest_route_wins_with_six_oxygen(self):
        """R3 (AC-R3.4, AC-R3.8): n, e, s, s, e, e wins with 6 oxygen left."""
        game = Game()
        results = play(game, SHORTEST_ROUTE)
        self.assertEqual(results[-1].outcome, Outcome.WON)
        self.assertEqual(results[-1].room.id, ESCAPE_ROOM)
        self.assertEqual(game.status, Status.WON)
        self.assertEqual(game.oxygen, 6)
        self.assertTrue(game.is_over)

    def test_R3_reactor_core_route_also_wins_with_six_oxygen(self):
        """R3 (AC-R3.4, AC-R3.8): the second 6-move route through the Reactor Core wins."""
        game = Game()
        play(game, REACTOR_ROUTE)
        self.assertEqual(game.status, Status.WON)
        self.assertEqual(game.oxygen, 6)

    def test_R3_ten_move_route_wins_with_two_oxygen(self):
        """R3 (AC-R3.4): reaching the pod on move 10 wins with 2 oxygen."""
        game = Game()
        results = play(game, TEN_MOVE_WIN)
        self.assertEqual(results[-1].outcome, Outcome.WON)
        self.assertEqual(game.status, Status.WON)
        self.assertEqual(game.oxygen, 2)

    def test_R3_moves_before_reaching_the_pod_keep_playing(self):
        """R3 (AC-R3.4): status stays PLAYING until the pod is entered."""
        game = Game()
        for result in play(game, SHORTEST_ROUTE[:-1]):
            self.assertEqual(result.outcome, Outcome.MOVED)
        self.assertEqual(game.status, Status.PLAYING)


class LosingTests(unittest.TestCase):
    def test_R3_twelve_move_pod_arrival_is_a_loss(self):
        """R3 (AC-R3.6): entering the pod on the move that hits 0 oxygen is a loss."""
        game = Game()
        results = play(game, TWELVE_MOVE_POD)
        self.assertEqual(results[-1].outcome, Outcome.LOST)
        self.assertEqual(results[-1].room.id, ESCAPE_ROOM)
        self.assertEqual(game.status, Status.LOST)
        self.assertEqual(game.oxygen, 0)

    def test_R3_wandering_for_twelve_moves_is_a_loss(self):
        """R3 (AC-R3.5): 12 moves without reaching the pod ends in LOST."""
        game = Game()
        results = play(game, WANDER_LOSS)
        for result in results[:-1]:
            self.assertEqual(result.outcome, Outcome.MOVED)
        self.assertEqual(results[-1].outcome, Outcome.LOST)
        self.assertEqual(game.status, Status.LOST)
        self.assertEqual(game.oxygen, 0)

    def test_R3_eleven_moves_with_one_oxygen_left_is_still_playing(self):
        """R3 (AC-R3.5): the loss happens at 0, not at 1."""
        game = Game()
        play(game, WANDER_LOSS[:11])
        self.assertEqual(game.oxygen, 1)
        self.assertEqual(game.status, Status.PLAYING)


class GameOverTests(unittest.TestCase):
    def test_R3_no_state_changes_after_winning(self):
        """R3 (AC-R3.7): once WON, further commands change nothing."""
        game = Game()
        play(game, SHORTEST_ROUTE)
        result = game.handle(move("west"))
        self.assertEqual(result.outcome, Outcome.GAME_OVER)
        self.assertEqual(result.oxygen_used, 0)
        self.assertEqual(game.room.id, ESCAPE_ROOM)
        self.assertEqual(game.oxygen, 6)
        self.assertEqual(game.status, Status.WON)

    def test_R3_no_state_changes_after_losing(self):
        """R3 (AC-R3.7): once LOST, further commands change nothing."""
        game = Game()
        play(game, WANDER_LOSS)
        room_before = game.room.id
        for command in (move("north"), Command("look", None), Command("quit", None)):
            with self.subTest(command=command):
                result = game.handle(command)
                self.assertEqual(result.outcome, Outcome.GAME_OVER)
                self.assertEqual(game.room.id, room_before)
                self.assertEqual(game.status, Status.LOST)

    def test_R3_oxygen_never_goes_below_zero(self):
        """R3 (spec 4.1 rule 4): oxygen stays at 0 after the game is lost."""
        game = Game()
        play(game, WANDER_LOSS + ["north", "south", "north"])
        self.assertEqual(game.oxygen, 0)

    def test_R3_quit_ends_the_game_without_win_or_loss(self):
        """R3 (spec 3.5, AC-R3.7): 'quit' sets status QUIT, uses no oxygen, then stops."""
        game = Game()
        result = game.handle(Command("quit", None))
        self.assertEqual(result.outcome, Outcome.QUIT)
        self.assertEqual(result.oxygen_used, 0)
        self.assertEqual(game.status, Status.QUIT)
        self.assertTrue(game.is_over)
        after = game.handle(move("north"))
        self.assertEqual(after.outcome, Outcome.GAME_OVER)
        self.assertEqual(game.room.id, START_ROOM)


MAP = Command("map")
SCAN = Command("scan")


class VisitedRoomTests(unittest.TestCase):
    def test_R4_new_game_has_visited_only_the_start_room(self):
        """R4 (AC-R4.2): the Cryo Bay counts as visited from the start."""
        game = Game()
        self.assertEqual(game.visited, {START_ROOM})

    def test_R4_successful_moves_add_rooms_to_visited(self):
        """R4 (AC-R4.2): every room entered is recorded."""
        game = Game()
        play(game, ["north", "east", "south"])
        self.assertEqual(game.visited,
                         {"cryo_bay", "medical_bay", "central_corridor", "engineering"})

    def test_R4_blocked_moves_add_nothing_to_visited(self):
        """R4 (AC-R4.2): bumping into a wall doesn't count as visiting."""
        game = Game()
        play(game, ["east", "south", "west"])
        self.assertEqual(game.visited, {START_ROOM})

    def test_R4_revisiting_a_room_records_it_once(self):
        """R4 (AC-R4.7): going back and forth doesn't duplicate rooms."""
        game = Game()
        play(game, ["north", "south", "north", "south"])
        self.assertEqual(game.visited, {"cryo_bay", "medical_bay"})

    def test_R4_winning_move_records_the_escape_pod(self):
        """R4 (AC-R4.2): the final room entered is recorded too."""
        game = Game()
        play(game, SHORTEST_ROUTE)
        self.assertIn(ESCAPE_ROOM, game.visited)
        self.assertEqual(len(game.visited), 7)

    def test_R4_turn_result_carries_a_snapshot_of_visited_rooms(self):
        """R4 (AC-R4.2): the result the CLI draws from can't change afterwards."""
        game = Game()
        result = game.handle(MAP)
        play(game, ["north"])
        self.assertEqual(result.visited, frozenset({START_ROOM}))
        self.assertIsInstance(result.visited, frozenset)


class MapCommandTests(unittest.TestCase):
    def test_R4_map_reports_mapped_with_current_room_and_visited(self):
        """R4 (AC-R4.2, AC-R4.3): 'map' returns MAPPED, the current room, and visited rooms."""
        game = Game()
        play(game, ["north", "east"])
        result = game.handle(MAP)
        self.assertEqual(result.outcome, Outcome.MAPPED)
        self.assertEqual(result.room.id, "central_corridor")
        self.assertEqual(result.visited,
                         frozenset({"cryo_bay", "medical_bay", "central_corridor"}))

    def test_R4_map_uses_no_oxygen_and_changes_nothing(self):
        """R4 (AC-R4.6): the map is free and doesn't move the player or end the game."""
        game = Game()
        play(game, ["north"])
        for _ in range(20):
            result = game.handle(MAP)
            self.assertEqual(result.oxygen_used, 0)
        self.assertEqual(game.oxygen, 11)
        self.assertEqual(game.room.id, "medical_bay")
        self.assertEqual(game.status, Status.PLAYING)
        self.assertEqual(game.visited, {"cryo_bay", "medical_bay"})

    def test_R4_map_at_one_oxygen_does_not_end_the_game(self):
        """R4 (AC-R4.6): checking the map on the last unit of oxygen is safe."""
        game = Game()
        play(game, WANDER_LOSS[:11])
        self.assertEqual(game.oxygen, 1)
        game.handle(MAP)
        self.assertEqual(game.oxygen, 1)
        self.assertEqual(game.status, Status.PLAYING)

    def test_R4_map_is_ignored_after_the_game_ends(self):
        """R4 (AC-R4.6) and R3 (AC-R3.7): once the game is over, 'map' does nothing."""
        game = Game()
        play(game, SHORTEST_ROUTE)
        self.assertEqual(game.handle(MAP).outcome, Outcome.GAME_OVER)


class ScanCommandTests(unittest.TestCase):
    def test_R5_scan_reports_scanned_with_the_current_room(self):
        """R5 (AC-R5.3): 'scan' returns SCANNED and the room whose clue to show."""
        game = Game()
        play(game, ["north", "east", "south"])
        result = game.handle(SCAN)
        self.assertEqual(result.outcome, Outcome.SCANNED)
        self.assertEqual(result.room.id, "engineering")
        self.assertEqual(result.room.clue, build_ship()["engineering"].clue)

    def test_R5_scan_uses_no_oxygen_and_changes_nothing(self):
        """R5 (AC-R5.4): scanning is free and doesn't move the player or end the game."""
        game = Game()
        result = game.handle(SCAN)
        self.assertEqual(result.oxygen_used, 0)
        self.assertEqual(game.oxygen, STARTING_OXYGEN)
        self.assertEqual(game.room.id, START_ROOM)
        self.assertEqual(game.status, Status.PLAYING)
        self.assertEqual(game.visited, {START_ROOM})

    def test_R5_same_room_can_be_scanned_repeatedly_with_the_same_clue(self):
        """R5 (AC-R5.5): repeated scans keep working and give the same clue."""
        game = Game()
        play(game, ["north"])
        results = [game.handle(SCAN) for _ in range(5)]
        for result in results:
            self.assertEqual(result.outcome, Outcome.SCANNED)
            self.assertEqual(result.room.clue, results[0].room.clue)
        self.assertEqual(game.oxygen, 11)

    def test_R5_scan_at_one_oxygen_does_not_end_the_game(self):
        """R5 (AC-R5.4): scanning on the last unit of oxygen is safe."""
        game = Game()
        play(game, WANDER_LOSS[:11])
        game.handle(SCAN)
        self.assertEqual(game.oxygen, 1)
        self.assertEqual(game.status, Status.PLAYING)

    def test_R5_scan_is_ignored_after_the_game_ends(self):
        """R5 (AC-R5.4) and R3 (AC-R3.7): once the game is over, 'scan' does nothing."""
        game = Game()
        play(game, WANDER_LOSS)
        self.assertEqual(game.handle(SCAN).outcome, Outcome.GAME_OVER)


class Round2DoesNotChangeRound1RulesTests(unittest.TestCase):
    def test_R4_R5_shortest_route_still_wins_with_six_oxygen_using_map_and_scan(self):
        """R4 (AC-R4.6) and R5 (AC-R5.4): free commands at every step don't change the outcome."""
        game = Game()
        for direction in SHORTEST_ROUTE:
            game.handle(MAP)
            game.handle(SCAN)
            game.handle(SCAN)
            game.handle(move(direction))
        self.assertEqual(game.status, Status.WON)
        self.assertEqual(game.oxygen, 6)

    def test_R4_R5_twelve_move_pod_arrival_is_still_a_loss_with_map_and_scan(self):
        """R4 (AC-R4.6) and R5 (AC-R5.4), with R3 (AC-R3.6): the boundary rule is unchanged."""
        game = Game()
        for direction in TWELVE_MOVE_POD:
            game.handle(SCAN)
            game.handle(MAP)
            game.handle(move(direction))
        self.assertEqual(game.status, Status.LOST)


def take(name):
    return Command("take", name)


def drop(name):
    return Command("drop", name)


INVENTORY = Command("inventory")
ALL_ITEMS = {"flashlight", "medkit", "keycard", "repair kit"}


def snapshot(game):
    """The parts of the game that free item commands must not change."""
    return (game.room_id, game.oxygen, game.status, set(game.visited))


def all_item_locations(game):
    """Every item the game knows about: room contents plus the inventory."""
    items = [item for room_items in game.room_items.values() for item in room_items]
    return items + list(game.inventory)


class ItemStartTests(unittest.TestCase):
    def test_R7_new_game_has_an_empty_inventory(self):
        """R7 (AC-R7.3): the player starts carrying nothing."""
        game = Game()
        self.assertEqual(game.inventory, [])
        self.assertEqual(game.handle(INVENTORY).inventory, ())

    def test_R6_new_game_room_items_match_the_starting_placement(self):
        """R6 (AC-R6.2): each room's items start as Room.items."""
        game = Game()
        for room_id, room in build_ship().items():
            with self.subTest(room=room_id):
                self.assertEqual(game.room_items[room_id], list(room.items))

    def test_R6_turn_result_shows_items_in_the_current_room(self):
        """R6 (AC-R6.3): results carry the current room's items for display."""
        game = Game()
        self.assertEqual(game.handle(Command("look")).items, ("flashlight",))
        self.assertEqual(game.handle(move("north")).items, ("medkit",))
        self.assertEqual(game.handle(move("east")).items, ())

    def test_R6_each_game_has_its_own_items(self):
        """R6 (AC-R6.2): taking an item in one game doesn't affect another."""
        first = Game()
        first.handle(take("flashlight"))
        self.assertEqual(Game().room_items["cryo_bay"], ["flashlight"])


class TakeTests(unittest.TestCase):
    def test_R6_take_moves_item_from_room_to_inventory(self):
        """R6 (AC-R6.4): taking the flashlight removes it from the Cryo Bay."""
        game = Game()
        result = game.handle(take("flashlight"))
        self.assertEqual(result.outcome, Outcome.TAKEN)
        self.assertEqual(result.item, "flashlight")
        self.assertEqual(game.inventory, ["flashlight"])
        self.assertEqual(game.room_items["cryo_bay"], [])
        self.assertEqual(result.items, ())
        self.assertEqual(result.inventory, ("flashlight",))

    def test_R6_take_multi_word_item(self):
        """R6 (AC-R6.4): the repair kit can be taken in Engineering."""
        game = Game()
        play(game, path_to("engineering"))
        result = game.handle(take("repair kit"))
        self.assertEqual(result.outcome, Outcome.TAKEN)
        self.assertIn("repair kit", game.inventory)

    def test_R6_take_item_from_another_room_is_not_here(self):
        """R6 (AC-R6.5): the keycard is on the Bridge, not in the Cryo Bay."""
        game = Game()
        before = snapshot(game)
        result = game.handle(take("keycard"))
        self.assertEqual(result.outcome, Outcome.NOT_HERE)
        self.assertEqual(result.item, "keycard")
        self.assertEqual(game.inventory, [])
        self.assertEqual(game.room_items["bridge"], ["keycard"])
        self.assertEqual(snapshot(game), before)

    def test_R6_take_unknown_item_is_not_here(self):
        """R6 (AC-R6.5): a name that isn't an item changes nothing."""
        game = Game()
        result = game.handle(take("banana"))
        self.assertEqual(result.outcome, Outcome.NOT_HERE)
        self.assertEqual(game.room_items["cryo_bay"], ["flashlight"])
        self.assertEqual(game.inventory, [])

    def test_R6_taking_the_same_item_twice_is_not_here(self):
        """R6 (AC-R6.5): once carried, the item is no longer in the room."""
        game = Game()
        game.handle(take("flashlight"))
        result = game.handle(take("flashlight"))
        self.assertEqual(result.outcome, Outcome.NOT_HERE)
        self.assertEqual(game.inventory, ["flashlight"])

    def test_R6_partial_item_name_does_not_match(self):
        """R6 (AC-R6.7): 'kit' does not take the repair kit."""
        game = Game()
        play(game, path_to("engineering"))
        for name in ("kit", "repair", "repair kits"):
            with self.subTest(name=name):
                self.assertEqual(game.handle(take(name)).outcome, Outcome.NOT_HERE)
        self.assertEqual(game.room_items["engineering"], ["repair kit"])

    def test_R6_take_with_no_name_is_invalid(self):
        """R6 (AC-R6.1): bare 'take' changes nothing."""
        game = Game()
        before = snapshot(game)
        result = game.handle(take(None))
        self.assertEqual(result.outcome, Outcome.INVALID)
        self.assertEqual(game.room_items["cryo_bay"], ["flashlight"])
        self.assertEqual(snapshot(game), before)

    def test_R6_take_uses_no_oxygen_and_changes_nothing_else(self):
        """R6 (AC-R6.6): taking is free; room, status, visited unchanged."""
        game = Game()
        game.handle(move("north"))
        before = snapshot(game)
        result = game.handle(take("medkit"))
        self.assertEqual(result.oxygen_used, 0)
        self.assertEqual(snapshot(game), before)

    def test_R6_take_at_one_oxygen_does_not_end_the_game(self):
        """R6 (AC-R6.6): a free action can't trigger the oxygen loss."""
        game = Game()
        play(game, ["north", "south"] * 5 + ["north"])
        self.assertEqual(game.oxygen, 1)
        game.handle(take("medkit"))
        self.assertEqual(game.status, Status.PLAYING)
        self.assertEqual(game.oxygen, 1)

    def test_R6_collecting_items_on_the_shortest_route_still_wins_with_six(self):
        """R6 (AC-R6.6): items don't change the win; 6 moves still leave 6 oxygen."""
        game = Game()
        game.handle(take("flashlight"))
        for direction in SHORTEST_ROUTE:
            result = game.handle(move(direction))
            if game.room_id == "medical_bay":
                game.handle(take("medkit"))
            if game.room_id == "engineering":
                game.handle(take("repair kit"))
        self.assertEqual(result.outcome, Outcome.WON)
        self.assertEqual(game.oxygen, 6)
        self.assertEqual(game.inventory, ["flashlight", "medkit", "repair kit"])

    def test_R6_take_is_ignored_after_the_game_ends(self):
        """R6 (AC-R6.6) and R3 (AC-R3.7): no item changes once the game is over."""
        game = Game()
        game.handle(Command("quit"))
        self.assertEqual(game.handle(take("flashlight")).outcome, Outcome.GAME_OVER)
        self.assertEqual(game.inventory, [])


class DropTests(unittest.TestCase):
    def test_R7_drop_moves_item_from_inventory_to_current_room(self):
        """R7 (AC-R7.4): a dropped item lands in the room the player is in."""
        game = Game()
        game.handle(take("flashlight"))
        game.handle(move("north"))
        result = game.handle(drop("flashlight"))
        self.assertEqual(result.outcome, Outcome.DROPPED)
        self.assertEqual(result.item, "flashlight")
        self.assertEqual(game.inventory, [])
        self.assertEqual(game.room_items["medical_bay"], ["medkit", "flashlight"])
        self.assertEqual(result.items, ("medkit", "flashlight"))
        self.assertEqual(result.inventory, ())

    def test_R7_dropped_item_stays_until_taken_again(self):
        """R7 (AC-R7.4): leave, come back, and the dropped item is still there."""
        game = Game()
        game.handle(take("flashlight"))
        game.handle(move("north"))
        game.handle(drop("flashlight"))
        play(game, ["east", "west"])
        self.assertIn("flashlight", game.handle(Command("look")).items)
        self.assertEqual(game.handle(take("flashlight")).outcome, Outcome.TAKEN)
        self.assertEqual(game.inventory, ["flashlight"])
        self.assertEqual(game.room_items["medical_bay"], ["medkit"])

    def test_R7_drop_item_not_carried_is_not_carried(self):
        """R7 (AC-R7.5): dropping something you don't have changes nothing."""
        game = Game()
        before = snapshot(game)
        for name in ("flashlight", "keycard", "banana"):
            with self.subTest(name=name):
                result = game.handle(drop(name))
                self.assertEqual(result.outcome, Outcome.NOT_CARRIED)
                self.assertEqual(result.item, name)
        self.assertEqual(game.room_items["cryo_bay"], ["flashlight"])
        self.assertEqual(game.inventory, [])
        self.assertEqual(snapshot(game), before)

    def test_R7_drop_with_no_name_is_invalid(self):
        """R7 (AC-R7.5): bare 'drop' changes nothing."""
        game = Game()
        game.handle(take("flashlight"))
        result = game.handle(drop(None))
        self.assertEqual(result.outcome, Outcome.INVALID)
        self.assertEqual(game.inventory, ["flashlight"])

    def test_R7_drop_uses_no_oxygen_and_changes_nothing_else(self):
        """R7 (AC-R7.6): dropping is free; room, status, visited unchanged."""
        game = Game()
        game.handle(take("flashlight"))
        game.handle(move("north"))
        before = snapshot(game)
        result = game.handle(drop("flashlight"))
        self.assertEqual(result.oxygen_used, 0)
        self.assertEqual(snapshot(game), before)


class InventoryTests(unittest.TestCase):
    def test_R7_inventory_reports_inventory_and_changes_nothing(self):
        """R7 (AC-R7.6): checking the inventory is free and changes nothing."""
        game = Game()
        game.handle(take("flashlight"))
        before = snapshot(game)
        result = game.handle(INVENTORY)
        self.assertEqual(result.outcome, Outcome.INVENTORY)
        self.assertEqual(result.oxygen_used, 0)
        self.assertEqual(result.inventory, ("flashlight",))
        self.assertEqual(snapshot(game), before)

    def test_R7_inventory_keeps_pickup_order(self):
        """R7 (AC-R7.2): items are listed in the order they were picked up."""
        game = Game()
        game.handle(move("north"))
        game.handle(take("medkit"))
        game.handle(move("south"))
        game.handle(take("flashlight"))
        self.assertEqual(game.handle(INVENTORY).inventory, ("medkit", "flashlight"))

    def test_R7_turn_result_inventory_is_a_snapshot(self):
        """R7 (AC-R7.2): an old result is not changed by later takes."""
        game = Game()
        first = game.handle(INVENTORY)
        game.handle(take("flashlight"))
        self.assertEqual(first.inventory, ())
        self.assertIsInstance(first.inventory, tuple)

    def test_R7_items_are_never_duplicated_or_lost(self):
        """R7 (AC-R7.7): after any mix of moves, takes, and drops, there are 4 items."""
        game = Game()
        script = [
            take("flashlight"), take("flashlight"), move("north"), take("medkit"),
            drop("flashlight"), drop("flashlight"), move("east"), drop("medkit"),
            move("north"), take("keycard"), take("medkit"), move("south"),
            take("medkit"), move("south"), take("repair kit"), drop("keycard"),
            drop("repair kit"), take("keycard"), drop("banana"), take(None),
        ]
        for step, command in enumerate(script):
            game.handle(command)
            with self.subTest(step=step, command=command):
                locations = all_item_locations(game)
                self.assertEqual(len(locations), 4)
                self.assertEqual(set(locations), ALL_ITEMS)


# ----- Round 4: health, hazards, and the medkit (R8, R9) -------------------

# n, e, s, e reaches the Reactor Core; each "w, e" after that re-enters it.
TO_REACTOR = ["north", "east", "south", "east"]
REACTOR_DEATH = TO_REACTOR + ["west", "east"] * 4   # 5 entries, 12 moves
TO_MEDKIT = ["north"]


def use(name):
    return Command("use", name)


def health_snapshot(game):
    """Everything a free command must leave alone, now including health."""
    return snapshot(game) + (game.health, tuple(game.inventory),
                             {r: tuple(i) for r, i in game.room_items.items()})


class HealthStartTests(unittest.TestCase):
    def test_R8_new_game_starts_with_10_health(self):
        """R8 (AC-R8.1): a new game has exactly 10 health."""
        self.assertEqual(STARTING_HEALTH, 10)
        self.assertEqual(Game().health, 10)

    def test_R8_results_report_current_health(self):
        """R8 (AC-R8.2): every TurnResult carries the health to display."""
        game = Game()
        self.assertEqual(game.handle(Command("look")).health, 10)
        self.assertEqual(game.handle(move("north")).health, 10)

    def test_R8_constants_match_the_requirements(self):
        """R8 (AC-R8.4) and R9 (AC-R9.2): 2 damage per hazard, 4 healing per medkit."""
        self.assertEqual(HAZARD_DAMAGE, 2)
        self.assertEqual(MEDKIT_HEALING, 4)
        self.assertEqual(MEDKIT, "medkit")


class HazardDamageTests(unittest.TestCase):
    def test_R8_entering_the_reactor_core_costs_2_health(self):
        """R8 (AC-R8.4): moving into the Reactor Core lowers health by 2."""
        game = Game()
        result = play(game, TO_REACTOR)[-1]
        self.assertEqual(result.room.id, "reactor_core")
        self.assertEqual(result.outcome, Outcome.MOVED)
        self.assertEqual(game.health, 8)
        self.assertEqual(result.health, 8)
        self.assertEqual(result.damage, 2)

    def test_R8_entering_the_cargo_hold_costs_2_health(self):
        """R8 (AC-R8.4): moving into the Cargo Hold lowers health by 2."""
        game = Game()
        result = play(game, ["north", "east", "south", "south"])[-1]
        self.assertEqual(result.room.id, "cargo_hold")
        self.assertEqual(game.health, 8)
        self.assertEqual(result.damage, 2)

    def test_R8_going_back_into_a_hazard_hurts_again(self):
        """R8 (AC-R8.4): every entry costs 2, not just the first."""
        game = Game()
        play(game, TO_REACTOR + ["west", "east", "west", "east"])
        self.assertEqual(game.health, 4)

    def test_R8_a_hazard_move_still_costs_exactly_1_oxygen(self):
        """R8 (AC-R8.5): hazard rooms cost the normal 1 oxygen."""
        game = Game()
        play(game, TO_REACTOR[:-1])
        before = game.oxygen
        result = game.handle(move("east"))
        self.assertEqual(game.oxygen, before - 1)
        self.assertEqual(result.oxygen_used, 1)

    def test_R8_safe_rooms_do_not_change_health(self):
        """R8 (AC-R8.5): moving into any non-hazard room leaves health alone."""
        game = Game()
        results = play(game, ["north", "east", "north", "east", "south", "west", "south"])
        for result in results:
            with self.subTest(room=result.room.id):
                self.assertEqual(result.health, 10)
                self.assertEqual(result.damage, 0)

    def test_R8_blocked_moves_and_commands_in_a_hazard_room_are_free(self):
        """R8 (AC-R8.5): look, scan, map, items, help, and bumping walls cost no health."""
        game = Game()
        play(game, TO_REACTOR)
        commands = [move("east"), move("north"), Command("look"), Command("scan"),
                    Command("map"), Command("help"), INVENTORY, take("banana"),
                    drop("banana"), use("banana"), use(None), Command("empty"),
                    Command("unknown", "fly")]
        for command in commands:
            with self.subTest(command=command):
                result = game.handle(command)
                self.assertEqual(game.health, 8)
                self.assertEqual(result.damage, 0)

    def test_R8_health_reaching_zero_ends_the_game(self):
        """R8 (AC-R8.6): a hazard that brings health to 0 is DIED and LOST."""
        game = Game()
        play(game, TO_REACTOR[:-1])
        game.health = 2
        result = game.handle(move("east"))
        self.assertEqual(result.outcome, Outcome.DIED)
        self.assertEqual(game.status, Status.LOST)
        self.assertEqual(game.health, 0)
        self.assertGreater(game.oxygen, 0)

    def test_R8_health_never_goes_below_zero(self):
        """R8 (AC-R8.6): with 1 health, a hazard leaves 0, not -1."""
        game = Game()
        play(game, TO_REACTOR[:-1])
        game.health = 1
        result = game.handle(move("east"))
        self.assertEqual(game.health, 0)
        self.assertEqual(result.health, 0)
        self.assertEqual(result.outcome, Outcome.DIED)

    def test_R8_no_commands_are_processed_after_dying(self):
        """R8 (AC-R8.6): once dead, handle() changes nothing."""
        game = Game()
        play(game, REACTOR_DEATH)
        before = health_snapshot(game)
        for command in (move("west"), Command("look"), use(MEDKIT), take("x")):
            with self.subTest(command=command):
                self.assertEqual(game.handle(command).outcome, Outcome.GAME_OVER)
                self.assertEqual(health_snapshot(game), before)

    def test_R8_health_and_oxygen_both_reaching_zero_is_the_health_ending(self):
        """R8 (AC-R8.7): five reactor entries end on move 12 with both at 0 -> DIED."""
        game = Game()
        results = play(game, REACTOR_DEATH)
        self.assertEqual(game.oxygen, 0)
        self.assertEqual(game.health, 0)
        self.assertEqual(results[-1].outcome, Outcome.DIED)
        self.assertEqual(game.status, Status.LOST)
        self.assertTrue(all(r.outcome is Outcome.MOVED for r in results[:-1]))

    def test_R8_four_hazard_entries_still_leave_the_player_alive(self):
        """R8 (AC-R8.6): health 2 is still alive and playing."""
        game = Game()
        results = play(game, TO_REACTOR + ["west", "east"] * 3)
        self.assertEqual(game.health, 2)
        self.assertEqual(results[-1].outcome, Outcome.MOVED)
        self.assertEqual(game.status, Status.PLAYING)

    def test_R8_shortest_routes_win_with_8_health_and_6_oxygen(self):
        """R8 (AC-R8.8): both 6-move routes escape without healing."""
        for route in (SHORTEST_ROUTE, REACTOR_ROUTE):
            with self.subTest(route=route):
                game = Game()
                result = play(game, route)[-1]
                self.assertEqual(result.outcome, Outcome.WON)
                self.assertEqual(game.health, 8)
                self.assertEqual(game.oxygen, 6)

    def test_R8_a_ten_move_route_through_both_hazards_still_wins(self):
        """R8 (AC-R8.8): reactor then cargo then reactor (3 hazards) still wins."""
        game = Game()
        route = TO_REACTOR + ["south", "west", "east", "north", "south", "east"]
        result = play(game, route)[-1]
        self.assertEqual(result.outcome, Outcome.WON)
        self.assertEqual(game.health, 4)
        self.assertEqual(game.oxygen, 2)

    def test_R8_earlier_boundary_rules_are_unchanged(self):
        """R8 (AC-R8.5) with R3 (AC-R3.5, AC-R3.6): oxygen losses still say LOST."""
        for route in (TWELVE_MOVE_POD, WANDER_LOSS):
            with self.subTest(route=route):
                result = play(Game(), route)[-1]
                self.assertEqual(result.outcome, Outcome.LOST)


class UseMedkitTests(unittest.TestCase):
    def setUp(self):
        self.game = Game()
        play(self.game, TO_MEDKIT)
        self.game.handle(take(MEDKIT))

    def hurt(self, times):
        """Walk from the Medical Bay into the Reactor Core ``times`` times."""
        play(self.game, ["east", "south", "east"] + ["west", "east"] * (times - 1))

    def test_R9_medkit_restores_4_health(self):
        """R9 (AC-R9.2): at 6 health the medkit brings the player to 10."""
        self.hurt(2)
        self.assertEqual(self.game.health, 6)
        result = self.game.handle(use(MEDKIT))
        self.assertEqual(result.outcome, Outcome.HEALED)
        self.assertEqual(self.game.health, 10)
        self.assertEqual(result.health, 10)
        self.assertEqual(result.healed, 4)
        self.assertEqual(result.item, MEDKIT)

    def test_R9_healing_never_goes_above_10(self):
        """R9 (AC-R9.2): at 8 health the medkit restores only 2."""
        self.hurt(1)
        result = self.game.handle(use(MEDKIT))
        self.assertEqual(self.game.health, 10)
        self.assertEqual(result.healed, 2)

    def test_R9_low_health_heals_the_full_4(self):
        """R9 (AC-R9.2): at 2 health the medkit brings the player to 6."""
        self.hurt(4)
        self.game.handle(use(MEDKIT))
        self.assertEqual(self.game.health, 6)

    def test_R9_a_used_medkit_leaves_the_inventory(self):
        """R9 (AC-R9.3): after a successful use the medkit is gone."""
        self.hurt(1)
        result = self.game.handle(use(MEDKIT))
        self.assertNotIn(MEDKIT, self.game.inventory)
        self.assertNotIn(MEDKIT, result.inventory)

    def test_R9_a_medkit_cannot_be_used_twice(self):
        """R9 (AC-R9.3, AC-R9.4): a second use says it is not carried."""
        self.hurt(2)
        self.game.handle(use(MEDKIT))
        play(self.game, ["west", "east"])  # back into the reactor: 10 -> 8
        result = self.game.handle(use(MEDKIT))
        self.assertEqual(result.outcome, Outcome.NOT_CARRIED)
        self.assertEqual(self.game.health, 8)

    def test_R9_medkit_not_yet_taken_cannot_be_used(self):
        """R9 (AC-R9.4): the medkit lying in the room must be taken first."""
        game = Game()
        play(game, TO_MEDKIT)
        game.health = 6
        before = health_snapshot(game)
        result = game.handle(use(MEDKIT))
        self.assertEqual(result.outcome, Outcome.NOT_CARRIED)
        self.assertEqual(result.item, MEDKIT)
        self.assertEqual(health_snapshot(game), before)

    def test_R9_dropped_medkit_cannot_be_used(self):
        """R9 (AC-R9.4): a medkit that was dropped is not carried."""
        self.hurt(1)
        self.game.handle(drop(MEDKIT))
        before = health_snapshot(self.game)
        self.assertEqual(self.game.handle(use(MEDKIT)).outcome, Outcome.NOT_CARRIED)
        self.assertEqual(health_snapshot(self.game), before)

    def test_R9_medkit_is_kept_at_full_health(self):
        """R9 (AC-R9.5): at 10 health the medkit isn't wasted."""
        before = health_snapshot(self.game)
        result = self.game.handle(use(MEDKIT))
        self.assertEqual(result.outcome, Outcome.FULL_HEALTH)
        self.assertEqual(result.healed, 0)
        self.assertIn(MEDKIT, self.game.inventory)
        self.assertEqual(health_snapshot(self.game), before)

    def test_R9_kept_medkit_still_works_later(self):
        """R9 (AC-R9.5): after a full-health try, the medkit heals once hurt."""
        self.game.handle(use(MEDKIT))
        self.hurt(1)
        self.assertEqual(self.game.handle(use(MEDKIT)).outcome, Outcome.HEALED)
        self.assertEqual(self.game.health, 10)

    def test_R9_using_the_medkit_is_free(self):
        """R9 (AC-R9.6): no oxygen, room, status, or visited changes."""
        self.hurt(1)
        before = snapshot(self.game)
        result = self.game.handle(use(MEDKIT))
        self.assertEqual(snapshot(self.game), before)
        self.assertEqual(result.oxygen_used, 0)
        self.assertEqual(result.damage, 0)

    def test_R9_medkit_can_be_taken_and_dropped_like_before(self):
        """R9 (AC-R9.7): the unused medkit moves like any other item."""
        self.assertEqual(self.game.handle(drop(MEDKIT)).outcome, Outcome.DROPPED)
        self.assertIn(MEDKIT, self.game.items_here)
        self.assertEqual(self.game.handle(take(MEDKIT)).outcome, Outcome.TAKEN)
        self.assertEqual(self.game.inventory, [MEDKIT])


class UseOtherItemsTests(unittest.TestCase):
    def test_R9_other_carried_items_cannot_be_used(self):
        """R9 (AC-R9.7): 'use flashlight' says it can't be used and changes nothing."""
        game = Game()
        game.handle(take("flashlight"))
        before = health_snapshot(game)
        result = game.handle(use("flashlight"))
        self.assertEqual(result.outcome, Outcome.CANT_USE)
        self.assertEqual(result.item, "flashlight")
        self.assertEqual(health_snapshot(game), before)
        self.assertEqual(game.inventory, ["flashlight"])

    def test_R9_items_not_carried_cannot_be_used(self):
        """R9 (AC-R9.4, AC-R9.7): not-carried check comes first, for any name."""
        game = Game()
        for name in ("flashlight", "keycard", "banana", "med"):
            with self.subTest(item=name):
                before = health_snapshot(game)
                result = game.handle(use(name))
                self.assertEqual(result.outcome, Outcome.NOT_CARRIED)
                self.assertEqual(result.item, name)
                self.assertEqual(health_snapshot(game), before)

    def test_R9_use_with_no_name_is_invalid(self):
        """R9 (AC-R9.1): bare 'use' is INVALID and changes nothing."""
        game = Game()
        before = health_snapshot(game)
        self.assertEqual(game.handle(use(None)).outcome, Outcome.INVALID)
        self.assertEqual(health_snapshot(game), before)

    def test_R9_items_are_conserved_until_the_medkit_is_used(self):
        """R9 (AC-R9.7): four items before the medkit is used, three after."""
        game = Game()
        script = [take("flashlight"), move("north"), take("medkit"), use("medkit"),
                  drop("flashlight"), move("east"), move("north"), take("keycard"),
                  use("keycard"), move("south"), move("south"), take("repair kit"),
                  move("east"), drop("keycard")]
        for step, command in enumerate(script):
            game.handle(command)
            with self.subTest(step=step, command=command):
                locations = all_item_locations(game)
                self.assertEqual(len(locations), 4)
                self.assertEqual(set(locations), ALL_ITEMS)
        game.handle(use("medkit"))
        locations = all_item_locations(game)
        self.assertEqual(len(locations), 3)
        self.assertEqual(set(locations), ALL_ITEMS - {MEDKIT})


if __name__ == "__main__":
    unittest.main()
