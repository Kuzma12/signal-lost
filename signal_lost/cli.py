"""Terminal front end for Signal Lost.

Reads player input, passes it through the parser and the Game, and turns
each TurnResult into text. All game rules live in game.py; this module
only handles presentation.
"""

import textwrap

from .game import STARTING_OXYGEN, Game, Outcome
from .parser import is_go_attempt, parse
from .world import MAP_GRID, build_ship

WIDTH = 50
RULE = "=" * WIDTH
PROMPT = "> "
LOW_OXYGEN_THRESHOLD = 3
_SHIP = build_ship()  # read-only map data used to draw the ship map

INTRO = "\n".join([
    RULE,
    "S I G N A L   L O S T".center(WIDTH).rstrip(),
    RULE,
    textwrap.fill(
        "You wake up in a cryo pod. Warning lights flash red. The ship's AI "
        "is silent and the hull is breached. Your suit has twelve units of "
        "oxygen left. Somewhere aboard is an escape pod. Find it before you "
        "run out of air.",
        WIDTH,
    ),
    "",
    "Move with north, south, east, west (or n, s, e, w).",
    "Each move to another room costs 1 oxygen.",
    "Type 'help' for all commands.",
    "",
])

HELP_TEXT = "\n".join([
    "AVAILABLE COMMANDS",
    "  north, south, east, west   move (or n, s, e, w,",
    "                             or 'go north')",
    "  look   (l)                 describe this room",
    "  map    (m)                 show explored rooms",
    "  scan   (sc)                scan room for clues",
    "  take <item>  (get)         pick up an item",
    "  drop <item>                leave an item here",
    "  inventory  (inv, i)        list what you carry",
    "  help   (h, ?)              show this list",
    "  quit   (q, exit)           abandon ship",
    "Moving to another room costs 1 oxygen.",
    "Everything else is free.",
])

WIN_MESSAGE = "\n".join([
    "",
    "",
    ">>> LAUNCH SEQUENCE INITIATED <<<",
    "The hatch seals behind you and the pod blasts free of the dying ship.",
    "You escaped with {oxygen} oxygen to spare.",
    "*** YOU WIN ***",
])

LOSS_MESSAGE = "\n".join([
    "",
    "",
    ">>> OXYGEN DEPLETED <<<",
    "Your vision narrows as the last of the air hisses away...",
    "*** GAME OVER: YOU LOST ***",
])

QUIT_MESSAGE = "You close your eyes and let the ship drift. Transmission ended."
GO_WHERE_MESSAGE = "Go where? Try north, south, east, or west."
UNKNOWN_MESSAGE = "Unknown command: '{text}'. Type 'help' for a list of commands."
BLOCKED_MESSAGE = "You can't go {direction} from here."

# Item messages (spec.md Section 3.9).
ITEMS_HERE_PREFIX = "Items here: "
TAKEN_MESSAGE = "You take the {item}."
NOT_HERE_MESSAGE = "There is no '{item}' here."
TAKE_WHAT_MESSAGE = "Take what?"
DROPPED_MESSAGE = "You drop the {item}."
NOT_CARRIED_MESSAGE = "You are not carrying '{item}'."
DROP_WHAT_MESSAGE = "Drop what?"
INVENTORY_HEADER = "You are carrying:"
INVENTORY_EMPTY = "Your inventory is empty."

# Ship map layout (spec.md Section 3.7): 4 cells of 11 characters with
# 2-character gaps fill exactly WIDTH columns.
MAP_CELL = 11
MAP_GAP = 2
MAP_SIZE = 4
MAP_HEADER = "SHIP MAP  (* = you are here)"
MAP_LABELS = {
    "cryo_bay": "Cryo Bay",
    "medical_bay": "Med Bay",
    "central_corridor": "Corridor",
    "bridge": "Bridge",
    "comms_array": "Comms",
    "mess_hall": "Mess",
    "engineering": "Engines",
    "reactor_core": "Reactor",
    "cargo_hold": "Cargo",
    "airlock_junction": "Airlock",
    "escape_pod": "Pod",
}


def render_exits(room):
    return "Exits: " + ", ".join(room.available_exits())


def render_gauge(oxygen, game_over=False):
    gauge = f"[ OXYGEN: {oxygen}/{STARTING_OXYGEN} ]"
    if not game_over and oxygen <= LOW_OXYGEN_THRESHOLD:
        gauge += "  !! LOW OXYGEN !!"
    return gauge


def render_room(room, oxygen, game_over=False, items=()):
    """Format a room the way spec.md Section 3.6 describes.

    ``items`` are the items in the room now; when there are any, an
    ``Items here:`` line goes just before the exits (Section 3.9).
    """
    lines = [
        RULE,
        f"  {room.name.upper()}",
        RULE,
        textwrap.fill(room.description, WIDTH),
        "",
    ]
    if items:
        lines.append(textwrap.fill(ITEMS_HERE_PREFIX + ", ".join(items), WIDTH))
    lines += [render_exits(room), render_gauge(oxygen, game_over)]
    return "\n".join(lines)


