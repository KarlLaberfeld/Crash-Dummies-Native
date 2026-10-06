# The Incredible Crash Dummies — native Windows port

**Work in progress. This is not a complete port.**

This project aims to faithfully reimplement the Game Boy release as a native
Windows game. The current build contains **Roof Jump**, **Air Bumper**, **Ski Slope**, **Bomb Factory**, and **Cruise Missile**, each with
reconstructed original graphics, four difficulty layouts, and a partial native
translation of the original game logic. The original title/options pages, stage
instructions, campaign progression, result portraits and ending are connected.
The original copyright screen, opening/result fades, high-score name entry, pay/time
counting, hidden password entry and music test are implemented. Perfect results
include the original four-emitter celebration. Title exit and first-instruction
fades, and the later 64-update alternating-map transition, are reconstructed.
Ending and high-score entry now include their blocking fades and input waits.
Finishing name entry clears its character strip, then either hands off to the
other player or fades back through the title opening without repeating copyright.
Stunts fade in
while gameplay continues, following the original global frame cadence. Remaining presentation
timing, exact sound fidelity, and full behavioral validation remain unfinished.
Native music and sound output now cover the original 14 songs and 26 effects,
with animation and key gameplay events connected; exact audio equivalence is
not yet established. Gameplay rendering now preserves individual sprite pieces,
original palette/overlap rules, the 40-piece total limit and the ten-piece limit
per image row. Dynamic graphics use the original two alternating resource
buffers, including the shared body-part graphics after a Roof landing.
Exact presentation phase still needs reference validation.

Air Bumper includes one documented native stability correction: if the crash
animation is still running when recovery is requested, the request is retained
until that animation finishes. This prevents a reproducible permanent stall.
The original ROM reproduces the failure in a separate reference emulator.
An experimental native clock now matches eleven Air reference cases without
supplied per-update counters, including partial sprite publication and buttons
sampled at each display service. Three additional original pause captures check
counter continuity, retained gameplay and suspended/resumed music; the native
pause now continues the display counter and samples held buttons. Windows
scheduler integration, remaining timing branches, image/audio parity and
physical-hardware behavior remain open; see [timing evidence and limits](docs/AIR_TIMING.md)
and [the original comparison](docs/ORIGINAL_COMPARISON.md).
See [pause and input evidence](docs/AIR_PAUSE.md) for the remaining boundaries.
A bounded native pause candidate is now coupled to gameplay and software audio.
Three independent original controls match 7,506 updates through post-resume
stunt end, including 317,080 sprite slots, 47,562 selected voice/work rows,
native effect requests, 5,252 graphics/status accesses and 1,332 storage bytes.
The pending startup services also agree; see [startup limits](docs/AIR_STARTUP.md).
Production integration, full pixels/PCM and hardware
qualification remain open; see [candidate evidence](docs/AIR_PAUSE_CANDIDATE.md).
Selected complete images now also agree: 262 unique matched Air frames, including the
incoming fade, ordinary play, pause, post-resume play and selected outgoing
fades. The bounded image probe now owns the known final-row object cancellation
and separate visible palette writes; Windows clock integration remains open. See
[image alignment and limits](docs/AIR_PIXELS.md); this is bounded evidence,
not full presentation or final-release acceptance.
The final display wait, audio-stop work and outgoing fade also match three
bounded original Air recordings; see [exit evidence](docs/AIR_EXIT.md).
An independent reference now also establishes a shared-scratch interruption
inside Air's placement scan. The native clock matches the resulting allocations
and all sixteen entity slots; see [placement evidence](docs/AIR_PLACEMENTS.md).
All 77 placement interrupt vectors and 836 pause counter-wait vectors now agree
on absolute source time. The identified source completion boundaries fix the
two previously rejected neighboring images. Protected pause crossings remain
unqualified and reject until measured; see [IRQ limits](docs/AIR_IRQ_BOUNDARIES.md).
The [reference tools](docs/REFERENCE_BACKENDS.md) remain separate from the game.

The Windows application uses C++ and Win32. It contains no Game Boy CPU
interpreter, JIT recompiler, or emulator core. The cartridge is read offline
only to extract identified graphics and game data. At runtime, the application
loads the generated `crash.dat`, `air.dat`, `ski.dat`, `bomb.dat`, `cruise.dat`, `ui.dat`, and `audio.dat` asset packages.

## Running locally

After building, open `build/CrashDummies.exe`. Keep `crash.dat`, `air.dat`, `ski.dat`, `bomb.dat`, `cruise.dat`, `ui.dat`, and `audio.dat` beside it.
The executable runs directly on Windows x64. Python and Zig are needed only
for extraction and compilation.

| Key | Action |
|---|---|
| Tab | Original Select button: open options or toggle players |
| F1 / F2 / F3 / F4 / F5 | Development mode: select Roof / Air / Ski / Bomb / Cruise |
| F6 | Return to the title page (abandons the current campaign) |
| Enter | Start campaign, skip instructions, continue results, or pause gameplay |
| Left / Right | Roof: move sideways; Air: tilt; Ski: steer; Bomb: change belt; Cruise: rotate |
| Up / Down | Roof: change falling posture; Ski Down: straighten; Bomb: move |
| Z or A | Roof/Ski: jump; Air: ascend; Bomb: defuse; Cruise: thrust |
| X or S | Roof: secondary action; Air: descend; Ski: accelerate; Bomb: punch |
| Esc | Pause / resume |
| R | Restart the stunt in development mode |
| 1–4 | Select difficulty and restart in development mode |

