# Signal Lost

*You wake up in a cryo pod. Warning lights flash red. The ship's AI is silent
and the hull is breached. Your suit has twelve units of oxygen left.
Somewhere aboard is an escape pod. Find it before you run out of air.*

**Signal Lost** is a single-player text adventure that runs in the terminal.
You move through a damaged spaceship by typing compass directions. Every
move to another room uses one unit of oxygen. Reach the Escape Pod before
your oxygen runs out to win.

This is a CSC 299 final project, built in rounds. **Round 1** (this version)
covers room navigation, room information, and oxygen with win/loss. Inventory,
puzzles, hazards, and save/load are planned for later rounds.

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

You start in the **Cryo Bay** with **12 oxygen**. Each time you enter a room,
the game shows its name, a short description, the exits you can take, and
your oxygen gauge:

```
==================================================
  CENTRAL CORRIDOR
==================================================
The ship's main artery. Emergency strip-lights
pulse red along a passage that branches in every
direction.

Exits: north, east, south, west
[ OXYGEN: 10/12 ]
```

### Commands

| Command | Shortcuts | What it does | Oxygen cost |
|---------|-----------|--------------|-------------|
| `north`, `south`, `east`, `west` | `n`, `s`, `e`, `w`, `go north` | Move to the next room | 1 |
| `look` | `l` | Describe the current room again | 0 |
| `help` | `h`, `?` | List the commands | 0 |
| `quit` | `q`, `exit` | Give up and end the game | 0 |

Commands ignore upper/lower case and extra spaces, so `  GO N ` works.

### Rules

- A successful move to another room costs **1 oxygen**.
- Bumping into a wall (a direction with no exit), typing an unknown command,
  `look`, and `help` are all **free**. You stay where you are.
- When your oxygen is 3 or less, the gauge shows `!! LOW OXYGEN !!`.
- **You win** if you enter the Escape Pod and still have oxygen left after
  that move.
- **You lose** if your oxygen reaches 0 before you escape. That includes
  arriving at the pod on your very last unit: you need air left over to launch.
- Pressing Ctrl-C or Ctrl-D ends the game cleanly.

**Hint:** the best route takes 6 moves, leaving plenty of oxygen to spare.
Some parts of the ship are dead ends, so read the room descriptions carefully.

## How to run the tests

The automated tests use Python's built-in `unittest` library. From the
project root:

```bash
python3 -m unittest discover -s tests -v
```

Each test name starts with the requirement it checks (`test_R1_…`,
`test_R2_…`, `test_R3_…`), and each docstring names the acceptance criterion
from `spec.md` Section 6 (for example `AC-R1.4`).

| File | What it checks |
|------|----------------|
| `tests/test_world.py` | The map: 11 rooms, two-way exits, everything reachable, shortest route is 6 moves |
| `tests/test_parser.py` | Command parsing: directions, shortcuts, `go`, case and spaces, bad input |
| `tests/test_game.py` | The rules: movement, oxygen cost, blocked moves, winning, losing, the 0-oxygen boundary |
| `tests/test_cli.py` | Terminal output and full scripted playthroughs, Ctrl-C/Ctrl-D, and running `main.py` |

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
├── problem.md            # Problem statement and requirements R1-R3
└── spec.md               # Round 1 specification
```

The game rules (`game.py`) are kept separate from terminal input and output
(`cli.py`). See [docs/decisions/0001.md](docs/decisions/0001.md) for why.
