# Restarted Air gameplay resource timing

The subsequent [interrupted-scene checkpoint](AIR_FOLLOWING_SCENES.md) extends
these controls through the remaining continuing updates and qualifies the
previously open map/display/placement interruption. The scope below is the
earlier resource checkpoint and overlaps that later evidence.

October 19, 2026: the ordinary easy Air retry now agrees with the original
through 1,295 complete updates, and the entry-pause/resume variant through
1,000 updates. These extend the two existing 266-update controls. They qualify
resource requests, deferred display uploads and pose publication in the native
diagnostic. The production Windows scheduler is not yet using this clock.

## Native completion order

The actor update can request a dynamic player frame before the resource
callback restores the previous visible frame. The diagnostic previously
rejected such outcomes and only exposed the already-restored actor state.
`AirGame::resourceInputEntities` now retains the actor outcome immediately
before that callback, when source-work measurement is enabled. The following
clock exposes this state at `entitiesDone`, then commits the native resource
queue and restored pose at callback completion, before sprite preparation.

The callback body must still complete without an interrupt. Its existing
source-derived completion durations are charged separately; an interrupt
crossing remains rejected rather than receiving an invented timing allowance.
The normal game's resource algorithm and visible behavior are unchanged.

Following updates now retain busy and completed queues across counter waits.
The native display callback uploads at most four decoded chunks per display,
defers the upload when a background row has priority, and publishes the new
frame and flags only with the final resource-buffer swap. The next resource
callback consumes the completion acknowledgement. Costs and state transitions
come from native handlers, decoded descriptors and display work; original
recorded times, queue states and actor snapshots never drive native playback.

## Independent comparison and scope

Both extended controls preserve their existing setup and ordinary button events.
Only the final held-input interval is longer. Two uninstrumented repetitions
of each extended control agree on the complete terminal 32-KiB memory hash.
Instrumented recordings independently reproduce that terminal hash using the
pinned SameBoy backend. No gameplay RAM, lives or seed is injected. SameBoy is
used only for the separately authorized comparison, outside the native port.

| Comparison | Ordinary retry | Entry pause/resume | Combined |
|---|---:|---:|---:|
| Complete following updates / displays | 1,295 | 1,000 | 2,295 |
| Boundary comparisons | 12,950 | 10,000 | 22,950 |
| Actor-slot comparisons | 207,200 | 160,000 | 367,200 |
| Occupied actor instances | 54,172 | 40,213 | 94,385 |
| Complete interrupt vectors | 2,590 | 2,000 | 4,590 |
| Requested / completed graphics transfers | 27 / 27 | 21 / 21 | 48 / 48 |
| Display upload batches | 102 | 79 | 181 |
| Displays deferring a transfer for a map row | 20 | 14 | 34 |
| Differences | 0 | 0 | 0 |

Adjacent `end` and `begin` comparisons overlap: 20,657 boundary samples are
distinct. The earlier 266-update controls and intermediate 290/300/360/1,000
experiments overlap these totals and are not additional independent coverage.
These remain two continuations of the same preceding easy Air retry, with
different entry pause/display histories; they do not qualify other difficulties
or an entire campaign. Their ending timers are respectively 23 and 28 seconds.

The comparator checks complete boundary/actor/display/vector coverage, inherited
timers and input history, absolute LCD deadlines, map gates, queued effects and
audio work. It additionally validates the original queue transitions against
locally decoded descriptors: no early request commit, unrelated actor change,
lost chunk, upload during map priority, early pose or missing completion is
accepted. Busy queue frame/flag fields are compared explicitly. Unused initial
queue scratch and the previously excluded script pointers/vacant payloads remain
outside the claim. Full graphics-buffer bytes, rendered images and PCM are not
compared by this extension.

## Verification and local reproduction

- 486 Python tests pass, including 24 new resource-integrity cases.
- The optimized native handoff suite passes 683 assertions, including a
  synthetic 13-chunk request, map-priority deferral, four display uploads,
  atomic frame/flag/buffer publication and acknowledgement cleanup.
- The source-work suite passes 4,200 assertions; the complete native Air suite
  passes 819,624 assertions, including all 64 recovery phases and input-only
  successes at all four difficulties.
- Four preceding original startup/exit controls (retry and three Ski entries)
  remain exact with the rebuilt diagnostic.

Build the diagnostic with `python tools/build_air_clock_probe.py`. Capture a
local original control with `tools/air_following_gameplay_reference.py capture`
and `--resource-transfers --updates N`. Replay with `--following-gameplay
--following-updates N` (also `--following-entry-pause` for that variant).
`tools/air_following_resource_reference.py` compares the resulting following
CSV against its capture, startup epoch and entry summary. Like the previous
tools, it requires matching backend/ROM/control hashes; a startup recording
from a shorter control must not be relabeled as the extended control.

All original data and logs remain ignored/local. The accepted ordinary control
is `local/sameboy-air-resource-long-control/`, with recordings under
`local/air-following-resource-1295-reference/` and native outputs prefixed
`local/air-following-resource-1295-services.csv`. The paused control is
`local/sameboy-air-resource-pause-extended/`, with corresponding
`local/air-following-resource-pause-extended-*` outputs. Test logs are
`local/air-resource-{python,native}-tests.log` and
`local/air-resource-prior-entry-regressions.log`.

## Next unqualified owner

The ordinary control's 1,296th update has its first non-wait interrupt:
STAT returns to the background preparation at `00:1f0e`, followed by additional
display/wait work. Its final state is not covered by the quiet-body acceptance.
The rejected 1,787-update recording is preserved under
`local/air-following-resource-1787-reference/gameplay.rejected.json`.
The longer 2,000-update request cannot complete: this original run stops
returning to the gameplay update gate after 1,787 completed continuations.
Its partial observations are explicitly saved as unaccepted in
`local/air-following-resource-2000-reference/gameplay.incomplete.json`; the
instrumented terminal hash still matches its unhooked control.

Next work is to qualify the interrupted map preparation, busy display and
placement/wait continuation, then the terminal retry/exit path. Later Air/Ski
and changed-player handoffs, genuine final-life/reset, earlier UI/LCD owners,
other unobserved work and production Windows scheduler integration remain open.
The final image/audio, human/device/independent-Windows and release gates in
ACCEPTANCE.md still apply. No final fidelity or new release is claimed.