The application shows the original copyright sequence before the title page. Press Tab for one/two-player
options; Z/X advances title pages. Results alternate between active players.
Results count pay and remaining time into savings. Z/X or Enter accelerates
counting; press again to continue. For a qualifying high score, Left/Right scrolls
the original character strip and Z/X confirms. Select its backspace/end symbols
to delete/finish. High scores remain in memory for the current application session. Roof Jump begins with the reconstructed camera flyover. Losing window focus
pauses the game. Campaign pause uses the original bottom status strip and
suspends music/effect sequencing until play resumes. The development window
currently uses German labels.

On a stationary title page (outside options), press Up, Down, Left, Right to
open the original password screen. Left/Right selects a digit and Up/Down changes
it. Enter submits and returns to the title after feedback; Z/X submits and
returns to password entry. Original passwords select the starting stunt,
difficulty, or music test. Password data are extracted locally from your ROM.
In the music test, Left/Right selects a tune and Up/Down selects an effect.
Z starts the tune, then triggers the selected effect while that tune is playing;
X stops playback and Enter exits. The counters use the original hexadecimal display.

## Building

Requirements: Windows x64, Python 3.10+, and [Zig 0.16.0](https://ziglang.org/download/).
No additional Python packages are required. Put Zig on PATH or pass its path
using `-Compiler`.

```powershell
./build.ps1 -Rom 'path/to/original.gb' -Test
```

If the project directory contains exactly one `.gb` file, `./build.ps1 -Test`
is sufficient. Only the documented US/EU revision is accepted: 131072 bytes,
SHA-256 `ef563c4a4b063ea045d71b435dd078c19d0738f85079928803167cee8f34a4ec`.

```powershell
python -m unittest discover -s tests -p 'test_*.py'
./build/CrashDummies.exe --self-test
./build/CrashDummies.exe --capture
./build/CrashDummies.exe --audio-smoke-test
./build/CrashDummies.exe --ui-smoke-test
./build/CrashDummies.exe --ui-no-audio-test
```

Native tests cover selected rules derived from the original, deterministic
replays, and terminal results on all four layouts of the implemented stunts.
Input-only test controllers complete all five stunts on all four difficulties;
their recorded button streams are replayed from fresh starts. These controllers
inspect native state and forecast moves. A campaign harness also completes all
20 stunts with carried timer/random phase and reaches the ending. These are not
human playthroughs or comparisons against the original. Tests **do not establish full fidelity**
to the original game. Captured images and the generated title-music WAV remain local in the build
directory. The audio smoke test checks Windows output over 300 updates; its
device/drop report is saved locally as `audio-output.txt`.
The UI smoke test sends Windows keyboard/focus/resize messages through the
application window and records assertions in `ui-window-test.txt`. It is
automated host integration coverage, not human visual acceptance.
The no-audio variant requests an invalid Windows output device to exercise
the real audio-open failure path while running the same UI checks. It does
not change system devices. Its separate logs are `ui-window-no-audio-test.txt`
and `audio-output-no-device.txt`. This verifies graceful startup after an
audio-open error; physical device removal and another Windows host remain
manual acceptance checks.

## Local preview packages

After building, run `./package.ps1` to create a preview ZIP in ignored `dist/`.
It contains the Windows executable and asset preparation tools, but no ROM or
original assets. After extracting it, run `./Prepare-Assets.ps1 -Rom 'path/to/original.gb'`
with Python 3.10+ once, then start `CrashDummies.exe` without Python.

For a ready-to-run local copy, use `./package.ps1 -IncludeLocalAssets`. That
archive includes extracted game data and must remain local. Both variants
include file hashes and source revision information, and are explicitly
unfinished previews. See [release acceptance](docs/ACCEPTANCE.md) for remaining
requirements before a final release.

## Project layout

- `src/`: native game logic, renderer, and Windows application.
- `tools/extract*.py`: reproducible extraction with cartridge hash validation.
- `tools/disassemble.py`: static inspection only; does not execute the ROM.
- `tests/`: synthetic format checks and native rule/replay tests.
- [Reverse-engineering notes](docs/REVERSE_ENGINEERING.md): documented structures and routines.
- [Project status](docs/STATUS.md): current progress and remaining work.
- [Air timing reconstruction](docs/AIR_TIMING.md): verified partial work costs, reused-slot animation correction and remaining scheduler work.

ROMs, extracted original graphics, asset packages, and local analysis dumps
are excluded from the repository. Generate assets from your own original
cartridge file. Original game content and trademarks belong to their respective
owners. This is an unofficial project.

Optional original-reference measurements now also support a separately compiled,
independent SameBoy backend. It is excluded from the native build and preview;
see [reference setup and evidence](docs/REFERENCE_BACKENDS.md).
