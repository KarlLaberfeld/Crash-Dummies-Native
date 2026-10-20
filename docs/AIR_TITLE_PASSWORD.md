# First password presentation comparison

October 20, 2026. Continues the accepted direction-unlock sequence from
2b4f through 2ba7, before the first password-editing counter wait. Both
retained single-player Air/easy histories have independent input-only controls
that append 100 host frames to the accepted sequence. Two unobserved runs
preserve both the accepted prefix hash and full-control hash; the observed
run agrees. Setup state and original ROM remain unchanged.

Each native continuation matches 251 boundaries, 82 display/music services,
324 interrupt vectors, 484 raster boundaries, 2,287 readiness polls, 1,723
stores, 2,048 direct map bytes and 492 active voice projection rows. Combined:
502 / 164 / 648 / 968 / 4,574 / 3,446 / 4,096 / 984 respectively, **zero
differences**. All 374 / 378 preceding complete native CSVs remain exact;
the complete attached original/native chain is requalified.

The typed native owner inherits the actual completed menu route, input/tick,
window/maps, LCD epoch/deadlines and song 1. It performs all 40 closing waits,
falls through into the first 320-byte clear, calls the second clear, writes
all 32 password glyphs in three rows, waits, resets/starts song 7, reopens in
40 waits and clears its cursor/eight digits. Native glyphs come from the
existing decoded UI package. Every access and interrupt is owned independently;
no observed state, clocks, vector schedule or fitted allowance drives native
execution. The title display callback is selector zero, with 116 cycles of
native display work. Countdown remains 54. Both complete maps and preserved
object storage agree.

The music reset exposes instruction completion to raster work. A display
observing partially reset audio is rejected. Active music voices are compared
before and after replacement; inactive and hardware-inapplicable fields keep
the [instruction-music exclusions](AIR_TITLE_PICTURE.md). Intermediate reset
payload equality, rendered frames, PCM and hardware parity are not claimed.

Prepare with `tools/air_title_password_reference.py prepare ROM --capture
ACCEPTED_UNLOCK_CONTROL --out PASSWORD_CONTROL`. Capture with its `capture`
command, passing `--capture ACCEPTED_UNLOCK_CONTROL --control PASSWORD_CONTROL
--parent-out UNLOCK_REFERENCE --out PASSWORD_REFERENCE`. Build the native
diagnostic with `tools/build_air_clock_probe.py` and replay the inherited
native chain with `--title-password` and the complete password raw button
stream. Its `compare` command inherits all unlock-comparator arguments, plus
`--password-out`, `--password-control` and `--unlock-base`. CSVs use
`.fifth.title-password*`; reports use `.title-password.comparison.json`.

Validation: optimized Windows diagnostic, both complete attached comparisons,
2,899 native presentation assertions and 1,285 Python tests, including 42 new
control/storage/callback/access integrity cases. The native target joins the
regular test build. ROM/assets/original recordings/reference binaries remain
local. No release or automation change.

This closes first password presentation only. Editing, digit/cursor bounds,
validation, accepted/rejected feedback, return paths and music-test operations
remain open. Eight local exploratory cases for selected maps/day/difficulty
are not timing qualification. Other [comparison families](ORIGINAL_COMPARISON_SCOPE.md),
production scheduler integration and final acceptance remain incomplete.
