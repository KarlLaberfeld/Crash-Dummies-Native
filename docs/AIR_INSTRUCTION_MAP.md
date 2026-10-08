# Subsequent instruction map transition

The native diagnostic now owns 268b through the following timed-text entry
(0a0a for an Air retry, 0c7a for the following Ski instruction). It polls native
LY until the source's equality test retains 144, disables objects, clears the
scroll value, changes both callbacks to selector five and writes LYC 95. The
short callback critical section rejects an unobserved pending crossing.

The following STAT write has a separate request boundary. Pinned SameBoy's
DMG write conflict temporarily asserts all STAT sources for one cycle
(`Core/sm83_cpu.c`, `GB_CONFLICT_STAT_DMG`). The preceding LY read can retain
144 across a music/display service; the STAT write itself can occur during
horizontal blank in the following frame. Native steady-LCD readiness verifies
horizontal/vertical blank and the request is accepted at the write completion.
This is a bounded source event, not a CPU or general STAT emulator. Other modes
reject. The periodic compare request continues independently at line 95.

The new display callback costs 144 source cycles and no longer decrements the
result countdown. The STAT callback restores the instruction's scroll value;
it does not disable objects again. Each of the 64 map selections owns one
counter wait and the completed LCDC write. The native code consumes the eight
locally extracted UI pattern bytes least-significant bit first. No observed
duration, readiness result, interrupt vector or map-selection byte is an input
to the native clock.

Five existing, independently control-verified originals agree at all 1,335
absolute boundaries, 330 displays, 665 complete vectors and 17,556 LY reads.
All 320 map selections and input/audio work agree. The genuine 14/14 path has
267 / 66 / 133 / 3,491; ordinary success has 267 / 66 / 133 / 3,538;
damage, normal timeout and the historically named `win` damage control each
have 267 / 66 / 133 / 3,509. These extend the same five preceding instruction
controls, not five new independent gameplay paths. Complete 32,768-byte
uninstrumented terminal hashes and qualified startup epochs remain checked.

Local evidence is in `local/air-perfect-map-*` and
`local/air-map-{success,damage,timeout,win}-*`. Reproduce a read-only recording
with `tools/air_instruction_map_reference.py capture`, then replay the complete
native result with `--instruction-map`, its ordinary display inputs and the
recording's complete result buttons. Compare the generated
`.instruction-map.csv` using that tool's `compare` mode and the matching startup
recording. Missing steps, truncated services, changed controls, callback/IRQ
ownership, running countdowns and reset chords reject; comparisons never
truncate to a common prefix.

Validation: optimized diagnostic, 35,070 ROM-free native result assertions and
12 new Python integrity checks. Synthetic tests independently check all 64
pattern-bit selections, preserved unrelated LCDC bits, the frozen countdown,
144-cycle callback and the single STAT-write request. They are not original
witnesses. ROM, extracted data and all original recordings remain local.

Timed text, text skipping/scrolling, input wait and exit fade, the following
LCD/gameplay entry, initial instruction, final-life/reset results, earlier UI,
unobserved owners and production Windows scheduling remain open. This does not
certify physical hardware, complete pixels or PCM. The production EXE is
unchanged, timing point 1 is incomplete, and there is no final release.
