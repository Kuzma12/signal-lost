# Signal Lost: Specification (Rounds 1-6)

This spec covers Rounds 1 to 6 of *Signal Lost*.

- **Round 1** defines how requirements **R1 (Room Navigation)**, **R2 (Room
  Information)**, and **R3 (Oxygen and Escaping)** from `problem.md` are
  built and tested.
- **Round 2** adds **R4 (Ship Map)** and **R5 (Room Scanner)**. Their
  design is in Sections 3.7 and 3.8, and their acceptance criteria are in
  Section 6. Round 2 changes nothing about how Round 1 features behave.
- **Round 3** adds **R6 (Collecting Items)** and **R7 (Inventory System)**.
  Their design is in Section 3.9, and their acceptance criteria are in
  Section 6. Round 3 changes nothing about how Round 1-2 features behave,
  except that the room display gains an `Items here:` line in rooms that
  hold items.
- **Round 4** adds **R8 (Health and Hazards)** and **R9 (Medkit Healing)**.
  Their design is in Section 3.10, and their acceptance criteria are in
  Section 6. Round 4 adds a health gauge line to the room display, a health
  step to the turn order (Section 4.2), a second way to lose, and the first
  item that is used up (the medkit). Everything else from Rounds 1-3
  behaves as before.
- **Round 5** adds **R10 (Keycard and Locked Escape Pod)** and **revises
  R3's escape condition**: the Escape Pod door starts locked and must be
  unlocked with the keycard before the player can win. The design is in
  Section 3.11, the revised escape rule (with the original R3 wording kept
  for history) is in Section 4.6, and the acceptance criteria are in
  Section 6. Earlier sections are not rewritten; where Round 5 changes
  something they say, a "(Round 5)" note points to the new text.
- **Round 6** adds **R11 (Saving the Game)** and **R12 (Loading the
  Game)**: `save` writes the whole game state to a JSON file and `load`
  restores it. The design is in Section 3.12 and the acceptance criteria
  are in Section 6. Round 6 changes no rule from Rounds 1-5; where it adds
  to something an earlier section says, a "(Round 6)" note points to the
  new text.

Inventory (Round 3) and hazards (Round 4) are now built. Features still
planned for later rounds (puzzles / locked doors and save/load) are **out
of scope**. Section 9 only describes where they will fit.

(Round 5) The locked Escape Pod door is now built (Section 3.11). Other
puzzles and locked doors, and save/load, are still out of scope.

(Round 6) Save/load is now built (Section 3.12). Other puzzles and locked
doors are still out of scope.

---

## 1. Game Overview and Purpose

### 1.1 Premise

> *You wake up in a cryo pod. Warning lights flash red. The ship's AI is
> silent and the hull is breached. Your suit has twelve units of oxygen left.
> Somewhere aboard is an escape pod. Find it before you run out of air.*

*Signal Lost* is a single-player text adventure in the terminal. The player
moves through a damaged spaceship by typing compass directions. Each move to
another room uses one unit of oxygen. The player wins by reaching the Escape
Pod before their oxygen runs out.

### 1.2 Design Goals

| Goal | How Round 1 meets it |
|------|----------------------|
| Easy to understand | Only four movement directions plus `help`, `look`, and `quit`. Every room lists its exits. Round 2 adds `map` and `scan`, both free. |
| Some challenge | The shortest route takes 6 moves out of 12. Dead ends and a loop of rooms that leads nowhere punish careless exploring. |
| Sci-fi atmosphere | Short, evocative room descriptions, ship-alert style messages, and an oxygen gauge shown after every move. |
| Polished | Clean formatting, input that ignores case and extra spaces, no crashes or tracebacks (including on Ctrl-C and Ctrl-D). |

### 1.3 Technical Constraints

- Python 3.10 or newer.
- **Standard library only.** No third-party packages and no `requirements.txt`.
- No randomness in Round 1. The same inputs always produce the same output,
  so the game can be tested reliably.
- Plain text output only. No ANSI colors or curses in Round 1, because
  terminal support varies. Atmosphere comes from the writing and from ASCII
  framing such as `====` rules and `[ OXYGEN ]` gauges.

---

## 2. Project Structure

```
signal-lost/
├── problem.md            # Problem statement (read-only)
├── spec.md               # This document
├── main.py               # Entry point: `python3 main.py`
├── signal_lost/          # Game package
│   ├── __init__.py
│   ├── world.py          # Room data model and the ship map
│   ├── parser.py         # Turns raw input text into a Command
│   ├── game.py           # Game state and rules (no printing, no input)
│   └── cli.py            # Terminal I/O loop and text rendering
└── tests/
    ├── __init__.py
    ├── test_world.py     # Map integrity
    ├── test_parser.py    # Command parsing
    ├── test_game.py      # Rules: movement, oxygen, win/loss
    └── test_cli.py       # Output formatting and full playthroughs
```

### 2.1 Module Responsibilities

| Module | Responsibility | Must NOT |
|--------|----------------|----------|
| `world.py` | Defines the `Room` type (id, name, description, exits, and from Round 2 a scanner `clue`) and `build_ship()`, which returns the full map. Also defines the `START_ROOM` and `ESCAPE_ROOM` ids and (Round 2) `MAP_GRID`, each room's row/column on the ship grid. (Round 3) Each `Room` also lists the items it holds at the start of a game. (Round 4) Each `Room` says whether it is a hazard, and `HAZARD_ROOMS` names those rooms. | Know about oxygen, input, or output. |
| `parser.py` | `parse(text) -> Command`. Normalizes case and whitespace, expands aliases (`n` → `north`, `go north` → `north`), and labels input as move / help / look / quit / map / scan / empty / unknown, and (Round 3) take / drop / inventory, and (Round 4) use. | Change game state. |
| `game.py` | `Game` class holding the current room, oxygen, status (`PLAYING`, `WON`, `LOST`, `QUIT`), and (Round 2) the set of visited room ids. (Round 3) It also holds the items currently in each room and the player's inventory. (Round 4) It also holds the player's health. `Game.handle(command) -> TurnResult` applies the rules and returns a structured result. | Call `print()` or `input()`. |
| `cli.py` | `run(input_fn=input, output_fn=print)`. Reads input, calls the parser and `Game.handle`, and renders results to text. | Contain game rules. |
| `main.py` | Calls `signal_lost.cli.run()` inside `if __name__ == "__main__":`. Nothing else. | Contain logic. |

(Round 6) A fifth package module, `signal_lost/savefile.py`, reads and
writes the save file (Section 3.12). It knows JSON and files but nothing
about rooms, oxygen, or rules: `write(path, data)` and `read(path)`, plus
the `SAVE_FILE` name and the `NoSaveFile` and `DamagedSave` errors.
`game.py` turns its state into plain data, checks loaded data against the
rules, and calls `savefile` from its `save` and `load` handlers; it still
never calls `print()` or `input()`. `parser.py` gains the `save` and
`load` kinds, and `cli.py` renders the new outcomes. A new test file,
`tests/test_savefile.py`, covers the file layer.

**Key principle:** game logic (`game.py`) stays separate from I/O (`cli.py`).
This keeps the rules easy to unit-test without faking a terminal. It also
lets later rounds add features without rewriting the loop.

### 2.2 Core Data Types

- **`Room`** (frozen dataclass): `id: str`, `name: str`,
  `description: str`, `exits: dict[str, str]` (direction → destination room id),
  and from Round 2 `clue: str` (the scanner text, Section 3.8). From Round 3,
  `items: tuple[str, ...]` (the item names in this room when a game starts,
  Section 3.9). `Room` stays frozen; items that move during play are tracked
  by `Game`, not by `Room`. From Round 4, `hazard: bool` (default `False`):
  `True` if entering the room hurts the player (Section 3.10).
- **`Command`** (frozen dataclass): `kind: str` (`"move"`, `"help"`,
  `"look"`, `"quit"`, `"map"`, `"scan"`, `"empty"`, `"unknown"`),
  `arg: str | None` (the direction for moves, the original text for unknown
  input). From Round 3, `kind` can also be `"take"`, `"drop"`, or
  `"inventory"`, and `arg` is the item name for `take` / `drop` (lower-case,
  single-spaced, or `None` if no name was typed). From Round 4, `kind` can
  also be `"use"`, with the item name in `arg` the same way.
- **`TurnResult`** (dataclass): `outcome` (an enum such as `MOVED`,
  `BLOCKED`, `INVALID`, `LOOKED`, `HELP`, `MAPPED`, `SCANNED`, `WON`, `LOST`,
  `QUIT`), `room: Room`, `oxygen: int`, `oxygen_used: int` (0 or 1), and from
  Round 2 `visited: frozenset[str]` (ids of every room entered so far,
  including the start room). From Round 3 it also has `items: tuple[str, ...]`
  (items in the current room now), `inventory: tuple[str, ...]` (items the
  player carries, in pickup order), and `item: str | None` (the item named by
  a `take` / `drop`). New outcomes: `TAKEN`, `NOT_HERE`, `DROPPED`,
  `NOT_CARRIED`, `INVENTORY`. From Round 4 it also has `health: int` (health
  now), `damage: int` (health lost to a hazard this turn, 0 or 2), and
  `healed: int` (health restored by a medkit this turn). New outcomes:
  `DIED` (health reached 0), `HEALED`, `FULL_HEALTH`, `CANT_USE`.
