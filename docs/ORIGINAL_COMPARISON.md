# Original-ROM comparison: Air Bumper, October 3, 2026

## Result

The original US/EU ROM reproduces the stopped-animation recovery failure in
PyBoy 2.7.0. A second run without hooks reproduces the same final memory state.
The native deferred-recovery safeguard is therefore an intentional fix for a
failure also observed in the emulated original, not evidence of an incorrectly
translated conditional animation starter. Physical Game Boy verification is
still outstanding.

The comparison also identifies a separate native timing gap: the original
global frame counter can advance during a gameplay update. The native standalone
stunt currently advances it exactly once per update. This changes input-driven
acceleration and eventually the route. Matching the recorded original counter
isolates the gameplay translation, but is not a runtime correction.

## Source and method

| Item | Recorded value |
|---|---|
| ROM | Local 128 KiB US/EU revision |
| SHA-256 | `ef563c4a4b063ea045d71b435dd078c19d0738f85079928803167cee8f34a4ec` |
| Reference | PyBoy 2.7.0, Python 3.13.5, Windows |
| Boot / audio | PyBoy bundled boot ROM; sound emulated, volume zero |
| Setup | Original UI passwords select Air Bumper and Normal; ordinary Start inputs enter gameplay |
| Gameplay input | Hold A and alternate left/right in 24-update bands; record actual sampled button bytes |
| Before-update sample | `00:03d8`, after the display wait and before player/entity work |
| After-update sample | `00:03fa`, after entity, sprite and map/placement work |
| Initial counter / timer remainder / random seed | 1721 / 0 / 46848 |
| Native source | Local checkpoint `03dd826`, private GitHub checkpoint `ea818a3c942d2fb666531c1316ae8b62096cfea4` |

The user explicitly authorized a separate emulator for comparison measurements.
It is not linked to the port, included in its build, or included in preview
packages. The capture tool reads the ROM and memory; it makes no gameplay RAM
writes. Password digits are read locally from the user's ROM rather than embedded
in the tool. Original trace data, images and states remain under ignored `local/`.

PyBoy implements instruction hooks with internal breakpoint instrumentation.
To check whether this affected the finding, the tool saves an uninstrumented
state before registering hooks and records the subsequent button/tick API calls.
A fresh instance loads that state and replays every call without registering any
hooks. Both runs end with all 32,768 compared bytes at `8000..ffff` identical:
SHA-256 `03783c97b547d3d3ee69b720ae5b78228e04ebc961f31eeffadf7ab9cd954eb8`.
This control checks instrumentation influence within this emulator; it is not
an independent emulator or hardware accuracy certification.

## Observations

Indices below are zero-based completed gameplay updates, not video timestamps.

1. At update 2457, global counter 4180, the crash deadline selects handler
   `3bb3`. The crash script is still active, with frame 5 and delay zero.
   Conditional start rejects recovery. The native fix records a pending request.
2. At update 2458, counter 4181, the original stops its crash script and remains
   in generic animation. The native version starts recovery instead.
3. The original remains stopped for all 600 further observed updates. Player
   position, camera position, seconds and timer remainder remain frozen. The
   uninstrumented control ends in the same state. No terminal result is reached.
4. With the recorded original counter supplied before each native step, all
   23 compared gameplay fields match for updates 0 through 2457. The first
   difference at 2458 is the intentional animation-completion difference above.
   Native control returns to Play at update 2596; the reference remains stopped.
5. With only the initial counter aligned and ordinary native clock progression,
   the first gameplay difference occurs at update 898: original speed/rate
   -17/-15, native -16/-14. This follows an extra original counter increment
   during update 895, from 2616 to 2617. Another occurs during update 1222,
   from 2944 to 2945. These are observed counter changes across one gameplay
   iteration, not an inferred animation-duration adjustment.

The 23 fields are handler, frame, flags, X/Y, camera X/Y, speed, rate, tilt,
crash counter/state, animation done/wait/delay/period, transfer state/remaining,
map-transfer flag, result flags, seconds, timer remainder and random seed.
Handler addresses and BCD seconds are normalized to their native representations.
Raw script pointers are not compared with native command indices. The global
counter is reported separately, and the native-only pending flag is recorded
separately. This is not a claim that every entity, pixel or audio sample matches.

The native probe copies only initial clock/timer/random context and button
inputs. In recorded-clock mode it additionally supplies each observed pre-update
counter. It never copies original player positions, collision outcomes, frames,
handlers or other world state. The aligned result is thus a useful rule-level
comparison while the unaligned result exposes the real timing difference.

## Reproduce locally

Keep all outputs local. The optional capture dependency is PyBoy 2.7.0; the
normal build and native executable do not require it. From the project root:

```powershell
python tools/air_reference.py capture 'path/to/original.gb' --reference-lib .tools/reference --out local/original-air-verified
$env:ZIG_GLOBAL_CACHE_DIR = Join-Path $PWD '.tools/zig-cache'
$env:ZIG_LOCAL_CACHE_DIR = Join-Path $PWD '.tools/zig-local-cache'
& .tools/zig-x86_64-windows-0.16.0/zig.exe c++ -std=c++17 -O2 -Wall -Wextra -Wpedantic -Isrc tools/air_reference_probe.cpp src/air.cpp src/game.cpp -o local/air-reference-probe.exe
& ./local/air-reference-probe.exe local/original-air-verified/inputs.txt > local/original-air-verified/native-contiguous.csv
& ./local/air-reference-probe.exe local/original-air-verified/inputs.txt --recorded-clock > local/original-air-verified/native-aligned.csv
python tools/air_reference.py compare local/original-air-verified/native-contiguous.csv --out local/original-air-verified
python tools/air_reference.py compare local/original-air-verified/native-aligned.csv --out local/original-air-verified
```

The native probe loads the existing local `build/crash.dat` and `build/air.dat`.
Do not treat a run that fails the ROM hash, control-memory check or complete-row
check as accepted evidence. The capture summary records the actual environment
and outcome; the comparison reports differences rather than hiding them.

## Remaining work

- Investigate the original counter increments during long game updates and
  model the relevant scheduling behavior natively. Do not hardcode these two
  replay indices as a runtime fix, and do not embed a CPU emulator in the port.
- Compare additional inputs, difficulties, successful finishes and failures.
  This single Air trace does not validate every Air case or the other stunts.
- Perform matched image and audio comparisons. Saved reference images here
  establish provenance only; no pixel/audio equivalence result is claimed.
- Confirm critical behavior on physical hardware or another independent
  reference implementation before claiming hardware equivalence.
