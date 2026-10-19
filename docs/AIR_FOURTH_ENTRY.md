# Two-life fresh Start and fourth Air entry

October 19, 2026. Native diagnostic continuation from the accepted
[two-life instruction](AIR_TWO_LIFE_INSTRUCTION.md). Both existing easy Air
histories now match the fresh-Start prompt/exit, LCD-off prefix/stage setup,
LCD restart and fourth-attempt first update through the next input gate.
This does not qualify later gameplay or integrate the Windows scheduler.

| New comparison scope | Ordinary | Earlier second-entry pause | Combined |
|---|---:|---:|---:|
| Boundaries | 267 | 619 | 886 |
| Display services | 105 | 281 | 386 |
| Complete vectors | 210 | 562 | 772 |
| Readiness/line polls | 1,847 | 1,847 | 3,694 |
| Prompt/clear stores | 532 | 532 | 1,064 |
| First-update actor slots | 160 | 160 | 320 |

All compared fields have zero differences. The histories overlap all earlier
accepted gameplay/result/UI work; they are not new independent input patterns.
Two lives remain throughout setup. Partial-second phases 14 / 48 come from
the just completed third game, rather than the second game's 54 / 33. Current
instruction timing/input, native map storage, fresh stage seed, HUD/fade and
the explicit 0387 sprite-direction reset retain their existing owners.

The diagnostic retains the actual completed instruction state and calls the
same exit/setup/entry/first-update adapter with the immediately preceding third
`AirGame`. Its bounded child stops after one update and cannot continue into
another result. No source semantic owner or production scheduler was modified.
Source observations remain comparison targets only, never native timing/state
inputs. All sixteen native delay/period blocks at entry match, including vacant
slots; occupied actors are compared across all ten first-update boundaries.

## Control integrity and evidence limits

Each child preserves the complete third-result/text parent events, setup state
and initial input file. It appends only Start press, one frame, Start release
and 300 frames; A/Left otherwise stay unchanged. There is no RAM, seed or life
injection. Two independent uninstrumented replays match both the parent's full
32,768-byte RAM digest at the attachment and the child's new final digest.
Each instrumented capture matches that child digest and the pinned SameBoy
backend. Separate parent/child records retain their own hashes and provenance.

All 188 ordinary and 192 paused earlier native CSVs are byte-identical to the
accepted two-life parent replay. The verifier also reruns the complete parent
instruction comparison against its own original result/startup records, then
checks child exit/prefix/stage/entry/gameplay work independently. Original
endpoints, life count, input edges, service origins, source animation continuity
and current partial-second inheritance must attach; a different generation
cannot silently select an older three-life retry.

An additional check found a pre-existing storage mismatch: never-allocated
vacant animation slots have native `done=true`, original `done=false` (ordinary
slots 14/15, paused slot 15). The existing actor comparator excludes vacant
payloads. This checkpoint keeps that flag limitation explicit, checks all
sixteen delay/period blocks and all occupied flags, and does not claim complete
raw animation-storage parity. The initial unused flags need separate source
initialization evidence/correction. Allocation explicitly replaces done/wait
flags; no gameplay timing difference from these unused bits is established here.

Full map/sprite bytes, images, PCM, subsequent fourth-attempt gameplay, arbitrary
interruptions, other players/stunts and production Windows scheduling are not
accepted by this comparison. Earlier row-publication evidence retains its own
scope; the new diagnostic map CSV alone is not new byte-level original proof.

## Reproduction

Prepare new input-only child controls from the accepted third-result controls
with the exact extension above and repeated unhooked parent/final checks. Keep
all control files local. Capture initial startup into a fresh startup folder,
then the following into a fresh reference folder using the child control:

- `air_instruction_exit_reference.py capture --following --after-retry 2`
- `air_following_setup_reference.py capture --next-retry --after-retry 2`
- `air_following_stage_reference.py capture --next-retry --after-retry 2`
- `air_following_entry_reference.py capture --next-retry --after-retry 2`
- `air_following_gameplay_reference.py capture --next-retry --after-retry 2` last.

Tools are under `tools/`; capture commands additionally take the usual ROM,
`--capture` and `--out` paths. Default selection remains unchanged. The later
generation requires explicit `--following` or `--next-retry` ownership; repeated
game updates do not count as new entries. Raw input samples retain the entire
preceding history; each current result retains its own service origin.

Build with `tools/build_air_clock_probe.py`. Use the complete-third-result replay
arguments from AIR_THIRD_RESULT.md, supply the child gameplay `buttons.txt`, and
append `--fourth-entry` alongside `--next-retry`. Earlier update counts stay
1,788 / 1,767 for the second game and 1,789 / 1,604 for the third game. The
earlier paused case still requires `--following-entry-pause`. The new flag owns
complete third-result and instruction continuation. Child outputs use
`.fourth.next-exit*`, `.next-prefix*`, `.next-stage*`, `.next-entry*` and
`.next-gameplay*` appended to the native base; earlier output scopes stay intact.

Run `tools/air_fourth_entry_reference.py NATIVE_BASE` with child `--capture`,
`--out`, `--startup`; parent `--parent-capture`, `--parent-out` (two-life text),
`--parent-startup`, `--parent-result-out` (third-result/gameplay); and
`--accepted-base` (accepted two-life native CSV base). It validates separate
control provenance, the exact input extension, all native parent CSVs, current
animation/timer inheritance, parent instruction and the five child comparisons.
The report is `.fourth.comparison.json`.

Local controls: `local/sameboy-air-fourth-entry-control/` and
`local/sameboy-air-fourth-pause-entry-control/`. Source recordings/startups and
native outputs use corresponding `air-fourth-entry` / `air-fourth-pause-entry`
names. ROM, decoded assets, original recordings, reference binaries and native
diagnostic executables remain ignored/local.

Validation: optimized native Windows diagnostic, both attached source comparisons,
919 synthetic native handoff assertions (including both new timer phases and
all sixteen current animation blocks), 733 Python tests, CLI generation guards
and all five unchanged default retry capture JSONs. Unchanged result/work/core
assertions retain their earlier scope and were not repeated. Production EXE
and `0.1.0-alpha.1` remain unchanged; continuation automation remains ACTIVE.

Next concrete work: fourth-attempt gameplay continuation, plus separate unused
animation-flag initialization qualification. Remaining stunt/player/final-life/
reset/UI paths, unobserved work, production scheduling, complete image/audio
comparison, human/controller/independent-Windows tests and distribution gates
remain open. Timing point 1 and [final acceptance](ACCEPTANCE.md) are incomplete.
