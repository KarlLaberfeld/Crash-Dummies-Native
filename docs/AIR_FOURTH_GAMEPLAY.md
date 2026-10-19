# Fourth Air gameplay continuation

Follow-up: [retained side-push inheritance](AIR_SIDE_PUSH_INHERITANCE.md) resolves
the paused discrepancy and qualifies both 1,000-update histories. The checkpoint
below retains the original failure evidence and its original scope.

October 19, 2026. Continuation of [two-life fourth entry](AIR_FOURTH_ENTRY.md).
The ordinary history matches 1,000 fourth-attempt updates. The earlier-paused
history exposes a timing discrepancy and is not accepted through that extent.
This is diagnostic work; production scheduler/EXE and alpha are unchanged.

## Accepted ordinary scope

10,000 boundaries, 160,000 actor slots, 1,000 display services, 2,000 vectors
and 40,000 published object slots match, with zero differences within scope.
Counts include the previously accepted first update. The inherited partial
second starts at 14; 738 timer increments produce 12 rollovers, the first in
zero-based update 307. Twenty resource requests, 75 uploads and 20 completions
match, with 15 map-deferred displays. All vectors are wait-owned; no additional
interrupted-body owner is accepted. A busy-scene capture intentionally rejects
this history because it exercises no non-wait vector; resource capture is the
appropriate scope, without weakening either analyzer.

All 220 earlier native CSVs/scopes remain complete-byte identical, or retain
their exact first-update prefix where gameplay now continues. Only the native
gameplay summary is replaced by its longer endpoint; the old map end marker
is excluded from the prefix, with the preceding row observations unchanged.
The complete accepted entry comparison is rerun under its own parent hashes.
Full row bytes are not independently compared by this new scope. Vacant done
flags retain the separately documented initial mismatch; occupied actors and
published object positions/flags remain covered.

## Unaccepted earlier-paused continuation

The native replay completes 1,000 updates, but the strict source comparison
reports seven timestamp differences at point indices 2622..2628 in zero-based
update 262 (the 263rd update). Native is 32 cycles late from `entitiesDone`
through `backEdge`. The following counter wait returns to the original cadence.
The player transitions from original Wait handler 5fc9 to Play 5fd6, with its
countdown parameter changing from 1 to 0. No actor/scalar/service/vector field
difference is reported by the resource comparator. Separate object-publication
comparison does not execute after the timing failure; it is not accepted.

The next task is to identify the original branch/instruction cost and correct
its semantic work owner. No timestamp shift, fitted allowance, skipped point
or relaxed tolerance is applied. This longer paused history must not be
described as exact. Its earlier entry/first-update acceptance remains intact.

## Control integrity and reproduction

For each accepted fourth-entry control, preserve setup state, initial input file
and complete events; append exactly `["tick", 1800, true]` with unchanged held
A/Left and released Start. Two independent uninstrumented replays must match
the parent's complete 32,768-byte RAM digest at the preserved attachment and
the new child digest at the endpoint. No RAM/life/seed injection is used.
Every instrumented capture matches the child digest and pinned backend.

Capture initial startup under the new child hash in a fresh startup folder.
Capture gameplay using `tools/air_following_gameplay_reference.py capture`
with the usual ROM, `--capture` and `--out`, plus
`--next-retry --after-retry 2 --updates 1000 --resource-transfers`.
It retains the full preceding raw button history and independently observed
object DMA publications. Parent recordings retain their own original hashes.

Build with `tools/build_air_clock_probe.py`. Use the accepted fourth-entry
replay arguments, the new gameplay `buttons.txt`, and append
`--fourth-updates 1000`. Extent must be 1..100000 and a non-default extent
requires `--fourth-entry`. The bounded child cannot enter a new result.
Native output stays under `NATIVE_BASE.fourth.next-gameplay*`.

Run `tools/air_fourth_gameplay_reference.py NATIVE_BASE` with current
`--capture`, `--out`, `--startup`; accepted fourth-entry `--first-base`,
`--start-capture`, `--start-out`, `--start-startup`; and its original instruction
chain `--parent-capture`, `--parent-out`, `--parent-startup`,
`--parent-result-out`, `--instruction-base`. It checks repeated controls, exact
input extension, original first-update equality, current timer progression,
complete native prefix and the accepted entry chain, then native resource and
object publication. Any timing difference remains a hard failure.
The accepted report is `.fourth-gameplay.comparison.json`.

Local controls: `local/sameboy-air-fourth-control/` and
`local/sameboy-air-fourth-pause-control/`. Recordings use
`local/air-fourth-1000-reference/` and `local/air-fourth-pause-1000-reference/`;
startups and native bases use the corresponding `air-fourth` naming. The paused
failure is retained in its native base's `.comparison.log` and
`.fourth.next-gameplay.resource-comparison.json`. All source recordings, ROM,
decoded assets and executables remain ignored/local.

Validation: optimized native Windows diagnostic, accepted ordinary comparison,
both unchanged first-update/entry chains and 743 Python tests. CLI invalid
extent and missing-entry guards pass. Native semantic owners were unchanged;
their previous assertions were not repeated. Final timing acceptance, the
paused discrepancy, later gameplay/results, other campaigns, unused initial
animation flags, production integration, complete images/PCM and final human/
device/Windows/distribution checks remain open. Automation remains ACTIVE.
