# Handoff: end of Round 3

For a fresh session starting the next round of *Signal Lost*. Standing rules
(how to work on this repo) are in `CLAUDE.md`; read that first. This file
covers **where things stand** and **what is still open**. The Round 1 and
Round 2 handoffs are still accurate for those rounds' details.

## 1. Current state

- **Round 3 is complete and committed** on `main` (last commit `2026a32`).
- **Push status:** the Round 3 requirements commit (`85d2151`) is on GitHub.
  The 7 Round 3 commits after it are **local only**: `main` is 7 commits
  ahead of `origin/main`. The user must review them before anything is
  pushed. This handoff and the `CLAUDE.md` update are **uncommitted**,
  waiting for the user's review.
- R6 (Collecting Items) and R7 (Inventory System) from `problem.md` are
  implemented and tested. **201 tests, all passing, none skipped** (135 from
  Rounds 1-2 plus 66 new).

| File | Tests | New in Round 3 | Names starting `R6_` / `R7_` |
|------|-------|----------------|------------------------------|
| `tests/test_world.py` | 25 | 5 | 5 / 0 |
| `tests/test_parser.py` | 27 | 9 | 5 / 4 |
| `tests/test_game.py` | 69 | 24 | 14 / 10 |
| `tests/test_cli.py` | 80 | 28 | 16 / 12 |

(Tests named `test_R6_R7_…` are counted under R6.)

What the player can do now, beyond Rounds 1-2:

- See items: any room display (game start, entering a room, `look`) adds
  `Items here: <a>, <b>` between the blank line and `Exits:` when the room
  holds items. Rooms with no items look exactly as before.
- `take <item>` / `get <item>`: moves the item from the room to the
  inventory. Free.
- `drop <item>`: moves a carried item into the current room, where it stays
  until taken again. Free.
- `inventory` / `inv` / `i`: lists carried items in pickup order, or
  `Your inventory is empty.` Free.
- `help` lists all three. README command table and rules are updated.

Starting items: `flashlight` (Cryo Bay), `medkit` (Medical Bay), `keycard`
(Bridge), `repair kit` (Engineering). Every other room, including the
Escape Pod, starts empty. **Items have no effect** on movement, oxygen, or
winning in Round 3.

Round 3 commits, in order: requirements (`85d2151`, pushed), spec
(`ebe35b1`), world items (`e7d7168`), parser (`d1b4fe7`), game rules
(`d497624`), CLI (`9b89631`), README (`d260889`), ADR 0003 (`2026a32`).
Each code step wrote its tests first and saw them fail before implementing;
tests and code were committed together because the rules forbid committing
failing tests.

## 2. How to run

```bash
python3 main.py                              # play
python3 -m unittest discover -s tests -v     # all tests, verbose
```

Smoke test that uses every item command and still wins with 6 oxygen:

```bash
printf 'take flashlight\nn\ntake medkit\ni\ne\ns\ntake repair kit\ndrop medkit\nlook\ns\ne\ninventory\ne\n' | python3 main.py
```

## 3. Decisions made this round, and why

The user chose the first four (asked before coding); the rest were made
during implementation and reported to the user.

| Decision | Why | Where recorded |
|----------|-----|----------------|
| 4 items: flashlight, medkit, keycard, repair kit, placed as above | R6 names a keycard and repair kit; a flashlight in the start room shows the item system right away; the medkit matches the Medical Bay description | user choice; spec 3.9, AC-R6.2 |
| Items are collect-only (no locks, no effects) | R6/R7 don't ask for effects; locks/puzzles are a future round and the scope rule forbids hooks now | user choice; spec 3.9, 10 |
| Full-name matching only, case and extra spaces ignored (`take kit` fails) | Simple and predictable; no ambiguity rules needed | user choice; spec 3.9, AC-R6.7 |
| Aliases: `get` = `take`; `inv`, `i` = `inventory`; no `take all` | Common adventure-game shortcuts, kept small | user choice; spec 3.5 |
| `Room.items` (frozen tuple) holds only the **starting** placement; `Game.room_items` (dict of lists) and `Game.inventory` (list) hold live state | Ship data from `build_ship()` never changes during play; each `Game` has its own items; an item is always in exactly one place | ADR `0003.md`, spec 2.2, 3.9 |
| Inventory in pickup order; room items in starting order with drops appended | Deterministic, easy to test exactly | spec 3.9 |
| No carrying limit | Not asked for | spec 3.9 |
| `TurnResult` gains `items`, `inventory` (tuple snapshots) and `item` | CLI renders from the result alone and can't mutate game state (same reasoning as `visited` in ADR 0002) | ADR `0003.md`, spec 2.2 |
| New outcomes `TAKEN`, `NOT_HERE`, `DROPPED`, `NOT_CARRIED`, `INVENTORY`; take/drop with no name return `INVALID` and the CLI says `Take what?` / `Drop what?` | Mirrors how a bad `go` returns `INVALID` and shows `Go where?` | ADR `0003.md`, spec 3.9 |
| `Items here:` line goes between the blank line and `Exits:`, only when non-empty | Keeps the Round 1 display format (and its test) unchanged for empty rooms | spec 3.9, AC-R6.3 |
| Items line and the not-here / not-carrying messages wrap at 50 columns | All four items in one room would otherwise make a 51-char line | AC-R7.8 |
| Message wording: `You take the X.`, `There is no 'X' here.`, `You drop the X.`, `You are not carrying 'X'.`, `You are carrying:` + `  - X` lines, `Your inventory is empty.` | Short, fit in 50 columns | spec 3.9 table |
| Spec title changed to "Rounds 1-3"; earlier sections only got "(Round 3)" annotations | Same pattern as Round 2; `CLAUDE.md` forbids rewriting earlier content | commit `ebe35b1` |
| ADR `0003.md` used for the inventory decision, not the oxygen boundary rule the Round 2 handoff suggested | The user asked for 0003 to record this round's decision | ADR `0003.md` |

