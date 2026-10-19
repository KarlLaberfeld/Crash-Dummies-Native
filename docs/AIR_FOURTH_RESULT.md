# Complete fourth Air failure and one-life result

October 19, 2026. Extends both accepted
[fourth-attempt continuations](AIR_SIDE_PUSH_INHERITANCE.md) through terminal
gameplay, outgoing fade, result setup/incoming and the complete failed-result
hold at 0514. Lives decrease from two to one. This does not enter the following
one-life instruction or qualify the final attempt/eliminated-player paths.
Production Windows scheduling and the versioned alpha remain unchanged.

## Accepted scopes

| Gameplay scope | Ordinary | Earlier second-entry pause | Combined |
|---|---:|---:|---:|
| Fourth updates, including earlier 1,000-update prefix | 1,788 | 1,764 | 3,552 |
| Boundaries | 17,880 | 17,640 | 35,520 |
| Actor slots | 286,080 | 282,240 | 568,320 |
| Display services | 1,793 | 1,768 | 3,561 |
| Complete vectors | 3,586 | 3,536 | 7,122 |
| Published object slots | 71,720 | 70,720 | 142,440 |
| Row boundaries, including two entry displays each | 3,592 | 3,542 | 7,134 |
| Row staging/tile bytes | 3,793,152 | 3,740,352 | 7,533,504 |

All compared fields have zero differences. Outgoing adds 148 phases, 64 display
services, 128 vectors and 2,560 published object slots. Complete result scope
adds 22 setup boundaries, 4,242 line polls, 2,096 incoming/hold boundaries,
1,028 displays and 2,056 vectors. Each result begins with two lives and returns
with exactly one. These are the same two input histories; earlier 1,000-update,
entry and campaign scopes overlap previous acceptance.

Persistent native row storage matches every recorded entry/gameplay publication.
The ordinary terminal VRAM endpoint is readable. The paused terminal endpoint
is blocked and explicitly retains the last unblocked tile array only across an
observed zero-write-attempt interval; RAM staging is read at the endpoint.
No general blocked-VRAM read claim is made. Matching row evidence is mandatory
for the partial-row gameplay scope, and object publication is compared as part
of the busy-scene resource comparison.

## Exact first-HALT STAT boundary

The ordinary history's zero-based update 1317 reaches a STAT request exactly
at the first HALT completion. The source trace shows ready publication, CALL,
PUSH, saved-counter read, LD B and HALT. STAT enters 20 cycles after that edge;
RETI returns to 261c HALT itself. There is no 261d counter read, comparison or
conditional branch between STAT return and re-entering HALT. The next VBlank
increments the saved counter, then the ordinary final read/test/return runs.

Native `AirClock::wait` already owned the vector and following display timing;
it now also omits the inappropriate 32-cycle test tail when its own STAT
deadline lands at that HALT boundary. It records 124 active wait cycles rather
than the ordinary 156; idle time and IRQ bodies remain separate. It does not
read the observed PC, a recorded cycle target or an update index.

The source analyzer admits this return only for STAT with ready=1 at the exact
first-HALT prefix: 8+12 ready setup, 24 CALL, 16 PUSH, 16 read, 4 LD B, 4 HALT,
20 vector entry after the back edge. It assigns the counter-wait owner and
requires its normal zero-lag deadline. Arbitrary 261c returns, a request inside
LD B, a closed gate or a display-edge case are not opened by this acceptance.
Synthetic neighboring requests distinguish saved-counter completion, exact
HALT entry and later sleeping wake (120 / 124 / 156 active cycles), with the
same later display endpoint. This qualifies the pinned DMG reference behavior;
independent hardware coverage remains open.

A separate read-only original execution trace confirms that sequence and
matches the unchanged full-control digest. The original source work is a
comparison target, never an input to native scheduling. This is a bounded
semantic wait algorithm, with no Game Boy CPU execution in the port.

## Controls, capture and replay

Each child preserves the complete accepted fourth-gameplay parent events,
setup state and initial input file, then appends exactly 1,000 unchanged-input
frames. Start remains released and A/Left remain held. Two independent
uninstrumented replays match the parent full-RAM digest at the attachment and
the new child digest at the endpoint. No RAM/seed/life injection is used; each
instrumented recording matches that child digest and the pinned backend.

Capture startup into a fresh folder. In a new result reference folder run the
following tools under `tools/`, with the usual ROM, `--capture` and `--out`:

- `air_following_gameplay_reference.py capture --next-retry --after-retry 2 --updates N --outro --busy-scenes --partial-rows`
- `air_map_reference.py capture --next-retry --after-retry 2`
- `air_result_prefix_reference.py capture --next-retry --after-retry 2`
- `air_result_transition_reference.py capture --next-retry --after-retry 2 --failure-hold` last, retaining all raw button samples.

N is 1,788 ordinary / 1,764 paused. Result selection waits for the third retry
entry before arming the fourth result; map/gameplay selection retains the
existing fourth-entry generation. A later result requires explicit next-retry
ownership. Default capture behavior remains unchanged; legacy third-result
map/prefix/transition JSONs reproduce exactly.

Build using `tools/build_air_clock_probe.py`. Keep the accepted fourth replay's
earlier-game extents and pause flag, supply the new result `buttons.txt`, and
use `--fourth-result --fourth-updates N` alongside `--next-retry` and
`--following-gameplay`. Earlier second-game extents remain 1,788 / 1,767;
third-game extents remain 1,789 / 1,604. The bounded child now owns its result,
but cannot recurse into another instruction/game. New result siblings are
`.fourth.next-outro*`, `.fourth.next-result*` and `.fourth.next-incoming*`.

Run `tools/air_fourth_result_reference.py NATIVE_BASE` with current `--capture`,
`--out`, `--startup`; accepted 1,000-update `--accepted-base`,
`--accepted-capture`, `--accepted-out`, `--accepted-startup`; and the first-entry/
parent/instruction arguments from `air_fourth_gameplay_reference.py`. It reruns
the accepted continuation chain under its original hashes, preserves complete
original/native prefixes, requires the fourth generation and two-to-one life
transition, then invokes strict resource/object, outgoing, result and row
comparators. Its report is `.fourth-result.comparison.json`.

Local controls: `local/sameboy-air-fourth-result-control/` and pause variant.
Recordings/startups use `local/air-fourth-result-reference/`,
`local/air-fourth-result-startup/` and pause variants. Native bases use
`local/air-fourth-result-services.csv*` and the pause variant. The retained
HALT-edge execution trace is local. ROM, decoded assets, recordings, reference
library and diagnostic binaries remain ignored/local.

Validation: optimized native Windows diagnostic, both complete attached chains,
52,920 result-clock / 580 pause-access / 927 handoff / 4,281 source-work
assertions, 777 Python tests, result ownership guard and three unchanged
default next-retry capture JSONs. The shared wait refinement justifies the
broader result/pause checks; unrelated core gameplay assertions were not
repeated. Earlier/first-update native scope counts are 222 / 226 files.

Next: attach the completed one-life result to its campaign/instruction using
the current native game and timing/input/row/scratch state. Final attempt,
eliminated-player/game-over, unused vacant done flags, other stunt/player/UI/
reset paths, unobserved work, production scheduling, full images/PCM and final
human/controller/independent-Windows/distribution checks remain open. Timing
point 1 and [final acceptance](ACCEPTANCE.md) are incomplete; automation is ACTIVE.
