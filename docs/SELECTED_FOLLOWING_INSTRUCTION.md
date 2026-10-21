# Selected post-result instruction transition, text and exit

This extends the actual [initial selected outcome](SELECTED_OUTCOME.md), rather
than constructing a new campaign. Each of eight one/two-player, full/skip
initial Air/easy attempts in the two retained histories receives both complete
next-instruction text with a fresh Start confirmation and deliberate late skip
with Start held through the outgoing fade. The scope ends at 0355, before the
following stunt setup/gameplay.

October 21, 2026: all eighteen cases match, zero differences. Totals are 37,298
boundaries, 15,896 displays, 31,810 vectors, 67,180 readiness reads, 1,614 glyph
stores, 30,328 palette/raster/scroll stores, 55,296 background bytes, 55,296
picture tile bytes and 95,376 logical voice rows. Counts overlap their shared
ancestors. Every case retains 533 ordinary-history or 537 earlier-pause complete
native CSV ancestors. Fresh optimized replays additionally preserve all 560/564
complete case CSVs byte for byte.

Validation: 1,936 Python tests, 94 native continuation assertions and the full
native Windows game/campaign/playthrough/audio/sprite regression pass. Normal
builds run the new native tests. The clean Windows EXE is rebuilt from the saved
source revision. Production implementation and final-release status are
unchanged; the broader task remains incomplete.

Two additional second-player controls explicitly cover a fresh Start arriving
during a scroll wait: it does not skip the text, then held Start bypasses the
prompt when the full text finishes. These are separate from the deliberate skip
controls. An earlier attempt to treat that input as a skip was correctly rejected
as incomplete, with unchanged observed/unobserved fingerprints; the rejected
recording is retained locally and is not counted as accepted evidence.

The native continuation retains its actual next live player: player one with
four lives in a one-player campaign, or player two with five lives in a two-player
campaign. The original and native text interpreters select that player's name.
Neither reference state nor an original clock initializes native execution.

The original comparison covers the line-144 readiness wait, object disable and
callback/LYC replacement including the immediate STAT-write request; all 64
map-selection waits/stores; timed glyphs, name substitution, scrolling and
full/late-skip completion; fresh Start prompt or held-Start bypass; all eight
palette steps and 32 fade waits; the final white-screen wait and audio stop.
Exact semantic boundaries, vector ownership, display/input/music work, glyph
polls/stores, palette/raster writes, six logical voices, native background bytes
and picture tile bytes are compared. No timing tolerance is used.

The first pilot rejected an assumption that the result presentation had cleared
the earlier instruction's scroll. The original retains that scroll until the
identified map-transition clear. Native state already retained it; the new
diagnostic forwards that actual native value to the existing map owner instead
of supplying zero. Existing outcome CSV ancestors remain byte-identical: their
unused generic `scroll` summary column was not a qualified source comparison
field. The new map boundaries explicitly compare the inherited value and its
actual clear. No production timing correction or reference-driven assignment
was introduced.

Each child appends input events to its own exact outcome control, with two
independent unobserved prefix/full fingerprints and identical setup/backend/ROM.
The accepted outcome control's final 800-frame interval already overlaps the
next instruction. The full path appends 1,200 idle frames and a fresh Start;
the deliberate skip path waits 16 further frames before pressing Start, rather
than claiming a skip at text entry. The separate `scroll-held` controls press
Start immediately and hold it for 1,200 frames, requiring the original fresh
edge inside the identified scroll wait, no text skip and a held-Start exit.
Observation still begins at the precise attached
268b endpoint inside the unchanged canonical replay. The prefix and complete
fingerprints must match with hooks installed.

Original direct storage records retain both 1,024-byte maps, all 1,024 picture
tile bytes and 256 prepared-object bytes before/after each component. Actual
glyph writes explain every background change; window/tile/object continuity
is checked in the source. Native storage comparison covers the owned first
1,024-byte background and 1,024 picture tile bytes at each component endpoint.
It does not claim native window-map parity or final rendered-frame parity.
Raw disabled original voice presets remain recorded; logical inactive voices
and active native driver fields are compared separately from final PCM.

Prepare `tools/selected_following_instruction_reference.py prepare ROM
--capture OUTCOME_CONTROL --out TEXT_CONTROLS`. This creates `full-prompt` and
`skip-held` controls. Use `--case scroll-held` for the two second-player cases
with the actual ignored-scroll edge. Capture each with `capture ROM --capture TEXT_CONTROL
--accepted-control OUTCOME_CONTROL --parent-out OUTCOME_REFERENCE --out
TEXT_REFERENCE`. The complete native diagnostic uses
`--players-following-instruction --players-gameplay-updates N`, retaining its
actual initial terminal extent and complete source-observed raw button stream.
Other full-chain options follow [selected terminal gameplay](SELECTED_TERMINAL.md).

Compare with `compare --capture TEXT_CONTROL --accepted-control OUTCOME_CONTROL
--parent-out OUTCOME_REFERENCE --out TEXT_REFERENCE --native-base NEW_BASE
--parent-base OUTCOME_BASE --parent-manifest OUTCOME_MANIFEST
--terminal-manifest TERMINAL_MAP_MANIFEST --startup ORIGINAL_STARTUP`.
The public entry point first qualifies the exact outcome and terminal/map graph,
then compares all complete native ancestor CSVs byte for byte and the attached
instruction components. Local batches may reuse already-qualified unchanged
parent graphs; exact control/setup/file identities and native prefixes remain
mandatory. Original assets, controls, recordings and reference binaries stay
local.

Further acceptance remains open for the actual subsequent player's game entry
and gameplay, other stunts/difficulties/outcomes, additional retained menu paths,
changed scores/name entry, rendered frames/PCM, production scheduler integration
and final Windows/device/distribution checks. This is not a final release or
completion of the entire original-comparison request. See
[matrix](ORIGINAL_COMPARISON_SCOPE.md) and [acceptance](ACCEPTANCE.md).
