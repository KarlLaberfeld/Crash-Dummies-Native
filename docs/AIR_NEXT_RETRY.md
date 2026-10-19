# Second Air retry: prompt, setup, entry and first update

October 19, 2026. Native diagnostic continuation, not production scheduler
acceptance. This extends [the next instruction](AIR_NEXT_INSTRUCTION.md) through
fresh Start, all outgoing instruction waits, masked stunt initialization, LCD
restart and the third Air attempt's first update/next input gate.

## Controls and results

Both existing easy Air histories are retained: ordinary retry, and retry with
an entry pause/resume in the second attempt. After the unchanged 4,200-frame
parent interval, append one frame of Start, release Start and run 300 frames.
A/Left remain held. No memory, lives, timer, seed or animation state is injected.
Two uninstrumented replays agree for each child; their full parent-prefix RAM
hashes equal the accepted parent control. Instrumented captures retain the
child's complete final control hash. Parent recordings keep their own hashes.

| Newly compared scope | Ordinary | Prior entry pause |
| --- | ---: | ---: |
| Instruction exit boundaries | 2,432 | 2,576 |
| Masked prefix boundaries | 5 | 5 |
| Stage setup boundaries | 14 | 14 |
| LCD entry boundaries | 12 | 12 |
| First update boundaries / actor slots | 10 / 160 | 10 / 160 |
| Total display services / complete vectors | 1,208 / 2,416 | 1,280 / 2,560 |
| Readiness/line polls / stores | 1,847 / 532 | 1,847 / 532 |
| Differences | 0 | 0 |

Combined new scope: 5,090 boundaries, 2,488 displays, 4,976 vectors, 3,694 polls,
1,064 stores and 320 actor slots. Long prompt waits are included in these totals;
they do not represent additional gameplay. Earlier second-attempt gameplay,
outgoing/result and next-instruction comparisons are rerun against their accepted
parent recordings and overlap the previous milestones.

Both campaigns retain three lives. The third attempt inherits partial-second
values 54 / 33 from the immediately preceding attempt, rather than the first
attempt or a fresh zero. The first update preserves those values, changes the
player from Intro to Rise and retains native timer, input, seed, HUD/fade, map
gate and LCD deadlines. Animation inheritance is checked across all sixteen
blocks in synthetic native tests; original first-update comparisons cover live
actors and relevant animation flags/delay/period, excluding raw script pointers
and unused vacant payloads.

## Allocation selector correction

The paused history exposed a wrong assumption: sprite allocation direction was
inherited from the completed Air game. Source 0387 explicitly clears that
selector after masked stage initialization. The original paused history has a
reversed selector at stage entry and song startup, then zero at 039c. Native
handoff now uses the explicit reset; animation blocks and partial-second state
still inherit independently. Both first updates start with forward allocation
and select reversed allocation during sprite preparation. The ordinary control
alone could not expose this error because its predecessor already had zero.

Stage capture records the selector and requires the final reset. Synthetic
tests reject a missing observation or an uncleared selector and distinguish
the immediately preceding animation/timer source from its ancestor.

## Reproduction and integrity

Keep the pinned SameBoy reference backend separate from native execution.
Create the child controls with identical setup state/input file and the exact
event extension above. Capture startup into a fresh child startup folder. Use
the same child ROM/control with these capture tools, into a fresh reference
folder; capture gameplay last to retain the complete raw input extent:

- `air_instruction_exit_reference.py capture --following`
- `air_following_setup_reference.py capture --next-retry`
- `air_following_stage_reference.py capture --next-retry`
- `air_following_entry_reference.py capture --next-retry`
- `air_following_gameplay_reference.py capture --next-retry` (default one update)

Tools are in `tools/`; all take the usual ROM, `--capture` and `--out` arguments.
Build with `tools/build_air_clock_probe.py`. Replay the child input history with
`--following-gameplay --following-updates N --next-retry`; N remains 1,788
ordinary / 1,767 paused, with `--following-entry-pause` only for the latter.
The native probe consumes button samples, decoded assets and its own returned
states; it loads no reference times, outcomes, snapshots or per-update counters.

Run `tools/air_next_retry_reference.py NATIVE_BASE` with `--capture`, `--out`,
`--startup`, `--parent-capture`, `--parent-out` and `--parent-startup`. The verifier
requires unchanged parent setup/input bytes, event-prefix identity, matching
backend/ROM and repeated prefix/final hashes. It runs four strict parent and
five child comparisons, joins original endpoints/campaign/input/service origins
and rejects detached or incomplete evidence. The result is the sibling
`.next-retry.comparison.json`. All component reports remain available.

Local child controls: `local/sameboy-air-next-start-control/` and
`local/sameboy-air-next-start-pause-control/`. Child observations/startups use
`local/air-next-start-reference/`, `local/air-next-start-startup/` and pause
variants. Native outputs use `local/air-next-start-services.csv*` and the pause
variant. These controls, original recordings, binaries and assets remain local.

Validation: O2 native diagnostic; 52,878 result-clock, 882 handoff/exit and 4,200
source-work assertions; 647 Python tests. Both preceding 1,000-update resource
controls, four startup/exit controls and the earlier genuine successful Air
gameplay/IRQ/result control pass. Core gameplay rules are unchanged; the earlier
819,624 assertions remain applicable and were not repeated.

## Remaining acceptance

Third-attempt timer/resource continuation is now qualified through 1,000 updates
per history in the [next checkpoint](AIR_THIRD_GAMEPLAY.md). The paragraph below
records this entry milestone's original remaining boundary.

The next bounded continuation is third-attempt gameplay beyond the first update,
especially timer rollover and interrupted work with its inherited 54/33 phase.
Following Ski, changed-player/shared-animation, genuine final-life/reset, earlier
UI/LCD and unobserved work still require their own qualified paths. Production
Windows scheduling, complete images/PCM, human/device/independent-Windows tests
and final distribution remain open. Production EXE and alpha are unchanged;
timing point 1 and final acceptance remain incomplete. See [acceptance](ACCEPTANCE.md).
