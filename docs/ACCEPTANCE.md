# Final release acceptance

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
