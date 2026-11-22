# Handoff: end of Round 5

For a fresh session starting Round 6 of *Signal Lost*. Standing rules (how
to work on this repo) are in `CLAUDE.md`; read that first. This file covers
**where things stand** and **what is still open**. The Round 1-4 handoffs
are still accurate for those rounds' details, except where Section 3 below
says the revised R3 changed something.

## 1. Current state

- **Round 5 is complete and committed** on `main` (last commit `5c4913c`,
  the scanner-clue correction; see Section 4.1).
- **Push status:** the Round 5 requirements commit (`f304820`) is on
  GitHub. The **8 commits after it are local only** (`main` is 8 ahead of
  `origin/main`). The user must review them before anything is pushed. This
  handoff and the `CLAUDE.md` update are **uncommitted**, waiting for the
  user's review.
- R10 (Keycard and Locked Escape Pod) and the revised R3 escape condition
  are implemented and tested. **317 tests, all passing, none skipped**
  (264 from Rounds 1-4 plus 53 new, 6 of them for the clue correction).

| File | Tests | New in Round 5 | Breakdown |
|------|-------|----------------|-----------|
| `tests/test_world.py` | 39 | 8 | 3 `R10_`, 5 `R5_R10_` (clue correction) |
| `tests/test_parser.py` | 31 | 1 | 1 `R10_` |
| `tests/test_game.py` | 127 | 26 | 21 `R10_` / `R9_R10_`, 5 `R3_` |
| `tests/test_cli.py` | 120 | 18 | 15 `R10_`, 2 `R3_`, 1 `R5_R10_` (clue correction) |

What the player can do now, beyond Rounds 1-4:

- **Locked pod:** the door from the Airlock Junction east into the Escape
  Pod starts locked. Trying it prints `The escape pod door is locked.` /
  `A keycard reader beside it blinks red.` / the exits line. The player
  stays put, with no oxygen or health cost and no map change.
- **`use keycard`** (keycard carried, at the Airlock Junction) prints
  `You swipe the keycard. The reader blinks green.` / `The escape pod door
  is unlocked.` It's free, the keycard stays in the inventory, and the door
  stays unlocked for the rest of the game, even if the keycard is dropped.
- Keycard used elsewhere: `The keycard doesn't work here.` Used again at the
  reader: `The escape pod door is already unlocked.` Not carried: the
  existing `You are not carrying 'keycard'.`
- **Winning** now needs the door unlocked first. The shortest win is
  **8 moves** with a detour to the Bridge, and it ends with **4 oxygen,
  8 health**.
- **Scanner:** the Central Corridor and Bridge clues now point toward the
  keycard instead of calling the Bridge a dead end (Section 4.1).

Round 5 commits, in order: requirements (`f304820`, pushed), spec
(`fb7fd8d`), world `KEYCARD_READER` (`343ce71`), parser test (`c4edb14`),
game rules plus the updated earlier tests (`0f7edb2`), CLI messages
(`1ca6819`), README (`dc739d1`), ADR 0005 (`cdeb47c`), scanner-clue
correction (`5c4913c`, made after the user reviewed the first handoff
draft). Each code step
wrote its tests first and saw them fail. The parser test passed straight
away because `use <item>` already handled the keycard. Tests and code
were committed together, and every commit is green.

## 2. How to run

```bash
python3 main.py                              # play
python3 -m unittest discover -s tests -v     # all tests, verbose
```

Smoke tests:

```bash
# Shortest win: 8 moves, keycard from the Bridge, ends with 4 oxygen, 8 health
printf 'n\ne\nn\ntake keycard\ns\ns\ns\ne\nuse keycard\ne\n' | python3 main.py

# Locked door: the old 6-move route now stops at the Airlock Junction
printf 'n\ne\ns\ns\ne\ne\nlook\nq\n' | python3 main.py

# Every keycard message: wrong place, locked, unlocked, already unlocked, win
printf 'n\ne\nn\ntake keycard\nuse keycard\ns\ns\ns\ne\ne\nuse keycard\nuse keycard\ne\n' | python3 main.py

# Corrected scanner clues: Corridor and Bridge both mention the keycard
printf 'n\ne\nscan\nn\nscan\nq\n' | python3 main.py

# Health ending (unchanged from Round 4)
printf 'n\ne\ns\ne\nw\ne\nw\ne\nw\ne\nw\ne\n' | python3 main.py
```

