"""Terminal output and full-playthrough tests for signal_lost.cli.

Every test name starts with the requirement it checks (R1-R9), and
its docstring names the acceptance criterion from spec.md Section 6.
The CLI is driven by a fake input function (a scripted list of inputs) and
a fake output function (a list that records every printed block), so no real
terminal is needed.
"""

import ast
import subprocess
import sys
import unittest
from pathlib import Path

from signal_lost.cli import HAZARD_MESSAGES, render_map, render_room, render_scan, run
from signal_lost.game import Status
from signal_lost.world import DIRECTIONS, build_ship

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ROOMS = build_ship()
RULE = "=" * 50

SHORTEST_ROUTE = ["n", "e", "s", "s", "e", "e"]
SHORTEST_ROOMS = ["medical_bay", "central_corridor", "engineering",
                  "cargo_hold", "airlock_junction", "escape_pod"]
WANDER_LOSS = ["n", "s"] * 6
TWELVE_MOVE_POD = ["n", "s", "n", "s", "n", "s", "n", "e", "s", "s", "e", "e"]

WIN_BANNER = "*** YOU WIN ***"
LOSS_BANNER = "*** GAME OVER: YOU LOST ***"
QUIT_MESSAGE = "You close your eyes and let the ship drift. Transmission ended."


class Session:
    """Runs the CLI with scripted input and records everything it does."""

    def __init__(self, inputs, interrupt=None):
        self.remaining = list(inputs)
        self.interrupt = interrupt
        self.events = []  # ("out", text) or ("prompt", text)
        self.game = run(input_fn=self._input, output_fn=self._output)

    def _input(self, prompt=""):
        self.events.append(("prompt", prompt))
        if not self.remaining:
            raise self.interrupt or EOFError
        return self.remaining.pop(0)

    def _output(self, text=""):
        self.events.append(("out", str(text)))

    @property
    def text(self):
        return "\n".join(text for kind, text in self.events if kind == "out")

    def turns(self):
        """Output grouped by prompt: turns()[0] is before the first prompt,
        turns()[i] is the response to the i-th input."""
        groups = [[]]
        for kind, text in self.events:
            if kind == "prompt":
                groups.append([])
            else:
                groups[-1].append(text)
        return ["\n".join(group) for group in groups]


def squash(text):
    """Collapse all whitespace so wrapped descriptions can be compared."""
    return " ".join(text.split())


def exits_line(room):
    return "Exits: " + ", ".join(d for d in DIRECTIONS if d in room.exits)


class StartOfGameTests(unittest.TestCase):
    def test_R2_starting_room_info_is_shown_before_the_first_prompt(self):
        """R2 (AC-R2.1): Cryo Bay name, description, exits, and oxygen appear first."""
        opening = Session([]).turns()[0]
        cryo = ROOMS["cryo_bay"]
        self.assertIn("CRYO BAY", opening)
        self.assertIn(squash(cryo.description), squash(opening))
        self.assertIn("Exits: north", opening)
        self.assertIn("[ OXYGEN: 12/12 ]", opening)

    def test_R1_opening_explains_how_to_move_and_get_help(self):
        """R1 (spec 1.2): the intro tells the player how to move and where to find help."""
        opening = Session([]).turns()[0]
        for word in ("north", "south", "east", "west", "help"):
            with self.subTest(word=word):
                self.assertIn(word, opening)

    def test_R3_opening_explains_the_oxygen_rule_and_the_goal(self):
        """R3 (spec 1.1): the intro mentions oxygen and the escape pod."""
        opening = Session([]).turns()[0].lower()
        self.assertIn("oxygen", opening)
        self.assertIn("escape pod", opening)

    def test_R1_prompt_is_angle_bracket_space(self):
        """R1 (spec 5): the input prompt is '> '."""
        session = Session([])
        prompts = [text for kind, text in session.events if kind == "prompt"]
        self.assertEqual(prompts, ["> "])


class RoomDisplayTests(unittest.TestCase):
    def test_R2_room_display_matches_the_spec_format(self):
        """R2 (spec 3.6): rule, uppercase name, rule, description, blank, exits, gauge."""
        room = ROOMS["central_corridor"]
        lines = render_room(room, 10).splitlines()
        self.assertEqual(lines[0], RULE)
        self.assertEqual(lines[1], "  CENTRAL CORRIDOR")
        self.assertEqual(lines[2], RULE)
        self.assertEqual(lines[-3], "")
        self.assertEqual(lines[-2], "Exits: north, east, south, west")
        self.assertEqual(lines[-1], "[ OXYGEN: 10/12 ]")
        self.assertEqual(squash(" ".join(lines[3:-3])), squash(room.description))

    def test_R2_exits_are_listed_in_north_east_south_west_order(self):
        """R2 (AC-R2.4): every room lists its real exits in the fixed order."""
        for room in ROOMS.values():
            with self.subTest(room=room.id):
                self.assertIn(exits_line(room), render_room(room, 12).splitlines())

    def test_R2_description_lines_fit_inside_the_frame(self):
        """R2 (AC-R2.3): descriptions are wrapped so no line is wider than the rule."""
        for room in ROOMS.values():
            with self.subTest(room=room.id):
                for line in render_room(room, 12).splitlines():
                    self.assertLessEqual(len(line), len(RULE))

    def test_R3_low_oxygen_warning_appears_at_three_or_less(self):
        """R3 (spec 4.5): the gauge adds '!! LOW OXYGEN !!' at 3 or less while playing."""
        room = ROOMS["engineering"]
        self.assertNotIn("LOW OXYGEN", render_room(room, 4))
        for oxygen in (3, 2, 1):
            with self.subTest(oxygen=oxygen):
                self.assertIn("!! LOW OXYGEN !!", render_room(room, oxygen))

    def test_R3_low_oxygen_warning_is_hidden_once_the_game_is_over(self):
        """R3 (spec 4.5): no warning on the final display of a finished game."""
        room = ROOMS["escape_pod"]
        self.assertNotIn("LOW OXYGEN", render_room(room, 2, game_over=True))


