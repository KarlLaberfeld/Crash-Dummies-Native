# Project status â€” October 1, 2026

## Objective

Produce a faithful **native Windows** port of the supplied Game Boy release,
without CPU emulation or replacing the original rules with a loose remake.
Private repository: https://github.com/KarlLaberfeld/TICD-Recompilation

**The overall task is not complete.** The Windows executable is a development
build of Roof Jump, Air Bumper, Ski Slope, Bomb Factory and Cruise Missile, not a complete game.

Repository descriptions and documentation must be in English. The working
conversation remains in German. Continue development until the port is complete.

## Implemented

- Hash-validated local extraction and a static disassembly tool.
- Original roof backgrounds, 69 sprite definitions, and four difficulty layouts.
- Native C++/Win32 application with keyboard controls, pause, and restart.
- Partial translation of roof physics, animation scripts, and object interactions.
- Compiler: `.tools/zig-x86_64-windows-0.16.0/zig.exe`.
- Build: `powershell -NoProfile -ExecutionPolicy Bypass -File ./build.ps1 -Test`.
- Local outputs: `build/CrashDummies.exe`, `build/crash.dat`, `build/air.dat`, and `build/ski.dat`, and `build/bomb.dat`.
- Source and documentation published to the private GitHub repository.
- Windows x64 GUI executable verified as PE subsystem 2 (no console window).

## Resume after usage reset â€” September 29, from 16:59 Europe/Berlin

The chat history records usage-limit failures at 14:07, 15:05, and 16:07.
Normal usage was available on resuming, with 5% of the five-hour window used.
No reset credit was consumed.

Reconstructed and corrected:

- Sprite origins and mirror centers from the original renderer, aligning
  graphics with collision positions. Current roof asset format: `TICDNAT4`.
- Visibility bounds, object respawning, and permanent target collection.
- Plane/balloon activation after the flyover and jump-input ordering.
- Upward awning collisions, plane stun, and simultaneous posture input.
- Original landing/body-piece animation, head-first impact, delayed results,
  and distinctions between success, perfect results, and insufficient breaks.
- Original HUD with four score digits, time, height bar, and gradual field updates.
- Original alternating cloud motion.

Validation: 11 Python tests and 48,863 native assertions passed. All four roof
layouts reach a terminal result without invalid animation commands. The count
includes repeated invariants, not that many independent test cases. Window-start
and image-capture checks passed. This is static source-derived validation,
not a demonstration of complete fidelity.

Published roof checkpoint: `763317baa9692388e2240a9f47bc9e9496284d1b`.

## Air Bumper work in progress

`tools/extract_air.py` now reconstructs the four maps, original graphics,
collision probes, speed/tilt tables, object definitions, and animation graphs.
The local output is `build/air.dat` (`TICDAIR3`). Native integration is now in
`src/air.h` and `src/air.cpp`, selectable with F2 (F1 returns to Roof Jump).
The implementation includes intro/countdown, movement and camera, six terrain
probes, collision response, pickups, breakable objects, damage, crash/return
states, finish gates, animations and the original gradual HUD updates.

The usage limit reset before the 23:06 Europe/Berlin heartbeat; normal usage
was available at 0%. No reset credit was consumed. Development resumed in the
same project. English README, notes and status were published in commit
`7ec557af391696c1184248c302d3369948db2815` before this continuation.

Validation: 15 Python tests, 48,863 roof assertions, and 449,064 Air assertions
passed. The assertion totals include repeated replay invariants, not independent
test cases. Twelve Air replays (three input patterns per difficulty) reach valid
terminal results. The easy steering replay reaches a successful gate result with eight items;
other runs end with insufficient quota, timeout or damage failure. These are not successful complete-game runs
or a proof of equivalence. Native window-start and frame-capture checks passed.

Original asynchronous sprite transfers are now modeled in both implemented
stunts, including map-row priority and animation waits. Remaining Air differences
include original sprite capacity/priority, exact palette/frame phase and
menu-seeded randomness; reference timing still needs validation.
The development selector and result overlay are temporary, not original menus.
Original audio and campaign/life integration are absent.

| Difficulty | Map rows | Objects | Seconds | Quota |
|---|---:|---:|---:|---:|
| Easy | 184 | 78 | 40 | 14 |
| Normal | 236 | 131 | 60 | 15 |
| Hard | 256 | 143 | 70 | 24 |
| Very hard | 256 | 143 | 70 | 16 |

## Remaining work

1. Validate and refine Air Bumper's original timing and edge cases, including
   reference timing and successful runs beyond the easy steering replay.
2. Continue roof fidelity checks: animation transfer timing, lifecycle,
   plane/balloon/rope interactions, and landing. See `REVERSE_ENGINEERING.md`.
3. Validate Ski Slope, Bomb Factory and Cruise Missile with successful natural playthroughs.
4. Complete presentation timing, high-score entry, and original music/sound.
5. Validate full playthroughs and fidelity, then prepare a portable distribution.

## Automatic continuation

The user explicitly requested automatic resumption after a usage-limit reset.
The active chat automation is `crash-dummies-nach-limit-reset-fortsetzen`,
scheduled hourly at minute 05. After a limit interruption, continue in this
project and chat. Keep ROMs and extracted assets local. Update this status
before ending a work session. Disable the automation only when the complete
port is finished. Do not create additional chats.

Native Air Bumper checkpoint published as `d3dcccae0379871a94aa45b6712847855312efb3`.
Later local work reconstructs resource-transfer timing and begins Ski Slope.


## Ski Slope native integration — latest continuation

Ski Slope is now selectable with F3. The local data package is `ski.dat`
(`TICDSKI1`); extractor `tools/extract_ski.py`, native code `src/ski.*`,
tests `tests/ski_tests.cpp`. All four layouts are reconstructed: rows
120/108/152/200, objects 52/58/77/124, flags 30/22/41/31, time 80/80/90/90.
Implemented: turning/straightening animations, velocity approach, jump/shadow,
terrain and object collisions, flags, crash/return, finish-zone depth and quota,
seven-column HUD cycle, native sprite-resource transfer queue. Window startup
and capture pass. All 15 Python tests and native suites pass: roof 48,863,
Air 449,064, Ski 297,291 assertions (mostly replay invariants). Twelve Ski
replays terminate in collision failure; successful Ski runs remain unverified.
Bomb Factory, Cruise Missile, original menus/campaign/ending/audio and full
fidelity checks still remain. The complete port is NOT finished.

