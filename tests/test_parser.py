"""Command parsing tests for signal_lost.parser.

Every test name starts with the requirement it checks (R1, R2, or R3), and
its docstring names the acceptance criterion from spec.md Section 6.
"""

import unittest

from signal_lost.parser import Command, is_go_attempt, parse

DIRECTION_SHORTCUTS = {"north": "n", "south": "s", "east": "e", "west": "w"}


class MovementParsingTests(unittest.TestCase):
    def test_R1_full_direction_words_parse_to_moves(self):
        """R1 (AC-R1.1): 'north', 'south', 'east', 'west' are move commands."""
        for direction in DIRECTION_SHORTCUTS:
            with self.subTest(direction=direction):
                self.assertEqual(parse(direction), Command("move", direction))

    def test_R1_single_letter_shortcuts_parse_to_moves(self):
        """R1 (AC-R1.2): 'n', 's', 'e', 'w' behave like the full words."""
        for direction, shortcut in DIRECTION_SHORTCUTS.items():
            with self.subTest(shortcut=shortcut):
                self.assertEqual(parse(shortcut), Command("move", direction))

    def test_R1_go_prefix_parses_to_moves(self):
        """R1 (AC-R1.2): 'go north' and 'go n' behave like 'north'."""
        for direction, shortcut in DIRECTION_SHORTCUTS.items():
            with self.subTest(direction=direction):
                self.assertEqual(parse(f"go {direction}"), Command("move", direction))
                self.assertEqual(parse(f"go {shortcut}"), Command("move", direction))

    def test_R1_case_and_extra_spaces_are_ignored(self):
        """R1 (AC-R1.3): '  NoRtH  ', 'GO N', 'go    east', tabs and newlines all work."""
        cases = {
            "  NoRtH  ": "north",
            "GO N": "north",
            "Go   South": "south",
            "go    east": "east",
            "\tWEST\n": "west",
            "  S ": "south",
        }
        for text, direction in cases.items():
            with self.subTest(text=text):
                self.assertEqual(parse(text), Command("move", direction))


class NonMovementParsingTests(unittest.TestCase):
    def test_R2_look_and_its_alias_parse_to_look(self):
        """R2 (spec 3.5): 'look' and 'l' re-show the room information."""
        for text in ("look", "l", "LOOK", "  Look "):
            with self.subTest(text=text):
                self.assertEqual(parse(text).kind, "look")

    def test_R3_help_and_its_aliases_parse_to_help(self):
        """R3 (spec 3.5, AC-R3.3): 'help', 'h', '?' are the oxygen-free help command."""
        for text in ("help", "h", "?", "HELP", " ? "):
            with self.subTest(text=text):
                self.assertEqual(parse(text).kind, "help")

    def test_R3_quit_and_its_aliases_parse_to_quit(self):
        """R3 (spec 3.5, AC-R3.7): 'quit', 'q', 'exit' end the game."""
        for text in ("quit", "q", "exit", "QUIT", "  Exit "):
            with self.subTest(text=text):
                self.assertEqual(parse(text).kind, "quit")


class InvalidInputParsingTests(unittest.TestCase):
    def test_R1_unrecognized_words_parse_to_unknown_with_original_text(self):
        """R1 (AC-R1.7): 'fly' and 'jump' are unknown; arg keeps what was typed."""
        self.assertEqual(parse("fly"), Command("unknown", "fly"))
        self.assertEqual(parse("  Jump  "), Command("unknown", "Jump"))

    def test_R1_go_without_a_direction_is_unknown(self):
        """R1 (AC-R1.7): a bare 'go' is a malformed go command."""
        command = parse("go")
        self.assertEqual(command.kind, "unknown")
        self.assertTrue(is_go_attempt(command))

    def test_R1_go_with_a_bad_direction_is_unknown(self):
        """R1 (AC-R1.7): 'go up' and 'go north now' are malformed go commands."""
        for text in ("go up", "GO UP", "go north now", "go fly"):
            with self.subTest(text=text):
                command = parse(text)
                self.assertEqual(command.kind, "unknown")
                self.assertTrue(is_go_attempt(command))

    def test_R1_other_unknown_input_is_not_a_go_attempt(self):
        """R1 (AC-R1.7): only input starting with the word 'go' counts as a go attempt."""
        for text in ("fly", "gopher", "north please", "dance"):
            with self.subTest(text=text):
                command = parse(text)
                self.assertEqual(command.kind, "unknown")
                self.assertFalse(is_go_attempt(command))

    def test_R1_empty_and_whitespace_input_parse_to_empty(self):
        """R1 (AC-R1.7): '' and '   ' are empty input."""
        for text in ("", "   ", "\t", "\n"):
            with self.subTest(text=repr(text)):
                self.assertEqual(parse(text), Command("empty", None))

    def test_R1_parse_never_raises_on_strange_input(self):
        """R1 (AC-R1.7): odd input never crashes the parser."""
        for text in ("!!!", "go go go", "n s e w", "123", "north\x00", "é", "go\tnorth"):
            with self.subTest(text=repr(text)):
                command = parse(text)
                self.assertIsInstance(command, Command)

    def test_R1_parse_does_not_mutate_anything(self):
        """R1 (spec 2.1): parsing the same text twice gives equal results."""
        self.assertEqual(parse("go north"), parse("go north"))


if __name__ == "__main__":
    unittest.main()
