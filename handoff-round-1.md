# Handoff: end of Round 1

For a fresh session starting the next round of *Signal Lost*. Standing rules
(how to work on this repo) are in `CLAUDE.md`; read that first. This file
covers **where things stand** and **what is still open**.

## 1. Current state

- **Round 1 is complete and committed** on `main` (pre-handoff commit `10d4053`,
  working tree clean before this file). The Round 1 commits have been pushed to Github.
- Requirements R1 (Room Navigation), R2 (Room Information), and R3 (Oxygen and
  Escaping) from `problem.md` are implemented as described in `spec.md`.
- **88 tests, all passing** (Python 3.12.3 on the dev machine; 3.10+ is the
  target). No skips.

| File | Tests |
|------|-------|
| `tests/test_world.py` | 13 |
| `tests/test_parser.py` | 14 |
| `tests/test_game.py` | 28 |
| `tests/test_cli.py` | 33 (includes 2 subprocess runs of `main.py` and an `ast` check that `game.py` never calls `print`/`input`) |

What the player can do today:

- Move with `north/south/east/west`, `n/s/e/w`, or `go <dir>` (case and
  spacing ignored).
- `look`/`l`, `help`/`h`/`?`, `quit`/`q`/`exit`. Ctrl-C and Ctrl-D quit cleanly.
- 11-room map (spec 3.1/3.2). Start is `cryo_bay`, goal is `escape_pod`.
  The shortest win takes 6 moves (`n e s s e e`) and leaves 6 oxygen.
- Oxygen gauge after every room display, with `!! LOW OXYGEN !!` at 3 or less
  (hidden on the final win/loss screen).

## 2. How to run

```bash
python3 main.py                              # play
python3 -m unittest discover -s tests -v     # all tests, verbose
python3 -m unittest                          # also works (spec 7.3 form)
```

Quick smoke test of a winning game:

```bash
printf 'n\ne\ns\ns\ne\ne\n' | python3 main.py
```

## 3. Decisions made, and why

| Decision | Why | Where recorded |
|----------|-----|----------------|
| Game rules (`game.py`) are separate from terminal I/O (`cli.py`); `run(input_fn, output_fn)` takes stand-in functions | Lets tests check rules and whole playthroughs with no real terminal, and gives later rounds one place to add commands | `docs/decisions/0001.md` |
| Arriving at the pod with **0** oxygen after the move is a **loss** | `problem.md` says you win "while they still have oxygen"; read as oxygen > 0 *after* paying for the move. Because every route has an even length, this makes move 12 into the pod a loss | `spec.md` 4.3, `AC-R3.6`, README "Rules" |
| Only a **successful** move costs oxygen; everything else is free | Directly from R1/R3 | `spec.md` 4.1 |
| No randomness | So full playthroughs give the same output every time and can be tested | `spec.md` 1.3 |
| Plain ASCII, 50-column layout, no ANSI color | Terminal support varies; atmosphere comes from the writing and `====` framing | `spec.md` 1.3, 3.6 |
| `Game.handle` uses a `kind -> handler` dict; all movement goes through `Game._move()` | One parser rule + one handler + one render branch per new command; lock and hazard checks have one home | `spec.md` 9, `CLAUDE.md` |
| No stubs or hooks for future features | Spec 9 requires it; keeps Round 1 code honest | `spec.md` 9 |

Smaller implementation choices the spec did not spell out:

- `Room.exits` is stored as a read-only `MappingProxyType` (spec 2.2 says
  `dict`). This stops game code from changing the map by accident.
- `Game(rooms=None)` takes an optional map so tests can pass in a custom one.
  If omitted, it uses `build_ship()`.
- A malformed `go` (`go`, `go up`) is parsed as `kind="unknown"`. The CLI
  uses `parser.is_go_attempt()` to show "Go where?" instead of the
  generic unknown-command message. The game logic treats both the same
  (`Outcome.INVALID`).
- Room descriptions were polished from the spec's drafts, as spec 3.2
  allows. Room names, ids, and exits match the spec exactly.
- `Outcome.GAME_OVER` and `Outcome.EMPTY` produce no output.

## 4. Unresolved / open questions

1. **No requirements exist past R3.** `problem.md` only has R1-R3, and
   `spec.md` is titled "Round 1." The next round needs requirements from the
   user. `CLAUDE.md` says not to rewrite either file, so **ask the user** how
   they want new requirements and acceptance criteria recorded: appended to
   the existing files, or in a new file such as a Round 2 spec. Don't
   decide this yourself.
2. **Some output lines are wider than 50 columns**, even though the
   layout rule says 50:
   - `Move with north, south, east, west (or n, s, e, w).` (51, intro)
   - `The hatch seals behind you and the pod blasts free of the dying ship.`
     (69, win message, wording copied from spec 4.4)
   - `You close your eyes and let the ship drift. Transmission ended.` (63, quit)
   - `Unknown command: '<text>'. Type 'help' for a list of commands.` (60+)

   No test checks line width. Fixing it means wrapping or rewording text
   that the spec quotes, so check with the user before changing it.
3. **The oxygen boundary rule has no ADR.** It is in spec 4.3 (which still
   has its "Review note" saying it is a judgment call), the README, and the
   tests, but `docs/decisions/` only has `0001.md`. The user may want it
   recorded as `0002.md`. Ask before writing it.
4. **Ctrl-C is only caught while waiting for input.** A `KeyboardInterrupt`
   during output would show a traceback. This is unlikely, since output is
   instant, and it is acceptable under AC-G.3 as written. Mentioned only for
   completeness.

## 5. Things the next session should know

- **Planned future features** (spec Section 9): inventory, puzzles/locked
  doors, hazards, save/load. Spec 9 says where each one plugs in. In short:
  - Inventory: an `items` field on `Room`, an `inventory` on `Game`, new
    parser kinds and handlers.
  - Locked doors: exits become small `Exit` objects; checks go in `_move()`.
  - Hazards: a step in `_move()` after entering a room (spec 4.2, step 3).
  - Save/load: serialize `room_id`, `oxygen`, `status` (plus whatever new
    state is added); rebuild the map from `build_ship()`.
- **Watch the parity and balance numbers.** `test_world.py` asserts the
  shortest route is 6 and `test_game.py` relies on even-length routes
  (10-move win, 12-move loss). Any map change, extra oxygen cost, or
  oxygen pickup will break those tests and the 4.3 reasoning. Update the
  tests on purpose; don't just patch them until they pass.
- **Where to add text:** all player-facing strings are constants at the
  top of `cli.py`. `render_result` has one branch per `Outcome`.
- **Test conventions** (also in `CLAUDE.md`): names start `test_R<n>_`, and
  the docstring cites an `AC-…` id. New rounds need new AC ids, which ties
  back to open question 1.
- `.gitignore` already excludes `__pycache__/`, virtualenvs, secrets, and
  `transcript*` / `*.jsonl` / `*.log` files.
- Commit history so far is one small commit per step (spec, tests,
  world, parser, game, cli, README, ADR, CLAUDE.md). Keep that pattern.