Last usage check: 99% of the five-hour window used; reset timestamp 1790734021.
Keep the existing automatic continuation active. Resume from this checkpoint,
validate Ski edge cases and successful traversal, then reconstruct Bomb Factory
(initialization 00:0fce, player kind 45, handler 01:6ef2). Do not create chats.
Graphics-queue checkpoint on GitHub: 7b262277afb73cd64829db17b12f5f353dce34d1.

The September 30, 03:06 UTC heartbeat found normal usage available (5% used).
Development resumed without consuming a reset credit. The previous Ski upload
had failed before its commit was created; local source and tested build survived.

## Bomb Factory native integration - September 30

Ski checkpoint is published as `db6107646cd89afc79ad8f815501156084cc41d8`.
Bomb Factory is selectable with F4. The extractor reads the fixed room,
33 sprite frames, four original spawn distributions, and six animation graphs.
The native implementation includes three belt speeds, six spawn markers,
press-edge lane changes, frame-transfer-gated positioning, walking, defusing,
punching, bomb falling/explosion, bonuses, quota and failure/perfect results.
Animation callbacks are decoded through an explicit allowlist into native
collision events; no cartridge instruction execution has been added.

The native Bomb suite passes 407,564 assertions (mostly replay invariants).
Twelve replays end in belt-loss failure; successful natural play remains
unverified. Synthetic tests cover success thresholds separately. Frame capture
shows the original room and actors. Menu-derived random seed/frame phase,
sprite hardware priorities and exact original timing remain open. Continue
with Cruise Missile (00:1245, kind 57, 01:73ed), then original menus, campaign,
ending, audio and fidelity validation. The complete port remains unfinished.
Keep automatic continuation active.

## Cruise Missile native integration - latest checkpoint

Bomb Factory was published as `7911ece7e42c2095ecab6dceb3d6a6403cc8ecb4`.
Cruise Missile is now selectable with F5. Local `cruise.dat` (`TICDCRU1`)
contains the original column-major 128-by-16 map, 42 frames, and four object
lists (13/27/34/38 entries). Native logic includes launch/ignition, sixteen
headings, thrust and gravity, camera/terrain probes, magnets, rockets,
projectiles, spring hazards, extra lives, target success and failure states.
All native suites pass; Cruise adds 297,036 assertions, mostly replay invariants.
Its twelve input-pattern replays fail on collisions; synthetic target tests
exercise both successful endings. A successful natural course remains unverified.
Capture shows the original map and missile. The complete port is NOT finished.

Next: audit original byte-wrapped collision rectangles across stunts; implement
original menus, campaign/lives/score/results, ending and native audio. Validate
natural playthroughs and timing. Cruise currently returns blank terrain outside
the declared map instead of interpreting adjacent original RAM. Shared remaining
differences include sprite hardware limits, palette phase, menu-seeded randomness
and the development selector. Keep the automatic continuation active.

## Collision audit, campaign rules and title assets - latest work

Cruise checkpoint published: `4e265f254a6e9aee26d0f1fbb3f30f51aad45f84`.
All five stunts now share the original byte-wrapped, unsigned collision rectangle
comparisons (00:1747/1834); quantization and asymmetric edge contact have targeted
regressions. Native Roof now passes 48,868 assertions; other stunt totals are
unchanged. All 18 Python tests and 59 new campaign-rule assertions pass.

`src/campaign.h` reconstructs the outer loop, but is NOT connected to interactive
play yet: five starting lives, independent alternating players, failed-attempt
pay discarded, successful pay and time transferred into six-digit savings,
perfect doubling, Bomb time-bonus suppression, five days per difficulty, and
ending after the twentieth successful stunt. Extra lives apply on failed runs too.
`tools/extract_ui.py` and `src/ui.*` reconstruct the six stationary title pages,
original font, default high scores and options pointer. `ui.dat` stays local.
`--capture` now writes title-0.bmp through title-5.bmp using the native renderer.
The interactive executable STILL uses its development stunt selector.

Next integration work: connect campaign state, original title/options and stage
instruction/result screens to the Windows application. Preserve actual original
flow rather than inventing a replacement menu. Title transition scrolling and
raster phase remain unported. Then high-score entry, ending and native audio.
Continue natural-play and frame/timing fidelity validation; the port is unfinished.
All source/docs stay English; original data stay excluded. Automation stays active.

Latest source checkpoint: `46b6218383f87aed9dd0f5b19fd48652b4b12b6e`.
A final palette audit found that composite sprites still used raw color indices.
They now apply the original OBP0=0xc4 / OBP1=0xe0 mappings (00:210b/20fa),
including opaque white pixels; title pointer uses OBP0. Fade phases and OAM
capacity/priority remain open. Regenerate all local packages when rebuilding.


## Interactive campaign presentation - September 30 continuation

The default application now opens the original title page. Tab maps Select;
Enter maps Start. Original options select one or two players. Instructions,
all five stunts, result screens, alternating players and the ending are wired
through the native campaign model. F1-F5 retains standalone stunt testing;
F6 abandons that session/campaign and returns to title. R and 1-4 are limited
to the development mode. `ui.dat` now requires `TICDUI02`; rebuild all assets.

Original instruction portraits, headers, text, player-name and quota macros,
five-frame glyph delay and 1/2/3/1/1 two-frame scroll steps are reconstructed.
Result portraits and sixteen success/failure message variants come from the
ROM. Ending graphics/text are extracted locally. Source includes no ROM data.
The sprite-palette correction from the preceding checkpoint is included.

