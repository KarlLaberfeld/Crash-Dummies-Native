# The Incredible Crash Dummies — native Windows port

**Work in progress. This is not a complete port.**

This project aims to faithfully reimplement the Game Boy release as a native
Windows game. The current build contains **Roof Jump**, with reconstructed
original graphics, four difficulty layouts, and a partial translation of the
original game logic. The other four stunts, original menus, audio, and full
behavioral validation remain unfinished. Air Bumper reconstruction is underway.

The Windows application uses C++ and Win32. It contains no Game Boy CPU
interpreter, JIT recompiler, or emulator core. The cartridge is read offline
only to extract identified graphics and game data. At runtime, the application
loads the generated `crash.dat` asset package.

## Running locally

After building, open `build/CrashDummies.exe`. Keep `crash.dat` beside it.
The executable runs directly on Windows x64. Python and Zig are needed only
for extraction and compilation.

| Key | Action |
|---|---|
| Enter | Start or pause the stunt |
| Left / Right | Move sideways |
| Up / Down | Change falling posture |
| Z or A | Primary action / jump |
| X or S | Secondary action |
| Esc | Pause / resume |
| R | Restart the stunt |
| 1–4 | Select difficulty and restart |

Roof Jump begins with the reconstructed camera flyover. Losing window focus
pauses the game. The development window currently uses German labels.

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
```

Native tests cover selected rules derived from the original, deterministic
replays, and completed roof-stunt runs. They **do not establish full fidelity**
to the original game. Captured images remain local in the build directory.

## Project layout

- `src/`: native game logic, renderer, and Windows application.
- `tools/extract.py`: reproducible extraction with cartridge hash validation.
- `tools/disassemble.py`: static inspection only; does not execute the ROM.
- `tests/`: synthetic format checks and native rule/replay tests.
- [Reverse-engineering notes](docs/REVERSE_ENGINEERING.md): documented structures and routines.
- [Project status](docs/STATUS.md): current progress and remaining work.

ROMs, extracted original graphics, asset packages, and local analysis dumps
are excluded from the repository. Generate assets from your own original
cartridge file. Original game content and trademarks belong to their respective
owners. This is an unofficial project.
