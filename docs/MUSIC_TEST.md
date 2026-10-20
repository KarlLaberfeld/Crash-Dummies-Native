# Music-test controls, all tunes and effects

October 20, 2026. Continues the accepted [music-test presentation](PASSWORD_RETURN.md)
in both retained single-player Air/easy histories. Five input-only cases per
history cover navigation, stop/restart, all fourteen tunes, all twenty-six
effects and restarting an already completed tune. Includes both selector wrap
directions, held/combined directions, combined B+A and Start exit through 2bdc.
Hexadecimal values are rendered before fresh input; B is processed before A.

All ten attached comparisons match 117,598 boundaries, 9,030 display/music
services, 27,090 vectors, 36,120 raster boundaries, 86,454 polls, 117,768 stores,
20,480 direct map bytes, 2,560 shadow-object bytes and 54,180 voice rows, with
zero differences. Each preserves all 413 / 417 complete preceding native CSVs.
Two unobserved prefix/full control hash repetitions and observed hashes agree.
Shared ancestors are fully qualified once per batch; every complete child
prefix, original input control and local capture is independently attached.

The native semantic owner executes its own numeric writer, selector logic,
audio reset/start/stop and queued effects using native state and actual source
work. Original clocks, voice snapshots and interrupt schedules never initialize
native execution. Disabled-driver flags, last song and pending values remain
recorded; the existing explicit logical-silence projection applies only when
the source driver is disabled. Enabled voice state remains compared.

The all-tunes case exposed a production audio bug at tune 10: a pulse attack
reaching volume 15 with zero decay incorrectly decremented to 14 immediately.
At 02:4196 / 447a / 4b2e the comparison uses the loaded decay value in A, rather
than the new stage. The original returns with volume 15, stage 1, counter 0;
decay begins on the following service. Native behavior and semantic work now
preserve that branch (276 / 272 / 276 cycles for pulse voices 0 / 1 / 4).
The previous 440-cycle assumption was wrong. The original case's 164-cycle
service discrepancy and volume mismatch both disappear after correction.
Regression checks cover pulse/effect/noise peaks and the following decay tick.

Use `tools/music_test_reference.py prepare/capture/compare`. Preparation extends
the accepted valid-9 return control with five fixed input-only tails. Capture
takes `ROM --capture ACCEPTED_RETURN_CONTROL --control TEST_CONTROL --parent-out
RETURN_REFERENCE --out TEST_REFERENCE`. Replay the full native chain with
`--music-test` and the resulting raw display input stream. Compare inherits the
return comparator arguments plus `--test-out`, `--test-control` and
`--return-screen-base`. `compare-batch MANIFEST` uses a local JSON list of
argument-path dictionaries with one shared ancestry. New diagnostic CSVs use
`.fifth.music-test*`; reports use `.music-test.comparison.json`.

Validation: optimized Windows diagnostic, all ten original comparisons,
43,181 native music-test assertions, 157 native audio assertions and 1,439
Python tests (39 new evidence-integrity tests). The music-test target joins
the regular test build. No ROM/assets/reference recordings or binaries are
published. No release or automation change.

This qualifies the music-test loop and its RET boundary, not its subsequent
complete menu return. That return, other title/player/campaign/stunt paths,
rendered frames/PCM, device tests and production scheduler integration remain
open in the [completion matrix](ORIGINAL_COMPARISON_SCOPE.md). The broader
request and final acceptance remain incomplete.
