# Source-owned Air result handoff

## Perfect handoff extension, October 7

The genuine 14/14 control now also matches the full native 0514..02ce handoff:
**11 boundaries, seven display services, 14 vectors, 3,670 LCD polls and all
1,024 intended blank writes**, with zero differences. The continuing emitter/
RNG/work state and 1,120 prepared plus 1,120 published bytes also agree.
Together with incoming/accounting, the same native control has 787 result
services. These are the same services as the isolated celebration recording;
do not add the two counts. Its native ledger reaches 576 cents before this
interval, selects the living first player and clears the result at its actual
store boundary.

The owner keeps publishing the preceding prepared list. Once result bit four
is cleared, it omits emitter advancement and charges the shorter 68-cycle
selector branch; synthetic integrity tests check this distinction. Display
readiness follows the published eight-pixel geometry. An overlapping line-120
disable can grant late horizontal blank only beyond a conservative uninterrupted
fetch bound; earlier ambiguous samples still reject. See
[the bound and accounting evidence](AIR_RESULT_ACCOUNTING.md).

Local evidence: `local/air-perfect-handoff-reference/`,
`local/air-perfect-handoff-services.csv.handoff*`,
`local/air-perfect-complete-{result,incoming,account,handoff}-comparison.log`.
The full replay passes all four original comparisons without a truncated common
prefix. Current checks: 18,680 result, 580 pause/session/pixel assertions and
295 Python tests. Baseline ordinary result/handoff and all three coupled pause
controls still pass. The production EXE/scheduler is unchanged.

The following header, instruction waits and next gameplay entry are separate
owners. Final-life/reset, complete result pixels/PCM, unobserved interruptions
and production integration remain open. Timing point 1 is not complete.

## Earlier ordinary-result checkpoint

The native diagnostic now continues from the completed ordinary success/failure
result at 0514 through live-player selection and the complete LCD-safe background
clear, ending explicitly at 02ce before the next instruction/header text.
The campaign supplies its own player/lives; no original campaign fields, clocks,
readiness modes or writes drive execution. The standalone probe uses the native
initial solo campaign's five lives and consumes one for an ordinary failure.

All four independently controlled originals match every absolute boundary,
display/STAT vector, held/fresh input, selected player/life/result field,
readiness poll and intended blank glyph write:

| Existing gameplay control | Boundaries | Displays | Vectors | LCD polls | Intended writes |
|---|---:|---:|---:|---:|---:|
| Genuine ordinary success | 11 | 3 | 6 | 3,568 | 1,024 |
| Damage | 11 | 3 | 6 | 3,556 | 1,024 |
| Timeout | 11 | 3 | 6 | 3,556 | 1,024 |
| Alternating-steering damage (`win` directory) | 11 | 3 | 6 | 3,556 | 1,024 |
| Total | 44 | 12 | 24 | 14,236 | 4,096 |

These extend existing controls, not four new gameplay patterns. Each original
uses ordinary buttons, matches its uninstrumented 32,768-byte terminal hash,
and has a separately qualified nine-point startup epoch. Missing terminal,
selection, access or interrupt coverage rejects; common-prefix acceptance is
forbidden. The original selected player is a comparison target.

0514 tests both life records, flips player at its actual store completion and
checks that player's lives. A solo campaign skips the eliminated second player,
then selects the first player on its second pass. The identified background
clear polls LCD readiness separately before all 1,024 ascending blank writes.
The guarded result countdown retains one during successful handoff; failure
handoff continues from 86 to 83. Music remains disabled.

The damage control exposed the inclusive VBlank mode sample at the steady
frame's first visible line. Its exact boundary retains mode one; the following
short blank returns mode zero before scan begins. The native owner now keeps
that distinction. Both modes permit the same accesses, so this corrects status
readback without changing gameplay/branch timing. Three coupled pause/graphics/
audio controls and prior successful/incoming/failure comparisons still pass.

Local evidence: `local/air-success-handoff-reference/` and matching `-native/`,
plus `local/air-failure-handoff-{damage,timeout,win}-{reference,native}/`.
Logs: `local/air-success-handoff-comparison.log`,
`local/air-failure-handoff-comparisons.log`,
`local/air-handoff-result-regression.log`,
`local/air-handoff-accounting-regression.log` and
`local/air-handoff-pause-regression-{coast,easy,hard}.log`.
Native source-shaped tests check direct switching, skipping, life preservation,
timer/counter wrapping, all map accesses and rejection when both players are
eliminated; two-live-player switching is synthetic evidence only. Current
validation: 18,437 result assertions, 574 pause/session/pixel assertions and
242 Python tests. The optimized native diagnostic and Windows production EXE
remain separate; the production scheduler is unchanged.

Reproduce the original recording with:

```text
python tools/air_handoff_reference.py capture <local.gb> --capture local/sameboy-air-success-accounting --out local/air-success-handoff-reference
local/air-clock-probe.exe local/sameboy-air-success-accounting/inputs.txt local/air-success-handoff-native/services.csv 0 --display-inputs local/air-success-finish-native/buttons.txt --result-handoff --result-inputs local/air-success-handoff-reference/buttons.txt
python tools/air_handoff_reference.py compare local/air-success-handoff-native/services.csv.handoff.csv --capture local/sameboy-air-success-accounting --out local/air-success-handoff-reference --startup local/air-success-accounting-startup
```

The Windows runtime requires no reference emulator. All recordings, ROM and
extracted data remain ignored/local. This bounded checkpoint does not certify
the following day/stunt labels, instruction waits, subsequent LCD/gameplay
setup, all-player elimination/title return, final-life/reset results,
complete result pixels, PCM, physical hardware or Windows scheduling. Timing
point 1 and the full release checklist remain open.

A newly found perfect original control legitimately collects 14/14, including
the crash-only object. Its 2,477 updates, 2,516 displays, 14,862 phases, 39,632
pre-update entity slots, inputs/final wait and all 5,032 IRQ vectors match through
0409. Its perfect result is now qualified through the handoff above.
See `local/sameboy-air-perfect/` and
`local/air-perfect-{main,all-irq}-comparison.log` for the bounded main-game proof.
