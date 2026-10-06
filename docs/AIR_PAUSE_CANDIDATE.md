# Native Air pause graphics candidate

October 6 timing follow-up: 836 pause counter-wait interrupt vectors agree
on absolute time in the same three controls. Source-protected entry and restore
handoffs now include their enable followers; pending protected crossings still
reject until independently measured. Full coupled comparisons pass again after
reducing simultaneous recording loads. See [IRQ scope](AIR_IRQ_BOUNDARIES.md).
Latest checks pass 573 pause/session/pixel, 113 source assertions and 133 Python
tests with a serial O0 diagnostic build; the production EXE is unchanged.

October 6 image follow-up: 262 unique selected complete images now agree, including
the known final-row object cancellation and visible outgoing palette writes.
See [pixel ownership and limits](AIR_PIXELS.md). This extends the bounded probe;
production scheduler integration remains open. The shared optional renderer
API changes the rebuilt EXE's hash; the byte-identical claim below describes
the earlier pause-only checkpoint, not this image follow-up.

The independent pause candidate now derives its own polls, counter waits,
graphics accesses and return time in three control-verified original scenarios.
Its shared session is coupled to ongoing native gameplay and software audio;
the three replays match through the post-resume stunt end.
This is bounded development evidence. The production Windows loop still uses
its existing display/update cadence; this checkpoint is not a final release.

## Results

| Scenario | Native prefix updates | Paused services | Bus events | Pause intervals | Storage bytes |
|---|---:|---:|---:|---:|---:|
| Normal coast, pause after 300, hold 31 | 300 | 35 | 1,751 | 77 | 444 |
| Easy coast, pause after 500, hold 120 | 500 | 124 | 1,748 | 255 | 444 |
| Hardest boost, pause after 100, hold 255 | 100 | 259 | 1,753 | 525 | 444 |
| Total | 900 | 418 | 5,252 | 857 | 1,332 |

All compared world fields before pause, forty-slot active geometry/scroll,
bus order/address/data/relative time, paused held/fresh input/counter values,
source interval work and the final return agree. Bus events include 4,304
independently predicted STAT samples and 948 graphics bytes. The 1,332 storage
bytes are the twenty-column row and 128-byte font at entry, after pause text,
and after restoration. Read-only direct storage observation establishes these
accepted contents even when a CPU bus read at that boundary would be blocked.
This still does not compare full frames or PCM.

The original source/access audit separately verifies 9,571 individual work
intervals and sixty retained status bytes. Its observed branches select audit
targets; they never drive the native candidate. Earlier isolated music evidence
and ordinary-clock cases retain their separate counts.

### Coupled gameplay, input and audio

| Scenario | Completed updates | Display services | Sprite slots | Selected voice rows |
|---|---:|---:|---:|---:|
| Normal coast | 3,989 | 4,025 | 161,000 | 24,150 |
| Easy coast | 2,789 | 2,914 | 116,560 | 17,484 |
| Hardest boost | 728 | 988 | 39,520 | 5,928 |
| Total | 7,506 | 7,927 | 317,080 | 47,562 |

These extend the same three scenarios; the prefix updates and paused services
are included, not additional independent cases. All selected post-step worlds,
held/fresh buttons, forty-slot sprite geometry/flags, graphics events/storage,
pause intervals and software voice/work fields match. Effect requests come
from native gameplay and are compared with independent original observations;
the original requests never drive the native audio sequencer. Active wave-voice
envelope fields and full PCM remain outside the selected software comparison.

The pending startup service also matches nine original boundaries in each
case. The missing four-cycle LCD access tail and a duplicated first ready-store
prefix are corrected; see [startup evidence and limits](AIR_STARTUP.md).
The coupled replays additionally match 7,509 ordinary display services, all
45,036 semantic work phases and 120,096 pre-update entity slots. These include
post-resume ownership and do not rely on recorded per-update counters.

## Native owners and input boundary

`air_clock_probe --pause-entry` runs native ordinary gameplay until its own
display sampler sees a fresh Start request. It preserves the fresh-button read
across a later interrupt and charges the taken call. The output geometry,
current HUD row, tick and input history all come from native state. Only the
initial clock/timer/RNG seed and raw per-display held buttons come from the
input-only recording. Original per-update counters, worlds, fresh edges, LCD
states, work, poll counts and HALT idle are not scheduling inputs.

`air_pause_clock.h` owns the four identified copies, their separate STAT,
source and destination accesses, the saved read values and the fixed twenty-
column layout. A bus sample occurs within a bounded access; a pending service
runs after that access completes. The saved status row survives the entire
pause. Unknown readiness, non-completing polls and invalid work reject.

`air_pause_session.h` shares this identified session between the isolated
graphics probe and `air_clock_probe --pause-replay`. The latter retains the real
native world, sprite publication, input history, pending effects and six voice
states. Paused services publish the retained sprites and advance the shared
game/display counter while HUD, timer, entities and driver sequencing freeze.
Restoration resumes the pending update without another counter wait. No original
voice, effect, geometry or update state is injected.

`air_pause_lcd.h` is a bounded steady-frame readiness candidate. It selects
the first ten native OAM objects by row, orders their fetches horizontally,
and derives scrolling, window and object transfer penalties. It distinguishes
read and write accessibility and rejects the unowned LCD-on first frame,
special window edges, and line-135 object cancellation.

