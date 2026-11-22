# Handoff: end of Round 6 (project complete)

For anyone picking up *Signal Lost* after Round 6, or preparing the final
portfolio. Standing rules for working on this repo are in `CLAUDE.md`;
read that first. The Round 1-5 handoffs are still accurate for their own
rounds, except where Section 6 below (the revised R3) says otherwise.

## 1. Current state

- **All six rounds are complete. Requirements R1-R12 are implemented and
  tested.** Round 5 also revised R3 (Section 6).
- **390 tests, all passing, none skipped** (317 from Rounds 1-5 plus 73
  new in Round 6).
- **Push status:** `origin/main` ends at `5bfa777` (the Round 6
  requirements). The **6 Round 6 commits after it are local only**
  (`main` is 6 ahead of `origin/main`), waiting for the user's review.
  This handoff and the `CLAUDE.md` update are **uncommitted**, also
  waiting for review.
- The working tree has no save file: tests only write saves into
  temporary folders, and `.gitignore` ignores `signal_lost_save.json`
  and `signal_lost_save.json.tmp`.

| File | Tests | New in Round 6 |
|------|-------|----------------|
| `tests/test_world.py` | 39 | 0 |
| `tests/test_parser.py` | 35 | 4 |
| `tests/test_game.py` | 161 | 34 |
| `tests/test_cli.py` | 138 | 18 |
| `tests/test_savefile.py` | 17 | 17 (new file) |
| **Total** | **390** | **73** |

Round 6 commits, in order:

| Commit | What |
|--------|------|
| `43c7796` | Spec: Section 3.12, AC-R11.1-11.7, AC-R12.1-12.9, Round 6 test plan and out-of-scope list |
| `ae3d9ad` | `signal_lost/savefile.py`, `tests/test_savefile.py`, `.gitignore` entries |
| `ea9a1ef` | Parser `save`/`load`; `Game` save, load, and save-file checks |
| `f83da0c` | CLI messages, help lines, `run(save_path=…)`; fix to the spec 7.2 example (8 oxygen, not 9) |
| `ded5dba` | README |
| `a21ed6f` | ADR 0006 |

Each code commit wrote its tests first and saw them fail before the code
was written. **Known slip:** the `ea9a1ef` message says 38 game tests and
44 damaged-save cases; the real numbers are 34 and 45. History is never
amended, so the correction is recorded in the `f83da0c` message.

## 2. Requirements R1-R12

Full text is in `problem.md`; design is in `spec.md`; acceptance
criteria (AC ids) are in `spec.md` Section 6.

