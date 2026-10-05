# Project status - October 5, 2026

Latest development couples the bounded native Air pause session to ongoing
gameplay, display input, graphics and software audio. Three independent original
controls match through stunt end: 7,506 updates, 7,927 display/input samples,
317,080 sprite slots, 47,562 selected voice/work rows and native effect requests.
All 7,509 ordinary display services, 45,036 source phases and 120,096 pre-update
entity slots also agree. This includes the previously checked 900 prefix
updates, 5,252 graphics/status bus events, 418 paused services, 857 pause
intervals and 1,332 accepted storage bytes; do not add these counts twice.
Nine pending-startup boundaries per case match after correcting the four-cycle
LCD access tail and duplicated first ready-store prefix. No original per-update
counters, work, idle, worlds, edges or effect requests drive the native replay.
527 pause/session assertions, 107 source assertions and 119 Python tests pass.
See [candidate scope](AIR_PAUSE_CANDIDATE.md) and [startup limits](AIR_STARTUP.md).
This is not production Windows scheduling, full PCM/pixels or hardware acceptance.

Last tested portable runtime checkpoint: local source commit `2195119`, corresponding
private GitHub commit `7313de4cdff7f2813e95f5978d276dfdd8ce5b54`.
The 25 changed source/document blobs were verified exactly after publication.
The clean-source ROM-free preview `CrashDummies-preview-2195119-9cbefd89.zip`
passes all 11 manifest hashes and contains the exact tested EXE. Bundled local
extraction succeeds in `local/Portable placement test 2195119/`; both normal
and failed-audio UI variants pass from that folder with spaces while launched
from another working directory. The extracted assets remain local; the archive
contains no ROM/assets/reference library. Local and GitHub commit identities
differ because this host publishes through the GitHub connector. This is a
development preview, not a final release.

Next concrete work: matched image comparison and remaining first-LCD-frame/
interrupted owners before production clock integration. Coupled reproduction:
`python tools/air_pause_coupled.py run coast` (also easy/hard).
Use `local/pause-coupled-{coast,easy,hard}/` and matching `-work-reference`,
`-startup-reference`, `-sprites-reference`, `-audio-reference` directories.
Original bus/storage targets remain `local/sameboy-air-pause-*-lcd-data/lcd.json`;
the standalone native geometry/prefix files remain in `local/pause-native-*-data/`.
Initial LCD-enable phase, arbitrary IRQ acceptance, pending critical-section
interrupts and line-135 object cancellation remain unowned and must reject.
Other interrupted entity/resource/row paths, startup/result setup, production
clock integration and the remaining ACCEPTANCE.md items also stay open.
The rebuilt Windows EXE is byte-identical to the tested preview; unchanged
campaign/UI suites do not need repetition without another runtime change.

## Objective

Produce a faithful **native Windows** port of the supplied Game Boy release,
without CPU emulation or replacing the original rules with a loose remake.
Private repository: https://github.com/KarlLaberfeld/TICD-Recompilation

**The overall task is not complete.** The Windows executable is a development
build of Roof Jump, Air Bumper, Ski Slope, Bomb Factory and Cruise Missile, not a complete game.

Latest evidence: an experimental native clock matches eleven control-verified Air
cases without supplied per-update counters: 32,801 completed updates and 32,909
display services, now using per-display input samples. Four cases also match
349,080 published sprite slots and 8,727 independently recorded held/fresh
button samples. Three separate pause cases validate 418 paused display services
and 6,922 complete native music-service comparisons. Three recordings also
match the final wait, audio stop and all 32 outgoing fade services; see AIR_EXIT.md. The
Windows loop still performs one game update per display interval; integration,
remaining handler/interruption paths, input/pause/exit timing, matched pixels and
PCM, and independent Windows/hardware testing remain open. The documented
native Air recovery safeguard remains intentional. See AIR_TIMING.md and the
latest checkpoint and AIR_PAUSE.md below. This is bounded reference evidence, not final acceptance.