class MovementOutputTests(unittest.TestCase):
    def test_R2_each_move_shows_the_new_room_name(self):
        """R2 (AC-R2.2): after every move the new room's name is printed."""
        turns = Session(SHORTEST_ROUTE).turns()
        for index, room_id in enumerate(SHORTEST_ROOMS, start=1):
            with self.subTest(move=index):
                self.assertIn(f"  {ROOMS[room_id].name.upper()}", turns[index])

    def test_R2_each_move_shows_the_new_room_description(self):
        """R2 (AC-R2.3): after every move the new room's description is printed."""
        turns = Session(SHORTEST_ROUTE).turns()
        for index, room_id in enumerate(SHORTEST_ROOMS, start=1):
            with self.subTest(move=index):
                self.assertIn(squash(ROOMS[room_id].description), squash(turns[index]))

    def test_R2_each_move_shows_the_correct_exits(self):
        """R2 (AC-R2.4): after every move the Exits line matches the room's real exits."""
        turns = Session(SHORTEST_ROUTE).turns()
        for index, room_id in enumerate(SHORTEST_ROOMS, start=1):
            with self.subTest(move=index):
                self.assertIn(exits_line(ROOMS[room_id]), turns[index].splitlines())

    def test_R3_oxygen_gauge_counts_down_after_each_move(self):
        """R3 (AC-R3.2): the gauge shows 11/12, 10/12, ... after each move."""
        turns = Session(SHORTEST_ROUTE[:5]).turns()
        for index in range(1, 6):
            with self.subTest(move=index):
                self.assertIn(f"[ OXYGEN: {12 - index}/12 ]", turns[index])

    def test_R1_shortcuts_go_form_and_mixed_case_move_the_player(self):
        """R1 (AC-R1.2, AC-R1.3): 'N', 'go e', and '  SOUTH ' all move."""
        turns = Session(["N", "go e", "  SOUTH "]).turns()
        self.assertIn("MEDICAL BAY", turns[1])
        self.assertIn("CENTRAL CORRIDOR", turns[2])
        self.assertIn("ENGINEERING", turns[3])


class InvalidInputOutputTests(unittest.TestCase):
    def test_R1_blocked_move_prints_cant_go_message_and_exits(self):
        """R1 (AC-R1.4): 'east' in the Cryo Bay says you can't go that way and lists exits."""
        session = Session(["east"])
        response = session.turns()[1]
        self.assertIn("You can't go east from here.", response)
        self.assertIn("Exits: north", response)
        self.assertEqual(session.game.oxygen, 12)

    def test_R1_blocked_move_does_not_redisplay_or_use_oxygen(self):
        """R1 (AC-R1.5, AC-R1.6): a blocked move shows no new room and no oxygen loss."""
        session = Session(["west", "south"])
        for response in session.turns()[1:3]:
            self.assertNotIn(RULE, response)
            self.assertNotIn("11/12", response)
        self.assertEqual(session.game.room.id, "cryo_bay")

    def test_R1_unknown_command_prints_unknown_message(self):
        """R1 (AC-R1.7): 'fly' prints the Unknown command message."""
        response = Session(["fly"]).turns()[1]
        self.assertIn("Unknown command: 'fly'. Type 'help' for a list of commands.", response)

    def test_R1_malformed_go_prints_go_where_message(self):
        """R1 (AC-R1.7): 'go' and 'go up' ask 'Go where?'."""
        turns = Session(["go", "go up"]).turns()
        for response in turns[1:3]:
            self.assertIn("Go where? Try north, south, east, or west.", response)

    def test_R1_empty_input_prints_nothing(self):
        """R1 (AC-R1.7): empty or whitespace input just shows the prompt again."""
        session = Session(["", "   "])
        self.assertEqual(session.turns()[1], "")
        self.assertEqual(session.turns()[2], "")
        self.assertEqual(session.game.oxygen, 12)

    def test_R2_look_shows_the_room_again_for_free(self):
        """R2 (spec 3.5) and R3 (AC-R3.3): 'look' reprints the room at the same oxygen."""
        session = Session(["n", "look"])
        response = session.turns()[2]
        self.assertIn("MEDICAL BAY", response)
        self.assertIn("[ OXYGEN: 11/12 ]", response)
        self.assertEqual(session.game.oxygen, 11)

    def test_R3_help_lists_commands_for_free(self):
        """R3 (AC-R3.3): 'help' lists the commands and uses no oxygen."""
        session = Session(["help"])
        response = session.turns()[1]
        for word in ("north", "south", "east", "west", "look", "help", "quit"):
            with self.subTest(word=word):
                self.assertIn(word, response)
        self.assertEqual(session.game.oxygen, 12)


