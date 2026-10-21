# Selected initial failure, player handoff and next instruction picture

October 21, 2026: eight attached original/native comparisons cover the actual
first selected Air/easy failure after one/two-player Start and full/held-skip
instructions in both retained histories. Each starts at its independently
qualified terminal wait, rather than creating a new campaign or replay origin.

Totals: 9,304 boundaries, 4,432 displays, 8,864 vectors, 17,416 graphics stores
and 24,864 logical voice rows, zero differences. Each case preserves all 494
ordinary-history or 498 earlier-pause complete native CSV ancestors. The
optimized diagnostic and 1,897 Python tests pass. The full native Windows
regression passed at the preceding menu/text checkpoint; production code is
unchanged by this diagnostic-only follow-up.

The comparison includes outgoing audio stop and all fade phases; masked result
setup and LCD polling; failure text/portrait, music startup, pending interrupts,
incoming fade, full 480-display hold and music stop; exactly one consumed life;
live-player selection and LCD-safe map clear; the next player/lives/stage header;
instruction song startup, six logical voices, 1,024 tile stores and 90 picture
map stores through the actual transition entry at 268b.

Player one's lives change from five to four. A one-player campaign skips the
inactive second player and returns to player one. A two-player campaign selects
player two with the original five lives, stage Air and easy difficulty. The
native continuation retains its own actual campaign and completed game. It
does not read reference clocks, memory states, lives, pictures or voice states.
Existing single-player post-retry guards remain intact.

Both controls are independently replayed twice, without observation hooks,
checking the complete prefix and complete extended memory fingerprints. The
observer then replays the same canonical setup/events unchanged. Hooks attach
before the terminal gameplay suffix; activation requires its exact previously
qualified endpoint. Prefix and extended fingerprints must remain unchanged.
Every component has strict source scope, exact shared endpoints, inherited
seed/input/counter/campaign checks and native comparisons without tolerances.

The source's absolute cycles and ticks are retained. Its complete raw input
sample index is recorded separately from diagnostic display indices: native
incoming-result ownership starts its own index at zero. The outgoing adapter
compares against the qualified terminal native display count. This is output
numbering only; there is no clock rebasing or reference-driven scheduling.
Disabled original voice presets are retained in the recording and compared as
inactive logical voices; active driver fields and music work are compared.

Reproduction: use `tools/selected_outcome_reference.py prepare ROM --capture
TERMINAL_CONTROL --out OUTCOME_CONTROL`, then `capture ROM --capture
OUTCOME_CONTROL --accepted-control TERMINAL_CONTROL --parent-out
TERMINAL_REFERENCE --out OUTCOME_REFERENCE`. The native full-chain diagnostic
uses `--players-initial-outcome --players-gameplay-updates N`, with that actual
terminal extent and the captured complete raw button stream. Other full-chain
arguments follow [selected terminal gameplay](SELECTED_TERMINAL.md).

Run `compare --capture OUTCOME_CONTROL --accepted-control TERMINAL_CONTROL
--parent-out TERMINAL_REFERENCE --out OUTCOME_REFERENCE --native-base NEW_BASE
--parent-base TERMINAL_BASE --parent-manifest TERMINAL_MAP_MANIFEST --startup
ORIGINAL_STARTUP`. The public comparator first requalifies the exact terminal
gameplay/map ancestor and all its parents; it then checks unchanged complete
native CSV ancestors and the six attached component streams. Original controls,
assets, reference binaries and recordings stay local.

This scope excludes the subsequent instruction transition/text and second
player's gameplay, other stunts/difficulties/outcomes, modified scores and name
entry, rendered-frame/PCM parity, production scheduler integration and final
Windows/device/distribution acceptance. The broader request and final version
remain incomplete. See [matrix](ORIGINAL_COMPARISON_SCOPE.md) and
[acceptance](ACCEPTANCE.md). No final release is claimed.
