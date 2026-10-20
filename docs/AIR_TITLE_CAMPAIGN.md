# Retained campaign choices and instruction LCD restart

October 20, 2026. Continues the accepted [masked register prefix](AIR_TITLE_INSTRUCTION.md)
from 0292 through retained campaign settings, fresh lives, the complete window
clear and LCD restart to 02bc, before EI. Pending service acceptance and the
actual instruction presentation remain separate owners.

The subsequent pending services and first background clear are now qualified
separately in [instruction resume](AIR_TITLE_RESUME.md).

Both ordinary / earlier-paused single-player Air/easy histories match nine
boundaries, 1,024 readiness reads, 1,032 stores and all 2,048 final map bytes
each, with no vectors. Combined: 18 boundaries / 2,048 reads / 2,064 stores /
4,096 map bytes / zero vectors, zero differences. Every preceding complete
native CSV remains byte-identical: 388 / 392 files. The comparator requalifies
the complete attached control/clock chain, including the preceding masked prefix.

## Choices, lives and storage

The earlier native session selected Air (day index 1), easy difficulty and one
player. All five attempts failed; neither a successful settlement nor a title
selection change altered these retained choices. The diagnostic adapter uses
its typed native stage/difficulty and bounded single-player history, rather
than source configuration bytes. The reference records those original bytes
only as comparison targets and rejects different original configurations.

The native owner takes prior player state separately from requested title
choices. It commits each day and difficulty store at its own source boundary,
then initializes five lives for player zero and zero for the inactive player.
The current-life continuation is updated with the native campaign. The existing
native `Campaign::start` model supplies the resulting host campaign state.

Native functional tests cover all 40 combinations of five starting days, four
difficulties and one/two players, with prior player values different from the
request. They also verify the four-cycle difference between life-init branches.
Those tests are not original timing qualification for two-player or other
starting configurations. Production integration must supply the actual retained
title choices and prior player state; it must not generally replace requested
start values with the last played stunt's values.

The full 1,024-cell window map is cleared with one independent LCD-off readiness
read per cell. Padding and offscreen cells are included. Background and object
storage remain unchanged; direct original entry maps attach to the accepted
Start maps through the already-qualified unchanged register prefix. All native
final map bytes are compared against direct original storage. No snapshots,
poll counts or observed timing initialize native execution.

## Restart boundary

LCDC changes from 51 to d1 at the identified restart access. The native LCD
epoch is the access's inherited sample boundary; the return leaves execution
twenty cycles after that epoch, before EI. The new future STAT line is 95 and
VBlank line is 144. Services remain masked and both pending requests are kept.
Original IF bits 0/1 are independently read and compared at all nine new
boundaries; they remain three in both histories. This extends the earlier
prefix's derived pending-request bookkeeping with direct boundary evidence.

There are no display, input or audio services in this scope. Tick, countdown
and raw input stay unchanged. The next owner must accept the pending services
with the instruction callbacks; this result does not certify their acceptance,
first-frame rendering, pixels, PCM or instruction contents.

## Reproduction and validation

Existing extended Start controls already cover this endpoint; no new events,
extensions or button samples are needed. Both observed runs retain their
accepted full-control hashes. Native replay uses the unchanged Start button
file. The separate pinned comparison emulator and original ROM/data/recordings
remain local and absent from the native Windows program/distribution.

Capture using `tools/air_title_campaign_reference.py capture ROM --capture
EXTENDED_START_CONTROL --parent-out INSTRUCTION_PREFIX_REFERENCE --out
CAMPAIGN_REFERENCE`. Rebuild using `tools/build_air_clock_probe.py` and replay
the accepted full attempt extents/inputs with `--title-campaign` in place of
`--title-instruction`. Explicit fifth entry and all preceding owners remain
required. New output uses `.fifth.title-campaign*`, including final maps.

Compare with `tools/air_title_campaign_reference.py compare NATIVE_BASE`, the
same arguments as `air_title_instruction_reference.py compare`, plus
`--campaign-out CAMPAIGN_REFERENCE` and
`--instruction-prefix-base ACCEPTED_INSTRUCTION_PREFIX_NATIVE_BASE`.
Reports use `.title-campaign.comparison.json`. Local evidence uses
`air-title-campaign[-pause]-reference` and matching services CSVs.

Validation: optimized native Windows diagnostic, both full attached comparisons,
82,670 native campaign assertions, CLI guard and 1,049 Python tests. The new
native target joins the regular test build. Tests cover ordered player commits,
all window cells, preserved storage/counters, restart deadlines, native pending
requests and invalid/ineligible campaign choices/state. Synthetic evidence
tests reject altered IF values, early life/LCD changes, missing or detached
reads/stores, wrong original configurations and incomplete/detached maps.
Unchanged game/audio/shared-clock checks retain their earlier scope.

Regular Windows EXE rebuilt from committed source; semantic timing stays
diagnostic, outside the production scheduler. No release or automation change.
Next: pending display/STAT acceptance and initial instruction flow. Other menu/
campaign/player/stunt paths, vacant flags, qualifying name entry, full graphics/
pixels/PCM and final human/device/independent-Windows/distribution gates remain
open. [Final acceptance](ACCEPTANCE.md) is incomplete.
