# Start title fade and music stop

October 20, 2026. Continues both accepted [fresh-Start decisions](AIR_TITLE_ACTIONS.md)
from 0269 through the outgoing fade, final wait and fixed audio stop to 0272,
before DI and the next instruction preparation. Both ordinary / earlier-paused
easy Air histories match, with no native state import or observed clock input.

Per history: 84 boundaries / 33 displays / 100 vectors / 134 raster boundaries /
328 operation-start stores / 2,048 unchanged final map bytes. Combined: 168 /
66 / 200 / 268 / 656 / 4,096, zero differences. All 374 / 378 earlier complete
native CSVs remain byte-identical. The composite requalifies the entire attached
original control/clock chain, including its accepted fresh-Start decision.

## Native transition and reset boundary

The native owner inherits the actual reopened title page, fresh Start, LCD
epoch/deadlines, input, map storage, palettes and song 1. All eight outgoing
palette steps use the existing decoded fade asset; each has four independent
counter waits. A final wait follows the fade. Fresh/held actions cannot shorten
these 33 display services. The wrapping tick advances, countdown stays 54,
and all raster/audio work continues from the actual inherited state.

After the last wait, fixed audio reset work exposes its source-derived atomic
boundaries to the same clock. Both original histories contain one additional
STAT service in this reset. That service updates the title's raster registers
and next compare deadline normally. No display/audio service observes the
partially reset voices; such an unowned overlap rejects in native execution.
There is no fitted uninterrupted allowance and no imported IRQ schedule.

The observer compares the identified NR52-off and music-disable stores.
Native logical audio stops at the disable completion boundary. Intermediate
voice RAM, initial wave storage, hardware audio samples/PCM and reset glitches
are not modeled or certified by these timing/store comparisons. Music stays
enabled through all 33 displays, then disables before the stop routine returns.
Final cumulative display/STAT totals are 698 / 927; the last reset-time STAT
also changes the retained raster phase and next deadline.

The full background/window maps remain unchanged. Entry direct storage must
match the accepted action endpoint; exit direct storage and all native final
map bytes are checked independently. Native tests also retain empty object
storage. This does not qualify full pixels or the next instruction's graphics.

## Original controls and reproduction

Each accepted input-only Start control is retained in full and extended by
80 frames with no new button events. The original setup file and all earlier
events stay byte-identical. Two unhooked runs must match the accepted complete
prefix hash and the new complete-control hash; the observed replay must retain
both. Parent events/setup/ROM/backend identities attach the extension to the
accepted Start case. Native input-only files preserve all previous samples
and append exactly 33 observed raw button samples. No original snapshots,
state, clocks or work budgets are supplied to the Windows game.

Prepare with `tools/air_title_start_reference.py prepare ROM --capture
ACCEPTED_START_CONTROL --parent-out ACTION_REFERENCE --out EXTENDED_CONTROL`.
Capture using `tools/air_title_start_reference.py capture ROM --capture
ACCEPTED_START_CONTROL --parent-out ACTION_REFERENCE --start-control
EXTENDED_CONTROL --out TITLE_START_REFERENCE`. The pinned, separate reference
emulator/core and all original controls/recordings remain local.

Build with `tools/build_air_clock_probe.py --out local/air-title-start-clock-probe.exe`.
Replay the accepted Start case's initial inputs and complete attempt extents,
using the new `buttons.txt` as `--result-inputs`; replace `--title-actions`
with `--title-start`. Explicit fifth entry and all preceding owners remain
required. New outputs use `.fifth.title-start*`, including the complete final maps.

Compare with `tools/air_title_start_reference.py compare NATIVE_BASE`, the same
arguments as `air_title_actions_reference.py compare`, plus
`--actions-base ACCEPTED_ACTION_NATIVE_BASE`, `--start-control EXTENDED_CONTROL`
and `--title-start-out TITLE_START_REFERENCE`. The inherited `--start-out`
still identifies the earlier fifth-entry recording. Reports use
`.title-start.comparison.json`. Local evidence uses
`air-title-start[-pause]-control`, `air-title-start[-pause]-reference` and
matching services CSVs.

Validation: optimized native Windows diagnostic, both complete attached
comparisons, 2,524 native Start assertions, CLI guard and 1,012 Python tests.
Native tests cover unskippable waits/palettes, display/input/tick ownership,
logical stop, map/object preservation, future deadlines and invalid route/
geometry/audio/reset-input rejection. Synthetic recording tests reject wrong
parent routes, edited input extensions, missing reset-time STAT, partial-reset
display observations, altered palettes/audio stores and detached storage.
The new native tests join the regular test build. Unchanged campaign/shared-
clock/menu tests retain their earlier scope without repetition.

Regular Windows EXE rebuilt from committed source; semantic timing remains
diagnostic, outside the production scheduler. No release or automation change;
ROM/assets/recordings/binaries remain local. Next: masked instruction preparation
after Start, unlock progression and subsequent page/player selection. Qualifying
name entry, other paths, vacant flags, full graphics/pixels/PCM and final human/
device/independent-Windows/distribution gates remain open.
[Final acceptance](ACCEPTANCE.md) is incomplete.
