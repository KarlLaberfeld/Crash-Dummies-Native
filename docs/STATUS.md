# Project status â€” September 29, 2026

## Objective

Produce a faithful **native Windows** port of the supplied Game Boy release,
without CPU emulation or replacing the original rules with a loose remake.
Private repository: https://github.com/KarlLaberfeld/TICD-Recompilation

**The overall task is not complete.** The Windows executable is a development
build of Roof Jump, Air Bumper, Ski Slope, Bomb Factory and Cruise Missile, not a complete game.

Repository descriptions and documentation must be in English. The working
conversation remains in German. Continue development until the port is complete.

## Implemented

- Hash-validated local extraction and a static disassembly tool.
- Original roof backgrounds, 69 sprite definitions, and four difficulty layouts.
- Native C++/Win32 application with keyboard controls, pause, and restart.
- Partial translation of roof physics, animation scripts, and object interactions.
- Compiler: `.tools/zig-x86_64-windows-0.16.0/zig.exe`.
- Build: `powershell -NoProfile -ExecutionPolicy Bypass -File ./build.ps1 -Test`.
- Local outputs: `build/CrashDummies.exe`, `build/crash.dat`, `build/air.dat`, and `build/ski.dat`, and `build/bomb.dat`.
- Source and documentation published to the private GitHub repository.
- Windows x64 GUI executable verified as PE subsystem 2 (no console window).

## Resume after usage reset â€” September 29, from 16:59 Europe/Berlin

The chat history records usage-limit failures at 14:07, 15:05, and 16:07.
Normal usage was available on resuming, with 5% of the five-hour window used.
No reset credit was consumed.

Reconstructed and corrected:

- Sprite origins and mirror centers from the original renderer, aligning
  graphics with collision positions. Current roof asset format: `TICDNAT4`.
- Visibility bounds, object respawning, and permanent target collection.
- Plane/balloon activation after the flyover and jump-input ordering.
- Upward awning collisions, plane stun, and simultaneous posture input.
- Original landing/body-piece animation, head-first impact, delayed results,
  and distinctions between success, perfect results, and insufficient breaks.
- Original HUD with four score digits, time, height bar, and gradual field updates.
- Original alternating cloud motion.

Validation: 11 Python tests and 48,863 native assertions passed. All four roof
layouts reach a terminal result without invalid animation commands. The count
includes repeated invariants, not that many independent test cases. Window-start
and image-capture checks passed. This is static source-derived validation,
not a demonstration of complete fidelity.

Published roof checkpoint: `763317baa9692388e2240a9f47bc9e9496284d1b`.

## Air Bumper work in progress

`tools/extract_air.py` now reconstructs the four maps, original graphics,
collision probes, speed/tilt tables, object definitions, and animation graphs.
The local output is `build/air.dat` (`TICDAIR3`). Native integration is now in
`src/air.h` and `src/air.cpp`, selectable with F2 (F1 returns to Roof Jump).
The implementation includes intro/countdown, movement and camera, six terrain
probes, collision response, pickups, breakable objects, damage, crash/return
states, finish gates, animations and the original gradual HUD updates.

The usage limit reset before the 23:06 Europe/Berlin heartbeat; normal usage
was available at 0%. No reset credit was consumed. Development resumed in the
same project. English README, notes and status were published in commit
`7ec557af391696c1184248c302d3369948db2815` before this continuation.

Validation: 15 Python tests, 48,863 roof assertions, and 449,064 Air assertions
passed. The assertion totals include repeated replay invariants, not independent
test cases. Twelve Air replays (three input patterns per difficulty) reach valid
terminal results. The easy steering replay reaches a successful gate result with eight items;
other runs end with insufficient quota, timeout or damage failure. These are not successful complete-game runs
or a proof of equivalence. Native window-start and frame-capture checks passed.

Original asynchronous sprite transfers are now modeled in both implemented
stunts, including map-row priority and animation waits. Remaining Air differences
include original sprite capacity/priority, exact palette/frame phase and
menu-seeded randomness; reference timing still needs validation.
The development selector and result overlay are temporary, not original menus.
Original audio and campaign/life integration are absent.

| Difficulty | Map rows | Objects | Seconds | Quota |
|---|---:|---:|---:|---:|
| Easy | 184 | 78 | 40 | 14 |
| Normal | 236 | 131 | 60 | 15 |
| Hard | 256 | 143 | 70 | 24 |
| Very hard | 256 | 143 | 70 | 16 |

## Remaining work

1. Validate and refine Air Bumper's original timing and edge cases, including
   reference timing and successful runs beyond the easy steering replay.
2. Continue roof fidelity checks: animation transfer timing, lifecycle,
   plane/balloon/rope interactions, and landing. See `REVERSE_ENGINEERING.md`.
3. Validate Ski Slope, Bomb Factory and Cruise Missile with successful natural playthroughs.
4. Port original menus, campaign, ending, and music/sound.
5. Validate full playthroughs and fidelity, then prepare a portable distribution.

## Automatic continuation

The user explicitly requested automatic resumption after a usage-limit reset.
The active chat automation is `crash-dummies-nach-limit-reset-fortsetzen`,
scheduled hourly at minute 05. After a limit interruption, continue in this
project and chat. Keep ROMs and extracted assets local. Update this status
before ending a work session. Disable the automation only when the complete
port is finished. Do not create additional chats.