class EndOfGameOutputTests(unittest.TestCase):
    def test_R3_winning_playthrough_prints_win_message_after_pod_info(self):
        """R3 (AC-R3.4) and R2 (AC-R2.5): pod room info, then the win banner."""
        session = Session(SHORTEST_ROUTE)
        text = session.text
        self.assertIn("ESCAPE POD", text)
        self.assertIn(">>> LAUNCH SEQUENCE INITIATED <<<", text)
        self.assertIn("You escaped with 6 oxygen to spare.", text)
        self.assertIn(WIN_BANNER, text)
        self.assertLess(text.index("  ESCAPE POD"), text.index(WIN_BANNER))
        self.assertEqual(session.game.status, Status.WON)

    def test_R2_escape_pod_info_is_shown_on_the_winning_move(self):
        """R2 (AC-R2.5): the pod's description and exits appear on the winning move."""
        final = Session(SHORTEST_ROUTE).turns()[-1]
        pod = ROOMS["escape_pod"]
        self.assertIn(squash(pod.description), squash(final))
        self.assertIn(exits_line(pod), final.splitlines())
        self.assertIn("[ OXYGEN: 6/12 ]", final)

    def test_R3_game_stops_reading_input_after_winning(self):
        """R3 (AC-R3.7): leftover input is never read once the player wins."""
        session = Session(SHORTEST_ROUTE + ["look", "w"])
        self.assertEqual(session.remaining, ["look", "w"])
        self.assertEqual(session.text.count(WIN_BANNER), 1)

    def test_R3_losing_playthrough_prints_loss_message_after_room_info(self):
        """R3 (AC-R3.5) and R2 (AC-R2.5): final room info at 0 oxygen, then the loss banner."""
        session = Session(WANDER_LOSS + ["n"])
        final = session.turns()[-1]
        self.assertIn("  CRYO BAY", final)
        self.assertIn("[ OXYGEN: 0/12 ]", final)
        self.assertIn(">>> OXYGEN DEPLETED <<<", final)
        self.assertIn(LOSS_BANNER, final)
        self.assertLess(final.index("[ OXYGEN: 0/12 ]"), final.index(LOSS_BANNER))
        self.assertNotIn("LOW OXYGEN", final)
        self.assertEqual(session.remaining, ["n"])
        self.assertEqual(session.game.status, Status.LOST)

    def test_R3_reaching_the_pod_with_zero_oxygen_prints_loss_not_win(self):
        """R3 (AC-R3.6) and R2 (AC-R2.5): pod info is shown, but the result is a loss."""
        session = Session(TWELVE_MOVE_POD)
        final = session.turns()[-1]
        self.assertIn("  ESCAPE POD", final)
        self.assertIn(LOSS_BANNER, final)
        self.assertNotIn(WIN_BANNER, session.text)

    def test_R3_low_oxygen_warning_appears_during_play(self):
        """R3 (spec 4.5): after move 9 (3 oxygen left) the warning is shown."""
        turns = Session(WANDER_LOSS[:10]).turns()
        self.assertNotIn("LOW OXYGEN", turns[8])
        self.assertIn("!! LOW OXYGEN !!", turns[9])
        self.assertIn("!! LOW OXYGEN !!", turns[10])

    def test_R3_quit_prints_goodbye_and_stops(self):
        """R3 (spec 3.5, AC-R3.7): 'quit' prints the goodbye message and reads no more input."""
        session = Session(["quit", "n"])
        self.assertIn(QUIT_MESSAGE, session.text)
        self.assertNotIn(WIN_BANNER, session.text)
        self.assertNotIn(LOSS_BANNER, session.text)
        self.assertEqual(session.remaining, ["n"])
        self.assertEqual(session.game.status, Status.QUIT)

    def test_R3_end_of_input_quits_cleanly(self):
        """R3 (AC-R3.7, AC-G.3): Ctrl-D (EOFError) prints the quit message with no traceback."""
        session = Session(["n"])
        self.assertIn(QUIT_MESSAGE, session.text)
        self.assertEqual(session.game.status, Status.QUIT)

    def test_R3_ctrl_c_quits_cleanly(self):
        """R3 (AC-R3.7, AC-G.3): Ctrl-C (KeyboardInterrupt) prints the quit message."""
        session = Session([], interrupt=KeyboardInterrupt)
        self.assertIn(QUIT_MESSAGE, session.text)
        self.assertEqual(session.game.status, Status.QUIT)


class ArchitectureAndEntryPointTests(unittest.TestCase):
    def test_R3_game_logic_module_has_no_print_or_input_calls(self):
        """R1-R3 (AC-G.4): game.py contains no print() or input(); all I/O is in cli.py."""
        source = (PROJECT_ROOT / "signal_lost" / "game.py").read_text(encoding="utf-8")
        called = {
            node.func.id
            for node in ast.walk(ast.parse(source))
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        }
        self.assertNotIn("print", called)
        self.assertNotIn("input", called)

    def _run_main(self, stdin_text):
        return subprocess.run(
            [sys.executable, "main.py"],
            input=stdin_text,
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT,
            timeout=10,
        )

    def test_R3_main_py_plays_a_winning_game_and_exits_zero(self):
        """R3 (AC-G.1, AC-R3.4): 'python3 main.py' runs with no setup and can be won."""
        completed = self._run_main("\n".join(SHORTEST_ROUTE) + "\n")
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn(WIN_BANNER, completed.stdout)
        self.assertEqual(completed.stderr, "")

    def test_R3_main_py_handles_end_of_input_without_a_traceback(self):
        """R3 (AC-G.3): closing stdin immediately ends the game cleanly."""
        completed = self._run_main("")
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn(QUIT_MESSAGE, completed.stdout)
        self.assertNotIn("Traceback", completed.stderr)


# Map labels from spec.md 3.7, used to check what is (and isn't) drawn.
MAP_LABELS = {
    "cryo_bay": "Cryo Bay", "medical_bay": "Med Bay",
    "central_corridor": "Corridor", "bridge": "Bridge",
    "comms_array": "Comms", "mess_hall": "Mess", "engineering": "Engines",
    "reactor_core": "Reactor", "cargo_hold": "Cargo",
    "airlock_junction": "Airlock", "escape_pod": "Pod",
}


