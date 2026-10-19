# Retained side push and fourth Air timing

October 19, 2026. Resolves the paused-history failure recorded in
[fourth Air continuation](AIR_FOURTH_GAMEPLAY.md). Both existing easy Air
histories now match 1,000 fourth-attempt updates. The cause was a lost native
scratch value at retry handoff; the source-work formula required no correction.
This does not complete timing point 1 or integrate the Windows scheduler.

## Source-backed cause and correction

Original FFCA retains the previous game's side-push state across result,
instruction and stage setup. The ordinary third game ends with zero; the paused
third game ends with four. Those values survive to the fourth entry and first
Play input. The native handoff copied animation and partial-second state but
`AirGame::start` had cleared this scratch. It now copies `preceding.lastForce`
alongside the other surviving fields, without loading any original snapshot.

At 6574 the left-steering helper first tests transfer state, then FFCA at 6578.
For nonzero FFCA, RET NZ at 657b returns before the rate test. That source body
costs 60 T-cycles: LDH/AND/untaken RET, then LDH/AND/taken RET. With zero FFCA
and zero rate it continues through LD HL, LD A,[HL-], AND and RET Z, costing
92. The existing `airInputWork` already distinguished these branches. Copying
the correct native state selects the original 60-cycle path in the paused
case, removing all seven 32-cycle boundary errors in update 263. No event
number, timestamp offset, tolerance or observed cycle budget drives execution.

Play clears FFCA only at 602d, after input and terrain-probe preparation:
602c XOR A plus 602d LDH takes 16 cycles, observed before 602f. Side pushes
later store 4 or -4 at 63d2/63d9; terrain bounce can also store 12. The inherited
field retains these semantic values; it is not merely a boolean timing switch.
Allocated actor state, counters, input, outcomes and object publication remain
owned by the existing native gameplay path.

## Accepted comparison scope

| Compared scope | Ordinary | Earlier second-entry pause | Combined |
|---|---:|---:|---:|
| Fourth updates, including accepted first update | 1,000 | 1,000 | 2,000 |
| Boundaries | 10,000 | 10,000 | 20,000 |
| Actor slots | 160,000 | 160,000 | 320,000 |
| Display services | 1,000 | 1,000 | 2,000 |
| Complete vectors | 2,000 | 2,000 | 4,000 |
| Published object slots | 40,000 | 40,000 | 80,000 |
| Supplemental side-push boundaries | 10,000 | 10,000 | 20,000 |
| Resource requests / completions | 20 / 20 | 21 / 21 | 41 / 41 |
| Resource uploads | 75 | 79 | 154 |
| Timer rollovers | 12 | 13 | 25 |

All compared fields have zero differences. Inherited phases 14 / 48 each
advance 738 times; first rollovers occur in zero-based updates 307 / 273.
All vectors in these extents are wait-owned. Complete prior entry/instruction
chains remain exact under their own hashes, and 220 / 224 earlier/first-update
native CSV scopes retain complete bytes or their explicit first-update prefix.
The supplemental side-push log is new and is checked independently.

The side-push observer replays the unchanged complete controls, reads FFCA at
every already-observed gameplay boundary, records the immediately preceding
failed terminal endpoint and instruments the first Wait-to-Play steering/clear
branches. Both hooked endpoints match the accepted full-control 32,768-byte
RAM hashes. Earlier repeated uninstrumented parent/child controls remain valid;
no control event, initial state, input file or hash was changed. Source cycle
targets select observations only; no source state/work is supplied to native
execution. Original recordings and the local phase/disassembly investigation
remain ignored/local.

## Reproduction and verification

Use the existing fourth-gameplay controls, source folders and replay arguments
from AIR_FOURTH_GAMEPLAY.md. Build the corrected diagnostic with
`tools/build_air_clock_probe.py` and replay each case under a fresh native base.
Use `--fourth-entry --fourth-updates 1000`, the existing raw gameplay buttons,
earlier game extents and the earlier entry-pause flag where required. The new
`.fourth.next-gameplay.side-push.csv` sibling records the native scratch at
every normal gameplay boundary. The same adapter also records the preceding
retry's native scratch without changing its execution.

Run the existing `tools/air_fourth_gameplay_reference.py` comparison with the
fresh native base and the unchanged accepted entry/parent paths. Both cases
must now pass the complete strict resource, actor, counter, object and native
prefix comparisons. The original failing outputs are retained separately;
the new replay does not overwrite them or relabel the old failure as success.

Capture supplemental observations using:

```text
python tools/air_side_push_reference.py capture ORIGINAL.gb --capture CONTROL --out GAMEPLAY_REFERENCE
```

This reads the matching existing `gameplay.json`; it needs one observed
Wait-to-Play transition and a pinned control-verified reference backend. Compare:

```text
python tools/air_side_push_reference.py compare NATIVE_SIDE_PUSH.csv --capture CONTROL --out GAMEPLAY_REFERENCE --startup STARTUP_REFERENCE
```

The observer validates inherited terminal
attachment, ordered boundary indices, source branch presence and duration,
zero-rate/transfer scope and the exact clear order before accepting native
timestamps and scratch values. Recordings never enter native replay inputs.

Local fresh bases are `local/air-side-push-services.csv*` and
`local/air-side-push-pause-services.csv*`. Source folders are the unchanged
`local/air-fourth-1000-reference/` and pause variant, with new `side-push.json`.
Original failing native outputs remain under their previous fourth-1000 bases.

Validation: optimized native Windows diagnostic; both complete attached
1,000-update comparisons and 20,000 supplemental side-push observations;
927 synthetic handoff assertions, 4,272 source-work assertions and 757 Python
tests. Synthetic cases exercise -4/0/4/12 retention and both steering branches;
they are not additional original gameplay histories. Unchanged result/core
assertions were not repeated. Production EXE, scheduler and alpha are unchanged.

Remaining: later fourth-attempt terminal/outgoing/result work, initial unused
vacant done flags, other stunt/player/final-life/reset/UI paths, unobserved
interruptions, full map/image/PCM comparisons, production scheduling and final
human/controller/independent-Windows/distribution gates. Timing point 1 and
[final acceptance](ACCEPTANCE.md) remain incomplete. Automation remains ACTIVE.