Native Air Bumper checkpoint published as `d3dcccae0379871a94aa45b6712847855312efb3`.
Later local work reconstructs resource-transfer timing and begins Ski Slope.


## Ski Slope native integration — latest continuation

Ski Slope is now selectable with F3. The local data package is `ski.dat`
(`TICDSKI1`); extractor `tools/extract_ski.py`, native code `src/ski.*`,
tests `tests/ski_tests.cpp`. All four layouts are reconstructed: rows
120/108/152/200, objects 52/58/77/124, flags 30/22/41/31, time 80/80/90/90.
Implemented: turning/straightening animations, velocity approach, jump/shadow,
terrain and object collisions, flags, crash/return, finish-zone depth and quota,
seven-column HUD cycle, native sprite-resource transfer queue. Window startup
and capture pass. All 15 Python tests and native suites pass: roof 48,863,
Air 449,064, Ski 297,291 assertions (mostly replay invariants). Twelve Ski
replays terminate in collision failure; successful Ski runs remain unverified.
Bomb Factory, Cruise Missile, original menus/campaign/ending/audio and full
fidelity checks still remain. The complete port is NOT finished.

Last usage check: 99% of the five-hour window used; reset timestamp 1790734021.
Keep the existing automatic continuation active. Resume from this checkpoint,
validate Ski edge cases and successful traversal, then reconstruct Bomb Factory
(initialization 00:0fce, player kind 45, handler 01:6ef2). Do not create chats.
Graphics-queue checkpoint on GitHub: 7b262277afb73cd64829db17b12f5f353dce34d1.

The September 30, 03:06 UTC heartbeat found normal usage available (5% used).
Development resumed without consuming a reset credit. The previous Ski upload
had failed before its commit was created; local source and tested build survived.

## Bomb Factory native integration - September 30

Ski checkpoint is published as `db6107646cd89afc79ad8f815501156084cc41d8`.
Bomb Factory is selectable with F4. The extractor reads the fixed room,
33 sprite frames, four original spawn distributions, and six animation graphs.
The native implementation includes three belt speeds, six spawn markers,
press-edge lane changes, frame-transfer-gated positioning, walking, defusing,
punching, bomb falling/explosion, bonuses, quota and failure/perfect results.
Animation callbacks are decoded through an explicit allowlist into native
collision events; no cartridge instruction execution has been added.

The native Bomb suite passes 407,564 assertions (mostly replay invariants).
Twelve replays end in belt-loss failure; successful natural play remains
unverified. Synthetic tests cover success thresholds separately. Frame capture
shows the original room and actors. Menu-derived random seed/frame phase,
sprite hardware priorities and exact original timing remain open. Continue
with Cruise Missile (00:1245, kind 57, 01:73ed), then original menus, campaign,
ending, audio and fidelity validation. The complete port remains unfinished.
Keep automatic continuation active.

## Cruise Missile native integration - latest checkpoint

Bomb Factory was published as `7911ece7e42c2095ecab6dceb3d6a6403cc8ecb4`.
Cruise Missile is now selectable with F5. Local `cruise.dat` (`TICDCRU1`)
contains the original column-major 128-by-16 map, 42 frames, and four object
lists (13/27/34/38 entries). Native logic includes launch/ignition, sixteen
headings, thrust and gravity, camera/terrain probes, magnets, rockets,
projectiles, spring hazards, extra lives, target success and failure states.
All native suites pass; Cruise adds 297,036 assertions, mostly replay invariants.
Its twelve input-pattern replays fail on collisions; synthetic target tests
exercise both successful endings. A successful natural course remains unverified.
Capture shows the original map and missile. The complete port is NOT finished.

Next: audit original byte-wrapped collision rectangles across stunts; implement
original menus, campaign/lives/score/results, ending and native audio. Validate
natural playthroughs and timing. Cruise currently returns blank terrain outside
the declared map instead of interpreting adjacent original RAM. Shared remaining
differences include sprite hardware limits, palette phase, menu-seeded randomness
and the development selector. Keep the automatic continuation active.

## Collision audit, campaign rules and title assets - latest work

Cruise checkpoint published: `4e265f254a6e9aee26d0f1fbb3f30f51aad45f84`.
All five stunts now share the original byte-wrapped, unsigned collision rectangle
comparisons (00:1747/1834); quantization and asymmetric edge contact have targeted
regressions. Native Roof now passes 48,868 assertions; other stunt totals are
unchanged. All 18 Python tests and 59 new campaign-rule assertions pass.

`src/campaign.h` reconstructs the outer loop, but is NOT connected to interactive
play yet: five starting lives, independent alternating players, failed-attempt
pay discarded, successful pay and time transferred into six-digit savings,
perfect doubling, Bomb time-bonus suppression, five days per difficulty, and
ending after the twentieth successful stunt. Extra lives apply on failed runs too.
`tools/extract_ui.py` and `src/ui.*` reconstruct the six stationary title pages,
original font, default high scores and options pointer. `ui.dat` stays local.
`--capture` now writes title-0.bmp through title-5.bmp using the native renderer.
The interactive executable STILL uses its development stunt selector.

Next integration work: connect campaign state, original title/options and stage
instruction/result screens to the Windows application. Preserve actual original
flow rather than inventing a replacement menu. Title transition scrolling and
raster phase remain unported. Then high-score entry, ending and native audio.
Continue natural-play and frame/timing fidelity validation; the port is unfinished.
All source/docs stay English; original data stay excluded. Automation stays active.