class MapOutputTests(unittest.TestCase):
    def test_R4_map_at_start_shows_only_the_cryo_bay_marked_as_current(self):
        """R4 (AC-R4.2, AC-R4.3, AC-R4.4): a new game's map has one room, marked '*'."""
        session = Session(["map"])
        self.assertEqual(session.turns()[1], "\n".join([
            "SHIP MAP  (* = you are here)",
            "",
            "[*Cryo Bay]",
            "",
            "You are in: Cryo Bay",
            "Rooms visited: 1 of 11",
            "",
        ]))

    def test_R4_map_matches_the_spec_example_after_exploring(self):
        """R4 (AC-R4.2-AC-R4.5): spec.md 3.7 example, after n, e, s, e."""
        session = Session(["n", "e", "s", "e", "map"])
        self.assertEqual(session.turns()[5], "\n".join([
            "SHIP MAP  (* = you are here)",
            "",
            "[ Med Bay ]--[ Corridor]",
            "     |            |",
            "[ Cryo Bay]  [ Engines ]--[*Reactor ]",
            "",
            "You are in: Reactor Core",
            "Rooms visited: 5 of 11",
            "",
        ]))

    def test_R4_map_hides_rooms_that_have_not_been_visited(self):
        """R4 (AC-R4.4): no label for any unvisited room appears on the map."""
        session = Session(["n", "e", "s", "e", "map"])
        response = session.turns()[5]
        for room_id in ("bridge", "comms_array", "mess_hall", "cargo_hold",
                        "airlock_junction", "escape_pod"):
            with self.subTest(room=room_id):
                self.assertNotIn(MAP_LABELS[room_id], response)
                self.assertNotIn(ROOMS[room_id].name, response)

    def test_R4_only_the_current_room_is_marked(self):
        """R4 (AC-R4.3): exactly one room carries the '*' marker, and it moves with you."""
        session = Session(["n", "map", "e", "map"])
        first, second = session.turns()[2], session.turns()[4]
        self.assertEqual(first.count("[*"), 1)
        self.assertIn("[*Med Bay ]", first)
        self.assertEqual(second.count("[*"), 1)
        self.assertIn("[*Corridor]", second)
        self.assertIn("[ Med Bay ]", second)

    def test_R4_no_line_is_drawn_across_a_sealed_bulkhead(self):
        """R4 (AC-R4.5): Mess Hall sits above Reactor Core but they don't connect."""
        rooms = {"cryo_bay", "medical_bay", "central_corridor", "mess_hall",
                 "engineering", "reactor_core"}
        lines = render_map("reactor_core", rooms).splitlines()
        mess_row = next(i for i, line in enumerate(lines) if "Mess" in line)
        under_mess = lines[mess_row + 1]
        mess_middle = lines[mess_row].index("[ Mess") + 5
        self.assertTrue(len(under_mess) <= mess_middle or under_mess[mess_middle] == " ")
        # Cryo Bay and Engineering share a row but have no door between them.
        self.assertIn("[ Cryo Bay]  [ Engines ]", lines[mess_row + 2])

    def test_R4_fully_explored_map_draws_every_room_and_every_connection(self):
        """R4 (AC-R4.2, AC-R4.5): 11 rooms, 6 horizontal and 6 vertical links."""
        text = render_map("airlock_junction", set(ROOMS))
        for room_id, label in MAP_LABELS.items():
            with self.subTest(room=room_id):
                self.assertIn(label, text)
        self.assertEqual(text.count("--"), 6)
        self.assertEqual(text.count("|"), 6)
        self.assertIn("Rooms visited: 11 of 11", text)

    def test_R4_map_lines_fit_in_50_columns(self):
        """R4 (AC-R4.8): even the fully explored map is no wider than the frame."""
        for current in ROOMS:
            with self.subTest(current=current):
                for line in render_map(current, set(ROOMS)).splitlines():
                    self.assertLessEqual(len(line), 50)

    def test_R4_map_uses_no_oxygen_and_keeps_you_in_place(self):
        """R4 (AC-R4.6): many map checks later, oxygen and room are unchanged."""
        session = Session(["n"] + ["map", "m", "  MAP "] * 4 + ["look"])
        self.assertEqual(session.game.oxygen, 11)
        self.assertEqual(session.game.room.id, "medical_bay")
        self.assertIn("[ OXYGEN: 11/12 ]", session.turns()[-2])  # [-1] is the EOF quit

    def test_R4_map_counts_a_revisited_room_once(self):
        """R4 (AC-R4.7): walking back and forth still shows 2 rooms visited."""
        session = Session(["n", "s", "n", "s", "map"])
        self.assertIn("Rooms visited: 2 of 11", session.turns()[5])

    def test_R4_help_lists_the_map_command(self):
        """R4 (AC-R4.1): the help text mentions 'map'."""
        session = Session(["help"])
        self.assertIn("map", session.turns()[1])


