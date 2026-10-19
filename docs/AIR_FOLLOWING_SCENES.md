# Interrupted scene work in restarted Air gameplay

Follow-up: [terminal update and outgoing fade](AIR_FOLLOWING_TERMINAL.md) extend
both histories through the final busy display and complete outgoing transition.
The table below retains this earlier continuing-update checkpoint's scope.

October 19, 2026: the ordinary easy Air retry now matches all 1,787 continuing
updates before its terminal update. The entry-pause/resume variant matches
1,766 continuing updates. Both include source-completion interrupts during
scene preparation, placement scanning, result testing and counter-wait entry.
These are extensions of the preceding resource controls, not additional games.
The production Windows scheduler is still outside this diagnostic acceptance.

## Native behavior

The previously open ordinary update 1,296 has a STAT interrupt during map-row
preparation and a VBlank during placement scanning. Its gameplay resource gate
stays closed. That display still publishes the prepared objects, samples input,
updates the HUD/counter, consumes the actor's requested effect and advances
music. The following counter wait owns another display before gameplay resumes.
Treating this interval as exactly one display per game update was insufficient.

The following clock now uses the existing source-completion algorithms for
sprites, unused-object clearing, map preparation and placements. Services can
run at their identified completion boundaries. Actor/resource calculation still
requires a quiet body. A VBlank during an unfinished staging-row copy still
rejects: it requires separate storage-publication ownership.

Busy displays call the native display callback with its resource gate closed;
they cannot prematurely upload a queued player frame. Scene timing retains
object disabling at STAT and re-enabling at VBlank. HUD progress refresh also
clears the shared placement lower-range scratch, so later range reads observe
the same value as the original. Interrupts in the result-read/rotate/back-edge
test and early wait prefix keep their individual source completion costs.

No original return address, recorded duration, per-update counter or observed
state selects native work. Native state, decoded assets, raw display-sampled
buttons and the continuing source LCD deadlines determine the replay.

## Original comparisons

The ordinary held-input control from the resource checkpoint is reused. The
paused control extends only its final held-input interval. Two uninstrumented
repetitions of that extended control agree on the complete terminal memory
hash; every instrumented capture agrees with its corresponding control.
Reference execution uses the separately authorized pinned local SameBoy backend.
No gameplay RAM/lives/seed is injected, and no emulator enters the port.

| Comparison | Ordinary retry | Entry pause/resume | Combined |
|---|---:|---:|---:|
| Continuing game updates | 1,787 | 1,766 | 3,553 |
| Boundary comparisons | 17,870 | 17,660 | 35,530 |
| Actor slots | 285,920 | 282,560 | 568,480 |
| Occupied actor instances | 84,845 | 83,550 | 168,395 |
| Complete display services | 1,792 | 1,770 | 3,562 |
| Complete interrupt vectors | 3,584 | 3,540 | 7,124 |
| Vectors at source completions outside the HALT wait | 34 | 29 | 63 |
| Requested / completed graphics transfers | 46 / 46 | 45 / 45 | 91 / 91 |
| Display upload batches | 174 | 168 | 342 |
| Map-priority resource deferrals | 28 | 26 | 54 |
| Published object slots | 71,680 | 70,800 | 142,480 |
| Differences | 0 | 0 | 0 |

Adjacent end/begin boundaries overlap: 31,979 samples are distinct. Earlier
resource and quiet-update experiments overlap these totals. The two histories
are still continuations of the same preceding easy Air retry with different
entry-pause/display histories; they do not qualify other difficulties or an
entire campaign. Both stop with 17 seconds left, before the terminal update.

The comparator requires every state boundary, actor slot, display and complete
vector in the declared extent. It checks exact native vector acceptance times
and source-completion/counter-wait ownership, absolute continuing deadlines,
counter/input/effect changes at intermediate boundaries, component audio/display
work, resource queue transitions and final summary attachment. Unobserved actor
or resource interrupts and displays during partial row staging reject.

Each original VBlank also records the prepared 40-object list before DMA.
The native list published at the same display matches allocation/presence and,
for present objects, X, Y and flags. This includes partially cleared/prepared
lists at interrupted scene boundaries. Unused-slot payloads and tile numbers
are excluded; decoded color-buffer contents, map/VRAM bytes, rendered pixels,
palette microtiming and PCM are not certified by this comparison.

## Tests and reproduction

The optimized native diagnostic and 683 handoff/pause assertions pass. All 518
Python tests pass, including 32 new synthetic scene-integrity tests for extra
services, object disable/enable, consumed effects, counter continuity, result
test costs, resource gating, bounded acceptance latency and sprite publications.
The two earlier 1,000-update resource controls and all four preceding original
startup/exit comparisons also pass with this rebuilt diagnostic. Native rule/
runtime code is unchanged; the preceding 4,200 source-work and 819,624 Air-rule
assertions remain applicable and were not rerun without a production change.

Use `tools/build_air_clock_probe.py` for the native diagnostic. The original
capture command `tools/air_following_gameplay_reference.py capture` now accepts
`--busy-scenes` (which includes resource-transfer observations). Supply a fresh
local output directory, original control and `--updates N`. Replay with
`--following-gameplay --following-updates N`, adding `--following-entry-pause`
for the paused variant. `tools/air_following_resource_reference.py` performs the
comparison and, for this scope, also requires the sibling `.sprites.csv` output.

The scene analyzer uses original return addresses only to reject observations
outside the identified native source algorithms. It never supplies them to the
native executable. Counts are derived from recorded services, rather than an
assumed one-display-per-update relationship; mixed hashes/backends, missing
vectors, stale deadlines and incomplete publication files reject.

Accepted ordinary evidence is under `local/air-following-scene-full-reference/`
and `local/air-following-scene-full-services.csv*`, using the unchanged
`local/sameboy-air-resource-long-control/` and its startup epoch. Paused evidence
is under `local/air-following-scene-pause-reference/` and corresponding native
outputs, using `local/sameboy-air-scene-pause-long-control/` and
`local/air-following-scene-pause-startup/`. All original snapshots, controls and
recordings remain ignored/local. Tests and regression logs use
`local/air-scene-*`.

## Next work

The ordinary 1,788th and paused 1,767th updates terminate the stunt. Their
terminal update, final busy display wait and outgoing fade are now separately
qualified in AIR_FOLLOWING_TERMINAL.md. Result setup/incoming/accounting and
the subsequent handoff still need attachment to this restarted LCD epoch.

Following Ski and changed-player/shared-animation ownership, genuine final-life/
reset, earlier UI/LCD entry, other unobserved interrupted work and production
Windows scheduler integration remain open. Full images/audio, human/device/
independent-Windows and final distribution gates in ACCEPTANCE.md still apply.
Timing point 1 and the final release are incomplete.