## 3. The revised R3 escape requirement

**Original R3 (Rounds 1-4):** reach the Escape Pod while you still have
oxygen and you win. The spec reads "still have oxygen" as oxygen > 0
*after* paying for the move (spec 4.3).

**Revised R3 (Round 5, `problem.md` "R3: Revised Escape Requirement"):**
the player must also unlock the pod door with the keycard first. Reaching
the pod without unlocking it is no longer a win. Oxygen and health must
still remain. The original oxygen rules still apply.

How it is built (spec Section 4.6, AC-R3.9-3.12):

- The lock is checked in `Game._move()` **before** the room changes. A
  locked move returns `LOCKED` and none of the move steps run. A move into
  the pod can only reach the win check once `pod_locked` is `False`.
- The win check is **unchanged** (`room == ESCAPE_ROOM and oxygen > 0`,
  after the health check). "In the pod" now implies "unlocked".
- The oxygen boundary still holds: entering the unlocked pod on move 12
  (0 oxygen) is a loss. Parity still holds: the pod is only reachable on an
  even move.
- The original R3 text and AC-R3.4 / AC-R3.8 are **kept word for word** in
  the spec, with a "(Round 5)" note saying AC-R3.10 / AC-R3.11 replace them.

Route facts (exhaustive search, also pinned by tests):

| Route | Moves | Oxygen left | Health left | Result |
|-------|-------|-------------|-------------|--------|
| `n,e,n,take keycard,s,s,s,e,use keycard,e` (Cargo Hold) | 8 | 4 | 8 | win |
| `n,e,n,take keycard,s,s,e,s,use keycard,e` (Reactor Core) | 8 | 4 | 8 | win |
| `n,s,n,e,n,take keycard,s,s,s,e,use keycard,e` | 10 | 2 | 8 | win |
| `n,s,n,s,n,e,n,take keycard,s,s,s,e,use keycard,e` | 12 | 0 | 8 | loss (4.3) |
| `n,e,s,s,e,e` (old 6-move win) | 5 + refused | 7 | 8 | locked, still playing |

Every winning route takes 8 or 10 moves. No route shorter than 8 wins (a
test replays them all).

## 4. Decisions made this round, and why

The user chose the first four (asked before coding). The rest were made
during implementation and reported to the user afterwards.

| Decision | Why | Where recorded |
|----------|-----|----------------|
| Once unlocked, the door **stays unlocked**, even if the keycard is dropped | R10 says `use keycard` unlocks the door; "carry to pass" would make the `use` step pointless | user choice; spec 3.11, AC-R10.7 |
| Locked message has a **keycard hint** line (`A keycard reader beside it blinks red.`) | Tells the player what to look for | user choice; spec 3.11 |
| Airlock `Exits:` line **unchanged** (`north, east, west`) | Keeps the Round 1 display format | user choice; AC-R10.9 |
| Superseded criteria **keep their text**, with "(Round 5)" notes pointing to AC-R3.10, AC-R3.11, etc. | Preserve R3 history; same pattern as AC-R7.7 in Round 4 | user choice; spec Section 6 |
| One `pod_locked: bool` on `Game`, not `Exit` objects or a lock table | One door; the scope rule forbids hooks for future features | ADR 0005 |
| Lock check in `_move()` after the "no exit" check, **before** the room changes | Refused move costs nothing and doesn't touch `visited` | ADR 0005, spec 4.2 note |
| Win check left unchanged | A locked pod can't be entered, so no extra condition is needed | ADR 0005, spec 4.6 |
| `KEYCARD_READER = "airlock_junction"` in `world.py`; `KEYCARD = "keycard"` in `game.py` | Where the reader is = ship layout; which item unlocks = game rule (same split as hazards in ADR 0004) | ADR 0005 |
| `use keycard` checks carried? → at reader? → already unlocked? | "carried?" stays first, as in Round 4. Away from the reader it is `WRONG_PLACE` even after unlocking | spec 3.11 table |
| New outcomes `LOCKED`, `UNLOCKED`, `ALREADY_UNLOCKED`, `WRONG_PLACE`; `TurnResult` unchanged | The CLI renders from the outcome alone | spec 2.2 |
| `LOCKED` rendered like `BLOCKED`: message lines, then the exits | Consistent with other refused moves | `cli.render_result` |
| Message wording: `You swipe the keycard. The reader blinks green.` (47 cols), `The escape pod door is unlocked.`, `...already unlocked.`, `The keycard doesn't work here.` | Short, under 50 columns | spec 3.11, `cli.py` constants |
| Keycard is **not** consumed | R10 says so; item counting (AC-R7.7 / AC-R9.7) unchanged | spec 3.11 |
| Flashlight and repair kit still `CANT_USE` | Not asked for | AC-R9.7 note |
| No changes to descriptions, help text, intro, or win message (clues: see 4.1) | Scope rule; Round 2 data | spec Section 10 (Round 5) |
| No parser change; one test pins `use keycard` parsing | `use` was already a generic verb | commit `c4edb14` |

