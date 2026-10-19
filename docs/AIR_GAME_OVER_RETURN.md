# Non-ranking score and game-over return

Follow-up: the [masked title-reset prefix](AIR_TITLE_RESET.md) now continues
both histories through LCD disable, clears and fixed graphics-copy work.
Title layout, LCD restart and graphics payload/pixels remain unqualified.

October 20, 2026. Continues both accepted [final-life results](AIR_FINAL_RESULT.md)
from the end of the fixed hold through high-score rejection, the no-survivor
test and all outgoing fade waits. Ends at title-reset entry, before its first
operation. It does not qualify title reset/initialization or a completed title
screen, qualifying-score insertion/name entry or surviving-player routing.

Both ordinary and earlier-paused histories match 120 new boundaries, eight
score rows, sixteen score-byte comparisons, 32 displays and 64 complete vectors
each. Combined: 240 boundaries / 16 rows / 32 compared score bytes / 64 displays /
128 vectors, with zero differences. All 325 / 329 earlier complete native CSVs
remain byte-identical, including the complete final-life result. The composite
requalifies that parent chain under its existing original control hashes.

The five native failed attempts retain their initial zero savings. All eight
initial scores exceed that amount; each comparison reads the first two BCD
bytes and returns with the lower-result condition. The original 48-byte score
table is observed unchanged at return. Native execution reads the existing
decoded initial table and does not modify it. The new byte comparison covers
the sixteen accessed score bytes, not a new full-byte proof of every name.

Both native player life counts are zero after the current final result. That
state selects the source's outgoing fade rather than another player. The native
clock retains input, countdown, music and display deadlines from that actual
result. Song 13 continues during the 32 fade displays; countdown becomes 54 and
total result display/vector pairs become 546. No original snapshots, score
decisions, costs or timestamps initialize native execution.

The separately bounded owner rejects a qualifying/equal score, a surviving
player or invalid BCD instead of inventing those unqualified continuations.
Synthetic native tests exercise first-, second- and third-byte rejection,
unchanged tables, equal-score rejection, survivor rejection and all fade waits.
The original zero-savings cases exercise the second-byte path only.

## Reproduction and validation

No original control extension is needed: both existing final-result controls
already run beyond the title-reset entry. Their independently repeated parent
and final hashes remain the accepted controls. New instrumented runs match the
same full-control digest and pinned backend; no RAM or score injection is used.

Capture with `tools/air_game_over_return_reference.py capture ROM --capture CONTROL
--parent-out FINAL_RESULT_REFERENCE --out RETURN_REFERENCE`. The source start
target is the independently captured final hold endpoint; it selects measurement
only and never enters native replay. ROM, table observations and recordings stay
local. The capture rejects qualifying scores and changed/incomplete controls.

Build with `tools/build_air_clock_probe.py --out local/air-game-over-return-clock-probe.exe`.
Use the existing final-result replay extents and initial/display inputs, the new
return recording's `buttons.txt`, and replace `--fifth-result` with
`--fifth-return`. Explicit fifth entry and all preceding ownership remain required.
Output adds `.fifth.game-over-return*`; earlier output remains exact.

Compare with `tools/air_game_over_return_reference.py compare NATIVE_BASE`, the
same chain arguments as `air_final_result_reference.py compare`, plus
`--return-out RETURN_REFERENCE` and `--final-base ACCEPTED_FINAL_NATIVE_BASE`.
Reports are `.game-over-return.comparison.json`. Local evidence uses
`air-game-over[-pause]-return-reference` and corresponding `return-services.csv`;
the controls remain `sameboy-air-fifth[-pause]-result-control`.

Validation: O2 native Windows diagnostic, both attached comparisons, 29,724
native final/result-return assertions and 835 Python tests. Shared gameplay,
audio and clock owners were unchanged; the earlier Windows/integration
qualifications retain their scope and were not repeated. The regular Windows
EXE is rebuilt from the committed source; the timing continuation is still
diagnostic, not integrated into its scheduler. No release or automation settings
are changed. ROM/assets/recordings/binaries remain local.

Next: title-reset internals and title entry, plus a separately controlled
qualifying-score/name-entry case. Other campaigns/players, vacant flags,
remaining UI/reset/work, production timing, complete images/PCM and final
human/device/independent-Windows/distribution gates remain open. Timing point 1
and [final acceptance](ACCEPTANCE.md) remain incomplete.