- **Constants** in `game.py`: `STARTING_OXYGEN = 12`, `OXYGEN_PER_MOVE = 1`.
  From Round 4: `STARTING_HEALTH = 10` (also the maximum), `HAZARD_DAMAGE = 2`,
  `MEDKIT = "medkit"`, `MEDKIT_HEALING = 4`.
- (Round 5) `world.py` adds `KEYCARD_READER = "airlock_junction"`, the room
  where the keycard works. `game.py` adds `KEYCARD = "keycard"`, a
  `pod_locked: bool` field on `Game` (`True` in a new game), and the
  outcomes `LOCKED` (tried to enter the locked pod), `UNLOCKED`,
  `ALREADY_UNLOCKED`, and `WRONG_PLACE` (keycard used away from the
  reader). `TurnResult` gains no new fields.
- (Round 6) `Command.kind` can also be `"save"` or `"load"` (no `arg`).
  `Game(rooms=None, save_path=SAVE_FILE)` takes the save file's path, and
  `cli.run(input_fn, output_fn, save_path=SAVE_FILE)` passes it through,
  so tests can use a temporary folder. `game.py` adds `SAVE_VERSION = 1`
  and the outcomes `SAVED`, `SAVE_FAILED`, `LOADED`, `NO_SAVE`, and
  `DAMAGED_SAVE`. `TurnResult` gains no new fields: a `LOADED` result
  already carries the restored room, oxygen, health, and items.

---

## 3. Spaceship Rooms and Navigation

### 3.1 Map

The ship has **11 rooms** on a grid. Every exit works in both directions: if
room A's `east` leads to B, then B's `west` leads back to A. Some rooms that
sit next to each other on the grid are **not** connected (sealed bulkheads).

```
                 [Bridge] ─────────── [Comms Array]
                     │                     │
 [Medical Bay] ── [Central Corridor] ── [Mess Hall]
     │                 │
 [Cryo Bay]       [Engineering] ───── [Reactor Core]
  (START)              │                   │
                  [Cargo Hold] ────── [Airlock Junction] ── [Escape Pod]
                                                              (GOAL)
```

### 3.2 Room Table

| Id | Name | Exits |
|----|------|-------|
| `cryo_bay` | Cryo Bay | north → `medical_bay` |
| `medical_bay` | Medical Bay | south → `cryo_bay`, east → `central_corridor` |
| `central_corridor` | Central Corridor | west → `medical_bay`, north → `bridge`, east → `mess_hall`, south → `engineering` |
| `bridge` | Bridge | south → `central_corridor`, east → `comms_array` |
| `comms_array` | Comms Array | west → `bridge`, south → `mess_hall` |
| `mess_hall` | Mess Hall | west → `central_corridor`, north → `comms_array` |
| `engineering` | Engineering | north → `central_corridor`, east → `reactor_core`, south → `cargo_hold` |
| `reactor_core` | Reactor Core | west → `engineering`, south → `airlock_junction` |
| `cargo_hold` | Cargo Hold | north → `engineering`, east → `airlock_junction` |
| `airlock_junction` | Airlock Junction | west → `cargo_hold`, north → `reactor_core`, east → `escape_pod` |
| `escape_pod` | Escape Pod | west → `airlock_junction` |

Short descriptions (final wording may be polished during implementation, but
each stays 1–3 sentences):

- **Cryo Bay:** Rows of shattered cryo pods line the walls. Frost creeps
  across the floor, and the bulkhead to the east is welded shut.
- **Medical Bay:** Overturned gurneys and scattered med-kits. A cracked
  monitor still traces a flat green line.
- **Central Corridor:** The ship's main artery. Emergency strip-lights pulse
  red along a passage that branches in every direction.
- **Bridge:** The captain's chair faces a viewport webbed with cracks. Stars
  wheel slowly past. The ship is tumbling.
- **Comms Array:** Banks of dead transmitters. A single screen blinks:
  `SIGNAL LOST`.
- **Mess Hall:** Trays float in the low gravity. Someone's coffee has frozen
  mid-spill.
- **Engineering:** Conduits spark overhead. A schematic on the wall shows an
  escape pod somewhere aft.
- **Reactor Core:** The reactor hums at a dangerous pitch. Heat shimmers off
  the shielding.
- **Cargo Hold:** Crates are strapped in towering stacks. Some have broken
  loose and drift in the dark.
- **Airlock Junction:** Pressure doors hiss and stutter. A sign reads:
  `ESCAPE POD →`.
- **Escape Pod:** A cramped capsule with one seat and a big red LAUNCH
  button.

### 3.3 Route Analysis (Challenge Balance)

- **Shortest winning route:** 6 moves. For example,
  `north, east, south, south, east, east` (Cryo → Medical → Central →
  Engineering → Cargo → Airlock → Pod). There is a second 6-move route
  through the Reactor Core.
- **Spare oxygen on the best route:** 12 − 6 = **6**.
- **Traps:** The Bridge / Comms Array / Mess Hall loop is a 4-move detour
  away from the corridor that leads nowhere. Following the Engineering
  schematic hint avoids it.
- **Parity note:** The map is a grid, so every path from Cryo Bay to the
  Escape Pod has an **even** number of moves. The pod can be reached on move
  6, 8, 10, or 12, but never on an odd move. (This matters for the boundary
  tests in Section 7.)

(Round 5) The 6-move routes no longer win, because they skip the Bridge
and so never pick up the keycard. The new shortest winning route is 8
moves; see Section 3.11. The parity note still holds.

(Round 5 clarification) The "Traps" bullet above is kept as written, but
the **Bridge** is no longer part of the trap: it holds the keycard, so it
is a required 2-move detour (north from the Central Corridor and back).
Only the Comms Array and Mess Hall are still a dead end. The scanner clues
were corrected to match (Section 3.8).

### 3.4 Movement Commands

| Input (case-insensitive, extra spaces ignored) | Meaning |
|------------------------------------------------|---------|
| `north`, `south`, `east`, `west` | Move in that direction |
| `n`, `s`, `e`, `w` | Shortcuts for the four directions |
| `go <direction>` (e.g. `go north`, `GO N`) | Same as the bare direction |

### 3.5 Non-Movement Commands

These commands **never** use oxygen:

| Input | Effect |
|-------|--------|
| `look` / `l` | Shows the current room's information again (Section 3.6) |
| `map` / `m` | (Round 2, R4) Shows the map of visited rooms (Section 3.7) |
| `scan` / `sc` | (Round 2, R5) Shows the current room's scanner clue (Section 3.8) |
| `take <item>` / `get <item>` | (Round 3, R6) Picks up an item in this room (Section 3.9) |
| `drop <item>` | (Round 3, R7) Leaves a carried item in this room (Section 3.9) |
| `inventory` / `inv` / `i` | (Round 3, R7) Lists the items being carried (Section 3.9) |
| `use <item>` | (Round 4, R9) Uses a carried item; only the medkit does anything (Section 3.10) |
| `help` / `h` / `?` | Lists the available commands |
| `quit` / `q` / `exit` | Ends the game with a goodbye message. This counts as neither a win nor a loss. |

(Round 5) `use keycard` at the Airlock Junction unlocks the Escape Pod door
(Section 3.11). It is also free.

### 3.6 Room Display Format (R2)

Every time the player **enters** a room, including the starting room at game
start and the Escape Pod at the moment of winning, the game prints:

```
==================================================
  CENTRAL CORRIDOR
==================================================
The ship's main artery. Emergency strip-lights pulse red
along a passage that branches in every direction.

Exits: north, east, south, west
[ OXYGEN: 10/12 ]
```

Rules:
- The room name appears in uppercase between two `=` rules.
- The description follows.
- `Exits:` lists available directions in the fixed order **north, east,
  south, west**, skipping any the room doesn't have.
- The oxygen gauge shows current/maximum.

### 3.7 Ship Map (R4, Round 2)

Typing `map` (or `m`) draws the part of the ship the player has explored.

**Visited rooms.** The game remembers every room the player has entered.
The Cryo Bay counts as visited from the start. A room is added when the
player successfully moves into it. Blocked moves, `look`, `scan`, and `map`
add nothing. Visiting a room again doesn't add it twice.

**Layout.** Each room has a fixed position on a 4-column by 4-row grid
(`MAP_GRID` in `world.py`), matching the diagram in 3.1:

| Row \ Col | 0 | 1 | 2 | 3 |
|-----------|---|---|---|---|
| 0 | | Bridge | Comms Array | |
| 1 | Medical Bay | Central Corridor | Mess Hall | |
| 2 | Cryo Bay | Engineering | Reactor Core | |
| 3 | | Cargo Hold | Airlock Junction | Escape Pod |

Every exit joins two rooms that sit next to each other on the grid (east is
column + 1, south is row + 1, and so on). A test checks this.

**Drawing rules.**

- Each grid cell is 11 characters wide, with 2-character gaps, so a full row
  is exactly 50 columns: `4 × 11 + 3 × 2 = 50`.
- A visited room is drawn as `[` + marker + label + `]`. The label is a short
  name of at most 8 characters, padded to 8. The marker is `*` for the
  current room and a space for every other room.
- Short labels: Cryo Bay → `Cryo Bay`, Medical Bay → `Med Bay`, Central
  Corridor → `Corridor`, Bridge → `Bridge`, Comms Array → `Comms`, Mess Hall
  → `Mess`, Engineering → `Engines`, Reactor Core → `Reactor`, Cargo Hold →
  `Cargo`, Airlock Junction → `Airlock`, Escape Pod → `Pod`.
