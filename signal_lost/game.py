"""Game state and rules for Signal Lost.

This module decides what happens on each turn and reports it as a
TurnResult. It never prints or reads input; the CLI does all of that.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from .world import (
    DIRECTIONS,
    ESCAPE_ROOM,
    KEYCARD_READER,
    START_ROOM,
    Room,
    build_ship,
)

STARTING_OXYGEN = 12
OXYGEN_PER_MOVE = 1
STARTING_HEALTH = 10   # also the most health the player can have
HAZARD_DAMAGE = 2      # health lost on every entry into a hazard room
MEDKIT = "medkit"
MEDKIT_HEALING = 4
KEYCARD = "keycard"     # unlocks the Escape Pod door at KEYCARD_READER


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
    HEALED = "healed"        # used the medkit and got health back
    FULL_HEALTH = "full_health"  # tried the medkit at full health; kept it
    CANT_USE = "cant_use"    # used a carried item that does nothing
    LOCKED = "locked"        # tried to enter the Escape Pod while it is locked
    UNLOCKED = "unlocked"    # used the keycard at the reader; the pod is open
    ALREADY_UNLOCKED = "already_unlocked"  # keycard at the reader, pod already open
    WRONG_PLACE = "wrong_place"  # used the keycard away from the reader
    WON = "won"              # moved into the unlocked escape pod with oxygen left
    LOST = "lost"            # moved and oxygen hit zero
    DIED = "died"            # moved into a hazard and health hit zero
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
    item: Optional[str] = None  # item named by a take, drop, or use
    health: int = STARTING_HEALTH
    damage: int = 0          # health lost to a hazard this turn
    healed: int = 0          # health restored by a medkit this turn


class Game:
    """Holds the player's current room, oxygen, health, game status, the
    rooms visited so far, the items in each room, the player's
    inventory, and whether the Escape Pod door is still locked."""

    def __init__(self, rooms=None):
        self.rooms = rooms if rooms is not None else build_ship()
        self.room_id = START_ROOM
        self.oxygen = STARTING_OXYGEN
        self.health = STARTING_HEALTH
        self.status = Status.PLAYING
        self.visited = {START_ROOM}
        # Every item is in exactly one place: one room's list or the
        # inventory (spec.md Section 3.9). A used medkit is in neither
        # (Section 3.10).
        self.room_items = {room_id: list(room.items)
                           for room_id, room in self.rooms.items()}
        self.inventory = []
        # The Escape Pod door starts locked; once unlocked with the keycard
        # it stays unlocked (spec.md Section 3.11).
        self.pod_locked = True
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
            "use": self._use,
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
        # The lock is checked before the room changes, so a refused move
        # costs no oxygen or health and isn't recorded as visited.
        if destination == ESCAPE_ROOM and self.pod_locked:
            return self._result(Outcome.LOCKED)

        # Turn resolution order from spec.md Section 4.2 (with the Round 4
        # health step from Section 3.10).
        self.room_id = destination
        self.visited.add(destination)
        self.oxygen = max(0, self.oxygen - OXYGEN_PER_MOVE)
        damage = HAZARD_DAMAGE if self.room.hazard else 0
        self.health = max(0, self.health - damage)

        # Health is checked first: the hazard hits on arrival, so dying
        # wins over running out of oxygen on the same move.
        if self.health == 0:
            self.status = Status.LOST
            outcome = Outcome.DIED
        elif self.room_id == ESCAPE_ROOM and self.oxygen > 0:
            self.status = Status.WON
            outcome = Outcome.WON
        elif self.oxygen == 0:
            self.status = Status.LOST
            outcome = Outcome.LOST
        else:
            outcome = Outcome.MOVED
        return self._result(outcome, oxygen_used=OXYGEN_PER_MOVE,
                            damage=damage)

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

    def _use(self, command):
        item = command.arg
        if item is None:
            return self._result(Outcome.INVALID)
        if item not in self.inventory:
            return self._result(Outcome.NOT_CARRIED, item=item)
        if item == KEYCARD:
            return self._use_keycard()
        if item != MEDKIT:
            return self._result(Outcome.CANT_USE, item=item)
        if self.health >= STARTING_HEALTH:
            return self._result(Outcome.FULL_HEALTH, item=item)
        healed = min(MEDKIT_HEALING, STARTING_HEALTH - self.health)
        self.health += healed
        self.inventory.remove(item)  # a used medkit is gone for good
        return self._result(Outcome.HEALED, item=item, healed=healed)

    def _use_keycard(self):
        """Unlock the Escape Pod door at the reader (spec.md Section 3.11).
        The keycard is never used up."""
        if self.room_id != KEYCARD_READER:
            return self._result(Outcome.WRONG_PLACE, item=KEYCARD)
        if not self.pod_locked:
            return self._result(Outcome.ALREADY_UNLOCKED, item=KEYCARD)
        self.pod_locked = False
        return self._result(Outcome.UNLOCKED, item=KEYCARD)

    def _quit(self, command):
        self.status = Status.QUIT
        return self._result(Outcome.QUIT)

    def _empty(self, command):
        return self._result(Outcome.EMPTY)

    def _invalid(self, command):
        return self._result(Outcome.INVALID)

    def _result(self, outcome, oxygen_used=0, item=None, damage=0, healed=0):
        return TurnResult(outcome, self.room, self.oxygen, oxygen_used,
                          frozenset(self.visited), self.items_here,
                          tuple(self.inventory), item, self.health,
                          damage, healed)