Validation: 18 Python tests and all prior stunt suites pass, alongside 59
campaign assertions and 206 UI assertions. UI tests cover both players, all
forty instruction variants, input edges, exact text/scroll waits, synthetic
20-stunt progression and five-life failure. Hidden Windows startup and native
capture succeed; instruction/result/ending images were inspected locally.
These are not successful natural full-game runs or proof of original fidelity.

Remaining: result money-count animation (currently immediate), high-score name
entry, original page transitions/fades and frame phase, audio, global random
seed/timer continuity, hardware sprite limits/priority and natural playthrough
validation. The full port remains unfinished; keep the continuation active.


## High scores, count-up and shared timing - latest checkpoint

Interactive campaign source was published as
`4c354b6c3a5690b33c58b79707cec91e815eb1fb` (local `474366c`).
The next working build adds original name entry with session high-score ranking,
three-character limit, scrolling alphabet, backspace/end symbols and both player
headers. Equal scores insert before existing ties. Game-over/ending waits lead
to name entry only for qualifying scores, then the remaining player or title.
F6 returns to title without clearing the in-memory table. Format: `TICDUI03`.

Result pay/time now counts into displayed savings, including perfect doubling,
Bomb time suppression, original row delays and skip input. Campaign money is
committed exactly once. The stage timer remainder survives stage changes and
random seeds now depend on the native global frame. Full original frame phase
is still unverified because fades/transitions remain absent.

Validation: 18 Python tests, all five unchanged native stunt suites, 59 campaign
assertions and 224 UI assertions pass. Native capture and hidden window smoke
checks passed; the high-score input image was inspected. Counts include replay
invariants and synthetic outcomes; no full successful natural playthrough is
claimed. All source/docs are English; generated original data stay local.

Next: original sound/music reconstruction, page/fade transitions and phase
validation, hardware sprite priority/capacity, and successful natural runs across
all difficulties. The complete port is still unfinished. Keep automation active.


## Title transitions and audio analysis - latest local work

High-score/count-up checkpoint published as
`9798a80f7e67ff6ed8e7d2465b79bbaf1ba08602` (local `c5b0ced`).
Title/options page changes now close/open in the original 40+40 updates, swapping
text while closed and retaining the intermediate dummy artwork. The new page's
hold timer begins after opening. 227 native UI assertions pass; transition image
capture was inspected. Initial boot/fades and hidden password screen remain open.

Added `tools/analyze_audio.py`: explicit decoding of all 14 four-channel music
tracks and all 26 sound effects (29 active streams), with notes, duration mode,
loops/calls and instrument references. It executes no cartridge CPU instructions.
Generated report stays in `local/`. Four additional Python tests (22 total) pass.
This is analysis infrastructure only: the Windows executable STILL HAS NO AUDIO.
Next reconstruct native envelopes/modulation and pulse/wave/noise synthesis,
then attach music/effect playback to the original events. Preserve channel
priority when effects override music. All remaining fidelity work above applies.

## Successful input replays and campaign fixes - September 30

Previous source checkpoint: `3f20d0301a662b9db241ff652ca6d890378f2a5f`
(local `18b67b6`). Usage was available after the reset; continuation resumed
without requesting or consuming a reset credit through an agent action.

New native test controllers complete all four difficulties of Ski Slope, Bomb
Factory and Cruise Missile. Actual runs receive only ordinary button inputs;
recorded inputs replay successfully from fresh zero-seed starts. Controllers use
native state and forecast copies, so this demonstrates reachable successful
outcomes, not human playability, original equivalence or full campaign completion.
Ski successes take 1642/1623/2166/3120 ticks; Bomb 3481/3617/4253/4108;
Cruise 2113/1780/1912/1893. All difficulty quotas are satisfied.

Fixed the campaign adapter for Roof Jump: its development result numbers are
not original bit flags. Timeout/fire could previously leave the transition
waiting, and insufficient breaks could be misclassified. The adapter now waits
for completion and returns the separate original result flags. All five stunt
HUDs now display the current player rather than always player 1.

Validation: 22 Python tests; native Roof 48,879, Air 449,065, Ski 297,304,
Bomb 407,577, Cruise 297,049, campaign 59 and UI 227 assertions pass. Large
counts include repeated replay invariants. Native capture and hidden Windows
startup pass. No cartridge or generated original data are published.

Next: successful Roof/Air inputs across all difficulties, native music/effects,
initial boot/fades and exact global frame phase, sprite hardware rules and
original-reference validation. Audio is still absent; the complete port is
unfinished. The continuation automation remains active.


## All twenty stunt variants and native campaign completion - latest checkpoint

Previous published checkpoint: `7a9c8ff86f7c83f47cd0167d835b9f7b6e34a231`
(tree `d68a08c0d794d83ad7e856109d83b300fc5f4bb2`, local `03cc4af`).
Roof and Air now also have successful input-only tests on all four difficulties,
including fresh recorded-input replay. Roof ticks: 1848/1713/1887/1921;
Air: 2628/2401/2737/2657. Roof actual result flags also settle successfully
through the campaign model. Counts: Roof 48,895; Air 449,077; other suites
unchanged. All 22 Python tests pass; build has no compiler warnings.

New `tests/playthrough_tests.cpp` runs the native campaign through twenty actual
successful stunts, carrying timer remainder and menu-derived random seeds.
It reaches Ending with savings 7,875 in 49,007 native global updates; no failed
attempts. Instructions and result counting are skipped with inputs. The harness
inserts one UI tick between starting a stage and its first gameplay update, so
it is a model integration check, not an exact Windows input/timing replay or an
original-game reference. Pilots inspect state and forecast copies but modify
actual stunt state only through button inputs. Included in `build.ps1 -Test`.

Open Air issue discovered by broader exploration: normal difficulty with
`A | (((tick+24)/24)%2 ? Left : Right)` can remain in Animation after a crash
(frame 5, animDone true, no timer updates). Local reproduction:
`local/air_stuck.cpp` / `local/air-stuck.txt`. At 01:6307 the ROM installs the
Animation handler and conditionally starts 6315 via 00:3b84; the native version
also rejects the follow-up if the preceding animation is still busy. Do not
force-start or clamp the return position speculatively. Audit original transfer/
animation timing and confirm a reference trace before changing this behavior.
The actual hidden return at 6336 compares full coordinates and moves +/-16.