- A connection is drawn only when **both** rooms are visited **and** an exit
  joins them: `--` in the gap for east/west, and `|` under the middle of the
  cell for north/south. Neighbors with a sealed bulkhead between them get no
  line.
- **Unvisited rooms are not drawn at all,** and neither are the lines into
  them. No `?` hints are shown. The player can still use `look` to see a
  room's exits.
- Trailing spaces are trimmed, and blank lines at the top and bottom of the
  grid are dropped.

**Output format** (after `n, e, s, e` from the start):

```
SHIP MAP  (* = you are here)

[ Med Bay ]--[ Corridor]
     |            |
[ Cryo Bay]  [ Engines ]--[*Reactor ]

You are in: Reactor Core
Rooms visited: 5 of 11
```

The map uses no oxygen and never changes the room or the game status.

### 3.8 Room Scanner (R5, Round 2)

Typing `scan` (or `sc`) shows the current room's clue:

```
[ SCAN: ENGINEERING ]
<clue text, wrapped to 50 columns>
```

- Every room has its **own** clue (`Room.clue`): one or two sentences,
  non-empty, plain ASCII, different from every other room's clue and from
  the room's description.
- A room always gives the **same** clue (no randomness, Section 1.3). The
  player can scan as often as they like.
- Scanning uses no oxygen and never changes the room or the game status.
- Clues point toward the escape route or warn about dead ends, so scanning
  is a free way to plan with limited oxygen. The Escape Pod has a clue too,
  even though entering it ends the game, so every room meets the rule above.

**(Round 5 clarification) Corrected clues.** The revised R3 and R10 make
the Bridge required, because the keycard is there. Two Round 2 clues told
the player to stay away from it, which would now mislead them, so they are
corrected. Every rule above still holds (one or two sentences, unique,
plain ASCII, free, repeatable). The other nine clues are unchanged.

| Room | Round 2 clue (kept here for history) | Clue from Round 5 |
|------|--------------------------------------|-------------------|
| Central Corridor | `A faint heat signature runs south, toward the engine rooms. The rooms to the north and east read cold and still.` | `A faint heat signature runs south, toward the engine rooms. Security logs place the captain's keycard on the Bridge, just north.` |
| Bridge | `The nav log shows the escape pod docked aft, beyond Engineering. Nothing forward of here leads off the ship.` | `The nav log shows the escape pod docked aft, beyond Engineering. Its hatch answers only to a crew keycard, so don't leave without one.` |

