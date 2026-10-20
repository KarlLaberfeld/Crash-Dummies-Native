# Post-game-over masked title reset

Follow-up: [post-campaign title composition](AIR_TITLE_LAYOUT.md) now qualifies
both histories through the static maps, register setup and masked LCD restart.
Its endpoint is before EI; pending services, first-frame pixels and fade remain
unqualified.

October 20, 2026. Continues both accepted [game-over returns](AIR_GAME_OVER_RETURN.md)
from title-reset entry through LCD disable, map/object/selector reset, fixed
title-graphics copy work and data-bank restoration. The endpoint precedes the
first-boot decision at 0206. Title layout, LCD restart and a displayed title
screen are not yet qualified.

Both ordinary and earlier-paused easy Air histories match ten boundaries,
2,128 equality polls and 2,320 stores each, with no interrupt services. Combined:
20 boundaries / 4,256 polls / 4,640 stores, zero differences. All 331 / 335
earlier complete native CSVs remain byte-identical, including the final result
and non-ranking score/fade return. The composite also requalifies the complete
original parent chain and its accepted control hashes.

The native continuation starts from its actual game-over return state. Its
inherited LCD epoch determines the line-145 equality wait; no observed poll
count, end time or snapshot enters execution. Services are masked immediately,
so tick, countdown, input edges and audio do not advance during reset. Both
pending interrupt requests arise before LCD disable. The old LCD epoch and
deadlines remain history; the later title display requires a separate restart.

The clear owner writes 1,024 window cells, 1,024 background cells and all 256
object-list bytes, including the unused tail. Sixteen further stores reset
object count, scroll and title/campaign selectors, and set the held-input
sentinel to 255 while retaining the pressed edge. Original score/name storage
is observed unchanged. The native masked state retains its own cleared maps
and object list; there is no source-state import.

Source work follows the identified LCD-off clear/copy branches: map glyphs use
144 cycles each, fixed graphics bytes use 104 cycles each, with the final
branch and wrappers accounted separately. The two graphics transfers have
1,920 and 4,096 bytes, respectively. This proves their work and endpoints,
**not their complete graphics payload or rendered pixels**. Those data/image
comparisons remain separate acceptance work. The inherited result LCD value
comes from its existing 0421 setup; bank transitions are title bank 3 and data
bank 1. No generic CPU/instruction execution is introduced.

## Reproduction and validation

The existing final-result controls already extend beyond this endpoint. No
input extension or RAM modification is needed. Each new instrumented original
run matches its existing full-control digest and pinned independent backend.
The separately authorized reference emulator is used only for measurement.

Capture with `tools/air_title_reset_reference.py capture ROM --capture CONTROL
--parent-out RETURN_REFERENCE --out RESET_REFERENCE`. It attaches to the
accepted return endpoint and rejects changed controls, reordered/missing
stores, advanced display counters, interrupts, changed scores and incomplete
LCD/bank transitions. ROM, original observations and graphics stay local.

Build with `tools/build_air_clock_probe.py --out local/air-title-reset-clock-probe.exe`.
Use the accepted final-result controls, complete attempt extents and return
recording's display inputs, replacing `--fifth-return` with `--title-reset`.
Explicit fifth entry and all preceding owners remain required. New outputs
are `.fifth.title-reset*`; all previous outputs retain their complete bytes.

Compare with `tools/air_title_reset_reference.py compare NATIVE_BASE`, the same
arguments as `air_game_over_return_reference.py compare`, plus
`--reset-out RESET_REFERENCE` and `--return-base ACCEPTED_RETURN_NATIVE_BASE`.
Reports are `.title-reset.comparison.json`. Local evidence uses
`air-title-reset[-pause]-reference` and `air-title-reset[-pause]-services.csv`;
the unchanged controls remain `sameboy-air-fifth[-pause]-result-control`.

Validation: optimized native Windows diagnostic, both complete attached
comparisons, 27,087 native title-reset assertions and 848 Python tests. Native
tests cover inherited scanline wrap, equality completion, pending requests,
full map/object clears, input sentinel/edge distinction and rejected entries.
The new native tests are included in the regular build's test option. Shared
gameplay/audio/clock owners are unchanged; their prior integration tests retain
their scope and are not repeated. The regular Windows EXE is rebuilt from
committed source; this timing remains diagnostic, outside its production
scheduler. No new release or automation change is made.

Next: post-reset first-boot/title layout and LCD restart, plus a separately
controlled qualifying-score/name-entry case. Other campaigns/players, vacant
flags, remaining UI/reset/work, production timing, full images/PCM and final
human/device/independent-Windows/distribution gates remain open. Timing point 1
and [final acceptance](ACCEPTANCE.md) remain incomplete.
