"""Reading and writing the save file for Signal Lost (spec.md Section 3.12).

This module only knows about files and JSON. It knows nothing about rooms,
oxygen, or the rules: game.py decides what goes into the file and checks
what comes back out.
"""

import json
import os

# One save slot, in the folder the game is started from.
SAVE_FILE = "signal_lost_save.json"
_TEMP_SUFFIX = ".tmp"


class NoSaveFile(Exception):
    """There is no save file to load."""


class DamagedSave(Exception):
    """The save file exists but can't be used."""


def write(path, data):
    """Write ``data`` to ``path`` as JSON, replacing any earlier save.

    The JSON is written to a temporary file next to ``path`` and then moved
    into place, so a write that fails part-way never damages the previous
    save. Raises ``OSError`` if the file can't be written, and ``TypeError``
    or ``ValueError`` if ``data`` can't be turned into JSON (before anything
    touches the disk).
    """
    text = json.dumps(data, indent=2) + "\n"
    temp_path = os.fspath(path) + _TEMP_SUFFIX
    try:
        with open(temp_path, "w", encoding="utf-8") as file:
            file.write(text)
        os.replace(temp_path, path)
    except OSError:
        try:
            os.remove(temp_path)
        except OSError:
            pass
        raise


def read(path):
    """Return the JSON value stored at ``path``.

    Raises ``NoSaveFile`` if there is no file, and ``DamagedSave`` if the
    file can't be read or isn't valid UTF-8 JSON. The file is never changed.
    """
    try:
        with open(path, encoding="utf-8") as file:
            text = file.read()
    except FileNotFoundError:
        raise NoSaveFile(path) from None
    except (OSError, UnicodeDecodeError) as error:
        raise DamagedSave(f"can't read {path}: {error}") from None
    try:
        return json.loads(text)
    except (ValueError, RecursionError) as error:
        raise DamagedSave(f"{path} is not valid JSON: {error}") from None
