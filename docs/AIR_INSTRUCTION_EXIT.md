# Following instruction exit through 0355

The native diagnostic owns the held-Start test at 032b, optional twenty-glyph
prompt and fresh-Start wait, all eight palette segments with 32 counter waits,
one final counter wait and the quiet sound reset. The explicit terminal is
0355, before DI and the following LCD/gameplay setup. Every display retains
the instruction callback, frozen countdown, text scroll and native audio/input.

Four independently control-verified originals match 414 semantic boundaries,
166 displays, 332 complete vectors, 200 readiness polls and 40 intended writes,
zero differences. Name and quota skip controls arrive with Start already held;
each owns 85 boundaries, 33 services and 66 vectors with no prompt writes.
An ordinary success and an Air failure retry display the prompt and wait for
fresh Start; each owns 122 / 50 / 100 / 100 / 20. Their input-only controls wait
17 services before that edge. Native synthetic input waits use different
durations; no measured duration or service count enters the clock.

Each native palette write has its source access boundary; the entire fade
continues sound and input. The sound reset owns 12,384 source cycles only when
it does not cross a periodic request. An interrupted reset rejects rather than
borrowing a whole-operation allowance. The prompt inherits the native text
cursor, including its 32-column pitch. Held Start bypasses the prompt; the
prompt's wait requires a fresh edge, and completion then performs the same
32-plus-one waits in both paths.

Recordings and controls remain local under `local/air-text-{name,quota}-exit-*`,
`local/air-instruction-{prompt,retry-prompt}-*` and matching SameBoy folders.
Reproduce with `tools/air_instruction_exit_reference.py capture`, the native
`--instruction-exit` replay with matching ordinary/result buttons, then its
`compare` mode with the independently qualified startup recording. Complete
terminal hashes, phase lengths, wait ownership, all intended accesses, service
input/audio work and absolute vectors are checked without common-prefix
truncation. These four paths extend previous gameplay; they are not four new
independent stunt outcomes.

Validation: optimized diagnostic, 36,048 ROM-free native result assertions and
357 Python tests. Synthetic tests separately verify the prompt cursor, held
versus fresh Start, eight palette values, 32 fade waits, the extra wait and
sound reset; integrity tests reject truncated phases, missing services,
unowned callbacks/IRQ ownership and incomplete resets.

This qualifies scalar source timing and intended writes, not complete pictures,
PCM, physical bus/hardware or the production Windows scheduler. Next LCD-off,
resources and following gameplay startup are still separate. Initial UI,
final-life/reset, unobserved owners and production integration keep timing
point 1 incomplete. ROM, assets and original recordings remain local. The
production EXE is unchanged; no final release is accepted.
