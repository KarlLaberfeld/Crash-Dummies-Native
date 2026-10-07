# Bounded Air interrupt completion and pause vectors

October 7 extension: [scene completion](AIR_SCENE_COMPLETION.md) corrects 23
additional sprite/map vectors. All 36,548 vectors in seven complete controls
now agree, including a genuinely successful ordinary finish. Coverage checks
require explicit terminal boundaries, not a matching common prefix. The
diagnostic builds at O2 again; the older O0 limitation below is superseded.
The [common result prefix](AIR_RESULT_PREFIX.md) is separately qualified.

October 6, 2026: this extends the native diagnostic clock. It is not production
Windows scheduling, a CPU interpreter or final timing acceptance.

## Placement completion

An aggregate routine budget can produce the right total work while accepting
an interrupt before the interrupted source operation has finished. A later
counter wait can hide that difference. The identified eight-record placement
scan now charges the completion boundaries of its range loads, conditional
returns, pointer advancement, bounded pool search and definition copies.
Costs come from the identified source routines, not captured return addresses.
Native placement records, range scratch and entity allocation still select the
actual branches. No CPU registers, opcode decoding or execution are introduced.

`AirClock::atomicWork` completes an identified operation before dispatching a
pending service. The optional interrupt observer labels source boundaries,
counter waits, pending startup and unqualified aggregate work separately. The
placement path uses only identified 4..24-cycle operations. Unknown definition
lookups reject. Existing native total-work and allocation tests still pass.

`air_irq_compare.py` compares every original interrupt inside the placement
interval with native phase 5, including its absolute vector cycle, kind and
update. The epoch follows the already independently qualified pending startup
vector at +52; it is not fitted to later events. Incomplete returns, missing
events, shifted vectors and aggregate owners reject.

| Existing control | Placement STAT | Placement VBlank | Total |
|---|---:|---:|---:|
| Easy steering damage, period 52 | 18 | 2 | 20 |
| Easy steering damage, period 44 / offset 12 | 33 | 24 | 57 |
| Three pause controls and normal timeout | 0 | 0 | 0 |

All **77** vectors agree exactly on the pinned SameBoy DMG-B reference. The
four zero-edge cases are regressions, not placement interrupt witnesses.
The period-44 capture retains its historical `win` directory suffix but ends
in damage. It is not a successful-finish control. Full world, service, phase,
entity, input and final-wait comparisons for the three outgoing controls pass
again. These extend existing scenarios; do not add their gameplay counts twice.

## Neighboring full images

Original services 1498 and 1499 interrupt the high-range read and a taken
conditional return. Their source-completed native object-disable edge is at
line-135 dot **270**, rather than the aggregate deadline's dot 262. Five
consecutive original images, services 1498..1502, now agree with native
publications 1497..1501. The latter three edges use the counter-wait owner at
dot 262. No captured edge or pixel enters native execution.

One image overlaps the earlier 258-image selection. The union is **262 complete
images / 6,036,480 pixels**, with zero differences and no masked regions. Blank
and frozen repetitions are included. This is not 262 independent situations.
Unqualified aggregate edges retain the conservative pixel-insensitivity guard;
sensitive unknown paths still reject. See [pixel ownership](AIR_PIXELS.md).

## Pause handoff and absolute wait vectors

The identified entry section retains services for 192 source cycles, followed
by the 12-cycle copy-source setup after enable. Restoration retains services
for 140 cycles, followed by its 16-cycle return. A native service gate now
models these two fixed handoffs. If both services were pending, VBlank has
priority over STAT; callbacks see the restored selector/audio state only after
the follower has completed. Ordinary work cannot bypass the closed gate.

Synthetic tests check deferred callbacks, exact work, service priority, invalid
followers and session rejection before side effects when a request lands in
the enable follower. **No existing control has an interrupt crossing either
protected section.** The diagnostic probe therefore explicitly rejects a
pending protected resume until an independent original crossing is qualified.
The source model is a candidate, not accepted evidence for that unobserved path.

The three complete pause replays still independently match gameplay, input,
graphics, selected voice/work fields, effects and startup boundaries. In
addition, `air_pause_irq_compare.py` checks absolute vector times against the
qualified startup epoch and requires the native counter-wait owner. Its native
pause bounds must match the original absolute copy/return bounds. Missing,
shifted or non-wait/protected interrupts reject.

| Existing pause control | STAT | VBlank | Matched vectors |
|---|---:|---:|---:|
| Normal coast, hold 31 | 35 | 35 | 70 |
| Easy coast, hold 120 | 124 | 124 | 248 |
| Hardest boost, hold 255 | 259 | 259 | 518 |
| Total | 418 | 418 | **836** |

These are additional timing checks of the same 418 paused display services,
not new scenarios or display coverage. All original returns are the identified
counter-wait boundary 261d. They do not qualify interrupted graphics copying.

## Reproduction and validation limits

Build the diagnostic probe as described in AIR_PAUSE_CANDIDATE.md. Add
`--interrupts-csv local/your-native-run/interrupts.csv` to the existing native
replay. Measurements remain local and compare never imports an emulator.

```powershell
python tools/air_irq_compare.py local/air-irq-outro-win-native/interrupts.csv --capture local/sameboy-air-outro-win --timing local/sameboy-air-outro-steer44-timing
python tools/air_pause_irq_compare.py local/air-irq-pause-coast-native/interrupts.csv --capture local/sameboy-air-pause-coast --timing local/sameboy-air-pause-coast-timing --startup local/pause-coupled-coast-startup-reference --phases-csv local/air-irq-pause-coast-native/services.csv.pause.phases.csv
```

Repeat the second command with matching easy/hard paths. All provenance,
ROM/control digests and the qualified reference convention must agree.

Latest tests pass **113 source-work assertions, 573 pause/session/pixel
assertions and 133 Python tests**. The optimized diagnostic rebuild and a
combined comparison initially failed because Windows commit was exhausted.
The diagnostic objects were successfully rebuilt serially at O0 with runtime
sanitizers disabled, then linked against the cached O2 runtime. Coupled
comparison now decodes recordings sequentially, reusing one music decode,
while retaining every provenance and coverage check. All six full original
comparisons, 77 placement vectors, 836 pause vectors, 262 unique complete images
and the 222 outgoing phases / 96 services pass with the current diagnostic.
Earlier 30 byte-identical regression logs also agree with the validated baseline.
This does not claim a successful optimized rebuild of this diagnostic revision.

The production EXE and its prior full native/campaign/13-14 Windows UI tests
are unchanged: none of these diagnostic clock headers is used by its scheduler.
No unchanged Windows suite was repeated. Initial LCD-enable access, other
interrupted entity/resource/map owners, arbitrary interrupt acceptance, result
setup, other stunts and production integration remain open. Full PCM and human,
physical-device and independent Windows/hardware tests remain required by
[final acceptance](ACCEPTANCE.md). No final package or release is made.
