# Following Air entry pause and return

The native diagnostic now owns fresh Start at the first following Air entry,
the complete pause and its return, and the first gameplay update afterwards.
One new input-only easy Air retry control matches the original with zero
differences. This extends the following startup and first-update owners; it
does not qualify later gameplay or the production Windows scheduler.

## Native ownership

`airFollowingEntry` takes the conditional pause call only on a fresh raw Start
edge. An explicit callback must complete the owned native pause, restore the
Air display/audio state and set `entryPauseComplete` before returning to 03d8.
The first gameplay update may then retain the consumed Start edge; it cannot
call pause a second time. A later fresh Start still needs a separate owner.
Missing callbacks or incomplete restoration reject rather than skip pause.

`airFollowingEntryPause` reuses the source-work pause session and native graphics
polling model. Its LCD geometry is relative to the newly enabled following
LCD epoch. The native cleared object buffer and camera scroll supply geometry;
the prior native Air game and decoded assets supply the fresh HUD row/font.
No observed polling count, reference timing, memory state or original seed
drives native work. Paused displays continue the counter and input/audio
services, without gameplay, HUD cursor or fade advancement. The source paused
display re-enables objects; STAT selector four disables them on its line.

The owner restores the entire status row and font, resumes native music state
and returns to the first update with the inherited partial second and animation
blocks. A read-only original pause-entry witness independently identifies the
consumed Start. The first-update comparison requires the corresponding completed
native pause return, not merely a permissive input flag.

## Original evidence and tests

The separately authorized pinned SameBoy reference replays ordinary button
events from the existing retry control. Start is pressed during the containing
host frame of the following entry wait, released during pause and pressed again
to resume. Two unhooked repetitions establish the control; all subsequent
measurement runs match its complete 32,768-byte terminal memory hash. No original
RAM or life counter is injected. Original data/recordings remain local.

The complete entry interval matches thirteen boundaries, 25 display services
and 50 complete vectors. Two displays/four vectors belong to initial restart;
the remaining 23/46 belong to pause. All 1,746 recorded bus events, 444 accepted
storage bytes in three row/font snapshots, and 53 pause intervals agree. The
three storage snapshots are not complete rendered frames or PCM measurements.

The first post-pause update and next wait/input gate separately match ten
boundaries, 160 actor slots (20 occupied instances), one display and two complete
vectors. Its starting 03d8 repeats the preceding entry endpoint: the combined
entry/update comparison has 22 distinct boundary samples, 26 displays and 52
vectors. These counts include the overlapping ordinary startup prefix and are
not additional independent normal-play coverage. The ordinary first-update
control and all four preceding startup/instruction-exit controls remain exact.

Validation: optimized Windows diagnostic; 663 ROM-free native handoff/pause
assertions, 52,850 result-clock assertions and 434 Python tests. New checks cover
epoch-relative graphics access, completed pause return, frozen world/HUD/fade,
restore/audio state, input edges and the consumed Start attachment. Comparison
integrity checks reject missing/reordered coverage, mixed control/backend hashes,
unknown vector owners, detached stage/epoch and changed bus/storage/phase work.
Unchanged production/campaign/Windows UI suites were not repeated for this
diagnostic-only extension.

## Reproduction

Local captures are `local/sameboy-air-entry-pause/`,
`local/air-entry-pause-reference/`, `local/air-entry-pause-startup/`,
`local/air-entry-pause-timing/`, `local/air-entry-pause-lcd/` and
`local/air-entry-pause-first-reference/`. The original capture tools use the
pinned reference only for comparison measurements. Native playback uses:

```text
local/air-clock-probe.exe local/sameboy-air-entry-pause/inputs.txt
  local/air-entry-pause-services.csv 0
  --display-inputs local/sameboy-outro-damage-buttons.txt
  --result-inputs local/air-entry-pause-first-reference/buttons.txt
  --following-entry-pause --following-gameplay
```

The independent comparison commands are `air_following_pause_reference.py
compare` and `air_following_gameplay_reference.py compare`. They load no
emulator. The former also takes the stage summary, startup epoch, separate
pause timing/LCD records and native pause geometry/bus/graphics/phases. Reports
are `local/air-entry-pause-comparison.log` and
`local/air-entry-pause-first-comparison.log`; final preceding regressions are
`local/air-entry-pause-prior-regressions.log` and
`local/air-entry-pause-prior-first-comparison.log`. Native build/test and Python
logs use the same ignored `local/air-entry-pause-*` prefix.

## Limits and remaining work

This qualifies one easy Air first-entry pause with its first post-resume update.
It does not qualify Ski/changed-player handoffs, later paused or unpaused play,
final-life/reset, earlier UI/LCD startup, unsupported protected/interrupted
entity/resource work or first-frame graphics geometry. It compares selected
actor/scalar fields and three row/font storage snapshots; full startup map/sprite
bytes, rendered images, PCM and hardware behavior remain separate acceptance
requirements. The production EXE and one-update-per-frame Windows scheduler are
unchanged. Timing point 1 and final-release acceptance remain incomplete;
the private repository and continuation automation stay active.