The latest independent-reference checkpoint also reconstructs interrupted
placement range ownership: a HUD refresh changes shared scratch during the
scan. Three SameBoy replays now match 7,655 updates, 7,791 services/input samples,
45,930 phases and all 122,480 pre-update entity slots, plus final waits and the
full outgoing fade. The eleven prior PyBoy cases remain separately verified.
The rebuilt EXE passes all native suites/campaigns and 13/14 Windows UI checks;
107 standalone source assertions and 103 Python tests pass. See AIR_PLACEMENTS.md
and REFERENCE_BACKENDS.md. Native pause polling and production integration are
still required; this does not mark the port complete.

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

## Air crash transfer-contention experiment — 2026-10-02

New hypothesis tested: map-row priority delays the crash animation beyond its
80-update recovery deadline, rather than a stale animation wait like the Roof
bug. The local diagnostic `local/air_transfer_budget.cpp` runs the same 64
initial phases and button schedule twice: unchanged native behavior, and an
explicitly non-original counterfactual that removes map contention only during
the crash handler. It does not alter the production engine.

Results in `local/air-transfer-budget.csv`: unchanged native behavior has 12
stalls, each with the crash script still active at recovery; the counterfactual
has zero late recovery boundaries and zero stalls across all 64 phases.
This narrows the issue to the animation/transfer budget. It does not establish
which timing differs from the original, or whether the original also stalls.
Removing map priority is not an accepted fix: the original explicitly gives
row updates priority. The runtime, known Air blocker and release status remain
unchanged. No full-suite rerun was needed for this diagnostic-only experiment.

Next useful Air evidence is a matching original capture around crash entry,
row transfers and the 80th crash update, or a newly identified source difference
in that scheduling path. Do not repeat the unchanged static audit or the same
64-phase sweep without a new hypothesis. Presentation pause-entry/publication
alignment and original audio/Windows acceptance remain independent open work.

## Pause display boundary — 2026-10-02

Completed the next independent presentation gap using 00:03cb/03d5 and
1476-14f1: the display callback runs before entering pause, and resumption
returns directly into the pending entity update. All five native stunts now
publish the pending display once at pause entry, preserve the resource/HUD
state during pause, and avoid a duplicate display update on resumption.
The campaign fade follows the same entry/resume boundary. No CPU execution
or hardware interrupt emulation was introduced.

Validation: local/pause-publication-build.log passes all 25 Python tests,
every native suite, and all three full campaign scenarios. Savings/results
are unchanged from the previous checkpoint (7,987; 9,226/8,754; 0/8,109).
A new shared regression covers prepared sprite publication, in-progress
resource transfer, HUD/fade suspension and resumption in all five stunts.
The fixture isolates intro logic so legitimate new frame requests do not
replace its controlled transfer. The Windows message test also passes all
13 checks, with the audio output device available and zero dropped buffers.

Source details are in REVERSE_ENGINEERING.md. Exact sub-frame drawing,
partial tile publication, original audio/reference comparisons, human and
second-Windows-host acceptance remain open. The Air crash blocker is unchanged;
its no-map-contention experiment remains diagnostic only. The native EXE in
build/ was rebuilt; the earlier b70af44 ZIP remains the prior preview checkpoint.
Automatic continuation stays active. ROM, extracted data and diagnostics remain
local and are not uploaded.

## Windows audio-open failure acceptance — 2026-10-02

Added a targeted `--ui-no-audio-test` mode. It asks the real Windows waveOut
API to open an invalid device identifier, verifies that opening fails, and
then runs the normal hidden-window gameplay/input/pause/focus/resize checks.
No system device is disabled and ordinary startup still uses WAVE_MAPPER.
Separate diagnostic logs preserve both normal and unavailable-output results.

The rebuilt EXE passes all 14 no-audio checks. A subsequent normal invocation
passes all 13 UI checks with an available output device and zero dropped
buffers. Build log: local/audio-failure-build.log. Runtime logs:
build/ui-window-no-audio-test.txt, build/audio-output-no-device.txt,
build/ui-window-test.txt and build/audio-output.txt. Gameplay, asset extraction
and audio synthesis code are unchanged; their latest complete suite remains
local/pause-publication-build.log. No redundant full-campaign rerun was needed.

This closes automated coverage of startup audio-open failure, not physical
unplugging, another audio driver, human play testing or a second Windows host.
ACCEPTANCE.md retains those evidence limits. Air crash timing and original
image/audio comparisons remain open; no final release is claimed. Automatic
continuation stays active, with original data and all generated outputs local.

