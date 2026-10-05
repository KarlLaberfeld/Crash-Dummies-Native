# Air Bumper source timing: partial reconstruction

The production Windows scheduler is **not finished**: it still performs one
game update per display interval. An experimental native semantic clock now
matches nine control-verified Air cases without supplied per-update counters
(28,103 updates, 28,153 display services). Music, STAT/wait and partial sprite
publication have checked models for these paths. Remaining handlers, interrupted
subphases, real-time input, pause and exit still need reconstruction before
Windows integration. See the latest checkpoint below. Source costs are derived
from identified routines, never fitted interrupt allowances or replay indices.

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

## Animation and handler checkpoint, 2026-10-04

Resource-queue preparation (`03de..03e4`) is now the fifth complete phase with
a source-derived model. Its reference-side formula agrees with all 3,059
measured updates, including acknowledgement, unchanged-frame, replacement and
empty-descriptor branches. The native resource calculation agrees through update
2458; its first difference at 2459 follows the intentional recovery safeguard.

The capture now measures individual entity bodies and nested animation calls.
It records 12,009 handler calls and 6,870 animation calls in the same verified
replay. The dispatcher decomposition, `1612 + 60 * liveCalls + bodyCosts`, agrees
with every measured entity phase. Here `bodyCosts` are **measured** values; this
decomposition does not establish a complete native budget.

Native animation accounting follows the existing semantic animation commands:
delays, dynamic-frame waits, loops, movement, allocation and termination. It
does not execute machine instructions. Per-update animation totals match through
update 2458. Unknown commands or non-yielding-loop guard failures mark the cost
incomplete instead of certifying a partial interval.

## Play, Crash and collision checkpoint — 2026-10-04

All **10,770 handler calls before update 2458** now have source-derived native
costs and agree exactly with the original. These cover 17 source addresses,
including all 1,461 Play calls, 320 Crash calls and the Wait-to-Play transition
that were previously unknown. The native entity phase uses `1612 + 60 *
liveCalls + sourceBodyCosts` and matches the whole `03d8..03de` interval through
update 2457, including the two overrun updates. This is now a comparison of
native source costs, rather than measured bodies substituted into a formula.

The new accounting follows camera movement, input order, motion-table factors,
timer rollover, damage severity, terrain bounce, side push, slow surfaces,
wall-triggered crashes, collision scans and callbacks. Search includes empty,
self and offscreen slots, byte-edge rejection order and the 12-cycle untaken
conditional callback. Callback spans include dispatch and body work, preventing
double counting. All 31 callback invocations in this replay match: types 7, 8,
9, 10 and 11. Motion, input and collision-scan components match through 2596;
the original is stalled by then while the native safeguard resumes Play at 2597.

This remains one input sequence and one difficulty. Source-derived timeout,
finish-delay, other callback types and helper branches not exercised here have
synthetic checks only. FinishMotion, WallSlide and Exploding still lack complete
body models; the Crash-to-Exploding branch propagates unknown work. Additional
reference cases are required before generalizing coverage to every Air path.
`handlerWorkCycles` uses -2 for unoccupied and -1 for unknown work. The native
entity total becomes -1 at update 2458 because deferred recovery is deliberately
not certified as original behavior; its safeguard remains unchanged.

## VBlank decomposition

The expanded, control-verified capture separates 3,063 VBlank services. All
fixed source parts and the conditional software-reset guard agree exactly.
The guard costs 240 cycles in this replay because reset is enabled; 160 is the
disabled path, not a universal allowance. An actual reset request without the
latch is not certified as a normally returning service.

| VBlank component | Observed T-cycles | Evidence |
|---|---:|---|
| Entry body before DMA | 180 | Source cost checked |
| DMA call and transfer delay | 704 | Source cost checked |
| Joypad sampling | 280 | Source cost checked |
| Display callback dispatch/body | 884–7,464 | Source model checked across 3,063 services |
| Counter/bookkeeping/reset guard | 240 | Conditional source cost checked |
| Pending effect setup | 64–620 | Source model checked across 3,063 services |
| Audio bank switch | 68 | Source cost checked |
| Music driver | 1,612–13,008 | Measured; source model incomplete |
| Bank/register restoration | 120 | Source cost checked |

Interrupt entry and return add 36 cycles. The component ranges cannot be summed
to predict a particular service: their extrema need not occur together. The
analysis rejects missing, unordered or escaped boundaries and removes nested
callback/interrupt work once. These measurements do not feed native gameplay.

