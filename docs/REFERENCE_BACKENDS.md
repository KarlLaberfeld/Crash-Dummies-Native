# Independent original-reference backends

Latest observer addition: `direct-vram-title-v1` copies the two fixed title
maps through the official read-only storage API. It performs no CPU bus access,
graphics synchronization, emulated-time advance or state modification. Its
export/build identity and DLL hash are verified; recordings require explicit
direct-read provenance. Entry storage can be CPU-read-blocked, so normal bus
reads cannot replace this observation. Both new title-page captures preserve
their existing full-control digests. See [scope](AIR_TITLE_PAGE.md).
The current local DLL SHA-256 is
`8cb11d32843e59f1cb6fb35ca5a2b43fbe5a362ea1bb48b76cc98cbb81632f48`.
Core/source/model/execution-observer identities and the existing pause API are
unchanged; the additive observer is a comparison-only adapter extension.

Earlier observer addition: `direct-vram-pause-v1` copies only the identified
twenty-byte status row and 128-byte font through the official read-only direct
storage API. It makes no CPU bus access, advances no cycles and writes nothing.
The actual export, build manifest and DLL hash are verified. This distinguishes
accepted storage from attempted write notifications, including boundaries where
CPU reads would be blocked. Three new captures retain their uninstrumented
controls and match native restoration/storage; see AIR_PAUSE_CANDIDATE.md.
That observer's earlier local DLL SHA-256 was
`d062221a134f9760811db593ebde0112088065f1937e4e53f30f6c14a397929b`.
Core/source/model/execution-observer identities remain unchanged. None of these
storage snapshots enters the native clock or graphics copy inputs.

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
states. Instruction boundaries use the official execution callback, which
excludes the dummy PC read during interrupt entry. The initial read-callback
implementation could count that discarded read as an executed stage. It has
been replaced; `execution-callback-v1` is now mandatory recording provenance
and is checked in both the build manifest and the loaded DLL. Graphics-bus
observations separately return original read bytes unchanged and permit every
attempted write. Exceptions stop the measurement. The native game accepts none
of this CPU/register state.

The reference models randomized power-on memory. A new boot can therefore have
a different starting state or full memory hash. Control equality means replay
of the **same saved state and button events**, not identical hashes across
different boots. Current comparisons use new control-verified execution-observer
recordings; earlier read-observer files cannot certify the current observer.

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

Latest coupled pause evidence extends the three existing controls through
post-resume stunt end: 7,506 updates, 7,927 display/input samples, 317,080 sprite
slots, 47,562 selected voice/work rows and native effect requests. All 7,509
ordinary display services, 45,036 phases and 120,096 pre-update entity slots
also agree. The bounded native graphics owner matches every pause event and
accepted storage byte. Nine pending-startup boundaries per case now agree.
See AIR_PAUSE_CANDIDATE.md and AIR_STARTUP.md. This is an experimental coupled
probe; the production scheduler, first LCD frame, arbitrary IRQs, full pixels/
PCM and original hardware remain unaccepted. Earlier audit-only statements
below describe their historical scope. Current checks: 527 native pause/session
assertions, 107 source assertions and 119 Python tests.

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

Three current timeout/steering-damage replays also validate the final wait and
outgoing fade. They match 7,655 native updates, 7,791 display/input samples,
45,930 source phases and 122,480 pre-update entity slots. All 222 exit intervals
and 96 outgoing services match separately. The previously intended winning
steering pattern actually ends in damage; it is not independent success evidence.
See [placement ownership](AIR_PLACEMENTS.md) for the shared-scratch correction.

Three pause bus recordings validate **4,304** actual STAT read/branch decisions,
including **3,356** failed polls. All 60 status-row reads are unblocked; 888
graphics writes are observed as attempts, not certified stores. Twelve copies,
418 paused services/waits and 415 frozen-world intervals pass the separate source
audit. Native polling still requires an independent LCD model and is unaccepted.
`tools/air_pause_lcd.py` records these targets; they never become native delays.

Latest pure Python tests pass 103 checks, including observer/provenance and
range-read rejection. Native source checks pass 107 assertions. The rebuilt
Windows EXE passes full native/campaign suites and both 13/14 automated UI
variants. SameBoy agreement is independent emulator evidence, not original-device
capture, pixel/PCM acceptance or a final release.
