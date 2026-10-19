# Crash Dummies Native

A native Windows reconstruction of **The Incredible Crash Dummies** for Game Boy.
Written in C++ and Win32, with no Game Boy CPU interpreter, JIT or emulator core.
This is a manually reconstructed port, not an automatic static recompilation.
It is unofficial and unaffiliated with the original rights holders.

**0.1.0-alpha.1 is an experimental preview, not a complete or fully faithful port.**
All five stunts are connected to the campaign, but original timing, presentation
and audio validation remain incomplete. Controller support has automated coverage;
physical controller testing is still outstanding. See the [feature and limitation
table](#features-and-limitations) before downloading.

## Download and quick start

1. Download the Windows x64 ZIP from [Releases](https://github.com/KarlLaberfeld/Crash-Dummies-Native/releases).
2. Extract the whole ZIP to a writable folder.
3. Install Python 3.10+ for one-time asset preparation. In PowerShell, run this
   from the extracted directory:

   ```powershell
   ./Prepare-Assets.ps1 -Rom 'C:\path\to\your\original.gb'
   ```

4. Start `CrashDummiesNative.exe`. Python is not needed while playing.

The release contains **no ROM or extracted game data**. Supply your own original
cartridge file. Only the 131,072-byte US/Europe revision with SHA-256
`ef563c4a4b063ea045d71b435dd078c19d0738f85079928803167cee8f34a4ec`
is supported. No ROM download links are provided.

Keep `crash.dat`, `air.dat`, `ski.dat`, `bomb.dat`, `cruise.dat`, `ui.dat` and
`audio.dat` beside the EXE after preparation. An incorrect ROM is rejected.
If PowerShell blocks scripts, inspect the downloaded script and use Windows'
file-unblocking facility for that file; no system-wide policy change is needed.

## Features and limitations

| Feature | Alpha status |
|---|---|
| Roof Jump, Air Bumper, Ski Slope, Bomb Factory, Cruise Missile | Implemented, four difficulty layouts each |
| Campaign, alternating two players, results, ending, name entry | Implemented; automated native campaign coverage |
| Original menus, passwords and music test | Implemented |
| Music and effects | 14 songs / 26 effects; exact output parity unverified |
| Keyboard and Xbox-compatible XInput controller | Supported; one pad shared by alternating players |
| Resizable window, integer pixel scaling, focus-loss pause | Supported |
| High scores | Current application session only |
| Save states / campaign resume / persistent settings | Not implemented |
| Remapping / fullscreen / in-game volume settings | Not implemented |
| Complete original timing | Experimental diagnostic work; not integrated into the Windows scheduler |

Air Bumper retains crash-recovery requests until the crash animation finishes.
This intentional stability correction avoids a stall also reproduced in the
original. See [recovery analysis](docs/AIR_RECOVERY.md).

## Controls

| Action | Keyboard | XInput controller |
|---|---|---|
| Move / navigate | Arrow keys | D-pad or left stick |
| Original A | Z or A | A |
| Original B | X or S | B |
| Start / continue / pause | Enter | Start / Menu |
| Select / options | Tab | Back / View |
| Pause / resume | Escape | Start / Menu |
| Return to title; abandon campaign | F6 | Keyboard only |

The first detected controller remains selected until disconnected. Connect it
at any time; release mapped buttons and center the stick before using it.
Disconnecting pauses gameplay. Focus loss releases inputs and pauses gameplay;
returning focus requires a fresh press to resume. A fixed per-axis deadzone
filters the left stick. DirectInput-only devices, vibration and remapping are
not supported. Physical controller testing remains outstanding; automated tests
cover mapping, edges, reconnect/focus protection and Windows integration.

F1-F5 select development stunts. In development mode, R restarts and 1-4 choose
difficulty. For high-score entry, Left/Right selects characters and A/B confirms;
choose the original backspace/end symbols to delete/finish.
On a stationary title page, Up, Down, Left, Right opens the password screen.
Original passwords and the music test use locally extracted data.

## Requirements and support

Windows x64 with GDI/Win32 and optional Windows audio output. XInput 1.4 or
9.1.0 is loaded from Windows if available; absence does not prevent keyboard
play. Python 3.10+ is required only to prepare assets. Building additionally
requires Zig 0.16.0. See [build and test instructions](docs/BUILDING.md).

This alpha has automated coverage on the development Windows installation;
it is not qualified on a second installation or physical controllers/audio
device removal. See [release notes](docs/RELEASE_NOTES.md) for validation and
[final acceptance](docs/ACCEPTANCE.md) for remaining work.

Use the issue template with version, Windows version, stunt/difficulty, input
device and reproduction steps. Do not attach ROMs, generated data, original
recordings or memory dumps containing them. For startup problems, check that
all seven prepared files are beside the EXE.

## Development, provenance and roadmap

- [Changelog](CHANGELOG.md) and [release notes](docs/RELEASE_NOTES.md)
- [Reconstruction status](docs/STATUS.md) and [reverse engineering](docs/REVERSE_ENGINEERING.md)
- [Code/data provenance and licensing status](docs/PROVENANCE.md)
- [Separate original-reference tools](docs/REFERENCE_BACKENDS.md)

Next fidelity work: high-score/name entry and player/title return after game over,
remaining interrupted
work, other stunt/player/reset paths and production scheduler integration; expand matched
original image/audio comparisons and human/independent Windows tests.
The [latest timing comparison](docs/AIR_FINAL_RESULT.md) qualifies
both existing Air histories through final-life consumption, the game-over
result and its fixed hold. Subsequent high-score/player/title flow remains unqualified.
Diagnostic timing is not yet integrated
into the production Windows scheduler.
Potential later conveniences include remapping, saved settings/high scores and
campaign resume; these are not promised features of this alpha.

ROMs, extracted assets, recordings and reference-emulator binaries remain local.

See the [publication audit](docs/PUBLICATION_AUDIT.md) for the checked repository
and release scope. This is a technical inspection, not a legal approval.

## License

Project contributions are provided under the [MIT License](LICENSE), to the
extent the contributors hold the rights to license them. The license does not
grant rights to the original ROM, graphics, music, game data or trademarks.
Reconstructed game code may involve third-party rights; MIT does not resolve
that provenance question. See [provenance](docs/PROVENANCE.md).
A ROM-free release is not a legal clearance.
