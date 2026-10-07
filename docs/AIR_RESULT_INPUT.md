# Source-owned Air result inputs

The native diagnostic samples raw held buttons at each result display service
and derives fresh edges itself. Source wait helpers retain their different
contracts: the initial ready wait saves the entire fresh byte, later label
waits inspect that latch, per-cent waits save only A/B/Start edges, and the
final hold accepts a fresh A/B/Start edge. Direction input can therefore latch
an early skip while it cannot end the final success/failure hold.

Latched skip bypasses later per-cent waits and intermediate glyph refreshes;
the entire original pay/time transfer still runs. It does not immediately end
the result screen. A separate fresh action ends the final hold. Held actions
do not create repeated fresh edges. Each conditional return/back edge has its
own source completion cost. Soft-reset combinations remain a guarded boundary.

Four separately controlled post-result input schedules extend the same genuine
successful gameplay pattern. Two more action schedules extend damage/timeout;
a direction schedule checks the complete damage hold. Inputs are ordinary
button events at fixed reference-frame times after stunt result, with no RAM
writes or result injection. Measured runs reproduce their uninstrumented
32,768-byte end hashes and separately qualify the nine-point startup epoch.

| Post-result control | Boundaries | Services | Complete vectors | LCD polls | Intended glyph writes |
|---|---:|---:|---:|---:|---:|
| B during initial ready wait | 1,733 | 627 | 1,254 | 342 | 67 |
| Up during initial ready wait | 1,733 | 627 | 1,254 | 326 | 67 |
| B during pay transfer | 1,814 | 627 | 1,254 | 1,692 | 445 |
| B during final successful hold | 2,753 | 602 | 1,204 | 17,634 | 4,802 |
| B during damage hold, including incoming fade | 210 | 95 | 190 | — | — |
| Start during timeout hold, including incoming fade | 210 | 95 | 190 | — | — |
| Up during damage hold, including incoming fade | 1,048 | 514 | 1,028 | — | — |

All differences are zero. The success rows cover accounting after incoming;
the failure rows include incoming. These are post-result extensions of existing
gameplay patterns, not seven additional independent gameplay successes. Each
success preserves savings 340 from pay 335 and five time cents and advances
the stunt index 1 to 2. The two failure action controls shorten the hold from
480 to 61 services; the direction control leaves all 480 waits intact.

Version-two reference comparisons additionally check held/fresh input and the
successful result's skip latch at every observed boundary. The probe accepts
`--result-inputs` with raw result button samples, never original fresh edges,
latch state, per-update counters, clocks or ledger values. Extra/missing input
samples reject. Reference tools preserve source/backend/control identity;
captured data stays local. Legacy unchanged-input evidence remains readable
and requires the complete original hold.

Local proof is under `local/air-success-input-{ready,direction,pay,timer}-*`,
`local/air-failure-input-{damage-b,timeout-start,damage-direction}-*`, matching
`local/sameboy-air-*-input-*/` controls and these logs:
`local/air-result-input-final-comparisons.log`,
`local/air-failure-input-comparisons.log`,
`local/air-accounting-input-regression.log`,
`local/air-result-input-unit-tests.log`,
`local/air-result-input-python-tests.log`.

```powershell
local/air-clock-probe.exe local/sameboy-air-success-input-pay/inputs.txt local/air-success-input-pay-native/services.csv 0 --display-inputs local/air-success-finish-native/buttons.txt --result-accounting --result-inputs local/air-success-input-pay-reference/buttons.txt
python tools/air_result_accounting_reference.py compare local/air-success-input-pay-native/services.csv.account.csv --capture local/sameboy-air-success-input-pay --out local/air-success-input-pay-reference --startup local/air-success-input-pay-startup
```

Native result tests pass 4,646 assertions; Python passes 211 tests. All four
ordinary incoming controls and three complete failure holds pass again after
the shared input changes. Baseline successful accounting also passes with the
additional version-two input/latch observations. Production code, Windows EXE
and its previously checked campaigns/UI are unchanged.

Requested timing point 1 remains open: perfect/final-life/reset results,
subsequent player/stunt setup, earlier UI/LCD entry, unobserved interrupted
owners, partial row pixels and Windows scheduling integration. This is scalar
access/input evidence, not full result image/PCM or final-release acceptance.
