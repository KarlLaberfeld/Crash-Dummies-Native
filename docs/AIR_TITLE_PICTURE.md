# Post-title instruction music and picture

Selected-player extension: twelve additional Start cases and eight full/skip
instruction paths now cover one/two players through the first Air game entry.
See [selected instructions](SELECTED_INSTRUCTION.md). The original first-Start
extent and historical validation counts below remain separately documented.

October 20, 2026. Continues [post-title header](AIR_TITLE_HEADER.md) from 031c
through song 2 start, tile copy and picture rectangle to 268b, before the
map transition and timed text. Both retained single-player Air/easy histories
match nine boundaries, four displays, eight vectors, 5,277 readiness reads,
1,114 graphics stores, eight scroll stores, 2,048 map bytes, 1,024 tile bytes
and 24 voice rows each. Combined: 18 / eight / 16 / 10,554 / 2,228 / 16 /
4,096 / 2,048 / 48 respectively, zero differences. All 409 / 413 preceding
complete native CSVs remain exact; the full attached chain is requalified.

The shared native picture writer now has an explicit instruction presentation;
default result behavior remains unchanged. Callback 5 retains countdown/lives
while actual displays sample input and advance native tick/music. The wrapper
inherits actual campaign choices, header maps and LCD state. Song 2 starts
with identified fixed work; interrupted reset still rejects. Every tile byte
is repacked from locally decoded native pixels, without importing observations.
All 1,024 transfers and 90 map glyphs match original values and access times.

An additive read-only observer copies the fixed 8340..873f instruction tile
region using the pinned reference's public direct-access API. It does not
synchronize graphics, advance emulated time or modify state. The core remains
unmodified. Direct final tile storage equals all attempted source stores and
every native byte. Full final maps, preserved headers/window/padding and full
object storage agree. Reference binaries/core never enter the Windows port.

All six voice slots are observed after each music service. The native comparison
checks activity, music work and previously qualified active sequencer/envelope/
pitch fields. Existing wave/noise/inactive-field exclusions remain explicit:
inactive payloads, wave envelope fields and nonapplicable noise pitch fields
are not claimed. This does not certify PCM, audio devices or rendered frames.

Both extended Start controls retain their full-control hashes with the new
observer. Events/extensions are unchanged. Each native raw input file preserves
the complete header prefix and appends exactly four display samples. Observed
state/clocks/schedules, graphics snapshots and fitted work allowances never
initialize native execution. ROM/assets/recordings/binaries stay local.

Capture: `tools/air_title_picture_reference.py capture ROM --capture
EXTENDED_START_CONTROL --parent-out HEADER_REFERENCE --out PICTURE_REFERENCE`.
Rebuild the read-only adapter with `tools/build_sameboy_reference.py` if needed,
and the native diagnostic with `tools/build_air_clock_probe.py`. Replay accepted
full extents/inputs using `--title-picture` and extended picture buttons.
Compare using `tools/air_title_picture_reference.py compare NATIVE_BASE`, all
header-comparator arguments plus `--picture-out PICTURE_REFERENCE` and
`--header-base ACCEPTED_HEADER_NATIVE_BASE`. Outputs use `.fifth.title-picture*`;
reports use `.title-picture.comparison.json`.

Validation: O2 diagnostic, both full attached comparisons, 14,902 native picture
assertions, 52,920 rebuilt shared result/instruction checks, CLI guard and 1,144
Python tests. Native fixtures cover independent solid bitplanes, all cells,
preserved unrelated storage and music continuation. Air/Ski native functional
tests do not qualify other starting choices against the original. Thirty-two
synthetic evidence tests cover provenance, direct tile storage, callback/input/
counter ownership, music selection and ordered/complete voice projection.

Windows EXE rebuilt from committed source; timing remains diagnostic. No release
or automation change. The broader requested [comparison work](ORIGINAL_COMPARISON_SCOPE.md)
is in progress. Later instruction/menu/stunt/player paths, full frames/PCM,
production timing and final human/device/independent-Windows/distribution gates
remain open. [Final acceptance](ACCEPTANCE.md) is incomplete.
