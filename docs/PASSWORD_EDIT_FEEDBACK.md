# Password editing, validation and feedback comparisons

October 20, 2026. Continues the [first password presentation](AIR_TITLE_PASSWORD.md)
through 2ba7..2bcf editing/submission and 2bcf..2bdc validation/feedback. The
music-test password ends at its action entry 2d65, before test presentation.

Seventeen cases run in both retained single-player Air/easy histories: separate
Start/A/B submission, cursor bounds, digit wrapping, combined directions, long
holds and all ten valid passwords. Valid digit inputs are decoded locally from
the identified original data table and supplied through ordinary key events.
Each append-only control preserves its accepted setup/prefix and has two
unobserved prefix/full hash repetitions plus matching observed replay. No RAM
edits establish any outcome.

| Compared extent, 34 cases combined | Editing | Validation/feedback |
|---|---:|---:|
| Semantic boundaries | 62,722 | 13,268 |
| Display/music services | 7,836 | 4,828 |
| Interrupt vectors | 23,508 | 17,136 |
| Raster boundaries | 31,344 | 24,616 |
| Access polls | 1,466 | 69,666 |
| Stores | 103,854 | 81,958 |
| Direct map bytes | 69,632 | 69,632 |
| Shadow object bytes | 8,704 | 8,704 |
| Voice projection rows | 47,016 | 28,968 |
| Differences | 0 | 0 |

Every editing case preserves 383 / 387 preceding complete native CSVs; every
feedback case preserves 393 / 397. Shared parent chains are qualified once
per batch. Every child still proves its *entire* native prefix byte-identical
to its qualified parent and independently checks its original controls and
new observations. Batches reject mixed ancestry. This avoids repeatedly
parsing unchanged ancestors without removing child qualification.

The native cursor is published before that iteration's Left/Right/Up/Down
decisions. Exact fresh masks, held inputs, combined-direction order, cursor
bounds, zero-to-ten decrement, ten-to-one increment, intermediate wrapped RAM
stores, safe glyph access and Start/A/B submit masks agree. The native object
buffer is populated by its own cursor stores and copied by actual display
services. Direct final background/window and full shadow-object storage match.
This does not claim rendered-object or complete frame parity.

Validation searches all ten native decoded rows in order, retaining individual
byte-comparison work. Accepted/rejected text, two clears, all 40 closing and
opening waits, the full 60-update hold and five stunt/four difficulty handlers
agree. The tenth action selects music-test entry. The comparison stops before
the subsequent title/password return or test screen.

The original raster interrupts the audio stop. The native owner reconstructs
the fixed reset operations and exposes their individual completions to its
raster service. The source reset work is 12,384 cycles; the observed interrupted
extent includes a 496-cycle raster interruption. That extra time is produced
by the independently scheduled raster callback, never a fitted allowance.
A display cannot observe partially reset native music.

After stopping, the original driver retains four parked raw active flags.
Recordings preserve those raw values. Only the comparison projection treats
voices as logically inactive when the recorded driver is explicitly disabled
and its music work is 60 cycles. Enabled voices cannot be masked this way.
Native audio clears its logical voices. Reset payload equality is explicitly
excluded; pre-stop active voice fields retain the
[instruction-music exclusions](AIR_TITLE_PICTURE.md). Rendered frames, PCM,
audio-register and hardware parity are not implied. The feedback hold counter
is compared only during its owned lifetime, not as unrelated raw BC scratch
before it is initialized.

Use `tools/password_edit_reference.py prepare/capture/compare` and
`tools/password_feedback_reference.py prepare/capture/compare`. Prepare takes
`ROM --capture ACCEPTED_PARENT_CONTROL --out CHILD_CONTROLS`; capture also
takes `--control CASE_CONTROL --parent-out PARENT_REFERENCE`. Each compare
inherits the preceding comparator's arguments. Editing additionally requires
`--edit-out`, `--edit-control`, `--password-base`; feedback additionally requires
`--feedback-out`, `--feedback-control`, `--edit-base`. `compare-batch MANIFEST`
accepts a local JSON list of compare-argument path dictionaries sharing one
qualified ancestry. Replay with `--password-edit` / `--password-feedback` and
the full raw display-input stream. Reports use `.password-edit.comparison.json`
and `.password-feedback.comparison.json`; raw CSVs use the corresponding
`.fifth.password-edit*` / `.fifth.password-feedback*` suffixes.

Validation: optimized Windows diagnostic; all 68 attached comparisons;
1,944 native edit assertions, 16,572 native feedback assertions and 1,369
Python tests, including 84 new editing/control/batch/reset-projection integrity
cases. New native targets join the regular test build. Original material and
reference binaries remain local. No release or automation change.

Next: title/password return presentation and full music-test operations,
then the other [game/menu comparison families](ORIGINAL_COMPARISON_SCOPE.md).
Production scheduling and final acceptance remain incomplete. These results
do not establish the user's complete broader comparison request.
