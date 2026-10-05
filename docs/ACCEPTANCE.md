# Final release acceptance

Latest pause checkpoint: three independent cases match 900 native prefix
updates, 5,252 graphics/status bus events, 418 paused services, 857 intervals
and 1,332 accepted graphics-storage bytes through restoration/return. The
candidate derives its own readiness and work; it uses no captured poll/idle
allowance. 519 pause assertions, 107 source assertions and 116 Python tests
pass. See [bounded pause evidence](AIR_PAUSE_CANDIDATE.md). Initial LCD phase,
arbitrary IRQs, software audio restoration, post-resume replay and production
integration remain required. The rebuilt Windows EXE is byte-identical to the
previously tested preview; no unchanged campaign/UI suite was repeated.

Latest checkpoint, October 5: interrupted Air placement range ownership is
reconstructed and tested against an independent original witness. All eleven
earlier PyBoy clocks still pass. Three current SameBoy replays match 7,655
updates, 7,791 display/input samples, 45,930 phases and 122,480 pre-update
frame/flags/position snapshots, plus final waits and complete outgoing fades.
The rebuilt EXE passes full native suites, three campaigns and the normal/
failed-audio 13/14 Windows checks. Standalone source work passes 107 assertions;
Python passes 103 tests. See [placement evidence](AIR_PLACEMENTS.md).

These remain development acceptance results. The final-release requirements
below still apply, especially production pause integration, other interrupted
owners, startup/result setup, Windows scheduler integration, other stunts,
matched images/audio and human/independent Windows validation.

This checklist separates native implementation tests from original-reference
evidence. Passing the native suites alone does not authorize a final-release label.

| Area | Evidence already available | Required before final release |
|---|---|---|
| Five stunts / four difficulties | Native rules, deterministic replay and a 20-stunt input-only campaign | Original comparisons for normal play, collisions, success and failure |
| Air crash recovery / timing | Native safeguard passes all 64 phase replays; original trace/control reproduce the failure; checked source models now include music and STAT/wait parts; an experimental ordinary-clock probe matches nine Air cases (28,103 completed updates, 28,153 services), including partial sprite preparation/clearing; two cases match 158,840 published sprite slots; a successful finish validates WallSlide/FinishMotion and final particle/sound behavior; boost expiration and severity drag are corrected | Retain the intentional recovery fix; complete remaining handlers and interrupted subphases, hardware/input/pause/exit timing, then integrate and verify the Windows scheduler; expand winning/failure/collision cases and verify on independent reference/hardware |
| Presentation | Source-derived menus, transitions, palette tests and double-buffered shared sprite resources | Reference captures at matched input/update boundaries, including gameplay entry, pause, landing/body parts and exit |
| Audio | All 14 songs and 26 effects decode; 5,441 isolated original services match native voice-state fields and work; pitch/byte-wrap corrections and source envelope regressions pass | Original recordings for timing, channel interaction, envelopes and pitch; verify actual gameplay requests and presentation timing across all stunts |
| Two players | Complete automated campaigns: both players finish, and player one is eliminated while player two finishes | Human playthrough and comparison with original player handoff/ending behavior |
| Windows | Native executable builds; UI tests pass with normal audio and an injected audio-open failure | Human input/focus/resize/pause tests, physical audio-device removal and a separate Windows installation |
| Distribution | Local preview packaging script, no ROM upload | Final acceptance results, reproducible package verification and versioned final release |

For every reference comparison, record the source and capture method, cartridge
revision, starting state, input sequence, update alignment, expected result,
observed result and remaining differences. Do not treat a native replay compared
against itself as original-reference evidence. Keep copyrighted captures/data
local. Keep repository-facing reports in English.

Manual Windows checks: start from an extracted folder with spaces in its path;
complete a campaign; enter and delete initials; start another campaign; exercise
both players; pause with Enter and Escape; switch focus; resize/minimize/restore;
test sound with and without an available output device; close and restart.
Record whether each check was actually run and on which environment.

## Development-host results, 2026-10-02

