# Actual subsequent-player Air setup, entry and first updates

October 21, 2026: all eighteen cases match, zero differences. Entry totals:
576 boundaries, 36 displays, 72 vectors,
30,843 readiness reads, 9,216 clear stores and 216 logical
voice rows. Gameplay totals: 576 updates, 5,760 boundaries,
92,160 actor slots (15,660 occupied), 576 displays,
1,152 vectors and 23,040 sprite slots. Shared ancestors overlap.
Every case preserves all 560 ordinary-history or 564 earlier-pause complete
native ancestor CSVs. Fresh final-binary replays preserve all 589/593 complete
case CSVs byte for byte.

Validation: 1,956 Python tests, 970 native handoff checks, 52,922 clock checks,
4,281 source-work checks and the full native Windows game/campaign/playthrough/
audio/sprite regression pass. A public-entry integration check requalifies one
complete ancestry; the other parent graphs reuse previously qualified unchanged
records. Normal builds now run the native handoff tests. A clean Windows
EXE is rebuilt from the saved source revision; production scheduling remains
unchanged and unqualified. This is not a final release.

This continues the eighteen accepted [post-result instruction controls](SELECTED_FOLLOWING_INSTRUCTION.md).
It observes the actual next live player after the selected Air/easy failure:
player one with four lives in a one-player campaign, or player two with five
lives while player one retains four. It does not construct a new campaign or
borrow the initial player's entry state.

Each exact parent receives another 80 idle frames. Two independent unobserved
replays retain the parent fingerprint and agree on the full child fingerprint.
The observer attaches at the parent's precise instruction completion, follows
masked setup and LCD restart, and records the first 32 quiet game updates.
The canonical parent input stream remains intact, including full-prompt,
deliberate late-skip and qualified second-player ignored-Start-during-scroll
controls in both ordinary and earlier-pause histories.

The native continuation inherits its own completed game's animation blocks,
including vacant-slot delay/period, partial second, previous side push and
last map camera. It uses the actual result/player owner and independently
decoded local assets. Reference cycles, snapshots, lives and outcomes never
initialize native playback. An explicit guarded next-player route permits the
qualified player-zero-to-player-one handoff; the existing same-player route
still rejects an accidental player switch.

The first pilot exposed a four-cycle stage-setup difference. The initial map
row loop reads the surviving native map cursor; resetting it to the legacy
initial-entry value selects the other direction branch. The continuation now
supplies its preceding native game's cursor to the map-work owner. Source
observations require that cursor to survive masked preparation until the
actual initial-row operation, then retain the prepared final row. Existing
initial/retry defaults and every complete parent CSV remain unchanged. No
timing allowance or measured duration was substituted.

Compared entry fields include exact setup/entry boundaries, readiness reads,
all 512 object/actor clear stores, interrupt masking and restart, actual
player/lives, camera, RNG, HUD/fade/input state, display/input/music work and
six logical voices. Gameplay comparison includes all 32 updates, scalar state,
all sixteen actor slots at every boundary (occupied payload plus inherited
vacant delay/period), resource ownership, interrupt times and sprite
positions/flags. Native campaign identity and both life counts remain checked
after those updates.

The public comparator first requalifies the exact accepted instruction,
outcome and terminal/map ancestry using explicit manifests. It then requires
the unchanged full native ancestor CSVs, source/control/backend/ROM/setup/file
identities, complete raw input prefix and the new entry/gameplay observations.
Local batches may reuse already-qualified unchanged parents, but retain all
identity, prefix and new comparison checks.

Prepare with `tools/selected_turn_reference.py prepare ROM --capture
INSTRUCTION_CONTROL --out TURN_CONTROL`. Capture with `capture ROM --capture
TURN_CONTROL --accepted-control INSTRUCTION_CONTROL --parent-out
INSTRUCTION_REFERENCE --out TURN_REFERENCE`. The full native diagnostic uses
`--players-turn-gameplay --players-gameplay-updates N`, where N remains that
case's actual preceding initial terminal extent, and the complete child raw
button stream. `--players-turn-entry` stops after entry. Other chain options
follow [selected terminal gameplay](SELECTED_TERMINAL.md).

Compare using `compare --capture TURN_CONTROL --accepted-control
INSTRUCTION_CONTROL --parent-out INSTRUCTION_REFERENCE --out TURN_REFERENCE
--native-base TURN_BASE --parent-base INSTRUCTION_BASE --parent-manifest
INSTRUCTION_MANIFEST --outcome-manifest OUTCOME_MANIFEST --terminal-manifest
TERMINAL_MAP_MANIFEST --startup ORIGINAL_STARTUP`. Original ROM, decoded data,
controls, recordings and reference binaries remain local.

This scope ends after 32 quiet updates. Later active/resource/row/pause/outcome
work in the subsequent attempt remains open, as do other stunts/difficulties,
campaign elimination/endings, retained menus/passwords, changed high scores,
rendered frames/PCM, production scheduler integration and final Windows/device/
distribution acceptance. It does not qualify sprite tile bytes, map publication
bytes or arbitrary vacant actor payloads. No final release is claimed.
