# Masked instruction LCD/register prefix

October 20, 2026. Continues both accepted [Start transitions](AIR_TITLE_START.md)
from 0272 through DI, LCD-off equality polling and instruction register setup
to 0292. Campaign configuration, player lives, map clearing, LCD restart and
instruction content are subsequent owners, not completed by this change.

Each history matches three boundaries, 1,641 independent LY polls and nine
operation-start stores, with no interrupt services. Combined: six boundaries /
3,282 polls / 18 stores / zero vectors, zero differences. All 382 / 386 previous
complete native CSVs remain byte-identical. The comparator requalifies the
complete attached original control/clock chain through Start/audio stop.

Native execution inherits the actual LCD epoch, pending-service deadlines,
stopped audio and title raster geometry. The masked equality loop stops at the
first read of line 145; no observed duration, poll count or timestamp enters
execution. LCDC initially retains the title's fb value, becomes 7b on LCD-off,
then becomes 51 in the instruction setup. Display/STAT callback selectors become
five, both scroll registers and center become zero, LYC becomes 95 and STAT
control becomes 44. Tick, countdown and input do not advance while masked.

Native pending-request bookkeeping derives from the accepted preceding
deadlines. These comparisons do not add an independent original IF-register
trace. Complete source map storage stays unchanged through the prefix; native
tests also preserve both maps and the empty object storage. No original map
snapshot initializes native execution, and instruction graphics/pixels are not
qualified by this register-only prefix.

The existing extended Start controls already cover this endpoint. No new input
event, extension or button sample is needed. Both observed replays retain the
accepted full-control hashes. ROM, controls and recordings remain local; the
separate pinned reference emulator remains absent from the Windows program.

Capture with `tools/air_title_instruction_reference.py capture ROM --capture
EXTENDED_START_CONTROL --parent-out TITLE_START_REFERENCE --out INSTRUCTION_REFERENCE`.
Build the diagnostic with `tools/build_air_clock_probe.py`; replay the accepted
Start inputs and complete attempt extents, replacing `--title-start` with
`--title-instruction`. New outputs use `.fifth.title-instruction*`.

Compare with `tools/air_title_instruction_reference.py compare NATIVE_BASE`,
the same arguments as `air_title_start_reference.py compare`, plus
`--instruction-out INSTRUCTION_REFERENCE` and
`--title-start-base ACCEPTED_TITLE_START_NATIVE_BASE`. Reports use
`.title-instruction.comparison.json`. Local evidence uses
`air-title-instruction[-pause]-reference` and matching services CSVs.

Validation: optimized Windows diagnostic, both complete attached comparisons,
5,983 native Start/setup assertions, CLI guard and 1,025 Python tests. The
existing regular Start test target includes the new masked-setup checks.
Tests retain every poll, correct selectors/deadlines and unchanged counters/
storage, and reject detached parents, masked services, missing polls/stores or
wrong registers. Unchanged campaign/shared-clock tests retain earlier scope.

Regular Windows EXE rebuilt from committed source; timing remains diagnostic,
outside its production scheduler. No release or automation change. Next:
campaign configuration/lives, window clearing and LCD restart, then instruction
content/presentation. Other paths, full graphics/pixels/PCM and final human/
device/independent-Windows/distribution gates remain open.
[Final acceptance](ACCEPTANCE.md) is incomplete.