## 4. Unresolved / open questions

1. **No requirements past R7.** The next round's requirements (R8+) must be
   written by the user, added to `problem.md` under a `## Round 4
   requirements` heading, committed, and pushed **before** development
   starts. Don't invent them.
2. **GitHub:** the 7 Round 3 implementation commits are not pushed. Wait for
   the user's review; don't push. This handoff and `CLAUDE.md` also need the
   user's review before they are committed.
3. **Some output lines are still wider than 50 columns** (carried over from
   Round 1, still unfixed):
   - `Move with north, south, east, west (or n, s, e, w).` (51, intro)
   - `Unknown command: '<text>'. Type 'help' for a list of commands.` (60+)
   - `The hatch seals behind you and the pod blasts free of the dying ship.`
     (69, win message, wording quoted in spec 4.4)
   - `You close your eyes and let the ship drift. Transmission ended.` (63, quit)

   All Round 2 and Round 3 output fits and is tested for it. Fixing these
   means rewording text the spec quotes, so ask the user first.
4. **The oxygen boundary rule still has no ADR** (spec 4.3 keeps its
   "Review note"). The next free number is `0004.md`. Ask before writing it.
5. **Section 9 and 10 headings in `spec.md` still say "Round 1"**. Round 2
   and Round 3 each appended a sub-heading to Section 10, and the Section 9
   Inventory row is marked "Built in Round 3". The next round should append
   the same way rather than retitling.
6. **Item names aren't shown on the map or in scan clues.** Clues were not
   changed this round, so none of them mention items. If items start to
   matter (for example a keycard lock), the user may want clues that hint
   at them.

## 5. Things the next session should know

- **Save/load must include** `room_id`, `oxygen`, `status`, `visited` (list
  of room ids), **`room_items`** (room id -> list of names, order matters),
  and **`inventory`** (list, order matters). `Room.items` comes from
  `build_ship()` and doesn't need saving. ADRs 0002 and 0003 note this.
- **Locked doors / item effects:** check `self.inventory` inside
  `Game._move()`, which is still the only place movement and `visited.add`
  happen. Put the check before the room changes. Decide with the user
  whether the map draws a locked exit (spec 3.7 draws every exit between
  two visited rooms).
- **Adding or renaming items:** edit `STARTING_ITEMS` in `world.py`. Names
  must be lower-case, single-spaced, and unique (a test checks). Several
  tests hard-code the four names and their rooms: `EXPECTED_ITEMS` in
  `test_world.py`, `ALL_ITEMS` and the conservation script in
  `test_game.py`, and the scripted sessions in `test_cli.py`. The world test
  also asserts there are exactly 4 items.
- **Item conservation** is tested by `test_R7_items_are_never_duplicated_or_lost`
  (`test_game.py`). Any new rule that consumes or creates items (using a
  medkit, for example) will need that test and AC-R7.7 revisited with the
  user.
- **The parser treats any input starting with `take`, `get`, or `drop` as an
  item command** and joins the remaining words as the name. A future verb
  must not collide with these, and `i` is now taken (inventory).
- **`render_room(room, oxygen, game_over=False, items=())`**: callers must
  pass `items=` or the items line is silently omitted. `run()` uses
  `game.items_here` for the opening display; every other display uses
  `result.items`.
- **Where to add text:** player-facing strings are constants near the top
  of `cli.py` (item messages are grouped under "Item messages"). Help rows
  put descriptions at column 29; a test checks help fits 50 columns.
- **Balance numbers unchanged:** shortest win is still 6 moves
  (`n e s s e e`), leaving 6 oxygen; all routes are even length. Item
  commands are free, so they never affect the oxygen boundary tests.
- Commit pattern held this round: requirements, spec, then tests-first
  commits for world, parser, game, CLI, then README and ADR. Keep it.
