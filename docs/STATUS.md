# Project status â€” September 29, 2026

## Objective

Produce a faithful **native Windows** port of the supplied Game Boy release,
without CPU emulation or replacing the original rules with a loose remake.
Private repository: https://github.com/KarlLaberfeld/TICD-Recompilation

**The overall task is not complete.** The Windows executable is a development
build of Roof Jump, Air Bumper and Ski Slope, not a complete game.

Repository descriptions and documentation must be in English. The working
conversation remains in German. Continue development until the port is complete.

## Implemented

- Hash-validated local extraction and a static disassembly tool.
- Original roof backgrounds, 69 sprite definitions, and four difficulty layouts.
- Native C++/Win32 application with keyboard controls, pause, and restart.
- Partial translation of roof physics, animation scripts, and object interactions.
- Compiler: `.tools/zig-x86_64-windows-0.16.0/zig.exe`.
- Build: `powershell -NoProfile -ExecutionPolicy Bypass -File ./build.ps1 -Test`.
- Local outputs: `build/CrashDummies.exe`, `build/crash.dat`, `build/air.dat`, and `build/ski.dat`.
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
3. Reconstruct the other two stunts from their initialization and handlers.
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
