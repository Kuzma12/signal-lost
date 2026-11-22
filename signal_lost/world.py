"""The ship map: room data and how the rooms connect.

This module only describes the world. It knows nothing about oxygen,
player input, or printing.
"""

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping

# Compass directions in the fixed order used when listing exits.
DIRECTIONS = ("north", "east", "south", "west")

START_ROOM = "cryo_bay"
ESCAPE_ROOM = "escape_pod"


@dataclass(frozen=True)
class Room:
    """A single location aboard the ship.

    ``exits`` maps a direction (e.g. ``"north"``) to the id of the room it
    leads to. It is stored as a read-only mapping so the map can't be
    changed by accident during play.
    """

    id: str
    name: str
    description: str
    exits: Mapping[str, str]

    def __post_init__(self):
        object.__setattr__(self, "exits", MappingProxyType(dict(self.exits)))

    def available_exits(self):
        """Return this room's exit directions in north, east, south, west order."""
        return [direction for direction in DIRECTIONS if direction in self.exits]


_ROOM_DATA = [
    (
        "cryo_bay",
        "Cryo Bay",
        "Rows of shattered cryo pods line the walls, their lids cracked open "
        "like eggshells. Frost creeps across the floor, and the bulkhead to "
        "the east is welded shut.",
        {"north": "medical_bay"},
    ),
    (
        "medical_bay",
        "Medical Bay",
        "Overturned gurneys and scattered med-kits litter the deck. A cracked "
        "monitor still traces a flat green line.",
        {"south": "cryo_bay", "east": "central_corridor"},
    ),
    (
        "central_corridor",
        "Central Corridor",
        "The ship's main artery. Emergency strip-lights pulse red along a "
        "passage that branches in every direction.",
        {
            "west": "medical_bay",
            "north": "bridge",
            "east": "mess_hall",
            "south": "engineering",
        },
    ),
    (
        "bridge",
        "Bridge",
        "The captain's chair faces a viewport webbed with cracks. Stars wheel "
        "slowly past. The ship is tumbling.",
        {"south": "central_corridor", "east": "comms_array"},
    ),
    (
        "comms_array",
        "Comms Array",
        "Banks of dead transmitters crowd the walls, cold to the touch. A "
        "single screen blinks over and over: SIGNAL LOST.",
        {"west": "bridge", "south": "mess_hall"},
    ),
    (
        "mess_hall",
        "Mess Hall",
        "Meal trays drift lazily in the failing gravity. Someone's coffee has "
        "frozen in mid-spill, a brown crystal ribbon above the table.",
        {"west": "central_corridor", "north": "comms_array"},
    ),
    (
        "engineering",
        "Engineering",
        "Conduits spark and spit overhead. A schematic on the wall shows an "
        "escape pod somewhere aft, past the cargo hold and the reactor.",
        {
            "north": "central_corridor",
            "east": "reactor_core",
            "south": "cargo_hold",
        },
    ),
    (
        "reactor_core",
        "Reactor Core",
        "The reactor hums at a pitch that makes your teeth ache. Heat "
        "shimmers off the shielding in warped, glassy waves.",
        {"west": "engineering", "south": "airlock_junction"},
    ),
    (
        "cargo_hold",
        "Cargo Hold",
        "Crates are strapped together in towering stacks. Some have broken "
        "loose and tumble silently through the dark.",
        {"north": "engineering", "east": "airlock_junction"},
    ),
    (
        "airlock_junction",
        "Airlock Junction",
        "Pressure doors hiss and stutter, never quite closing. A stenciled "
        "sign on the far wall reads: ESCAPE POD ->",
        {
            "west": "cargo_hold",
            "north": "reactor_core",
            "east": "escape_pod",
        },
    ),
    (
        "escape_pod",
        "Escape Pod",
        "A cramped capsule with a single crash seat and one big red LAUNCH "
        "button. Through the porthole, the stars wait.",
        {"west": "airlock_junction"},
    ),
]


def build_ship():
    """Build and return the full ship map as ``{room_id: Room}``.

    A fresh dictionary is returned on every call, so each game gets its
    own copy.
    """
    return {
        room_id: Room(room_id, name, description, exits)
        for room_id, name, description, exits in _ROOM_DATA
    }