| Req | Round | Summary | Spec |
|-----|-------|---------|------|
| R1 Room Navigation | 1 | Move with `north`/`south`/`east`/`west` (`n`/`s`/`e`/`w`, `go north`). A blocked direction is refused and costs no oxygen | 3.4, 5 |
| R2 Room Information | 1 | Every room entered shows its name, description, and exits | 3.6 |
| R3 Oxygen and Escaping | 1, **revised in 5** | Start with 12 oxygen, 1 per successful move. Win by reaching the escape pod with oxygen left; lose at 0. See Section 6 | 4.1-4.6 |
| R4 Ship Map | 2 | `map` shows visited rooms, marks the current one, and hides the rest. Free | 3.7 |
| R5 Room Scanner | 2 | `scan` gives the current room's clue. Free and repeatable | 3.8 |
| R6 Collecting Items | 3 | Rooms list items; `take <item>` moves one to the inventory. Free | 3.9 |
| R7 Inventory System | 3 | `inventory` lists carried items (or says it's empty); `drop <item>` leaves one in the room. Free | 3.9 |
| R8 Health and Hazards | 4 | 10 health. Entering the Reactor Core or Cargo Hold costs 2 health each time; 0 health is a loss. Winnable without healing | 3.10 |
| R9 Medkit Healing | 4 | `use medkit` restores 4 health (max 10) and is used up; kept at full health | 3.10 |
| R10 Keycard and Locked Escape Pod | 5 | The pod starts locked. Take the keycard from the Bridge; `use keycard` at the Airlock Junction unlocks it for good. Free, keycard kept | 3.11 |
| R11 Saving the Game | 6 | `save` writes the whole game state to a JSON file. Free, confirmed with a message | 3.12 |
| R12 Loading the Game | 6 | `load` restores the save and shows the room and gauges. A missing or damaged save is reported and the current game is kept. Free | 3.12 |

## 3. How to run

```bash
python3 main.py                              # play
python3 -m unittest discover -s tests -v     # all 390 tests, verbose
python3 -m unittest discover -s tests        # quiet
python3 -m unittest tests.test_savefile -v   # one file
```

Python 3.10+, standard library only, nothing to install.

Smoke tests (run them from a scratch folder if you don't want a save file
in the project; `.gitignore` covers it either way):

```bash
# Shortest win: 8 moves, keycard from the Bridge, ends with 4 oxygen, 8 health
printf 'n\ne\nn\ntake keycard\ns\ns\ns\ne\nuse keycard\ne\n' | python3 main.py

# Locked door: the old 6-move route stops at the Airlock Junction
printf 'n\ne\ns\ns\ne\ne\nlook\nq\n' | python3 main.py

# Save, wander, load (back in the Corridor with 8 oxygen), then win with 4
printf 'n\ne\nn\ntake keycard\ns\nsave\ns\ns\nload\ns\ns\ne\nuse keycard\ne\n' | python3 main.py

# Save in one run, load and win in the next
printf 'n\ne\nn\ntake keycard\ns\ns\ns\ne\nuse keycard\nsave\nq\n' | python3 main.py
printf 'load\ne\n' | python3 main.py

# Damaged save: reported, current game unchanged
echo '{"oxygen": 99' > signal_lost_save.json
printf 'load\nlook\nq\n' | python3 main.py
rm signal_lost_save.json

# No save
printf 'load\nq\n' | python3 main.py

# Health ending
printf 'n\ne\ns\ne\nw\ne\nw\ne\nw\ne\nw\ne\n' | python3 main.py
```

## 4. Save and load (Round 6)

**Commands.** `save` and `load`, single words, case and spaces ignored.
There are no one-letter aliases (`s` is south, `l` is look). `save game` /
`load 2` are unknown commands. Both are free (no oxygen or health), and
both are ignored after the game ends, as every command is.

**File.** `signal_lost_save.json` in the current working directory
(`savefile.SAVE_FILE`). One slot, overwritten without asking. Written as
2-space-indented UTF-8 JSON to `signal_lost_save.json.tmp`, then moved into
place with `os.replace`, so a failed save never damages the last one.

**Format** (`Game.save_data()`):

```json
{"version": 1, "room": "...", "oxygen": 10, "health": 10,
 "status": "playing", "visited": ["...sorted..."],
 "room_items": {"<every room id>": ["..."]},
 "inventory": ["...pickup order..."], "pod_locked": true}
```

A used medkit is simply missing. Room data (names, exits, hazards,
starting items) comes from `build_ship()` and is never saved.

**Messages.**

| Outcome | Output |
|---------|--------|
| `SAVED` | `Game saved.` |
| `SAVE_FAILED` | `Save failed: the file could not be written.` |
| `LOADED` | `Game loaded.`, a blank line, then the room display (items, exits, oxygen and health gauges) |
| `NO_SAVE` | `There is no saved game to load.` |
| `DAMAGED_SAVE` | `The save file is damaged and can't be loaded.` / `Your current game is unchanged.` |

**Damaged-file checks** (`Game._check_save`, spec 3.12). A file is damaged
unless it is readable UTF-8 JSON with an object at the top, and has exactly
the nine keys, `version` 1, `status` `"playing"`, integer oxygen 1-12 and
health 1-10 (no booleans or decimals), a known room that isn't the pod,
visited rooms with no repeats that include `cryo_bay` and the current room
but not the pod, every room id in `room_items` with string lists and an
empty pod, a string-list inventory, every item exactly once (only the
medkit may be missing), and a boolean `pod_locked`. **All checks run before
anything changes**, then the state is replaced in one assignment, so a
load is all-or-nothing.

**Where the code is.**

| Module | Round 6 part |
|--------|--------------|
| `savefile.py` | `SAVE_FILE`, `write()`, `read()`, `NoSaveFile`, `DamagedSave`. Files and JSON only; imports nothing from the game |
| `parser.py` | `"save"` and `"load"` in `_COMMAND_ALIASES` |
| `game.py` | `SAVE_VERSION`, `Game(save_path=SAVE_FILE)`, `save_data()`, `_check_save()`, `_save`, `_load`, five outcomes |
| `cli.py` | Five message constants and branches, two help lines, `run(…, save_path=SAVE_FILE)` |

**Decisions made with the user before coding:** current-folder save file,
one overwritten slot, room display on load, full validation. Everything
else (module split, atomic write, version field, sorted `visited`, exact
message wording, no aliases) was decided during implementation and
recorded in ADR 0006.

## 5. Important design decisions and ADRs

All ADRs are in `docs/decisions/`, in Y-statement format.

| ADR | Round | Decision |
|-----|-------|----------|
| 0001 | 1 | Keep game rules (`game.py`) separate from terminal I/O (`cli.py`). `Game.handle(command) -> TurnResult`; a test forbids `print`/`input` in `game.py` |
| 0002 | 2 | Track visited rooms on `Game`; draw the map from fixed `MAP_GRID` positions |
| 0003 | 3 | Starting items live on the frozen `Room`; items that move during play live in `Game.room_items` and `Game.inventory` |
| 0004 | 4 | Hazard damage happens inside `_move()`; health is checked before the win and oxygen checks |
| 0005 | 5 | One `pod_locked` flag, checked in `_move()` before the room changes; the win check is unchanged |
| 0006 | 6 | Save/load as checked, versioned JSON through a file-only `savefile` module; all-or-nothing load; atomic write; `save_path` for tests |

Other standing decisions (details in `CLAUDE.md` and the spec):

- **Deterministic game**, no randomness, so whole playthroughs are tested.
- **Turn order in `_move()`:** exit exists? (`BLOCKED`) → pod locked?
  (`LOCKED`, nothing changes) → move → visited → oxygen −1 → hazard damage
  → health 0? (`DIED`) → pod with oxygen > 0? (`WON`) → oxygen 0? (`LOST`).
- **Oxygen boundary:** arriving at the pod with 0 oxygen after the move
  is a loss (spec 4.3). Every route is an even number of moves.
- **Only successful moves cost anything.** Everything else is free.
- **Output** is plain ASCII, 50 columns, no colors.
- **Command dispatch** through a `kind -> method` dict; adding a command
  means one parser rule, one handler, outcomes, and render branches.

## 6. The Round 5 revision to R3

**Original R3 (Rounds 1-4):** reach the escape pod while you still have
oxygen and you win. "Still have oxygen" means oxygen > 0 after paying for
the move.

**Revised R3 (Round 5, `problem.md` "R3: Revised Escape Requirement"):**
the pod door must also be unlocked with the keycard first. Reaching the
pod without unlocking it no longer counts as a win. Oxygen and health must
still remain, and the original oxygen rules still apply.

How it was handled:

- The lock is checked in `_move()` before the room changes, so a move into
  the locked pod returns `LOCKED` and costs nothing. The win check itself
  is unchanged: being in the pod now implies it was unlocked.
- The shortest win went from **6 moves (6 oxygen left)** to **8 moves
  (4 oxygen, 8 health)**. Every winning route takes 8 or 10 moves.
- The original R3 text and AC-R3.4 / AC-R3.8 are kept word for word in the
  spec (4.6, Section 6), with "(Round 5)" notes pointing to AC-R3.9-3.12.
  AC-R6.6, AC-R8.8 and AC-R9.7 got the same kind of note.
- 28 existing tests (14 in `test_game.py`, 14 in `test_cli.py`) that
  walked straight into the pod were given the keycard detour, in commit
  `0f7edb2`. The commit message explains each change. The old route
  constants are kept for the "old routes no longer win" tests.
- Two scanner clues that steered players away from the Bridge were
  corrected (`5c4913c`, AC-R5.7).

Round 6 changed no rule and no existing test expectation.

## 7. Remaining issues and limitations

1. **Wide Round 1 lines.** The intro `Move with…` line (51 columns),
   `Unknown command: '…'. Type 'help'…`, the win line `The hatch seals…`
   (69), and the quit message (63) are over 50 columns. The width tests
   skip them. Rewording needs the user's OK.
2. **No ADR for the oxygen boundary rule** (spec 4.3 review note). Next
   free ADR number: `0007.md`.
3. **Help footer** says "Everything else is free." That's true for oxygen
   and health, but hazard moves cost health. Unchanged since Round 4.
4. **Health can only reach 0 on move 12.** With these numbers the health
   ending only happens together with the last unit of oxygen (Round 4
   analysis). Health mostly limits wandering.
5. **The lock is hard-wired to the pod door.** A second locked door would
   need a small refactor (for example, a set of locked room ids).
6. **Spec history text still says 6 moves** (1.2, 3.3, AC-R3.8) with
   Round 5 notes. `test_world.py`'s 6-move tests are map-only facts and
   are still true. Don't "fix" them.
7. **Save/load limits (by design, spec Section 10 "Round 6"):**
   - One slot, no confirmation before overwriting, no auto-save, no
     loading at start-up, no deleting the save from inside the game.
   - The save goes to whatever folder the game was started from, so
     starting from another folder means "no save".
   - The checks reject only impossible states. A hand-edited file that
     describes a reachable state (for example, an earlier point with more
     oxygen) still loads, which R12 allows.
   - A file with a different `version` is reported as damaged. A future
     round that adds state must bump the version and decide whether old
     saves still load.
   - `game.py` now reaches the file system through `savefile`. It still
     never prints or reads input.
8. **README rules bullet** about free actions was reflowed in Round 6,
   which fixed the uneven wrap mentioned in the Round 5 handoff.
9. **Not on GitHub yet:** the 6 Round 6 commits, this handoff, and the
   `CLAUDE.md` update.

## 8. For the final portfolio

**Artifacts to point to:**

| What | Where |
|------|-------|
| Problem statement and all requirements as the user wrote them, by round | `problem.md` |
| Specification, extended each round without rewriting earlier rounds | `spec.md` (Sections 3.7-3.12 per feature, Section 6 acceptance criteria, Section 7 test plan, Section 10 scope per round) |
| Architecture decisions | `docs/decisions/0001.md`-`0006.md` |
| Round-by-round handoffs | `handoff-round-1.md` … `handoff-round-6.md` |
| Player documentation | `README.md` |
| Instructions for AI-assisted sessions | `CLAUDE.md` |
| Test suite (390 tests, requirement-named) | `tests/` |
| Development history | `git log` (58 commits, never amended or rewritten) |

**Process points worth showing:**

- **Requirements first, then spec, then tests, then code.** Each round
  committed (and pushed) the user's requirements, extended the spec, then
  wrote failing tests before the code, one layer per commit.
- **Traceability.** Every test name starts with its requirement
  (`test_R11_…`) and its docstring cites an acceptance-criterion id
  (`AC-R11.6`). Spec Section 7.2 maps criteria to tests.
- **Handling a revised requirement** (Round 5, R3): original text kept
  word for word, new criteria added, the changed tests listed and
  explained in a commit message.
- **Clarifying questions before building** each round (for example, the
  four Round 6 questions in Section 4), with the answers recorded in the
  spec and the ADRs.
- **Honest history:** mistakes are corrected with new commits, never
  rewritten (for example, the `ea9a1ef` test-count slip corrected in
  `f83da0c`, and the Round 5 scanner-clue fix in `5c4913c`).
- **Architecture held up across six rounds.** The rules/I-O split from
  ADR 0001, the `kind -> method` dispatch, and the single `_move()` were
  never rewritten. Each feature plugged in where spec Section 9 said it
  would.

**Before submitting:**

1. Review and commit `handoff-round-6.md` and `CLAUDE.md`.
2. Push `main` to GitHub once the user has reviewed it.
3. Run `python3 -m unittest discover -s tests` on a clean clone to confirm
   390 passing.
4. Optionally record a short playthrough showing the keycard win, the
   locked door, a hazard, and save → load.
