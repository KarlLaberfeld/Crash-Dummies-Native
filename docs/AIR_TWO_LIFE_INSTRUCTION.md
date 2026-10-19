# Two-life handoff and complete next instruction

October 19, 2026. Native diagnostic continuation of the
[complete third Air failure](AIR_THIRD_RESULT.md), from result return at 0514
through the next completed instruction text at 032b. This does not yet start
the fourth attempt or integrate the Windows scheduler.

The subsequent Start/entry is qualified separately in
[fourth Air entry](AIR_FOURTH_ENTRY.md); this checkpoint retains its original scope.

Both existing ordinary/prior-entry-pause histories match the complete live-player
selection, background clear, two-life header, music/picture loading, map
transition and timed instruction text. Per history: 1,607 boundaries, 629 display
services, 1,259 complete vectors, 12,856 readiness/line polls, 2,286 stores and
64 map selections, zero differences. Combined: 3,214 boundaries / 1,258 displays /
2,518 vectors / 25,712 polls / 4,572 stores / 128 selections. These are the same
two histories, not new independent gameplay patterns; all earlier gameplay/
outgoing/result and accepted-prefix comparisons overlap prior checkpoints.

The native result adapter now returns its actual completed transition. The
continuation copies the current campaign, applies that transition's two lives
to its selected player, and passes its current LCD epoch, counters and input
into the existing handoff/instruction owners. It does not reload an earlier
result, reset lives or restart a clock. The current instruction's software
scroll (64) survives until the next map's explicit clear; header glyph stores
and all boundary/summary life fields match two. Fresh timing and original
snapshots are comparison targets only, never native scheduling inputs.

The same unchanged controls already contain enough released-Start time to finish
this instruction. No events, setup state, input file or final control digest
were changed. Each new instrumented capture matches the previously accepted
full-control digest and pinned backend. The earlier repeated uninstrumented
controls remain the independent control evidence.

## Reproduction and guards

Capture into fresh instruction folders using the same third-result controls:

- `air_handoff_reference.py capture --following --after-retry 2`
- `air_instruction_header_reference.py capture --following --after-retry 2`
- `air_instruction_picture_reference.py capture --following --after-retry 2`
- `air_instruction_map_reference.py capture --following --after-retry 2`
- `air_instruction_text_reference.py capture --following --after-retry 2` last.

Tools are under `tools/`; all take the usual ROM, `--capture` and `--out` paths.
Capture selection counts instruction/entry pairs, not ordinary repeated game
updates. The new selection requires `--following`; default capture behavior is
unchanged. Raw display inputs retain the entire prior history, while service
indices remain relative to the current result's own display origin.

Build with `tools/build_air_clock_probe.py`. Use the complete-third-result replay
arguments from AIR_THIRD_RESULT.md, but supply the new instruction `buttons.txt`
and append `--third-instruction 5`. Extents 1..4 stop after handoff/header/picture/
map and need matching raw input extents. The default remains no continuation.
Output siblings are `.third.next-handoff*` through `.third.next-text*`; the
preceding `.next-incoming*`, `.next-gameplay*` and all earlier scopes remain intact.

First run the full `air_third_result_reference.py` chain on that native output.
Then run `tools/air_next_instruction_reference.py NATIVE_BASE --after-retry 2`
with `--capture` set to the same third-result control, `--out` to its fresh
instruction folder, `--startup` to the accepted result startup, and
`--result-out` to the accepted third-result reference folder. The separate
result path avoids relabeling or copying original evidence. It requires a
completed third-result marker and the matching instruction generation on every
component, then checks full source work, inheritance, endpoints and counters.
The final report is `.third-instruction.comparison.json`.

Local observations use `local/air-two-life-instruction-reference/` and
`local/air-two-life-pause-instruction-reference/`. Native outputs use
`local/air-two-life-instruction-services.csv*` and the pause variant. Controls,
result observations and startups remain the accepted `air-third-result` paths.
Original recordings, decoded assets, ROM and binaries remain local/ignored.

Validation: optimized native diagnostic, both full attached third-result chains
and both new instruction comparisons; 708 Python tests and CLI bounds/ownership
guards. All five legacy following-instruction capture outputs remain identical
to their accepted ordinary-control recordings. Native semantic owners are
unchanged; the previous 52,920 result / 883 handoff / 4,264 source-work assertions
remain applicable and were not repeated. Production EXE and alpha are unchanged.

## Remaining acceptance

Next concrete work is this instruction's fresh-Start exit and fourth-attempt
entry, retaining two lives and the immediately preceding third game's animation
and partial-second state. Current controls do not press Start again. Other
stunt/player/shared-animation, genuine final-life/reset, earlier UI/LCD and
unobserved work remain separate. Production scheduler integration, full images/
PCM, human/device/independent-Windows tests and distribution remain open.
Timing point 1 and [final acceptance](ACCEPTANCE.md) remain incomplete.
