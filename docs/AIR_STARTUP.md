# Pending Air startup service ownership

Three existing independent SameBoy pause controls now also have read-only
startup recordings. Each preserves the complete 32,768-byte uninstrumented
end-state hash. No new boot or modified original input sequence is used.
This qualifies the bounded pending-service sequence, not the preceding UI,
first LCD scanline, arbitrary interrupt latency or production Windows scheduler.

## Source and comparison boundary

The identified LCD-on helper at `00:25a8` reads LCDC, sets its enable bit and
writes it before the return at `00:25ae`. The final access portion takes four
cycles, then RET takes sixteen. The comparison epoch is four cycles before
that observed return. It is determined by the source access, not by fitting
a later display or pause edge. No absolute original epoch enters the native
process. At `00:03c6`, EI followed by LD consumes twelve cycles; both display
and STAT interrupts are already pending. Their source entry is twenty cycles.

All three controls have the following relative times:

| Boundary | Original / native cycles |
|---|---:|
| LCD-on return completed / EI entry | 20 |
| Display interrupt vector | 52 |
| Display body work | 12,336 |
| Pending STAT interrupt vector | 12,424 |
| Ready store completed / first counter-wait call | 12,740 |

The STAT body consumes 288 cycles; each interrupt return consumes sixteen.
The ready store consumes twelve. The original retains IE/IF bits for both
pending services, increments the global and eight-bit display counters once,
and publishes the ready flag. Native display work comes from its gameplay,
HUD, effect and music owners; no captured cost drives it. Actual native startup
boundaries are logged separately and compared, including the return/store.

The previous candidate omitted the last four-cycle access portion. The probe
also repeated the first ready-store prefix after startup had already performed
it. Long HALT waits concealed these errors from post-update comparisons. Both
are corrected; the subsequent complete three coupled pause replays still agree.

## Reproduction and limits

Use the pinned separate reference described in REFERENCE_BACKENDS.md. For each
`case` in `coast`, `easy`, `hard`:

```powershell
python tools/air_startup_reference.py capture 'path/to/original.gb' --capture local/sameboy-air-pause-coast --out local/pause-coupled-coast-startup-reference
python tools/air_startup_reference.py compare local/pause-coupled-coast/services.csv --capture local/sameboy-air-pause-coast --out local/pause-coupled-coast-startup-reference
```

Capture records nine source boundaries; compare reads both native service work
and actual `services.csv.startup.csv` clock boundaries. The coupled runner also
requires this comparison. Missing/reordered events, shifted access tails,
incorrect pending flags, counter publication or mixed provenance reject.
All recordings remain local. Compare imports no emulator.

Synthetic evidence-validation tests include counter wrap and corrupted pending
flags, order, tail and publication. They prevent incomplete recordings from
being reported as acceptance; they do not replace original measurements.

The independent reference's first LCD frame and hardware interrupt microtiming
are still unqualified. The pause readiness model explicitly rejects that first
frame. Completing these pending services does not establish the whole title-to-
gameplay transition, result setup, other interrupted owners, pixel/PCM parity or
Windows scheduling. `productionStartupAccepted: false` remains in every report.