class ScanOutputTests(unittest.TestCase):
    def test_R5_scan_shows_the_current_rooms_name_and_clue(self):
        """R5 (AC-R5.3): scanning in the Medical Bay shows the Medical Bay clue."""
        session = Session(["n", "scan"])
        response = session.turns()[2]
        self.assertEqual(response.splitlines()[0], "[ SCAN: MEDICAL BAY ]")
        self.assertIn(squash(ROOMS["medical_bay"].clue), squash(response))
        self.assertNotIn(squash(ROOMS["cryo_bay"].clue), squash(response))

    def test_R5_every_room_scans_to_its_own_clue(self):
        """R5 (AC-R5.3): render_scan shows each room's clue under its name."""
        for room in ROOMS.values():
            with self.subTest(room=room.id):
                text = render_scan(room)
                self.assertEqual(text.splitlines()[0], f"[ SCAN: {room.name.upper()} ]")
                self.assertEqual(squash(" ".join(text.splitlines()[1:])), squash(room.clue))

    def test_R5_scanning_again_gives_the_same_clue(self):
        """R5 (AC-R5.5): repeated scans in one room print identical text."""
        session = Session(["n", "scan", "sc", "SCAN"])
        turns = session.turns()
        self.assertEqual(turns[2], turns[3])
        self.assertEqual(turns[3], turns[4])

    def test_R5_scan_uses_no_oxygen_and_keeps_you_in_place(self):
        """R5 (AC-R5.4): scans don't cost oxygen or move the player."""
        session = Session(["n"] + ["scan"] * 10 + ["look"])
        self.assertEqual(session.game.oxygen, 11)
        self.assertEqual(session.game.room.id, "medical_bay")
        self.assertIn("[ OXYGEN: 11/12 ]", session.turns()[-2])  # [-1] is the EOF quit

    def test_R5_scan_output_fits_in_50_columns(self):
        """R5 (AC-R5.6): wrapped clues are no wider than the frame."""
        for room in ROOMS.values():
            with self.subTest(room=room.id):
                for line in render_scan(room).splitlines():
                    self.assertLessEqual(len(line), 50)

    def test_R5_help_lists_the_scan_command(self):
        """R5 (AC-R5.1): the help text mentions 'scan'."""
        session = Session(["help"])
        self.assertIn("scan", session.turns()[1])

    def test_R4_R5_help_text_fits_in_50_columns(self):
        """R4 (AC-R4.1) and R5 (AC-R5.1): the longer help list still fits the frame."""
        for line in Session(["help"]).turns()[1].splitlines():
            self.assertLessEqual(len(line), 50)


