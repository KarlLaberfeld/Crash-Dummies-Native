# Air common result setup timing

October 7, 2026. The native diagnostic now reconstructs the common result
setup from `0409` through `0462`, including the separately measured perfect
four-emitter initialization. Ordinary text/portraits, accounting, music, LCD
enable and incoming fade are qualified by the result documents linked below.
Running perfect celebration and its incoming portrait/music/fade are qualified
in [celebration evidence](AIR_CELEBRATION.md); perfect accounting remains open.
The production UI still uses its previous frame-based schedule.

## Source ownership

After the outgoing fade, the source disables services and calls `2588` to
turn the LCD off. This routine waits for LY **equal to 145**, not greater
than or equal to 145. A return from the outgoing display at line 150 must
therefore wait for the next frame's line 145. Polls consume 32 source cycles;
the successful poll takes the shorter exit branch.

`air_result_clock.h` derives readback from the existing native cycle axis.
The pinned DMG source changes LY two dots into a line and briefly exposes
153 before the early zero reset. No recorded poll counts, idle allowances,
line bytes or absolute epochs enter native execution. The native prefix
also records the deferred periodic requests while source services are masked.
Both requests are pending after the observed equality waits.

The fixed LCD-off operations are derived from the identified routines:

| Interval | Source cycles |
|---|---:|
| DI, LCD-off call/prefix/exit | 208 + 32 per unsuccessful poll |
| Clear 256 object-list bytes, including unused tail | 6,196 |
| Configure result display registers | 96 |
| Clear two 1,024-byte maps through the safe-store helper | 295,104 |
| Result selectors/flags, excluding perfect celebration | 144 |
| Graphics bank selection | 68 |
| 4,096-byte LCD-off graphics copy | 426,056 |
| Data bank selection | 68 |
| Current player pointer preparation | 88 |

The 727,820 cycles after LCD-off returns are substantial setup work even
though the display counter is stopped. Modeling one UI frame does not qualify
this delay. The diagnostic models source work and boundaries; it does not
perform a new hardware tile/map copy or replace the native result renderer.

## Perfect initialization

The genuine perfect Air control collects all 14 objects using ordinary buttons,
including the crash-only collectible, and reaches result 7. `044a` then calls
`14f2`: display selector 2, STAT selector 4 and countdown 720 replace the ordinary
selectors/countdown. The four `157f` resets derive horizontal positions from the
shared native random state, set Y 143, velocity 251 and radius zero, and stagger
the emitters by 0/16/32/48 services. Their field/random algorithm is implemented
in `air_celebration.h`. No recorded random state or initialized emitter is used
as a native input; the probe passes the state left by native gameplay.

Each reset costs 328 source cycles: 172 for the identified random calculation
and 156 for its caller/field initialization. The first three pointer/call prefixes
cost 36; the final tail-call prefix costs 28. The taken conditional call and four
selector/countdown stores add 108 relative to ordinary flags work. This makes
the flags interval 1,700 rather than 144 cycles and adds **1,556 cycles**, for
729,376 fixed cycles after LCD-off returns. Explicit initialization boundaries
distinguish these operations; the final emitter shares the flags-ready boundary.

The independently controlled perfect recording matches all **15 absolute
boundaries / 2,121 LY reads**, final selector/countdown/random state and all 20
initialized emitter fields. Earlier controls are retained and still match
44 / 8,485, giving **59 / 10,606** prefix checks across five controls. These are
observed comparison counts, never runtime delays. The instrumented perfect
capture retains its original uninstrumented 32,768-byte end-state hash.
The final state comparison does not certify each intermediate field-store time.

Perfect capture uses schema 2 and requires the additional ordered boundaries
and complete initialized state. Older ordinary schema-1 captures remain valid;
a perfect result cannot borrow that schema or ordinary work. Missing native
seed/state, changed countdown, truncated emitters and wrong tail-call work
reject. The incoming result owner now accepts perfect results with the qualified
celebration/native initialization and its own portrait profile; see
[incoming evidence and limits](AIR_CELEBRATION.md).

Reproduction, in addition to the main perfect gameplay qualification:

```powershell
python tools/air_result_prefix_reference.py capture 'path/to/original.gb' --capture local/sameboy-air-perfect --out local/air-perfect-result-prefix-reference
local/air-clock-probe.exe local/sameboy-air-perfect/inputs.txt local/air-perfect-prefix-services.csv 0 --display-inputs local/air-perfect-buttons.txt --result-prefix
python tools/air_result_prefix_reference.py compare local/air-perfect-prefix-services.csv.result.csv --capture local/sameboy-air-perfect --out local/air-perfect-result-prefix-reference --startup local/air-perfect-startup
```

Local logs: `air-perfect-prefix-capture.log`, `air-perfect-prefix-comparison.log`,
`air-perfect-prefix-ordinary-regression.log`, `air-perfect-prefix-result-tests.log`
and `air-perfect-prefix-all-python-tests.log`, all under ignored `local/`.
The O2 diagnostic passes 18,485 ROM-free result assertions and all 251 Python
tests. The production Windows executable and scheduler are unchanged; no
unchanged full campaigns are repeated for this diagnostic-only preparation.

## Independent controls

Four controls agree at all **44 absolute boundaries** and **8,485 LY reads**,
including each read's returned byte and completion time, LCD-disable time,
deferred requests and final prefix boundary. The successful control has 2,121
reads; timeout has 2,122; steering damage has 2,121 each. These are observed
targets, never runtime inputs. Instrumentation preserves each original's
uninstrumented 32,768-byte end-state hash.

The three previous outgoing recordings stopped 40 frames after the result.
That was too short to finish this setup. New controls extend only that final
observation to 120 frames. Complete gameplay traces/input files and every
preceding input event are byte-identical; only the last observation duration
changes. Each extended control has its own qualified startup epoch and
control hash. Old captures are retained; evidence provenance is not mixed.

Capture and comparison, using the separately authorized pinned reference:

```powershell
python tools/air_result_prefix_reference.py capture 'path/to/original.gb' --capture local/sameboy-air-finish-search/120-56 --out local/air-result-success-reference
python tools/air_startup_reference.py capture 'path/to/original.gb' --capture local/sameboy-air-finish-search/120-56 --out local/air-result-success-startup
local/air-clock-probe.exe local/sameboy-air-finish-search/120-56/inputs.txt local/air-success-finish-native/services.csv 0 --display-inputs local/air-success-finish-native/buttons.txt --result-prefix
python tools/air_result_prefix_reference.py compare local/air-success-finish-native/services.csv.result.csv --capture local/sameboy-air-finish-search/120-56 --out local/air-result-success-reference --startup local/air-result-success-startup
```

`--result-prefix` includes the independently owned final wait/outgoing fade.
Its ordinary IRQ terminal file remains at `0409`; result-prefix boundaries,
polls and deferred requests are separate outputs. The comparator requires
complete point/poll coverage and checks the actual native outputs. Unknown
perfect-result paths without their separate schema/state, source/capture mismatches, missing reads, changed
pending requests and incorrect copy work reject.

The subsequent ordinary layout/portrait, music, LCD restart and incoming fade,
plus complete ordinary failure holds, are now qualified separately in
[result transition evidence](AIR_RESULT_TRANSITION.md). Ordinary successful
accounting is qualified in [accounting evidence](AIR_RESULT_ACCOUNTING.md).
Perfect accounting/handoff, final-life results and remaining initial/interrupted owners stay open.
Windows scheduling, result pixels/PCM and final acceptance are separate.
