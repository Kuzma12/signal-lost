

Instructions for future development sessions on this project.

## Project

A terminal text adventure for a CSC 299 final project, built in rounds.
Requirements live in `problem.md` (R1-R5) and the design in `spec.md`.
**Rounds 1-2 are complete:** navigation, room info, oxygen, win/loss (R1-R3),
the ship map (R4), and the room scanner (R5).

## Commands

```bash
python3 main.py                              # play the game
python3 -m unittest discover -s tests -v     # run all tests (must be 100% passing)
```

## Hard rules

- **Do not rewrite `problem.md` or `spec.md`.** They are the committed
  requirements and spec. Each round *extends* `spec.md` (new sections,
  acceptance criteria, test plan) without changing earlier rounds' content.
  If an earlier part seems wrong, raise it with the user first.
- **Standard library only.** No third-party packages and no `requirements.txt`.
  Python 3.10+.
- **Tests first.** Write or update `unittest` tests before implementing a
  feature. Every test name starts with the requirement it checks
  (`test_R1_…` through `test_R5_…`, and future `R6…`), and its
  docstring cites the acceptance-criterion id from the spec (e.g. `AC-R3.6`).
- **No failing or skipped tests** before a commit. Don't use `skip` decorators.
- **Small Git commits** with messages that explain what changed and why.
  **Never undo or amend a commit** (no `--amend`, `reset`, `revert`,
  rebase, or force-push); history must not be rewritten.
- **Don't push to GitHub** until the user has reviewed the work.
- **Stay in scope for the current round.** Don't add stub fields,
  placeholder commands, or unused hooks for future features (spec Section 9).
- Don't create round handoff files unless the user asks. At the start of a
  session, read the latest `handoff-round-N.md` if one exists.
- **New requirements (R6+) must be written by the user** and added to
  `problem.md` under a `## Round N requirements` heading. Never write them
  yourself. Commit and push the requirements before starting development,
  then extend `spec.md` for the round before writing tests.

## Architecture (keep it this way)

| Module | Role | Must not |
|--------|------|----------|
| `signal_lost/world.py` | `Room` dataclass (incl. `clue`), `build_ship()`, `MAP_GRID`, `START_ROOM`, `ESCAPE_ROOM`, `DIRECTIONS` | know about oxygen or I/O |
| `signal_lost/parser.py` | `parse(text) -> Command`, `is_go_attempt()` | change game state |
| `signal_lost/game.py` | `Game.handle(command) -> TurnResult`, `Status`, `Outcome`, oxygen constants | call `print()` or `input()` (a test enforces this) |
| `signal_lost/cli.py` | `run(input_fn, output_fn)`, all text rendering and messages, `render_map()`, `MAP_LABELS` | contain game rules |
| `main.py` | calls `run()` | contain logic |

- `Game.handle` dispatches with a `kind -> method` dict. To add a command,
  add one parser rule, one handler, one `Outcome` if needed, and one render
  branch in `cli.render_result`.
- All movement goes through `Game._move()`; put future lock and hazard checks there.
  `_move()` is also the only place that adds to `Game.visited`.
- The game is deterministic (no randomness) so whole playthroughs can be tested.
- Output is plain ASCII text, 50 columns wide, with no ANSI colors.

## Key rule decisions

- Oxygen starts at 12; only a **successful** move costs 1. `look`, `map`,
  `scan`, `help`, blocked moves, and unknown commands are free.
- Arriving at the Escape Pod with **0** oxygen after the move is a **loss**
  (spec 4.3). Every route is an even number of moves, so move 12 into the pod loses.
- See `docs/decisions/` for architecture decision records (Y-statement format).
  Add a new numbered record (next is `0003.md`) for each significant decision.
- Changing the ship layout means updating the room table and `MAP_GRID`
  (`world.py`) and `MAP_LABELS` (`cli.py`, plus its copy in `test_cli.py`)
  together. Map cells are 11 chars and labels at most 8, so 4 columns = 50.

## Future rounds (not implemented yet)

Inventory, puzzles/locked doors, hazards, save/load. See spec Section 9 for
where each one plugs in.