The automated Windows window test passes 13 checks through keyboard, focus and
resize messages: boot/title, campaign start, Roof entry, pause/resume with
audio, title return, Air development selection, Escape handling, focus-loss
key release and resizing. It also passes from an extracted preview directory
containing spaces, using a different working directory. The output device is
available and reports no dropped buffers. This is one Windows host and uses
synthetic messages; human observation and another Windows installation remain
unchecked.

The `--ui-no-audio-test` variant passes the same 13 UI checks plus a check
that an invalid Windows device identifier actually fails to open. The native
application continues through gameplay, pause/resume and title return with
no output device. A subsequent normal run again opens the output device and
passes all 13 checks. Logs are separate for the two modes. This exercises the
real API error path without disabling or removing system devices; it does
not establish behavior on actual device removal or a different driver/host.

The expanded input-only campaign harness now completes three scenarios through
ending/name-entry/title return: single-player (20 wins, no failures), both
players (20 wins each, with two/three failed attempts), and player-one
elimination (five losses, followed by player two's 20 wins). Player handoffs
and isolation of the other player's campaign state are checked. These runs
also cross the original 16-bit global update counter boundary. Predictive
pilots supply gameplay buttons; no stunt results or player lives are injected.
This is automated native acceptance, not a human or original-game comparison.

The first expanded run found a Roof animation wait left active after balloon
contact. The missing reset from the original 3d15 helper was implemented and
covered by balloon/rope collision regressions. All three campaigns pass after
that correction. The unrelated Air crash reproducer was subsequently fixed
with deferred recovery; see [the recovery analysis](AIR_RECOVERY.md) for the
deliberate native behavior difference and remaining reference requirement.

Both preview archive manifests and file hashes have been verified. The default
archive excludes ROM and asset packages; its bundled extraction was run from
the local original ROM and the resulting executable passed the Windows test.
The first package check caught a missing analyze_audio.py dependency, which
was added before repeating extraction successfully. Local-asset archives stay
under ignored dist/ and are not uploaded.

Original-reference search located a Game Boy manual listing on GamesDatabase,
another on videogamemanual.com, and World of Longplays' Game Boy recordings.
The manual URLs failed to open in the retrieval tool. These are candidates,
not completed comparisons or proof of original-hardware capture. No image or
audio parity result is claimed from search snippets.

The dynamic-sprite transfer audit found two alternating buffers, not ordinary
in-place replacement of the visible player. Every nonempty descriptor fits its
buffer. The native renderer now retains that resource state and uses it for all
dynamic entities. This fixes Roof's three descriptor-free body-part layouts,
which share the five-chunk landing upload. Tests cover progressive and replaced
uploads, bank-tail retention, prepared pixel snapshots and actual landing data.
This narrows the partial-tile question; it does not replace matched original
captures or establish exact scanline timing. The Air crash deadline is unchanged;
the subsequent recovery-request safeguard is documented separately.

## Air source-clock checkpoint, 2026-10-05

Nine control-verified original Air cases match 28,103 completed native updates,
28,153 display services and all 168,618 semantic work phases/entry counters. Two
independent sprite captures match 158,840 published slots for presence,
coordinates and flags. The winning case reaches result 3 with ten items and
validates 35 WallSlide and 128 FinishMotion calls. A final-step particle error
is corrected. Music-request replays match 5,441 services and 32,646 voice rows.
No original per-update clock, cost, voice state or world outcome drives these
ordinary-clock native replays. Initial phase and update-aligned buttons are
supplied; this is an experimental probe, not accepted Windows scheduling.

Full native suites and all three campaigns pass after the gameplay corrections;
72 Python tests and 89 synthetic source-work checks pass. Remaining acceptance
items in the table are unchanged: missing handlers/interrupt ownership, actual
input/pause/exit and Windows integration, other stunts, matched pixels/PCM,
human and independent-host testing, and final packaging. Do not mark this final.

## Pause and display-input checkpoint, 2026-10-05

Three control-verified original pause cases validate 418 paused display services,
12 source copy bodies and 418 outer waits. Game state/timer/RNG stay frozen while
the shared counter continues. Native pause counter/input continuity and effect
setup ordering are corrected; all five stunts pass standalone counter-wrap and
campaign pause regressions. Three isolated music replays match 6,922 complete
services/41,532 selected voice rows, including the disabled-driver calls.
Partial final services are excluded and explicitly labeled.

All nine experimental clock cases now use per-display held-button samples,
without original per-update counters/buttons or recorded fresh edges. Previous
state/service/phase/sprite comparisons still pass; separate captures additionally
verify 3,971 held/fresh samples. This narrows the input requirement but does not
establish physical input microtiming or Windows scheduler integration. Native
pause entry/copy/return ownership, unknown/interrupted Air work and exit/startup
remain open. See AIR_PAUSE.md for methods and limits.

Full native suites and all three campaigns pass after these gameplay/audio
changes. Latest standalone checks pass 82 Python and 92 synthetic source-work
tests. The rebuilt EXE passes 13 normal and 14 real audio-open-failure automated
Windows checks. Human play/device removal/independent-host tests and the other
original-reference, pixel/audio and distribution requirements remain open.

## Explosion and wait-snapshot checkpoint, 2026-10-05

Ten original Air cases now match 30,180 ordinary-clock updates, 30,258 services
and 181,080 source phases. Three sprite/input cases match 243,040 slots and
6,076 held/fresh samples. The new case validates Exploding/Return work and a
wait with an interrupt before the counter snapshot; all previous cases still
pass after the correction. A separate outer-loop measurement confirms that
ownership and marks its incomplete final interrupt explicitly.

Latest validation passes 84 Python and 99 synthetic source-work tests, a new
Windows build and 13 automated UI checks. Earlier full campaigns followed the
last gameplay/audio change and remain applicable; this accounting-only update
does not repeat them. The acceptance gaps above remain open. In particular,
this does not integrate the candidate clock into production or certify human,
independent-host, original pixel/PCM or final distribution behavior.

## Final gameplay display wait - 2026-10-05

The ordinary-clock probe can now continue through 0400's final display wait,
stopping at 0403 before audio stop and the outgoing fade. The original leaves
FFAE clear throughout this wait; the native callback therefore retains the busy
resource gate rather than enabling an extra graphics upload. It continues HUD,
display counter, button sampling and music services without another game update.

Three new control-verified recordings extend existing input-only paths by two
hardware frames after the result: damage/explosion, successful finish and
normal-difficulty timeout. The native final wait matches original entry/exit
counters, elapsed cycles, one complete display service and the retained gate in
all three cases. The measured durations differ (47,740 / 31,940 / 58,636 cycles);
they are comparison targets, never native delays. State, phase and service
comparisons continue to match across the 8,417 repeated gameplay updates and
8,476 services including these waits. The damage case additionally matches all
84,240 sprite slots and 2,106 independently recorded held/fresh samples through
the final service. These are extensions of three of the ten cases, not three
new independent gameplay paths.

Reference tools now allow a bounded post-result recording and compare the final
wait explicitly. Missing boundaries, changed controls, enabled resource gates
and incomplete final intervals are rejected. Latest validation passes 87 Python
and 100 synthetic source-work tests. The existing 13-check Windows UI run passed
after the accounting-only change; no new production scheduling behavior is
claimed. Evidence stays under ignored local/air-final-{wait,win,timeout}-*.

Audio stop at 0403, outgoing fade/result setup and normal UI startup are still
outside this clock's accepted scope. Pause LCD polling, interrupted entity/
resource/row ownership, production integration, other stunts, matched pixels/PCM
and human/independent Windows tests remain required by ACCEPTANCE.md. The
complete port and final distribution are not accepted.

## Outgoing fade and terminal sprite publication - 2026-10-05

Three control-verified recordings extend the existing success, damage/explosion
and timeout paths through the complete outgoing fade. All 222 semantic phases
match: audio-stop work, fade entry, 24 palette writes, 96 waits and their tails.
All 96 display services separately match source component costs and native
HUD/bar, held inputs, effects and disabled music. Separate input captures match
8,572 held/fresh samples through the 8,417 repeated gameplay updates and exit.
These extend three of the ten existing cases; they do not add independent
normal-play coverage. See AIR_EXIT.md for method, reproduction and limits.

The production Windows outro now publishes the sprite list prepared by the
terminal update. Previously it retained the preceding visible list. All-five-
stunt marker regressions confirm publication while entities, gameplay timer
and pending resource transfers stay unchanged. This fixes a display boundary,
not the production scheduler or scanline pixel behavior.

Validation: 94 Python tests and 102 synthetic source-work checks; full native
suites, all 64 Air recovery phases, four input-only difficulty successes and
all three full campaigns pass. Air passes 819,624 assertions and audio 150.
The rebuilt Windows EXE passes 13 automated normal and 14 actual audio-open-
failure UI checks. The ROM-free preview archive's 11 file hashes match its
manifest and its EXE matches the tested build. Bundled extraction succeeds in
a local folder containing spaces; both 13/14 UI variants then pass while
launched from a different working directory. The preview is labeled unfinished
and records its pre-commit dirty source identity. It contains no ROM/assets;
extracted data stays in the ignored local test folder. These checks use one
Windows host and synthetic messages, not human/device-removal acceptance.
No unchanged campaigns were repeated before this production presentation change.

The candidate clock now reaches 0409 after final wait, audio stop and outgoing
fade. Result-screen DI/setup, normal UI startup, native pause LCD polling,
unsupported interrupted entity/resource/row work and production integration
remain open. Original reset voice-state parity, matched pixels/PCM, other
stunts and human/independent Windows acceptance are still required. The private
repository and continuation automation remain active; no final release is made.

## Result-test interrupt boundary - 2026-10-05

A second input-only easy winning replay alternates steering every 16 updates
and reaches result 3 with 11 items after 2,621 updates. Its experimental clock
initially stopped after update 2,414. The original interrupt returned to 03fd:
it occurred in the result read/rotate/back-edge test, after all six gameplay
phases, while FFAE was still zero. It did not interrupt a figure's handler.
The probe now accepts this completed-state loop boundary. Unsupported entity,
resource and row ownership continues to reject; error messages include phase,
tick and service identifiers for accurate diagnosis.

The entire new replay matches 2,621 updates, 2,651 complete services, 15,726 work
phases/entry counters, 106,040 sprite slots and 2,651 independently captured
held/fresh samples. The terminal extra partial service is outside the native
comparison scope. Combined ordinary-gameplay evidence now comprises eleven
cases, 32,801 updates, 32,909 services and 196,806 phases; four sprite/input cases
cover 349,080 slots and 8,727 samples. The separate three final-wait/fade cases
remain extensions, not additional independent gameplay cases.

This is a probe/diagnostic change with a new original witness. The production
Windows build, full native/campaign tests, normal/failed-audio UI checks and
portable preview from the outgoing-fade checkpoint remain applicable; unchanged
campaigns were not repeated. Captures and logs remain ignored/local under
local/air-steer16-*. Production integration and the remaining ACCEPTANCE.md
requirements are still open. No final-release status is claimed.

## Independent original reference - 2026-10-05

The locally installed PyBoy reference uses a fixed LCD pixel-transfer duration,
which cannot establish original pause polling behavior. An independent official
SameBoy 1.0.3 reference (pinned source, open boot ROM, DMG-B model) is now set up
under ignored .tools/. It is used only for authorized original measurements;
no reference core, DLL, boot ROM or recording enters the port or preview.
See REFERENCE_BACKENDS.md for the hardware-source link and reproducible setup.

The first control-verified SameBoy normal-coast case independently matches
3,989 native ordinary-clock updates, 3,990 complete services, 23,934 source
phases/entry counters, 159,600 sprite slots and 3,990 held/fresh samples. This
repeats an existing scenario on another engine; the eleven earlier PyBoy cases
remain separately counted. All measurement runs preserve the uninstrumented
end-state control. A SameBoy pause recording validates four copies, 35 paused
services/waits and 34 frozen-world intervals. Its LCD poll counts are observed
comparison data, never native clock inputs; independent native polling work
remains required.

Backend, revision/model and independent recording provenance are now explicit;
mixed records are rejected. The separate reference adapter exposes read-only
observations and button inputs with unmodified save/load states. The official
source revision and library/boot identity are checked. Latest pure Python tests
pass 98 checks. Native code/build/three campaigns and both Windows/portable UI
variants remain unchanged from the fully tested outgoing-fade checkpoint, so
those suites were not repeated. The overall port is still incomplete.