The new clues tell the player **where** the keycard is and **that** the pod
needs it. They don't say where it is used (the Airlock Junction reader) or
which command to type; the lock message (Section 3.11) gives that hint when
the player reaches the door. The Mess Hall clue ("This end of the ship
loops back on itself") is still accurate and is unchanged.

### 3.9 Items and Inventory (R6, R7, Round 3)

**Items.** An item is identified by its name: a short, lower-case string
that is unique on the ship. Items are only collected and carried in Round 3.
They do not open doors, change oxygen, or affect winning or losing.

Starting placement (`Room.items` in `world.py`):

| Room | Item |
|------|------|
| Cryo Bay | `flashlight` |
| Medical Bay | `medkit` |
| Bridge | `keycard` |
| Engineering | `repair kit` |

Every other room, including the Escape Pod, starts empty. The flashlight sits
in the starting room so the player meets the item system right away.

**Item state.** `Game` keeps the items currently in each room (starting from
`Room.items`) and the player's inventory. Inventory order is the order items
were picked up. A room's items are listed in their starting order, and an
item dropped there is added to the end. An item is always in exactly one
place, either one room or the inventory, so items are never duplicated or
lost. There is no carrying limit.

**Name matching.** `take` and `drop` need the item's full name. Case and
extra spaces are ignored, so `TAKE   Repair  Kit` takes the repair kit, but
`take kit` does not match anything.

**Seeing items (R6).** Whenever a room is displayed (on entering it, at game
start, and with `look`), a line lists its current items, between the blank
line and the `Exits:` line:

```
==================================================
  CRYO BAY
==================================================
<description>

Items here: flashlight
Exits: north
[ OXYGEN: 12/12 ]
```

The line is left out when the room holds no items, so empty rooms look
exactly as in Section 3.6. A long list wraps to 50 columns.

**Commands and messages.**

| Input | Case | Output | State change |
|-------|------|--------|--------------|
| `take <item>` / `get <item>` | item is in this room | `You take the <item>.` | item moves from the room to the end of the inventory |
| | item is not in this room (already carried, elsewhere, or not a real item) | `There is no '<item>' here.` | none |
| | no name (`take`, `get`) | `Take what?` | none |
| `drop <item>` | item is carried | `You drop the <item>.` | item moves from the inventory to the end of this room's items |
| | item is not carried | `You are not carrying '<item>'.` | none |
| | no name (`drop`) | `Drop what?` | none |
| `inventory` / `inv` / `i` | carrying items | `You are carrying:` then one `  - <item>` line each, in pickup order | none |
| | carrying nothing | `Your inventory is empty.` | none |

`<item>` in the messages is the normalized (lower-case, single-spaced) name.
None of these commands use oxygen or change the room or game status. Taking
an item does not change the map or the visited rooms.

### 3.10 Health, Hazards, and the Medkit (R8, R9, Round 4)

**Health.** A new game starts with **10 health**, which is also the most
the player can have. Health never goes below 0 or above 10.

**Showing health.** Every room display (game start, entering a room, `look`,
and the final display of a finished game) gets a health gauge on its own line
directly under the oxygen gauge:

```
Exits: north, west
[ OXYGEN: 9/12 ]
[ HEALTH: 8/10 ]
```

It goes on a separate line because oxygen, health, and the `!! LOW OXYGEN !!`
warning would not fit in 50 columns on one line. There is no low-health
warning.

**Hazard rooms.** The **Reactor Core** and the **Cargo Hold** are hazards
(`Room.hazard` is `True`; `HAZARD_ROOMS` in `world.py`). No other room is.
Every **successful** move into a hazard room, including going back into one,
lowers health by **2**. The move still costs the normal 1 oxygen. Blocked
moves, `look`, and every other command never change health, even while
standing in a hazard room. Starting rooms, the Escape Pod, and every other
room are safe.

When a move hurts the player, the room display is followed by a blank line
and a hazard message:

```
!! HAZARD: -2 HEALTH !!
A drifting crate slams into you.
```

The second line depends on the room: the Reactor Core says `Radiation from
the reactor scorches your suit.`, and the Cargo Hold says `A drifting crate
slams into you.`

**Dying.** If health reaches 0, the game ends: status becomes `LOST`, the
outcome is `DIED`, and the room display and hazard message are followed by:

```
>>> CRITICAL INJURIES <<<
Your suit alarms fade as everything goes dark...
You didn't survive.
*** GAME OVER: YOU LOST ***
```

If one move brings **both** health and oxygen to 0, the player gets this
health ending, not the oxygen one (the hazard hits on arrival). See 4.2.

**Balance.** The Airlock Junction can only be reached through the Reactor
Core or the Cargo Hold, so every winning route takes at least 2 damage.
Both 6-move routes win with **8 health** and 6 oxygen, so the player can
escape without healing (R8). The nearest hazard is 4 moves from the start,
and re-entering a hazard takes at least 2 more moves, so a fifth hazard
entry (the one that brings health from 10 to 0) can only happen on move 12,
when oxygen also runs out. Health matters most as a limit on wandering
through hazard rooms, and the medkit lets a careless player survive one
extra hazard.

**Using items (R9).** `use <item>` uses an item the player is carrying. The
name is matched the same way as `take` and `drop` (Section 3.9).

| Input | Case | Output | State change |
|-------|------|--------|--------------|
| `use medkit` | carrying the medkit, health below 10 | `You use the medkit and restore <n> health.` | health goes up by 4, but not above 10 (`<n>` is the amount actually restored); the medkit is removed from the inventory and is gone for good |
| | carrying the medkit, health is 10 | `You are already at full health.` then `You keep the medkit for later.` | none (the medkit stays in the inventory) |
| `use <item>` | the item is not carried (still in a room, already used, or not a real item) | `You are not carrying '<item>'.` | none |
| | carrying an item other than the medkit | `You can't use the <item>.` | none |
| | no name (`use`) | `Use what?` | none |

The "not carried" check comes first, so `use keycard` without the keycard
says you are not carrying it. Using an item costs no oxygen and never
changes the room, status, or visited rooms. A medkit lying in the room must
be taken before it can be used. Taking, dropping, and listing items, the
medkit included, work exactly as in Section 3.9.

**Item count.** Items are still never duplicated or moved by anything
other than `take` and `drop`. The one change is that a medkit that has been
used is no longer anywhere: not in a room and not in the inventory. So the
ship holds four items until the medkit is used, and three after.

### 3.11 Keycard and the Locked Escape Pod (R10, Round 5)

**The lock.** The only locked door on the ship is the one from the
Airlock Junction into the Escape Pod. It is locked when a game starts
(`Game.pod_locked` is `True`). The Escape Pod is still listed in the
Airlock Junction's exits, and the `Exits:` line does not change: the
Airlock Junction still shows `Exits: north, east, west`.

**Trying the locked door.** A move into the Escape Pod while the door is
locked is refused, like a blocked move:

```
The escape pod door is locked.
A keycard reader beside it blinks red.
Exits: north, east, west
```

The outcome is `LOCKED`. The player stays in the Airlock Junction, and
oxygen, health, status, the visited rooms, and items do not change. The
lock check happens before the room changes (Section 4.2), so a refused
move never costs oxygen or health and never adds the pod to the map.

**Unlocking.** The keycard starts on the Bridge (Section 3.9). The player
takes it and types `use keycard` at the Airlock Junction (`KEYCARD_READER`
in `world.py`). `use` follows the same order as Section 3.10: first
"carried?", then "which item?". For the keycard:

| Input | Case | Output | State change |
|-------|------|--------|--------------|
| `use keycard` | not carrying the keycard | `You are not carrying 'keycard'.` (outcome `NOT_CARRIED`) | none |
| | carried, in any room except the Airlock Junction | `The keycard doesn't work here.` (outcome `WRONG_PLACE`) | none |
| | carried, at the Airlock Junction, door locked | `You swipe the keycard. The reader blinks green.` then `The escape pod door is unlocked.` (outcome `UNLOCKED`) | the door is unlocked |
| | carried, at the Airlock Junction, door already unlocked | `The escape pod door is already unlocked.` (outcome `ALREADY_UNLOCKED`) | none |

Using the keycard costs no oxygen or health and never changes the room,
status, or visited rooms. The keycard is **not** used up: it stays in the
inventory and can be dropped and taken like any item, so the ship always
holds the four items until the medkit is used (Section 3.10). The
flashlight and repair kit still say `You can't use the <item>.`

**Staying unlocked.** Once unlocked, the door stays unlocked for the rest
of the game, even if the keycard is dropped. There is no way to lock it
again.

**Winning.** With the door unlocked, a move into the Escape Pod follows
the normal turn order (Section 4.2): it costs 1 oxygen, and the player
wins only if oxygen is above 0 after the move (Section 4.3) and health is
above 0. See Section 4.6 for the revised R3 escape rule.

**Balance.** The Bridge is a dead end off the Central Corridor, so the
keycard costs a 2-move detour (north to the Bridge and back). The shortest
winning routes take **8 moves**:

- `north, east, north, take keycard, south, south, south, east, use
  keycard, east` (through the Cargo Hold), and
- `north, east, north, take keycard, south, south, east, south, use
  keycard, east` (through the Reactor Core).

Both pass one hazard and win with **4 oxygen and 8 health**, so the game
is still winnable from 12 oxygen and 10 health without healing (R3, R8).
Every winning route has 8 or 10 moves (by exhaustive search; 12 is a loss
by Section 4.3). The lock only refuses moves, so the Round 4 health
analysis in Section 3.10 is unchanged.

### 3.12 Saving and Loading (R11, R12, Round 6)

**Commands.** `save` and `load` are single words; case and extra spaces
are ignored (`  SAVE ` works). They have no one-letter aliases, because
`s` is south and `l` is look. Anything after the word (`save game`,
`load 2`) is an unknown command. `help` lists both. Like every other
command, they are ignored once the game has ended (Section 4.4); during
play the game loop never reaches that point, since it stops reading input.

**One save slot.** The save file is `signal_lost_save.json`
(`savefile.SAVE_FILE`) in the folder the game is started from (the
current working directory). There is one slot: every `save` replaces the
previous save without asking. The file is ignored by Git (`.gitignore`).

**What is saved.** Every piece of live game state on `Game` (Sections
3.7, 3.9-3.11), and nothing that comes from `build_ship()`:

```json
{
  "version": 1,
  "room": "central_corridor",
  "oxygen": 10,
  "health": 10,
  "status": "playing",
  "visited": ["central_corridor", "cryo_bay", "medical_bay"],
  "room_items": {
    "airlock_junction": [],
    "bridge": ["keycard"],
    "cargo_hold": [],
    "central_corridor": [],
    "comms_array": [],
    "cryo_bay": [],
    "engineering": ["repair kit"],
    "escape_pod": [],
    "medical_bay": [],
    "mess_hall": [],
    "reactor_core": []
  },
  "inventory": ["flashlight", "medkit"],
  "pod_locked": true
}
```

- `version` is the save format number, `SAVE_VERSION = 1`.
- `room`, `oxygen`, `health`, and `status` are the player's current
  values. `status` is always `"playing"`, because saving after the game
  ends is impossible.
- `visited` is the set of visited room ids, written in sorted order so the
  file is the same for the same state.
- `room_items` lists every room id, each with its items in display order
  (Section 3.9). `inventory` is in pickup order.
- `pod_locked` is the Escape Pod door (Section 3.11).
- A used medkit is simply missing from both `room_items` and `inventory`
  (Section 3.10), so no extra field is needed.

The file is written with the standard-library `json` module (2-space
indent, UTF-8, ending in a newline). It is written to a temporary file
next to it (`signal_lost_save.json.tmp`) and then moved into place, so a
save that fails halfway never damages the previous save.

**Saving.**

| Case | Output | State change |
|------|--------|--------------|
| The file is written | `Game saved.` (outcome `SAVED`) | none (the file on disk is replaced) |
| The file can't be written (e.g. the folder is read-only, or the path is a folder) | `Save failed: the file could not be written.` (outcome `SAVE_FAILED`) | none; an earlier save file is left as it was |

Saving costs no oxygen or health and never changes the room, status,
visited rooms, items, inventory, or lock.

**Loading.**

| Case | Output | State change |
|------|--------|--------------|
| The file exists and passes every check below | `Game loaded.`, a blank line, then the restored room display (Section 3.6: name, description, `Items here:`, exits, oxygen and health gauges, as for `look`) (outcome `LOADED`) | the whole game state is replaced by the saved state |
| There is no save file | `There is no saved game to load.` (outcome `NO_SAVE`) | none |
| The file is damaged (any check below fails) | `The save file is damaged and can't be loaded.` then `Your current game is unchanged.` (outcome `DAMAGED_SAVE`) | none |

Loading never deletes, changes, or rewrites the save file. The `load`
command itself costs nothing: oxygen and health become exactly the saved
values. Loading is all-or-nothing: every check runs **before** any state
changes, so a damaged file can never leave a half-loaded game. The
restored game is a fresh copy, so playing on after `load` never changes
the file until the next `save`, and `load` can be used again to go back.

**Checks on a save file.** The file is damaged unless **all** of these
hold:

1. It can be read, is valid UTF-8, and is valid JSON whose top level is an
   object. (A file that exists but can't be read, such as a folder with
   that name, counts as damaged.)
2. It has exactly the keys `version`, `room`, `oxygen`, `health`,
   `status`, `visited`, `room_items`, `inventory`, and `pod_locked`.
3. `version` is the integer 1, and `status` is `"playing"`.
4. `oxygen` is an integer from 1 to 12, and `health` is an integer from 1
   to 10. (`true`/`false` and decimals such as `5.0` are not integers.)
   Neither can be 0 during play, because that ends the game.
5. `room` is a ship room id other than `escape_pod` (entering the pod
   always ends the game).
6. `visited` is a list of room ids with no repeats that includes
   `cryo_bay` and `room` and does not include `escape_pod`.
7. `room_items` is an object whose keys are exactly the 11 room ids, and
   each value is a list of strings; the `escape_pod` list is empty.
8. `inventory` is a list of strings.
9. Across `room_items` and `inventory`, every item is one of the four
   starting items, none appears twice, and either all four are there, or
   all except the medkit (it was used).
10. `pod_locked` is `true` or `false`.

These match the rules from earlier rounds: any state the game can reach
during play passes, and a hand-edited file that gives extra oxygen, a
second keycard, or a position inside the pod does not.

**Balance.** Saving and loading do not change any route or number in
Sections 3.3, 3.10, or 3.11. Loading can return the player to a state
with more oxygen than they have now; that is the purpose of R12.

**Output width.** Every new message fits in 50 columns.

---

## 4. Oxygen, Winning, and Losing

### 4.1 Oxygen Rules (R3)

1. Oxygen starts at **12**.
2. A **successful** move to a different room lowers oxygen by exactly **1**.
3. Blocked moves, invalid commands, empty input, `look`, `help`, `quit`,
   (Round 2) `map` and `scan`, and (Round 3) `take`, `drop`, and
   `inventory`, and (Round 4) `use` use **0** oxygen.
4. Oxygen never goes below 0.

(Round 6) `save` and `load` also use **0** oxygen. A successful `load`
sets oxygen to the saved value (Section 3.12).

### 4.2 Turn Resolution Order

When a move succeeds, the game does these steps in order:

1. Move the player to the destination room.
2. Lower oxygen by 1.
3. Show the destination room's information (R2).
4. Check for a **win**: the room is `escape_pod` **and** oxygen > 0. If so,
   status becomes `WON`.
5. Otherwise, check for a **loss**: oxygen == 0. If so, status becomes
   `LOST`.
6. Otherwise, keep playing.

(Round 4) Health adds one step and one check. After step 2, if the
destination is a hazard room, health goes down by 2 (never below 0). Before
the win check in step 4, if health is 0, status becomes `LOST` with outcome
`DIED`, and the win and oxygen checks are skipped. Section 3.10 has the
details.

(Round 5) Before step 1, if the destination is the Escape Pod and the door
is still locked, the move is refused with outcome `LOCKED` and none of the
steps run (Section 3.11). A move into the pod can therefore only reach
the win check once the door is unlocked.

### 4.3 Boundary Interpretation

`problem.md` says the player wins on reaching the pod "while they still have
oxygen" and loses if "oxygen reaches zero before escaping." This spec reads
"still have oxygen" as **oxygen > 0 after the move is paid for.** So:

- Reaching the pod with 1 or more oxygen left after the move is a **win**.
- If the move into the pod brings oxygen to 0, that is a **loss**. The player
  used their last breath on the way and has nothing left when they arrive.

> **Review note:** This is a judgment call. The other reading would be
> "arriving on the last unit still wins." If you prefer that, only step 4's
> condition changes (drop `and oxygen > 0`). Because of the parity note in
> 3.3, this decides whether reaching the pod on move 12 wins or loses.

### 4.4 End-of-Game Messages

**Win** (printed after the Escape Pod room display):
```
>>> LAUNCH SEQUENCE INITIATED <<<
The hatch seals behind you and the pod blasts free of the dying ship.
You escaped with 6 oxygen to spare.
*** YOU WIN ***
```

**Loss** (printed after the room display where oxygen hit 0):
```
>>> OXYGEN DEPLETED <<<
Your vision narrows as the last of the air hisses away...
*** GAME OVER: YOU LOST ***
```

**Quit:**
```
You close your eyes and let the ship drift. Transmission ended.
```

After any of these, the program exits normally with exit code 0. It does
**not** read more input.

### 4.5 Low-Oxygen Warning (flavor)

When oxygen is 3 or less (and the game hasn't ended), the gauge line also
shows `!! LOW OXYGEN !!`. This is only cosmetic and doesn't change any rule.

### 4.6 Revised Escape Requirement (R3, Round 5)

**Original R3 escape condition (Rounds 1-4, kept for history).** From
`problem.md`, Initial requirements: "The goal is to find the escape pod
before running out of oxygen. If they reach the escape pod while they
still have oxygen, they win." Sections 4.2-4.4 and AC-R3.4 / AC-R3.8 built
this rule, and it held through Round 4.

**Revised condition (Round 5).** From `problem.md`, Round 5 requirements:
the player must also unlock the escape pod door with the keycard before
they can escape, still needs oxygen and health remaining to win, and
reaching the escape pod without unlocking the door no longer counts as a
win. The revision replaces the earlier escape condition; the original
oxygen rules still apply.

So from Round 5, the player wins when **all** of these are true after a
move into the Escape Pod:

1. The door was unlocked with the keycard before the move (Section 3.11).
   While it is locked, the move never happens, so it can never win.
2. Oxygen is above 0 after paying for the move (unchanged, Section 4.3).
   Arriving on move 12 with 0 oxygen is still a loss.
3. Health is above 0 (unchanged from Round 4; a hazard can't hit on the
   way into the pod, because the pod is not a hazard room).

The oxygen rules in 4.1, the oxygen loss in step 5 of 4.2, the boundary in
4.3, and the win and loss messages in 4.4 are unchanged.

---

## 5. Handling Invalid Commands

| Situation | Response | Room changes? | Oxygen used? |
|-----------|----------|---------------|--------------|
| Valid direction, but the room has no exit that way | `You can't go <direction> from here.` followed by the room's exits | No | **No** |
| Unrecognized command (e.g. `fly`, `jump`) | `Unknown command: '<text>'. Type 'help' for a list of commands.` | No | **No** |
| `go` with no direction or a bad one (`go`, `go up`) | `Go where? Try north, south, east, or west.` | No | **No** |
| Empty or whitespace-only input | Shows the prompt again with no message | No | **No** |
| Ctrl-D (EOF) or Ctrl-C | Prints the quit message and exits cleanly (no traceback) | n/a | n/a |

Input is trimmed and lower-cased before parsing, so `  NoRtH  ` means
`north`. The prompt is `> `.

(Round 5) Trying to enter the locked Escape Pod is answered like a blocked
move, with the lock message from Section 3.11 and the room's exits. The
room, oxygen, and health do not change.

(Round 6) `save` or `load` followed by more words (`save game`) is an
unknown command. A missing or damaged save file and a save that can't be
written are answered with the messages in Section 3.12; none of them
changes the game or crashes it.

---

## 6. Acceptance Criteria

Each criterion has an ID. Section 7 maps every ID to at least one test.

### R1: Room Navigation

| ID | Criterion |
|----|-----------|
| AC-R1.1 | Typing `north`, `south`, `east`, or `west` when that exit exists moves the player to the connected room. |
| AC-R1.2 | The shortcuts `n`/`s`/`e`/`w` and the form `go <direction>` behave the same as the full direction words. |
| AC-R1.3 | Direction input ignores case and extra spaces. |
| AC-R1.4 | Typing a valid direction with no exit shows a "can't go that way" message. |
| AC-R1.5 | After a blocked move, the player stays in the same room. |
| AC-R1.6 | After a blocked move, oxygen is unchanged. |
| AC-R1.7 | Unknown commands, malformed `go`, and empty input leave the room and oxygen unchanged and never crash the game. |
| AC-R1.8 | All exits in the map work both ways, and every room can be reached from the Cryo Bay. |

### R2: Room Information

| ID | Criterion |
|----|-----------|
| AC-R2.1 | At game start, the starting room's information is shown before the first prompt. |
| AC-R2.2 | After every successful move, the new room's **name** is shown. |
| AC-R2.3 | After every successful move, the new room's **description** is shown. |
| AC-R2.4 | After every successful move, the new room's **available exits** are shown, and they match the room's actual exits. |
| AC-R2.5 | Room information is also shown when entering the Escape Pod (the winning move) and when entering the room where oxygen hits 0 (the losing move). |
| AC-R2.6 | Every room has a non-empty name, a non-empty description, and at least one exit. |

### R3: Oxygen and Escaping

| ID | Criterion |
|----|-----------|
| AC-R3.1 | A new game starts with exactly 12 oxygen. |
| AC-R3.2 | Each successful move lowers oxygen by exactly 1. |
| AC-R3.3 | Blocked moves, invalid commands, `look`, and `help` do not change oxygen. |
| AC-R3.4 | Reaching the Escape Pod with oxygen > 0 after the move sets status to `WON` and shows a win message. |
| AC-R3.5 | When oxygen reaches 0 anywhere other than a winning arrival, status becomes `LOST` and a loss message is shown. |
| AC-R3.6 | Reaching the Escape Pod on the move that brings oxygen to 0 is a **loss** (see 4.3). |
| AC-R3.7 | Once the game is `WON`, `LOST`, or `QUIT`, no more commands are processed and the program exits. |
| AC-R3.8 | Following the shortest route (6 moves) wins with 6 oxygen left. |

(Round 5) R3's escape condition was revised (Section 4.6). The rows above
are kept as written for history. **AC-R3.4** is replaced by AC-R3.10, and
**AC-R3.8** is replaced by AC-R3.11. AC-R3.1-3.3 and AC-R3.5-3.7 still
apply unchanged; AC-R3.6 now needs the door unlocked to be tested.

### R3: Revised Escape Requirement (Round 5)

| ID | Criterion |
|----|-----------|
| AC-R3.9 | Reaching the Escape Pod without unlocking the door is not a win: the move is refused, and the status stays `PLAYING`. |
| AC-R3.10 | With the door unlocked, entering the Escape Pod with oxygen > 0 and health > 0 after the move sets status to `WON` and shows the win message. (Replaces AC-R3.4.) |
| AC-R3.11 | The shortest winning route takes 8 moves (including the keycard detour to the Bridge) and wins with 4 oxygen and 8 health; no shorter route wins. (Replaces AC-R3.8.) |
| AC-R3.12 | The original oxygen rules still apply with the door unlocked: entering the pod on the move that brings oxygen to 0 is a loss, and a 10-move win ends with 2 oxygen. |

### R4: Ship Map (Round 2)

| ID | Criterion |
|----|-----------|
| AC-R4.1 | `map` and `m` (ignoring case and extra spaces) are recognized as the map command, and `help` lists it. |
| AC-R4.2 | The map shows every room the player has visited, including the Cryo Bay at the start. |
| AC-R4.3 | The map marks the current room with `*`, and only the current room. It also names the current room. |
| AC-R4.4 | Rooms the player has not visited do not appear on the map, and neither do connections into them. |
| AC-R4.5 | A line is drawn between two visited rooms only when an exit joins them. |
| AC-R4.6 | Using the map uses no oxygen and does not change the room or status. |
| AC-R4.7 | Each room is recorded once no matter how often it is entered, and the map shows "Rooms visited: N of 11". |
| AC-R4.8 | Every room's map position agrees with its exits, and every map line fits in 50 columns. |

### R5: Room Scanner (Round 2)

| ID | Criterion |
|----|-----------|
| AC-R5.1 | `scan` and `sc` (ignoring case and extra spaces) are recognized as the scan command, and `help` lists it. |
| AC-R5.2 | Every room has a non-empty clue that is different from every other room's clue and from its own description. |
| AC-R5.3 | Scanning shows the current room's name and that room's clue. |
| AC-R5.4 | Scanning uses no oxygen and does not change the room or status. |
| AC-R5.5 | The same room can be scanned more than once, and it gives the same clue each time. |
| AC-R5.6 | Scanner output fits in 50 columns. |

(Round 5 clarification) AC-R5.1-5.6 still apply unchanged. AC-R5.7 is
added because the Bridge became required in Round 5.

| ID | Criterion |
|----|-----------|
| AC-R5.7 | (Round 5) No clue steers the player away from the Bridge. The Central Corridor clue says the keycard is on the Bridge to the north and still points south toward the engine rooms; the Bridge clue says the escape pod needs a keycard. Neither clue says where or how the keycard is used. |

### R6: Collecting Items (Round 3)

| ID | Criterion |
|----|-----------|
| AC-R6.1 | `take <item>` and `get <item>` (ignoring case and extra spaces) are recognized as the take command with the item's normalized name; `take` or `get` with no name gives `Take what?`. `help` lists `take`. |
| AC-R6.2 | The ship starts with the flashlight in the Cryo Bay, the medkit in the Medical Bay, the keycard on the Bridge, and the repair kit in Engineering. Item names are unique, and the Escape Pod has no items. |
| AC-R6.3 | When a room is displayed (game start, entering it, `look`), its current items are listed on an `Items here:` line; the line is left out when the room has none. |
| AC-R6.4 | Taking an item that is in the current room removes it from the room, adds it to the inventory, and confirms with a message. |
| AC-R6.5 | Taking an item that is not in the current room (already carried, in another room, or not a real item) says it is not here and changes nothing. |
| AC-R6.6 | Taking an item uses no oxygen and does not change the room or status. Collecting items along the shortest route still wins with 6 oxygen. |
| AC-R6.7 | Item names must be typed in full (case and spaces ignored); a partial name such as `kit` does not match. |

(Round 5) The second sentence of AC-R6.6 refers to the old 6-move route.
From Round 5, taking items still costs no oxygen, and collecting items
along the 8-move keycard route still wins with 4 oxygen (AC-R3.11).

### R7: Inventory System (Round 3)

| ID | Criterion |
|----|-----------|
| AC-R7.1 | `inventory`, `inv`, and `i` (ignoring case and extra spaces) are recognized as the inventory command, and `drop <item>` as the drop command. `help` lists both. |
| AC-R7.2 | The inventory command lists every carried item, in pickup order. |
| AC-R7.3 | With nothing carried, the inventory command says `Your inventory is empty.` |
| AC-R7.4 | Dropping a carried item removes it from the inventory and puts it in the current room, where it is shown and stays until taken again (it can be taken again later). |
| AC-R7.5 | Dropping an item that is not carried says so and changes nothing; `drop` with no name gives `Drop what?`. |
| AC-R7.6 | Checking the inventory and dropping items use no oxygen and do not change the room or status. |
| AC-R7.7 | Items are never duplicated or lost: across all rooms and the inventory there are always exactly the four starting items. |
| AC-R7.8 | Item and inventory output fits in 50 columns, even with all four items in one room. |

(Round 4) From Round 4 on, AC-R7.7 holds until the medkit is used. After
that, AC-R9.7 applies instead.

### R8: Health and Hazards (Round 4)

| ID | Criterion |
|----|-----------|
| AC-R8.1 | A new game starts with exactly 10 health. |
| AC-R8.2 | Every room display (game start, entering a room, `look`, and the final display when the game ends) shows `[ HEALTH: <h>/10 ]` on the line under the oxygen gauge. |
| AC-R8.3 | The Reactor Core and the Cargo Hold are the only hazard rooms. |
| AC-R8.4 | Every successful move into a hazard room, including going back into one, lowers health by exactly 2 and shows the hazard message for that room. |
| AC-R8.5 | A move into a hazard room costs exactly 1 oxygen, the same as any move. Moves into safe rooms, blocked moves, and all non-move commands (including `look` in a hazard room) do not change health. |
| AC-R8.6 | When health reaches 0, status becomes `LOST` and the game shows the room, the hazard message, and the "You didn't survive." ending; no more commands are processed. Health never goes below 0. |
| AC-R8.7 | If one move brings both health and oxygen to 0, the health ending is shown, not the oxygen one. |
| AC-R8.8 | The player can escape without healing: both 6-move routes win with 8 health and 6 oxygen. |
| AC-R8.9 | Health and hazard output fits in 50 columns. |

(Round 5) AC-R8.8 refers to the 6-move routes, which no longer win. The
R8 goal still holds: both 8-move keycard routes win without healing, with
8 health and 4 oxygen (AC-R3.11, AC-R10.8).

### R9: Medkit Healing (Round 4)

| ID | Criterion |
|----|-----------|
| AC-R9.1 | `use <item>` (ignoring case and extra spaces) is recognized as the use command with the item's normalized name; `use` with no name gives `Use what?`. `help` lists `use`. |
| AC-R9.2 | With the medkit carried and health below 10, `use medkit` restores 4 health, never going above 10, and says how much was restored. |
| AC-R9.3 | A successful `use medkit` removes the medkit from the inventory. |
| AC-R9.4 | `use medkit` when the medkit is not carried (never taken, dropped, or already used) says the player is not carrying it and changes nothing. |
| AC-R9.5 | `use medkit` at full health says so, keeps the medkit, and changes nothing. |
| AC-R9.6 | Using an item uses no oxygen and does not change the room, status, or visited rooms. |
| AC-R9.7 | Other items work as before: `use` on any other carried item says it can't be used and changes nothing, and `take`, `drop`, and `inventory` still work for every item, including the medkit before it is used. Items are never duplicated or lost, except that a used medkit is no longer in any room or the inventory. |

(Round 5) From Round 5 the keycard is an exception to "any other carried
item": it follows AC-R10.3-10.6. The flashlight and repair kit still can't
be used. The keycard is never used up, so the item count rule is unchanged.

### R10: Keycard and Locked Escape Pod (Round 5)

| ID | Criterion |
|----|-----------|
| AC-R10.1 | A new game starts with the Escape Pod door locked, and the keycard on the Bridge. |
| AC-R10.2 | Moving into the Escape Pod while the door is locked shows `The escape pod door is locked.`, the keycard-reader hint, and the exits. The player stays in the Airlock Junction, and oxygen, health, status, visited rooms, and items do not change. This holds every time it is tried. |
| AC-R10.3 | With the keycard carried, `use keycard` at the Airlock Junction unlocks the door and says so; the next move east enters the Escape Pod. |
| AC-R10.4 | Unlocking uses no oxygen or health, does not change the room, status, or visited rooms, and does not use up the keycard (it stays in the inventory). |
| AC-R10.5 | `use keycard` with the keycard carried in any room other than the Airlock Junction says `The keycard doesn't work here.` and changes nothing. |
| AC-R10.6 | `use keycard` without carrying the keycard says the player is not carrying it, and the door stays locked. |
| AC-R10.7 | Once unlocked, the door stays unlocked even if the keycard is dropped; `use keycard` at the Airlock Junction again says `The escape pod door is already unlocked.` and changes nothing. |
| AC-R10.8 | The game is still winnable from 12 oxygen and 10 health without healing, using the keycard (8-move routes, 4 oxygen and 8 health left). |
| AC-R10.9 | The Airlock Junction's `Exits:` line is unchanged by the lock, `help` still lists `use`, and all new output fits in 50 columns. |

### R11: Saving the Game (Round 6)

| ID | Criterion |
|----|-----------|
| AC-R11.1 | `save` (ignoring case and extra spaces) is recognized as the save command; `save` followed by other words is an unknown command. `help` lists `save`. |
| AC-R11.2 | `save` writes `signal_lost_save.json` in the current folder as a JSON object with `version` 1 and the current `room`, `oxygen`, `health`, `status`, `visited` (sorted), `room_items` (every room), `inventory` (pickup order), and `pod_locked`. |
| AC-R11.3 | Saving uses no oxygen or health and does not change the room, status, visited rooms, items, inventory, or lock. |
| AC-R11.4 | A successful save prints `Game saved.` |
| AC-R11.5 | There is one save slot: saving again replaces the previous save with the current state. |
| AC-R11.6 | If the file can't be written, `Save failed: the file could not be written.` is shown, the game goes on unchanged, and an earlier save file is not changed. |
| AC-R11.7 | The save file (and its temporary file) is ignored by Git, and saving uses only the standard library. |

### R12: Loading the Game (Round 6)

| ID | Criterion |
|----|-----------|
| AC-R12.1 | `load` (ignoring case and extra spaces) is recognized as the load command; `load` followed by other words is an unknown command. `help` lists `load`. |
| AC-R12.2 | Loading a save restores the room, oxygen, health, inventory (in order), the items in every room, the visited rooms (the map), and the pod lock, with status `PLAYING`. |
| AC-R12.3 | After loading, the game behaves exactly as if the saved game had gone on: the same commands give the same results, including unlocking the pod and winning. This works from a new game and from a new run of `python3 main.py`. |
| AC-R12.4 | A successful load prints `Game loaded.` and then the restored room display, with its items, exits, and the oxygen and health gauges. |
| AC-R12.5 | The `load` command itself uses no oxygen or health: afterwards both equal the saved values exactly. Loading does not change or delete the save file, and the same save can be loaded more than once. |
| AC-R12.6 | With no save file, `load` prints `There is no saved game to load.`, changes nothing, and does not crash. |
| AC-R12.7 | A damaged save file (unreadable, not UTF-8, not JSON, or failing any check in Section 3.12) makes `load` print the damaged-file message and change nothing, without crashing. |
| AC-R12.8 | Loading is all-or-nothing: a file that fails a check after other fields looked valid still leaves every part of the current game unchanged. |
| AC-R12.9 | All save and load output fits in 50 columns. |

### General Quality

| ID | Criterion |
|----|-----------|
| AC-G.1 | `python3 main.py` starts the game with no extra setup. |
| AC-G.2 | `python3 -m unittest` runs all tests from the project root, and they all pass. |
| AC-G.3 | EOF and Ctrl-C end the game cleanly without a traceback. |
| AC-G.4 | `game.py` has no `print` or `input` calls. All I/O happens in `cli.py`. |

---

## 7. Automated Testing (unittest)

### 7.1 Framework and Conventions

- Uses only the standard-library `unittest` module.
- Test files are named `tests/test_*.py` so `unittest` discovery finds them.
- Tests are deterministic and need no terminal. The CLI is tested by passing
  in fake `input_fn` and `output_fn` callables: a scripted list of inputs, and
  a list that collects the output lines.
- Each test creates a fresh `Game`, so no state is shared between tests.

### 7.2 Test Plan

| File | Test (summary) | Covers |
|------|----------------|--------|
| `test_world.py` | Map has 11 rooms; `START_ROOM` and `ESCAPE_ROOM` exist | AC-R2.6 |
| | Every exit's destination exists and the reverse exit points back | AC-R1.8 |
| | Every room can be reached from `cryo_bay` (BFS) | AC-R1.8 |
| | Every room has a non-empty name, a description, and at least one exit | AC-R2.6 |
| | Shortest path from start to pod is 6 (BFS) | AC-R3.8 |
| `test_parser.py` | `north`/`n`/`go north`/`GO N`/`  North  ` all parse to move north (and the same for all 4 directions) | AC-R1.2, AC-R1.3 |
| | `look`, `help`, `quit` and their aliases parse correctly | 3.5 |
| | `fly`, `go`, `go up`, `""`, `"   "` parse to unknown/empty with no exception | AC-R1.7 |
| `test_game.py` | New game: room is `cryo_bay`, oxygen is 12, status is `PLAYING` | AC-R3.1 |
| | Valid move changes the room and lowers oxygen by 1 | AC-R1.1, AC-R3.2 |
| | Blocked move: outcome is `BLOCKED`, room and oxygen unchanged | AC-R1.4–1.6, AC-R3.3 |
| | Unknown, empty, look, and help: room and oxygen unchanged | AC-R1.7, AC-R3.3 |
| | Shortest route → `WON` with oxygen 6 | AC-R3.4, AC-R3.8 |
| | 10-move route ending at pod → `WON` with oxygen 2 | AC-R3.4 |
| | 12-move route ending at pod → `LOST` (boundary) | AC-R3.6 |
| | 12 moves of back-and-forth without reaching the pod → `LOST` | AC-R3.5 |
| | After `WON` or `LOST`, `handle()` makes no further state changes | AC-R3.7 |
| | 11 blocked moves then 1 real move: oxygen is 11 (blocked moves are free) | AC-R1.6, AC-R3.3 |
| `test_cli.py` | Output starts with the Cryo Bay name, description, and exits before the first prompt | AC-R2.1 |
| | After each move, output has the new room's name, description, and correct `Exits:` line | AC-R2.2–2.4 |
| | Winning playthrough: pod room info is printed, then `YOU WIN`; loop ends with inputs left over | AC-R2.5, AC-R3.4, AC-R3.7 |
| | Losing playthrough: final room info is printed, then `GAME OVER` | AC-R2.5, AC-R3.5 |
| | Blocked move prints the "can't go" message | AC-R1.4 |
| | Unknown command prints the "Unknown command" message | AC-R1.7 |
| | `input_fn` raising `EOFError` or `KeyboardInterrupt` → quit message, no exception | AC-G.3 |
| | `game.py` source has no `print(` or `input(` (static check) | AC-G.4 |

Round 2 additions:

| File | Test (summary) | Covers |
|------|----------------|--------|
| `test_world.py` | Every room has a clue that is unique and differs from its description | AC-R5.2 |
| | `MAP_GRID` covers every room, positions are unique, and each exit joins grid neighbors | AC-R4.8 |
| `test_parser.py` | `map`/`m`/`  MAP ` parse to map; `scan`/`sc`/`SCAN` parse to scan | AC-R4.1, AC-R5.1 |
| `test_game.py` | New game has visited = {`cryo_bay`}; moves add rooms; blocked moves and revisits don't | AC-R4.2, AC-R4.7 |
| | `map` and `scan` return `MAPPED`/`SCANNED` and change no oxygen, room, or status, even when repeated | AC-R4.6, AC-R5.4, AC-R5.5 |
| | Shortest route still wins with 6 oxygen when `map`/`scan` are used at every step | AC-R4.6, AC-R5.4 |
| `test_cli.py` | Map at start shows only the Cryo Bay, marked `*` | AC-R4.2–4.4 |
| | Map after exploring shows visited rooms, correct lines, no unvisited labels | AC-R4.2–4.5 |
| | Sealed bulkhead between two visited rooms has no line | AC-R4.5 |
| | Map lines fit in 50 columns, including the fully explored map | AC-R4.8 |
| | Scan prints the current room's clue; repeated scans print the same text | AC-R5.3, AC-R5.5 |
| | `help` lists `map` and `scan` | AC-R4.1, AC-R5.1 |

Round 3 additions:

| File | Test (summary) | Covers |
|------|----------------|--------|
| `test_world.py` | Starting items are in the rooms listed in 3.9; names are unique, lower-case, and non-empty; the Escape Pod is empty | AC-R6.2 |
| `test_parser.py` | `take`/`get`/`  TAKE  Repair  Kit ` parse to take with a normalized name; bare `take`/`get` give no name | AC-R6.1, AC-R6.7 |
| | `drop <item>` parses to drop; `inventory`/`inv`/`i` parse to inventory | AC-R7.1 |
| `test_game.py` | New game: empty inventory, room items match `Room.items` | AC-R6.2, AC-R7.3 |
| | Take moves an item from room to inventory (`TAKEN`); missing, carried, partial, or no-name takes change nothing | AC-R6.4, AC-R6.5, AC-R6.7 |
| | Drop moves an item from inventory to the current room (`DROPPED`), and it can be taken again; drop of an uncarried item changes nothing | AC-R7.4, AC-R7.5 |
| | Inventory keeps pickup order | AC-R7.2 |
| | Take, drop, and inventory change no oxygen, room, status, or visited rooms; shortest route with items still wins with 6 | AC-R6.6, AC-R7.6 |
| | Item total stays at four after a mix of moves, takes, and drops | AC-R7.7 |
| `test_cli.py` | Start, entering, and `look` show `Items here:`; empty rooms have no such line | AC-R6.3 |
| | Take, drop, and inventory print the messages in 3.9 (including empty inventory, `Take what?`, `Drop what?`) | AC-R6.4, AC-R6.5, AC-R7.2-7.5 |
| | A dropped item appears when the player comes back to that room | AC-R7.4 |
| | `help` lists take, drop, and inventory; item output fits 50 columns with all items in one room | AC-R6.1, AC-R7.1, AC-R7.8 |

Round 4 additions:

| File | Test (summary) | Covers |
|------|----------------|--------|
| `test_world.py` | Only the Reactor Core and Cargo Hold are hazards; `HAZARD_ROOMS` matches `Room.hazard` | AC-R8.3 |
| | Every route to the pod passes a hazard; both 6-move routes enter exactly one | AC-R8.8 |
| `test_parser.py` | `use medkit`/`  USE  MedKit ` parse to use with a normalized name; bare `use` gives no name | AC-R9.1 |
| `test_game.py` | New game has 10 health; entering a hazard costs 2 health and 1 oxygen, again on re-entry; safe moves, blocked moves, and other commands don't | AC-R8.1, AC-R8.3-8.5 |
| | Health 0 → `DIED`/`LOST`, health never negative; both reaching 0 together → `DIED`; game over afterwards | AC-R8.6, AC-R8.7 |
| | Shortest routes win with 8 health and 6 oxygen | AC-R8.8 |
| | `use medkit` heals 4, capped at 10, removes the medkit; not carried, full health, other items, and no name change nothing; use is free | AC-R9.2-9.7 |
| | Item total is three after the medkit is used, four before | AC-R9.7 |
| `test_cli.py` | Health gauge line under oxygen at start, after moves, on `look`, and on the final win/loss/death displays | AC-R8.2 |
| | Hazard message after entering each hazard room; no message in safe rooms | AC-R8.4 |
| | Health ending text, including when oxygen hits 0 on the same move | AC-R8.6, AC-R8.7 |
| | `use` messages from 3.10; `help` lists `use`; all new output fits 50 columns | AC-R9.1-9.5, AC-R8.9 |

Round 5 additions:

| File | Test (summary) | Covers |
|------|----------------|--------|
| `test_world.py` | `KEYCARD_READER` is the Airlock Junction, next to the pod; the keycard starts on the Bridge | AC-R10.1 |
| `test_parser.py` | `use keycard` / `  USE  KeyCard ` parse to use with the name `keycard` | AC-R10.3 |
| `test_game.py` | New game has the pod locked; a locked move gives `LOCKED` and changes nothing, even when repeated or done at low oxygen | AC-R10.1, AC-R10.2, AC-R3.9 |
| | `use keycard`: unlocks at the Airlock, is free, keeps the keycard; wrong room, not carried, and already unlocked change nothing; dropping the keycard keeps the door open | AC-R10.3-10.7 |
| | Keycard routes: 8-move routes win with 4 oxygen and 8 health; no route without the keycard wins; 10-move win ends with 2 oxygen; 12-move pod arrival is a loss | AC-R3.10-3.12, AC-R10.8 |
| | The flashlight and repair kit still can't be used; item count is unchanged after unlocking | AC-R9.7 |
| `test_cli.py` | Locked-door message and exits; unlock, already-unlocked, and wrong-place messages | AC-R10.2-10.7 |
| | Full keycard playthrough wins; the Airlock exits line is unchanged; new output fits 50 columns | AC-R3.10, AC-R10.8, AC-R10.9 |
| `test_world.py` | (Round 5 clarification) Corridor clue names the keycard, the Bridge, and north, and still points south; Bridge clue says the pod needs a keycard; the old "cold and still" / "Nothing forward" wording is gone; neither clue mentions the airlock, the reader, or `use keycard` | AC-R5.7 |
| `test_cli.py` | (Round 5 clarification) Scanning the Corridor and the Bridge shows the keycard hint within 50 columns | AC-R5.7, AC-R5.6 |

Round 6 additions (every test uses a temporary folder, so no test writes a
save file into the project):

| File | Test (summary) | Covers |
|------|----------------|--------|
| `test_parser.py` | `save`/`  SAVE ` and `load`/`Load` parse to save and load; `save game` and `load 2` are unknown | AC-R11.1, AC-R12.1 |
| `test_savefile.py` | `write` then `read` returns the same data; the file is UTF-8 JSON with a trailing newline; the default name is `signal_lost_save.json` | AC-R11.2 |
| | Writing replaces an earlier file; a failed write leaves the earlier file unchanged and raises `OSError` | AC-R11.5, AC-R11.6 |
| | Reading a missing file raises `NoSaveFile`; unreadable, non-UTF-8, and non-JSON files raise `DamagedSave` | AC-R12.6, AC-R12.7 |
| | `.gitignore` ignores the save file and its temporary file; the module imports only the standard library | AC-R11.7 |
| `test_game.py` | `save` writes every field listed in 3.12 with the current values, and changes no state or oxygen/health | AC-R11.2-11.4 |
| | Saving twice keeps only the second state; an unwritable path gives `SAVE_FAILED` and changes nothing | AC-R11.5, AC-R11.6 |
| | `load` in a new game restores every field (including an unlocked pod, a used medkit, and dropped items) | AC-R12.2, AC-R12.5 |
| | A loaded game and an uninterrupted game give the same results for the rest of a winning script | AC-R12.3 |
| | No file gives `NO_SAVE`; each kind of damaged file gives `DAMAGED_SAVE`; neither changes any state | AC-R12.6-12.8 |
| | Save and load after the game has ended give `GAME_OVER` and write nothing | 3.12 |
| `test_cli.py` | `save` prints `Game saved.`; `load` prints `Game loaded.` and the room display with gauges; missing, damaged, and unwritable files print their messages; `help` lists both; output fits 50 columns | AC-R11.1, AC-R11.4, AC-R11.6, AC-R12.1, AC-R12.4, AC-R12.6, AC-R12.7, AC-R12.9 |
| | Save, wander, load, and finish the keycard route: wins with 4 oxygen | AC-R12.3 |
| | `python3 main.py` saves in one run and loads and wins in a second run (in a temporary folder) | AC-R12.3 |

(Round 5) Existing Round 1-4 tests whose scripted routes walked straight
into the pod are given the keycard detour, because the revised R3 makes
those routes stop at the locked door instead of winning. The paths below
marked "Round 1" and "Round 4" keep their historical wording.

Example scripted paths:
- **Shortest win (6):** `n, e, s, s, e, e`
- **10-move win:** `n, s, n, s, n, e, s, s, e, e`
- **12-move pod arrival (loss):** `n, s, n, s, n, s, n, e, s, s, e, e`
- **Wander loss (12):** `n, s` repeated 6 times
- **(Round 4) Hazard death (12):** `n, e, s, e`, then `w, e` repeated 4
  times (the Reactor Core five times; health and oxygen both reach 0)
- **(Round 5) Keycard win (8):** `n, e, n, take keycard, s, s, s, e, use
  keycard, e` (4 oxygen, 8 health). Through the Reactor Core: `n, e, n,
  take keycard, s, s, e, s, use keycard, e`.
- **(Round 5) 10-move keycard win:** `n, s, n, e, n, take keycard, s, s,
  s, e, use keycard, e` (2 oxygen)
- **(Round 5) 12-move keycard pod arrival (loss):** `n, s, n, s, n, e, n,
  take keycard, s, s, s, e, use keycard, e`
- **(Round 5) Locked door:** `n, e, s, s, e, e` now stops at the Airlock
  Junction with the lock message, with 7 oxygen and 8 health.
- **(Round 6) Save and come back:** `n, e, n, take keycard, s, save, s, s,
  load, s, s, e, use keycard, e` wins with 4 oxygen and 8 health: the
  `load` puts the player back in the Central Corridor with 8 oxygen.

### 7.3 Running Tests

From the project root:

```bash
python3 -m unittest            # quiet
python3 -m unittest -v         # verbose, one line per test
```

---

## 8. Running the Game

From the project root, with one command:

```bash
python3 main.py
```

No install step, virtual environment, or dependencies are needed.

---

## 9. Extensibility for Later Rounds (Round 1 design notes)

The Round 1 design leaves clear places for future features. **None of the
following will be built in Round 1.**

> **Status after Round 4:** Inventory (Round 3) and hazards (Round 4) are
> built; the rows below say where. Puzzles / locked doors and save/load are
> still not implemented. Save/load now also needs `visited`, `room_items`,
> `inventory`, and `health` (Sections 3.7, 3.9, 3.10).
>
> **Status after Round 5:** The locked Escape Pod door is built as a single
> `pod_locked` flag on `Game`, checked in `Game._move()` before the room
> changes (Section 3.11). A general `Exit` object was not needed for one
> door. Save/load also needs `pod_locked`.
>
> **Status after Round 6:** Save/load is built (Section 3.12). As planned
> above, only player state is saved and the map comes from `build_ship()`.
> The row below says what changed from the plan.

| Future feature | Where it will plug in |
|----------------|-----------------------|
| **Inventory** (`take`, `drop`, `inventory`) | *Built in Round 3, see Section 3.9.* Add an `items` field to `Room` and an `inventory` to `Game`. Add new `Command.kind` values in `parser.py` and handlers in `Game.handle`. The CLI loop doesn't change. |
| **Hazards** (e.g. a reactor leak that costs extra oxygen) | *Built in Round 4 as health damage, see Section 3.10.* Add a hook in `Game` after "enter room" (step 3 in 4.2) that can change oxygen or status. Rooms get an optional hazard attribute. |
| **Puzzles / locked doors** | Exits can later point to a small `Exit` object (destination + optional lock condition). Movement already goes through a single method, `Game._move()`, so lock checks go in one place. |
| **Save / load** | All game state lives in plain data on `Game` (room id, oxygen, status). Later rounds add `to_dict()` / `from_dict()` and JSON storage. The map is rebuilt from `build_ship()`, so only player state needs saving. *(Round 6) Built in Section 3.12 as `Game.save_data()` and a checked restore in `game.py`, with JSON file reading and writing in `savefile.py`. It saves room id, oxygen, health, status, visited, room items, inventory, and the pod lock.* |
| **New commands in general** | `Game.handle` sends each command to a handler using a dict of `kind → method`, so adding a command means adding one parser rule and one handler. |

Round 1 code must **not** include stub fields, placeholder commands, or unused
hooks for these features. The structure above is enough to add them cleanly
later.

---

## 10. Out of Scope for Round 1

Items, inventory, hazards, puzzles, locked doors, save/load, randomness,
color output, sound, difficulty levels, and score tracking.

### Round 2

Round 2 adds only the map (R4) and the scanner (R5). Everything listed
above is still out of scope. Scanning does not reveal unvisited rooms on
the map, and the map does not hint at unexplored exits.

### Round 3

Round 3 adds only collecting items (R6) and the inventory (R7). Items have
no effect on movement, oxygen, or winning; locked doors, puzzles, item
descriptions (`examine`), using items, carrying limits, `take all` /
`drop all`, and partial item names are out of scope. Hazards, save/load,
and the rest of the list above are still out of scope.

### Round 4

Round 4 adds only health and hazards (R8) and using the medkit (R9).
Hazards that cost oxygen or change over time, random damage, other ways to
heal, a low-health warning, health in the win message, uses for the
flashlight, keycard, or repair kit, locked doors, puzzles, and save/load
are out of scope.

### Round 5

Round 5 adds only the locked Escape Pod door and the keycard (R10) and
the revised escape condition (R3). Other locked doors, other puzzles,
re-locking the door, a keycard that is used up, marking locked exits on the
`Exits:` line or the map, changing scan clues or room descriptions, uses
for the flashlight or repair kit, and save/load are out of scope.

(Round 5 clarification) One exception to the list above: the Central
Corridor and Bridge scan clues were corrected, because they told the
player to avoid the Bridge, which R10 makes required (Section 3.8, AC-R5.7).
Room descriptions and every other clue are unchanged.

### Round 6

Round 6 adds only saving (R11) and loading (R12). Several save slots or
named saves, choosing the save file's location in the game, asking before
overwriting, auto-saving, loading automatically at start-up, deleting a
save from the game, saving after the game ends, save files from other
versions of the game, encryption or checksums, and showing the inventory
or the lock on `load` are out of scope. Other puzzles and locked doors are
still out of scope.