At checkpoint preparation, ordinary usage was allowed with 94% of the five-hour
window consumed, 15% weekly. No reset credit was invoked. Keep continuation
active. Next priority: native audio sequencing/synthesis/event wiring, then
remaining fades/boot, sprite limits/priority and timing/reference validation.
The executable is still silent and the port remains unfinished.


## Native music and sound output - September 30, 17:00 continuation

The five-hour limit reset; the resuming check showed 0% used, weekly 16%.
No reset credit was invoked. Previous published source:
`4871891e7837a83ca76757782b785fcbaeac727e` (local `93513cc`),
tree `55985b62b527475e70d4e39183a71c7c6dfb5449`.

The executable is no longer silent. `tools/extract_audio.py` creates local-only
`audio.dat` (`TICDAUD1`, 53,021 bytes): 5,335 identified music commands, seven
instrument envelopes, two wave tables, resolved frequency lookup values and
song/effect roots. No CPU code or cartridge memory bus is used at runtime.
`src/audio.*` translates the music data language, six software voices, original
software envelope/modulation state, and pulse/wave/noise sound generation.
`src/windows_audio.h` submits stereo PCM through the Windows audio device.

Title, instructions, all five stunts, success/perfect/failure, game-over/ending
and name-entry music are connected. Animation sound commands and the identified
landing, impact, break, pickup, jump, explosion and launch calls now queue their
original effect IDs. Same-update calls preserve the original last-request-wins
slot. Effects override pulse 1/noise output while underlying music advances.
Name entry queues add/delete/end effects. Development restart restarts music.

Validation: 23 Python tests; 109 native audio assertions; all five stunt suites,
UI/campaign tests and the complete 20-win campaign harness pass. Native counts:
Roof 48,896; Air 449,078; Ski 297,304; Bomb 407,578; Cruise 297,049; campaign 59;
UI 227. All 14 songs run 12,000 updates without an unknown command; all 26
effects terminate. Title PCM is nonzero and its fractional sample count matches
the original frame cadence. A hidden Windows output run over 300 updates reports
an available device and zero dropped buffers. Generated previews stay local.

This is an initial native sound implementation, NOT verified waveform fidelity.
Driver writes are currently coalesced at video-update boundaries; exact
intra-update register timing, low timer bits, hardware envelope quirks and DMG
wave-RAM behavior have not been matched. Noise attack transition edge cases,
rare modulation carry behavior, UI fade/audio phase and any remaining effect
call sites still need comparison. Optional register-list/stereo-motion commands
are rejected; they do not occur in the identified original streams. No human
listening/reference capture equivalence is claimed.

The Air animation stall, boot/fades, hidden password page, global event phase,
OAM limits/priority and broader original-reference checks remain open. Keep the
continuation automation active; the full port is still unfinished.


## Audio publication and Air crash trace follow-up

Published audio source: `fb98d46dd4aa83a098478ca78fdd37c28b35292c`,
tree `e4bdc7d5daa3899c5a6ca33282d478799343fda0`, local `e199b8d`.
A fresh extraction/build/test run passed all 23 Python tests and all native
suites without compiler warnings. The rebuilt executable's 300-update Windows
audio test again exited successfully with an available device and zero drops.
ROM, extracted packages, PCM previews and diagnostic traces remain ignored/local.

The normal-difficulty Air stall is now narrowed to a one-update boundary in
this native trace. `local/air_crash_trace.cpp` records the second crash at input
index 1955. At index 2035 its 80-update crash counter expires, but the final
animation delay has only just reached zero; the end command runs one update
later. The original conditional start at 01:6312 -> 00:3b84 therefore rejects
animation 6315 in the native state, leaving the generic animation handler idle.
Frame transfers in this crash cost 3/3/3/3 updates; map-row work delays the
second and fourth transfer. Original 00:0c42 explicitly gives that work priority.
The copied animation periods (0, 8, 52, 4), delay countdown branch at 00:3bbd,
and conditional animation start were rechecked against static disassembly.
This identifies the race but does not yet prove a native timing error versus
an original-game edge case. Do not force the follow-up animation or alter
return coordinates without further evidence. Next audit: global frame phase,
map-row scheduling and the original resource-transfer completion boundary.


## Gameplay sprite limits and priority - September 30, 22:07 continuation

The limit reset; initial usage was 1% primary, 31% weekly. Previous published
checkpoint: `0946738df942d23ecc51616c213b789aa995e9ac`, tree
`53e965413a7f81555ba9c52d39845b500cb25258`, local `bf86c78`.

All five gameplay renderers now preserve ordered 8x16 pieces and raw colors,
rather than layering complete flattened images. Implemented: original signed
piece placement and flips, attribute XOR, alternating slot direction, forty
visible slots, first-ten vertical selection per row, X/slot overlap priority,
and background masking after object priority. White-mapped nonzero colors
remain opaque. Sprite list construction occurs at the simulation visibility
pass; capacity also stops later visibility/removal work. Repaint uses that
stored list, so newly scanned placements wait until the next pass.

Regenerate local packages: Roof/Air/Ski/Bomb/Cruise versions are now
TICDNAT5/TICDAIR4/TICDSKI2/TICDBOM2/TICDCRU2. There are still seven runtime
packages; original/composite/piece data remain local. Source and docs only
may be committed/uploaded.

Validation: 24 Python tests, 23 native sprite assertions and four new native
visibility/publication assertions. All prior stunt/UI/audio/campaign tests
pass without compiler warnings. Roof now has 48,900 assertions; other counts
remain unchanged. The 20-win campaign still reaches Ending with savings 7,875
at global update 49,007. Local captures for all five stunts were inspected.
No original screenshot equivalence is claimed.

