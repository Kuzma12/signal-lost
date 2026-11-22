# Signal Lost: Specification (Rounds 1-3)

This spec covers Rounds 1 to 3 of *Signal Lost*.

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

Features planned for later rounds (inventory, hazards, puzzles, save/load)
are **out of scope**. Section 9 only describes where they will fit.

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
| `world.py` | Defines the `Room` type (id, name, description, exits, and from Round 2 a scanner `clue`) and `build_ship()`, which returns the full map. Also defines the `START_ROOM` and `ESCAPE_ROOM` ids and (Round 2) `MAP_GRID`, each room's row/column on the ship grid. (Round 3) Each `Room` also lists the items it holds at the start of a game. | Know about oxygen, input, or output. |
| `parser.py` | `parse(text) -> Command`. Normalizes case and whitespace, expands aliases (`n` → `north`, `go north` → `north`), and labels input as move / help / look / quit / map / scan / empty / unknown, and (Round 3) take / drop / inventory. | Change game state. |
| `game.py` | `Game` class holding the current room, oxygen, status (`PLAYING`, `WON`, `LOST`, `QUIT`), and (Round 2) the set of visited room ids. (Round 3) It also holds the items currently in each room and the player's inventory. `Game.handle(command) -> TurnResult` applies the rules and returns a structured result. | Call `print()` or `input()`. |
| `cli.py` | `run(input_fn=input, output_fn=print)`. Reads input, calls the parser and `Game.handle`, and renders results to text. | Contain game rules. |
| `main.py` | Calls `signal_lost.cli.run()` inside `if __name__ == "__main__":`. Nothing else. | Contain logic. |

**Key principle:** game logic (`game.py`) stays separate from I/O (`cli.py`).
This keeps the rules easy to unit-test without faking a terminal. It also
lets later rounds add features without rewriting the loop.

### 2.2 Core Data Types

- **`Room`** (frozen dataclass): `id: str`, `name: str`,
  `description: str`, `exits: dict[str, str]` (direction → destination room id),
  and from Round 2 `clue: str` (the scanner text, Section 3.8). From Round 3,
  `items: tuple[str, ...]` (the item names in this room when a game starts,
  Section 3.9). `Room` stays frozen; items that move during play are tracked
  by `Game`, not by `Room`.
- **`Command`** (frozen dataclass): `kind: str` (`"move"`, `"help"`,
  `"look"`, `"quit"`, `"map"`, `"scan"`, `"empty"`, `"unknown"`),
  `arg: str | None` (the direction for moves, the original text for unknown
  input). From Round 3, `kind` can also be `"take"`, `"drop"`, or
  `"inventory"`, and `arg` is the item name for `take` / `drop` (lower-case,
  single-spaced, or `None` if no name was typed).
- **`TurnResult`** (dataclass): `outcome` (an enum such as `MOVED`,
  `BLOCKED`, `INVALID`, `LOOKED`, `HELP`, `MAPPED`, `SCANNED`, `WON`, `LOST`,
  `QUIT`), `room: Room`, `oxygen: int`, `oxygen_used: int` (0 or 1), and from
  Round 2 `visited: frozenset[str]` (ids of every room entered so far,
  including the start room). From Round 3 it also has `items: tuple[str, ...]`
  (items in the current room now), `inventory: tuple[str, ...]` (items the
  player carries, in pickup order), and `item: str | None` (the item named by
  a `take` / `drop`). New outcomes: `TAKEN`, `NOT_HERE`, `DROPPED`,
  `NOT_CARRIED`, `INVENTORY`.
- **Constants** in `game.py`: `STARTING_OXYGEN = 12`, `OXYGEN_PER_MOVE = 1`.

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
| `help` / `h` / `?` | Lists the available commands |
| `quit` / `q` / `exit` | Ends the game with a goodbye message. This counts as neither a win nor a loss. |

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

---

## 4. Oxygen, Winning, and Losing

### 4.1 Oxygen Rules (R3)

1. Oxygen starts at **12**.
2. A **successful** move to a different room lowers oxygen by exactly **1**.
3. Blocked moves, invalid commands, empty input, `look`, `help`, `quit`,
   (Round 2) `map` and `scan`, and (Round 3) `take`, `drop`, and
   `inventory` use **0** oxygen.
4. Oxygen never goes below 0.

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

Example scripted paths:
- **Shortest win (6):** `n, e, s, s, e, e`
- **10-move win:** `n, s, n, s, n, e, s, s, e, e`
- **12-move pod arrival (loss):** `n, s, n, s, n, s, n, e, s, s, e, e`
- **Wander loss (12):** `n, s` repeated 6 times

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

## 9. Extensibility for Later Rounds (design only; NOT implemented now)

The Round 1 design leaves clear places for future features. **None of the
following will be built in Round 1.**

| Future feature | Where it will plug in |
|----------------|-----------------------|
| **Inventory** (`take`, `drop`, `inventory`) | *Built in Round 3, see Section 3.9.* Add an `items` field to `Room` and an `inventory` to `Game`. Add new `Command.kind` values in `parser.py` and handlers in `Game.handle`. The CLI loop doesn't change. |
| **Hazards** (e.g. a reactor leak that costs extra oxygen) | Add a hook in `Game` after "enter room" (step 3 in 4.2) that can change oxygen or status. Rooms get an optional hazard attribute. |
| **Puzzles / locked doors** | Exits can later point to a small `Exit` object (destination + optional lock condition). Movement already goes through a single method, `Game._move()`, so lock checks go in one place. |
| **Save / load** | All game state lives in plain data on `Game` (room id, oxygen, status). Later rounds add `to_dict()` / `from_dict()` and JSON storage. The map is rebuilt from `build_ship()`, so only player state needs saving. |
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
