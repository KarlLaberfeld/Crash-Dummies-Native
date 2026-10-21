# Selected initial-game map and interrupted-scene comparisons

October 21, 2026: all eight selected one/two-player, full/skip variants in both
retained histories match, zero differences in every accepted extent:

| Scope | Cases | Gameplay updates | Displays | Map boundaries | Row/map bytes |
|---|---:|---:|---:|---:|---:|
| First resource transfers, update 320 | 8 | 2,560 | 2,560 | 5,136 | 5,423,616 |
| Map-deferred uploads, update 640 | 8 | 5,120 | 5,120 | 10,256 | 10,830,336 |
| Interrupted scenes/partial rows, update 1,216 | 8 | 9,728 | 9,763 | 19,542 | 20,636,352 |

These are overlapping extents, not independent unique game frames. The 640
cases include 64 requests, 240 uploads, 64 completions and 16 map-deferred
displays. The 1,216 cases include 348 requests, 1,316 uploads, 344 completions
and 284 map-deferred displays; a request need not complete before the bounded
endpoint. There are 38 sprite, 15 map and 85 placement interruptions, including
eight displays during partial-row preparation. All 1,556,480 actor snapshots,
19,526 vectors and 390,520 sprite-presence/position/flag slots match in that
extent. Twelve map boundaries per eight-case family retain CPU read blocking;
none is read through the blocked CPU accessor. Validation: optimized diagnostic,
all accepted original comparisons and 1,757 Python tests. Production sources
are unchanged from the preceding full regression checkpoint.

The observation adapter emits the native row destination, all 32 staging bytes
and all 1,024 background tile-map bytes at entry, before/after every display
transfer and at the bounded endpoint. The existing semantic map owner produces
these values from decoded assets and retained native state. Original clocks,
return addresses, snapshots and service lists never enter native execution.

The separate pinned SameBoy observer reads physical `9800..9bff` storage through
`direct-vram-title-v1`. CPU read-block status remains in every observation. This
is necessary because some initial/end boundaries occur while CPU VRAM reads are
blocked; reading through the CPU memory accessor would return unrelated blocked
bus values. The default CPU-style map analyzer remains strict. Direct reads
require an explicit opt-in, matching observer metadata and an owner on every
boundary. No address range beyond that identified map is qualified here.

Every map recording is attached by file hash, ROM/control/player/input identity,
entry/end cycles and each independently recorded display-phase entry to its
accepted gameplay recording. A complete service pair is mandatory. Source
analysis checks the unchanged staging state during copying, exact transfer
work and the complete resulting map, including unchanged unrelated cells.
Comparison checks native completion times and all 1,056 bytes per boundary.

`selected_gameplay_reference.py` supports explicit 32/320/640/1216-update scopes.
Input preparation appends held A+Right for 300/620/1196 host frames to an accepted
instruction control, then releases both buttons and waits four frames. Two
unobserved prefix/full replays must agree with the observed replay. Larger
scopes preserve the accepted original/native first 32, 320 and (for 1216) 640
update streams. Neutral and right-only attempts without resource coverage remain
rejected. The 640 scope requires actual map-deferred uploads; the 1216 scope
requires interrupted sprites, map and placements plus a display during partial
row preparation and a matching byte-level row comparison.

Shared return addresses require the actual nested caller: the bank helper must
return to the scene-bank handoff; unsigned sprite-coordinate helpers must return
to their identified layout/culling operation. The short indirect scene-callback
prefix can accept STAT at its existing native completion boundaries. A display
before its row-publication gate is owned remains rejected. A service after the
counter wait's CALL/PUSH but before its initial counter read must match that
exact completion time; its counter snapshot includes that display and therefore
requires a later one. These are comparison filters for already reconstructed
native operations, not observed scheduling instructions.

Reproduce maps with `tools/selected_map_reference.py capture` using `--capture`,
`--gameplay-out`, `--out` and the local ROM. `compare-batch` takes the corresponding
selected-gameplay argument manifest with `map_out` added. For 640, gameplay
arguments additionally identify `resource_gameplay_out`, `resource_gameplay_base`
and `resource_gameplay_control` (the accepted 320 scope). For 1216 they also
identify `deferred_gameplay_out`, `deferred_gameplay_base` and
`deferred_gameplay_control` (the accepted 640 scope). The native flags are
`--players-gameplay --players-gameplay-updates N`; storage output ends in
`.fifth.selected.title-gameplay.map.csv`. Shared ancestors are qualified once per
batch and complete earlier native files are checked independently for each case.

This does not qualify sprite tile data, later/terminal gameplay, other stunts or
difficulties, player switching, rendered gameplay frames, PCM or production
Windows scheduling. See [selected instructions](SELECTED_INSTRUCTION.md), the
[remaining comparison matrix](ORIGINAL_COMPARISON_SCOPE.md) and
[final acceptance](ACCEPTANCE.md). ROM, decoded assets, source recordings and
reference binaries remain local. No final release or automation change.
