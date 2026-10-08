# Following Air restart through quiet gameplay

The native diagnostic now continues two easy Air retry variants through 266
updates each: ordinary entry and entry pause/resume. Both match their complete
original controls with zero differences. This covers the full rise, the wait
phase and the first four active-play updates, including inherited timer phase,
scene motion, placements, HUD/fade progression, raw inputs and one effect request.
The next update begins a graphics transfer and remains explicitly unowned here.

## Native behavior and corrected boundary

`airFollowingAirQuietUpdate` continues the established first-update source work
with the actual native game, audio and continuing LCD epoch/deadlines. Every
update decodes the current display-sampled raw buttons and prior raw history;
the next native update can consume a fresh edge without borrowing the previous
game's controls. Gameplay costs come from native handlers/resources and the
existing sprite, row and placement completion owners. No original time, memory
or game state is supplied to these operations.

The longer comparison exposed the shared C00C/C00D row-scratch/publication gate:
when no new row is prepared, its high byte clears while the previous low byte
remains. The earlier first-update-only comparison always prepared a row and
could not expose this. The native diagnostic now clears that high byte at the
completed map callback. All other selected fields already matched in the first
266-update experiment; the correction removes the 2,614 stale-scratch boundary
differences in its ordinary variant.

An actor can queue an original effect during the quiet body. The display service
now queues that actual native request into native audio and clears it at the
owned service, retaining the resulting setup/voice work. Effect 20 is observed
in these controls; its 472-cycle setup is a comparison result, not a native
constant. Quiet means no unowned display interruption of the body, not silent
audio. Pending transfers, unrecognized work, new pause/reset and terminal stunt
results still reject and require their own completion owners.

## Evidence and verification

The ordinary variant extends the existing input-only retry control. The paused
variant preserves the previously qualified pause button schedule and extends
only its final post-resume tick interval from five to 300 host frames. Two
independent unhooked repetitions agree on its full terminal memory hash. The
separately authorized pinned SameBoy records 266 updates through the next 03d8;
every instrumented run agrees with its unhooked control. No RAM/lives/seed is
injected. The native probe reads raw button samples and decoded assets only.

Each variant matches 2,660 boundary comparisons, 42,560 actor slots (8,058
occupied instances), 266 displays and 532 complete vectors. Adjacent end/begin
samples are the same source boundary: 2,395 boundary samples per variant are
distinct. The first ten comparisons repeat the preceding first-update scope.
Combined comparison totals are 5,320 / 85,120 / 16,116 / 532 / 1,064 respectively;
these are two restart variants and do not increase independent main-Air campaign
coverage. Source timer phase remains 35 through rise/wait and advances to 39
over the first four active updates, with 40 seconds still remaining.

Comparison requires full coverage, contiguous snapshots, native entry attachment,
matching backend/control hashes, every inherited wait deadline and complete
vectors. Live actor frame/flags/handler/position, animation flags/delay/period and
seven parameters agree. Vacant allocation/sentinel fields agree; raw script
pointers and unused vacant payloads remain excluded. Native and original display,
effect and music work agree separately. Complete images, prepared/published
graphics bytes and PCM are not compared by this checkpoint.

Validation: optimized Windows diagnostic, 663 ROM-free native handoff/pause
assertions and 456 Python tests. Twenty-one new quiet-comparison integrity checks
cover lost continuation/timer/gate state, truncation/reordering, unknown IRQ owners,
deadline drift, effect consumption, missing pause proof and pending resource work.
The first-update analyzer also rejects a mismatched declared update extent. All
four prior startup/exit controls and the ordinary first update remain exact.
The preceding 52,850 result assertions remain applicable; result implementation
and the production Windows EXE/campaign/UI behavior are unchanged and were not
retested without a new production change.

## Local reproduction and continuation

Native playback uses `--following-gameplay --following-updates 266`; the paused
variant also uses `--following-entry-pause`. `air_following_gameplay_reference.py
capture --updates 266` records the original; `air_following_quiet_reference.py`
compares without loading an emulator. Local ordinary evidence uses
`local/air-following-retry-quiet-*`; paused evidence uses
`local/sameboy-air-entry-pause-quiet/` and `local/air-following-pause-quiet-*`.
Comparison logs are `local/air-following-{retry,pause}-quiet-comparison.log`.
Build/tests and preceding regressions are `local/air-following-quiet-*`.
All original data/recordings remain ignored and local.

The exploratory 300-update ordinary recording is preserved as
`local/air-following-retry-quiet-reference/gameplay.rejected.json`. It is not an
accepted native comparison. At update index 266 (the 267th update), the original
resource phase sets transfer state one with thirteen remaining pieces. This
checkpoint stops at the preceding complete wait/input gate. The next concrete
work is to commit that resource request and its following display transfers at
their source completion boundaries, then extend normal restarted gameplay.
Ski/changed-player/global animation-pool handoffs, genuine final-life/reset,
earlier UI/LCD, unobserved protected/interrupted owners and production Windows
scheduler integration remain required. Timing point 1 and final acceptance are
incomplete; no final release. The continuation automation remains active.
