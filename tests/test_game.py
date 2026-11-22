"""Game rule tests for signal_lost.game.

Every test name starts with the requirement it checks (R1-R5), and
its docstring names the acceptance criterion from spec.md Section 6.
Each test builds a fresh Game, so no state is shared between tests.
"""

import unittest
from collections import deque

from signal_lost.game import (
    OXYGEN_PER_MOVE,
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


if __name__ == "__main__":
    unittest.main()
