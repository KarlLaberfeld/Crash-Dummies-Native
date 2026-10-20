# First-page direction unlock comparisons

October 20, 2026. Adds correct Up/Down/Left/Right, long-held Up, a wrong
direction followed by the correct sequence, and combined Up+Left followed by
the correct sequence. Each case runs in both accepted ordinary/earlier-paused
histories. The owner ends at 2b4f before the password transition; it does not
qualify password presentation, entry, validation or return.

All eight complete comparisons match 1,957 boundaries, 221 displays, 663
vectors, 884 raster boundaries, 2,065 stores and 16,384 final map bytes, zero
differences. Each preserves all 366 / 370 preceding complete native CSVs.
The full attached original/native chain is requalified per case.

Fresh exact direction masks advance native sequence progress. Held input
creates no edge and never repeats a step. A wrong or combined mask resets to
the first step without retrying that same edge. The fourth correct edge
resets the selector and exits before another page-duration decrement or
Start/Select/A/B decision. Native work owns both selector stores, all source
branches, display/input/audio services and the inherited raster clock. No
observed states, timings, service schedules or fitted budgets drive execution.

The long-held case has 29 display samples in the ordinary history and 30 in
the earlier-paused history. The original joypad halves are read separately;
the host-frame release boundary can produce a different sampling edge. Native
execution consumes each actual raw sample rather than normalizing host frames.
Both cases retain one fresh Up step and match independently. The game countdown
stays 54; only nonterminal menu iterations decrement the page duration.

Every input-only control forks the previously accepted first-page host-frame
boundary. Original setup/events before the fork stay unchanged. Each new
prefix/full control is replayed unobserved twice, and the observed replay
retains both hashes. No RAM edits or state overrides are used. The comparator
checks exact tail events/setup/ROM/backend identities and the page attachment.
Source captures and native raw-input prefixes retain the entire preceding
history. Full maps remain unchanged through the sequence decision.

Prepare using `tools/air_title_unlock_reference.py prepare ROM --capture
ORIGINAL_CONTROL --actions-control ACCEPTED_START_CASE --page-out PAGE_REFERENCE
--out CASE_CONTROLS`. Capture each case using `capture ROM --capture
ORIGINAL_CONTROL --parent-out PAGE_REFERENCE --fade-out FADE_REFERENCE
--case-control CASE_CONTROL --out CASE_REFERENCE`. Rebuild the native probe
with `tools/build_air_clock_probe.py`; replay accepted full extents/inputs with
`--title-unlock` and each case's button file. Compare using `compare NATIVE_BASE`
and first-page/action-comparator arguments, replacing `--actions-out` with
`--unlock-out`. Native outputs use `.fifth.title-unlock*`; reports use
`.title-unlock.comparison.json`.

Validation: O2 diagnostic, all eight full comparisons, 748 native unlock
assertions, 44,343 rebuilt prior menu assertions, CLI prerequisite guard and
1,167 Python tests (23 new synthetic integrity cases). New tests cover held,
combined and wrong inputs, exact progress/reset stores, no page mutation,
tick rollover, terminal duration ownership and invalid prerequisite ownership.
The new native target joins the regular test build. Windows EXE rebuilt from
committed source; semantic timing remains diagnostic. No release/automation
change; ROM/assets/recordings/binaries remain local.

The broader requested [original comparisons](ORIGINAL_COMPARISON_SCOPE.md)
remain in progress. Password transition/validation, other pages/player/options/
music-test/name-entry/campaign/stunt paths and first-instruction continuation
still require separate original witnesses. Full frames/PCM and production/
human/device/independent-Windows/distribution gates remain open.
