# Independent original-reference backends

The Windows port contains no Game Boy CPU emulator, interpreter or JIT. Its
build and portable package use none of the reference components described here.
They are optional tools for the user's explicitly authorized original-ROM
measurements. Engine source, DLLs, boot ROMs, states and recordings stay under
ignored `.tools/` and `local/`; only the measurement adapters are tracked.

## Why an independent reference was added

The locally installed PyBoy 2.7.0 source uses a fixed 170-dot pixel-transfer
interval. That is a limitation of this reference, not an original-hardware
timing rule. The hardware description gives a variable interval affected by
scroll, window and objects, with a baseline of 172 dots. This matters when the
original pause code polls STAT before graphics memory access.
[Pan Docs rendering description](https://gbdev.io/pandocs/Rendering.html)

Do not copy PyBoy's fixed interval into native pause scheduling or feed measured
failed-poll counts back into the native clock. Its earlier control-verified
source measurements remain valid evidence for that engine's executions, not
proof of hardware LCD behavior. Pending final acceptance remains explicit.

The independent reference is official SameBoy **1.0.3**, source revision
`208ba4afabffab9edde416f2dbb8ae459e34adb8`, model **DMG-B**. It provides its own
open-source boot ROM and a public C library interface.
[Official source](https://github.com/LIJI32/SameBoy/tree/v1.0.3),
[official release](https://github.com/LIJI32/SameBoy/releases/tag/v1.0.3).

## Local setup and isolation

Clone the official tag into `.tools/sameboy-reference`. Obtain the official
Windows release archive only for its open-source `dmg_boot.bin`, placing it in
`.tools/sameboy-windows-reference`. The archive SHA-256 published by GitHub is
`66fb05acc075abba860f2c5fa31af2198fef9767573d28834c78d0dfc15746b2`; its DMG boot
ROM SHA-256 is
`6f64da4cecd7e54e2f928eb3e3ba7810a7a567d0d247cc71737d1771e073a916`.
No Nintendo boot ROM is required or distributed.

```powershell
python tools/build_sameboy_reference.py
```

The builder requires the existing local Zig compiler and the exact, unmodified
official Core revision. It downloads nothing. It builds a separate adapter DLL
and records DLL/boot hashes in an ignored manifest. The adapter verifies DLL
identity, version and actual hardware model. Debugger, cheats, rewind and host
timekeeping are disabled for repeatable measurements; cartridge execution and
LCD timing remain in the external reference library.

The adapter supplies buttons, read-only observations and unmodified save/load
states. Instruction-boundary observations use the library's read callback and
return its original byte unchanged. SameBoy increments PC before that read;
the bridge accounts for this boundary without patching instructions. Exceptions
stop the measurement. The native game accepts none of this CPU/register state.

Captures explicitly select a backend; PyBoy remains the default for existing
recordings. Backend, version, model, source revision and applicable build hashes
are recorded. Mixing engines/revisions or missing independent provenance is
rejected before comparison. Legacy PyBoy captures are kept separately.

```powershell
python tools/air_reference.py capture 'path/to/original.gb' --reference-backend sameboy --out local/sameboy-air-coast --difficulty 1 --pattern coast
python tools/air_timing.py capture 'path/to/original.gb' --reference-backend sameboy --capture local/sameboy-air-coast --out local/sameboy-air-coast-timing
python tools/air_input_reference.py 'path/to/original.gb' --reference-backend sameboy --capture local/sameboy-air-coast --out local/sameboy-air-coast-input
python tools/air_sprite_reference.py 'path/to/original.gb' --reference-backend sameboy --capture local/sameboy-air-coast --out local/sameboy-air-coast-sprites
```

## Current independent evidence

The normal coast recording matches its uninstrumented 32,768-byte end-state
control. The native ordinary clock matches **3,989 updates, 3,990 complete
display services, 23,934 phase/entry-counter checks, 159,600 sprite slots and
3,990 independently measured held/fresh samples**. Counters/costs/outcomes are
comparison targets, not per-update native inputs. This repeats an existing
gameplay scenario on an independent engine; it is not another distinct pilot.

A separate normal-difficulty pause recording after update 300 (31-frame hold)
also preserves its control state. Four source copy bodies, 35 paused services/
waits and 34 frozen-world intervals agree with the reconstructed source work.
The measured LCD poll counts differ from the earlier PyBoy recording. They
remain observations, not native delays. Native pause-clock ownership is still
unaccepted.

Latest pure Python tests pass 98 checks, including engine/model/provenance
rejection. The Windows binary and full native/campaign/UI/preview validation
from the preceding checkpoint remain applicable: this work changes reference
tools, not the production game. SameBoy agreement is independent emulator
evidence, not original-device capture, pixel/PCM acceptance or a final release.
