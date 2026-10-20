# Player-selection presentation and controls

Continuation update: the complete outgoing object clear, A/B title return,
selected one/two-player campaign, instruction picture/music/text/exit and first
Air game-entry displays are now separately compared. See
[selected instruction scope](SELECTED_INSTRUCTION.md). The earlier extent and
test counts below describe the original selection-only milestone.

October 20, 2026. Continues the accepted fresh first-page Select action in
both retained single-player Air/easy histories. Eight input-only cases per
history cover one/two players, A/B back decisions, held Select, combined
Up+Down+Select+Start, combined A+Start and the cursor's full blinking interval.

The qualified extent is 2749 through outgoing 1b2f object-clear entry: forty
closing waits, both complete clears, all forty-four glyphs, forty reopening
waits, cursor update and fresh selection/exit decisions. The arrow is written
before processing a fresh toggle; its Y is 72 or 88, X is 24, tile is 254 or
255 according to the independent tick bit, and attributes are 128. Select,
Up and Down share one toggle decision; holding creates no new edge, combined
toggle bits toggle once, toggling precedes Start and Start takes precedence
over A/B. Title music remains live throughout this owner.

All sixteen original/native comparisons match 7558 boundaries, 2016 display/music services, 7296 vectors, 10560 raster boundaries, 39312 polls, 36998 stores, 32768 map bytes, 4096 shadow-object bytes, 12096 voice rows, with zero
differences. Each preserves all 374 / 378 preceding complete native CSVs.
Two unobserved prefix/full control hash repetitions and the observed replay
agree. Preparation appends only fixed input tails to the accepted Select
control. Captures retain original maps, all 256 shadow-object bytes and active
voice fields; independent native execution owns every clock/input/selection/
glyph/cursor write. No original clock, state or interrupt schedule initializes
the native owner. ROM, assets and original measurements remain local.

Use `tools/air_title_players_reference.py prepare/capture/compare-batch`.
Prepare from the accepted Select action control; capture takes that control
plus its `actions.json` reference as parent. Native full-chain replay uses
`--title-players` and the capture's complete raw input stream. New CSVs use
`.fifth.title-players*`; reports use `.title-players.comparison.json`. Batch
argument dictionaries extend the action comparator with `actions_base`,
`players_out`, `players_control`. Shared ancestors are fully requalified once,
and each entire child prefix and source control is separately audited.

Validation: optimized native Windows diagnostic; all sixteen attached original
comparisons; 3,261 native selection assertions; 1,487 Python tests including
34 new provenance/storage/input/blink tests. The target joins the regular test
build. The comprehensive existing game/campaign/playthrough/audio suite passed
after the production pulse-envelope correction; these new diagnostics add no
further production behavior change. Final packaging still requires a clean
build of the saved revision.

This covers choosing and the outgoing decision, not the following object clear,
complete A/B menu return, two-player campaign startup or gameplay. Those paths,
other title pages/game families, rendered frames/PCM, independent Windows/device
tests and production scheduler integration remain open. The broader request
and final acceptance are incomplete. No release/automation change.
