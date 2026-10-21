# Actual subsequent-player Air active/resource comparison

October 21, 2026: all four representative cases match, zero differences:
1,280 updates, 12,800 boundaries, 204,800 actor slots
(38,855 occupied), 1,280 displays, 2,560 vectors,
51,200 sprite slots, 8 requests, 32 uploads and
8 completions. No map-deferred upload is claimed. Totals include
the shared accepted first 32 updates. Each case preserves 580/584 complete
earlier native CSVs plus the five first-32 gameplay byte prefixes.

Validation: 1,969 Python tests and four native CLI ownership guards pass. A fresh
optimized second-player replay preserves all 589 complete case CSVs; unchanged
default-32 replays preserve all 589/593 CSVs. One public-entry integration check
requalifies its complete accepted ancestry; other parent graphs reuse previously
qualified unchanged records. Production source/build/native test code is
unchanged, so the full Windows regression remains the passing preceding entry
milestone. The Windows EXE is rebuilt from the saved clean source revision.

This extends four representative [actual-turn entry controls](SELECTED_TURN.md)
through 320 updates: one/two players in the ordinary and earlier-pause histories,
with full initial and following instructions. Player one retains four lives;
the actual second player has five while player one retains four. The remaining
fourteen entry-control variants retain their earlier 32-update qualification.

Each accepted control receives A+Right held for 300 frames, then release and
four idle frames. Two independent unobserved prefix/full replays must agree.
The original observer reuses the identical accepted entry record and exact
entry input prefix, attaches at its actual cycle and observes all 320 updates.
It requires unchanged control/setup/backend/ROM identities and an unchanged
accepted first-32 original point/interrupt prefix. It does not relabel an
initial selected-game recording as a subsequent-player recording.

The native diagnostic adds `--players-turn-updates 320` with the existing
`--players-turn-gameplay`. Its separate `--players-gameplay-updates N` remains
the actual preceding initial terminal extent. Unsupported turn extents and
turn-update requests without their gameplay owner reject. The existing default
remains 32 and preserves both complete default replay cases byte for byte.
No reference state, clock, resource result or update timing initializes native
execution. Production game and scheduler code are unchanged.

Comparison requires active resource requests, wait-owned uploads and completed
frame/flag publication. Scalar and occupied actor state, callback work, exact
interrupt/display/input/audio work and sprite positions/flags are checked.
All complete native ancestors and setup/entry CSVs remain unchanged; the first
32 native point/actor/service/vector/sprite streams must be exact byte prefixes.
The longer summary and row/map diagnostic streams are separate endpoints.
An initial comparison guard correctly rejected its incomplete filename glob;
the corrected enumerator includes the base CSV and requires core earlier
families. Regression tests cover missing/changed complete ancestors and changed
gameplay prefixes. No failed case is counted as accepted evidence.

Prepare with `tools/selected_turn_active_reference.py prepare ROM --capture
TURN_CONTROL --out ACTIVE_CONTROL`. Capture using `capture ROM --capture
ACTIVE_CONTROL --accepted-control TURN_CONTROL --parent-out TURN_REFERENCE
--out ACTIVE_REFERENCE`. Compare with `compare --capture ACTIVE_CONTROL
--accepted-control TURN_CONTROL --parent-out TURN_REFERENCE --out
ACTIVE_REFERENCE --native-base ACTIVE_BASE --parent-base TURN_BASE
--parent-manifest TURN_MANIFEST --instruction-manifest INSTRUCTION_MANIFEST
--outcome-manifest OUTCOME_MANIFEST --terminal-manifest TERMINAL_MAP_MANIFEST`.
The public entry point first qualifies its exact accepted 32-update case and
complete earlier ancestry. Local batches can reuse unchanged previously
qualified parent graphs while retaining all new identity/prefix comparisons.
ROM, extracted assets, controls, recordings and reference binaries stay local.

This scope does not qualify deferred uploads, interrupted sprite/map/placement
work, partial-row bytes, pause, terminal/outcome handling or later campaign
turns. Sprite tile bytes, rendered frames/PCM and production scheduling remain
unqualified. Remaining instruction-control variants, other stunts/difficulties,
retained menu/password/score paths and final Windows/device/distribution gates
remain open. This is not a final release or completion of the broad request.
