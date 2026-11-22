"""The ship map: room data and how the rooms connect.

This module only describes the world. It knows nothing about oxygen,
player input, or printing.
"""

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping, Tuple

# Compass directions in the fixed order used when listing exits.
DIRECTIONS = ("north", "east", "south", "west")

START_ROOM = "cryo_bay"
ESCAPE_ROOM = "escape_pod"

# Each room's (row, column) on the ship grid, used to draw the map
# (spec.md Section 3.7). Every exit joins two neighboring cells.
MAP_GRID = {
    "bridge": (0, 1),
    "comms_array": (0, 2),
    "medical_bay": (1, 0),
    "central_corridor": (1, 1),
    "mess_hall": (1, 2),
    "cryo_bay": (2, 0),
    "engineering": (2, 1),
    "reactor_core": (2, 2),
    "cargo_hold": (3, 1),
    "airlock_junction": (3, 2),
    "escape_pod": (3, 3),
}


@dataclass(frozen=True)
class Room:
    """A single location aboard the ship.

    ``exits`` maps a direction (e.g. ``"north"``) to the id of the room it
    leads to. It is stored as a read-only mapping so the map can't be
    changed by accident during play. ``clue`` is what the scanner reports
    in this room. ``items`` names the items lying here when a game starts;
    the Game tracks where items are after that.
    """

    id: str
    name: str
    description: str
    exits: Mapping[str, str]
    clue: str
    items: Tuple[str, ...] = ()

    def __post_init__(self):
        object.__setattr__(self, "exits", MappingProxyType(dict(self.exits)))
        object.__setattr__(self, "items", tuple(self.items))

    def available_exits(self):
        """Return this room's exit directions in north, east, south, west order."""
        return [direction for direction in DIRECTIONS if direction in self.exits]


# Items lying in each room when a game starts (spec.md Section 3.9).
# Names are lower-case and unique so typed names can be matched exactly.
STARTING_ITEMS = {
    "cryo_bay": ("flashlight",),
    "medical_bay": ("medkit",),
    "bridge": ("keycard",),
    "engineering": ("repair kit",),
}

_ROOM_DATA = [
    (
        "cryo_bay",
        "Cryo Bay",
        "Rows of shattered cryo pods line the walls, their lids cracked open "
        "like eggshells. Frost creeps across the floor, and the bulkhead to "
        "the east is welded shut.",
        {"north": "medical_bay"},
        "Air is flowing in through the north hatch. Your suit "
        "logs the welded east bulkhead as impassable.",
    ),
    (
        "medical_bay",
        "Medical Bay",
        "Overturned gurneys and scattered med-kits litter the deck. A cracked "
        "monitor still traces a flat green line.",
        {"south": "cryo_bay", "east": "central_corridor"},
        "A trail of fresh bootprints in spilled antiseptic leads "
        "east, toward the heart of the ship.",
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
        "A faint heat signature runs south, toward the engine "
        "rooms. The rooms to the north and east read cold and still.",
    ),
    (
        "bridge",
        "Bridge",
        "The captain's chair faces a viewport webbed with cracks. Stars wheel "
        "slowly past. The ship is tumbling.",
        {"south": "central_corridor", "east": "comms_array"},
        "The nav log shows the escape pod docked aft, beyond "
        "Engineering. Nothing forward of here leads off the ship.",
    ),
    (
        "comms_array",
        "Comms Array",
        "Banks of dead transmitters crowd the walls, cold to the touch. A "
        "single screen blinks over and over: SIGNAL LOST.",
        {"west": "bridge", "south": "mess_hall"},
        "The last outgoing message was cut off mid-word: "
        "\"ALL CREW TO AIRLOCK JUNC-\".",
    ),
    (
        "mess_hall",
        "Mess Hall",
        "Meal trays drift lazily in the failing gravity. Someone's coffee has "
        "frozen in mid-spill, a brown crystal ribbon above the table.",
        {"west": "central_corridor", "north": "comms_array"},
        "Sensors find no exits here except the ones you can see. "
        "This end of the ship loops back on itself.",
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
        "Two aft routes register on the schematic: east through "
        "the Reactor Core or south through the Cargo Hold. Both reach "
        "the airlock.",
    ),
    (
        "reactor_core",
        "Reactor Core",
        "The reactor hums at a pitch that makes your teeth ache. Heat "
        "shimmers off the shielding in warped, glassy waves.",
        {"west": "engineering", "south": "airlock_junction"},
        "Radiation is high but within suit limits for a quick "
        "pass. The south door opens onto Airlock Junction.",
    ),
    (
        "cargo_hold",
        "Cargo Hold",
        "Crates are strapped together in towering stacks. Some have broken "
        "loose and tumble silently through the dark.",
        {"north": "engineering", "east": "airlock_junction"},
        "The cargo manifest lists the hold's east door as the "
        "aft route to Airlock Junction.",
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
        "The escape pod's docking beacon pings from the east door, "
        "strong and steady.",
    ),
    (
        "escape_pod",
        "Escape Pod",
        "A cramped capsule with a single crash seat and one big red LAUNCH "
        "button. Through the porthole, the stars wait.",
        {"west": "airlock_junction"},
        "Launch systems are green and the pod's air tanks are "
        "full. One press and you are gone.",
    ),
]


def build_ship():
    """Build and return the full ship map as ``{room_id: Room}``.

    A fresh dictionary is returned on every call, so each game gets its
    own copy.
    """
    return {
        room_id: Room(room_id, name, description, exits, clue,
                      STARTING_ITEMS.get(room_id, ()))
        for room_id, name, description, exits, clue in _ROOM_DATA
    }