The source of the phase/edge conventions is explicit. The pinned independent
DMG reference asserts VBlank five dots into its blanking line; the remaining
aligned HALT half-step reaches counter-wait interrupt acceptance three dots
later. Graphics is therefore evaluated eight dots ahead of this candidate's
counter-wait clock. Its source coroutine retains the completed edge before
advancing state. These are reconstructed event-order rules, not per-recording
offsets or fitted poll allowances. They are reference-specific candidate
conventions and cannot certify arbitrary interrupted instructions or hardware.
See pinned [display events](https://github.com/LIJI32/SameBoy/blob/208ba4afabffab9edde416f2dbb8ae459e34adb8/Core/display.c),
[HALT/interrupt acceptance](https://github.com/LIJI32/SameBoy/blob/208ba4afabffab9edde416f2dbb8ae459e34adb8/Core/sm83_cpu.c)
and [coroutine edges](https://github.com/LIJI32/SameBoy/blob/208ba4afabffab9edde416f2dbb8ae459e34adb8/Core/timing.h).
Hardware duration/penalty context comes from [Pan Docs](https://gbdev.io/pandocs/Rendering.html);
[Mooneye LCD-on](https://github.com/Gekkio/mooneye-test-suite/blob/main/acceptance/ppu/lcdon_timing-GS.s)
and [object timing](https://github.com/Gekkio/mooneye-test-suite/blob/main/acceptance/ppu/intr_2_mode0_timing_sprites.s)
provide independent hardware-tested boundaries, not executed port dependencies.

An initial whole-phase comparison matched totals while disagreeing on individual
accesses. It was rejected. The final comparison requires every event and complete
storage coverage; it rejects shifted samples, altered modes/data, missing events,
incorrect geometry, mixed provenance and missing accepted-storage ownership.

## Local reproduction

Use the existing pinned independent reference setup in REFERENCE_BACKENDS.md.
All ROM/data/state/recording outputs remain ignored. `extract_ui.py` additionally
writes local `pause.dat`: the pause font, restored status font and twenty text
bytes. The established UI07 payload remains byte-for-byte unchanged.

Build the candidate tools with the existing local Zig compiler:

```powershell
zig c++ -std=c++17 -O2 -Isrc tools/air_clock_probe.cpp src/air.cpp src/game.cpp src/audio.cpp src/ui.cpp -o local/air-clock-probe.exe
zig c++ -std=c++17 -O2 -Isrc tools/air_pause_probe.cpp -o local/air-pause-probe.exe
zig c++ -std=c++17 -O2 -Isrc tests/air_pause_clock_tests.cpp -o local/air-pause-clock-tests.exe
```

Record controls with `air_input_reference.py --include-paused` and collect
`air_pause_lcd.py` observations using the existing matching pause controls.
Then run, for example:

```powershell
python tools/air_pause_compare.py run --capture local/sameboy-air-pause-coast --inputs local/pause-prefix-coast-input/inputs.json --lcd local/sameboy-air-pause-coast-lcd-data/lcd.json --timing local/sameboy-air-pause-coast-timing/pause.json --out local/pause-native-coast-data
```

The easy/hard controls use the analogous paths. `comparison.json` explicitly
retains `productionPauseAccepted: false`. `air_pause_access.py` separately
audits original bus/work recordings without importing an emulator.

For the coupled comparison, additionally collect matching original sprite
and music records with `air_sprite_reference.py --include-paused` and
`audio_timing.py capture --reference-backend sameboy`. Collect source work with
`air_timing.py capture --reference-backend sameboy` and the pending startup
boundaries with `air_startup_reference.py capture`. Use the existing control
directory as `--capture` for each recorder; all must preserve its end-state hash.
Their output paths are respectively `local/pause-coupled-{case}-sprites-reference`,
`-audio-reference`, `-work-reference`, and `-startup-reference`. Then run:

```powershell
python tools/air_pause_coupled.py run coast
python tools/air_pause_coupled.py run easy
python tools/air_pause_coupled.py run hard
```

Outputs remain in `local/pause-coupled-{case}/`. Comparison rejects incomplete
coverage or mixed backend/revision/ROM/control provenance before acceptance.
`productionSchedulerAccepted: false` remains explicit. Audio comparison is
coupled to native gameplay, unlike the earlier isolated request replays.

## Remaining work

Qualification still needs initial LCD-enable/normal UI entry, arbitrary IRQ
acceptance and pending interrupts across critical sections, special window
edges and interrupted line-135 readiness. The bounded image projection owns
selected cancellation edges separately; it does not remove the LCD readiness
guard. The candidate rejects unsupported cases.
Its paused callback is restricted to an enabled reset check, no pending effect
request and a disabled music driver. The standalone graphics callback accounts
only for audio work; the coupled probe now also compares selected retained and
resumed voice fields. This is not full output-state or PCM acceptance.

Next address the remaining first-frame/startup/result setup and interrupted
owners before production Windows scheduling. Other stunts, matched images/audio,
human play, physical device removal, an independent Windows host and final
distribution remain required under ACCEPTANCE.md.

Validation: 527 pause access/geometry/session assertions, 107 existing source assertions,
119 Python tests and an ordinary coast replay (3,989 updates, 3,990
services, 23,934 phases) pass. The rebuilt Windows EXE is byte-identical to the
already fully tested placement preview (SHA-256
`a6c4f2177d7f18246dd24f3c0c1d63847d9bbafb9caa806ad2aa43cd22c28b7a`).
Unchanged campaign/UI suites were not repeated. No reference library, ROM,
extracted pause data or original recording is uploaded or packaged.
