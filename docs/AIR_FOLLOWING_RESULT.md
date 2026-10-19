# Restarted Air result setup, incoming fade and complete failure hold

October 19, 2026: both existing easy Air retry histories now match from their
outgoing endpoints through common result setup, incoming fade, the full failure
hold and music stop/return at 0514. This is diagnostic timing acceptance for
two non-final failure results, not the whole campaign or production scheduler.

## Native behavior

The common result setup's line-145 equality wait now receives the most recent
native LCD epoch. Scanline polling is relative to that epoch while completion
timestamps remain absolute. Reusing process time modulo a hardware frame was
valid for the initial Air clock only; it could not establish the restarted
result's LCD phase. The default zero origin remains available for the already
qualified initial-game controls. Negative, future or incomplete epochs reject.

The existing semantic result setup then performs the masked object/register/
map reset and fixed graphics copy. The incoming transition receives the native
result, selected campaign player, inherited lives, display counter, raw input,
audio state and locally decoded layout/UI assets. The identified non-final
failure store consumes one life at its eight-cycle completion. These histories
enter with four lives and leave with three; they do not reinitialize a campaign.

The result LCD restarts with new absolute deadlines. Already pending VBlank
and STAT run in their identified priority before the failure wait. Music startup,
all eight incoming palette stages and 32 counter waits retain their existing
native work. The complete 480-display hold receives no fresh action in these
controls, then stops music and returns. Displays continue input sampling,
countdown/audio work and the global tick. The final result countdown is 86.

No recorded cycle, poll count, original life value or memory snapshot selects
native execution. The probe reads raw buttons and decoded local assets only;
source algorithms compute every outcome and deadline. It runs no Game Boy CPU
instructions. Original execution remains a separate authorized comparison tool.

## Original comparison

Only the final held-input interval was extended from 2,242 to 2,900 frames in
each existing control, allowing the full hold to finish. Setup snapshots and
preceding events are unchanged; no RAM, seed, life or outcome is injected.
Two uninstrumented repetitions agree per extended control. Every new startup,
gameplay/outgoing, result-prefix and incoming/hold capture agrees with the
corresponding full 32,768-byte control-memory hash on the pinned SameBoy backend.

| Result comparison | Ordinary retry | Entry pause/resume | Combined |
|---|---:|---:|---:|
| Prefix boundaries including LCD-disable observation | 11 | 11 | 22 |
| Line-145 equality poll reads | 2,121 | 2,122 | 4,243 |
| Incoming/hold/stop boundaries | 1,048 | 1,048 | 2,096 |
| Complete result display services | 514 | 514 | 1,028 |
| Complete interrupt vectors | 1,028 | 1,028 | 2,056 |
| Full hold displays (included above) | 480 | 480 | 960 |
| Inherited / remaining lives | 4 / 3 | 4 / 3 | same two histories |
| Differences | 0 | 0 | 0 |

The 514 displays comprise one pending startup service, one failure wait, 32
incoming fade waits and the 480-display hold. Shared prefix/incoming endpoints
are compared twice; outgoing endpoints overlap the previous checkpoint. These
counts extend the same two easy Air histories, not additional independent games.

All prior gameplay/outgoing coverage is rechecked with these extended controls:
3,555 updates, 35,550 gameplay boundaries, 568,800 actor slots, 148 outgoing phases
and 145,120 published object slots still match. Those totals overlap the preceding
checkpoint. The successful prior control and all four preceding startup/exit
controls also retain exact comparisons with the rebuilt diagnostic.

The result verifier requires explicit following-result capture scope and exact
attachment to the outgoing endpoint. It checks every prefix boundary/poll, all
incoming/hold boundaries, palette registers, music-enabled state, raw/fresh input,
counter/countdown, component audio/display work and complete vectors. It verifies
the inherited player/lives/input/seed state, one life consumption, pending-service
priority, final life count and the result LCD's subsequent deadlines. Missing or
mixed controls, truncated holds, detached endpoints and stale deadlines reject.

Result text/portrait copying is qualified by source layout work and completion
boundaries. This does not certify all actual VRAM/color-buffer bytes, complete
rendered result images, audio reset memory layout, palette bus microtiming or
PCM. It does not qualify final-life handling, reset, a successful restarted
stunt, following Ski/changed-player gameplay or arbitrary interrupted work.

## Tests and reproduction

The O2 diagnostic passes both full extended controls. Native tests pass 52,871
result assertions, 863 handoff/pause/exit assertions and 4,200 source-work
assertions. Added cases qualify shifted LCD origins at every observed boundary
and poll sequence, reject invalid epochs, and carry the four-to-three life
transition across all 480 hold displays. All 584 Python tests pass, including
31 new synthetic result-attachment/integrity cases. Two earlier 1,000-update
resource controls, four startup/exit controls and the earlier successful Air
gameplay/IRQ/result control pass. Core gameplay rules are unchanged; their
previous 819,624 assertions remain applicable and were not rerun.

For each locally control-verified recording:

1. Capture startup with `tools/air_startup_reference.py capture`.
2. Capture gameplay/outgoing with `tools/air_following_gameplay_reference.py
   capture --updates N --outro`.
3. Capture the restarted prefix with `tools/air_result_prefix_reference.py
   capture --following` and the incoming/full hold with
   `tools/air_result_transition_reference.py capture --following --failure-hold`.
   Supply the same ROM, control folder and output folder to these commands.
4. Build with `tools/build_air_clock_probe.py`. Replay using raw display buttons
   and `--following-gameplay --following-updates N --following-result-hold`;
   add `--following-entry-pause` for the paused history. The incoming capture's
   `buttons.txt` contains all preceding result/instruction/retry/outgoing samples,
   not only the new result's 514 samples. `--following-result` stops after its
   incoming fade when paired with a capture without `--failure-hold`.
5. Run the existing gameplay-resource and outgoing comparators. Run
   `tools/air_following_result_reference.py` against the native base output path
   and the same capture/startup/output folders. It requires sibling
   `.following-result*`, `.following-incoming*` and `.following-outro.summary.csv`
   files, and writes `.following-result.comparison.json`.

Local controls are `local/sameboy-air-result-control/` and
`local/sameboy-air-result-pause-control/`. Original observations are under
`local/air-following-result-reference/` and the corresponding pause folder;
startup observations use `local/air-following-result-startup/` and its pause
variant. Native outputs use `local/air-following-result-services.csv*` and
`local/air-following-result-pause-services.csv*`. Logs and test binaries use
`local/air-following-result-*`. All original data/recordings remain ignored/local.

## Remaining work

Attach the 0514 post-failure return to player selection, background clearing and
the next instruction using the inherited three-life campaign. Following Ski,
changed-player/shared-animation paths, final-life/reset, earlier UI/LCD and
unobserved work remain open. Production Windows scheduler integration, full
images/PCM, human/device/independent-Windows and final distribution acceptance
still apply. The production EXE/versioned alpha are unchanged. Timing point 1
and final-release acceptance remain incomplete; see ACCEPTANCE.md.
