# Handoff: end of Round 4

For a fresh session starting the next round of *Signal Lost*. Standing rules
(how to work on this repo) are in `CLAUDE.md`; read that first. This file
covers **where things stand** and **what is still open**. The Round 1-3
handoffs are still accurate for those rounds' details.

## 1. Current state

- **Round 4 is complete and committed** on `main` (last commit `6515570`).
- **Push status:** the Round 4 requirements commit (`b554037`) is on GitHub.
  The **8 commits after it are local only** (`main` is 8 ahead of
  `origin/main`). The user must review them before anything is pushed. This
  handoff and the `CLAUDE.md` update are **uncommitted**, waiting for the
  user's review.
- R8 (Health and Hazards) and R9 (Medkit Healing) are implemented and
  tested. **264 tests, all passing, none skipped** (201 from Rounds 1-3 plus
  63 new). No Round 1-3 test body was changed; only the "(R1-R7)" note in
  each test module's docstring became "(R1-R9)".

| File | Tests | New in Round 4 | Names starting `R8_` / `R9_` |
|------|-------|----------------|------------------------------|
| `tests/test_world.py` | 31 | 6 | 6 / 0 |
| `tests/test_parser.py` | 30 | 3 | 0 / 3 |
| `tests/test_game.py` | 101 | 32 | 17 / 15 |
| `tests/test_cli.py` | 102 | 22 | 14 / 8 |

(`test_R8_R9_…` is counted under R8.)

What the player can do now, beyond Rounds 1-3:

- **Health:** starts at 10 (also the max). Every room display shows
  `[ HEALTH: h/10 ]` on its own line under the oxygen gauge.
- **Hazards:** every successful move into the **Reactor Core** or the
  **Cargo Hold** (including re-entry) costs 2 health plus the normal 1
  oxygen, and prints a blank line, `!! HAZARD: -2 HEALTH !!`, and a
  room-specific line after the room display. Blocked moves and other
  commands never cost health.
- **Dying:** health 0 → status `LOST`, outcome `DIED`, ending
  `>>> CRITICAL INJURIES <<<` / `Your suit alarms fade as everything goes
  dark...` / `You didn't survive.` / `*** GAME OVER: YOU LOST ***`.
- **`use <item>`:** `use medkit` (carried, health < 10) heals up to 4,
  capped at 10, and removes the medkit. Free. Help lists it.

Round 4 commits, in order: requirements (`b554037`, pushed), spec
(`ca547cc`), world hazards (`c5c49e4`), parser `use` (`480f171`), game
rules (`c5d3750`), CLI (`4c30c81`), README (`fca22f3`), ADR 0004
(`6d90a26`), spec overview correction (`6515570`). Each code step wrote
its tests first and saw them fail; tests and code were committed together.

## 2. How to run

```bash
python3 main.py                              # play
python3 -m unittest discover -s tests -v     # all tests, verbose
```

Smoke tests:

```bash
# Shortest win: one hazard, ends with 6 oxygen and 8 health
printf 'n\ne\ns\ns\ne\ne\n' | python3 main.py

# Health ending: Reactor Core five times; health and oxygen both hit 0
printf 'n\ne\ns\ne\nw\ne\nw\ne\nw\ne\nw\ne\n' | python3 main.py

# Medkit: full-health try keeps it, then heals 4 after two reactor entries
printf 'n\ntake medkit\nuse medkit\ne\ns\ne\nw\ne\nuse medkit\ni\nq\n' | python3 main.py
```

## 3. Decisions made this round, and why

The user chose the first four (asked before coding); the rest were made
during implementation and reported to the user.

| Decision | Why | Where recorded |
|----------|-----|----------------|
| If one move empties both health and oxygen, the **health ending** is shown | Hazard hits on arrival; also the only way the health ending can occur with these numbers (see 4.1) | user choice; spec 3.10, 4.2, AC-R8.7; ADR 0004 |
| AC-R7.7 (always four items) gets a Round 4 exception: a used medkit is gone | Earlier spec text must not be rewritten; added AC-R9.7 and a note under AC-R7.7 | user choice; spec Section 6 |
| Health gauge on its **own line** under oxygen | Both gauges plus `!! LOW OXYGEN !!` would be 53 columns | user choice; spec 3.10, AC-R8.2 |
| Only warning is the damage message on entering; scan clues and descriptions unchanged | Keeps Round 2 data untouched; Reactor description already hints at danger | user choice; spec 3.10 |
| `Room.hazard: bool` + `HAZARD_ROOMS` in `world.py`; damage/health/healing constants in `game.py` | World says *which* rooms are dangerous; *how much* is a game rule | ADR 0004 |
| Damage applied inside `Game._move()` right after the oxygen cost; health checked before win/oxygen checks | One function fully decides a move; movement stays in one place | ADR 0004, spec 4.2 note |
| New `DIED` outcome (status still `LOST`) | CLI picks the ending from the outcome alone | ADR 0004 |
| `use` is a generic item verb (parsed like `take`/`drop`) | Same name normalization; other items can gain uses later without parser changes | spec 3.10 |
| `use` checks in order: carried? → medkit? → full health? | Clear message per case | spec 3.10 table |
| Messages: `You use the medkit and restore <n> health.` (n = amount actually restored), `You are already at full health.` + `You keep the medkit for later.`, `You can't use the <item>.`, `Use what?`; not carried reuses `You are not carrying '<item>'.` / `NOT_CARRIED` | Short, under 50 columns, consistent with `drop` | spec 3.10 |
| New outcomes `HEALED`, `FULL_HEALTH`, `CANT_USE`; bare `use` → `INVALID` | Same pattern as take/drop | ADR 0004 |
| `TurnResult` gains `health`, `damage`, `healed` | CLI renders from the result alone (ADR 0001-0003 pattern) | spec 2.2 |
| `render_room(..., health=None)` draws the health line only when given | Round 1-3 display tests (which check `lines[-1]` is the oxygen gauge) stay valid unchanged; new tests check every real display has health | `cli.py` docstring |
| Move endings (`MOVED`, `WON`, `LOST`, `DIED`) share one render path via `_MOVE_ENDINGS` | Replaced three near-identical branches | commit `4c30c81` |
| Hazard texts: Reactor `Radiation from the reactor scorches your suit.`, Cargo `A drifting crate slams into you.` | Fit 50 columns; `HAZARD_MESSAGES` in `cli.py` | spec 3.10 |
| No low-health warning, no health in the win message, help footer and intro unchanged | Not asked for; scope rule | spec Section 10 (Round 4) |
| Spec title → "Rounds 1-4"; earlier sections only got "(Round 4)" notes | Same pattern as Rounds 2-3 | commit `ca547cc` |
| Spec overview and Section 9 heading corrected (inventory and hazards no longer listed as future work) | User asked; separate documentation commit | commit `6515570` |

