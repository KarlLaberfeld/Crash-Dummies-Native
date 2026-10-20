# First instruction text, prompt and exit comparisons

October 20, 2026. Continues the [incoming fade](AIR_TITLE_ENTRANCE.md)
through 0a0a..032b timed text and 032b..0355 prompt/fade/audio stop. Both
retained single-player Air/easy histories have two new input-only controls:
complete text followed by fresh Start, and deliberately skipped text with
Start held across the exit decision. Other campaigns are not covered here.

| Compared extent, four cases combined | Text | Prompt/exit |
|---|---:|---:|
| Semantic boundaries | 2,716 | 2,994 |
| Display/music services | 1,144 | 1,456 |
| Interrupt vectors | 2,288 | 2,912 |
| Access polls | 436 | 200 |
| Glyph stores | 224 | 40 |
| Scroll/center stores or exit scroll/palette stores | 2,368 | 3,008 |
| Direct map bytes | 8,192 | 8,192 |
| Direct picture tile bytes | 4,096 | 4,096 |
| Active voice projection rows | 6,864 | 8,736 |
| Differences | 0 | 0 |

Each text case preserves 427 / 431 preceding complete native CSVs; each exit
case preserves 436 / 440. Full attached chains are requalified. Each control
replays its unchanged accepted prefix and appended tail twice without hooks;
both prefix and full memory hashes agree with observed replay. Setup state
and ROM remain unchanged. No RAM edits establish either branch.

The full case publishes 109 text glyphs, scrolls the instruction center to 64,
prints all 20 prompt glyphs and waits for a new Start edge. The skip case
publishes three name-substitution glyphs before the skip, retains center zero
and bypasses the prompt because Start remains held. Actual joypad sampling,
each counter wait, macro expansion, glyph-access polling, scroll-center commit,
STAT scroll selection and VBlank scroll reset are compared. The full prompt
wait has 695 display services; the held-Start exit has 33. No timeout or input
edge is replaced with a fitted display budget.

The native typed continuation inherits its own campaign, palettes, instruction
storage, LCD epoch, deadlines, input/tick and song 2 from the qualified entrance.
The shared text and exit owners optionally emit actual scroll/palette stores;
their existing default behavior remains unchanged. Every display advances the
native music driver independently. Countdown and lives stay fixed. All map and
tile bytes and preserved object storage are checked directly. Eight outgoing
palette groups retain four waits each, followed by the final wait and the
uninterrupted 12,384-cycle logical audio stop. Qualification stops at 0355,
before the next gameplay LCD setup.

The stopped original driver has **four parked raw active flags**: 369f resets
audio storage and reinstalls presets before 3710 disables the driver. Native
audio clears its logical voices. The comparison records those four flags but
compares the disabled driver and zero *logical playing voices*, not equality of
reset voice payloads or raw flags. A driver still enabled cannot pass. Active
voice fields before stopping retain the documented
[music/picture exclusions](AIR_TITLE_PICTURE.md). Unused inherited text
delay/cursor fields are excluded until overwritten, as in the existing shared
text comparison. These exclusions do not imply rendered-frame, PCM, hardware
or audio-register parity.

Prepare controls with `tools/air_title_text_controls.py ROM --capture
ACCEPTED_START_CONTROL --out CONTROLS`. Record text using
`tools/air_title_text_reference.py capture ROM --capture CASE_CONTROL
--accepted-control ACCEPTED_START_CONTROL --parent-out ENTRANCE_REFERENCE
--out TEXT_REFERENCE`; record exit using
`tools/air_title_instruction_exit_reference.py capture ROM --capture
CASE_CONTROL --parent-out TEXT_REFERENCE --out EXIT_REFERENCE`.

Build the native diagnostic using `tools/build_air_clock_probe.py`. Extend the
accepted native inputs with each measured button stream and replay with
`--title-text` or `--title-instruction-exit`. The text comparator inherits all
entrance comparator arguments plus `--title-text-out`, `--text-control` and
`--entrance-base`. Exit additionally requires `--title-instruction-exit-out`
and `--title-text-base`. Reports use `.title-text.comparison.json` and
`.title-instruction-exit.comparison.json`; raw CSVs use `.fifth.title-text*`
and `.fifth.title-instruction-exit*`.

Validation: optimized native diagnostic, all eight attached comparisons,
220 native text assertions, 582 native exit assertions, 52,920 shared result
clock assertions and 1,243 Python tests, including 51 new synthetic checks for
detached controls/storage, missing music/scroll/palette observations and the
explicit stopped-driver representation. New native targets join the regular
test build. The regular Windows EXE is rebuilt from committed source.
ROM/assets/original recordings/reference binaries remain local. No release
or automation change.

The user's broader [original-comparison request](ORIGINAL_COMPARISON_SCOPE.md)
remains **in progress**. Next: password presentation/validation/returns after
the qualified unlock entry, subsequent title/player/options/music-test paths,
other campaign/stunt/difficulty/player/outcome/reset paths and continuation
from this exit into gameplay. Production scheduling, full frames/PCM and final
human/device/independent-Windows/distribution gates remain open.
