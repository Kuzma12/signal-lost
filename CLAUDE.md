Instructions for future development sessions on this project.

## Project

A terminal text adventure for a CSC 299 final project, built in rounds.
Requirements live in `problem.md` (R1-R10) and the design in `spec.md`.
**Rounds 1-5 are complete and requirements R1-R10 work:** navigation, room
info, oxygen, win/loss (R1-R3), the ship map (R4), the room scanner (R5),
collecting items (R6), the inventory with `drop` (R7), health and hazard
rooms (R8), healing with `use medkit` (R9), and the locked Escape Pod
opened with `use keycard` (R10). Round 5 also **revised R3**: winning now
requires unlocking the pod door first (spec Section 4.6 keeps the original
R3 wording for history).

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
  (`test_R1_…` through `test_R10_…`, and future `R11…`), and its
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
- **Revised requirements:** when the user revises an earlier requirement
  (as Round 5 did with R3), keep the original spec text and acceptance
  criteria word for word and add "(Round N)" notes pointing to the new
  criteria. Change an existing test only when the revision changes its
  expected result, and explain each change in the commit message.
- **New requirements (R6+) must be written by the user** and added to
  `problem.md` under a `## Round N requirements` heading. Never write them
  yourself. Commit and push the requirements before starting development,
  then extend `spec.md` for the round before writing tests.

## Architecture (keep it this way)

| Module | Role | Must not |
|--------|------|----------|
| `signal_lost/world.py` | `Room` dataclass (incl. `clue`, starting `items`, and `hazard` flag), `build_ship()`, `STARTING_ITEMS`, `HAZARD_ROOMS`, `MAP_GRID`, `START_ROOM`, `ESCAPE_ROOM`, `KEYCARD_READER`, `DIRECTIONS` | know about oxygen, health, locks, or I/O |
| `signal_lost/parser.py` | `parse(text) -> Command`, `is_go_attempt()` | change game state |
| `signal_lost/game.py` | `Game.handle(command) -> TurnResult`, `Status`, `Outcome`, oxygen and health constants (`STARTING_HEALTH`, `HAZARD_DAMAGE`, `MEDKIT`, `MEDKIT_HEALING`, `KEYCARD`), live state (`health`, `room_items`, `inventory`, `pod_locked`) | call `print()` or `input()` (a test enforces this) |
| `signal_lost/cli.py` | `run(input_fn, output_fn)`, all text rendering and messages, `render_room()`, `render_map()`, `render_inventory()`, `render_hazard()`, `MAP_LABELS`, `HAZARD_MESSAGES`, lock messages (`LOCKED_MESSAGE`, `UNLOCKED_MESSAGE`, `ALREADY_UNLOCKED_MESSAGE`, `WRONG_PLACE_MESSAGE`) | contain game rules |
| `main.py` | calls `run()` | contain logic |

- `Game.handle` dispatches with a `kind -> method` dict. To add a command,
  add one parser rule, one handler, one `Outcome` if needed, and one render
  branch in `cli.render_result`.
- All movement goes through `Game._move()`. It is the only place that
  adds to `Game.visited`, the only place hazard damage happens, and where
  the pod lock is checked. Turn order: exit exists? (`BLOCKED`) → pod
  locked? (`LOCKED`, nothing changes) → move → visited → oxygen −1 →
  hazard damage → health 0? (`DIED`) → pod with oxygen > 0? (`WON`) →
  oxygen 0? (`LOST`). Any new lock check must also come **before** the room
  changes. See `docs/decisions/0005.md`.
- `Room` is frozen and `Room.items` is only the **starting** placement.
  Items that move during play live in `Game.room_items` and
  `Game.inventory`; every item is always in exactly one of them, except a
  used medkit, which is in neither (tests check). The keycard is never used
  up. See `docs/decisions/0003.md` and `0004.md`.
- `render_room(..., health=None)` only draws the health line when `health`
  is passed. Every real display passes it (tests check); a new caller must too.
- The game is deterministic (no randomness) so whole playthroughs can be tested.
- Output is plain ASCII text, 50 columns wide, with no ANSI colors.

## Key rule decisions

- Oxygen starts at 12; only a **successful** move costs 1. `look`, `map`,
  `scan`, `take`, `drop`, `inventory`, `use`, `help`, blocked moves, the
  locked pod door, and unknown commands are free.
- Arriving at the Escape Pod with **0** oxygen after the move is a **loss**
  (spec 4.3). Every route is an even number of moves, so move 12 into the pod loses.
- Health starts at 10 (also the max). Every successful move into the
  Reactor Core or Cargo Hold costs 2 health (plus the usual 1 oxygen).
  Health 0 is a loss with outcome `DIED`. Health is checked **before** the
  win and oxygen checks, so emptying both on one move gives the health
  ending (user's choice). With these numbers health can only reach 0 on
  move 12.
- `use medkit` heals up to 4 (capped at 10) and removes the medkit; at full
  health it is kept. The flashlight and repair kit still do nothing
  (`You can't use the X.`).
- **Locked Escape Pod (R10):** the door from the Airlock Junction
  (`KEYCARD_READER`) into the pod starts locked (`Game.pod_locked`). A move
  into it returns `LOCKED` and costs nothing. `use` checks carried? first;
  then for the keycard: not at the reader → `WRONG_PLACE`, already open →
  `ALREADY_UNLOCKED`, else unlock (`UNLOCKED`). The keycard is kept and the
  door **stays unlocked** even if the keycard is dropped (user's choice).
  The Airlock `Exits:` line is unchanged.
- **Revised R3:** you win only by entering the **unlocked** pod with
  oxygen > 0 (and health > 0). The win check itself is unchanged; a locked
  pod simply can't be entered. The shortest win is now **8 moves** (detour
  to the Bridge for the keycard) and ends with **4 oxygen, 8 health**. Every
  winning route takes 8 or 10 moves. The old 6-move routes stop at the
  locked door. Winning test scripts must include `take keycard` and
  `use keycard` (see the `KEYCARD_*` constants in the tests).
- **Scanner clues must not steer the player away from the keycard**
  (AC-R5.7). In Round 5 the Central Corridor and Bridge clues were
  corrected to point toward the keycard on the Bridge, without saying
  where or how it is used. Moving the keycard or changing those rooms
  means revisiting the clues and `Round5ClueTests` in `test_world.py`.
- See `docs/decisions/` for architecture decision records (Y-statement format).
  Add a new numbered record (next is `0006.md`) for each significant decision.
- Changing the ship layout means updating the room table and `MAP_GRID`
  (`world.py`) and `MAP_LABELS` (`cli.py`, plus its copy in `test_cli.py`)
  together. Map cells are 11 chars and labels at most 8, so 4 columns = 50.
  Changing hazard rooms means updating `HAZARD_ROOMS` (`world.py`) and
  `HAZARD_MESSAGES` (`cli.py`) together (a test checks they match).
- Item names are lower-case and unique and must be typed in full (case and
  extra spaces ignored). Changing items means updating `STARTING_ITEMS`
  (`world.py`) and the tests that hard-code the four names. Moving the
  keycard or changing exits changes the 8-move win and many hard-coded
  oxygen/health numbers; re-run an exhaustive route search.

## Future rounds (not implemented yet)

Save/load (and any further puzzles or locked doors) are not built. See spec
Section 9 for where they plug in. Save/load must include `visited`,
`room_items`, `inventory`, `health`, and `pod_locked` as well as `room_id`,
`oxygen`, and `status`. The Round 5 lock is a single flag for the pod door
only; don't generalize it unless a requirement asks.
