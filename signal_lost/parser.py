"""Turns raw text typed by the player into a structured Command.

The parser never changes game state; it only interprets text.
"""

from dataclasses import dataclass
from typing import Optional

_DIRECTION_ALIASES = {
    "north": "north", "n": "north",
    "south": "south", "s": "south",
    "east": "east", "e": "east",
    "west": "west", "w": "west",
}

_COMMAND_ALIASES = {
    "look": "look", "l": "look",
    "help": "help", "h": "help", "?": "help",
    "quit": "quit", "q": "quit", "exit": "quit",
    "map": "map", "m": "map",
    "scan": "scan", "sc": "scan",
}

_GO = "go"


@dataclass(frozen=True)
class Command:
    """A parsed player command.

    ``kind`` is one of ``"move"``, ``"help"``, ``"look"``, ``"quit"``,
    ``"map"``, ``"scan"``, ``"empty"``, or ``"unknown"``. ``arg`` is the direction for a move,
    the text the player typed (trimmed) for unknown input, and ``None``
    otherwise.
    """

    kind: str
    arg: Optional[str] = None


def parse(text):
    """Parse one line of player input into a Command.

    Case and extra whitespace are ignored, so ``"  GO   N "`` is the same
    as ``"north"``.
    """
    original = text.strip()
    words = original.lower().split()

    if not words:
        return Command("empty")

    if len(words) == 1:
        word = words[0]
        if word in _DIRECTION_ALIASES:
            return Command("move", _DIRECTION_ALIASES[word])
        if word in _COMMAND_ALIASES:
            return Command(_COMMAND_ALIASES[word])

    if len(words) == 2 and words[0] == _GO and words[1] in _DIRECTION_ALIASES:
        return Command("move", _DIRECTION_ALIASES[words[1]])

    return Command("unknown", original)


def is_go_attempt(command):
    """True if an unknown command was a malformed ``go`` (e.g. ``go`` or ``go up``).

    The CLI uses this to show "Go where?" instead of a generic
    unknown-command message.
    """
    if command.kind != "unknown" or not command.arg:
        return False
    return command.arg.lower().split()[0] == _GO
