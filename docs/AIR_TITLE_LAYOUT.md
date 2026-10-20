# Post-campaign title composition and masked LCD restart

October 20, 2026. Continues both accepted [masked title resets](AIR_TITLE_RESET.md)
through the already-shown boot-screen decision, static title composition,
callback/window/compare setup and LCD restart. Ends at 0258 **before EI**.
Pending-service acceptance, first-frame pixels and the following title fade/menu
remain separate owners. This is not complete production title timing.

Both ordinary and earlier-paused easy Air histories match 55 boundaries,
241 stores and all 2,048 map bytes each, with no interrupt services. Combined:
110 boundaries / 482 stores / 4,096 map bytes, zero differences. All 337 / 341
earlier complete native CSVs remain byte-identical. The composite requalifies
the complete preceding control/clock chain, including the masked reset.

The actual completed campaign establishes the native post-boot branch: the
one-time boot screen precedes campaign entry. Native execution supplies this
semantic condition, not the original C005 byte. Capture independently checks
that the original boot flag is nonzero. First-boot execution is rejected by
the new owner and remains unqualified here.

The four decoded rectangles contain 14x3 and 20x5 background cells, then 8x4
and 6x10 window cells. Their 234 stores retain all tile identifiers, including
values above 127; they are raw map identifiers, not text glyphs. Seven further
stores select the title STAT callback, configure display/window geometry and
restart the LCD. Every store's original start time/address/value is compared.
The entire final two-map storage is independently compared, including cells
that remain blank. Original high-score/name storage stays unchanged.

The native owner uses the actual reset maps, input and timing state. Its
identified layout entry includes the RST trampoline's JP before the layout
reader. Static dispatch, rectangle bank changes, row carry branches, glyph
stores and final returns have explicit source work. The first comparison
exposed that missing trampoline operation; adding its identified 16-cycle
work resolves the difference without a fitted offset. No source timestamps,
snapshots, decisions or measured costs initialize native execution.

Display/audio/input services remain masked. Tick, countdown, song 13 and the
held-button sentinel survive unchanged. The new LCD epoch determines future
line-23 STAT and line-144 VBlank deadlines; both older pending requests remain
distinct and unserviced at the endpoint. Window X/Y are 166/112. The new epoch
does not by itself establish first-frame rendering or IRQ acceptance.

The new ignored `title-layout.dat` contains only decoded static layout commands
and rectangle map cells. It contains no instruction stream or code pointers.
The port executes native composition loops; the separate emulator remains a
measurement tool only. Existing UI assets/extractors and production rendering
are unchanged. This map proof does not certify the earlier title-tile graphics
payload, first-frame pixels, full image output or PCM.

## Reproduction and validation

The existing final-result controls extend beyond this endpoint. No new input
extension or RAM modification is needed. Both instrumented captures match the
accepted full-control digests and pinned backend. ROM, decoded map data and
original recordings stay local.

Create the diagnostic asset with `tools/extract_title_layout.py ROM`; default
output is ignored `build/title-layout.dat`. Capture with
`tools/air_title_layout_reference.py capture ROM --capture CONTROL --parent-out
RESET_REFERENCE --out LAYOUT_REFERENCE`. Capture attaches to the accepted
reset endpoint and rejects changed controls, first-boot execution, missing/
reordered commands/rows/stores, service execution and changed score/map storage.

Build with `tools/build_air_clock_probe.py --out local/air-title-layout-clock-probe.exe`.
Use the accepted reset replay's complete attempt extents and inputs, replacing
`--title-reset` with `--title-layout`. Explicit fifth entry and all preceding
owners remain required. New outputs are `.fifth.title-layout*`, including the
complete map snapshot; earlier output stays exact.

Compare with `tools/air_title_layout_reference.py compare NATIVE_BASE`, the same
arguments as `air_title_reset_reference.py compare`, plus
`--layout-out LAYOUT_REFERENCE` and `--reset-base ACCEPTED_RESET_NATIVE_BASE`.
Reports are `.title-layout.comparison.json`. Local evidence uses
`air-title-layout[-pause]-reference` and `air-title-layout[-pause]-services.csv`;
controls remain `sameboy-air-fifth[-pause]-result-control`.

Validation: optimized native Windows diagnostic, both complete attached
comparisons, 2,117 native title-layout assertions, CLI ownership guard and 872
Python tests. Native tests cover complete composition including high-valued
identifiers, independent map layers, input preservation, restarted deadlines,
pending-service separation and malformed state/assets. New decoder/scope tests
exercise truncated/invalid layouts, map geometry, missing rows/cells and
masked-service violations. The new native tests join the regular test build.
Shared gameplay/audio/clock owners retain their prior integration scope and
were not needlessly retested. Regular Windows EXE rebuilt from committed
source; diagnostic timing is still outside its production scheduler. No new
release or automation change; ROM/data/recordings/binaries stay local.

Next: title pending-display/STAT acceptance, initial display services and fade.
Qualifying-score/name entry, vacant flags, other campaign/player/stunt/reset
paths, production timing, full images/PCM and human/device/independent-Windows/
distribution gates remain open. Timing point 1 and [final acceptance](ACCEPTANCE.md)
are incomplete.
