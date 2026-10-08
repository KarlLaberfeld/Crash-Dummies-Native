# Following Air gameplay handoff

The bounded native diagnostic now continues the easy Air retry through its
complete first update and the next wait/input gate. The existing original
retry control matches ten boundaries, 160 actor slots (20 occupied instances),
one display and two complete counter-wait vectors, with zero differences.
The first 03d8 boundary repeats the preceding entry endpoint; this is an
extension of that control, not another independent gameplay case.

## Inheritance and work

`airFollowingAirHandoff` constructs the next Air stage from decoded native
assets. The prior native Air game supplies the partial second, sprite allocation
direction and all sixteen semantic animation blocks. The source clears the
actor buffer but retains animation cursors, delay, period and loop fields.
Only the two newly allocated actors reset their done/waiting flags.
The following entry supplies the new scene seed, counter, HUD cursor, fade
phase and raw input history. Fresh edges are preserved; held buttons cannot
manufacture a new edge. No reference state or observed duration drives this.

`airFollowingAirFirstUpdate` owns the saved-player prefix, actor and resource
work, sprite preparation/clear, map preparation and eight-record placement
scan. Existing native scene and placement completion algorithms are reused.
The actor/resource body requires a quiet interval; an unknown interrupted
body rejects. The subsequent counter wait uses the inherited new LCD epoch
and deadlines, preserving STAT/VBlank order and source input/audio work.

In the observed retry the first body has 18,900 cycles. Its map destination
changes from the retained startup row (440) to the newly prepared row (432).
The partial second remains 35, the fresh level duration is 40 seconds and the
first update retains the seed derived by entry. The following display advances
the global counter from 4,852 to 4,853, HUD cursor from two to three and fade
from seven to six. These are comparison results, not native inputs.

## Verification

`air_following_gameplay_reference.py capture` replays the full input-only
control in the separately authorized pinned SameBoy reference. Its terminal
32,768-byte memory hash agrees with the original unhooked control. It records
the first update through the next 03d8 and exports the single additional raw
display-button sample, with all preceding samples. No original RAM is changed.

The optimized probe's `--following-gameplay` includes the full preceding
result/instruction/startup chain and accepts that button file. The separate
`compare` command loads no emulator and requires full coverage, matching
control/backend identities, explicit attachment to entry, continuing display
indices, complete vectors and the inherited deadlines. It compares live actor
frame/flags/handler/coordinates, done/waiting/delay/period and seven parameters.
Every vacant slot's sentinel and allocation state is compared. Raw script
pointers and unused vacant payloads are excluded explicitly.

Validation: 647 ROM-free native handoff assertions and 414 Python tests.
Twenty new comparison integrity tests detect lost inherited timer/animation
state, missing/reordered actors/phases/vectors, unknown IRQ owners, busy-body
crossings, reset/pause inputs, detached scene seeds/deadlines and terminal
counter changes. The four complete preceding startup controls and their
instruction exits remain exact on the rebuilt optimized diagnostic.
An initial synthetic fixture lacked a nonzero quota; its divide-by-zero was
fixed in the fixture before the complete native handoff suite passed.

Local evidence: `local/air-following-retry-first-reference/`,
`local/air-following-retry-first-services.csv.following-gameplay.*`,
`local/air-following-first-comparison.log`, `local/air-first-handoff-tests.log`,
`local/air-first-python-tests.log` and `local/air-following-first-prior-regressions.log`.
Original data and recordings remain local and ignored.

## Remaining scope

This qualifies one easy Air retry's first update and wait. Later gameplay,
Ski handoff, changed-player/global animation-pool ownership, entry pause,
genuine final-life/reset and earlier UI/LCD startup still need their owners
and original controls. Full prepared/published map and sprite bytes, startup
images/PCM, unobserved interrupted work and production Windows scheduling are
not certified here. The production EXE is unchanged. Timing point 1 and final
release acceptance remain incomplete; the continuation automation stays active.