class Round2PlaythroughTests(unittest.TestCase):
    def test_R4_R5_winning_with_map_and_scan_still_leaves_six_oxygen(self):
        """R4 (AC-R4.6) and R5 (AC-R5.4): free commands don't change the shortest win."""
        inputs = []
        for direction in SHORTEST_ROUTE:
            inputs += ["map", "scan", direction]
        session = Session(inputs)
        self.assertIn(WIN_BANNER, session.text)
        self.assertIn("You escaped with 6 oxygen to spare.", session.text)
        self.assertEqual(session.game.oxygen, 6)

    def test_R4_R5_main_py_accepts_map_and_scan(self):
        """R4 (AC-R4.1) and R5 (AC-R5.1), with AC-G.1: the real entry point runs both."""
        completed = subprocess.run(
            [sys.executable, "main.py"],
            input="map\nscan\n" + "\n".join(SHORTEST_ROUTE) + "\n",
            capture_output=True, text=True, cwd=PROJECT_ROOT, timeout=10,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("SHIP MAP", completed.stdout)
        self.assertIn("[ SCAN: CRYO BAY ]", completed.stdout)
        self.assertIn(WIN_BANNER, completed.stdout)
        self.assertEqual(completed.stderr, "")


def response_lines(session, turn):
    return session.turns()[turn].splitlines()


class ItemDisplayTests(unittest.TestCase):
    def test_R6_starting_room_lists_its_item(self):
        """R6 (AC-R6.3): the opening Cryo Bay display shows the flashlight."""
        opening = Session([]).turns()[0].splitlines()
        self.assertIn("Items here: flashlight", opening)
        # The items line sits between the blank line and the exits line.
        index = opening.index("Items here: flashlight")
        self.assertEqual(opening[index - 1], "")
        self.assertEqual(opening[index + 1], "Exits: north")

    def test_R6_entering_a_room_lists_its_items(self):
        """R6 (AC-R6.3): moving into the Medical Bay shows the medkit."""
        self.assertIn("Items here: medkit", response_lines(Session(["n"]), 1))

    def test_R6_look_lists_the_rooms_items(self):
        """R6 (AC-R6.3): 'look' shows the current room's items too."""
        self.assertIn("Items here: flashlight", response_lines(Session(["look"]), 1))

    def test_R6_room_with_no_items_has_no_items_line(self):
        """R6 (AC-R6.3): empty rooms look exactly as in spec 3.6."""
        response = Session(["n", "e"]).turns()[2]
        self.assertIn("CENTRAL CORRIDOR", response)
        self.assertNotIn("Items here", response)

    def test_R6_taken_item_is_no_longer_listed_in_the_room(self):
        """R6 (AC-R6.3, AC-R6.4): after taking the flashlight, look shows no items."""
        session = Session(["take flashlight", "look"])
        self.assertNotIn("Items here", session.turns()[2])

    def test_R6_render_room_lists_items_passed_in(self):
        """R6 (AC-R6.3): render_room puts the items line just before the exits."""
        lines = render_room(ROOMS["cargo_hold"], 9, items=("keycard", "medkit")).splitlines()
        self.assertEqual(lines[-3], "Items here: keycard, medkit")
        self.assertEqual(lines[-2], exits_line(ROOMS["cargo_hold"]))


class TakeOutputTests(unittest.TestCase):
    def test_R6_take_prints_confirmation(self):
        """R6 (AC-R6.4): 'take flashlight' says you take it."""
        session = Session(["take flashlight"])
        self.assertEqual(session.turns()[1].strip(), "You take the flashlight.")
        self.assertEqual(session.game.inventory, ["flashlight"])

    def test_R6_get_and_mixed_case_names_work(self):
        """R6 (AC-R6.1, AC-R6.7): 'GET  Flashlight' takes the flashlight."""
        session = Session(["GET  Flashlight"])
        self.assertEqual(session.turns()[1].strip(), "You take the flashlight.")

    def test_R6_take_multi_word_item_prints_its_full_name(self):
        """R6 (AC-R6.4): the repair kit is named in full."""
        session = Session(["n", "e", "s", "take Repair   Kit"])
        self.assertEqual(session.turns()[4].strip(), "You take the repair kit.")

    def test_R6_take_missing_item_says_it_is_not_here(self):
        """R6 (AC-R6.5): 'take keycard' in the Cryo Bay says it is not here."""
        session = Session(["take keycard"])
        self.assertEqual(session.turns()[1].strip(), "There is no 'keycard' here.")
        self.assertEqual(session.game.inventory, [])

    def test_R6_partial_name_says_it_is_not_here(self):
        """R6 (AC-R6.7): 'take kit' in Engineering does not take the repair kit."""
        session = Session(["n", "e", "s", "take kit"])
        self.assertEqual(session.turns()[4].strip(), "There is no 'kit' here.")

    def test_R6_take_with_no_name_asks_take_what(self):
        """R6 (AC-R6.1): bare 'take' or 'get' asks 'Take what?'."""
        turns = Session(["take", "get"]).turns()
        self.assertEqual(turns[1].strip(), "Take what?")
        self.assertEqual(turns[2].strip(), "Take what?")

    def test_R6_take_uses_no_oxygen(self):
        """R6 (AC-R6.6): taking leaves the gauge at 12."""
        session = Session(["take flashlight", "look"])
        self.assertIn("[ OXYGEN: 12/12 ]", session.turns()[2])


class InventoryOutputTests(unittest.TestCase):
    def test_R7_empty_inventory_says_so(self):
        """R7 (AC-R7.3): with nothing carried, the inventory is empty."""
        for text in ("inventory", "inv", "i"):
            with self.subTest(text=text):
                self.assertEqual(Session([text]).turns()[1].strip(),
                                 "Your inventory is empty.")

    def test_R7_inventory_lists_items_in_pickup_order(self):
        """R7 (AC-R7.2): each carried item is listed in the order taken."""
        session = Session(["n", "take medkit", "s", "take flashlight", "inventory"])
        self.assertEqual(response_lines(session, 5),
                         ["You are carrying:", "  - medkit", "  - flashlight"])

    def test_R7_inventory_uses_no_oxygen(self):
        """R7 (AC-R7.6): checking the inventory is free."""
        session = Session(["n", "i", "inv", "look"])
        self.assertIn("[ OXYGEN: 11/12 ]", session.turns()[4])


class DropOutputTests(unittest.TestCase):
    def test_R7_drop_prints_confirmation(self):
        """R7 (AC-R7.4): dropping a carried item says so."""
        session = Session(["take flashlight", "drop flashlight"])
        self.assertEqual(session.turns()[2].strip(), "You drop the flashlight.")
        self.assertEqual(session.game.inventory, [])

    def test_R7_dropped_item_is_shown_when_returning_to_the_room(self):
        """R7 (AC-R7.4): drop in the Medical Bay, leave, come back, and it's listed."""
        session = Session(["take flashlight", "n", "drop flashlight", "e", "w"])
        self.assertIn("Items here: medkit, flashlight", response_lines(session, 5))

    def test_R7_dropped_item_can_be_taken_again(self):
        """R7 (AC-R7.4): the dropped item stays until picked up again."""
        session = Session(["take flashlight", "drop flashlight", "take flashlight", "i"])
        self.assertEqual(session.turns()[3].strip(), "You take the flashlight.")
        self.assertIn("  - flashlight", response_lines(session, 4))

    def test_R7_drop_item_not_carried_says_so(self):
        """R7 (AC-R7.5): dropping something not carried changes nothing."""
        session = Session(["drop keycard"])
        self.assertEqual(session.turns()[1].strip(), "You are not carrying 'keycard'.")

    def test_R7_drop_with_no_name_asks_drop_what(self):
        """R7 (AC-R7.5): bare 'drop' asks 'Drop what?'."""
        self.assertEqual(Session(["drop"]).turns()[1].strip(), "Drop what?")

    def test_R7_drop_uses_no_oxygen(self):
        """R7 (AC-R7.6): dropping leaves the gauge unchanged."""
        session = Session(["n", "take medkit", "drop medkit", "look"])
        self.assertIn("[ OXYGEN: 11/12 ]", session.turns()[4])


class ItemHelpAndWidthTests(unittest.TestCase):
    def test_R6_R7_help_lists_take_drop_and_inventory(self):
        """R6 (AC-R6.1) and R7 (AC-R7.1): help mentions every item command."""
        response = Session(["help"]).turns()[1]
        for word in ("take", "get", "drop", "inventory", "inv"):
            with self.subTest(word=word):
                self.assertIn(word, response)

    def test_R7_help_text_still_fits_in_50_columns(self):
        """R7 (AC-R7.8): the help list with item commands fits the frame."""
        for line in Session(["help"]).turns()[1].splitlines():
            self.assertLessEqual(len(line), 50, line)

    def test_R7_all_four_items_in_one_room_fit_in_50_columns(self):
        """R7 (AC-R7.8): a long items line wraps inside the frame."""
        inputs = ["take flashlight", "n", "take medkit", "e", "n", "take keycard",
                  "s", "s", "take repair kit", "drop flashlight", "drop medkit",
                  "drop keycard", "drop repair kit", "look"]
        session = Session(inputs)
        response = session.turns()[len(inputs)]
        self.assertIn("ENGINEERING", response)
        for line in response.splitlines():
            self.assertLessEqual(len(line), 50, line)
        self.assertIn("Items here: flashlight, medkit, keycard, repair kit",
                      squash(response))

    def test_R7_full_inventory_fits_in_50_columns(self):
        """R7 (AC-R7.8): the inventory list with every item fits the frame."""
        inputs = ["take flashlight", "n", "take medkit", "e", "n", "take keycard",
                  "s", "s", "take repair kit", "inventory"]
        session = Session(inputs)
        lines = response_lines(session, len(inputs))
        self.assertEqual(len([line for line in lines if line.startswith("  - ")]), 4)
        for line in lines:
            self.assertLessEqual(len(line), 50, line)


class Round3PlaythroughTests(unittest.TestCase):
    def test_R6_R7_collecting_items_on_the_way_still_wins_with_six_oxygen(self):
        """R6 (AC-R6.6) and R7 (AC-R7.6): items don't change the shortest win."""
        inputs = ["take flashlight", "n", "take medkit", "i", "e", "s",
                  "take repair kit", "drop medkit", "s", "e", "inventory", "e"]
        session = Session(inputs)
        self.assertIn(WIN_BANNER, session.text)
        self.assertIn("You escaped with 6 oxygen to spare.", session.text)
        self.assertEqual(session.game.inventory, ["flashlight", "repair kit"])

    def test_R6_R7_main_py_accepts_item_commands(self):
        """R6 (AC-R6.1) and R7 (AC-R7.1), with AC-G.1: the real entry point runs them."""
        completed = subprocess.run(
            [sys.executable, "main.py"],
            input="take flashlight\ni\ndrop flashlight\nlook\nq\n",
            capture_output=True, text=True, cwd=PROJECT_ROOT, timeout=10,
        )
        self.assertEqual(completed.returncode, 0)
        self.assertIn("You take the flashlight.", completed.stdout)
        self.assertIn("  - flashlight", completed.stdout)
        self.assertIn("You drop the flashlight.", completed.stdout)
        self.assertNotIn("Traceback", completed.stderr)


# ----- Round 4: health, hazards, and the medkit (R8, R9) -------------------

TO_REACTOR = ["n", "e", "s", "e"]
REACTOR_DEATH = TO_REACTOR + ["w", "e"] * 4
DEATH_HEADER = ">>> CRITICAL INJURIES <<<"
DEATH_TEXT = "You didn't survive."
HAZARD_HEADER = "!! HAZARD: -2 HEALTH !!"


def gauge_lines(text):
    """The (oxygen, health) gauge line pairs in a block of output."""
    lines = text.splitlines()
    return [(line, lines[i + 1]) for i, line in enumerate(lines[:-1])
            if line.startswith("[ OXYGEN:")]


class HealthDisplayTests(unittest.TestCase):
    def test_R8_opening_shows_full_health_under_oxygen(self):
        """R8 (AC-R8.2): the first room display has the health gauge line."""
        opening = Session([]).turns()[0]
        self.assertEqual(gauge_lines(opening), [("[ OXYGEN: 12/12 ]", "[ HEALTH: 10/10 ]")])

    def test_R8_every_move_shows_health_under_oxygen(self):
        """R8 (AC-R8.2): entering a room shows current health on the next line."""
        turns = Session(TO_REACTOR).turns()
        expected = [("11", "10"), ("10", "10"), ("9", "10"), ("8", "8")]
        for index, (oxygen, health) in enumerate(expected, start=1):
            with self.subTest(move=index):
                self.assertEqual(gauge_lines(turns[index]),
                                 [(f"[ OXYGEN: {oxygen}/12 ]", f"[ HEALTH: {health}/10 ]")])

    def test_R8_look_shows_health(self):
        """R8 (AC-R8.2): look shows the health gauge, and costs no health."""
        turns = Session(TO_REACTOR + ["look"]).turns()
        self.assertIn("[ HEALTH: 8/10 ]", turns[5].splitlines())
        self.assertNotIn(HAZARD_HEADER, turns[5])

    def test_R8_final_displays_show_health(self):
        """R8 (AC-R8.2): the win, oxygen-loss, and death displays show health."""
        cases = [(SHORTEST_ROUTE, "[ HEALTH: 8/10 ]"),
                 (WANDER_LOSS, "[ HEALTH: 10/10 ]"),
                 (REACTOR_DEATH, "[ HEALTH: 0/10 ]")]
        for inputs, gauge in cases:
            with self.subTest(inputs=inputs):
                self.assertIn(gauge, Session(inputs).turns()[-1].splitlines())

    def test_R8_render_room_shows_health_when_given(self):
        """R8 (AC-R8.2): render_room puts the health gauge last, under oxygen."""
        lines = render_room(ROOMS["engineering"], 3, health=6).splitlines()
        self.assertEqual(lines[-2], "[ OXYGEN: 3/12 ]  !! LOW OXYGEN !!")
        self.assertEqual(lines[-1], "[ HEALTH: 6/10 ]")


class HazardOutputTests(unittest.TestCase):
    def test_R8_entering_the_reactor_shows_its_hazard_message(self):
        """R8 (AC-R8.4): the hazard message follows the room display."""
        turn = Session(TO_REACTOR).turns()[4]
        lines = turn.splitlines()
        self.assertIn(HAZARD_HEADER, lines)
        start = lines.index(HAZARD_HEADER)
        self.assertEqual(lines[start - 1], "")
        self.assertEqual(lines[start - 2], "[ HEALTH: 8/10 ]")
        self.assertEqual(squash(" ".join(lines[start + 1:])),
                         "Radiation from the reactor scorches your suit.")

    def test_R8_entering_the_cargo_hold_shows_its_hazard_message(self):
        """R8 (AC-R8.4): the Cargo Hold has its own hazard text."""
        turn = Session(["n", "e", "s", "s"]).turns()[4]
        self.assertIn(HAZARD_HEADER, turn)
        self.assertIn("A drifting crate slams into you.", turn)

    def test_R8_every_hazard_room_has_a_message(self):
        """R8 (AC-R8.4): HAZARD_MESSAGES covers exactly the hazard rooms."""
        hazards = {room.id for room in ROOMS.values() if room.hazard}
        self.assertEqual(set(HAZARD_MESSAGES), hazards)

    def test_R8_going_back_into_a_hazard_shows_the_message_again(self):
        """R8 (AC-R8.4): every entry shows the hazard message."""
        turns = Session(TO_REACTOR + ["w", "e"]).turns()
        self.assertIn(HAZARD_HEADER, turns[4])
        self.assertNotIn(HAZARD_HEADER, turns[5])
        self.assertIn(HAZARD_HEADER, turns[6])
        self.assertIn("[ HEALTH: 6/10 ]", turns[6])

    def test_R8_safe_rooms_show_no_hazard_message(self):
        """R8 (AC-R8.5): only hazard rooms print the message."""
        session = Session(["n", "e", "n", "e", "s", "w", "s", "s", "e"])
        self.assertNotIn("HAZARD", "\n".join(session.turns()[1:7]))

    def test_R8_shortest_win_shows_the_hazard_then_wins_with_8_health(self):
        """R8 (AC-R8.8): the player escapes without healing."""
        session = Session(SHORTEST_ROUTE)
        self.assertIn(HAZARD_HEADER, session.turns()[4])
        self.assertIn(WIN_BANNER, session.text)
        self.assertEqual(session.game.health, 8)


class DeathOutputTests(unittest.TestCase):
    def test_R8_health_ending_is_shown_when_health_and_oxygen_hit_zero(self):
        """R8 (AC-R8.6, AC-R8.7): five reactor entries print the death ending."""
        session = Session(REACTOR_DEATH + ["look"])
        final = session.turns()[-1]
        self.assertEqual(len(session.turns()), len(REACTOR_DEATH) + 1)  # look never read
        for text in (HAZARD_HEADER, DEATH_HEADER, DEATH_TEXT, LOSS_BANNER):
            with self.subTest(text=text):
                self.assertIn(text, final)
        self.assertNotIn("OXYGEN DEPLETED", final)
        self.assertLess(final.index("[ HEALTH: 0/10 ]"), final.index(HAZARD_HEADER))
        self.assertLess(final.index(HAZARD_HEADER), final.index(DEATH_HEADER))
        self.assertLess(final.index(DEATH_TEXT), final.index(LOSS_BANNER))
        self.assertEqual(session.game.status, Status.LOST)

    def test_R8_oxygen_loss_still_shows_the_oxygen_ending(self):
        """R8 (AC-R8.7) with R3 (AC-R3.6): reaching the pod on move 12 is unchanged."""
        final = Session(TWELVE_MOVE_POD).turns()[-1]
        self.assertIn(">>> OXYGEN DEPLETED <<<", final)
        self.assertNotIn(DEATH_HEADER, final)


class UseOutputTests(unittest.TestCase):
    def test_R9_using_the_medkit_reports_health_restored(self):
        """R9 (AC-R9.2, AC-R9.3): 'You use the medkit and restore N health.'"""
        inputs = ["n", "take medkit", "e", "s", "e", "w", "e", "use medkit", "i"]
        turns = Session(inputs).turns()
        self.assertEqual(turns[8], "You use the medkit and restore 4 health.\n")
        self.assertIn("Your inventory is empty.", turns[9])

    def test_R9_capped_healing_reports_the_amount_actually_restored(self):
        """R9 (AC-R9.2): at 8 health the message says 2."""
        turns = Session(["n", "take medkit", "e", "s", "e", "use medkit", "look"]).turns()
        self.assertEqual(turns[6], "You use the medkit and restore 2 health.\n")
        self.assertIn("[ HEALTH: 10/10 ]", turns[7])

    def test_R9_full_health_keeps_the_medkit(self):
        """R9 (AC-R9.5): the medkit isn't wasted at full health."""
        turns = Session(["n", "take medkit", "use medkit", "i"]).turns()
        self.assertEqual(turns[3], "You are already at full health.\n"
                                   "You keep the medkit for later.\n")
        self.assertIn("  - medkit", turns[4])

    def test_R9_using_an_item_not_carried_says_so(self):
        """R9 (AC-R9.4): a medkit still in the room has to be taken first."""
        turns = Session(["n", "USE  MEDKIT", "use banana"]).turns()
        self.assertEqual(turns[2], "You are not carrying 'medkit'.\n")
        self.assertEqual(turns[3], "You are not carrying 'banana'.\n")

    def test_R9_other_items_cannot_be_used(self):
        """R9 (AC-R9.7): 'use flashlight' says it can't be used."""
        turns = Session(["take flashlight", "use flashlight"]).turns()
        self.assertEqual(turns[2], "You can't use the flashlight.\n")

    def test_R9_use_with_no_name_asks_what(self):
        """R9 (AC-R9.1): bare 'use' gives 'Use what?'."""
        self.assertEqual(Session(["use"]).turns()[1], "Use what?\n")

    def test_R9_using_the_medkit_costs_no_oxygen(self):
        """R9 (AC-R9.6): oxygen is the same before and after use."""
        session = Session(["n", "take medkit", "e", "s", "e", "use medkit", "look"])
        self.assertIn("[ OXYGEN: 8/12 ]", session.turns()[7])

    def test_R9_help_lists_use(self):
        """R9 (AC-R9.1): help shows the use command."""
        help_text = Session(["help"]).turns()[1]
        self.assertIn("use <item>", help_text)

    def test_R8_R9_new_output_fits_in_50_columns(self):
        """R8 (AC-R8.9) and R9: help, hazards, death, and use messages fit."""
        inputs = (["help", "take flashlight", "use flashlight", "use", "use banana",
                   "n", "take medkit", "use medkit", "e", "s", "s",
                   "e", "n", "s", "w", "e", "n", "s", "w"])
        session = Session(inputs)
        self.assertIn(DEATH_HEADER, session.text)
        for line in session.text.splitlines():
            if line.startswith(("Unknown command", "The hatch", "You close", "Move with")):
                continue  # Round 1 lines already known to be wider (handoff 3)
            with self.subTest(line=line):
                self.assertLessEqual(len(line), 50)
        for room_id, message in HAZARD_MESSAGES.items():
            with self.subTest(room=room_id):
                self.assertLessEqual(len(message), 50)


if __name__ == "__main__":
    unittest.main()
