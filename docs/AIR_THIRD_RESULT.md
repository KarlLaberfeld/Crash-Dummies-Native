# Complete third Air failure, outgoing fade and result

October 19, 2026. Native diagnostic qualification, not production Windows
scheduler acceptance. Both easy Air histories now continue from their accepted
[1,000-update prefixes](AIR_THIRD_GAMEPLAY.md) through terminal gameplay, outgoing
fade, common result setup, incoming fade and complete failure hold at 0514.
Each result consumes exactly one inherited life: three before, two afterwards.

## Compared scope

| Scope | Ordinary history | Prior entry-pause history |
| --- | ---: | ---: |
| Third-attempt updates | 1,789 | 1,604 |
| Gameplay boundaries / actor slots | 17,890 / 286,240 | 16,040 / 256,640 |
| Gameplay displays / complete vectors | 1,794 / 3,588 | 1,618 / 3,236 |
| Gameplay published object slots | 71,760 | 64,720 |
| Resource requests / completions | 46 / 46 | 35 / 35 |
| Outgoing phases / displays / vectors | 74 / 32 / 64 | 74 / 32 / 64 |
| Result prefix boundaries / line polls | 11 / 2,121 | 11 / 2,122 |
| Incoming/hold boundaries / displays / vectors | 1,048 / 514 / 1,028 | 1,048 / 514 / 1,028 |
| Row-storage boundaries / bytes | 3,594 / 3,795,264 | 3,242 / 3,423,552 |
| Differences | 0 | 0 |

Gameplay totals: 33,930 boundaries, 542,880 actor slots, 3,412 displays and
6,824 vectors. Outgoing totals: 148 phases, 64 displays, 128 vectors and 2,560
object slots. Result totals: 22 prefix boundaries, 4,243 polls, 2,096 incoming/
hold boundaries, 1,028 displays and 2,056 vectors. Complete row comparisons add
6,836 boundaries / 7,218,816 bytes, from LCD enable through terminal return.
Do not add the paused resource report's row totals again: they are the same row
evidence. Gameplay includes the previously accepted 1,000 updates per history;
earlier campaign/result/instruction/entry coverage is repeated attachment proof.

The ordinary/paused inherited timer phases remain 54/33. Terminal values are
14/48. Their differing paths and completion counts come from native game state;
recorded update counts select only the diagnostic endpoint, not game outcomes.
Native terminal ownership rejects an unfinished stunt, takes the busy result
branch and omits a continuing-gameplay input test. Outgoing work retains the
closed resource gate and its current LCD epoch. The subsequent result owns its
new LCD deadlines, input/audio, life decrement and complete 480-display hold.

## New bounded owners and storage correction

The ordinary history exposes two STAT returns inside the shared offset helper
at 0020/0021 during placement allocation. The observer now retains its nested
caller. Comparison accepts the bounded 0020..0022 helper only in placement
phase, with a closed resource gate and caller 1ae0. Existing native placement
work already splits this table-offset operation into completion boundaries;
no reference return address is passed into native scheduling. Placement's
parameter-copy tail through 1b0e is also identified in the paused history.

The paused history additionally exposes two VBlank services during row
preparation, at 1f0a and 1eb8. Native following setup now retains its source-owned
32-byte staging buffer and 32x32 published background between updates. Each
completed byte store updates staging; a display copies the current staged row,
including old bytes or an older destination when preparation is unfinished.
Later stores cannot retroactively change the published tiles. Partial-row
acceptance additionally requires owned instruction-background history.

Byte comparison exposed a second issue: startup's 32 iterations leave ring row
22 unwritten for this level. That row still contains the preceding instruction
text. Initializing the native published map with zeros produced six mismatching
early boundaries. The next-instruction adapter now projects background clearing,
header/picture/text stores into native storage; prompt stores preserve/update it
through exit. Stage initialization overlays only the rows it actually prepares.
The retained instruction row is then overwritten by a later gameplay row, just
as in the original. No original tile or snapshot initializes native storage.

