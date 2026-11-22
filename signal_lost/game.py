"""Game state and rules for Signal Lost.

This module decides what happens on each turn and reports it as a
TurnResult. It never prints or reads input; the CLI does all of that.
"""

from dataclasses import dataclass
from enum import Enum

from .world import DIRECTIONS, ESCAPE_ROOM, START_ROOM, Room, build_ship

STARTING_OXYGEN = 12
OXYGEN_PER_MOVE = 1


class Status(Enum):
    PLAYING = "playing"
    WON = "won"
    LOST = "lost"
    QUIT = "quit"


class Outcome(Enum):
    """What a single call to Game.handle() did."""

    MOVED = "moved"          # moved to a new room and the game continues
    BLOCKED = "blocked"      # valid direction, but no exit that way
    INVALID = "invalid"      # unrecognized or malformed command
    EMPTY = "empty"          # blank input
    LOOKED = "looked"        # re-described the current room
    HELP = "help"            # asked for the command list
    WON = "won"              # moved into the escape pod with oxygen left
    LOST = "lost"            # moved and oxygen hit zero
    QUIT = "quit"            # player gave up
    GAME_OVER = "game_over"  # command ignored because the game already ended


@dataclass
class TurnResult:
    outcome: Outcome
    room: Room
    oxygen: int
    oxygen_used: int = 0


class Game:
    """Holds the player's current room, oxygen, and game status."""

    def __init__(self, rooms=None):
        self.rooms = rooms if rooms is not None else build_ship()
        self.room_id = START_ROOM
        self.oxygen = STARTING_OXYGEN
        self.status = Status.PLAYING
        self._handlers = {
            "move": self._move,
            "look": self._look,
            "help": self._help,
            "quit": self._quit,
            "empty": self._empty,
            "unknown": self._invalid,
        }

    @property
    def room(self):
        return self.rooms[self.room_id]

    @property
    def is_over(self):
        return self.status is not Status.PLAYING

    def handle(self, command):
        """Apply one Command to the game and return what happened."""
        if self.is_over:
            return self._result(Outcome.GAME_OVER)
        handler = self._handlers.get(command.kind, self._invalid)
        return handler(command)

    # ----- command handlers ------------------------------------------------

    def _move(self, command):
        direction = command.arg
        if direction not in DIRECTIONS:
            return self._result(Outcome.INVALID)
        destination = self.room.exits.get(direction)
        if destination is None:
            return self._result(Outcome.BLOCKED)

        # Turn resolution order from spec.md Section 4.2.
        self.room_id = destination
        self.oxygen = max(0, self.oxygen - OXYGEN_PER_MOVE)

        if self.room_id == ESCAPE_ROOM and self.oxygen > 0:
            self.status = Status.WON
            outcome = Outcome.WON
        elif self.oxygen == 0:
            self.status = Status.LOST
            outcome = Outcome.LOST
        else:
            outcome = Outcome.MOVED
        return self._result(outcome, oxygen_used=OXYGEN_PER_MOVE)

    def _look(self, command):
        return self._result(Outcome.LOOKED)

    def _help(self, command):
        return self._result(Outcome.HELP)

    def _quit(self, command):
        self.status = Status.QUIT
        return self._result(Outcome.QUIT)

    def _empty(self, command):
        return self._result(Outcome.EMPTY)

    def _invalid(self, command):
        return self._result(Outcome.INVALID)

    def _result(self, outcome, oxygen_used=0):
        return TurnResult(outcome, self.room, self.oxygen, oxygen_used)