### 4.1 Scanner-clue correction (commit `5c4913c`)

The first draft of this handoff pointed out that two Round 2 clues told the
player to avoid the Bridge, which is now required because it holds the
keycard. The user asked for them to be fixed before Round 5 closed.

| Room | Old clue (Rounds 2-5) | New clue |
|------|-----------------------|----------|
| Central Corridor | `…toward the engine rooms. The rooms to the north and east read cold and still.` | `A faint heat signature runs south, toward the engine rooms. Security logs place the captain's keycard on the Bridge, just north.` |
| Bridge | `…beyond Engineering. Nothing forward of here leads off the ship.` | `The nav log shows the escape pod docked aft, beyond Engineering. Its hatch answers only to a crew keycard, so don't leave without one.` |

Decisions made while doing it (reported to the user):

- **Hint level:** the clues say *where* the keycard is and *that* the pod
  needs it, but not where it is used (the Airlock Junction reader) or the
  command (`use keycard`). The lock message gives that hint at the door.
  A test checks that neither clue mentions the airlock, the reader,
  "unlock", or `use keycard`.
- The Corridor clue **keeps its first sentence** (south toward the engine
  rooms), so it still points to the exit route.
- The **Mess Hall** clue ("This end of the ship loops back on itself") and
  the **Comms Array** clue are unchanged: those rooms really are a dead end.
  The other seven clues and every room description are unchanged.
- **Spec:** "(Round 5 clarification)" notes in 3.3 (the Bridge is no longer
  part of the trap; Comms and Mess still are), 3.8 (old and new clue text
  side by side), new **AC-R5.7**, the Round 5 test plan, and Section 10.
  No earlier text was edited.
- **Tests:** no existing test hard-coded either clue, so **none changed**.
  Five new `test_R5_R10_…` tests in `test_world.py` (`Round5ClueTests`)
  and one in `test_cli.py` (`KeycardOutputTests`) cover AC-R5.7. They are
  named R5 first, because the scanner is R5 and the reason for the change
  is R10.
