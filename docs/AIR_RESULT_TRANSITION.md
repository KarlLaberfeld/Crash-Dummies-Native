# Bounded Air result transition and failure hold

October 7 perfect extension: separately qualified celebration, perfect portrait,
music startup, pending services and complete incoming fade now agree at
81 boundaries / 33 services / 66 vectors, including both prepared/published
sprite lists. See [perfect evidence and overlap limits](AIR_CELEBRATION.md).
The ordinary evidence below retains its own counts. Perfect accounting/handoff
and Windows integration remain open.

The native source clock now continues the ordinary result setup from 0462
through the complete incoming fade. Three ordinary failure controls additionally
continue through all 480 post-fade waits, music stop and the return at 0514.
This is a diagnostic clock, not yet the Windows scheduler. No CPU emulator or
original per-update work/timing allowance drives it.

## Native owners

`src/air_result_transition.h` reconstructs these identified operations:

- Success/failure predicates and Air-specific static text layout.
- The 1024-byte result portrait copy while LCD-off.
- The shared music reset, eight song roots and 23 hardware bytes: 14,052 cycles.
- LCD-on's final access/return, then the four-cycle enable and identified
  24-cycle follower. Pending VBlank precedes pending STAT.
- Result display selector 10: 272 cycles, including the 600-service countdown.
- The pop-only result STAT callback: 248 cycles; ordinary requests at line 143.
- All eight incoming palettes, their separate writes and 32 counter waits.
- On ordinary failure, a non-final life decrement and the initial counter wait.
- The 480-service result hold, returning branch and 12,384-cycle music stop.

`result-timing.dat` is generated locally by `extract_ui.py`. It contains only
structural counts for the identified static text language: character classes,
anchors/rows/layers, rectangle dimensions and destination row carries. The
native code computes work from these structures. There are no cartridge
instructions, recorded costs or recorded result clocks in this package.
The established `ui.dat` payload and production asset format are unchanged.

The result LCD restart creates a new periodic epoch. The pending startup is
charged separately before normal line-143/144 requests. Failure music starts
after an additional counter wait. Failed results retain held buttons, clear
fresh edges through display sampling and complete the 480-service wait without
expiring the source's 600-service timer. Original 16-bit update wrapping is
retained. Final-life, perfect, soft-reset, countdown-expiry, changed post-stunt
input and partially interrupted music reset require separate owners and reject
or remain outside this bounded input contract.

## Independent original evidence

The four input patterns are the genuine successful finish, timeout, damage and
the historical `win`-named damage case. Pinned SameBoy DMG-B replay uses only
original password/Start/gameplay buttons, with no gameplay RAM writes. Each
measurement reproduces its uninstrumented 32,768-byte final control hash.
The game-start epoch is qualified independently by the nine startup points.

| Scope | Patterns | Boundaries | Display services | Complete IRQ vectors |
|---|---:|---:|---:|---:|
| Ordinary incoming result | 4 | 336 | 135 | 270 |
| Complete failure results, including incoming result | 3 | 3,144 | 1,542 | 3,084 |
| Union: successful incoming result plus complete failures | 4 | 3,225 | 1,575 | 3,150 |

All comparisons have zero differences. The second row includes the incoming
failure boundaries, so it must not be added to the first as new situations.
The longer failure controls extend only the final observation from 120 to
650 frames; their gameplay traces, update input files and preceding input
events are byte-identical. They are extensions, not new gameplay patterns.

Actual native boundary times, update/countdown state, three palettes, music
enabled state, every service's component work/input and every vector time/owner
are checked. The comparator requires complete coverage, validates source
palette/branch/counter-wait work and rejects missing, shifted, reordered or
unqualified events. The native replays read only the initial game state and
button samples; original outputs are comparison targets.

Local evidence: `local/air-result-{success,timeout,damage,win}-transition/`,
`local/air-result-hold-{timeout,damage,win}-reference/`, matching startup/native
folders, `local/air-result-incoming-check.log` and
`local/air-failure-hold-check.log`. Captures and assets remain ignored.

```powershell
python tools/build_air_clock_probe.py
local/air-clock-probe.exe local/sameboy-air-finish-search/120-56/inputs.txt local/air-success-finish-native/services.csv 0 --display-inputs local/air-success-finish-native/buttons.txt --result-incoming
python tools/air_result_transition_reference.py compare local/air-success-finish-native/services.csv.incoming.csv --capture local/sameboy-air-finish-search/120-56 --out local/air-result-success-transition --startup local/air-result-success-startup
```

Use `--result-failure-hold` for a failure native replay and `--failure-hold`
when capturing its original result transition. Use the matching longer control
and independently captured startup, not another case's measurements.

## Remaining timing work

Successful accounting after 047e is now qualified through 0514 for one ordinary
success with unchanged buttons; see [accounting evidence](AIR_RESULT_ACCOUNTING.md).
Input skips now have separate qualified owners; see [result inputs](AIR_RESULT_INPUT.md).
Requested point 1 is not complete. Subsequent setup remains open.
Perfect celebration and
final-life transitions also remain. Initial UI/LCD access, unobserved entity/
resource/protected-pause interruptions, partial row pixels and production
Windows integration still need qualification. This evidence establishes
neither result pixels/PCM, independent hardware/Windows nor final acceptance.

Latest validation: 2,085 source-work assertions, 573 pause/session/
pixel assertions, 4,646 result-clock assertions and 211 Python tests. The O2
diagnostic also retains all seven complete gameplay controls, including all
36,548 main-game IRQ vectors. The rebuilt Windows EXE passes native suites,
three complete campaign scenarios, 34 sprite assertions and normal/failed-audio
13/14 UI checks. Its production clock remains unchanged.