The Air crash's map-row-priority and conditional animation branches were
rechecked, with no new justified correction. Its 80-update/animation boundary
remains unresolved. Also open: exact slot/display phase and transfer latency,
boot/fades, hidden password page, audio edge cases, and broader original
reference validation. The port remains unfinished; keep continuation active.


## Copyright screen and initial title transition

Sprite checkpoint published as `aa89ba4e2dd8a22a1d59a6bfd48d24f4a49813a9`,
tree `018ecc3fc2500fb9806b6b034427435e4c33b1b9`, local `5591ac4`.

Normal Windows startup now shows the ROM's copyright screen with the original
eight palette steps (four updates each), fixed 180-update hold and fade-out.
The first title appearance then fades in, waits once, changes to title music,
closes its blank/dummy center, installs page zero and opens it. Music continues
across phase boundaries until the identified song change. These opening phases
do not accept Start; a held button must be released before it can start play.
`ui.dat` is now TICDUI04 and must be regenerated.

A full extraction/build/test run passed: 24 Python tests, UI assertions now
237, all prior game/audio/sprite suites and the twenty-win campaign unchanged.
Both new opening captures were inspected locally. Windows audio ran through
300 opening updates with an available device, zero dropped buffers and exit 0.
Power-on/LCD alignment and remaining menu/game/result fades are still unverified.
The isolated campaign harness intentionally skips boot and is not a wall-clock
reference. The Air stall and other documented fidelity gaps remain open.


## Shared frame phase - final checkpoint for this continuation

Opening checkpoint published as `93a3721de3ee446ec77206785ac12b59efe210de`,
tree `b9583587c57b621d32de065e9b9cb1bf08285f54`, local `2845dea`.
Campaign gameplay now uses the UI's continuing C00A/B-equivalent frame value,
including time spent in menus and pauses. Individual stunt counters wrap at
16 bits; isolated development/tests still start at zero. Sprite slot direction
now has its own toggle per visibility pass, as in 1bfb, rather than using the
global counter parity.

All 24 Python tests and native suites pass. Roof assertions: 48,901; Air:
449,081; UI: 237; sprite: 23; audio: 109; other suite counts unchanged. The
old easy-Air test schedule failed when its zero-phase assumption was removed.
The test pilot now forecasts alternating ordinary-input schedules on copies at
the actual starting phase; the measured run receives only buttons. The shared
frame campaign passes with 20 wins in 23 attempts (three failed attempts),
savings 8,221, global update 62,605. This replaces the zero-phase campaign's
49,007/7,875 checkpoint result, not the independent per-stunt replay evidence.

Missing lifecycle/fade/setup waits still change phase relative to an original
power-on run. Air's crash-animation boundary remains unresolved. Next work:
remaining inter-screen fades, hidden password/music-test page, exact frame and
audio phase/reference comparison. The native Windows port is not complete.
Continue after the next usage reset; no reset credit was used.

## Hidden password entry and music test

The shared-frame checkpoint is now published as
`c015b872aba7f29a8e00d6192e1533c507f139be`, tree
`2d57588eb48afc343c97985e1c9fdc884bb755ef`, local `ee67de3`.
The previous upload was deferred because automatic approval review reached
its usage limit; retry after the reset succeeded. No reset credit was used.

Reconstructed the original Up/Down/Left/Right unlock on stationary title
pages, eight-digit password editing, fixed feedback hold, and all ten actions:
five starting stunts, four difficulties and the music test. Both campaign
players inherit the selected starting settings. Start returns to title after
submission; A/B returns to fresh entry. Music-test exit preserves that choice.
The original center close/open transitions and the password music wait are
modeled. Digit sequences and four page maps remain local in TICDUI05.

Music test wraps over all 14 tunes and 26 effects. Its displayed counters
are hexadecimal, following the original nibble renderer. A starts the chosen
tune or, when that same tune still has active music voices, queues the effect.
B stops all playback. Explicit audio stop now clears queued effects as well.
The host passes actual music voice activity to the menu state machine.

Validation: 25 Python tests, 313 native UI assertions, 112 audio assertions;
all prior stunt/campaign/sprite suites pass with no compiler warnings. The
shared-frame campaign still reaches 20 wins in 23 attempts, savings 8,221,
update 62,605. Password and music-test captures were inspected locally.
These are source-derived and synthetic checks, not original-machine reference
comparisons. ROM data and generated captures/packages are not uploaded.

The port remains incomplete. Remaining work includes other lifecycle fades
and setup waits, the Air crash-animation boundary, detailed audio behavior and
reference validation of frame/display phase. Keep automatic continuation active.

## Original pause display and suspended audio

Password/music-test checkpoint: remote
`f817a85bb164edd23fc95c662d0e2e071ce68d2d`, tree
`5015db53ef351b0d350c1d459b426f5ba3fb4964`, local `77e8265`.

Campaign pause now replaces only the bottom eight-pixel HUD strip with the
original PAUSE!! graphics. The playfield remains visible and unchanged;
the previous central help box is retained only in development mode. TICDUI06
adds the locally extracted 160x8 strip, so regenerate ui.dat.

Audio no longer keeps sequencing during a paused stunt. Software voices,
note durations, envelopes and pending effects remain suspended. Output
channels are cleared on entry, reflecting the original power-off; wave data
remain intact, but the wave DAC/volume require subsequent music commands.
The Windows queue is cleared at pause/resume so buffered sound or silence
does not delay the audible transition. The global UI frame counter continues.

Validation: all 25 Python tests and the native suites pass. Roof has 48,903
assertions, UI 315, audio 122; other counts unchanged. The campaign remains
20 wins in 23 attempts, savings 8,221, update 62,605. A local Windows audio
smoke test ran 210 output updates with 90 paused: device available, no dropped
buffers, silent pause, and 120 advancing driver updates. The pause capture
was inspected. Build logs: local/pause-build.log and local/pause-final-build.log.

This establishes the reconstructed pause control/display behavior, not exact
hardware audio recovery or sample equivalence. Pulse/noise retrigger timing,
remaining lifecycle fades and setup waits, Air's crash-animation stall and
original reference comparison remain open. Continue development; the port is
not complete and automatic continuation remains active.