## Outgoing HUD publication — 2026-10-02

Corrected another identified presentation gap: the original gameplay callback
continues updating the HUD during the outgoing stunt fade, even though FFAE
has disabled dynamic resource transfers. The native snapshot had frozen that
HUD, potentially hiding score changes from the final gameplay updates.
UiFlow now refreshes the outgoing HUD during the visible fade, preserving
frozen entities, timer and resource-transfer state. Source notes explain the
callback ordering and remaining hardware/palette evidence limits.

The targeted all-five-stunt regression passes (local/outro-hud-test.txt), and
the Windows EXE was rebuilt successfully (local/outro-hud-build.log). The
regression is also part of the existing native campaign test entry point.
Gameplay rules and outcomes are unchanged; their latest complete campaign
suite is still local/pause-publication-build.log. This targeted change did
not require repeating the unchanged campaign pilots or extractor tests.

Air's crash deadline, partial-tile display, original audio/image comparisons
and outstanding human/second-host acceptance remain open. No final version
is claimed, and the automatic continuation remains active. Local ROM/data,
reference artifacts and generated binaries remain excluded from GitHub.

## Shared sprite resources and Roof landing graphics — 2026-10-02

A new transfer-destination hypothesis identified the original two-buffer scheme.
Ordinary uploads fill the inactive resource and swap only on completion, so
partial player graphics are not expected from that path. The audit also found
an actual extraction/rendering error: Roof frames 30-32 have no independent
upload and use the three extra chunks loaded with landing frame 29. The old
extractor incorrectly treated their descriptor pointers as fresh graphics.

All five native stunts now retain decoded resource buffers, honor upload
replacement and unwritten tails, and snapshot sprite colors for publication.
Roof's detached body parts resolve shared resident data. No CPU emulation was
introduced and gameplay scheduling, collisions and the Air deadline are unchanged.
Updated local formats: TICDNAT6, TICDAIR5, TICDSKI3, TICDBOM3 and TICDCRU3.
Re-extract the five gameplay packages when updating the executable. UI/audio
formats are unchanged. See REVERSE_ENGINEERING.md for source addresses and limits.

Validation: local/shared-sprite-build.log passes 26 Python tests, every native
suite and all three full campaign scenarios. Results remain 7,987 (solo),
9,226/8,754 (both complete) and 0/8,109 (first player eliminated). Additional
focused landing/resource regressions pass 48,917 Roof assertions and 30 sprite
assertions (local/self-test.txt and local/sprite-test.txt). Assertion counts
include repeated replay invariants, not independent scenarios. The final EXE
was rebuilt (local/shared-sprite-final-build.log) and passes all 13 Windows UI
checks. Tests and source analysis establish this reconstruction correction;
they do not establish original-hardware image/audio parity.

The Air crash stall, matched original captures, human playthrough, physical
audio-device removal and a second Windows installation remain release gates.
Do not rerun the unchanged Air phase sweep without a new timing hypothesis.
The new resource evidence narrows the partial-tile issue; exact sub-frame
publication and unreferenced startup buffer contents still need references.
The project and repository remain private and incomplete. Automatic continuation
stays active. ROM, decoded assets, captures, binaries and preview ZIPs stay local.

## Air crash/recovery handoff fixed - 2026-10-03

Implemented an explicit deferred recovery request for the player. If the crash
script is still active at the original 80-update boundary, conditional start
rejects recovery. The native port now remembers that request, lets the current
script finish (including its final sound), and starts the original recovery
script once. On-time recovery, map-row priority, transfer budgets, movement
and animation periods are unchanged. Pause retains the request; restart, a new
crash and a terminal result clear it.

This resolves the reachable native liveness failure, but is deliberately a
native safeguard, not a proven correction to original timing. The source
audit has not established whether the cartridge reaches the same edge case.
See AIR_RECOVERY.md for exact source addresses, behavior and evidence limits.
Do not mark original-reference timing accepted on the strength of this fix.