## 4. Unresolved / open questions

1. **Health can only reach 0 on move 12.** The nearest hazard is 4 moves
   from the start and each re-entry takes at least 2 more moves, so the 5th
   hit (10 → 0) lands exactly when oxygen runs out (checked by exhaustive
   search). The health ending is reachable only because health is checked
   first. With the medkit used, death by health is impossible. If the user
   wants hazards to bite harder, that needs a requirements change (R3 fixes
   12 oxygen, R8 fixes 10 health and 2 damage). Raise it; don't change it.
2. **No requirements past R9.** Round 5 requirements (R10+) must be
   written by the user, added to `problem.md` under `## Round 5
   requirements`, committed, and pushed **before** development starts.
3. **GitHub:** the 8 Round 4 commits are not pushed. Wait for review. This
   handoff and `CLAUDE.md` also need review before they are committed.
4. **Still-wide Round 1 lines** (unchanged from the Round 3 handoff):
   intro `Move with north, south, east, west (or n, s, e, w).` (51), the
   `Unknown command: ...` message (60+), the win line `The hatch seals
   behind you...` (69), and the quit message (63). The Round 4 width test
   skips these four by prefix. Fixing them means rewording text the spec
   quotes, so ask first.
5. **Help footer says "Everything else is free."** True for oxygen, but
   hazard moves now also cost health. Left alone because the user chose no
   extra warnings; the user may want it reworded.
6. **Oxygen boundary rule still has no ADR** (spec 4.3 "Review note").
   ADR 0004 went to the Round 4 decision. Next free number: `0005.md`.
7. **Spec Section 9 save/load row** still lists only room id, oxygen,
   status; a status note above the table lists the extra state. The row
   itself is Round 1 text.
8. **Clues don't mention hazards or items.** If the user wants scanning to
   warn about the Reactor/Cargo, that changes Round 2 room data.

## 5. Important warnings for Round 5

- **Save/load must include** `room_id`, `oxygen`, **`health`**, `status`,
  `visited` (list of room ids), `room_items` (room id → list, order
  matters), and `inventory` (list, order matters). A used medkit is simply
  absent from both item collections; no extra flag is needed.
  `Room.items` and `Room.hazard` come from `build_ship()` and need no saving.
- **Locked doors:** put the check in `Game._move()` **before** the room
  changes, so a locked hazard room never costs oxygen or health and never
  gets added to `visited`.
- **Turn order in `_move()` matters:** move → visited → oxygen −1 → hazard
  damage → health 0? (`DIED`) → pod with oxygen > 0? (`WON`) → oxygen 0?
  (`LOST`). Tests pin the double-zero case (`REACTOR_DEATH` in
  `test_game.py` and `test_cli.py`).
- **Changing balance numbers** (`STARTING_HEALTH`, `HAZARD_DAMAGE`,
  `MEDKIT_HEALING`, hazard rooms) breaks many hard-coded expectations:
  "8 health" after the shortest route, the 5-entry `REACTOR_DEATH` script,
  heal amounts of 4 and 2, and `test_R8_constants_match_the_requirements`.
  `HAZARD_ROOMS` and `cli.HAZARD_MESSAGES` must stay in sync (a test checks).
- **Any rule that moves through a hazard affects health.** Round 1-3
  scripts happened to survive (the 12-move pod loss passes the Cargo Hold
  once and still ends with the oxygen ending). New long scripted
  playthroughs through hazards may now end in `DIED`.
- **`render_room` needs `health=`** (and `items=`) from every caller or the
  line silently disappears. `run()` uses `game.health` / `game.items_here`
  for the opening display; everything else uses the `TurnResult`.
- **Parser verbs taken:** `take`, `get`, `drop`, `use` (any input starting
  with these is an item command), plus single words `i`, `l`, `m`, `h`,
  `q`, `sc`, `inv`, `exit`, `?`. A new verb must not collide.
- **Giving other items a use** (keycard, repair kit, flashlight): extend
  `Game._use` after the "carried?" check; today any non-medkit returns
  `CANT_USE`. If an item is consumed, revisit AC-R7.7/AC-R9.7 and
  `test_R9_items_are_conserved_until_the_medkit_is_used` with the user.
- **Where to add text:** player-facing strings are constants near the top
  of `cli.py` (`DEATH_MESSAGE`, `HAZARD_HEADER`, `HAZARD_MESSAGES`, use
  messages next to the item messages). Help descriptions start at column
  29; tests check help and all new output fit 50 columns.
- Commit pattern held again: requirements, spec, then tests-first commits
  for world, parser, game, CLI, then README and ADR. Keep it.
