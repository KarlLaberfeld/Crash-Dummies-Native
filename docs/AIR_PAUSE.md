# Air pause and display-sampled input

This checkpoint uses the hash-pinned US/EU cartridge and the separately
authorized local PyBoy 2.7.0 reference. The native Windows executable contains
no CPU emulator. ROM, inputs, state, captures and measurements remain ignored
and local. Control replays use the original UI and button events, without
gameplay memory writes; each instrumented replay matches the complete 32,768
bytes of its uninstrumented end state.

## Original pause behavior

Three captures pause after completed Air updates 300, 500 and 100, on normal,
easy and hardest difficulty respectively. Requested holds of 31, 120 and 255
frames yield 35, 124 and 259 paused services after the recorded press/release
events. The hard boost run terminates before update 1,000; an initial attempt
with that pause point was rejected as pause evidence and was replaced by the
early pause. Outcomes are timeout or damage, not successful paused finishes.

1476 saves audio routing/master, the display selector and driver enable. It
selects callback 1, disables the driver and powers off the channels. Air's STAT
selector remains 4. The pause copies/restores the bottom status row and its
font, waits for a fresh Start press, restores audio/selector state, then returns
to the pending update without another gameplay callback. Entities, camera,
timer, animation and RNG remain unchanged across 415 adjacent paused services.
C00A still advances once per VBlank; input is still sampled by 23e3.

The source-derived work agrees in all three captures:

- Entry critical section: 192 oscillator cycles; audio restoration: 140;
  final return: 16.
- Four 2359 copy bodies per pause: `196 + 104 * bytes + 32 * failed_polls +
  4 * destination_wraps`, for 20, 128, 20 and 128 bytes. Caller/setup work for
  each pair is 128. A failed poll is counted from the BIT instruction's Z flag;
  rereading STAT at the branch misses LCD-mode transitions.
- The fixed pause layout script: `4396 + 32 * failed_polls` cycles. This is the
  identified window-layer/position/20-column rectangle/end language, not CPU
  interpretation.
- Selector-4 STAT body: 288. Paused VBlank components retain DMA, input,
  bookkeeping and effect setup; display callback work is 160 and the disabled
  music call is 60. No paused pending-effect request occurs in these captures.
- 418 outer waits: source active work is 120 plus 36 per STAT wake. Remaining
  HALT idle is measured elapsed time, not an execution allowance.

`tools/air_reference.py` records the pause scenario. `air_pause_timing.py`
captures and reports its bounded source work, rejecting missing copies,
unmodeled requests, changed gameplay and counter discontinuity.

## Native corrections and music evidence

All five native stunts retain their prepared gameplay callback during pause,
continue the wrapping display counter and sample controls. The game timer and
entities remain frozen; held controls do not become a new edge on resume.
Direct standalone counter-wrap/input tests and campaign pause tests pass.

Audio output remains silent and software streams stay frozen. Effect setup
precedes the disabled driver in the original; pending requests now initialize
their roots during pause and sequence only after resuming. The pending-request
case is established from source and synthetic regressions, not an original
dynamic witness. Existing output power-off/wave-DAC behavior is retained.

Three isolated native song/effect/pause-request replays match 6,922 complete
original services and 41,532 selected voice-state/work rows, including 418
disabled calls. Disabled calls require six post-state snapshots; missing
snapshots cannot certify agreement. Two recordings stop inside one further
service. Its boundaries are stored separately and excluded, with the report
marked incomplete. No original voice state or measured cost drives the replay.
This does not establish gameplay-wide effect timing or PCM equality.

## Per-display buttons in the experimental clock

`air_clock_probe` accepts `--display-inputs buttons.txt`. Every display service
samples held buttons and derives its own fresh edges, even when the previous
game update is still in progress. The existing input file supplies initial
clock/timer/RNG phase and comparison scope; its per-update counter/button rows
are ignored in this mode. No outcomes, measured work or original edges enter
the native calculation. Start requests are explicitly rejected because this
clock's pause entry/copy/return ownership is not yet accepted.

All nine existing Air cases still match 28,103 completed updates, 28,153
services, all 168,618 semantic work phases/entry counters and the two sprite
comparisons (158,840 published slots). Independent single-2436-hook captures
also verify 3,971 held/fresh samples across steering and the successful finish.
`air_input_reference.py` records those comparison targets; `air_clock_compare`
requires complete sample coverage and the same ROM/control hash. Native fresh
edges are never replaced with captured edges.

## Acceptance limits

The ordinary Windows loop still performs one game update per display interval.
These corrections and probes do not complete scheduler integration. Native
pause timing needs independent LCD-poll/graphics ownership, startup and exit
paths; other interrupted Air phases/handlers remain unsupported. Measured
poll counts and idle times must not be inserted into the native clock as
allowances. Physical button microtiming, matched pixels/PCM, other stunts,
human play, physical audio-device removal and a separate Windows host remain
open under ACCEPTANCE.md. No final-release label is justified.

## Independent original reference - 2026-10-05

The locally installed PyBoy reference uses a fixed LCD pixel-transfer duration,
which cannot establish original pause polling behavior. An independent official
SameBoy 1.0.3 reference (pinned source, open boot ROM, DMG-B model) is now set up
under ignored .tools/. It is used only for authorized original measurements;
no reference core, DLL, boot ROM or recording enters the port or preview.
See REFERENCE_BACKENDS.md for the hardware-source link and reproducible setup.

The first control-verified SameBoy normal-coast case independently matches
3,989 native ordinary-clock updates, 3,990 complete services, 23,934 source
phases/entry counters, 159,600 sprite slots and 3,990 held/fresh samples. This
repeats an existing scenario on another engine; the eleven earlier PyBoy cases
remain separately counted. All measurement runs preserve the uninstrumented
end-state control. A SameBoy pause recording validates four copies, 35 paused
services/waits and 34 frozen-world intervals. Its LCD poll counts are observed
comparison data, never native clock inputs; independent native polling work
remains required.

Backend, revision/model and independent recording provenance are now explicit;
mixed records are rejected. The separate reference adapter exposes read-only
observations and button inputs with unmodified save/load states. The official
source revision and library/boot identity are checked. Latest pure Python tests
pass 98 checks. Native code/build/three campaigns and both Windows/portable UI
variants remain unchanged from the fully tested outgoing-fade checkpoint, so
those suites were not repeated. The overall port is still incomplete.