The new regression failed on the previous implementation. It now passes all
64 initial phases, including all twelve formerly stalled cases, with 232
completed returns to player control and every replay reaching a stunt result.
Additional checks cover on-time startup, preserved crash sound, one-time
recovery, pause/restart, terminal cancellation and unrelated entity updates.
The focused Air suite passes 822,125 assertions (including repeated replay
invariants) and successful ordinary-input runs on all four difficulties.
The rebuilt Windows EXE passes all 13 UI checks with zero dropped audio buffers.
Detailed original data and diagnostic logs remain local.

Full validation also passes: 26 Python tests, every native suite and all three
complete campaign scenarios (local/air-recovery-build.log). Their results are
unchanged: 7,987 solo; 9,226/8,754 with both players completing; and 0/8,109
with player one eliminated before player two completes. The executable at
build/CrashDummies.exe contains the fix. Preview packaging now describes the
stability correction instead of listing the reproduced stall as unfixed.

Remaining release gates are matched original timing/image/audio references,
human playthrough, physical audio-device removal, a second Windows installation
and final distribution acceptance. The repository stays private and the
automatic continuation stays active; this Air fix does not finish the port.

## Original-ROM Air comparison - 2026-10-03

The user authorized a separate reference emulator for measurement only. The
original local US/EU ROM now has a reproducible Air trace using PyBoy 2.7.0,
Python 3.13.5, normal UI/password inputs and read-only gameplay instrumentation.
At update 2458 it reaches the same stopped-script recovery failure. It remains
frozen for another 600 observed updates. A control replay without hooks produces
the same 32,768-byte memory snapshot; the finding is not hook-dependent in this
reference environment. This is emulated-original evidence, not hardware proof.

The native probe matches all 23 compared gameplay fields for 2,458 updates when
supplied the observed original global counter. The next difference is the
intentional recovery safeguard. However, the original counter increments during
updates 895 and 1222. With ordinary native clock progression, speed/rate already
diverge at update 898. The original can span another display interval during
an update; native scheduling does not yet account for that. Do not claim full
timing parity or hardcode those two indices as a fix.

Reproduction tools: tools/air_reference.py and tools/air_reference_probe.cpp.
Report and instructions: docs/ORIGINAL_COMPARISON.md. Evidence remains under
local/original-air-verified/, including capture-summary.json, original trace,
input log, control state/images and both native comparison reports. The optional
emulator is not a runtime/build/package dependency. No original data is uploaded.

Validation: repeatable hooked/control capture, compiled native replay in ordinary
and recorded-clock modes, and 29 Python tests including comparison normalization,
divergence detection and truncated-trace rejection. No native runtime code or
asset formats changed in this comparison checkpoint; the previous full native,
campaign and Windows results remain the relevant build checks. No redundant
campaign rerun or replacement EXE was needed.

Next concrete fidelity work: investigate native modeling of the measured display
counter cadence, followed by more reference inputs/layouts and matched pixels/
audio. Human, physical audio-device and second-Windows-host acceptance remain
open. Keep the repository private and automatic continuation active.

## Source timing reconstruction checkpoint - 2026-10-03

**Original-time scheduling is still incomplete.** Native Air gameplay still
advances once per display interval. Do not describe this checkpoint as the fix
for the extra original VBlanks, and do not enable scheduling from partial costs.

The measured overrun occurs during placement scanning/creation, with FFAE zero;
the original then waits for another VBlank at 2617. Variable display/audio
service costs also affect the available work interval. New control-verified
timing instrumentation records every completed update, VBlank and STAT service.
Its final memory matches the existing uninstrumented original control exactly.

Four source-derived cost models now match all 3,059 reference updates: sprite
preparation, unused sprite-list clearing, map-row preparation and eight-placement
scanning. C++ models use native semantic state and decoded layouts, without CPU
emulation or frame-index exceptions. Optional graphics-cost collection is used
by the native probe, not ordinary Windows gameplay. Native exports with that
collection enabled and disabled match byte for byte.

The expanded comparison exposed a real timing defect: native Air slot reuse
cleared an animation delay/period that original 1acd preserves. Fixed allocation
to retain delay, period, script and loop cursors while marking animation done
and clearing its frame wait. A synthetic regression fails against the previous
allocator. Restart still clears all slots. Recorded-clock comparison now matches
the four actual native costs through update 2470, and occupied non-player frame,
flags and positions through 2578. The first player difference remains the
intentional recovery safeguard at 2458. These are scoped comparisons, not full
world, image, audio or real-time parity.

