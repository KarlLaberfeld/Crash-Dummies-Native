# One-life instruction and final Air entry

October 19, 2026. Continues both accepted
[fourth Air results](AIR_FOURTH_RESULT.md) through live-player selection,
one-life header, music/picture/map/text, fresh-Start exit, fifth-attempt setup
and first update/next input gate. This is the final available attempt in these
two fixed easy Air histories. Its later gameplay and final-life consumption
are not yet accepted. Production Windows scheduler/EXE and alpha are unchanged.

## New comparison scope

| Instruction scope | Ordinary | Earlier second-entry pause | Combined |
|---|---:|---:|---:|
| Boundaries | 1,607 | 1,607 | 3,214 |
| Display services | 629 | 629 | 1,258 |
| Complete vectors | 1,259 | 1,259 | 2,518 |
| Readiness/line polls | 12,856 | 12,856 | 25,712 |
| Stores | 2,286 | 2,286 | 4,572 |
| Map selections | 64 | 64 | 128 |

| Following exit/setup/entry scope | Ordinary | Earlier second-entry pause | Combined |
|---|---:|---:|---:|
| Boundaries | 269 | 319 | 588 |
| Display services | 106 | 131 | 237 |
| Complete vectors | 212 | 262 | 474 |
| Readiness/line polls | 1,847 | 1,847 | 3,694 |
| Prompt/clear stores | 532 | 532 | 1,064 |
| First-update actor slots | 160 | 160 | 320 |

All compared fields have zero differences. The one remaining life survives
header, prompt, stage setup and entry; it is not consumed at Start. Partial-
second phases 33 / 43 come from the just completed fourth game, rather than
earlier third-game phases 14 / 48. All sixteen delay/period blocks agree,
including vacant slots. Occupied actors retain the existing full first-update
field coverage. Separate side-push capture matches all twenty boundaries:
the fourth games' terminal scratch is zero and remains zero through entry/Intro.

The earlier never-allocated vacant done-flag mismatch remains explicit; no
complete raw animation-storage parity claim is added. Native fifth-entry row
storage comes from the current native instruction stores and stage preparation,
but the new map CSV is not independently compared byte-for-byte to original
fifth-game VRAM. Earlier complete fourth-game row proof retains its own scope.
Images, PCM, later fifth gameplay, final-life handling, other campaigns and
production scheduling remain unqualified.

## Native state ownership and controls

The retry adapter now returns an owning bundle containing its actual native
game, setup state and completed result transition. The outer continuation
retains that fourth game while passing its returned one-life result to the
existing instruction owners, then its game to the same bounded entry adapter.
No earlier native game, original snapshot, measured clock or per-update state
is loaded to restart this attempt. The existing diagnostic still uses its
initial phase/counter/seed header, decoded assets and raw button samples; this
continuation introduces no new original-state initialization or measured schedule.

The unchanged fourth-result controls already run long enough to complete the
one-life text. Those original UI recordings keep the same accepted full-control
hashes. Fresh entry controls preserve the complete parent events, setup state
and initial input file, appending only Start press, one frame, Start release
and 300 frames. Two uninstrumented repetitions per case match both the parent's
32,768-byte RAM digest at the attachment and the new child final digest. All
hooked captures match that child endpoint and the pinned backend. There is no
RAM, seed or life injection.

All 242 ordinary and 246 paused earlier native CSVs remain byte-identical to
their accepted complete fourth-result replay. Both complete fourth-result
comparison chains also pass again against the new native parent's output,
under their own original hashes. These regressions overlap earlier acceptance;
the tables above count only the newly qualified instruction/entry scopes.

## Reproduction

Under the unchanged fourth-result controls, capture the five instruction parts
into fresh one-life reference folders:

- `air_handoff_reference.py capture --following --after-retry 3`
- `air_instruction_header_reference.py capture --following --after-retry 3`
- `air_instruction_picture_reference.py capture --following --after-retry 3`
- `air_instruction_map_reference.py capture --following --after-retry 3`
- `air_instruction_text_reference.py capture --following --after-retry 3` last for raw input extent.