## Options input ordering

Pause checkpoint published as `83e24f232e5e9d29b6eaae7b03061960536294d1`,
tree `63ffb16c5a0c4086c7c25a670954e0a746930a9b`, local `06302f9`.
A further source check at 00:278f-279a found that the original toggles player
selection before processing Start. The native options page now does the same
when both arrive in one update. Multiple selection buttons still toggle only
once; directions outside options do not alter the player count.

The Windows EXE was rebuilt. All 318 UI assertions pass, including three
new simultaneous-input cases (local/options-ui-test.txt). Gameplay/audio code
is unchanged; the prior full campaign/audio validation remains applicable.
No completion claim: lifecycle transitions, exact phase/audio comparison and
the documented Air animation boundary remain open. Continue after usage reset
if interrupted; no reset credit was used.

## Asynchronous stunt-entry fade

Options-order checkpoint: remote `3f1324e0d5a1188c68070ce6645892bac157d256`,
tree `bfb3b82cdd340e996bbfbc5ee1b62ef0c560762b`, local `99393d4`.

The campaign now starts each stunt with the original eight-step fade from
white, advancing on even global frames while gameplay continues. Pause freezes
the fade but not the shared frame counter. The existing palette masks preserve
sprite white colors through the common final palette mapping. Developer-mode
previews retain their immediate full-color view. Asset format stays TICDUI06.

Validation: all 25 Python tests and native suites pass without compiler warnings.
UI assertions are now 341; other counts are unchanged. The campaign remains
20 wins in 23 attempts, savings 8,221, global update 62,605. Captures at initial,
eighth and sixteenth updates were inspected; these show the native progression,
not an original-machine comparison. Logs: local/gameplay-fade-build.log and
local/gameplay-fade-final-build.log.

Other lifecycle transitions still need reconstruction. Source review confirms
blocking 32-update instruction-out/result-in fades, a distinct 64-update later
instruction transition, and different result timeout origins. Do not simply
add 32 to every result timeout: success uses the background 600-update counter
initialized before fade-in, while ordinary failure waits 480 after fade-in.
Air's crash-animation boundary and detailed audio/display equivalence remain
unresolved. The port is still incomplete; automatic continuation stays active.

## Result fade-in and post-count timing

Gameplay-fade checkpoint: remote `95f922def644ec14c28a7f580fa9315b4e1de05f`,
tree `b6edfc56e4dfd9123851164a2cfadceea3fc910b`, local `7f948a2`.

Result screens now run the original blocking 32-update fade-in before pay
counting or input acceptance. A button held through that fade cannot become a
new skip press. Success retains the shared 600-update budget during fading
and counting, then adds 60 updates to the remaining budget. The original
background counter stops at one, so counting that exhausts the budget still
gets 61 updates before automatic continuation. Fresh action input can skip
that hold. Ordinary failure and game-over wait 480 updates after fading;
game-over still does not accept a skip.

All 25 Python tests and native suites pass. UI assertions: 352; other suite
counts unchanged. The added waits change the continuing event/random phase:
the current campaign reaches 20 wins in 22 attempts (two failed attempts),
savings 7,974, global update 59,899. This supersedes the earlier campaign phase
result without altering isolated stunt logic. Mid-fade and complete result
captures were inspected. Log: local/result-fade-build.log.

The pre-result gameplay fade-out/setup and some music/setup waits are still
missing, as are title/instruction and later screen transitions. Absolute
power-on phase and pixel/audio equivalence remain unverified. Air's documented
animation-boundary stall is unresolved. The port remains unfinished.


## Blocking instruction and stunt exits — October 1

Previous checkpoint: remote `2d3133fcfb77e3c45e5293f03c9e9a78bccea817`,
tree `1c06e00015e57dc240dbca4033aa06fbf4a9c5a0`, local `4e3fa9d`.

Instruction Start now freezes typing/scrolling, fades out over 32 updates,
and holds white for one further update before starting the stunt. The song
continues through that exit. Stunt termination now preserves the last native
playfield, waits once, stops music, and fades out over 32 updates before the
result screen. Failure and game-over add their original one-update wait
before result music/fade. Skip input cannot bypass these blocking transitions.
The asset format remains TICDUI06; no newly extracted data are required.

Review of the perfect-result initialization found another timing difference:
it installs a 720-update background budget, replacing the ordinary 600.
The subsequent sixty-update addition and retained-one rule remain unchanged.
Short perfect results therefore expire at result update 780, ordinary ones
at 660. The four celebration emitters initialized by the same original
routine are not yet rendered; this is a newly recorded presentation gap.

Validation: 25 Python tests and every native suite pass without compiler
warnings. UI now has 498 assertions; the other suite counts are unchanged.
The complete campaign reaches 20 wins in 23 attempts, savings 8,659, global
update 63,844. The new waits exposed weaknesses in the input-only test pilot:
its first run lost the last life after 19 wins. The final Cruise planner now
uses a wider/deeper forecast on the hardest level, as it already did on the
second level; no gameplay rules or live states were changed to obtain success.
The earlier UI test fixture also needed its odd-frame start corrected for the
new delay. Final passing log: local/stunt-transitions-final-build.log.
Instruction exit captures at updates 16 and 32 were inspected. These and the
unit image comparisons validate native output, not original-machine parity.

Continue with title/first-instruction and later map transitions, perfect-result
celebration, and the missing gameplay-loop/setup timing (including input edges
at stunt entry). Air's crash-animation boundary, pending graphics transfer
behavior around exits, and detailed audio/pixel equivalence remain unresolved.
The port is not finished. Automatic continuation remains active; no quota reset
credit was used. All original ROM/extracted assets/captures remain local.


## Input continuity, celebration and instruction transitions

Previous checkpoint: remote `9ef7f1de10ad398706cfb626aeda3bcd1f202fdf`,
tree `1ac71232802dcdf1263c01f6fd179529812f9fb3`, local `9179e30`.
Work resumed after the five-hour usage window reset; no reset credit was used.

