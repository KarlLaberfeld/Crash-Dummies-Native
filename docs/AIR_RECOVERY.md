# Air Bumper crash recovery

## Failure and source evidence

The medium-layout replay `A | (((elapsed + 24) / 24) % 2 ? Left : Right)`
previously stalled in 12 of 64 initial global-update phases (0 through 63).
It reached the recovery handler with a stopped crash animation and never
returned player control. This is a native reproducer, not a cartridge capture.

The reconstructed handoff follows these original routines:

- `01:61fe` starts the crash with an 80-update counter and the script at `622d`.
- `01:6246` advances that script and the falling player until the deadline.
- `01:6307` selects the generic animation handler and requests recovery `6315`.
- `00:3b84` refuses that request if an animation is still active.
- The crash script ends with effect 4 and a stop; it does not install recovery.

Map-row priority (`00:0c3f`) can delay the dynamic-frame transfers awaited by
the crash script. In the affected native replays, the 80-update deadline
arrives before the script stops. The rejected recovery request was discarded;
the generic animation handler subsequently had no remaining work.

Static analysis agrees with the conditional starter, delay decrement, four-chunk
transfer budget and map-row priority. It does not establish that the cartridge
reaches exactly the same timing. Disabling map contention removed the local
failure but changed an identified original rule, so that diagnostic was not
used as the fix.

## Deliberate native stability correction

The player now retains a recovery request rejected at that boundary. The
current crash script finishes normally, including its final sound. At its
stop, the request starts the unchanged recovery script once; that script
begins executing on the following update. On-time requests still start at
the original deadline. Transfer priority, script periods, the deadline,
collision rules and saved return coordinates are unchanged.

Only the player can consume this request. Pause preserves it; restarting the
stunt, entering a new crash or starting a terminal result clears it. This
adds one explicit native state flag, with no CPU interpretation, forced
animation restart, coordinate teleport or arbitrary recovery timeout.

This is a liveness fix in the native port, **not a newly proven translation
of original behavior**. A matched original trace remains necessary to decide
whether the cartridge has this edge case or another timing detail is missing.
If a source-backed scheduling correction makes late requests unreachable,
remove the safeguard only after keeping these regression scenarios passing.

## Regression evidence

The new test failed against the pre-fix native implementation at the stopped
animation assertion. With the correction, all 64 phase replays reach a stunt
result within 12,000 updates. Exactly 12 phases exercise deferred recovery;
the sweep observes 232 completed returns to player control. Each observed
recovery must return control within 512 updates; that bound is a test assertion,
not a runtime timeout or rule.

Focused checks cover an unchanged on-time handoff, preserving the late crash
script, its final sound, one-time recovery startup, pause, restart, terminal
result cancellation and isolation from other animated entities. The Air suite
passes 822,125 assertions, including ordinary replays and successful input-only
runs on all four difficulties. Counts include repeated invariants. Original
game equivalence and human play acceptance are not established by these tests.

The rebuilt Windows executable also passes the full native suite, all three
complete campaign scenarios, and the 13 Windows UI checks. The campaign results
remain unchanged from the preceding checkpoint. The build's 26 Python tests
pass as well. Logs: `local/air-recovery-build.log`, `build/air-test.txt`,
`build/playthrough-test.txt`, `build/ui-window-test.txt` and `build/audio-output.txt`.

ROM, disassembly, extracted assets, detailed replay logs and generated binaries
remain local. The repository contains source, tests and these evidence notes.
