# Source-owned Air row staging and publication

The [third-failure continuation](AIR_THIRD_RESULT.md) now reuses this owner
across following updates and qualifies two additional partial-row displays.
Following startup can seed the published map from native instruction stores:
ring row 22 is not overwritten by that level's initial row loop. Its retained
text, subsequent overwrite and complete staging/publication match the original.
The earlier successful-control evidence below retains its own scope and hashes.

`src/air_map_publication.h` reconstructs the original 32-byte staging row and
32x32 background map. LCD-off startup prepares and copies the 32 source rows.
Later preparation computes the destination from the previous camera, picks the
metatile row/direction and replaces each left/right tile separately. The scene
clock commits the destination and every byte at its identified source write.
Display publication copies the current buffer to the current destination, even
when preparation is unfinished. No captured tile, time or original register
drives this native algorithm. Windows rendering/scheduling is still unchanged.

This closes the observed successful-control interruption at 1eda: its display
still sees the previous destination and staging buffer. Previously scalar
transfer work was owned, but selecting its image rejected. The native image
projection now uses the published map. Subsequent preparation cannot replace
bytes already copied by that display retroactively.

The independently controlled successful Air replay matches all 5,114
boundaries: startup, both sides of 2,556 display transfers and the explicit
0409 terminal result-setup boundary. All absolute times, flags, destinations,
32 staging bytes and 1,024 published tiles agree: 5,400,384 byte comparisons,
zero differences. Original tile snapshots check unblocked reads; this is not
an arbitrary blocked VRAM observer. Missing/reordered pairs, transfers that
change staging, wrong bytes/work, blocked reads and common-prefix truncation reject.

Three consecutive complete original images around the interruption also agree:
original services 2369..2371 / native publications 2368..2370, 69,120 pixels,
no masks. All 262 previously selected images pass again with buffered projection.
The union is 265 complete selected images / 6,105,600 pixels. These extend an
existing successful control, not a new independent gameplay pattern.

Full successful gameplay/service/phase/entity/input/sprite comparison, all
5,112 gameplay vectors, result prefix and incoming result pass again. Existing
image regressions also retain 222 outgoing phases and 96 fade services.
Unchanged production campaigns were not repeated. ROM-free source tests pass
4,200 assertions, including all 32 partial byte positions and publication before
destination completion. Python passes 226 tests; result tests retain 4,646 assertions.

Local proof: `local/air-success-map-reference/map.json`,
`local/air-success-map-native/map.csv`, `local/air-map-final-comparison.log`,
`local/air-success-map-pixels-reference/`, `local/air-map-pixel-regression.log`,
`local/air-map-last-line-comparison.log`, `local/air-map-main-regression.log`,
`local/air-map-unit-tests.log` and `local/air-map-python-tests.log`.
All captures and assets remain ignored/local.

```powershell
python tools/build_air_clock_probe.py
local/air-clock-probe.exe local/sameboy-air-finish-search/120-56/inputs.txt local/air-success-map-native/services.csv 0 --display-inputs local/air-success-finish-native/buttons.txt --outro-fade --map-csv local/air-success-map-native/map.csv
python tools/air_map_reference.py compare local/air-success-map-native/map.csv --capture local/sameboy-air-finish-search/120-56 --out local/air-success-map-reference --startup local/air-result-success-startup
```

Unobserved entity/resource interruptions, protected pause crossings, earlier
UI/LCD entry, special results and subsequent player/stunt setup remain open.
This bounds the observed row interruption and selected images, not every
possible visible access, result pixels/PCM, hardware or the Windows clock.
Requested timing point 1 is not complete.