Row snapshots start at 03c6, before the two entry displays, while VRAM is readable.
All before/after-transfer snapshots use unblocked original reads. The ordinary
terminal endpoint occurs while CPU-style VRAM reads are blocked: its report
explicitly marks retained tile evidence from the final unblocked transfer,
across an observed interval with zero background-VRAM write attempts. RAM
staging and scalar values are read at the endpoint. Arbitrary blocked reads
still reject; this is not a claim that a blocked read returned real tile data.
The paused endpoint is directly readable. Full images/PCM remain outside scope.

## Control integrity and reproduction

Append 1,000 unchanged held-A/Left, released-Start frames to each accepted
extended third-attempt control. Preserve all earlier events, setup state and
input file. Two uninstrumented replays agree per new control and retain its
accepted parent's full RAM digest at that endpoint. Instrumented captures match
the new full final digest. ROM, snapshots and extracted data stay local.

Capture startup into a fresh folder. In the same new reference folder run:

- `air_following_gameplay_reference.py capture --next-retry --updates N --outro --busy-scenes`; add `--partial-rows` for the paused history.
- `air_map_reference.py capture --next-retry`.
- `air_result_prefix_reference.py capture --next-retry`.
- `air_result_transition_reference.py capture --next-retry --failure-hold` last, to retain all raw input samples.

Tools are under `tools/` and take the usual ROM/control/output arguments.
N is 1,789 ordinary / 1,604 paused. Build with `tools/build_air_clock_probe.py`.
Replay with `--following-gameplay --following-updates M --next-retry
--next-updates N --next-result`, retaining `--following-entry-pause` for the
paused history. M remains 1,788 / 1,767 for the preceding second attempt.
`--next-terminal` stops after the outgoing fade without entering the result.

Run `tools/air_third_result_reference.py NATIVE_BASE` with matching new
`--capture`, `--out`, `--startup`; accepted 1,000-update `--accepted-base`,
`--accepted-capture`, `--accepted-out`, `--accepted-startup`; and the explicit
first-entry/start/parent arguments used by `air_third_gameplay_reference.py`.
The verifier reruns that complete accepted chain, requires unchanged original
and native 1,000-update prefixes, then invokes strict resource/object, outgoing,
result and row-storage comparators. Partial-row resource comparison cannot pass
without matching row evidence. Mixed controls, missing ownership/storage,
incomplete holds, altered life counts and truncated prefixes reject.

Local controls are `local/sameboy-air-third-result-control/` and the pause variant;
observations/startups use `local/air-third-result-reference/`,
`local/air-third-result-startup/` and pause variants. Native outputs use
`local/air-third-result-services.csv*` and the pause variant. The final sibling
report is `.third-result.comparison.json`. All original recordings remain ignored.

Validation: optimized native diagnostic; 52,920 result, 883 handoff/exit and
4,264 source-work assertions; 698 Python tests. Both accepted entry/1,000-update
chains, both prior resource controls, four startup/exit controls and the earlier
successful gameplay/IRQ/result control pass. Legacy `--following` result captures
remain identical to their accepted recordings after the new retry selector.
Core gameplay rules are unchanged; their prior assertions were not repeated.

## Remaining acceptance

The next two-life campaign/instruction handoff is now qualified through its
complete text in the [next checkpoint](AIR_TWO_LIFE_INSTRUCTION.md). The
paragraph below records this third-result checkpoint's original boundary.

Next: attach the third failure's two-life result to its next campaign/instruction
handoff using the just completed native game and result state. Changed-player/
shared-animation, following Ski, genuine final-life/reset, earlier UI/LCD and
unobserved work remain separate tasks. Production scheduler integration, full
image/audio fidelity, human/device/independent-Windows and final distribution
gates remain open. Production EXE and versioned alpha are unchanged. Timing
point 1 and [final acceptance](ACCEPTANCE.md) remain incomplete.