def render_inventory(inventory):
    """List carried items in pickup order, or say there are none."""
    if not inventory:
        return INVENTORY_EMPTY
    return "\n".join([INVENTORY_HEADER, *(f"  - {item}" for item in inventory)])


def _map_column(col):
    """Character offset where grid column ``col`` starts."""
    return col * (MAP_CELL + MAP_GAP)


def render_map(current_id, visited):
    """Draw the visited part of the ship (spec.md Section 3.7).

    Only rooms in ``visited`` are drawn, and a line joins two rooms only
    when both are visited and an exit connects them.
    """
    by_cell = {MAP_GRID[room_id]: room_id for room_id in visited}
    lines = []
    for row in range(MAP_SIZE):
        room_line = [" "] * WIDTH
        link_line = [" "] * WIDTH
        for col in range(MAP_SIZE):
            room_id = by_cell.get((row, col))
            if room_id is None:
                continue
            start = _map_column(col)
            marker = "*" if room_id == current_id else " "
            cell = f"[{marker}{MAP_LABELS[room_id]:<8}]"
            room_line[start:start + MAP_CELL] = cell
            exits = _SHIP[room_id].exits
            east = by_cell.get((row, col + 1))
            if east is not None and exits.get("east") == east:
                room_line[start + MAP_CELL:start + MAP_CELL + MAP_GAP] = "--"
            south = by_cell.get((row + 1, col))
            if south is not None and exits.get("south") == south:
                link_line[start + MAP_CELL // 2] = "|"
        lines.append("".join(room_line).rstrip())
        lines.append("".join(link_line).rstrip())
    while lines and not lines[0]:
        lines.pop(0)
    while lines and not lines[-1]:
        lines.pop()
    return "\n".join([
        MAP_HEADER,
        "",
        *lines,
        "",
        f"You are in: {_SHIP[current_id].name}",
        f"Rooms visited: {len(visited)} of {len(_SHIP)}",
    ])


def render_scan(room):
    """Show the scanner clue for ``room`` (spec.md Section 3.8)."""
    return "\n".join([
        f"[ SCAN: {room.name.upper()} ]",
        textwrap.fill(room.clue, WIDTH),
    ])


def render_result(result, command):
    """Turn a TurnResult into the text to show, or None to show nothing."""
    outcome = result.outcome
    if outcome is Outcome.MOVED:
        return (f"You head {command.arg}...\n\n"
                + render_room(result.room, result.oxygen, items=result.items))
    if outcome is Outcome.WON:
        return (f"You head {command.arg}...\n\n"
                + render_room(result.room, result.oxygen, game_over=True,
                              items=result.items)
                + WIN_MESSAGE.format(oxygen=result.oxygen))
    if outcome is Outcome.LOST:
        return (f"You head {command.arg}...\n\n"
                + render_room(result.room, result.oxygen, game_over=True,
                              items=result.items)
                + LOSS_MESSAGE)
    if outcome is Outcome.BLOCKED:
        return (BLOCKED_MESSAGE.format(direction=command.arg) + "\n"
                + render_exits(result.room))
    if outcome is Outcome.LOOKED:
        return render_room(result.room, result.oxygen, items=result.items)
    if outcome is Outcome.HELP:
        return HELP_TEXT
    if outcome is Outcome.MAPPED:
        return render_map(result.room.id, result.visited)
    if outcome is Outcome.SCANNED:
        return render_scan(result.room)
    if outcome is Outcome.TAKEN:
        return TAKEN_MESSAGE.format(item=result.item)
    if outcome is Outcome.NOT_HERE:
        return textwrap.fill(NOT_HERE_MESSAGE.format(item=result.item), WIDTH)
    if outcome is Outcome.DROPPED:
        return DROPPED_MESSAGE.format(item=result.item)
    if outcome is Outcome.NOT_CARRIED:
        return textwrap.fill(NOT_CARRIED_MESSAGE.format(item=result.item), WIDTH)
    if outcome is Outcome.INVENTORY:
        return render_inventory(result.inventory)
    if outcome is Outcome.QUIT:
        return QUIT_MESSAGE
    if outcome is Outcome.INVALID:
        if command.kind == "take":
            return TAKE_WHAT_MESSAGE
        if command.kind == "drop":
            return DROP_WHAT_MESSAGE
        if is_go_attempt(command) or command.kind == "move":
            return GO_WHERE_MESSAGE
        return UNKNOWN_MESSAGE.format(text=command.arg)
    return None  # EMPTY and GAME_OVER print nothing


def run(input_fn=input, output_fn=print):
    """Play one game of Signal Lost and return the finished Game.

    ``input_fn`` and ``output_fn`` can be replaced so tests can script
    the player's input and capture the output.
    """
    game = Game()
    output_fn(INTRO)
    output_fn(render_room(game.room, game.oxygen, items=game.items_here) + "\n")

    while not game.is_over:
        try:
            text = input_fn(PROMPT)
        except (EOFError, KeyboardInterrupt):
            output_fn("")
            text = "quit"
        command = parse(text)
        result = game.handle(command)
        message = render_result(result, command)
        if message is not None:
            output_fn(message + "\n")

    return game
