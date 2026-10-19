# Final life and game-over result

October 19, 2026. Continues both accepted
[complete final Air attempts/outgoing fades](AIR_FIFTH_GAMEPLAY.md) through
result setup, the single remaining life decrement, game-over text and savings,
song 13, incoming fade and the fixed 480-display hold. Stops at the high-score
routine's call boundary; high-score selection/name entry and subsequent player
or title return are not yet timing-qualified. The release remains an alpha.

## Original comparison

| Scope | Ordinary | Earlier second-entry pause | Combined |
|---|---:|---:|---:|
| Common result-prefix boundaries | 10 | 10 | 20 |
| Prefix equality polls | 2,121 | 2,121 | 4,242 |
| Final-result boundaries | 1,054 | 1,054 | 2,108 |
| Displays | 514 | 514 | 1,028 |
| Complete vectors | 1,028 | 1,028 | 2,056 |
| Game-over glyph readiness polls | 186 | 186 | 372 |
| Game-over glyph stores | 31 | 31 | 62 |
| Fixed-hold displays, included above | 480 | 480 | 960 |
| Earlier complete native CSVs retained | 313 | 317 | 630 |

All compared fields have zero differences. Lives remain one through masked
setup, portrait/text and the pending startup services, then become zero exactly
at the life store. The taken final branch takes 16 cycles; the established
non-final branch remains 12. No life is consumed at instruction Start or twice
at the result. Current native state owns the continuation throughout.

These two histories both started with zero savings and completed only failed
attempts, so no successful payout owner ran. The diagnostic supplies the native
campaign's unchanged initial zero, rather than reading an original amount.
Original comparison therefore qualifies zero savings only. Synthetic native
tests separately exercise amounts from zero to 999,999 and forced cents.

The final hold calls the fixed-count routine, not the action-skippable failure
hold. Native tests introduce fresh A/Start edges while retaining all 480 waits.
The fixed original controls retain their held buttons and the original source
branch tests only the loop count. There is no claim that all original input,
reset, timeout, player or savings variants have been measured.

## Two newly identified work owners

Game-over text starts during the first LCD-on frame. Its local source capture
observes the cleared 256-byte prepared object list and non-window/non-scrolling
geometry. Both first-frame text sequences match all readiness polls and stores.
Only the explicit empty-result owner admits visible lines after the first
restart line and before line 143 in that frame. First-line behavior, arbitrary
first-frame VRAM reads/writes, changing scroll/window/objects and hardware
qualification remain excluded. Existing steady-frame callers retain their
first-frame rejection.

Later game-over music exposed a four-cycle work error in 23 services per
history. An independently hooked source service isolates it to the noise
voice's instrument lookup: the original tests bit 7 in A, whereas pulse voices
test [HL]. The register test costs eight cycles rather than twelve. Both noise
voices now share the correct work formula in native and verification code.
The six-voice/18-command sparse source service and every complete final-result
music service agree after this correction. No fitted service correction,
timestamp or source voice state drives native playback. PCM remains unqualified.

The common incoming implementation has explicit final/non-final ownership.
The established incoming API still rejects last-life failure; only the separate
final owner accepts one life and the failure selectors/countdown. It returns
from its bounded prefix at zero lives before drawing the game-over text. Final
result assets and native input guards reject unsupported modes and missing data.

The local diagnostic text asset adds a sixth decoded static layout in format
`TICDRL03`. Versions 01/02 remain supported for earlier owners; their capabilities
do not silently acquire a game-over banner. The five existing layout bodies
and all other UI extraction outputs, including the packaged `ui.dat`, remain
byte-identical. No original strings, glyph data or recordings are added to Git.

## Control attachment and reproduction

Each original control preserves its complete accepted final-gameplay events
and appends 1,000 frames with unchanged buttons. Two uninstrumented repetitions
match both the parent RAM digest and the new final digest. All hooked endpoints
match that child digest and the pinned reference backend. Setup state and
initial input file remain unchanged; no RAM, life, seed, money or clock injection
is used. ROM, decoded files, observations and binaries remain local.

With the usual ROM, `--capture` and `--out` arguments, capture:

- `tools/air_startup_reference.py capture` into a fresh startup folder.
- `tools/air_result_prefix_reference.py capture --next-retry --after-retry 3`.
- `tools/air_final_result_reference.py capture` last, to retain all preceding raw display button samples.

Generation four is now explicitly available to the original result selector;
instruction and entry selectors still reject a later, unowned generation. The
new final capture requires the fifth Air failure, one life becoming zero,
complete pending/periodic services, the fixed hold and the bounded text geometry.
Incomplete or changed-control captures fail rather than claiming acceptance.

Refresh local UI diagnostic assets with `tools/extract_ui.py`, then build with
`tools/build_air_clock_probe.py --out local/air-final-result-clock-probe.exe`.
Use the complete fifth replay's initial/display inputs, the new final-result
`buttons.txt`, and its unchanged ordinary extents 1,788 / 1,789 / 1,788 / 1,789
or paused extents 1,767 / 1,604 / 1,764 / 1,762. Keep `--fifth-entry` and replace
`--fifth-terminal` with `--fifth-result`; the paused history also keeps
`--following-entry-pause`. Explicit entry, instruction, predecessor result and
terminal ownership are still required. The diagnostic continues its existing
initial phase/counter/seed header; no new original-state initialization is added.

Run `tools/air_final_result_reference.py compare NATIVE_BASE` with new child
`--capture`, `--out`, `--startup`; accepted final-gameplay `--accepted-base`,
`--accepted-capture`, `--accepted-out`, `--accepted-startup`; and the earlier
entry/instruction chain arguments used by `air_fifth_gameplay_reference.py`
(`--first-base`, `--start-capture`, `--start-out`, `--start-startup`,
`--parent-capture`, `--parent-out`, `--parent-startup`, `--parent-result-out`,
`--instruction-base`). The composite requalifies the accepted parent under its
original hashes, verifies complete native byte identity, attaches new prefix
and campaign/input/seed state, then compares the final result. Output is
`.final-result.comparison.json`; native final files use `.fifth.final-result*`,
with the common setup under `.fifth.next-result*`.

Local evidence uses `sameboy-air-fifth[-pause]-result-control`,
`air-final[-pause]-result-reference/startup`, and
`air-final[-pause]-result-services.csv`. The sparse music observation is
`air-final-music-330`. These are ignored/local.

Validation: optimized native Windows diagnostic, both attached original
comparisons, 29,712 native final-result assertions, 52,920 result-clock
assertions and 825 Python tests. The Windows build also runs existing
controller/source-work/pause/native game/audio checks; all three native
integration scenarios (one player, two players, eliminated player) pass.
These tests are not additional original-timing comparisons. Published
timing scope remains diagnostic: it is not yet integrated into the production
Windows scheduler, and no new alpha release is published. Automation settings
are unchanged.

Follow-up: [non-ranking score and title-reset entry](AIR_GAME_OVER_RETURN.md)
now match both zero-savings histories. Next: qualifying high-score/name entry and internal title
flow. Nonzero-savings original cases, never-allocated vacant done flags, other
campaigns/stunts/players, earlier UI/reset/unobserved work, production scheduling,
complete images/PCM and human/controller/independent-Windows/distribution gates
remain open. Timing point 1 and [final acceptance](ACCEPTANCE.md) are incomplete.
