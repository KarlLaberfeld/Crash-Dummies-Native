# Air Bumper source timing: partial reconstruction

The original-time scheduler is **not finished**. The Windows runtime still
performs one gameplay update per display interval. Four source-derived work
costs are implemented and checked; they are not yet a complete frame budget.
Do not use their partial sum to skip updates or claim real-time parity.

## Measured cause

The separate, user-authorized PyBoy 2.7.0 reference replay reproduces 3,059
completed updates from the existing control-verified Air capture. Timing hooks
read the emulated oscillator counter, not host wall time. The new instrumented
run has the same final 32,768 bytes as the earlier uninstrumented control,
SHA-256 `03783c97b547d3d3ee69b720ae5b78228e04ebc961f31eeffadf7ab9cd954eb8`.
This establishes consistency in that reference environment, not physical
hardware equivalence.

VBlank interrupts updates 895 and 1222 during placement processing, returning
to `00:1b05` (definition parameter copy) and `00:19f1` (range check) respectively.
At both interruptions, `FFAE` is zero: the main loop is still working. The
global counter advances anyway. After the loop finishes, `00:2617` waits for
another counter change. Consequently, one game update can consume two display
intervals. A fixed 59.7275 Hz update rate alone cannot reproduce this behavior.
The existing Windows display/audio rate already uses 70,224 / 4,194,304 seconds.

The VBlank service cost varies from 4,188 to 16,160 oscillator T-cycles across
this capture. This includes display, input and sound work. Using a single
guessed interrupt allowance would produce incorrect overrun decisions.

| Work interval | Update 895 | Update 1222 |
|---|---:|---:|
| Entity update and saved player frame, `03d8..03de` | 25,724 | 27,644 |
| Resource preparation and bank switch, `03de..03e4` | 252 | 252 |
| Sprite preparation, `03e4..03e7` | 19,724 | 21,920 |
| Unused sprite-list clearing and bank switch, `03e7..03ed` | 688 | 988 |
| Map-row callback, `03ed..19a2` | 2,228 | 2,228 |
| Eight-placement scan, `19a2..03fa` | 10,204 | 4,304 |

These are routine work costs, with interrupt entry, interrupt bodies and
interrupt return removed. IRQ hooks at `0040`/`0048` run after the 20-cycle
entry; hooks at `2484`/`2555` run before the 16-cycle return. The analysis rejects
overlapping interrupts and work intervals that end inside an interrupt.
The two updates require 58,820 and 57,336 work cycles. After accounting for the
intervening 324-cycle STAT service, they have used 55,972 and 56,332 work cycles
when VBlank interrupts them. Respectively 2,848 and 1,004 cycles of the main
update remain. These are measured intervals, not constants for the scheduler.

## Native work accounting

`src/air_work.h` computes sprite preparation and tail-clear costs from native
entity positions, flags, decoded layouts, clipping and allocation direction.
It models the original branch costs, signed-add carry cases and whole-entity
capacity check. `AirGame::step` accounts for map-row generation and placement
range tests, active records, free-slot searches, creation and table wraps.
There is no CPU instruction dispatcher, CPU state, ROM execution, or replay
index lookup. Graphics cost collection is enabled by the reference probe;
normal gameplay does not repeat the geometry pass solely for diagnostics.

The independent reference-side formulas match all four measured routine costs
for all 3,059 updates, including both overruns. The actual C++ port's four costs
match the original through update 2470 inclusive when supplied the recorded
global counter. They first differ at 2471, after the intentional crash-recovery
fix has already changed animation state at 2458. This checks these routines;
the recorded counter remains a diagnostic input, not a runtime solution.

## Timing-related behavior correction

Work comparison initially found a native placement-cost difference at update
1188. Broader entity logging located an earlier animation difference at update
466. The original allocation routine `1acd..1ad7` changes the saved animation's
done/wait flags but retains its delay, period, script and loop cursors. Native
allocation reset that entire block, advancing animation when a slot was reused.

