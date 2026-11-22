"""Command parsing tests for signal_lost.parser.

Every test name starts with the requirement it checks (R1-R7), and
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


class Round2CommandParsingTests(unittest.TestCase):
    def test_R4_map_and_its_alias_parse_to_map(self):
        """R4 (AC-R4.1): 'map' and 'm' are the map command, ignoring case and spaces."""
        for text in ("map", "m", "MAP", "  Map  ", "M"):
            with self.subTest(text=text):
                self.assertEqual(parse(text), Command("map"))

    def test_R5_scan_and_its_alias_parse_to_scan(self):
        """R5 (AC-R5.1): 'scan' and 'sc' are the scan command, ignoring case and spaces."""
        for text in ("scan", "sc", "SCAN", "  Scan ", "SC"):
            with self.subTest(text=text):
                self.assertEqual(parse(text), Command("scan"))

    def test_R5_s_still_means_south_not_scan(self):
        """R5 (AC-R5.1) and R1 (AC-R1.2): the scan alias does not take over 's'."""
        self.assertEqual(parse("s"), Command("move", "south"))

    def test_R4_map_and_scan_with_extra_words_are_unknown(self):
        """R4 (AC-R4.1) and R5 (AC-R5.1): only the bare words are commands."""
        for text in ("map room", "scan north", "go map"):
            with self.subTest(text=text):
                self.assertEqual(parse(text).kind, "unknown")


class ItemParsingTests(unittest.TestCase):
    def test_R6_take_and_get_parse_to_take_with_the_item_name(self):
        """R6 (AC-R6.1): 'take <item>' and 'get <item>' are the take command."""
        for text in ("take keycard", "get keycard", "TAKE KEYCARD", "  Get   Keycard "):
            with self.subTest(text=text):
                self.assertEqual(parse(text), Command("take", "keycard"))

    def test_R6_multi_word_item_names_are_normalized(self):
        """R6 (AC-R6.1, AC-R6.7): case and extra spaces inside the name are ignored."""
        for text in ("take repair kit", "  TAKE  Repair   Kit ", "get REPAIR KIT"):
            with self.subTest(text=text):
                self.assertEqual(parse(text), Command("take", "repair kit"))

    def test_R6_take_with_no_item_name_has_no_arg(self):
        """R6 (AC-R6.1): bare 'take' or 'get' is a take command with no name."""
        for text in ("take", "GET", "  take  "):
            with self.subTest(text=text):
                self.assertEqual(parse(text), Command("take"))

    def test_R6_partial_names_are_passed_through_unchanged(self):
        """R6 (AC-R6.7): the parser does not guess; 'take kit' names 'kit'."""
        self.assertEqual(parse("take kit"), Command("take", "kit"))

    def test_R7_drop_parses_to_drop_with_the_item_name(self):
        """R7 (AC-R7.1): 'drop <item>' is the drop command with a normalized name."""
        for text, name in (("drop medkit", "medkit"), ("  DROP  Repair Kit", "repair kit")):
            with self.subTest(text=text):
                self.assertEqual(parse(text), Command("drop", name))

    def test_R7_drop_with_no_item_name_has_no_arg(self):
        """R7 (AC-R7.5): bare 'drop' is a drop command with no name."""
        self.assertEqual(parse("drop"), Command("drop"))

    def test_R7_inventory_and_its_aliases_parse_to_inventory(self):
        """R7 (AC-R7.1): 'inventory', 'inv', 'i' are the inventory command."""
        for text in ("inventory", "inv", "i", "INVENTORY", "  Inv ", "I"):
            with self.subTest(text=text):
                self.assertEqual(parse(text), Command("inventory"))

    def test_R7_inventory_with_extra_words_is_unknown(self):
        """R7 (AC-R7.1): only the bare inventory words are the command."""
        for text in ("inventory now", "i keycard"):
            with self.subTest(text=text):
                self.assertEqual(parse(text).kind, "unknown")

    def test_R6_R7_item_commands_do_not_change_existing_aliases(self):
        """R6 (AC-R6.1) and R7 (AC-R7.1): directions and 'go' still parse as before."""
        self.assertEqual(parse("e"), Command("move", "east"))
        self.assertEqual(parse("go east"), Command("move", "east"))
        self.assertFalse(is_go_attempt(parse("take keycard")))


if __name__ == "__main__":
    unittest.main()
