# Player selection after later title pages

October 21, 2026: 176 further original/native comparisons match, zero
differences. The accepted first-page A ancestry reaches each later page (1..4)
in both retained histories. Each page then uses all eight selection cases:
one/two-player Start, A/B back, held Select, simultaneous toggle/Start,
simultaneous A/Start and cursor blinking.

| Extent | Cases | Boundaries | Displays | Map bytes | Picture tile bytes | Voice rows |
|---|---:|---:|---:|---:|---:|---:|
| Complete Select presentation/cursor/decision | 64 | 59,672 | 13,952 | 131,072 | - | 83,712 |
| Complete object clear and Start or A/B return | 64 | 4,400 | 1,312 | 131,072 | - | 7,872 |
| Selected Start through instruction music/picture | 48 | 5,952 | 2,016 | 589,824 | 49,152 | 10,656 |

Counts describe bounded, overlapping extents, not independent complete games.
The first extent includes all 40 close waits, both clears, selection text,
40 open waits, cursor bytes/blinking, fresh input priority and live music.
The second includes all 160 object-clear stores. A/B then resets the actual
retained page index, closes, clears, composes page zero and reopens it. Start
retains the page and chosen player count. The third includes fade/audio stop,
masked setup, fresh campaign/lives, LCD restart and pending services, header,
instruction music and picture.

The native Select entry validates an explicit completed-carousel origin, its
retained page timer and future deadlines. First-page absolute guards remain
intact. Only actual selection sets `selectedPlayers`; no later title page is
relabeled as player selection. The exit now retains its real page until the
original page-reset operation, then clears the carousel marker after A/B return.
The existing semantic screen, campaign and audio owners execute every phase.
Original times, services, snapshots and queues never initialize native state.

Source observations attach to the exact accepted `cycle.json`, then to exact
player/exit files and controls by hash. Their real carousel and selection case
labels remain distinct. Observers may be installed immediately before the
verified fresh-input suffix, while replaying every original event unchanged.
A full-prefix and late-hook replay produced byte-identical observations/buttons.
Two independently replayed uninstrumented prefix checkpoints accelerated local
control preparation; matching normal complete controls were checked as well.
Observed source runs still replay the complete original setup/input history and
must match accepted prefix and complete-control hashes. These checkpoints are
reference-only and never native playback inputs.

Prepare/capture later Select with `tools/air_title_players_reference.py`, using
`--capture CYCLE_CONTROL --later-parent CYCLE_REFERENCE`, and `--case CASE`
optionally during preparation. Capture additionally takes the selected child
`--control` and the same `--parent-out CYCLE_REFERENCE`. Extend player controls
and capture the complete exit with `tools/air_title_players_exit_reference.py`.
Then `tools/selected_instruction_reference.py capture` observes the same exit
control through picture completion. See the earlier [selection workflow](AIR_TITLE_PLAYERS.md)
and [selected instructions](SELECTED_INSTRUCTION.md) for the full native parent chain.

The diagnostic adds `--title-cycle-action-page N` with one of
`--title-cycle-players`, `--title-cycle-players-exit`, or
`--title-cycle-players-picture`. New output stems use `.fifth.later.*`, with
`.fifth.later.selected.title-*` for the selected instructions. Later-selection
manifests retain the original first-page action arguments and add `later_base`,
`later_out`, `later_control` and the actual child paths. The player and exit
modules provide `compare-later-batch`; the instruction module provides
`compare-later-selected-batch`. Every complete native ancestor CSV is audited,
and each child retains its exact already-qualified parent, including raw buttons.

Validation: 23,795 native player/continuation/instruction assertions across
first and later pages, 1,863 Python tests, optimized diagnostic and full native
Windows game/campaign/playthrough/audio/sprite regression pass. Fresh final
probe replays check the complete output against accepted runs. These are
original clock/access/storage/logical-voice comparisons; they do not establish
rendered transition frames, PCM, physical devices or Windows scheduler parity.

See [later full/skip text](LATER_INSTRUCTION_TEXT.md), the
[comparison matrix](ORIGINAL_COMPARISON_SCOPE.md) and [acceptance](ACCEPTANCE.md).
Further retained menu/password use, later gameplay/player switching, other
stunts/difficulties/outcomes, changed scores/name entry and final output/device
checks remain open. ROM/assets/recordings/reference binaries stay local.
No final release is claimed.
