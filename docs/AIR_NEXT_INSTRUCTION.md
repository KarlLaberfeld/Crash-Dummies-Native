# Post-retry result handoff and complete next instruction

October 19, 2026: both existing easy Air retry histories match from the result
return at 0514 through the following instruction's completed text at 032b.
The original controls retain held A/Left; they do not press Start again. This
is diagnostic timing/bounded publication acceptance, not a production scheduler
or complete campaign qualification.

## Native continuation

The continuation uses the native result transition and campaign. It preserves
the three remaining lives, skips the eliminated second player, clears all 1,024
background cells through the LCD-safe glyph writer and clears the result only
at its identified store. The following header prints the selected player, three
lives, same Air stunt and same difficulty. Instruction music/picture work,
callback/compare-line changes, all 64 map selections, typing and scrolling then
use the existing semantic source owners and locally decoded assets.

The previous instruction's software scroll byte survives gameplay and the
result screen. These histories retain 64. It must remain visible at next-map
entry, the line wait and object-disable completion, then clear at 269e. The map
owner now receives this value from the preceding native instruction state.
Default zero remains valid for the already qualified initial result controls;
invalid byte values reject. Retaining software scroll does not change source
work or the continuing LCD deadlines. This does not claim that hardware SCY
always follows that software byte during the intervening screens.

The native result LCD epoch, tick, countdown, raw/fresh input history and service
counts remain continuous across all five components. The map transition alone
changes the compare line and generates its already identified STAT-write
request. Changing players, an unsupported stunt, active music at handoff or an
inconsistent life count cannot borrow this diagnostic continuation.

`tools/air_next_instruction_probe.h` contains output/orchestration only. Native
algorithms execute in the existing handoff/header/picture/map/text owners. It
loads no original snapshots, measured delays, life counts, polls or writes.
There is no Game Boy CPU execution in the port or native diagnostic.

## Original observations

Each previous 2,900-frame held-input tail was extended to 4,200 frames, allowing
the full next instruction text to complete. Earlier events/setup snapshots are
unchanged; no RAM, seed, life or outcome is injected. Two uninstrumented replays
agree per extended control. Startup, gameplay/outgoing, result setup/incoming/
hold and all five new component captures match the corresponding full control
memory hash on the separately authorized pinned SameBoy backend.

Following capture scope excludes the initial result and instruction. It requires
the instruction preceding the first Air retry and that retry's actual gameplay
entry. All preceding raw display inputs are retained. The new result's 0462
entry establishes the local service-number origin; only comparison numbering
is rebased, never the original clock, tick or button history.

| Per-history component | Boundaries | Displays | Vectors | Polls | Stores |
|---|---:|---:|---:|---:|---:|
| Result/player/background handoff | 11 | 3 | 6 | 3,556 | 1,024 |
| Player/lives/stunt/difficulty header | 12 | 1 | 2 | 278 | 39 |
| Instruction music and picture | 9 | 4 | 8 | 5,276 | 1,114 |
| Callback/map transition | 267 | 66 | 133 | 3,509 | 64 map selections, separate |
| Complete instruction text | 1,308 | 555 | 1,110 | 237 | 109 |
| Total per history | 1,607 | 629 | 1,259 | 12,856 | 2,286 + 64 selections |
| Both histories | 3,214 | 1,258 | 2,518 | 25,712 | 4,572 + 128 selections |

Both histories have zero differences. Adjacent component endpoints overlap;
these counts extend the same ordinary and entry-pause easy Air histories,
rather than new independent games. Previously accepted gameplay/outgoing/result
coverage is rechecked under the new full-control hashes and still matches.

Every declared source boundary, display component/audio cost, input edge,
complete vector, readiness/line poll and destination/value store is compared.
The chain additionally requires exact adjacent endpoint attachment, stable
campaign selection/lives, retained scroll, restarted-result service numbering,
absolute LCD deadlines, final counters and summaries. The header's life value
and actual printed glyph stores both agree. The extra vector is the known
map-transition STAT-write request, not an omitted/guessed periodic service.

