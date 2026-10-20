# Selected-player instruction and initial-game comparisons

October 20, 2026. The accepted Select-page decision now continues through the
complete native object clear, selected campaign startup, instruction music and
picture, incoming fade, text, prompt/skip and the first Air gameplay entry.
Both retained histories are included; the second history previously paused in
gameplay. These are diagnostic timing owners, not production scheduler acceptance.

The sixteen selection continuations match all 160 outgoing object stores.
Start returns after 1,316 mainline cycles. A/B complete the forty closing waits,
two clears, ten-row first page and forty reopening waits; song 1 continues and
the 480-update menu duration is restored. The selected player count is retained.
Totals: 1,100 boundaries, 328 displays, 1,296 vectors, 1,936 raster points,
11,384 polls, 10,128 stores, 32,768 map bytes, 4,096 object bytes and 1,968
voice rows. All sixteen comparisons have zero differences.

Twelve selected Start cases cover one/two players, held Select, simultaneous
toggle/Start, A/Start and cursor blinking. They match the outgoing fade and
audio stop, masked instruction setup, fresh campaign lives, pending requests,
full header and instruction picture/music. Two players receive five lives each;
one player leaves the second record at zero. Totals: 1,488 boundaries, 504
displays, 1,416 vectors, 1,608 raster points, 141,590 polls, 42,792 stores,
147,456 map bytes, 12,288 tile bytes and 2,664 voice rows, zero differences.

Eight append-only children cover one/two players with complete text/fresh Start
and deliberate skip/held Start in both histories. Incoming palette masks,
all text/glyph/readiness/scroll work, the prompt, outgoing fade and logical
music stop match. Totals: 12,416 boundaries, 5,632 displays, 11,264 vectors,
1,288 polls, 544 glyph stores, 11,816 other stores, 49,152 map bytes, 24,576
tile bytes and 33,792 voice rows. Each retains all 439 / 443 preceding complete
native CSVs byte for byte. All eight comparisons have zero differences.

Those same eight controls also qualify 0355..03d8: LCD-off equality polling,
both complete 256-byte clears, masked Air/easy stage work, scene seed,
resource/HUD work, game-music startup, pending and periodic vectors and the
first two game displays. All eight comparisons match. This does not qualify
the subsequent gameplay body or copied scene/HUD/actor payloads. Stage fields
that have not yet been overwritten retain the existing explicit scratch-field
exclusions; no new allowance or observed schedule initializes native execution.

## Provenance and boundaries

Controls append inputs to accepted histories. Both unobserved prefix/full
hash repetitions agree with the observed replay. The ROM, setup and backend
identity are checked independently. Captures use pinned SameBoy 1.0.3 DMG-B
only for reference; all recordings, assets, ROM and reference binaries remain
local. Direct map/tile/object snapshots and active logical voice fields are
compared. A disabled driver's parked raw voice flags are retained in source
recordings but are not asserted to be native playback. The established unused
text delay/cursor and voice payload exclusions remain explicit.

Raw input-file sample numbers include earlier history than the native timing
owner's display counter. Their complete prefix is checked separately; comparison
service numbering comes from the independently qualified parent summary. Actual
source cycles, ticks, work, vectors and service counts are still compared.

A real shared readiness discrepancy was corrected: the pinned reference keeps
mode 0 through dot 5 of line 144, before entering mode 1 at dot 6. The
native model now exposes that boundary too. Both modes permit VRAM access;
no wait duration or fitted work offset was added. This is reference-model
evidence, not independent physical-hardware verification.

## Reproduction

Use `tools/air_title_players_exit_reference.py prepare/capture/compare-batch`
after accepted player-selection captures, then
`tools/selected_instruction_reference.py capture/compare-batch` for Start.
The latter extends player-exit arguments with `exit_base`, `selected_out`.
Native flags are `--players-exit` and `--players-picture`.

Prepare full/skip children with `tools/air_title_text_controls.py`, then use
`tools/selected_text_reference.py capture/compare-batch`. Capture requires
`--accepted-control`, `--parent-out`, `--capture`, `--out`; batches extend the
selected instruction arguments with `selected_base`, `text_control`,
`selected_text_out`. Native flag: `--players-text-exit`.

`tools/selected_game_entry_reference.py capture/compare-batch` uses the same
text controls; extend text comparator arguments with `text_base`,
`game_entry_out`. Native flag: `--players-game-entry`. All flags replay the
complete earlier native chain with only decoded assets and raw button inputs.
Shared ancestors are qualified once per batch and every complete child prefix
is separately audited. CSV stems use `.fifth.selected.title-*`.

Optimized native tests cover 4,751 player/continuation/instruction/game-entry
assertions. The Python integrity suite checks detachment, missing observations,
wrong lives/choices, changed storage, pending-service priority and partial audio
reset coverage. The shared pause, resume and page regressions also pass.

Other campaigns, further gameplay and player switching, later menu actions,
modified high scores, rendered frames/PCM, production scheduling and final
Windows/device acceptance remain open. See the [matrix](ORIGINAL_COMPARISON_SCOPE.md).
The broader request is not complete; no final release or automation change.
