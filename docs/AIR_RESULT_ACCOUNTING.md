# Bounded successful Air result accounting

The native diagnostic continues ordinary successful Air results from 047e
through the next-stunt index update and return at 0514. It reconstructs source
operations, not CPU instructions. The Windows scheduler is still unchanged.

`src/air_result_accounting.h` owns the initial 15 waits, savings/pay/time labels,
numeric formatting, LCD-safe glyph stores, the 20/15 waits between labels,
one-cent pay/time transfers, final countdown-plus-60 hold and music stop.
The result compare line changes from 143 to 120 at its actual access boundary.
The three static layouts are decoded locally into `result-layouts.dat`; no
instructions, captured times or original ledger values enter the native model.
Formatting and work are calculated from native amounts and semantic commands.

The result timer retains one when its decrement would reach zero. That service
costs 228 cycles instead of the ordinary 272; it omits the countdown stores.
The successful recording independently verifies 61 such services. This is a
source guard, not an expired gameplay timer. The original stunt index C088
advances from Air (1) to Ski (2); this is not the campaign day index.

The input-only successful control holds A and alternates steering every 120
updates with offset 56 on difficulty zero. It earns 335 cents, finishes with
five seconds and transfers 340 cents to initial savings zero. The extended
1,500-frame observation has byte-identical gameplay trace/input files and
preceding events. Both uninstrumented and read-only measured runs retain the
same 32,768-byte control hash. A separate nine-point startup qualifies the epoch.

The comparison checks all 2,753 boundaries, 627 additional display services,
1,254 complete interrupt vectors, 17,634 LCD-mode readbacks and 4,802 intended
glyph writes, with zero differences. It verifies native ledger, time, stunt
index, countdown, music state and every service component. Missing coverage,
incorrect order, changed provenance and shifted accesses reject. Together with
the incoming fade this result has 660 services; the intervals share a boundary
and must not be counted as independent gameplay patterns.

Intended glyph writes are measured before the original store. These checks
establish readiness, intended bytes/destinations and timing; they do not prove
complete result image parity or physical hardware write acceptance. Evidence
covers one ordinary success with unchanged post-stunt buttons. Perfect results,
button skips/reset, final-life results, the subsequent player/stunt setup,
unobserved interrupted owners and production integration remain open.

Local evidence: `local/sameboy-air-success-accounting/`,
`local/air-success-accounting-reference/`, matching `-startup/`,
`local/air-success-finish-native/account-services.csv*`,
`local/air-success-accounting-final-comparison.log` and
`local/air-accounting-checkpoint-verification.log`. Source control contains no
ROM, extracted data, captures or reference core.

```powershell
python tools/build_air_clock_probe.py
local/air-clock-probe.exe local/sameboy-air-success-accounting/inputs.txt local/air-success-finish-native/account-services.csv 0 --display-inputs local/air-success-finish-native/buttons.txt --result-accounting
python tools/air_result_accounting_reference.py compare local/air-success-finish-native/account-services.csv.account.csv --capture local/sameboy-air-success-accounting --out local/air-success-accounting-reference --startup local/air-success-accounting-startup
```

Validation adds ROM-free formatting/ledger/access/clock tests and strict
comparator rejection tests: 4,624 native result assertions and 200 Python
tests. The four incoming controls and three complete failure holds pass again
after the shared countdown change. Existing gameplay/image and Windows
campaign/UI evidence remains applicable; no unchanged campaigns were repeated.
Requested timing point 1 and the overall final-release checklist remain open.
