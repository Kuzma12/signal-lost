"""Terminal output and full-playthrough tests for signal_lost.cli.

Every test name starts with the requirement it checks (R1, R2, or R3), and
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

from signal_lost.cli import render_room, run
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


if __name__ == "__main__":
    unittest.main()
