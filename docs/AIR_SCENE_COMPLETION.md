# Air scene completion and complete IRQ coverage

October 7, 2026. This is native diagnostic evidence, not Windows scheduling
or a final timing claim. No CPU interpreter is part of the port.

## Corrected completion ownership

Comparing every original vector exposed 23 previously hidden differences in
the two steering outgoing controls: sprite preparation and map preparation
accepted STAT/VBlank 4..16 oscillator cycles early. The subsequent counter
wait concealed these differences in the earlier whole-update comparisons.

`air_scene_clock.h` reconstructs the identified camera-relative geometry,
frame lookup, signed/unsigned coordinate helpers, clipping, piece publication,
entity returns, unused-sprite clearing and sixteen-cell map preparation.
Native entities, layouts, camera values and allocation direction select the
branches. Source completion costs own each service boundary. Neither recorded
return addresses nor per-event correction tables select native behavior.
Piece Y, X, colors and flags publish separately; a pending service observes
completed writes and retains the not-yet-written fields. Resource queue
acknowledgement/replacement and result-test/counter-wait prefixes also have
identified completion boundaries. An interrupted resource/entity display
still rejects because partial state publication is not qualified.

All 23 differences are corrected. The existing six controls match **31,436**
complete vectors. `air_all_irq_compare.py` also requires the independently
observed terminal boundary and exact coverage; a common-prefix comparison is
forbidden. Each pause control excludes exactly one original interrupt after
the native result-test boundary, explicitly, rather than hiding an event.
The outgoing controls compare through `0409`, before result setup starts.

## A genuinely successful control

A new easy-difficulty SameBoy control uses alternating steering, period 120,
offset 56, and ordinary button inputs through the original UI. It collects
eight of fourteen targets and ends with source result `03`: successful,
without the perfect-result celebration. Instrumented and uninstrumented
32,768-byte end states agree. No gameplay memory writes are used.

It matches **2,510 updates, 2,556 display/input services, 102,240 sprite slots,
15,060 work phases, 40,160 pre-update entity slots and all 5,112 IRQ vectors**,
plus the final wait and outgoing fade. The union of these seven controls is
36,548 vectors. Counts extend existing controls; do not add previous subset
counts again. The older `win` directory remains a damage control.

The successful control interrupts map preparation after its transfer flag
is set but before the row cells are ready. The native scalar transfer gate
now has a completed source owner here; world/service/work/IRQ comparisons
agree. Selecting that interrupted row for image projection explicitly
rejects: old/partial tile-buffer publication is not yet qualified. This is
not proof of pixels at that edge.

## Validation and reproduction

The diagnostic and source tests build at O2 with
`python tools/build_air_clock_probe.py`. Serial compilation avoids the earlier
compiler memory issue; this checkpoint does not depend on an O0 diagnostic.
Synthetic tests exercise culling, eviction, coordinate wrap, mirrors, both
allocation directions, separate partial writes, empty/replaced resources,
map flag completion and exhausted sprite lists. They are not reference data.

Existing complete image selections remain unchanged: **262 unique frames /
6,036,480 pixels**, zero differences, no mask. They cover the six existing
controls, not the new successful control. All 222 outgoing phases and 96
fade services still match. See [image scope](AIR_PIXELS.md).

For a local outgoing control:

```powershell
python tools/air_all_irq_compare.py local/air-irq-outro-damage-native/interrupts.csv --capture local/sameboy-air-outro-damage --timing local/sameboy-air-outro-steer52-timing --boundary-csv local/air-irq-outro-damage-native/services.csv.boundary.csv --exit local/sameboy-air-outro-damage-exit
```

For pause, supply `--pause` instead of `--exit`, using its independently
controlled pause recording. The comparator checks cartridge/control/backend
identity, complete returns, terminal times, native owners, ordering and counts.
Missing or shifted events, protected/aggregate owners and overlapping
inconsistent recordings reject. All measurements/assets stay local.

Remaining scope: initial UI/LCD access, unobserved interrupted entities and
resource publication, pending protected pause crossings, partial row pixels,
successful result accounting/celebration and production scheduling. The common
[result prefix](AIR_RESULT_PREFIX.md) and ordinary
[result transition/failure hold](AIR_RESULT_TRANSITION.md) are separately qualified. No hardware,
PCM, other-stunt or final-release timing acceptance follows from these controls.
