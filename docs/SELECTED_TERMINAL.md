# Complete initial selected Air attempt through its terminal wait

October 21, 2026: all eight original/native Air/easy cases match through their
actual failed-attempt completion and closed final counter wait, zero differences.
They follow selected one/two-player Start and full/held-skip instructions in both
retained histories. Completion counts are measured separately:

| Player choice / instructions | Ordinary history | Earlier-pause history |
|---|---:|---:|
| One player / full prompt | 2,355 | 2,328 |
| One player / held skip | 2,378 | 2,354 |
| Two players / full prompt | 2,355 | 2,358 |
| Two players / held skip | 2,358 | 2,355 |

This is the first player's first Air attempt, including the two-player selections.
It does not qualify the second player's subsequent turn. An initial assumption
that every case ended at 2,355 updates was rejected by the original. Separate
exploration measured the endpoints; exploration itself is not accepted evidence.
Each accepted case then received independently repeated uninstrumented prefix/
full controls and its own unchanged observed fingerprint.

Totals: 18,841 updates; 188,410 boundaries; 3,014,560 actor snapshots (912,816
occupied); 18,902 displays; 37,804 vectors; 756,080 sprite slots; 39,937,920 row/
map bytes. There are 636 requests/completions, 2,392 uploads and 523 map-deferred
displays, plus 62 sprite, 22 map and 190 placement interruptions and eight
partial-row displays. Counts overlap the earlier bounded extents and histories.
Inactive actor payloads and sprite tile bytes are not newly qualified.

Native actor completion independently sets the result. The verifier requires
that result at the explicitly requested extent, retains the closed resource gate
for the final counter wait and omits the next gameplay input test. An earlier
or missing native completion rejects the scope. Neither the requested count nor
original snapshots/queues set the native result or schedule its interrupts.
Original/native actors, timer, random state, resource work, display/input/audio
costs, sprite geometry and row storage are compared at the actual boundaries.

Every accepted first 32/320/640/1,216 source and native gameplay stream remains
unchanged. Source and native startup/before/after row snapshots through 1,216
are also retained byte for byte. The old row recording's final endpoint lies
inside the extended run; the extended recording has its own final endpoint.
Complete preceding native CSVs are unchanged. Row bytes use the explicit pinned
direct-storage observer; CPU read-block status remains recorded separately.

A newly measured STAT completion returns to 261c immediately before HALT,
100 cycles after the back edge; the existing first-HALT completion returns to
the same address four cycles later. The source adapter now distinguishes exact
semantic ownership (atomic completion versus counter wait). The comparison
previously inferred ownership from the address alone. It now uses the exact
already-validated boundary for each vector. Neighboring unowned times and a
display at this new prefix still reject. Native clock/gameplay code required
no adjustment; native edge tests independently distinguish both cases. No
cycle tolerance or correction was introduced.

Prepare `tools/selected_gameplay_reference.py prepare ROM --capture TEXT_CONTROL
--out PLAY_CONTROL --terminal --updates N`, using the measured extent for that
actual parent. Capture with the same N, `--accepted-control TEXT_CONTROL` and
`--parent-out GAME_ENTRY_REFERENCE`. Its explicit control marker selects the
terminal observation. Capture attached bytes with `tools/selected_map_reference.py`.
The native full-chain replay uses `--players-gameplay-terminal
--players-gameplay-updates N`; both are required and option order is independent.
Other complete-chain arguments remain those of [selected gameplay](SELECTED_INSTRUCTION.md).

The previous map/interruption manifest gains `interrupted_gameplay_out`,
`interrupted_gameplay_base`, `interrupted_gameplay_control` and
`interrupted_map_out` for the accepted 1,216-update parent, then new control,
gameplay/map outputs and native base paths. The existing gameplay/map comparators
check all earlier extents and exact parent identities. Inputs remain decoded
assets and raw buttons. Original recordings and reference binaries stay local.

Validation: all eight terminal/row comparisons, 1,877 Python tests and 593 native
access/clock checks pass. Fresh optimized native replays preserve all 494 complete
CSVs of both a terminal case and the earlier 1,216-update case. Invalid terminal
scope combinations reject before playback. The full native Windows game/
campaign/playthrough/audio/sprite regression passed at the preceding menu/text
checkpoint; this follow-up changes diagnostic adapters/qualification only.
The Windows EXE is rebuilt from the saved source revision.

The extent ends before outgoing fade/audio stop, result presentation/life
consumption, player selection/handoff and the next instruction/game. Other
stunts/difficulties/outcomes, modified scores, transition/gameplay pixels, PCM,
production scheduling and final device/Windows/distribution acceptance remain
open. See the [matrix](ORIGINAL_COMPARISON_SCOPE.md) and [acceptance](ACCEPTANCE.md).
The broader request and final version remain incomplete; no final release.
