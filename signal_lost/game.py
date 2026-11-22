"""Game state and rules for Signal Lost.

This module decides what happens on each turn and reports it as a
TurnResult. It never prints or reads input; the CLI does all of that.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional

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
    MAPPED = "mapped"        # asked for the map of visited rooms
    SCANNED = "scanned"      # scanned the current room for a clue
    TAKEN = "taken"          # picked up an item in the current room
    NOT_HERE = "not_here"    # tried to take an item that isn't in the room
    DROPPED = "dropped"      # left a carried item in the current room
    NOT_CARRIED = "not_carried"  # tried to drop an item not being carried
    INVENTORY = "inventory"  # asked what the player is carrying
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
    visited: frozenset = frozenset()
    items: tuple = ()        # items in the current room now
    inventory: tuple = ()    # items carried, in pickup order
    item: Optional[str] = None  # item named by a take or drop


class Game:
    """Holds the player's current room, oxygen, game status, the rooms
    visited so far, the items in each room, and the player's inventory."""

    def __init__(self, rooms=None):
        self.rooms = rooms if rooms is not None else build_ship()
        self.room_id = START_ROOM
        self.oxygen = STARTING_OXYGEN
        self.status = Status.PLAYING
        self.visited = {START_ROOM}
        # Every item is in exactly one place: one room's list or the
        # inventory (spec.md Section 3.9).
        self.room_items = {room_id: list(room.items)
                           for room_id, room in self.rooms.items()}
        self.inventory = []
        self._handlers = {
            "move": self._move,
            "look": self._look,
            "help": self._help,
            "quit": self._quit,
            "map": self._map,
            "scan": self._scan,
            "take": self._take,
            "drop": self._drop,
            "inventory": self._inventory,
            "empty": self._empty,
            "unknown": self._invalid,
        }

    @property
    def room(self):
        return self.rooms[self.room_id]

    @property
    def items_here(self):
        """Items in the current room, in display order."""
        return tuple(self.room_items[self.room_id])

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
        self.visited.add(destination)
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

    def _map(self, command):
        return self._result(Outcome.MAPPED)

    def _scan(self, command):
        return self._result(Outcome.SCANNED)

    def _take(self, command):
        item = command.arg
        if item is None:
            return self._result(Outcome.INVALID)
        here = self.room_items[self.room_id]
        if item not in here:
            return self._result(Outcome.NOT_HERE, item=item)
        here.remove(item)
        self.inventory.append(item)
        return self._result(Outcome.TAKEN, item=item)

    def _drop(self, command):
        item = command.arg
        if item is None:
            return self._result(Outcome.INVALID)
        if item not in self.inventory:
            return self._result(Outcome.NOT_CARRIED, item=item)
        self.inventory.remove(item)
        self.room_items[self.room_id].append(item)
        return self._result(Outcome.DROPPED, item=item)

    def _inventory(self, command):
        return self._result(Outcome.INVENTORY)

    def _quit(self, command):
        self.status = Status.QUIT
        return self._result(Outcome.QUIT)

    def _empty(self, command):
        return self._result(Outcome.EMPTY)

    def _invalid(self, command):
        return self._result(Outcome.INVALID)

    def _result(self, outcome, oxygen_used=0, item=None):
        return TurnResult(outcome, self.room, self.oxygen, oxygen_used,
                          frozenset(self.visited), self.items_here,
                          tuple(self.inventory), item)
