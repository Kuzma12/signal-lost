# Handoff: end of Round 2

For a fresh session starting the next round of *Signal Lost*. Standing rules
(how to work on this repo) are in `CLAUDE.md`; read that first. This file
covers **where things stand** and **what is still open**. The Round 1
handoff (`handoff-round-1.md`) is still accurate for Round 1 details.

## 1. Current state

- **Round 2 is complete and committed** on `main` (last commit `8b55759`).
- **Push status:** At the time of this handoff, the Round 2 requirements were already pushed, and 8 implementation commits were waiting for review and push..** `main` is 8 commits ahead of `origin/main`. Only the
  Round 2 requirements commit (`55cf321`) is on GitHub, as the rule requires.
  The user must review the Round 2 work before anything else is pushed.
- R4 (Ship Map) and R5 (Room Scanner) from `problem.md` are implemented as


| File | Tests | of which R4 / R5 |
|------|-------|------------------|
| `tests/test_world.py` | 20 | 3 / 4 |
| `tests/test_parser.py` | 18 | 2 / 2 |
| `tests/test_game.py` | 45 | 12 / 5 |
| `tests/test_cli.py` | 52 | 13 / 6 |

What the player can do now, beyond Round 1:

- `map` / `m`: an ASCII grid of visited rooms, `*` on the current room, plus
  `You are in: <room>` and `Rooms visited: N of 11`. Free.
- `scan` / `sc`: `[ SCAN: <ROOM NAME> ]` followed by that room's clue,
  wrapped to 50 columns. Free, repeatable, always the same clue.
- `help` lists both. The README command table and rules were updated.

Round 2 commits, in order: requirements (`55cf321`), spec (`c863b34`),
world data (`89c87b0`), parser (`1b7e6f5`), game (`99b4e38`), CLI
(`8827e86`), spec map-example fix (`848d415`), README (`c1c6227`),
ADR 0002 (`8b55759`). Each step wrote its tests first.

## 2. How to run

```bash
python3 main.py                              # play
python3 -m unittest discover -s tests -v     # all tests, verbose
```

Smoke test that exercises both new commands and wins:

```bash
printf 'm\nn\ne\ns\ns\ne\nm\nsc\ne\n' | python3 main.py
```

## 3. Decisions made this round, and why

| Decision | Why | Where recorded |
|----------|-----|----------------|
| `Game` keeps a `visited` set (starts with `cryo_bay`), updated **only** in `Game._move()` | One place where "visiting" happens, so future lock/hazard checks in `_move()` can't get out of step with the map | ADR `0002.md`, spec 3.7 |
| `TurnResult.visited` is a `frozenset` snapshot | The CLI can't mutate game state through it, and old results stay correct | ADR `0002.md` |
| Fixed `MAP_GRID` (row, col) positions in `world.py`, with a test that every exit joins grid neighbors | A map that looks like the ship and is checked against the real exits; simpler than computing layout at run time | ADR `0002.md`, spec 3.7 |
| 11-char cells, 2-char gaps, 8-char labels (`MAP_LABELS` in `cli.py`) | 4 x 11 + 3 x 2 = exactly 50 columns | spec 3.7, ADR `0002.md` |
| Unvisited rooms and lines into them are not drawn; no `?` hints | R4 says unexplored rooms "should stay hidden" | spec 3.7, 10 |
| A line is drawn only if both rooms are visited **and** an exit joins them | Neighbors with a sealed bulkhead must not look connected | AC-R4.5 |
| Each `Room` has a `clue` field; clues are unique, differ from the description, and are deterministic | R5 says "each room should have its own clue"; no randomness (spec 1.3) | spec 3.8, AC-R5.2 |
| Clues hint at the route or warn about dead ends; the Escape Pod has a clue too | Makes scan a useful free planning tool; every room meets the "own clue" rule | spec 3.8 |
| `map` and `scan` cost no oxygen and change no state | Directly from R4/R5 | AC-R4.6, AC-R5.4 |
| Spec was **extended** (new sections, ACs, test plan) rather than rewritten; title is now "Rounds 1-2" | `CLAUDE.md` forbids rewriting `spec.md` but asks for it to be updated each round | commit `c863b34` |

## 4. Unresolved / open questions

1. **No requirements past R5.** The next round's requirements (R6+) must be
   written by the user, added to `problem.md` under a `## Round 3
   requirements` heading, committed, and pushed **before** development
   starts. Don't invent them.
2. **GitHub:** Make sure all Round 2 commits and the handoff are pushed before starting Round 3.** Wait for the user's review. Don't push.
3. **Some output lines are still wider than 50 columns** (carried over from
   Round 1, still unfixed; checked with the smoke test):
   - `Move with north, south, east, west (or n, s, e, w).` (51, intro)
   - `Unknown command: '<text>'. Type 'help' for a list of commands.` (60+)
   - `The hatch seals behind you and the pod blasts free of the dying ship.`
     (69, win message, wording quoted in spec 4.4)
   - `You close your eyes and let the ship drift. Transmission ended.` (63, quit)

   The new map and scan output does fit, and is tested for it. Fixing the
   rest means rewording text the spec quotes, so ask the user first.
4. **The oxygen boundary rule still has no ADR.** `0002.md` was used for
   the map decision, so if the user wants this one recorded it would be
   `0003.md`. Spec 4.3 still carries its "Review note" calling it a
   judgment call. Ask before writing it.
5. **Section 9 and 10 headings in `spec.md` still say "Round 1"**
   ("NOT implemented now", "Out of Scope for Round 1"). Section 10 got a
   Round 2 sub-heading appended. The next round should append its own
   sub-heading the same way rather than retitling the old ones.
6. **`CLAUDE.md` had a garbled line** about recording requirements. It
   was cleaned up in this handoff session (uncommitted, pending the user's
   review), so check it reads the way the user wants.

## 5. Things the next session should know

- **Save/load must include `visited`** (as a list of room ids) along with
  `room_id`, `oxygen`, and `status`. ADR 0002 notes this.
- **Changing the ship layout** (adding rooms, moving exits) now touches
  three things: the room table in `world.py`, `MAP_GRID` in `world.py`,
  and `MAP_LABELS` in `cli.py`. Tests fail if the grid disagrees with the
  exits or a map line goes past 50 columns. There is no direct test of
  the 8-character label limit, and `test_cli.py` keeps its own copy of
  the labels, so update both. The grid has spare cells at
  (0,0), (0,3), (1,3), (2,3), (3,0). A room outside the 4x4 grid would
  break the 50-column math.
- **Locked doors and the map:** spec 3.7 draws a line wherever an exit
  joins two visited rooms. If an exit becomes locked, decide with the user
  whether the map shows it before it is unlocked.
- **Hazards and visiting:** if a hazard can stop the player entering a
  room, put that check before the `visited.add` in `_move()`.
- **Clue text is a hint system.** If the map or route changes, re-read the
  clues in `world.py`; several point at specific directions
  (e.g. Airlock Junction: "docking beacon pings from the east door").
- **Balance numbers unchanged:** shortest win is still 6 moves
  (`n e s s e e`), leaving 6 oxygen; route lengths are all even. See the
  Round 1 handoff on why that matters for tests.
- **Where to add text:** player-facing strings are constants at the top of
  `cli.py`; `render_result` has one branch per `Outcome` (now including
  `MAPPED` and `SCANNED`). The map is drawn by `cli.render_map()`.
- Commit pattern held this round: requirements, spec, then tests-first
  commits for world, parser, game, CLI, then README and ADR. Keep it.