The stores include 1,024 cleared cells, 39 header glyphs, 1,024 picture tile
bytes / 90 picture-map glyphs and 109 text glyphs per history. Map register
selection is compared at all 64 transitions. This does not certify complete
rendered frames, all intermediate VRAM contents, palette bus microtiming, PCM,
hardware or arbitrary interrupted work. Other players, stunts, difficulties,
final-life/reset and the next gameplay entry are not certified here.

## Validation and reproduction

The O2 diagnostic passes both complete controls. Native suites pass 52,878
result-clock assertions, 863 handoff/pause/exit assertions and 4,200 source-work
assertions. All 620 Python tests pass, including 36 new capture-scope,
attachment and inherited-scroll cases. Both preceding 1,000-update resource
controls, all four startup/exit comparisons and the prior successful Air
gameplay/IRQ/result control remain exact. Core gameplay rules are unchanged;
their earlier 819,624 assertions remain applicable and were not rerun.

Capture the same control's startup, gameplay/outgoing and complete restarted
result as described in AIR_FOLLOWING_RESULT.md. Then run `capture --following`
with each of:

- `tools/air_handoff_reference.py`
- `tools/air_instruction_header_reference.py`
- `tools/air_instruction_picture_reference.py`
- `tools/air_instruction_map_reference.py`
- `tools/air_instruction_text_reference.py`

Supply the same ROM/control/output folders. Capture text last: its `buttons.txt`
contains the entire required preceding display-input history. Build using
`tools/build_air_clock_probe.py`. Replay with `--following-gameplay
--following-updates N --next-instruction 5`, adding `--following-entry-pause`
for the paused variant. `N` remains 1,788 ordinary / 1,767 paused. This enables
the terminal wait, outgoing fade and full result hold before the new chain.
Diagnostic extents 1..4 stop after handoff/header/picture/map; each needs a
matching input extent, since spare or missing samples reject.

Run the gameplay-resource, outgoing and restarted-result comparators first.
Then run `tools/air_next_instruction_reference.py` on the native base output
path with matching `--capture`, `--out` and `--startup`. It requires all sibling
`.next-handoff*`, `.next-header*`, `.next-picture*`, `.next-map*`, `.next-text*`,
the preceding `.following-incoming.summary.csv` and native first instruction
exit file. It invokes every component comparator and checks chain attachment.
The output is `.next-instruction.comparison.json`. Mixed hashes/backends,
initial-result captures, wrong service origins and incomplete coverage reject.

Local controls are `local/sameboy-air-next-control/` and its pause variant.
Observations use `local/air-following-next-reference/` and
`local/air-following-next-pause-reference/`; startup folders use the corresponding
`-startup` suffix. Native outputs use `local/air-next-services.csv*` and
`local/air-next-pause-services.csv*`. Logs/test binaries use `local/air-next-*`.
All original snapshots, controls, recordings and extracted data remain ignored/
local. The earlier shorter text capture was incomplete and is not acceptance
evidence; the longer complete captures supersede it.

## Remaining work

The prompt/exit and third Air entry/first update are now qualified in the
[second-retry continuation](AIR_NEXT_RETRY.md). The remaining-work paragraph
below describes this checkpoint's original boundary.

Continue 032b's Start prompt/exit, then the next Air setup/entry. Preserve the
completed text/cursor/scroll, three-life campaign and animation blocks from the
immediately preceding native Air game. The current controls never press Start
again, so fresh-input measurement is required for that next entry. Following
Ski, changed-player/shared-animation, final-life/reset, earlier UI/LCD and other
unobserved work remain open. Production scheduling, full images/PCM, human/
device/independent-Windows and final distribution gates still apply. The
production EXE/versioned alpha are unchanged; point 1/final acceptance are not
complete. See ACCEPTANCE.md.
