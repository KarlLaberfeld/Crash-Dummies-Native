# First title page and center reopening

October 20, 2026. Continues both accepted [title-closing histories](AIR_TITLE_CLOSE.md)
through two window clears, first-page installation and forty reopening waits.
Ends at 2707, before restoring the menu duration and entering its input loop.
This does not yet qualify menu interaction, other pages or a complete reset path.

Both ordinary and earlier-paused easy Air histories match 142 boundaries,
42 display services, 165 vectors, 246 raster boundaries, 1,373 operation-start
stores, 2,715 readiness polls and all 2,048 final map bytes each. Combined:
284 boundaries / 84 displays / 330 vectors / 492 raster boundaries / 2,746
stores / 5,430 polls / 4,096 map bytes, zero differences. All 358 / 362 preceding
complete native CSVs remain byte-identical. The composite requalifies the
complete original control/clock chain.

## Two clears and page composition

The closing routine falls through into its first 320-cell clear. After that
returns, the caller explicitly invokes the same clear again. Both passes and
their separate readiness decisions are retained. The first page then copies
a 20x10 rectangle into window rows 14 through 23. Its tile identifiers come
from the existing local decoded UI map; no new artwork/data file is added to
the repository. Cleared row padding, unrelated window cells and the complete
background map are preserved and independently checked at the endpoint.

The source-derived layout wrappers, bank/copy/row-carry work and every glyph
readiness loop run on the inherited native clock. No source timestamps, poll
counts, IRQ schedules, snapshots or fitted work allowances enter execution.
The forty reopening waits each increment window Y and center independently:
72 to 112 and 176 through 178, ... 254 to zero. Held/fresh actions cannot skip
this motion. Song 1 continues, display ticks advance and countdown stays 54.
Cumulative result display/STAT totals become 662 / 854.

## Bounded right-edge readiness and storage observation

The title uses WX=166. The pinned DMG reference handles that window edge in
HBlank without extending visible transfer in this empty-OAM/no-horizontal-
scroll case. The native readiness owner opts into precisely that profile:
eight-pixel objects, all object coordinates zero, SCX zero and WX 166. Default
special-edge rejection and other window/object profiles remain unchanged.
All 2,715 independently read mode values, including failed polls, match per
history. This is a pinned-reference readiness qualification, not a hardware
window-glitch or pixel-output proof. First-frame access remains unqualified.

A new comparison-only `direct-vram-title-v1` observer copies the two fixed map
areas through SameBoy's official direct-access API. An ordinary CPU-style
read at the initial checkpoint is blocked and returns ff, so it cannot prove
storage preservation. The direct observer advances no emulated time, writes
no state and performs no graphics synchronization. It records full entry and
exit storage; replaying only the identified map stores reproduces the final
snapshot exactly. The earlier blocked-read attempt was rejected and remains
local, not an accepted storage proof.

The adapter exports an explicit observer identity, included in its build
metadata and recordings; its DLL hash is verified. The pinned unmodified core,
DMG-B model, boot ROM, execution callback and existing pause-storage API remain
unchanged. Both new captures retain their old full-control digests after the
read-only adapter extension. Neither the reference library nor its core source
is included in the native game or distribution. See [backend details](REFERENCE_BACKENDS.md).

## Reproduction and validation

Existing final-result controls already extend beyond this endpoint. No new
event extension or RAM modification is needed. Input-only recordings preserve
all previous closing samples and append exactly 42 samples per history.

Rebuild the optional local adapter with `tools/build_sameboy_reference.py`.
Capture with `tools/air_title_page_reference.py capture ROM --capture CONTROL
--parent-out CLOSE_REFERENCE --fade-out FADE_REFERENCE --out PAGE_REFERENCE`.
Capture attaches to the accepted closing endpoint. Direct storage provenance,
both clears, all rows, reopening steps and unrelated map preservation are
required. ROM, recordings, snapshots and decoded assets stay local.

Build with `tools/build_air_clock_probe.py --out local/air-title-page-clock-probe.exe`.
Use the closing replay's complete attempt extents/initial inputs, the new page
recording's `buttons.txt` for `--result-inputs`, and replace `--title-close` with
`--title-page`. Explicit fifth entry and every preceding owner remain required.
New outputs are `.fifth.title-page*`, including the complete final map snapshot.

Compare with `tools/air_title_page_reference.py compare NATIVE_BASE`, the same
arguments as `air_title_close_reference.py compare`, plus
`--page-out PAGE_REFERENCE` and `--close-base ACCEPTED_CLOSE_NATIVE_BASE`.
Reports are `.title-page.comparison.json`. Local evidence uses
`air-title-page[-pause]-reference` and `air-title-page[-pause]-services.csv`;
controls remain `sameboy-air-fifth[-pause]-result-control`.

Validation: optimized native Windows diagnostic, both complete attached
comparisons, 13,535 native title-page assertions, CLI guard and 917 Python
tests. Guards retain the default WX rejection and reject other edges, scroll,
object geometry, wrong entry/song and reset chords. Native tests preserve
both clears, rectangle padding/unrelated maps and all forty opening waits.
Shared LCD/title regression checks pass: 580 pause / 4,281 source-work / 52,920
result-clock / 29,724 final-result / 1,258 closing / 1,922 fade assertions.
The new native tests join the regular test build. Unchanged complete campaigns
retain their previous integration scope and are not repeated. Regular Windows
EXE rebuilt from committed source; timing remains diagnostic, outside its
production scheduler. No release or automation change; binaries stay local.

Follow-up: the [first menu idle timeout](AIR_TITLE_MENU.md) now qualifies all
480 waits and automatic page advance. Next: fresh menu input and subsequent page/player-selection
paths. Qualifying-score/name entry, vacant flags, other campaign/player/stunt/
reset paths, production timing, full graphics/pixels/PCM and final human/device/
independent-Windows/distribution gates remain open. Timing point 1 and
[final acceptance](ACCEPTANCE.md) are incomplete.
