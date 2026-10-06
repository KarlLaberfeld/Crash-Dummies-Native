# Interrupted Air placement ownership

October 6 completion follow-up: all 77 placement interrupt vectors now match
the independent original exactly, including identified access/conditional-return
completion. The two formerly rejected neighboring image edges are reconstructed.
See [absolute interrupt evidence and limits](AIR_IRQ_BOUNDARIES.md).

This is experimental native-clock work, not Windows scheduler integration.
The ordinary Windows wrapper retains its existing placement behavior.

## Original witness and correction

A control-verified SameBoy DMG-B recording on easy difficulty alternates
steering every 44 updates, offset 12. Its actual outcome is damage (`0x21`)
after **1,802** updates. The local directory retains its earlier intended
`win` label; this recording is not evidence of a successful finish.

At update 1,445, VBlank returns to **19bb**, inside pointer advancement after
the fourth range test. The HUD cursor was 12. The progress refresh at 2f4c
calls division at 16eb, which shares **FF9C** with placement's lower bound.
The division's bounded numerator/remainder leaves this overflow byte zero.
CPU register pushes preserve registers but do not preserve shared scratch.
FF9E, the upper bound, remains 100.

Independent 19ef/19f3 observations record four lower reads of **86**, followed
by four lower reads of **0** and upper reads of **100**. Three remaining entity
slots then fill and the fourth allocation fails. Source placement work is
**9,200** cycles; assuming an unchanged range incorrectly predicts **3,008**.
The difference is actual record/allocation work, not a scheduling allowance.

`air_placement_clock.h` implements this identified eight-record algorithm with
separate range reads, caller work, allocation and table wrapping. It runs no
CPU instructions. `air_clock_probe` defers placements until this phase, and its
native display callback derives the shared-scratch change from its own HUD
refresh. Original bounds, counters, costs and actor outcomes never drive it.
Source camera state supplies the retained upper-bound value even if a display
occurs between the two initial scratch stores.

The full witness now matches **1,802 player updates, 1,866 display services,
10,812 work phases/entry counters, 28,832 pre-update entity slots, 74,640 sprite
slots and 1,866 held/fresh input samples**. Final wait and all 74 audio-stop/
outgoing-fade intervals also match. The initial clock/timer/random phase is
supplied once; all sixteen entity slots are independently checked, including
the new allocations. These snapshots cover frame, visibility flags and
coordinates, not every internal actor field. Inactive slots ignore irrelevant
retained memory bytes.

## Reference-observer correction

The initial independent adapter observed opcode reads. SameBoy also reads PC
during interrupt entry without executing that instruction; this caused a
duplicate stage in another measurement. The official execution callback now
owns instruction observations. Its identity `execution-callback-v1` is checked
in the adapter manifest/DLL and recording provenance. Earlier observer records
are rejected when mixed with current recordings. The core remains unmodified.
New recordings preserve their own uninstrumented save-state/event controls.
Randomized power-on RAM means separate boots need not share an end-state hash.
See [reference setup](REFERENCE_BACKENDS.md).

## Validation and limits

All eleven earlier PyBoy clock cases still pass: **32,801** completed updates,
**32,909** services and **196,806** work phases. Three independent SameBoy
timeout/steering-damage replays match **7,655** updates, **7,791** services/input
samples, **45,930** work phases and **122,480** pre-update entity slots. Each
also matches its final wait, 74 exit intervals and 32 outgoing services. These
engine repetitions stay separate from the eleven earlier gameplay cases.

The rebuilt production EXE passes full native suites, all 64 Air recovery
phases, four difficulty successes and all three campaigns. Standalone source
checks pass **107** assertions and Python passes **103** tests. Normal Windows
UI and actual audio-open failure checks pass **13/14** checks on this host.

Native pause LCD polling, interrupted entity/resource/row ownership, normal
startup/result setup and production clock integration remain open. Sprite-slot
agreement is not pixel equivalence; software audio observations are not PCM
acceptance. Other stunts, human/device-removal/independent Windows checks and
final distribution still require [acceptance](ACCEPTANCE.md). No final release
is claimed. All original captures, states and data remain local.
