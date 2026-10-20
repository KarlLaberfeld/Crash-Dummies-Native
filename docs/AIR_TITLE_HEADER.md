# Post-title instruction header and first wait

October 20, 2026. Continues the accepted [instruction resume](AIR_TITLE_RESUME.md)
from 02ce through player name/lives, day and difficulty text and the first
counter wait to 031c, before instruction music starts.

Both retained single-player Air/easy histories match 12 boundaries, one display,
two vectors, 272 readiness reads, 39 glyph stores, two scroll stores and all
2,048 final map bytes each. Combined: 24 boundaries / two displays / four
vectors / 544 reads / 78 glyph stores / four scroll stores / 4,096 map bytes,
zero differences. All 402 / 406 preceding complete native CSVs remain exact.
The comparator requalifies the complete attached original/native histories.

## Shared text, separate presentation

The existing native header writer now accepts an explicit presentation owner.
Its default result path retains all prior success/failure behavior. The new
post-title wrapper inherits the actual fresh native campaign, completed map
clear, LCD epoch/deadlines and sampled input. It guards callback 5, zero center/
scroll, empty background/window/object storage, retained countdown and current
player/lives before invoking the shared decoded layouts.

This instruction presentation uses callback 5's 144-cycle display body and
288-cycle STAT body. It compares both scroll stores, keeps countdown at 54
and retains five lives. The actual display samples input and advances tick;
stopped audio retains the identified 64-cycle effect and 60-cycle music paths.
There is no borrowed result-countdown decrement. The final wait completes on
its own counter service and identified return tail.

Player/day/difficulty/lives come from native campaign records. Layout commands
and player-name glyphs come from locally decoded assets. Every glyph value,
destination and polling boundary agrees with the originals. Complete final
map storage is compared, including unchanged padding/window cells; the full
object list stays unchanged. This proves map contents and access timing, not
rendered pixels, PCM or hardware equivalence.

Both existing extended Start controls already cover this endpoint. Capture
preserves their full-control hashes; no events or extension frames change.
The native input-only file preserves the entire accepted resume prefix and
appends exactly one new raw display sample per history. No observed clocks,
services, map snapshots or fitted work allowances initialize native execution.
The separate authorized comparison emulator and ROM/assets/recordings/binaries
remain local and outside the native Windows runtime/distribution.

## Validation and reproduction

Capture with `tools/air_title_header_reference.py capture ROM --capture
EXTENDED_START_CONTROL --parent-out RESUME_REFERENCE --out HEADER_REFERENCE`.
Rebuild with `tools/build_air_clock_probe.py` and replay the same accepted
full extents and inputs with `--title-header` and the extended header button
file. Explicit fifth entry and all preceding owners are still required.

Compare with `tools/air_title_header_reference.py compare NATIVE_BASE`, all
resume-comparator arguments, plus `--title-header-out HEADER_REFERENCE` and
`--resume-base ACCEPTED_RESUME_NATIVE_BASE`. New outputs use
`.fifth.title-header*`; reports use `.title-header.comparison.json`. Local
evidence uses `air-title-header[-pause]-reference` and matching services CSVs.

Validation: optimized native Windows diagnostic, both full attached original
comparisons, 1,613 new native header assertions, 52,920 rebuilt shared result/
instruction regression assertions, CLI guard and 1,112 Python tests. The new
native target joins the regular test build. Native functional tests cover all
20 day/difficulty choices using synthetic independent layouts, stale input
edge clearing, tick rollover, countdown/life retention, map publication and
ineligible entry states. Only the two actual Air/easy single-player histories
have original timing qualification. Thirty synthetic evidence tests reject
detached controls/maps, wrong callbacks, borrowed countdown behavior, changed
player/input/counter state, missing scroll stores and a shortened final wait.

Regular Windows EXE rebuilt from committed source; this semantic clock remains
diagnostic, outside the production scheduler. No release or automation change.
Next: instruction music and stunt picture/content after 031c under the retained
instruction callbacks. Other menu/player/stunt/campaign paths, qualifying name
entry, vacant flags, full pixels/PCM, production timing and final human/device/
independent-Windows/distribution gates remain open.
[Final acceptance](ACCEPTANCE.md) remains incomplete.
