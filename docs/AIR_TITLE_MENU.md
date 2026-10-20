# First title-menu idle timeout

October 20, 2026. Continues both accepted [first-page reopenings](AIR_TITLE_PAGE.md)
from 2707 through all 480 menu waits, automatic page-index advance and the
next closing-call entry at 26ea. This qualifies the complete idle duration of
page zero, not fresh menu interaction, page-one composition or production timing.

Each ordinary / earlier-paused easy Air history matches 4,324 boundaries,
480 display services, 1,440 vectors, 1,920 raster boundaries, 4,321 stores and
all 2,048 unchanged final map bytes. Combined: 8,648 boundaries / 960 displays /
2,880 vectors / 3,840 raster boundaries / 8,642 stores / 4,096 map bytes, zero
differences. All 366 / 370 previous complete native CSVs remain byte-identical.
The composite requalifies the full attached original clock/control chain.

## Native duration and input scope

The restored first-page counter starts at 480, independently of the frozen
game countdown (54). Each wait snapshots the actual display counter and
finishes after its next change. Input processing checks the unlock sequence,
Start, Select and A/B before decrementing the duration. With no fresh input,
the full counter expires and the actual page index advances from zero to one.
The native owner stops before closing that next page.

Both original histories retain held A+Right with no fresh edge throughout
this scope. The native idle owner also distinguishes held Start/Select from
fresh edges in unit tests. It rejects any fresh-input/unlock branch rather
than applying the idle timing to a different path. Those branches still need
separate original comparisons. Native raw display samples use the source
button encoding; the public UI's abstract input flags are not substituted.

The original reset's unlock selector remains at its initial position in
every observed boundary. No sequence progress or extra store is inferred.
Native execution inherits the actual page, input, LCD epoch/deadlines,
display/audio state and song 1. Per-operation work retains source interrupt
boundaries; counter waits retain their own acceptance owner. No observed
timestamps, IRQ schedules, native state overrides or fitted work allowances
are execution inputs. The port contains no reference CPU/emulator core.

Each display advances the wrapping tick and song 1. Two zero-center raster
services run per wait; their complete register-store sequence matches. Final
cumulative result display/STAT totals are 1,142 / 1,814. The background/window
maps and empty object storage remain unchanged. Direct reference storage at
entry must equal the accepted page's final maps; entry/exit equality and all
native final map bytes are independently checked. This is storage/register/
timing evidence, not a complete pixel, window-glitch or PCM comparison.

## Reproduction and validation

The existing final-result controls already cover the full timeout. No event
extension or RAM modification was necessary. Both captures retain their old
full-control digests; input-only files preserve every previous page sample
and append exactly 480 samples per history. Adapter/core/model/boot identities
remain those of the accepted page comparison.

Capture using `tools/air_title_menu_reference.py capture ROM --capture CONTROL
--parent-out PAGE_REFERENCE --fade-out FADE_REFERENCE --out MENU_REFERENCE`.
The separate, pinned comparison emulator is read-only during capture; its
library, ROM, snapshots and recordings remain local.

Build with `tools/build_air_clock_probe.py --out local/air-title-menu-clock-probe.exe`.
Use the accepted page replay's initial inputs and complete attempt extents,
the new menu recording's `buttons.txt` for `--result-inputs`, and replace
`--title-page` with `--title-menu`. Explicit fifth entry and all preceding
owners remain required. New outputs use `.fifth.title-menu*`, including the
complete final map snapshot.

Compare with `tools/air_title_menu_reference.py compare NATIVE_BASE`, the same
arguments as `air_title_page_reference.py compare`, plus
`--menu-out MENU_REFERENCE` and `--page-base ACCEPTED_PAGE_NATIVE_BASE`.
Reports are `.title-menu.comparison.json`. Local evidence uses
`air-title-menu[-pause]-reference` and `air-title-menu[-pause]-services.csv`;
controls remain `sameboy-air-fifth[-pause]-result-control`.

Validation: optimized native Windows diagnostic, both complete attached
comparisons, 44,212 native menu assertions, CLI guard and 943 Python tests.
Native tests cover all waits and service counts, held actions, tick wrap,
graphics preservation, valid entry ownership and invalid/reset/fresh-input
rejection. Synthetic recording tests reject detached maps, shortened duration,
unlock progress, altered inputs, missing/reordered/overlapping vectors,
incomplete raster stores and wrong page advancement. The native tests join
the regular test build. Unchanged shared-clock and campaign tests retain
their previous scope without repetition.

Regular Windows EXE rebuilt from committed source. The semantic timing owner
remains diagnostic, outside the production scheduler. No release or automation
change; ROM, extracted assets, recordings and binaries remain local.

Next: qualify fresh menu inputs/unlock progression, page-one composition and
player selection. Qualifying high-score/name entry, vacant flags, other player/
campaign/stunt/reset paths, production timing, full graphics/pixels/PCM and
human/device/independent-Windows/distribution gates remain open.
[Final acceptance](ACCEPTANCE.md) is incomplete.
