# Third Air attempt: inherited timer and resource continuation

October 19, 2026. Diagnostic timing acceptance only. Both existing easy Air
histories now continue through 1,000 updates of the third attempt, following
the [accepted entry and first update](AIR_NEXT_RETRY.md).

## Results and limits

| Compared third-attempt work | Ordinary history | Prior entry-pause history |
| --- | ---: | ---: |
| Updates / semantic boundaries | 1,000 / 10,000 | 1,000 / 10,000 |
| Actor slots / occupied actor instances | 160,000 / 40,365 | 160,000 / 40,033 |
| Displays / complete vectors | 1,000 / 2,000 | 1,000 / 2,000 |
| Published object slots | 40,000 | 40,000 |
| Resource requests / completions | 20 / 20 | 21 / 21 |
| Resource-upload displays | 75 | 79 |
| Map-deferred resource displays | 15 | 14 |
| Inherited partial-second phase | 54 | 33 |
| Timer increments / second rollovers | 738 / 13 | 738 / 12 |
| First rollover update (zero-based) | 267 | 288 |
| Final seconds / partial-second phase | 27 / 12 | 28 / 51 |
| Differences | 0 | 0 |

Combined: 20,000 boundaries, 320,000 actor slots, 2,000 displays, 4,000 vectors,
80,000 published object slots, 41 completed requests and 25 second rollovers.
These totals include the two first updates accepted previously. The earlier
gameplay/result/instruction/entry comparisons overlap their prior milestones;
they are attachment evidence, not additional independent gameplay cases.

The intro/rise interval retains the inherited partial second: a preliminary
240-update observation contained no timer increments or resource work. The
longer scope includes active player work, timer rollover, resource requests,
four-chunk uploads, map deferrals and acknowledged completion. The timer check
requires one-step phase progression and seconds decrement at 59-to-0; it rejects
changes outside actor work and a scope without an actual rollover.

All observed vectors in this interval return to the counter wait. No body
interrupt occurs, so the stricter interrupted-scene coverage requirement is
not satisfied and is not claimed. The resource/quiet-work analyzer is used;
scene acceptance is not weakened to turn a quiet history into interrupted-work
evidence. Object publication is still compared against independently observed
OAM snapshots for every display: presence, visible geometry and flags. Full
tile bytes, pixels and PCM are outside this comparison.

## Native continuation and provenance

The diagnostic accepts `--next-updates N` together with `--next-retry`. The
default remains one update. Invalid extents, missing retry ownership and an
incomplete next instruction reject. Repeated updates reuse the existing native
actor/resource, sprite/map/placement and counter-wait owners. Prepared and
published objects are exported separately. No original counters, return
addresses, timer states or observed work costs drive native scheduling.

The accepted child control already ended with 300 released-Start frames. Append
another 1,800 frames without changing any earlier event, setup state or input
file. Two uninstrumented replays per extended control agree, and both full-RAM
hashes at the accepted child's endpoint equal its original control hash. Every
instrumented capture matches the extended final hash. No memory/life/seed/timer
injection is used. Parent and child recordings keep their distinct hashes.

The new verifier reruns the accepted first-update chain against its original
controls. It then requires byte-identical preceding native CSV outputs and
prefix-identical first-update outputs, including actors, input/audio, vectors
and object publication. Ordinary/paused histories check 136/140 native prefix
files. Original first-update points/vectors/service origin also match exactly.
Resource, timer and object comparators then check the longer recording.

## Reproduction

Keep the pinned reference emulator separate from native execution. Capture
startup for each extended control using `tools/air_startup_reference.py`.
Capture its third-attempt gameplay with:

```text
tools/air_following_gameplay_reference.py capture ORIGINAL_ROM
  --capture EXTENDED_CONTROL --out THIRD_REFERENCE
  --next-retry --updates 1000 --resource-transfers
```

Build with `tools/build_air_clock_probe.py`. Retain a new one-update replay of
the accepted entry control using the same diagnostic executable. Replay the
extended control with its new `buttons.txt`, `--following-gameplay
--following-updates N --next-retry --next-updates 1000`; N remains 1,788
ordinary / 1,767 paused, with `--following-entry-pause` for the latter.

Run `tools/air_third_gameplay_reference.py NATIVE_BASE` with the extended
`--capture`, `--out`, `--startup`, the new one-update `--first-base`, the accepted
entry's `--start-capture`, `--start-out`, `--start-startup`, and its earlier
`--parent-capture`, `--parent-out`, `--parent-startup`. All paths are explicit to
avoid mixing final control hashes. The final sibling report is
`.third-gameplay.comparison.json`; individual component reports remain available.

Local extended controls are `local/sameboy-air-third-control/` and
`local/sameboy-air-third-pause-control/`. Observations use
`local/air-third-1000-reference/` and its pause variant. Startup folders use
`local/air-third-startup/` and its pause variant. Native outputs use
`local/air-third-1000-services.csv*` and its pause variant; accepted first-update
replays use `local/air-third-next-start-first.csv*` and the pause variant.
ROM, extracted data, recordings and reference/native binaries remain local.

Validation: optimized native diagnostic, both complete attached comparisons,
the earlier first-entry comparisons and 667 Python tests. CLI bounds/ownership
guards also reject invalid requests. Native semantic owners and production code
were not changed; the preceding 52,878 result / 882 handoff / 4,200 work and
819,624 core gameplay assertions remain applicable and were not repeated.

## Remaining work

Third-attempt terminal/outgoing/result continuation is now qualified in the
[next checkpoint](AIR_THIRD_RESULT.md). The paragraph below records this
1,000-update checkpoint's original boundary.

Continue the third attempt through its terminal update and result, with any
new interrupted-work owner justified by actual observations. Other stunt,
player/shared-animation, final-life/reset and earlier UI/LCD paths still need
their own comparisons. Production Windows scheduling, full image/audio fidelity,
human/device/independent-Windows testing and final distribution remain open.
The production EXE and versioned alpha are unchanged. Timing point 1 and
[final acceptance](ACCEPTANCE.md) remain incomplete.