Validation: **47 Python tests, 51 synthetic C++ source-work checks**, a rebuilt
Windows executable and 13 automated UI checks. All 3,059 state exports with
accounting enabled/disabled match the previous checkpoint byte for byte,
SHA-256 `8b41e9d4d7a8c2b21d37c54abf16a77b4699de691727e0a765f680f66622a382`.
The instrumented original final memory still matches the uninstrumented control.
Unchanged campaign tests were not repeated for this diagnostic-only change.
Evidence: ignored `local/air-play-irq-timing/`, `local/air-play-build.log` and
`build/ui-window-test.txt`. No original data or replacement preview ZIP is published.

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
& ./local/air-reference-probe.exe local/original-air-verified/inputs.txt --recorded-clock --work-csv local/air-timing/native-work.csv --entities-csv local/air-timing/native-entities.csv --handlers-csv local/air-timing/native-handlers.csv --display-csv local/air-timing/native-display.csv > local/air-timing/native-state.csv
python tools/air_timing.py compare local/air-timing/native-work.csv
python tools/air_timing.py compare-handlers local/air-timing/native-handlers.csv
python tools/air_timing.py compare-entities local/air-timing/native-entities.csv
python tools/air_timing.py compare-display local/air-timing/native-display.csv
python tools/air_reference.py compare local/air-timing/native-state.csv --out local/original-air-verified
```

The pure analysis and synthetic Python tests do not import or require PyBoy.
Capture schema 8 requires handler, animation, collision, motion, input,
VBlank components, nested display boundaries and effect-root workloads; older timing captures
are rejected with a recapture instruction rather than silently skipping evidence.
The standalone C++ checks use synthetic data only and run as part of
`build.ps1 -Test`; they can also be compiled from `tests/air_work_tests.cpp`, `src/air.cpp`
and `src/game.cpp` without the extracted assets.
Capturing is the only emulator-dependent operation. The timing probe deliberately
does not use original positions, allocation results or layouts to drive native
gameplay. Native entity logging occurs before `step`; exclude the player from
that pre-step comparison because the original's preceding display callback can
complete a player resource upload. The separate post-step comparator covers it.

## Display/effect source checkpoint, 2026-10-04

The independent Python source formulas agree with all **3,063** measured display
callbacks and effect-setup intervals. The display model separates map transfer,
dynamic resources, one HUD column, scroll, LCD control, fade and full HUD refresh.
Map transfer remains active when the main-update resource gate is closed; it
takes priority over dynamic copying. The refresh cost includes the mathematical
division quotient's bit count and progress-bar return paths. These formulas use
semantic state, not instruction execution, recorded frame indices or a fitted
allowance. Native models are in `src/air_video_work.h` and `src/audio_work.h`;
unknown display components propagate as -1.

Source analysis also corrected a native progress-bar glyph. For an exact positive
multiple of eight below the six-segment maximum, the original writes full segments
followed by tile 0xf0. The previous native loop left that next tile empty. Zero
progress remains empty, six full segments have no extra terminator, and the
low-byte quotient wrap is retained. All **235** original HUD refreshes match the
independent tile formula. This verifies the refreshed values, not when native
display services occur.

The new direct native display comparison makes the remaining phase gap explicit:
at game update zero the original HUD cursor is 2 and native is 1. The first
display-cost difference is update 11; bar values first differ at 414/622. A
separate control-verified startup trace explains the initial gap. At 03c6, just
after enabling the LCD, IF=0x13 and IE=3; a pending VBlank is serviced at scanline
zero, followed by pending STAT. Only then does 03cb call the counter-change wait
at 2617. The next VBlank precedes the first game update at 03d8. The original
therefore performs two display callbacks before that update. This is source/phase
evidence for future scheduling, not permission to seed the native cursor to a
fitted value. Hooks inside the HALT wait helper stalled the reference tool and
were discarded; only outer boundaries were used for the successful startup trace.

Both expanded captures retain the unchanged control memory SHA-256
`03783c97b547d3d3ee69b720ae5b78228e04ebc961f31eeffadf7ab9cd954eb8`.
Accounting-enabled and disabled native state exports still match the prior
checkpoint, hash `8b41e9d4d7a8c2b21d37c54abf16a77b4699de691727e0a765f680f66622a382`.
Those exports do not include HUD pixels. Effect-cost accounting also preserves
native PCM byte for byte through 240 frames of music and overlapping effects;
this is an accounting regression, not an original-audio parity result.

Validation: **52 Python tests, 65 synthetic C++ source-work checks, 822,497 Air
assertions, 131 audio assertions**, a rebuilt Windows EXE and **13 automated
Windows UI checks**. All 64 recovery phases and four difficulty pilots pass.
Unchanged full campaign suites were not repeated. Evidence stays in ignored
`local/air-display-effect-timing/`, `local/startup-phase.json`,
`local/startup-phase.log`, `local/air-display-build.log`, and the native test logs
under `build/`. No new preview ZIP or final release is produced.

**Runtime timing is still unfinished.** The ordinary Windows loop still advances
one game update per display interval. Display/effect formulas establish source
work, not native phase alignment. Music-driver work, STAT/wait phase and the
independent service/update scheduler remain outstanding.

## Experimental native clock checkpoint - 2026-10-05

The source music model reproduces all 3,063 baseline services and 18,378 voice
calls. Native voice fields also match an isolated replay driven solely by song
and effect requests. Carry, byte-wrap and square-envelope corrections have
regressions. Outer-loop captures validate STAT body costs, wait/resume/tail
paths and startup order against unchanged control memory. Inner HALT hooks were
not used. Idle time is measured evidence, not a work allowance.

The experimental C++ probe advances display/audio/HUD independently of completed
game updates using source work. Initial timer/random/clock phase and
update-aligned buttons are supplied once/per update respectively; counters,
measured costs and original world states are never supplied per update.
Unsupported work/interrupted ownership stops the probe. The normal Windows
application retains its existing scheduler until broader validation completes.

Nine comparisons cover the recovery prefix, four coast difficulties, boost,
acceleration, steering and a successful finish. They match 24 post-update fields
and all checked service fields across 28,103 updates and 28,153 VBlanks. The
intentional recovery boundary is not modeled as original work. The steering case
includes twelve extra VBlanks: placement, progressive unused-slot clearing and a
preparation entry between entities. Separate single-DMA-hook captures verify
158,840 published sprite slots across steering and the successful finish.
Presence, coordinates and flags are checked; tile contents, pixels, PCM and
subinstruction IRQ latency are not. A combined DMA/outer-loop capture changed
control memory and was discarded.

New reference comparisons exposed boost-expiration pose and severity-drag RNG
errors; both are corrected. A successful original landing validates finish-sound
ownership and fixes the final result branch, where the port wrongly generated
particles. WallSlide and FinishMotion source costs now match all 35/128 calls in
that capture. All six ordinary-clock work phases and their entry counters match
across all nine cases; 28,103 updates imply 168,618 checked work phases. New
regressions also cover camera-lead direction, padded-map scroll limits and enemy
penalty work. The clock candidate commits the busy/ready store at its source
boundary and publishes sprite Y/X/tile/flags progressively. Row-building
interruptions remain unsupported; only the no-row callback with an already-clear
pending flag is safe. Latest validation passes 72 Python, 89 synthetic
source-work checks, the full native suites with 819,624 Air and 150 audio
assertions, four input-only Air successes, all 64 recovery phases and three
campaigns. Logs/data remain ignored/local; detailed limits and Windows checks
are in STATUS.md and ACCEPTANCE.md.

## Required next work

The subsequent [pause/input checkpoint](AIR_PAUSE.md) validates three original
pause source paths, corrects native counter/input and paused effect ordering,
and repeats all nine clock cases with per-display held buttons. Separate
captures also compare native fresh-edge calculations. Pause's variable LCD
copy polling and native entry/return scheduling remain open; reference poll
counts are not native work inputs. Latest tests pass 82 Python and 92 synthetic
source-work checks, the full native suites/three campaigns and Windows UI
tests with normal and failed audio output.

1. Expand the existing FinishMotion/WallSlide and Exploding evidence to other
   branches and additional collision cases. Reconstruct missing work and check state/effect/cost ownership; unknown
   paths remain -1. Expand music branches without an existing reference witness.
2. Account for interrupts within entity updates, resource/map callbacks and
   sprite geometry and row construction. Piece writes and no-row callbacks
   now have source ownership, checked in the winning case. Do not publish a fully prepared sprite list before its source
   preparation completes.
3. Reconstruct native pause LCD polling, normal UI startup and result-screen
   setup beyond the bounded final-wait/audio-stop/fade evidence in AIR_EXIT.md. Integrate the accepted scheduler
   into Windows only after those paths can be handled faithfully.
4. Expand original comparisons to all stunts/difficulties and matched pixels/PCM,
   then complete human/independent Windows tests and release packaging under
   ACCEPTANCE.md. Synthetic/native campaigns alone cannot establish fidelity.

Do not hardcode overrun update numbers, drive cartridge timing from Windows CPU
speed, add a runtime emulator or mark release timing accepted at this
checkpoint.

## Explosion and wait-counter ownership - 2026-10-05

An input-only easy-difficulty capture with alternating steering period 52
reaches a damage result after 2,077 updates. All state and update/handler costs
agree, including 63 Exploding and 61 Return calls. The new source explosion
formula separates countdown-only, final hide/animation, particle allocation,
RNG and alternating sound paths. Invalid countdowns remain -1; this does not
certify every possible allocation or collision branch.

A counter-read boundary in 2617's wait was previously charged as one block.
If VBlank runs during the preceding CALL/PUSH, the original reads the updated
counter and needs another service before returning. The native model now
charges that prefix before taking its snapshot, then commits the read before
a pending service. Total work remains unchanged. Two synthetic regressions
distinguish an interrupt before the read from one pending during the read.

The corrected ordinary clock matches all 2,077 updates and 2,105 services of
this case, all six work phases/entry counters, 84,200 sprite slots and 2,105
independently captured held/fresh inputs. All nine previous cases still pass.
Combined evidence now covers 30,180 updates, 30,258 services and 181,080 phases;
three sprite/input captures cover 243,040 slots and 6,076 samples. Latest
validation passes 84 Python tests, 99 synthetic source-work checks and 13
Windows UI checks on the rebuilt EXE. Prior full gameplay/campaign tests remain
applicable because this work changes accounting, not production gameplay.

An independent loop capture validates 2,077 waits with one or two VBlanks,
2,106 STAT bodies and all resume/tail costs. Return addresses distinguish a
service before the snapshot from a HALT wake. The last incomplete interrupt
is explicitly recorded/excluded; changed control still rejects the capture.
Idle remains a measurement, not a native work allowance.

Original captures and logs remain ignored/local. The new phase agreement does
not establish native pause LCD polling, unsupported interrupted entity/resource
or row work, UI startup/exit, production scheduler integration, matched pixels
or PCM, or final release acceptance.

## Final gameplay display wait - 2026-10-05

The ordinary-clock probe can now continue through 0400's final display wait,
stopping at 0403 before audio stop and the outgoing fade. The original leaves
FFAE clear throughout this wait; the native callback therefore retains the busy
resource gate rather than enabling an extra graphics upload. It continues HUD,
display counter, button sampling and music services without another game update.

Three new control-verified recordings extend existing input-only paths by two
hardware frames after the result: damage/explosion, successful finish and
normal-difficulty timeout. The native final wait matches original entry/exit
counters, elapsed cycles, one complete display service and the retained gate in
all three cases. The measured durations differ (47,740 / 31,940 / 58,636 cycles);
they are comparison targets, never native delays. State, phase and service
comparisons continue to match across the 8,417 repeated gameplay updates and
8,476 services including these waits. The damage case additionally matches all
84,240 sprite slots and 2,106 independently recorded held/fresh samples through
the final service. These are extensions of three of the ten cases, not three
new independent gameplay paths.

Reference tools now allow a bounded post-result recording and compare the final
wait explicitly. Missing boundaries, changed controls, enabled resource gates
and incomplete final intervals are rejected. Latest validation passes 87 Python
and 100 synthetic source-work tests. The existing 13-check Windows UI run passed
after the accounting-only change; no new production scheduling behavior is
claimed. Evidence stays under ignored local/air-final-{wait,win,timeout}-*.

Audio stop at 0403, outgoing fade/result setup and normal UI startup are still
outside this clock's accepted scope. Pause LCD polling, interrupted entity/
resource/row ownership, production integration, other stunts, matched pixels/PCM
and human/independent Windows tests remain required by ACCEPTANCE.md. The
complete port and final distribution are not accepted.

## Outgoing fade and terminal sprite publication - 2026-10-05

Three control-verified recordings extend the existing success, damage/explosion
and timeout paths through the complete outgoing fade. All 222 semantic phases
match: audio-stop work, fade entry, 24 palette writes, 96 waits and their tails.
All 96 display services separately match source component costs and native
HUD/bar, held inputs, effects and disabled music. Separate input captures match
8,572 held/fresh samples through the 8,417 repeated gameplay updates and exit.
These extend three of the ten existing cases; they do not add independent
normal-play coverage. See AIR_EXIT.md for method, reproduction and limits.

The production Windows outro now publishes the sprite list prepared by the
terminal update. Previously it retained the preceding visible list. All-five-
stunt marker regressions confirm publication while entities, gameplay timer
and pending resource transfers stay unchanged. This fixes a display boundary,
not the production scheduler or scanline pixel behavior.

Validation: 94 Python tests and 102 synthetic source-work checks; full native
suites, all 64 Air recovery phases, four input-only difficulty successes and
all three full campaigns pass. Air passes 819,624 assertions and audio 150.
The rebuilt Windows EXE passes 13 automated normal and 14 actual audio-open-
failure UI checks. The ROM-free preview archive's 11 file hashes match its
manifest and its EXE matches the tested build. Bundled extraction succeeds in
a local folder containing spaces; both 13/14 UI variants then pass while
launched from a different working directory. The preview is labeled unfinished
and records its pre-commit dirty source identity. It contains no ROM/assets;
extracted data stays in the ignored local test folder. These checks use one
Windows host and synthetic messages, not human/device-removal acceptance.
No unchanged campaigns were repeated before this production presentation change.

The candidate clock now reaches 0409 after final wait, audio stop and outgoing
fade. Result-screen DI/setup, normal UI startup, native pause LCD polling,
unsupported interrupted entity/resource/row work and production integration
remain open. Original reset voice-state parity, matched pixels/PCM, other
stunts and human/independent Windows acceptance are still required. The private
repository and continuation automation remain active; no final release is made.

## Result-test interrupt boundary - 2026-10-05

A second input-only easy winning replay alternates steering every 16 updates
and reaches result 3 with 11 items after 2,621 updates. Its experimental clock
initially stopped after update 2,414. The original interrupt returned to 03fd:
it occurred in the result read/rotate/back-edge test, after all six gameplay
phases, while FFAE was still zero. It did not interrupt a figure's handler.
The probe now accepts this completed-state loop boundary. Unsupported entity,
resource and row ownership continues to reject; error messages include phase,
tick and service identifiers for accurate diagnosis.

The entire new replay matches 2,621 updates, 2,651 complete services, 15,726 work
phases/entry counters, 106,040 sprite slots and 2,651 independently captured
held/fresh samples. The terminal extra partial service is outside the native
comparison scope. Combined ordinary-gameplay evidence now comprises eleven
cases, 32,801 updates, 32,909 services and 196,806 phases; four sprite/input cases
cover 349,080 slots and 8,727 samples. The separate three final-wait/fade cases
remain extensions, not additional independent gameplay cases.

This is a probe/diagnostic change with a new original witness. The production
Windows build, full native/campaign tests, normal/failed-audio UI checks and
portable preview from the outgoing-fade checkpoint remain applicable; unchanged
campaigns were not repeated. Captures and logs remain ignored/local under
local/air-steer16-*. Production integration and the remaining ACCEPTANCE.md
requirements are still open. No final-release status is claimed.

## Independent original reference - 2026-10-05

The locally installed PyBoy reference uses a fixed LCD pixel-transfer duration,
which cannot establish original pause polling behavior. An independent official
SameBoy 1.0.3 reference (pinned source, open boot ROM, DMG-B model) is now set up
under ignored .tools/. It is used only for authorized original measurements;
no reference core, DLL, boot ROM or recording enters the port or preview.
See REFERENCE_BACKENDS.md for the hardware-source link and reproducible setup.

The first control-verified SameBoy normal-coast case independently matches
3,989 native ordinary-clock updates, 3,990 complete services, 23,934 source
phases/entry counters, 159,600 sprite slots and 3,990 held/fresh samples. This
repeats an existing scenario on another engine; the eleven earlier PyBoy cases
remain separately counted. All measurement runs preserve the uninstrumented
end-state control. A SameBoy pause recording validates four copies, 35 paused
services/waits and 34 frozen-world intervals. Its LCD poll counts are observed
comparison data, never native clock inputs; independent native polling work
remains required.

Backend, revision/model and independent recording provenance are now explicit;
mixed records are rejected. The separate reference adapter exposes read-only
observations and button inputs with unmodified save/load states. The official
source revision and library/boot identity are checked. Latest pure Python tests
pass 98 checks. Native code/build/three campaigns and both Windows/portable UI
variants remain unchanged from the fully tested outgoing-fade checkpoint, so
those suites were not repeated. The overall port is still incomplete.
