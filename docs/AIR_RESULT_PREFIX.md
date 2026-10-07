# Air common result setup timing

October 7, 2026. The native diagnostic now reconstructs the common result
setup from `0409` through `0462`. Result-specific text/portraits, accounting,
music, LCD enable, incoming fade and perfect celebration remain open.
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
perfect-result paths, source/capture mismatches, missing reads, changed
pending requests and incorrect copy work reject.

The subsequent ordinary layout/portrait, music, LCD restart and incoming fade,
plus complete ordinary failure holds, are now qualified separately in
[result transition evidence](AIR_RESULT_TRANSITION.md). Successful accounting,
perfect/final-life results and remaining initial/interrupted owners stay open.
Windows scheduling, result pixels/PCM and final acceptance are separate.