The Windows host and campaign harness now share the same stunt stepping path.
Stunt setup waits for the next update, and global input history survives menus
and pause. A key held across either boundary is no longer synthesized as a new
press. Fresh presses still work. The asynchronous entry fade starts on the
first actual gameplay update. All five native stunt types exercise these cases.

Perfect results now animate the original four staggered celebration emitters,
using the original integer lookup tables, random-state continuation, byte
wrapping, 8x8 sprites and background/object priority. TICDUI07 adds 400 bytes
of local tables; ui.dat has been regenerated. Three celebration captures were
inspected. This closes the missing-animation item, with exact original display
publication phase still unverified.

Title Start now fades the existing page for 32 updates, waits once, and stops
its music. First instructions have their one setup wait and 32-update fade-in.
Later instructions wait once then alternate the outgoing background and new
instruction map over the original 64 pattern bits. Text/input processing stays
suspended during entry. A held Start does not interrupt typing; the separate
original held-input check after typing completes can then start instruction
exit. Tests cover that distinction as well as fresh presses. Outgoing result
celebration sprites are removed before map alternation.

Validation: full extraction, all 25 Python tests and every native suite passed
in local/instruction-alternation-build.log. The campaign reached all 20 wins in
20 attempts, savings 8,138, global update 52,671. This supersedes previous phase
results. A final isolated held-Start correction was rebuilt and verified with
all 619 UI assertions (local/presentation-final-build.log and
local/presentation-final-ui-test.txt); the campaign's button path is unchanged.
Other native suite counts remain unchanged. Title/first-instruction captures
were inspected, and the capture executable exited successfully. No compiler
warnings. ROM, extracted tables/packages and all captures remain local.

Air's crash-boundary audit again matched static animation/transfer routines,
but still lacks evidence to distinguish a port timing fault from an original
edge case. No speculative recovery was introduced. Remaining work includes
ending/name-entry/return-to-title transitions, exact graphics publication and
hardware/setup phase, original-reference behavior/audio comparisons, broader
human/Windows acceptance tests and the final distribution package. The port
is still incomplete; automatic continuation remains active.

## Ending and name-entry lifecycle checkpoint — 2026-10-01

Previous published checkpoint: remote
`aa7fd19b2adcda1652f4a52bc46076da8754d7fe`, tree
`5fdb157b78ecfa96d9f6dcdd8c3d676e494c237f`, local `03d517b`.
The initial ending/name-entry edits were interrupted before validation. Work
resumed with ordinary usage available (five-hour window reset, weekly usage
94% at the resumption check). No reset credit was used.

Ending now fades out the final result while its celebration keeps moving,
waits once during setup, fades in, and only then runs the original unskippable
480-update hold. Qualifying scores fade out either game-over or ending, then
fade in the name screen. Letter entry, scrolling and arrow blinking stay
blocked during those transitions; held buttons do not generate new presses.
The arrows start with their original tiles and toggle only in the active loop.

Finishing a name clears the alphabet strip and removes its raster effects and
arrows. The surviving player receives the instruction transition; otherwise
the screen fades out and the title opening runs again, preserving scores and
skipping copyright. Music changes follow the identified source call order,
including continued ending music for an unranked score and silence after name
entry until title music starts. No asset format or stunt rules changed.

Validation: build/CrashDummies.exe rebuilt without compiler warnings; all 25
Python tests and all native suites passed (local/ending-transitions-build.log).
UI assertions increased from 619 to 710. All other suite counts are unchanged.
The input-only campaign again reaches 20 wins in 20 attempts, savings 8,138,
global update 52,671 at the last stunt's finish; that harness stops on entry
to Ending, while the UI tests cover the new ending/high-score/return sequence.
Capture mode exited successfully and the ending/name/return contact sheet was
inspected locally. The Windows audio smoke test exited successfully with an
available output device and zero dropped buffers. None of these observations
establish full equivalence to the original game or replace human acceptance.

Remaining: resolve Air's reachable crash-animation stall using evidence;
verify graphics transfer/publication and hardware/setup phase; compare game,
image and audio behavior against original references; perform broader human,
two-player and Windows acceptance; prepare the final distribution package.
The major missing ending/name-entry/title-return transitions are implemented,
but exact hardware timing is still unverified. The port remains incomplete.
Automatic continuation stays active. ROM, assets and captures remain local.

## Air crash phase sweep — 2026-10-01

Latest published implementation: remote
`22c69769fed1019514e1352b1214467c2d55f6e1`, tree
`e0599e2be1afca56d5e0ed66d9adcfb6ed32eab7`, local `3e41734`.
Ordinary usage was available at this check; weekly usage was 98%. No reset
credit was used. The tested Windows build remains unchanged.

A new local diagnostic sweeps 64 initial global-update phases on Air's second
layout, using the same held-A / alternating-horizontal input (24-update runs)
and normal native state progression. It detects an inactive animation handler
with no terminal result. Twelve phases stall: 0, 4, 5, 21, 22, 27 and those six
plus 32. The other 52 reach terminal results within 12,000 input updates.
Each phase and phase+32 pair has identical output in this experiment. Stalls
occur at zero-based input indices 1,503–3,616, around Y=32,964–33,104, with 24–40 seconds left.
Files: local/air_phase_audit.cpp, local/air-phase-audit.txt (both local only).

This establishes that the reachable native failure is not confined to one
startup phase; it does not prove the original has the same fault. The renewed
static check still matches the 80-update crash counter, conditional animation
start at 6307/3b84 and delay behavior at 3bbd. No speculative force-start or
recovery was added. Next useful evidence must address the dynamic frame/map
transfer schedule or a matching original reference at this boundary. Do not
repeat the same static handler audit as a substitute for that evidence.

## Animation resource-wait correction — 2026-10-02

Previous checkpoint: remote `6e06d588d5f1cd35719ca312d81050963a10468d`,
tree `bf5dedabf581222ae6cb0cad8d794e08032c53df`, local `3419ea7`.
Ordinary usage is available again; the latest tool check reported primary 1%
and weekly 0%. This agent did not invoke a quota-reset action.