- No README change was needed (it doesn't quote clues).

## 5. Tests changed because of the revised R3

Every one of these walked straight into the pod using the old 6-, 10- or
12-move routes. Under the revised R3, those routes now stop at the locked
door (`LOCKED`), so the tests never reached their win or loss. Each was
changed to take the keycard detour using **real moves** (the tests never
set `pod_locked = False` directly). No other existing test body changed;
each module docstring went from "(R1-R9)" to "(R1-R10)". All changes are in
commit `0f7edb2`.

**`tests/test_game.py` (14):**

| Test | Change |
|------|--------|
| `test_R1_every_exit_on_the_shortest_route_moves_the_player` | Walks the 8-move keycard route: 8 expected rooms, including the Bridge |
| `test_R3_shortest_route_wins_with_six_oxygen` → **`…_four_oxygen`** | `KEYCARD_ROUTE`; oxygen 6 → 4; cites AC-R3.10/3.11 |
| `test_R3_reactor_core_route_also_wins_with_six_oxygen` → **`…_four_oxygen`** | `KEYCARD_REACTOR_ROUTE`; 6 → 4 |
| `test_R3_ten_move_route_wins_with_two_oxygen` | `KEYCARD_TEN_MOVE_WIN` (still 2 oxygen) |
| `test_R3_twelve_move_pod_arrival_is_a_loss` | `KEYCARD_TWELVE_MOVE_POD`; also asserts the `UNLOCKED` step |
| `test_R3_no_state_changes_after_winning` | Keycard route; oxygen 6 → 4 |
| `test_R4_winning_move_records_the_escape_pod` | Keycard route; visited count 7 → 8 (Bridge added) |
| `test_R4_map_is_ignored_after_the_game_ends` | Keycard route to reach `WON` |
| `test_R4_R5_shortest_route_still_wins_with_six_oxygen_using_map_and_scan` → **`…_four_oxygen_…`** | Keycard route; 6 → 4 |
| `test_R4_R5_twelve_move_pod_arrival_is_still_a_loss_with_map_and_scan` | Keycard 12-move route |
| `test_R6_collecting_items_on_the_shortest_route_still_wins_with_six` → **`…_with_four`** | Keycard route; 6 → 4; inventory now includes the keycard |
| `test_R8_shortest_routes_win_with_8_health_and_6_oxygen` → **`…_and_4_oxygen`** | Both keycard routes; 6 → 4 oxygen (health still 8) |
| `test_R8_a_ten_move_route_through_both_hazards_still_wins` | The 3-hazard 10-move route can't fit the 2-move keycard detour, so it became a 2-hazard keycard route: health 4 → 6, oxygen still 2 |
| `test_R8_earlier_boundary_rules_are_unchanged` | 12-move pod case uses the keycard route |

**`tests/test_cli.py` (14):** the three `MovementOutputTests`
(`…room_name`, `…room_description`, `…correct_exits`, now over
`KEYCARD_ROUTE` via `move_turns()`),
`test_R3_winning_playthrough_prints_win_message_after_pod_info` (`6` → `4
oxygen to spare`), `test_R2_escape_pod_info_is_shown_on_the_winning_move`
(`OXYGEN: 4/12`), `test_R3_game_stops_reading_input_after_winning`,
`test_R3_reaching_the_pod_with_zero_oxygen_prints_loss_not_win`,
`test_R3_main_py_plays_a_winning_game_and_exits_zero`,
`test_R4_R5_winning_with_map_and_scan_still_leaves_six_oxygen` →
**`…_four_oxygen`**, `test_R4_R5_main_py_accepts_map_and_scan`,
`test_R6_R7_collecting_items_on_the_way_still_wins_with_six_oxygen` →
**`…_four_oxygen`** (inventory now `flashlight, keycard, repair kit`),
`test_R8_final_displays_show_health`,
`test_R8_shortest_win_shows_the_hazard_then_wins_with_8_health` (hazard is
now on turn 7, not 4), `test_R8_oxygen_loss_still_shows_the_oxygen_ending`.

The old route constants (`SHORTEST_ROUTE`, `REACTOR_ROUTE`, `TEN_MOVE_WIN`,
`TWELVE_MOVE_POD`) are **kept** in both files. They now serve the AC-R3.9
tests ("old routes no longer win") and partial walks (e.g.
`SHORTEST_ROUTE[:5]` to the reader). The new constants are `KEYCARD_ROUTE`,
`KEYCARD_REACTOR_ROUTE` (game only), `KEYCARD_TEN_MOVE_WIN` (game only),
and `KEYCARD_TWELVE_MOVE_POD`. `test_game.py` gains `step()` /
`run_script()` (mixed directions and `"<verb> <item>"` strings).
`test_cli.py` gains `move_turns()` and `replies()`.

## 6. Unresolved / open questions

1. **Resolved: misleading scan clues.** Fixed in `5c4913c` (Section
   4.1). Remaining smaller point: spec 3.3's original "Traps" bullet and
   spec 1.2 ("a loop of rooms that leads nowhere") still read as Round 1
   wrote them, with a Round 5 clarification note under 3.3 only. If a
   future clue or layout change happens, keep AC-R5.7 true: no clue may
   steer the player away from wherever the keycard is.
2. **The lock is hard-wired to the Escape Pod.** A second locked door would
   need a small refactor (e.g. a set of locked room ids). Don't build it
   unless a requirement asks.
3. **Health can still only reach 0 on move 12** (Round 4 handoff 4.1). The
   lock only refuses moves, so this is unchanged.
4. **Spec 3.3, 1.2, and AC-R3.8 still say 6 moves.** They are kept as
   history with Round 5 notes. `test_world.py`'s
   `test_R3_shortest_route_to_escape_pod_is_six_moves` and
   `test_R8_shortest_routes_enter_exactly_one_hazard` are **map-only**
   facts (shortest graph path, ignoring the lock) and are still true.
   Don't "fix" them to 8.
5. **Help footer** still says "Everything else is free." This is true for
   oxygen; hazard moves cost health (Round 4 handoff 4.5). Unchanged.
6. **Still-wide Round 1 lines** (intro `Move with…` 51, `Unknown
   command…`, win `The hatch seals…` 69, quit message 63). The width tests
   skip them by prefix. Rewording them needs the user's OK.
7. **Oxygen boundary rule still has no ADR** (spec 4.3 review note). Next
   free ADR number: `0006.md`.
8. **Spec Section 9 save/load row** still lists only room id, oxygen, and
   status (Round 1 text). The status notes above the table list the extra
   state, now including `pod_locked`.
9. **README rules bullet** about free actions was reflowed unevenly when
   "trying the locked pod door" was added. It's cosmetic.

## 7. Important details for Round 6

- **No requirements past R10 exist yet.** Round 6 requirements (R11+)
  must be written by the user, added to `problem.md` under
  `## Round 6 requirements`, committed, and pushed **before** development
  starts. `CLAUDE.md` names save/load as the remaining planned feature; it
  may or may not be what the user writes.
- **If Round 6 is save/load**, the saved state is: `room_id`, `oxygen`,
  `health`, `status`, `visited` (list of room ids), `room_items` (room
  id → list, order matters), `inventory` (list, order matters), and
  **`pod_locked`** (new in Round 5). A used medkit is just absent; no flag
  is needed. `Room` data (`items`, `hazard`, exits) comes from
  `build_ship()` and is not saved. A loaded game must give identical
  output to a played one; the game is deterministic.
- **Turn order in `_move()`:** direction valid? → exit exists?
  (`BLOCKED`) → **pod locked? (`LOCKED`)** → move → visited → oxygen −1
  → hazard damage → health 0? (`DIED`) → pod with oxygen > 0? (`WON`) →
  oxygen 0? (`LOST`) → `MOVED`. Tests pin each step.
- **`use` order:** no name (`INVALID`) → not carried (`NOT_CARRIED`) →
  keycard (`_use_keycard`: `WRONG_PLACE` / `ALREADY_UNLOCKED` /
  `UNLOCKED`) → not medkit (`CANT_USE`) → full health (`FULL_HEALTH`) →
  heal (`HEALED`). Giving the flashlight or repair kit a use means a new
  branch before `CANT_USE`.
- **Any new winning playthrough must include the keycard steps.** The old
  6-move scripts stop at the door. Use the `KEYCARD_*` constants and
  `run_script()` / `step()` in `test_game.py`. In `test_cli.py`, use
  `replies(session)` rather than `turns()[-1]`: when a script ends without
  ending the game, the last turn is the end-of-input quit message.
- **Clue text:** if the keycard moves, or the Bridge or Corridor exits
  change, the AC-R5.7 tests in `test_world.py` (`Round5ClueTests`) must
  change too, and the clues must still not steer players away from the
  keycard.
- **Balance numbers are hard-coded in many tests:** 4 oxygen / 8 health on
  the 8-move win, 7 oxygen at the locked door, visited count 8, heal
  amounts of 4 and 2, the 5-entry `REACTOR_DEATH` script. Changing
  `STARTING_OXYGEN`, `HAZARD_DAMAGE`, room exits, or item placement
  (especially moving the keycard) breaks them. Re-run an exhaustive route
  search after any such change.
- **`render_room` needs `health=` and `items=`** from every caller (Round 4
  warning, still true).
- **Parser verbs taken:** `take`, `get`, `drop`, `use`, plus single words
  `i`, `l`, `m`, `h`, `q`, `sc`, `inv`, `exit`, `?`. Save/load commands
  (e.g. `save`, `load`) don't collide, but check `s` (south) and other
  one-letter aliases.
- **Commit pattern** held again: requirements, spec, then tests-first
  commits per layer, then README, then ADR. When a game change breaks
  older CLI tests, update those tests in the **same** commit as the game
  change, so every commit stays green (done in `0f7edb2`).