The native Air allocator now preserves those fields. A synthetic inherited-delay
regression fails against the previous allocator and passes with the correction.
Restart still clears the pool. The original/native frame, flags and positions
of occupied non-player slots now match through update 2578 inclusive in the
recorded-clock replay, instead of first differing at 466. The later divergence
follows the intentional recovery safeguard; no claim about all internal entity
fields or rendered pixels is made. Player comparison still matches its 23
fields through update 2457, then reaches that intentional safeguard.

## Reproduce locally

First produce the control-verified capture described in
[ORIGINAL_COMPARISON.md](ORIGINAL_COMPARISON.md). All generated files stay under
ignored `local/`; never upload original layouts, state, recordings or traces.

```powershell
python tools/air_timing.py capture 'path/to/original.gb' --reference-lib .tools/reference
python tools/air_timing.py report
$env:ZIG_GLOBAL_CACHE_DIR = Join-Path $PWD '.tools/zig-cache'
$env:ZIG_LOCAL_CACHE_DIR = Join-Path $PWD '.tools/zig-local-cache'
& .tools/zig-x86_64-windows-0.16.0/zig.exe c++ -std=c++17 -O2 -Wall -Wextra -Wpedantic -Isrc tools/air_reference_probe.cpp src/air.cpp src/game.cpp -o local/air-reference-probe.exe
& ./local/air-reference-probe.exe local/original-air-verified/inputs.txt --recorded-clock --work-csv local/air-timing/native-work.csv --entities-csv local/air-timing/native-entities.csv > local/air-timing/native-state.csv
python tools/air_timing.py compare local/air-timing/native-work.csv
python tools/air_timing.py compare-entities local/air-timing/native-entities.csv
python tools/air_reference.py compare local/air-timing/native-state.csv --out local/original-air-verified
```

The pure analysis and synthetic Python tests do not import or require PyBoy.
Capturing is the only emulator-dependent operation. The timing probe deliberately
does not use original positions, allocation results or layouts to drive native
gameplay. Native entity logging occurs before `step`; exclude the player from
that pre-step comparison because the original's preceding display callback can
complete a player resource upload. The separate post-step comparator covers it.

## Required next work

Checkpoint validation passes 39 Python tests, all native suites, all 64 Air
recovery phases (822,497 Air assertions including replay invariants), three
complete campaign scenarios and 13 Windows UI checks with no dropped audio
buffers. Logs are local/air-work-verified-build.log and build/ui-window-test.txt.
The allocator regression also fails against the prior implementation. Native
state exports with graphics work accounting enabled and disabled are identical.

The animation correction changes the deterministic pilot's route: the solo
campaign finishes all twenty stunts with one retry and 8,478 savings. Both-player
completion finishes at 8,620/8,455 with three/two failed attempts; the elimination
scenario finishes at 0/8,493 with five/zero failures. Campaign acceptance now
explicitly verifies preserved progress/savings and life loss on each failure,
and continues to require all twenty wins, the ending and return to title. The
earlier zero-failure solo requirement tested pilot perfection rather than game
correctness; it is not retained as a fidelity oracle. No game results are injected.

1. Account for the entity-handler, animation, collision and resource-queue paths
   (`03d8..03e4`) from their semantic native operations. Compare each interval
   against the new reference measurements instead of fitting a total constant.
2. Reconstruct variable interrupt service work, including audio and HUD paths,
   and the main-loop wait/interrupt phase. The observed min/max is not a model.
3. Introduce separate display and completed-game-update progression. An extra
   VBlank must advance global input/audio/HUD/display work without inventing an
   extra entity update. Respect the dynamic-transfer gate and the map callback;
   do not indiscriminately suppress all display work when `FFAE` is zero.
4. Run ordinary-clock native replays with no supplied per-update counter and
   require agreement before the intentional recovery difference. Then expand
   inputs, difficulties and the other stunts; compare image/audio boundaries.

Do not hardcode updates 895/1222, drive cartridge timing from Windows CPU speed,
add a runtime emulator, or mark release timing accepted at this checkpoint.