See AIR_TIMING.md and tools/air_timing.py. Local evidence is in local/air-timing/;
all original state, layouts and captures stay local. No asset format changed.

Validation currently available: 39 Python tests, 822,497 focused Air assertions
including all 64 recovery phases, all four input-only difficulty successes, and
13 Windows UI checks with zero dropped audio buffers. The full build, every
native suite and all three campaign scenarios pass in
local/air-work-verified-build.log: 8,478 solo (one failed attempt), 8,620/8,455
with both players completing (three/two failed attempts), and 0/8,493 with the
first player eliminated (five/zero failures). The rebuilt Windows EXE is
build/CrashDummies.exe; no new preview ZIP was produced. The faithful animation
change makes the existing pilot retry one solo Air attempt. The campaign harness
now checks failure life loss and preserved progress/savings on every loss,
retaining all twenty wins, ending and title-return requirements. It no longer
mistakes a perfect pilot run for a game-correctness condition. No outcome is
injected or game logic changed to assist the pilot.

Next: source-account 03d8..03e4 (entity handlers, animation, collisions and resource
queue), then variable interrupt/audio/HUD work and wait-loop phase. Only with a
complete budget should display and completed-game-update progression be split.
Require ordinary-clock comparison without supplied per-update ticks, then expand
inputs/difficulties. Do not repeat the unchanged placement/sprite audits without
a new hypothesis. Keep the private repository and continuation automation active.

## Animation/resource timing checkpoint - 2026-10-04

**Runtime cadence is still unfinished.** This checkpoint extends source-work
accounting, not the Windows scheduling policy. Gameplay and the intentional
Air recovery safeguard remain unchanged.

The resource queue is now the fifth fully reconstructed work phase; its pure
source formula matches all 3,059 reference updates. The reference capture now
measures 12,009 handler bodies and 6,870 nested animation calls. Dispatcher
bookkeeping (1612 + 60 per live call) plus measured bodies agrees exactly with
the whole entity phase. This is a decomposition, not a complete source budget.

Native resource/animation totals match through update 2458. Before that deliberate
recovery difference, 8,988 modeled native handler calls at 15 source addresses
also match the original. Play (1,461 calls), Crash (320) and the Wait-to-Play
transition (one) remain unmodeled in this prefix; unknown costs use -1, never zero.
Other helper paths not exercised by the replay are explicitly not reference-
verified. Detailed scope, reproduction commands and limitations: AIR_TIMING.md.

Validation: 41 Python tests; 23 new synthetic C++ source-work checks, requiring
no ROM; rebuilt build/CrashDummies.exe; 13 automated Windows UI checks. Native
state exports with accounting enabled/disabled and the previous checkpoint are
byte-identical across all 3,059 updates. The expanded original instrumentation
still matches the existing uninstrumented control memory exactly. Unchanged
campaign suites were not rerun for this diagnostic-only change. No new preview
ZIP or final release was produced. Evidence stays in local/air-animation-timing/
and local/air-animation-build.log; no ROM, extracted data or original capture is
included in Git.

Next concrete work: reconstruct Play/Crash collision and motion work using the
new handler boundaries, then variable interrupt/audio/HUD work and wait phase.
Do not enable a scheduler from partial costs or replace unknown costs with a
fitted constant. Ordinary-clock comparison without per-update supplied counters
must pass before original-time cadence is accepted. Retain the private repository
and continuation automation.


## Play/collision and VBlank timing checkpoint - 2026-10-04

**Original-time scheduling is still unfinished.** Windows gameplay still advances
once per display interval. No fitted interrupt allowance or frame-index exception
was introduced, and the deferred Air recovery safeguard is unchanged.

The missing Play, Crash and Wait-to-Play costs are reconstructed. All 10,770
handler calls before the intentional difference at update 2458 match independently
measured original bodies, with no unknown costs in that prefix. All six native
main-update phases now agree through update 2457, including overruns 895/1222.
Collision scan, callbacks, motion and input have separate validated boundaries.
All 31 callback calls exercised here (types 7/8/9/10/11) match. Other callback
branches and timeout/finish-delay costs have source and synthetic checks only;
FinishMotion, WallSlide, Exploding and further inputs still require comparison.
Unknown work propagates as -1, including native-only recovery at update 2458.

