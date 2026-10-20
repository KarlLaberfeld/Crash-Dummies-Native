# Post-campaign title services and incoming fade

Follow-up: [title music and center closing](AIR_TITLE_CLOSE.md) now qualify
both histories through interrupted song 1 initialization and forty closing
waits. Window clearing/page installation, reopening/menu and pixels/PCM remain
unqualified.

October 20, 2026. Continues both accepted [title layouts](AIR_TITLE_LAYOUT.md)
from EI entry through the initial pending display/STAT pair, complete incoming
fade and the following counter wait. Ends at 025f, before selecting title song
1. Center motion, page installation and the title menu remain separate owners.

Both ordinary and earlier-paused easy Air histories match 76 boundaries,
34 display services, 100 vectors, 132 raster boundaries and 321 stores each.
Combined: 152 boundaries / 68 displays / 200 vectors / 264 raster boundaries /
642 stores, zero differences. All 344 / 348 earlier complete native CSVs remain
byte-identical. The composite requalifies the full original parent chain.

The actual preceding native layout supplies its new LCD epoch, future request
deadlines, two retained pending requests, title maps/cleared objects, input sentinel
and callback selectors. The EI follower completes its CALL before the pending
display and then STAT service. Those initial vectors have separate ownership
from the subsequent HALT/counter-wait vectors. No observed timestamps, work
costs, poll counts, IRQ schedule or source snapshots initialize native execution.

The title's zero-motion raster alternates between two identified branches.
The upper branch selects LCDC fb, scroll Y 88 and line 103; the lower branch
restores LCDC c3, scroll Y zero and line 23. Both callback work and future
compare deadlines come from native state. The upper branch retains its two
distinct scroll writes, including the repeated value. All operation-start
times, addresses and resulting values are compared; this is not an electrical
bus-sampling or pixel-transfer proof. Nonzero center-motion geometry rejects
until its own branch is reconstructed.

The shared clock gains an optional native raster-work callback. Its existing
fixed Air/result callback paths remain unchanged when that callback is absent.
The new title owner supplies only the identified two raster branches. There
is no CPU state, opcode dispatch or generic memory-bus implementation.

Title display callback zero has 116 cycles of display dispatch. It increments
display ticks and services the inherited effect/music state, while retaining
the old result countdown at 54. Song 13 continues; song 1 is selected only
after this endpoint. The 32 fade waits and final wait are not skipped by held
or newly pressed A/Start. With the initial pending display, this gives 34 new
displays and 66 STAT services: cumulative result totals become 580 / 612.
Incoming palettes reach e4 / c4 / e0. Native held/pressed samples and every
effect/music service cost match the original within this scope, not PCM.

## Reproduction and validation

Both existing final-result controls already extend beyond the endpoint. No
new input extension or RAM modification is needed. Instrumented captures match
their accepted full-control hashes and pinned backend. The new input-only
sample files preserve every preceding return sample and append exactly 34
title samples; no timing/state data are loaded by the native process.

Capture with `tools/air_title_fade_reference.py capture ROM --capture CONTROL
--parent-out LAYOUT_REFERENCE --out FADE_REFERENCE`. Source scope attaches to
the accepted layout endpoint. Capture rejects changed controls, nested or
incomplete vectors, wrong pending priority/return, missing raster branches,
changed countdown, missing stores and inconsistent palette masks. Original
observations and new `buttons.txt` stay local.

Build with `tools/build_air_clock_probe.py --out local/air-title-fade-clock-probe.exe`.
Use the accepted layout replay's complete extents and initial inputs, the new
fade recording's `buttons.txt` for `--result-inputs`, and replace
`--title-layout` with `--title-fade`. Explicit fifth entry and all preceding
owners remain required. Output adds `.fifth.title-fade*`, including display,
vector, raster and write streams; all previous outputs remain exact.

Compare with `tools/air_title_fade_reference.py compare NATIVE_BASE`, the same
arguments as `air_title_layout_reference.py compare`, plus
`--fade-out FADE_REFERENCE` and `--layout-base ACCEPTED_LAYOUT_NATIVE_BASE`.
Reports are `.title-fade.comparison.json`. Local evidence uses
`air-title-fade[-pause]-reference` and `air-title-fade[-pause]-services.csv`;
controls remain `sameboy-air-fifth[-pause]-result-control`.

Validation: optimized native Windows diagnostic, both complete attached
comparisons, 1,922 native title-fade assertions and 887 Python tests. Fresh
A/Start transitions do not shorten the fade. Native guards cover malformed
entry deadlines, pending requests, center geometry, input/reset and unknown
raster work. The new tests join the regular test build. Shared-clock regression
checks pass: 52,920 result-clock / 29,724 final-result / 580 pause / 4,281 source-
work assertions. Unchanged full game/campaign runs retain their prior scope
and were not repeated. Regular Windows EXE rebuilt from committed source;
diagnostic timing remains outside the production scheduler. No new release
or automation change; ROM/data/recordings/binaries stay local.

Next: title song selection, center closing/page installation/reopening and
menu behavior. Qualifying-score/name entry, vacant flags, other campaign/
player/stunt/reset paths, production timing, complete graphics/pixels/PCM and
human/device/independent-Windows/distribution gates remain open. Timing point 1
and [final acceptance](ACCEPTANCE.md) remain incomplete.
