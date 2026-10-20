# Title music start and center closing

October 20, 2026. Continues both accepted [title fades](AIR_TITLE_FADE.md)
through song 1 initialization and forty center-closing waits. Ends at 27f9,
before clearing or installing the next window page. Page clearing/composition,
reopening and menu interaction remain separate owners.

Both ordinary and earlier-paused easy Air histories match 132 boundaries,
40 display services, 159 vectors, 238 raster boundaries and 518 stores each.
Combined: 264 boundaries / 80 displays / 318 vectors / 476 raster boundaries /
1,036 stores, zero differences. All 351 / 355 earlier complete native CSVs stay
byte-identical, including the entire title fade. The composite requalifies the
full original control/clock chain.

## Interrupted music initialization

The next line-23 STAT request falls inside title song initialization. Its
source return is 23af, at the hardware-copy entry after its caller completes.
The native reset exposes the identified fixed clear, preset, wave, song-root
and hardware-copy work as atomic source boundaries. The actual native raster
service may run there; no measured interrupt schedule or fitted allowance is
used. The existing aggregate non-interrupted music-start owners stay intact.

No VBlank/audio service occurs during this reset in either original history.
The new owner rejects any such observation instead of servicing partially
reset native voices. Native `playMusic(1)` commits the completed logical reset
before the first new display/audio observation. Partial audio RAM/register
contents are **not** certified, and the native logical song identifier is not
compared to the original's earlier selected-song store during reset. Boundary
timing, the intervening raster service, completed selection and every later
display/effect/music service cost are compared. This does not prove PCM.

## Closing geometry and raster work

Each of forty display waits is followed by a separate window-Y decrement and
center-position subtraction. Window Y goes 112 to 72; the center wraps through
254, 252, ... to 176. The endpoint's value 176 is stored after the last observed
display. Subsequent rendering at that final position is outside this scope.

For moving centers 254 through 178, the top raster callback selects the title
map, sets scroll to `(center + 88) & 255` and schedules compare line
`(23 - center) & 255`. A new middle branch restores scroll 88 and schedules
line 103; the bottom branch restores scroll zero and line 23. The two existing
zero-center branches remain byte-exact in the earlier fade. One shared native
raster owner now describes these title phases. It contains no CPU state or
instruction execution.

All raster entry/exit geometry and title operation-start stores are compared,
including the two distinct zero-center scroll stores and forty independent
window/center updates. This is not a physical bus-sampling or pixel-transfer
proof. All native future compare deadlines come from its center and LCD epoch.
Display input is still sampled, but held or fresh A/Start cannot shorten the
fixed motion. The old result countdown stays 54. Song 1 is active for all forty
new displays; cumulative result display/STAT totals become 620 / 731.

## Reproduction and validation

The existing final-result controls already extend beyond this endpoint. No
new event extension or RAM modification is needed. Both hooked captures match
their accepted full-control digests and pinned backend. New input-only sample
files preserve all preceding fade samples and append exactly forty samples.
No original times, snapshots, decisions or work allowances enter native replay.

Capture with `tools/air_title_close_reference.py capture ROM --capture CONTROL
--parent-out FADE_REFERENCE --out CLOSE_REFERENCE`. The source endpoint selects
measurement only. Capture rejects changed controls, the wrong music-reset
interrupt return, VBlank observing partial reset, incomplete center/window
motion, missing raster branches/stores and changed result countdown.

Build with `tools/build_air_clock_probe.py --out local/air-title-close-clock-probe.exe`.
Use the accepted fade replay's complete extents and initial inputs, the new
closing recording's `buttons.txt` for `--result-inputs`, and replace
`--title-fade` with `--title-close`. Explicit fifth entry and all preceding
owners remain required. Output adds `.fifth.title-close*`; earlier outputs
retain their complete bytes.

Compare with `tools/air_title_close_reference.py compare NATIVE_BASE`, the same
arguments as `air_title_fade_reference.py compare`, plus
`--close-out CLOSE_REFERENCE` and `--fade-base ACCEPTED_FADE_NATIVE_BASE`.
Reports are `.title-close.comparison.json`. Local evidence uses
`air-title-close[-pause]-reference` and `air-title-close[-pause]-services.csv`;
controls remain `sameboy-air-fifth[-pause]-result-control`.

Validation: optimized native Windows diagnostic, both complete attached
comparisons, 1,258 native title-close assertions, the previous 1,922 title-fade
assertions, CLI ownership guard and 902 Python tests. Native guards cover wrong
initial geometry/song, reset chords and display observation during partial
reset. Alternating fresh A/Start samples retain all forty steps. A native-only
test also covers the merged final-center raster branch; that branch's original
rendering remains outside this observation. New native tests join the regular
test build. The shared fixed clock/audio/campaign owners are unchanged; their
prior regression/integration scope remains applicable without rerunning the
same complete campaigns. Regular Windows EXE rebuilt from committed source;
diagnostic timing remains outside its production scheduler. No new release or
automation change; ROM/data/recordings/binaries stay local.

Next: closed-window clearing/page installation, center reopening and menu
behavior. Qualifying-score/name entry, vacant flags, other campaign/player/
stunt/reset paths, production timing, full graphics/pixels/PCM and final human/
device/independent-Windows/distribution gates remain open. Timing point 1 and
[final acceptance](ACCEPTANCE.md) are incomplete.