Capture schema 6 also decomposes 3,063 VBlank services. Fixed prefix/DMA/joypad/
bank/restore costs and the conditional reset guard match every service. Variable
display work is 884..7464, effect setup 64..620, music 1612..13008 T-cycles.
Those ranges are measurements, not source models or scheduling allowances.
The guard is 240 here because reset is enabled, rather than the 160 disabled path.
Control memory remains identical to the earlier uninstrumented original replay.

Validation: 47 Python tests; 51 synthetic C++ source-work checks; rebuilt
build/CrashDummies.exe; 13 automated Windows UI checks. Accounting-enabled,
-disabled and previous native exports are byte-identical over all 3,059 updates.
Diagnostic-only changes did not justify repeating unchanged campaign suites.
Logs/evidence: local/air-play-irq-timing/, local/air-play-build.log and
build/ui-window-test.txt. No new ZIP or final release; original data stays local.

Next concrete work: source-model the variable display callback (map/resource,
HUD/scroll), effect setup and music-driver intervals, then STAT/main-loop wait
phase. Cover remaining Air handler and input branches with new reference cases.
Only then split display/game-update progression and require ordinary-clock
agreement without supplied per-update counters. Do not repeat unchanged phase
checks without a new hypothesis. Keep the repository private, reports in English,
and the continuation automation active until all ACCEPTANCE.md requirements pass.

## Display/effect timing and startup phase checkpoint - 2026-10-04

**Original-time scheduling is still unfinished.** The native Windows loop still
advances one game update per display interval. This checkpoint completes the
display/effect source-work models and fixes a progress-bar glyph; it does not
claim a final timing or audio match.

The independent source formulas match all 3,063 original display callbacks and
effect-setup intervals. Display work separates map/resource transfer, HUD column,
scroll, LCD, fade and full HUD refresh. The source formula reproduces all 235
original refreshed bars. Native rendering now emits the original 0xf0 terminator
after exact positive eight-point segments below a full bar, instead of leaving
the next tile blank. Zero/full bars and quotient wrapping remain covered.

Direct native display comparison exposes a remaining startup phase difference:
the first original game update follows HUD cursor 2, native cursor 1. A separate
control-verified measurement shows a pending VBlank serviced immediately after
03c6 enables interrupts, then pending STAT, then 03cb's wait for another VBlank.
IF=0x13 and IE=3 at entry; the first service starts at scanline zero. Preserve
this mechanism in the future scheduler, rather than inserting a fitted cursor
offset. Extra display services during long work remain outstanding as well.

Original final control memory remains byte-identical. Native exported state
with accounting enabled/disabled remains identical to the previous checkpoint;
that export does not cover HUD pixels. Optional effect accounting preserves PCM
through 240 frames of music and overlapping effects. Original-audio equivalence
is not established.

Validation: 52 Python tests; 65 synthetic C++ source-work checks; 822,497 Air
assertions with all 64 recovery phases and four input-only difficulty successes;
131 audio assertions; rebuilt build/CrashDummies.exe; 13 automated Windows UI
checks. Unchanged full campaign suites were not repeated. Evidence stays in
local/air-display-effect-timing/, local/startup-phase.json and related local/build
logs. No new ZIP, final release, ROM, extracted data or original recordings are
published.

Next: reconstruct the music-driver body, complete STAT/wait phase including the
pending startup service, then split display and completed-game-update progression.
Require ordinary-clock comparison without supplied per-update counters before
accepting timing. Expand remaining Air branches, inputs and difficulties, then
other stunts and image/audio comparisons under ACCEPTANCE.md. Keep GitHub text
English, the repository private and the continuation automation active.

## Music, wait and experimental native clock checkpoint - 2026-10-05

Source models now cover all 3,063 captured music services (18,378 voice calls),
including 6,981 commands and 3,238 notes. Independent native replay of the same
song/effect requests matches active voice-state fields and service costs. Three
source corrections preserve voice-one ADC carry, portamento byte wrapping and
square-envelope fallthrough. Optional accounting preserves native PCM; original
PCM equality remains unverified. STAT and outer wait/resume/tail boundaries
match the control-verified baseline, including the pending startup interrupts.

