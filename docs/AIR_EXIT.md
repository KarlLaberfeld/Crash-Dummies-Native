# Air final display, audio stop and outgoing fade

October 6 image follow-up: the existing three SameBoy controls now also match
171 selected complete images, including the outgoing palette stages. The
native projection retains separate palette owners and pixels drawn before
a visible write. The 222 exit phases and 96 display services still agree.
See [full-image scope and remaining limits](AIR_PIXELS.md). The historical
SameBoy `win` directory is a steering-damage recording, as described below;
it is not the separate earlier successful PyBoy control.

Independent follow-up: three current SameBoy execution-observer recordings
(one timeout, two steering-damage paths) also match final wait, audio stop and
all outgoing fade intervals/services. This adds 222 bounded exit intervals and
96 outgoing services checked on a second engine. All their gameplay phases,
inputs and pre-update frame/flags/positions are separately compared. One path
requires the [interrupted placement correction](AIR_PLACEMENTS.md). These are
not independent successful-finish or pixel/PCM/hardware acceptance claims.

This is bounded original-reference evidence for an experimental semantic clock.
The complete port and production Windows scheduler are still unfinished. The
reference emulator is a separate measurement tool; the native program executes
no Game Boy CPU instructions. All recordings, original state and palette data
remain ignored/local.

## Captures and comparisons

Three control-verified input-only recordings cover easy successful steering,
easy damage/explosion and normal timeout. Each extends the existing gameplay
inputs by 40 hardware frames after the result, without changing original RAM.
Separate measurements record the final wait, outgoing main phases, VBlank
components and held/fresh button samples. Every measurement preserves the
uninstrumented recording's final 32,768-byte memory digest.

The three final display waits match entry/exit counters, elapsed cycles and the
retained busy resource gate. The native durations are computed from independent
display deadlines and source work; the measured 31,940 / 47,740 / 58,636-cycle
spans are comparison targets, never scheduling delays.

The outgoing intervals match all **222 phases**: three audio-stop calls, three
fade entries, 24 palette writes, 96 waits and 96 continuation/return paths.
Each fade's 32 display services also matches native HUD cursor/bar, button
samples and display/effect/music costs. Independent input measurements match
all **8,572** held/fresh samples through gameplay, final wait and fade. The
8,417 gameplay updates are repeats of three of the ten existing cases, not new
independent gameplay coverage. No original counters, costs or world outcomes
drive the ordinary-clock probe.

## Source ownership

- 0400 calls the counter-change wait while FFAE remains zero. DMA publishes the
  sprite list prepared by the terminal update; resource uploads stay gated.
- 0403 calls 3707/369f. Register/state clears and the initial wave copy contribute
  **12,384 cycles**, including the caller. A VBlank inside the partially cleared
  audio state remains unsupported and stops the native probe.
- 0406 calls 20b4. Entry costs 44 cycles. Each of eight palette stages costs 76
  cycles and owns four counter-change waits. BG palette uses the identified
  table; object palettes apply masks 0xcf and 0xf3. Native palette data comes
  from the local extracted UI assets, never the measurement file.
- Wait active work is 120 cycles plus 36 for each unsuccessful STAT wake.
  HALT idle follows clock deadlines. Ordinary continuations cost 16 cycles,
  segment continuations 28 and the final caller return 40.
- VBlank still cycles HUD columns and publishes sprites with the resource gate
  closed. No new entity/game timer update occurs. Music driver work is 60 and
  effect setup is 64 when no request is pending. The source component audit
  checks these separately so HALT idle cannot hide a wrong service cost.

The native Windows outro had retained the preceding visible sprite list. Its
display refresh now publishes the terminal prepared list before rendering the
HUD/outgoing scene. A marker regression covers all five stunts while checking
that entities, gameplay timer and pending resource work remain unchanged. This
presentation correction does not integrate the experimental scheduler.

## Reproduce locally

```powershell
python tools/air_reference.py capture 'path/to/original.gb' --reference-lib .tools/reference --out local/air-outro-win-original --difficulty 0 --pattern alternating --steer-period 44 --steer-offset 12 --after-result-frames 40
python tools/air_exit_timing.py capture 'path/to/original.gb' --reference-lib .tools/reference --capture local/air-outro-win-original --out local/air-outro-win-exit
python tools/air_input_reference.py 'path/to/original.gb' --reference-lib .tools/reference --capture local/air-outro-win-original --out local/air-outro-win-input
```

Export only each input sample's `held` value to a local button file, one integer
per service. Fresh edges remain comparison targets. Compile the diagnostic from
`tools/air_clock_probe.cpp`, `src/air.cpp`, `src/game.cpp`, `src/audio.cpp` and
`src/ui.cpp`, with C++17 and the `src` include directory. Extracted assets are
loaded from `build/`; the UI source is needed for the palette asset loader.

```powershell
./local/air-clock-probe.exe local/air-outro-win-original/inputs.txt local/air-outro-win-services.csv 0 --display-inputs local/air-outro-win-buttons.txt --outro-fade > local/air-outro-win-native.csv
python tools/air_exit_timing.py compare local/air-outro-win-services.csv.outro.csv --out local/air-outro-win-exit --services-csv local/air-outro-win-services.csv
```

The probe stops at 0409, before disabling interrupts and constructing the result
screen. Palette-register agreement is not pixel equivalence. Audio reset work
is not acceptance of the original reset voice fields or PCM. Native pause LCD
polling, interrupted entity/resource/row work, normal UI startup, result setup,
other stunts, physical input/audio behavior and independent Windows testing
remain open under [ACCEPTANCE.md](ACCEPTANCE.md).

## Validation checkpoint

The production publication correction passes full native suites, all 64 Air
recovery phases, four difficulty successes and three complete campaigns.
Latest independent checks pass 94 Python tests and 102 synthetic source-work
assertions. Windows UI checks pass 13 with normal audio and 14 with an actual
invalid-device open failure. A ROM-free preview passes manifest/hash checks,
bundled extraction and both UI variants from a folder with spaces and a different
working directory. These are one-host automated development checks. Human,
physical-device-removal and independent-host acceptance remain open.
