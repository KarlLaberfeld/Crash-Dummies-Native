# Native perfect Air celebration and incoming result timing

October 7, 2026. The diagnostic now reconstructs the running four-emitter
celebration and integrates its first 33 services into the complete perfect
incoming result. Perfect accounting/handoff and production Windows scheduling
remain open. This extends the existing genuine 14/14 control, not a second
independent perfect gameplay recording.

## Native component

`air_celebration.h` owns the identified emitter state and the complete 160-byte
prepared sprite list. Each service clears that list, decrements staggered
delays, resets expired emitters through the native shared RNG, or prepares ten
particles per active emitter. Drawing uses the extracted wave/product/tile
tables and byte arithmetic, including signed quadrants, rounded table lookup,
priority flag 128 and coordinate wrap. Velocity and radius updates use the
display counter before bookkeeping increments it.

The fixed source operations and native branches derive their own work:

| Operation | Cycles |
|---|---:|
| Complete list clear and four emitter dispatches | 1,508 |
| Delayed emitter | 144 |
| Expired emitter reset | 676 |
| Moving-emitter work outside drawing | 468 plus 12/20 velocity and 12/20 radius branches |
| Ten-particle drawing outside variable offset lookups | 4,168 |

Offset work depends on the native angle sign, radius sign and wave/magnitude
comparison. It charges the identified table and negation paths, not an observed
cost or fitted delay. No CPU instruction stream/register machine is executed.
The diagnostic inherits emitters/random state and the display counter from
its independently qualified native main gameplay and result prefix. Only the
comparison's extent bounds the isolated replay.

The control-verified reference covers **787 complete celebration services**
through the first next-instruction boundary. All emitter/random state, source
body work and **125,920 prepared bytes** agree. It includes 640 delayed,
26 reset and 2,482 moving emitter calls, 316 velocity increments and 1,946
radius increments, with all 40 sprites active in some services. Maximum
observed radius is 69: negative-radius branches have source/synthetic tests,
not an original witness in this control. The component comparison does not
qualify absolute result accounting or glyph readiness times.

## Perfect incoming result

`air_result_transition.h` selects the perfect portrait profile at 0568 and
music 5, retains the 720-service countdown and uses STAT selector 4's 288-cycle
object-disable callback. Layouts remain LCD-off. The pending VBlank/STAT pair,
LCD restart epoch, palette writes, counter waits and all source return/branch
boundaries retain their separately reconstructed owners. Each display prepares
the next celebration list while publishing the preceding one.

The complete incoming perfect result agrees at **81 absolute boundaries,
33 display services and all 66 IRQ vectors**, including native countdown,
counter wrap behavior, fresh inputs, music/effect work and palette state.
The 33 prepared lists and 33 published lists also agree byte-for-byte:
**5,280 bytes each**. Published targets are read at the original post-DMA
display entry during VBlank. The native transition returns both prepared and
visible lists for later owners. These 33 celebration services overlap the
787-component extent; do not count them as separate animation coverage.
Scalar/list parity does not establish complete rendered result images or PCM.

The result profile package is now TICDRT02, adding the perfect portrait's
structural profile. Legacy TICDRT01 still loads for ordinary results, while
perfect incoming requires the new profile and valid native initialization.
Both formats reject missing/trailing records. UI07 graphics/data remain
unchanged and local. Original ROM, extracted packages and captures are ignored.

## Reproduction and validation

```powershell
python tools/air_celebration_reference.py capture 'path/to/original.gb' --capture local/sameboy-air-perfect --out local/air-perfect-celebration-reference
local/air-clock-probe.exe local/sameboy-air-perfect/inputs.txt local/air-perfect-celebration-services.csv 0 --display-inputs local/air-perfect-buttons.txt --perfect-celebration 787
python tools/air_celebration_reference.py compare local/air-perfect-celebration-services.csv.celebration.csv --capture local/sameboy-air-perfect --out local/air-perfect-celebration-reference
python tools/air_result_transition_reference.py capture 'path/to/original.gb' --capture local/sameboy-air-perfect --out local/air-perfect-incoming-reference
local/air-clock-probe.exe local/sameboy-air-perfect/inputs.txt local/air-perfect-incoming-services.csv 0 --display-inputs local/air-perfect-buttons.txt --result-inputs local/air-perfect-incoming-reference/buttons.txt --result-incoming
python tools/air_result_transition_reference.py compare local/air-perfect-incoming-services.csv.incoming.csv --capture local/sameboy-air-perfect --out local/air-perfect-incoming-reference --startup local/air-perfect-startup
```

The original instrumentation preserves the uninstrumented 32,768-byte control
hash. Captures have explicit complete terminal boundaries and reject missing
services, state gaps, partial list tails and source/capture mismatches. Perfect
incoming schema 3 requires celebration/publication fields and its own selector;
legacy ordinary captures cannot qualify it.

Local evidence logs are `air-perfect-celebration-{capture,comparison,coverage}.log`,
`air-perfect-incoming-{capture,comparison,result-tests,python-tests}.log`,
`air-perfect-incoming-ordinary-regression.log` and
`air-perfect-incoming-handoff-regression.log`, all under ignored `local/`.
The O2 diagnostic and 18,668 ROM-free result assertions / 278 Python tests pass.
All baseline ordinary incoming/accounting/full-failure comparisons and the
ordinary successful handoff remain exact. The production EXE/scheduler is
unchanged; unchanged full campaigns are not repeated for this diagnostic work.

The perfect accounting and handoff are now also qualified: 747 and seven
additional services, all emitter/work/prepared/published fields, source IRQ
times, LCD polls and intended writes agree. They complete the same 787-service
result extent; the counts overlap this component recording. See
[accounting](AIR_RESULT_ACCOUNTING.md) and [handoff](AIR_RESULT_HANDOFF.md).
Latest checks: 18,680 result, 580 pause/session/pixel assertions and 295 Python
tests; ordinary result/handoff and three coupled pause controls pass.

Next: final-life/reset results, later instruction/setup and other
pending owners remain required. Point 1 and [final acceptance](ACCEPTANCE.md)
are not complete.