Air displayTick and updateGame are separated. The experimental air_clock_probe
charges semantic source work to an independent clock; it supplies initial
clock/timer/random phase and update-aligned buttons only. It does not inject
per-update counters, measured work, outcomes or original entity state. Unknown
work or unsupported interrupted phases stop the probe. Production Windows
scheduling is unchanged pending broader ownership/input/pause/exit validation.

Nine cases cover the original recovery prefix, all four coast difficulties,
boost, acceleration, steering and a successful finish. Native post-update
fields, callback gates, HUD/effect requests and service costs match 28,103
updates and 28,153 services. The recovery capture stops before the intentional
difference at update 2458; other cases complete their original
timeout/damage/success outcomes. Steering includes 12 additional displays and
partial sprite preparation/clearing. Two cases match 158,840 published sprite
slots for presence, position and flags in separate, control-verified captures.
Tiles, pixels, PCM and hardware are not certified. Combined outer-loop/DMA hooks
changed control memory and were discarded; a single DMA-boundary capture passed
the unchanged control check.

Two measured gameplay corrections fix boost-expiration pose and severity drag
when speed reaches zero. A successful original finish now validates the
finish-sound countdown and final-result branch: native particles were
incorrectly spawned on the last step. All 2,351 recorded-clock states now match,
as do the independent clock, phase work and 95,120 published slots. Source work
for 35 WallSlide and 128 FinishMotion calls matches. Camera scroll-limit,
camera-lead, wall entry, quota and enemy-penalty accounting were corrected from
source. A busy/ready gate interrupt immediately before its store caused an early
upload; the candidate now commits that semantic store before servicing pending
work. Sprite publication follows Y/X/tile/flag write ordering, and accepts the
no-row map path only when its pending state is already false. No replay indices
drive it. The second music capture matches 2,378 services and 14,268 native
voice rows; combined music evidence covers 5,441 services. Original PCM is still
unchecked.

Validation: 72 Python tests; 89 synthetic C++ source-work checks; full native
suites (819,624 Air and 150 audio assertions), all 64 recovery phases, four
input-only difficulty successes and three full campaigns; rebuilt Windows EXE.
Single-player finishes 20 wins with one retry and 8,478 savings; both-player
completion finishes 8,620/8,455 with three/two failures; elimination finishes
0/8,493 with five/zero failures. These are native tests, not original proof. The
normal Windows UI and actual audio-open-failure variants passed 13/14 checks on
this host during this checkpoint. Physical removal and another host are open.

Evidence remains ignored/local in original-air-*, air-*-timing,
air-music-timing, air-loop-timing and air-steer44-sprite-reference. Build/test
logs include local/air-finish-build-tests.log and
local/air-finish-final-build.log. Latest source-work regressions also pass 89
checks in local/air-work-tests.exe. No final ZIP or release is produced. Next:
remaining Exploding/handler branches, interrupted entity/resource/row-building
subphases, then input/pause/exit and Windows integration, other stunts and final
ACCEPTANCE.md checks. Keep the private repository and continuation automation.

## Pause and display input checkpoint - 2026-10-05

Three control-verified Air captures cover requested pauses of 31, 120 and 255
frames on normal, easy and hardest difficulty. They produce 35, 124 and 259
paused VBlanks, including button press/release frames. Gameplay, timer and RNG
remain unchanged across 415 adjacent paused services; the global 16-bit display
counter continues. Source entry/restore work, four copies per pause, window text,
STAT, all paused display/music subphases and 418 outer waits agree. Failed LCD
polls are counted from the source branch flags, not a later STAT register read.
Their variable work and measured HALT idle are reference evidence only; neither
is supplied as a fitted native allowance.

The native pause now advances the shared counter and samples controls in all
five stunts while retaining entities, gameplay timer, HUD and resources after
the entry callback. This corrects standalone/development-mode counter freezing;
campaign counters also agree during pause. Synthetic regressions cover counter
wrap, held/fresh input and deferred crash recovery. Music still powers off the
outputs and freezes its software streams. Source 3714 prepares a pending effect
before the disabled driver call even during pause; native ordering is corrected.
That pending-request corner is source/synthetic evidence, not a captured original
pending-during-pause witness.