The dynamic-frame audit uncovered a shared error in all five animation engines:
they saved the script cursor too early. The original only commits it at a delay
or loop yield; a pending resource transfer returns to the previously saved
block, replaying preceding sound/movement/flag commands. All five engines now
follow that rule. Air's original recovery script has a regression check for
its repeated effect-15 request during transfer waits. A shared fixture verifies
movement and sound replay through a jump, delayed cursor commit and termination
in every stunt. Roof's loop decrement also now uses the original byte wrapping.

Validation: the Windows executable was rebuilt and all 25 Python tests plus
every native suite passed (local/animation-block-resume-build.log). Air now has
449,086 assertions, and the campaign harness includes an additional all-five
animation-resumption check. Other suite counts are unchanged. The complete
campaign still reaches 20 wins in 20 attempts, savings 8,138, with final-stunt
global update 52,671. No compiler warnings. No asset formats changed.

The 64-phase Air diagnostic was rebuilt and repeated: every output line matches
the earlier sweep (local/air-phase-audit-resume.txt). The known stall remains;
this fix improves source fidelity but does not establish its cause. Continue
with transfer/publication scheduling and original-reference evidence, followed
by broader human/Windows acceptance and final packaging. Exact hardware/audio
equivalence remains unverified. The port is not complete; automatic continuation
remains active. Original ROM, extracted data and diagnostic outputs stay local.

## Visible-frame publication and Windows preview validation — 2026-10-02

Previous implementation: remote `70f0a7f1bec35263b3ee3bfe0c95392003c97fbc`,
tree `979f295ee3595705c2fd3111097e90e19cf2e42a`, local `b36f60b`.
The user explicitly renewed work on all remaining points. Earlier hourly
checks had stopped at polling because the saved prompt required a new limit
interruption. The existing heartbeat now continues unfinished work when idle
and usage is available, while retaining quiet notifications and this project.

All five stunts now separate prepared objects/camera from the visible frame,
following the original display-before-entity-update order. Terminal rendering
also preserves the old visible scene until the final wait publishes the last
prepared scene. Source notes explain remaining partial-transfer, pause-entry
and HUD/fade alignment limitations; exact hardware equivalence is not claimed.

Full validation passed in local/video-publication-build.log: 25 Python tests,
every native suite and a 20-win/20-attempt campaign (savings 8,138, final-stunt
global update 52,671). Roof now has 48,904 assertions. The final distinct-outro
scene regression passes all 712 UI assertions in
local/video-publication-ui-test.txt; the final EXE was rebuilt afterward.
Air's 64-phase sweep is unchanged (local/air-phase-audit-publication.txt), so
the known crash stall is still unresolved.

The new --ui-smoke-test exercises the real Windows message handlers over 840
updates. All 13 checks pass, including keyboard/menu flow, pause with audio,
focus loss, resize and title return. package.ps1 generates isolated preview
ZIPs with manifests/hashes. Both package policies were verified; the asset-free
package was extracted into a path with spaces, prepared using the local ROM,
and successfully launched/tested with a different working directory. The
audio output device was available with zero dropped buffers. A missing helper
dependency found by the initial packaging test was fixed before rerunning it.

docs/ACCEPTANCE.md records release gates and distinguishes automated checks
from original-reference and human evidence. External manual/longplay candidates
were located, but manual retrieval failed; no completed image/audio comparison
is claimed. Human playthroughs, full two-player acceptance, another Windows
installation, original-reference timing/audio validation and the Air stall
remain open. Packages are explicitly previews, not final releases. ROM,
extracted data, ZIPs and captures stay local. Automatic work remains active.

### Expanded campaign acceptance and Roof stall fix

The full two-player acceptance run found an additional Roof stall: a balloon
catch retained a dynamic-frame animation wait. The original 00:3d15 cancels
that wait and the animation; Roof had omitted those side effects. Direct
frame changes now use the same semantics as the other stunt engines. A local
reproducer starting difficulty 3, player 2 at global update 27,181 previously
ran below the level indefinitely; it now completes successfully. New collision
regressions cover both balloon and rope catches. See REVERSE_ENGINEERING.md.

Final validation in local/roof-reset-campaign-build.log passes all 25 Python
tests and every native suite (Roof 48,906; UI 712). The campaign harness now
checks three complete runs through ending/name entry/title return:

- Single player: 20 wins, no failures, savings 7,987.
- Both players finish: 20 wins each, two/three failures, savings 9,226/8,754.
- Player one eliminated after five losses; player two finishes all 20 stunts
  without failure, savings 8,109.

The differing scores/phases supersede the earlier single-player baseline for
this source revision. Actual gameplay buttons drive the measured runs, with
no injected outcomes or extra lives. Player alternation, other-player state
isolation and global counter wrap are exercised. Full two-player automated
acceptance is now complete; human/original-reference acceptance remains open.
The rebuilt EXE also passes all 13 Windows message tests with zero dropped
audio buffers. The Air stall is unchanged and remains a release blocker.

### Publication resumed after usage reset — 2026-10-02

The automatic approval service exhausted its usage allowance after creating
an unpublished GitHub tree. No branch update occurred at that point. After
usage became available, publication resumed through the same approval path.
The tested code checkpoint is local `b70af44`, published on private main as
`08d8fff45be1d53a8de215c2d6c92ef71e589daf` (tree
`af207caa1019e0187448ea5b5604043dba411c01`).

A ready-to-run local preview is at
`dist/CrashDummies-preview-b70af44-6462a40b.zip`. Its manifest identifies a
clean source revision; all listed file hashes were verified. The packaged
EXE passed the 13 Windows checks when launched from a different working
directory, with the output device available and zero dropped buffers.
This package includes extracted assets for local use and was not uploaded.
The repository contains English source documentation and extraction tools.
The project remains incomplete; the next gameplay blocker is the Air crash
stall, followed by the outstanding reference/human/second-host checks listed
in ACCEPTANCE.md. Automatic continuation remains active.
