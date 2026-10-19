# Restarted Air terminal update and outgoing fade

Follow-up: [restarted result setup, incoming fade and full failure hold](AIR_FOLLOWING_RESULT.md)
now attach to both outgoing endpoints. The counts below retain this earlier
terminal/outgoing checkpoint's scope.

October 19, 2026: both existing easy Air retry histories now match through the
terminal game update, final busy display wait, audio stop and complete outgoing
fade. The diagnostic stops before 0409's result setup. This extends the same
ordinary and entry-pause/resume controls from AIR_FOLLOWING_SCENES.md; it is
not a new difficulty, full-campaign or production-Windows timing qualification.

## Native ownership

The result is computed by the native actor logic. Only a newly completed stunt
can enter the terminal branch; requesting a terminal extent cannot force one.
The result read/rotate/untaken back-edge costs 28 cycles, versus the continuing
update's 32. The last counter-change wait keeps FFAE's graphics gate closed.
It publishes the terminal prepared object list, advances display/HUD/input/audio
and returns at 0403, 72 cycles after the recorded VBlank body end. It performs
neither the next ready-store pair nor the 48-cycle gameplay input gate. Queued
player graphics cannot upload during this busy display.

The outgoing transition inherits the resulting native clock, display counter,
input history, prepared objects and game state. The identified 12,384-cycle
audio-stop operation clears native audio, followed by a 44-cycle fade entry.
Eight 76-cycle palette stages each own four counter waits; continuation tails
cost 16, 28 or 40 cycles according to the source loop. Palettes come from locally
decoded UI assets. Each outgoing display keeps graphics uploads closed, samples
raw input, updates the HUD/counter and executes the silent audio callbacks.
STAT disables objects and VBlank enables them. The absolute continuing service
deadlines remain attached to the restarted LCD epoch.

The actor/resource body still requires quiet ownership. Identified scene work
can accept its already qualified source-completion interrupts. An interrupt in
partially reset audio or an outgoing palette/tail operation still rejects;
these controls only interrupt the outgoing counter waits. No original PC,
duration, outcome, palette measurement or memory snapshot drives native work.
There is no Game Boy CPU execution in the port or native diagnostic.

## Original comparisons

Both existing input-only long controls are reused without modifying original
RAM or replay events. Their uninstrumented hashes were already checked twice;
every new instrumented capture matches the corresponding full control-memory
digest. Original execution uses the separately authorized pinned local SameBoy
backend. Original snapshots, assets, recordings and emulator binaries stay local.

| Comparison | Ordinary retry | Entry pause/resume | Combined |
|---|---:|---:|---:|
| Updates including terminal update | 1,788 | 1,767 | 3,555 |
| Gameplay boundary comparisons | 17,880 | 17,670 | 35,550 |
| Actor slots | 286,080 | 282,720 | 568,800 |
| Occupied actor instances | 84,865 | 83,570 | 168,435 |
| Gameplay display services | 1,793 | 1,771 | 3,564 |
| Gameplay interrupt vectors | 3,586 | 3,542 | 7,128 |
| Outgoing phase intervals | 74 | 74 | 148 |
| Outgoing displays / vectors | 32 / 64 | 32 / 64 | 64 / 128 |
| Published object slots, gameplay + fade | 73,000 | 72,120 | 145,120 |
| Differences | 0 | 0 | 0 |

There are 31,997 distinct gameplay samples after removing adjacent end/begin
overlap. The 63 non-HALT scene/result/wait-prefix interrupts, 91 completed
graphics transfers, 342 upload batches and 54 map deferrals from the previous
checkpoint are retained; the terminal updates add no new transfers. These
totals include, rather than add to, the shorter accepted controls.

The terminal comparator requires the result bit to appear after actor
completion, remain stable through scene/wait and agree with native state at
every boundary. It validates the distinct terminal branch/wait costs and closed
gate. Existing actor, scalar, queue, service, input/audio-component and complete
vector comparisons remain mandatory for every update.

The outgoing comparator requires attachment to the accepted terminal endpoint,
all 74 phases, palette registers, counters, input edges, all 32 displays / 64
counter-wait vectors, inherited deadlines and final summary. Both gameplay and
outgoing comparisons require every published 40-object list. Presence and live
X/Y/flags match; unused payloads and tile indices remain excluded. Complete
map/VRAM/color-buffer bytes, rendered images, bus-level palette timing, audio
reset memory layout and PCM are not certified here.

## Validation and reproduction

The optimized native diagnostic passes both complete controls through 0409.
All 553 Python tests pass, including 35 new terminal/outgoing integrity cases.
The native handoff/pause/exit suite passes 863 assertions, including an unfinished
stunt's rejection, closed terminal/outgoing graphics gates, retained display
edges, silent callback work, exact deadlines and interrupted-audio rejection.
Both earlier 1,000-update resource comparisons and all four preceding startup/
exit comparisons remain exact. Core gameplay/runtime code is unchanged; the
previous 4,200 source-work and 819,624 Air-rule assertions remain applicable
and were not rerun without a production change.

Build with `tools/build_air_clock_probe.py`. Capture using
`tools/air_following_gameplay_reference.py capture` with `--updates N --outro`
(or `--terminal` to stop at 0403). Replay raw buttons with `--following-gameplay
--following-updates N --following-outro`; add `--following-entry-pause` for the
paused control. Terminal-only native playback uses `--following-terminal`.
The explicit last-update flag rejects an earlier or later terminal outcome.

Run `tools/air_following_resource_reference.py` on `.following-gameplay.csv`
with the usual startup/entry summaries; it includes all gameplay publications.
Run `tools/air_following_outro_reference.py` on `.following-outro.csv`, using
`.following-gameplay.summary.csv` as `--entry-summary` and the same verified
control/startup/capture folder. The outgoing comparator additionally requires
the sibling services, interrupts, sprites and summary files. Mixed controls,
missing coverage, stale deadlines and detached entry state reject.

Local accepted evidence uses `local/air-following-outro-reference/` and
`local/air-following-outro-services.csv*`, with the unchanged
`local/sameboy-air-resource-long-control/` and
`local/air-following-resource-long-startup/`. Paused evidence uses
`local/air-following-outro-pause-reference/` and corresponding native files,
`local/sameboy-air-scene-pause-long-control/` and
`local/air-following-scene-pause-startup/`. Terminal-only captures/native outputs
use `local/air-following-terminal*`; regression logs use `local/air-terminal-*`.

## Remaining timing work

Result setup, incoming transition and full failure hold are now qualified in
AIR_FOLLOWING_RESULT.md for these two failure controls. Attach the following
campaign/instruction handoff using the remaining three lives. Then qualify following Ski and
changed-player/shared-animation paths, genuine final-life/reset, earlier UI/LCD
entry and unobserved work. Production scheduler integration and the remaining
image/audio, human/device/independent-Windows and distribution gates in
ACCEPTANCE.md remain required. The production EXE and versioned alpha are
unchanged. Timing point 1 and final-release acceptance remain incomplete.