Isolated native song/effect/pause request replays match 6,922 completed music
services (41,532 compared voice rows), including 418 disabled services, in the
three captures. Original voice states and work are comparison targets only.
Two captures end inside another music call; that final partial interval is
explicitly recorded and excluded rather than certified. PCM is not compared.

The experimental clock can now read buttons once per display service rather
than once per completed update. It derives fresh edges itself, including the
loss of an edge after an extra service. All nine existing cases still match
28,103 updates, 28,153 services, 168,618 phase/entry-counter checks and the two
sprite comparisons. Separate single-hook captures verify 3,971 held/fresh input
samples in steering and the successful finish. Recorded edges, per-update
buttons/counters, work and world outcomes do not drive this mode. Initial
clock/timer/RNG phase and per-display held-button requests are supplied; replay
length bounds the measured comparison scope. Physical input microtiming remains
unverified. Start/pause input is rejected by this clock probe until native pause
entry/copy/return ownership is reconstructed.

Validation after gameplay/audio changes: full native suites and all three
campaigns pass; Air retains 819,624 assertions, all 64 recovery phases and four
input-only difficulty successes; audio passes 150 assertions. Latest standalone
checks pass 82 Python tests and 92 synthetic source-work checks. The rebuilt
Windows executable passes 13 normal and 14 actual audio-open-failure UI checks.
These are automated messages on one host, not human/device-removal acceptance.
Local evidence: air-pause-*-timing, air-pause-*-music, air-display-input-clock,
air-*-input-reference, local/air-pause-build-tests.log and Windows logs in build/.
No final package or release is produced. Next: remaining interrupted/unknown Air
work, native pause/exit/startup ownership and scheduler integration, then other
stunts, matched pixels/PCM and the remaining ACCEPTANCE.md gates.

## Explosion and wait-snapshot checkpoint - 2026-10-05

A new easy-difficulty, input-only original capture (alternating steering every
52 updates) reaches a damage result after 2,077 updates and 2,105 VBlanks.
Its 63 Exploding calls and 61 Return calls match native state and source costs;
all 2,077 handler/update component costs are modeled and agree. Explosion work
accounts for countdown, allocation, two RNG calls, particle creation and the
alternating sound request. This adds accounting without changing gameplay.

The ordinary-clock replay exposed a wait snapshot ownership error. A VBlank
arriving before the original counter read belongs to the new snapshot; the
wait must then continue to a later VBlank. The native model now charges CALL/PUSH
before the read and commits the read before a pending interrupt. Its total
active work is unchanged. Synthetic checks cover both sides of that boundary.
No recorded counter, idle allowance or replay index drives the correction.

The complete new ordinary-clock replay matches state, display/audio work,
12,462 phase/entry-counter checks, 84,200 sprite slots and 2,105 independently
captured held/fresh samples. All nine earlier cases still pass after the wait
correction. Combined ordinary-clock evidence is 30,180 updates, 30,258 services,
181,080 phases, 243,040 sprite slots and 6,076 held/fresh samples. The baseline
still ends at the documented intentional recovery boundary. This validates the
new path, not arbitrary handler branches or unsupported interruptions.

A separate outer-loop capture confirms 2,077 complete waits, including the new
two-service snapshot case, 2,106 STAT bodies and all resume/tail costs. Its
control memory is unchanged. One final interrupt is incomplete: metadata
explicitly records and excludes it. The loop tool now separates that boundary
from changed-control failures; it does not turn a partial service into evidence.

Validation: 84 Python tests, 99 synthetic source-work checks, rebuilt Windows
EXE and 13 automated Windows UI checks. Full campaigns already passed after
the preceding gameplay/audio changes; this accounting-only checkpoint does not
repeat unchanged campaigns. Evidence remains under ignored local/air-explosion-*
and local/air-display-input-clock*. Production Windows scheduling, native pause
LCD polling/ownership, startup/exit, other stunts, pixels/PCM and independent
Windows/hardware acceptance remain unfinished. No final release is produced.

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
