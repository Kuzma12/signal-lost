# Signal Lost

*You wake up in a cryo pod. Warning lights flash red. The ship's AI is silent
and the hull is breached. Your suit has twelve units of oxygen left.
Somewhere aboard is an escape pod. Find it before you run out of air.*

**Signal Lost** is a single-player text adventure that runs in the terminal.
You move through a damaged spaceship by typing compass directions. Every
move to another room uses one unit of oxygen, and some rooms are dangerous
to enter. Reach the Escape Pod before your oxygen or your health runs out to
win.

This is a CSC 299 final project, built in rounds. **Round 1** covers room
navigation, room information, and oxygen with win/loss. **Round 2** adds a
ship map of the rooms you've explored and a room scanner that gives clues.
**Round 3** adds items you can pick up, carry, and drop. **Round 4** (this
version) adds health, hazard rooms that hurt you, and a medkit you can use
to heal. Puzzles and save/load are planned for later rounds.

## Requirements

- Python 3.10 or newer
- Nothing else. The game uses only the standard library, so there is nothing
  to install and no virtual environment to set up.

## How to run

From the project root:

```bash
python3 main.py
```

## How to play

You start in the **Cryo Bay** with **12 oxygen** and **10 health**. Each time
you enter a room, the game shows its name, a short description, any items
lying there, the exits you can take, and your oxygen and health gauges:

```
==================================================
  CENTRAL CORRIDOR
==================================================
The ship's main artery. Emergency strip-lights
pulse red along a passage that branches in every
direction.

Exits: north, east, south, west
[ OXYGEN: 10/12 ]
[ HEALTH: 10/10 ]
```

### Commands

| Command | Shortcuts | What it does | Oxygen cost |
|---------|-----------|--------------|-------------|
| `north`, `south`, `east`, `west` | `n`, `s`, `e`, `w`, `go north` | Move to the next room | 1 |
| `look` | `l` | Describe the current room again | 0 |
| `map` | `m` | Show a map of the rooms you've visited (`*` marks where you are) | 0 |
| `scan` | `sc` | Scan the current room for a clue | 0 |
| `take <item>` | `get <item>` | Pick up an item in this room, e.g. `take repair kit` | 0 |
| `drop <item>` | | Leave a carried item in this room | 0 |
| `inventory` | `inv`, `i` | List the items you are carrying | 0 |
| `use <item>` | | Use a carried item; `use medkit` heals you | 0 |
| `help` | `h`, `?` | List the commands | 0 |
| `quit` | `q`, `exit` | Give up and end the game | 0 |

Commands ignore upper/lower case and extra spaces, so `  GO N ` works.
Item names must be typed in full: `take Repair Kit` works, `take kit` doesn't.

### Rules

- A successful move to another room costs **1 oxygen**.
- Bumping into a wall (a direction with no exit), typing an unknown command,
  `look`, `map`, `scan`, `take`, `drop`, `inventory`, `use`, and `help` are
  all **free**. You stay where you are.
- The map only shows rooms you have already entered. Rooms you haven't found
  yet stay hidden.
- Four items are hidden around the ship (a flashlight, a medkit, a keycard,
  and a repair kit). Rooms list their items as `Items here: ...`. Taking an
  item moves it into your inventory; dropping it leaves it in your current
  room until you pick it up again. Only the medkit does anything; the other
  items don't open doors or change your oxygen yet.
- **Hazards:** the **Reactor Core** and the **Cargo Hold** are dangerous.
  Every time you enter one (including going back in), you lose **2 health**
  and see a `!! HAZARD !!` warning. The move still costs the normal 1
  oxygen. Standing in a hazard room, looking around, or bumping into its
  walls doesn't hurt.
- **Medkit:** carry the medkit and type `use medkit` to restore 4 health
  (never above 10). It is used up. At full health the game tells you so and
  you keep it. You have to `take` it before you can use it.
- When your oxygen is 3 or less, the gauge shows `!! LOW OXYGEN !!`.
- **You win** if you enter the Escape Pod and still have oxygen left after
  that move.
- **You lose** if your oxygen reaches 0 before you escape. That includes
  arriving at the pod on your very last unit: you need air left over to launch.
- **You also lose** if your health reaches 0 ("You didn't survive."). If a
  move empties your health and your oxygen at the same time, you get the
  health ending.
- Pressing Ctrl-C or Ctrl-D ends the game cleanly.

**Hint:** the best route takes 6 moves and passes just one hazard, leaving
6 oxygen and 8 health. You can escape without ever healing.
Some parts of the ship are dead ends, so read the room descriptions carefully.

## How to run the tests

The automated tests use Python's built-in `unittest` library. From the
project root:

```bash
python3 -m unittest discover -s tests -v
```

Each test name starts with the requirement it checks (`test_R1_…` through
`test_R9_…`), and each docstring names the acceptance criterion
from `spec.md` Section 6 (for example `AC-R1.4`).

| File | What it checks |
|------|----------------|
| `tests/test_world.py` | The map: 11 rooms, two-way exits, everything reachable, shortest route is 6 moves, map grid, clues, starting items, hazard rooms |
| `tests/test_parser.py` | Command parsing: directions, shortcuts, `go`, `map`, `scan`, `take`/`get`/`drop`/`inventory`/`use`, case and spaces, bad input |
| `tests/test_game.py` | The rules: movement, oxygen cost, blocked moves, winning, losing, the 0-oxygen boundary, visited rooms, taking and dropping items, health, hazard damage, using the medkit |
| `tests/test_cli.py` | Terminal output and full scripted playthroughs, map and scan output, item and inventory messages, health gauge, hazard and death messages, `use` messages, Ctrl-C/Ctrl-D, and running `main.py` |

## Project structure

```
signal-lost/
├── main.py               # Entry point: python3 main.py
├── signal_lost/
│   ├── world.py          # Rooms and the ship map (data only)
│   ├── parser.py         # Turns typed text into a Command
│   ├── game.py           # Game state and rules (no printing or input)
│   └── cli.py            # Terminal input/output and text rendering
├── tests/                # unittest suite
├── docs/decisions/       # Architecture decision records
├── problem.md            # Problem statement and requirements R1-R9
└── spec.md               # Specification for Rounds 1-4
```

The game rules (`game.py`) are kept separate from terminal input and output
(`cli.py`). See [docs/decisions/0001.md](docs/decisions/0001.md) for why.
