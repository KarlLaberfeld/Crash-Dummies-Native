# Actual subsequent-player Air active/resource comparison

October 21, 2026: sixteen actual-turn active instruction-control variants now
match through 320 updates, zero differences. Twelve new cases extend the
previous four representative controls. Totals: 5,120 updates,
51,200 boundaries, 819,200 actor slots (155,608 occupied),
5,120 displays, 10,240 vectors, 204,800 sprite slots,
32 resource requests, 128 uploads and 32 completions.
Shared first-32 ancestors overlap. No map-deferred upload is claimed.

The scope includes one/two-player initial full/skip instructions and following
full confirmation or deliberate late skip/held exit in both histories. Two
ignored-Start-during-scroll controls correctly reject active-resource coverage:
all 3,200 observed boundaries retain an empty queue. Their earlier 32-update
qualification stands; a separately owned coast scope or later active extent is
still required. Neither rejected recording is counted as accepted. Every accepted case keeps
its actual player/lives, native animation/timer/side-push/map cursor, unchanged
entry and accepted first 32 original/native updates. Each preserves 580/584
complete earlier native CSVs plus five early gameplay byte prefixes.

A new late-skip public-entry integration check qualifies its complete ancestry;
a fresh optimized late-skip replay preserves all 589 complete case CSVs. The
four previously accepted cases are reused unchanged. Diagnostic/production/
test source is unchanged, so the passing 1,969 Python tests, CLI guards and
preceding full Windows regression are not repeated without a new hypothesis.
The Windows EXE is rebuilt from the saved clean source revision.

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
unqualified. Other stunts/difficulties,
retained menu/password/score paths and final Windows/device/distribution gates
remain open. This is not a final release or completion of the broad request.
