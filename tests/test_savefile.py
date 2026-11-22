"""Save file tests for signal_lost.savefile (Round 6).

Every test name starts with the requirement it checks (R11-R12), and
its docstring names the acceptance criterion from spec.md Section 6.
Every test works in its own temporary folder, so nothing is written into
the project.
"""

import ast
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from signal_lost import savefile
from signal_lost.savefile import SAVE_FILE, DamagedSave, NoSaveFile, read, write

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SAMPLE = {"version": 1, "room": "cryo_bay", "inventory": ["repair kit"],
          "pod_locked": True}


class SaveFileTestCase(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.folder = Path(folder.name)
        self.path = self.folder / SAVE_FILE


class WriteTests(SaveFileTestCase):
    def test_R11_default_save_file_is_in_the_current_folder(self):
        """R11 (AC-R11.2): the save file is signal_lost_save.json, a relative path."""
        self.assertEqual(SAVE_FILE, "signal_lost_save.json")
        self.assertFalse(Path(SAVE_FILE).is_absolute())

    def test_R11_write_then_read_gives_back_the_same_data(self):
        """R11 (AC-R11.2) and R12 (AC-R12.2): the data survives a round trip."""
        write(self.path, SAMPLE)
        self.assertEqual(read(self.path), SAMPLE)

    def test_R11_file_is_utf8_json_ending_in_a_newline(self):
        """R11 (AC-R11.2): the file is plain JSON any tool can read."""
        write(self.path, SAMPLE)
        text = self.path.read_bytes().decode("utf-8")
        self.assertTrue(text.endswith("}\n"))
        self.assertEqual(json.loads(text), SAMPLE)

    def test_R11_write_accepts_a_string_path(self):
        """R11 (AC-R11.2): Game passes a plain file name by default."""
        write(str(self.path), SAMPLE)
        self.assertEqual(read(str(self.path)), SAMPLE)

    def test_R11_writing_again_replaces_the_earlier_save(self):
        """R11 (AC-R11.5): one slot; the newest save wins."""
        write(self.path, SAMPLE)
        write(self.path, {"version": 1, "room": "bridge"})
        self.assertEqual(read(self.path), {"version": 1, "room": "bridge"})

    def test_R11_no_temporary_file_is_left_behind(self):
        """R11 (AC-R11.6): the temporary file is moved into place."""
        write(self.path, SAMPLE)
        self.assertEqual([p.name for p in self.folder.iterdir()], [SAVE_FILE])

    def test_R11_failed_write_raises_and_keeps_the_earlier_save(self):
        """R11 (AC-R11.6): a write that fails can't damage the last save."""
        write(self.path, SAMPLE)
        before = self.path.read_bytes()
        with self.assertRaises(TypeError):
            write(self.path, {"bad": object()})   # not JSON-serializable
        self.assertEqual(self.path.read_bytes(), before)
        self.assertEqual([p.name for p in self.folder.iterdir()], [SAVE_FILE])

    def test_R11_writing_into_a_missing_folder_raises_oserror(self):
        """R11 (AC-R11.6): an unwritable path raises OSError for Game to report."""
        with self.assertRaises(OSError):
            write(self.folder / "missing" / SAVE_FILE, SAMPLE)

    def test_R11_writing_over_a_folder_raises_oserror(self):
        """R11 (AC-R11.6): a folder with the save file's name can't be replaced."""
        self.path.mkdir()
        with self.assertRaises(OSError):
            write(self.path, SAMPLE)
        self.assertTrue(self.path.is_dir())


class ReadTests(SaveFileTestCase):
    def test_R12_missing_file_raises_no_save_file(self):
        """R12 (AC-R12.6): no save is its own case, not a crash."""
        with self.assertRaises(NoSaveFile):
            read(self.path)

    def test_R12_bad_files_raise_damaged_save(self):
        """R12 (AC-R12.7): empty, cut-off, non-JSON, and non-UTF-8 files are damaged."""
        contents = {
            "empty": b"",
            "not json": b"hello, ship",
            "cut off": b'{"version": 1, "room": "cryo',
            "not utf-8": b'{"room": "\xff\xfe"}',
            "trailing junk": b'{"version": 1} extra',
        }
        for label, data in contents.items():
            with self.subTest(label):
                self.path.write_bytes(data)
                with self.assertRaises(DamagedSave):
                    read(self.path)

    def test_R12_a_folder_with_the_save_name_is_damaged(self):
        """R12 (AC-R12.7): a save path that can't be read is damaged, not missing."""
        self.path.mkdir()
        with self.assertRaises(DamagedSave):
            read(self.path)

    def test_R12_read_returns_any_json_value_for_game_to_check(self):
        """R12 (AC-R12.7): the file layer parses JSON; game.py checks its shape."""
        self.path.write_text("[1, 2, 3]\n", encoding="utf-8")
        self.assertEqual(read(self.path), [1, 2, 3])

    def test_R12_reading_never_changes_the_file(self):
        """R12 (AC-R12.5): loading leaves the save file as it was."""
        self.path.write_bytes(b"not json")
        with self.assertRaises(DamagedSave):
            read(self.path)
        self.assertEqual(self.path.read_bytes(), b"not json")

    def test_R12_both_errors_are_distinct_exceptions(self):
        """R12 (AC-R12.6, AC-R12.7): the game can tell 'missing' from 'damaged'."""
        self.assertTrue(issubclass(NoSaveFile, Exception))
        self.assertTrue(issubclass(DamagedSave, Exception))
        self.assertFalse(issubclass(NoSaveFile, DamagedSave))
        self.assertFalse(issubclass(DamagedSave, NoSaveFile))


class ProjectRulesTests(unittest.TestCase):
    def test_R11_save_files_are_ignored_by_git(self):
        """R11 (AC-R11.7): the save file and its temporary file are git-ignored."""
        for name in (SAVE_FILE, SAVE_FILE + ".tmp"):
            with self.subTest(name):
                completed = subprocess.run(
                    ["git", "check-ignore", "--no-index", "-q", name],
                    cwd=PROJECT_ROOT, capture_output=True, timeout=10)
                self.assertEqual(completed.returncode, 0,
                                 f"{name} is not ignored by .gitignore")

    def test_R11_savefile_imports_only_the_standard_library(self):
        """R11 (AC-R11.7): no third-party packages and no game modules."""
        source = Path(savefile.__file__).read_text(encoding="utf-8")
        imported = set()
        for node in ast.walk(ast.parse(source)):
            if isinstance(node, ast.Import):
                imported.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                self.assertEqual(node.level, 0, "savefile must not import game modules")
                imported.add(node.module.split(".")[0])
        stdlib = getattr(sys, "stdlib_module_names", None)
        if stdlib is not None:
            self.assertLessEqual(imported, set(stdlib))
        self.assertLessEqual(imported, {"json", "os", "pathlib", "tempfile"})


if __name__ == "__main__":
    unittest.main()
