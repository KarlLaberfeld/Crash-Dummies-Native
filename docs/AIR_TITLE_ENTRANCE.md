# First instruction reveal and retained alternate flag

October 20, 2026. Continues [music/picture](AIR_TITLE_PICTURE.md) from 268b
through the first-instruction branch, native alternate-flag enable and full
incoming fade to 0a0a before timed text. This is a different path from the
already documented later-instruction 64-step patterned map transition.

Both retained single-player Air/easy histories match 76 boundaries, 32 displays,
64 vectors, 89 stores, 2,048 unchanged map bytes, 1,024 unchanged tile bytes and
192 voice rows each. Combined: 152 boundaries / 64 displays / 128 vectors /
178 stores / 4,096 map bytes / 2,048 tile bytes / 384 voice rows, zero differences.
All 418 / 422 preceding complete native CSVs remain exact. The entire attached
original/native chain is requalified.

The earlier native title reset clears the alternate flag. The owner inherits
that native zero value, sets it to one at its actual store and takes the
incoming fade. It does not import the observed C09d value or borrow the later
patterned-transition owner. The native guard rejects alternate=1 and incompatible
result/callback/campaign/palette/image states.

Eight palette groups retain four independent counter waits each. Callback 5
keeps countdown/lives fixed, while actual displays advance input/tick and song 2.
All 24 palette writes, flag store, scroll stores, interrupt ownership and active
voice projections agree. A fresh Start does not shorten this fade in native
functional tests; original qualification here retains the two existing input
histories. Full direct tiles/maps and full object storage stay unchanged.
Final palettes are e4/c4/e0. Rendered-frame, PCM and hardware parity are not
implied; active voice-field exclusions remain those of the music/picture scope.

Existing extended Start controls already cover this endpoint. Events/extensions
and full-control hashes remain unchanged. Each native raw input file preserves
its complete picture prefix and appends exactly 32 observed display samples.
No original state, clocks, service schedules, palette snapshots or fitted work
allowances drive native execution. ROM/assets/recordings/reference binaries stay
local and outside the native Windows program/distribution.

Capture with `tools/air_title_entrance_reference.py capture ROM --capture
EXTENDED_START_CONTROL --parent-out PICTURE_REFERENCE --out ENTRANCE_REFERENCE`.
Build with `tools/build_air_clock_probe.py`, replay accepted full extents/inputs
with `--title-entrance` and extended entrance buttons, then compare using
`tools/air_title_entrance_reference.py compare NATIVE_BASE`, all picture-comparator
arguments plus `--entrance-out ENTRANCE_REFERENCE` and `--picture-base
ACCEPTED_PICTURE_NATIVE_BASE`. Outputs use `.fifth.title-entrance*`; reports use
`.title-entrance.comparison.json`.

Validation: O2 diagnostic, both attached comparisons, 322 native entrance
assertions, CLI guard and 1,192 Python tests (25 new synthetic integrity cases).
Native tests cover the correct first/later branch, all waits/masks, tick rollover,
active music, ignored fresh Start, unchanged image/campaign state and invalid
entries. New target joins the regular test build. Windows EXE rebuilt from
committed source; timing remains diagnostic. No release or automation change.

The broader [comparison request](ORIGINAL_COMPARISON_SCOPE.md) remains in
progress. Next: complete first-instruction timed text/skip/prompt/exit controls,
then other menu/player/password/name-entry/campaign/stunt paths. Full frames/
PCM, production scheduling and final human/device/independent-Windows/
distribution gates remain open. Final acceptance incomplete.
