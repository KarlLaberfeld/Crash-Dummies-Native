# Pending instruction services and first background clear

October 20, 2026. Continues the accepted [campaign restart](AIR_TITLE_CAMPAIGN.md)
from 02bc before EI through current-player life selection, the full LCD-on
background clear and result reset to 02ce, before the instruction header.

The following player/lives/day/difficulty header and its first wait are now
qualified separately in [post-title header](AIR_TITLE_HEADER.md).

Both retained single-player Air/easy histories match seven boundaries, four
display services, eight vectors, 3,567 readiness reads, 1,034 stores and all
2,048 final map bytes each. Combined: 14 boundaries / eight displays / 16
vectors / 7,134 reads / 2,068 stores / 4,096 map bytes, zero differences.
All 395 / 399 preceding complete native CSVs remain byte-identical. The
comparison requalifies the entire attached original and native control chain.

## Pending services and first-frame accesses

EI takes effect after the complete CALL follower. The native owner explicitly
accepts the retained VBlank request before STAT, with their source-defined
acceptance/body/return boundaries. The original return address for both is the
player-selection routine. This is semantic native work; no Game Boy opcodes,
register file or CPU state are executed by the Windows program.

Instruction display callback 5 clears vertical scroll and retains countdown.
Its identified body is 144 cycles; the stopped audio paths take 64 effect and
60 music cycles. STAT callback 5 copies the retained zero center into vertical
scroll, with a 288-cycle body. Every scroll store and all periodic interrupt
acceptance boundaries agree with the originals. Four actual displays advance
tick and sample input; they do not decrement countdown or consume fresh lives.
The native current player and five lives come from the preceding campaign,
and the old native result remains 33 until the final result-clear store.

Every background cell retains its own busy/ready polling and safe store,
including padding and offscreen cells. All 1,024 background stores and both
final maps agree; the already-empty window and full object storage stay intact.
The independent source evidence analyzer also audits each polling loop and
its elapsed mainline work after excluding complete observed services. These
observations are comparison targets only and never drive native execution.

The previous empty-result first-frame readiness owner deliberately excluded
line 143 and VBlank. A separate instruction-restart scope now admits these
later lines for empty, unscrolled, object/window-disabled geometry. The first
LCD-on line remains rejected; object/window-enabled or scrolled first-frame
geometry is not generalized. The full original poll trace matches the native
geometry model, including the first frame's newly admitted region. This does
not certify hardware behavior, first-frame pixels or raster glitches.

The original extended Start controls already contain this endpoint. No events
or extension frames changed. Each capture retains its existing full-control
hash. The input-only native file preserves the entire accepted Start prefix
and appends exactly four newly observed display input samples. Source choices,
snapshots, measured clocks, interrupt schedules and poll counts do not
initialize the native owner. The separate pinned comparison emulator, ROM,
extracted assets, original recordings and binaries remain local.

## Reproduction and validation

Capture with `tools/air_title_resume_reference.py capture ROM --capture
EXTENDED_START_CONTROL --parent-out CAMPAIGN_REFERENCE --buttons-from
START_REFERENCE --out RESUME_REFERENCE`. Rebuild the optimized native probe
with `tools/build_air_clock_probe.py`. Replay the same accepted full attempt
extents and input files with `--title-resume` and the newly extended button
file. Explicit fifth entry and every preceding owner are required.

Compare with `tools/air_title_resume_reference.py compare NATIVE_BASE`, all
arguments from the campaign comparator, plus `--resume-out RESUME_REFERENCE`
and `--campaign-base ACCEPTED_CAMPAIGN_NATIVE_BASE`. Outputs use
`.fifth.title-resume*`; reports use `.title-resume.comparison.json`. Local
evidence uses `air-title-resume[-pause]-reference` and matching services CSVs.

Validation: optimized native Windows diagnostic, both full attached original
comparisons, 22,549 native resume assertions, 29,724 rebuilt final-result
regression assertions, CLI guard and 1,082 Python tests (33 new synthetic
evidence guards). The new native target joins the regular test build. Tests
cover pending priority/follower completion, tick rollover, input edge clearing,
retained countdown/lives, every cell/read/store, preserved unrelated storage,
future deadlines and rejection of unowned first-line/geometry/player states.
Synthetic evidence contains no ROM or original recordings and rejects altered
ancestry, vectors, service work, inputs, maps, polling and access boundaries.

Regular Windows EXE rebuilt from committed source; timing remains diagnostic,
outside the production scheduler. No release or automation change. Next is the
instruction header/content with callback 5 and retained countdown; the existing
post-result header owner cannot be reused unchanged. Other menu/player/stunt/
campaign paths, qualifying name entry, vacant flags, full pixels/PCM, production
timing and human/device/independent-Windows/distribution gates remain open.
[Final acceptance](ACCEPTANCE.md) is incomplete.