Tools are under `tools/`; capture commands take the usual ROM, `--capture` and
`--out` arguments. The generation guard requires the fourth result marker and
third instruction/entry pair. Repeated ordinary game updates cannot advance
selection. Earlier generation/default behavior remains unchanged.

Prepare the input-only child controls with the exact Start extension above and
repeated parent/final control checks. Capture initial startup into fresh child
startup folders, then exit/setup/entry into child reference folders:

- `air_instruction_exit_reference.py capture --following --after-retry 3`
- `air_following_setup_reference.py capture --next-retry --after-retry 3`
- `air_following_stage_reference.py capture --next-retry --after-retry 3`
- `air_following_entry_reference.py capture --next-retry --after-retry 3`
- `air_following_gameplay_reference.py capture --next-retry --after-retry 3` last.
- `air_side_push_reference.py capture` with the same child control/reference folder.

The supplemental side-push observer accepts the bounded final Intro only when
all ten named boundaries retain the preceding failed game's value. It makes
no claim about the later steering branch in this short extent. All source
measurements are comparison targets and never enter native replay inputs.

Build with `tools/build_air_clock_probe.py`. Use the complete fourth-result
replay's earlier-game extents/pause flag, the new child gameplay `buttons.txt`,
and `--fifth-entry`. Ordinary second/third/fourth extents remain
1,788 / 1,789 / 1,788; paused extents remain 1,767 / 1,604 / 1,764.
`--fifth-instruction N` (1..5) can stop at one-life handoff/header/picture/map/
text with a matching input extent. Final entry requires complete text and all
preceding result ownership. The default adds no fifth continuation.

Outputs use `.fifth.next-handoff*` through `.fifth.next-text*`, then
`.fifth.next-exit*`, `.next-prefix*`, `.next-stage*`, `.next-entry*` and
`.next-gameplay*` under the same `.fifth` base. Older third/fourth siblings stay
intact. Verify the original parent result chain with
`tools/air_fourth_result_reference.py` under the parent's source hashes.

Run `tools/air_fifth_entry_reference.py NATIVE_BASE` with child `--capture`,
`--out`, `--startup`; original parent `--parent-capture`, `--parent-out`
(one-life instruction), `--parent-startup`, `--parent-result-out` (fourth
result/gameplay); and `--accepted-base` (accepted complete fourth-result native
base). It requires explicit generation, one life, immediate fourth-game timer/
animation inheritance, native parent byte identity and the separate original
control attachment. It invokes all instruction, exit/setup/entry/first-update
and supplemental scratch comparisons. Reports are
`.fifth-instruction.comparison.json` and `.fifth.comparison.json`.

Local parent UI folders: `local/air-one-life-instruction-reference/` and pause
variant. Child controls: `local/sameboy-air-fifth-entry-control/` and pause
variant. Recordings/startups/native outputs use corresponding `air-fifth-entry`
and `air-fifth-pause-entry` names. ROM, decoded assets, original observations,
reference library and native binaries remain ignored/local.

Validation: O2 native Windows diagnostic, both complete new comparisons,
supplemental source scratch matches, both full parent result chains, 945 native
handoff assertions and 794 Python tests. CLI bounds/missing-parent/incomplete-
text guards pass. All five earlier two-life instruction capture JSONs reproduce
unchanged. Semantic core owners were not modified, so previous result/work/
pause assertion scopes remain applicable and were not repeated. Production
EXE/alpha are unchanged; automation remains ACTIVE.

Next: continue fifth-attempt gameplay, then reconstruct final-life consumption,
eliminated-player selection and game-over behavior. Initial vacant done flags,
other stunt/player/UI/reset paths, unobserved work, production integration,
complete image/audio parity and final human/controller/independent-Windows/
distribution tests remain open. Timing point 1 and [final acceptance](ACCEPTANCE.md)
remain incomplete.
