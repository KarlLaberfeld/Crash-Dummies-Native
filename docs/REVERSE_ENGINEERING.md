# Reverse-engineering notes

## Scope and evidence

The input is a 128 KiB MBC1 cartridge, title `CRASH DUMMIES`, no cartridge RAM.
SHA-256: `ef563c4a4b063ea045d71b435dd078c19d0738f85079928803167cee8f34a4ec`.

Addresses below use `bank:CPU-address`. Fixed-bank addresses start with `00`.
The 16 KiB bank layout and code were inspected locally. The disassembler is a
linear inspection aid: it does **not** distinguish data from code automatically.
Inline text/animation data in its output must never be treated as valid code
merely because it can be decoded as instructions.

No original machine instructions are executed by the Windows runtime. The
original game's *animation command language* is decoded offline to indexed,
typed commands. C++ implements its semantics. Native game-handler IDs replace
original code pointers. This is a game subsystem port, not CPU emulation.

## Rooftop data

| Address | Meaning / evidence |
|---|---|
| `00:08bb` | Roof Jump initialization |
| `00:09b1` | Four 6-byte difficulty records: placement pointer, repeated wall sections, remaining objects, BCD seconds, fire tolerance |
| `00:197e` | Placement records: type byte, little-endian X, little-endian Y; FF terminator |
| `00:196e` | Add 0x1000 to placement X coordinates |
| `00:198c` | Expands each placement from 5 to 7 bytes with spawned/persistent-state fields |
| `00:19a2` | Scan eight object records per gameplay update |
| `00:1abc` | Sixteen live entity slots; instantiate object definition |
| `00:3430` | Object-definition pointer table |
| `00:34b4` | First player definition: frame 3, intro handler, initial velocity/pose fields |
| `04:4000` | 97 background tiles |
| `04:4610` | Static roof object tiles |
| `04:51b0` | Four planar metatile quadrants, each 0x62 entries |
| `04:5338` | 10-wide map, 5 initial rows, 4 repeating rows, 9 ending rows |
| `03:58d0` | 35 dynamic frame descriptors: byte count in 32-byte units, bank, source pointer |
| `03:595c` | 69 frame-definition pointers |
| `00:1cb6` | Sprite geometry parser: 8-byte header followed by Y/X/tile/flags tuples, FF terminator |
| `00:1747` | Collision bounds use draw offset + collision offset + width/height |

The second placement list starts at fixed-bank `00:3fd6` and continues into
bank 1. The extractor intentionally uses the contiguous file bytes here; it
must not blindly reject that pointer as a bank-1 address below 0x4000.

| Difficulty | Height px | Objects | Time s | Fire tolerance |
|---|---:|---:|---:|---:|
| Easy | 1888 | 36 | 60 | 4 |
| Normal | 1696 | 39 | 60 | 3 |
| Hard | 1952 | 49 | 70 | 2 |
| Very hard | 1952 | 46 | 70 | 1 |

## Roof behavior translated so far

- `01:55daâ€“563a`: flyover, waiting and roof start sequence.
- `01:56de`: main falling update, held lateral input and pressed posture input.
- `01:5748`: Q12.4 position updates and X clamp to 0x1040â€“0x1880.
- `01:59cc/59d2`: lateral velocity -10/+10 fixed-point units.
- `01:5a0eâ€“5a81`: neutral/spread/head-first target velocities 24/20/28.
- `01:5a8b`: vertical velocity moves one unit toward pose target.
- `01:5c8b`: awning damage count; head-first/spread break, neutral bounces.
- `01:5ef3`: solid balcony breaks once; neutral bounce -4, reward 5/10.
- `01:5f29`: landing target, reward 100, one-time removal.
- `00:312d`: BCD timer decremented after 60 updates.
- `00:3b80â€“3cfa`: animation commands, loops, positions, frame changes and native-handler transitions.
- `00:3e75`: camera tracking expressed directly in native integer arithmetic.

## Corrections verified against static routines, 2026-09-29

- Sprite origin: `00:1cdb/1cf3` adds header bytes 6/7 (half extents) to
  the display offset before the piece offsets. Hardware coordinate biases
  +8/+16 cancel when drawing the screen. Whole-frame mirroring uses that
  same center. The previous extraction omitted the half extents, displacing
  graphics relative to their collision boxes. Data format `TICDNAT2` prevents
  silently loading old images; regenerate `crash.dat` after updating.
- `00:1cb6â€“1cf6`: padded visibility bounds, after display offset, are
  X [-2*halfWidth-16, 176], Y [-2*halfHeight-16, 152], inclusive.
  Offscreen flags are updated after entity handlers and before placement scans.
  Native repaint frequency does not affect this state. Capacity and priority
  were added in the September 30 sprite composition checkpoint below.
- `00:3da5` removes a live entity without resetting its placement's active
  byte. Only visibility eviction with flag bits 4 and 2 clears that byte
  (`00:1c91â€“1cb2`). A collected target therefore cannot reappear on a later scan.
- `01:55fe` activates balloons/planes at the end of the intro camera rise;
  this is separate from animation command 0x92 (`00:3cf1`, sound-driver gate).
  `01:563a` processes walking before the jump button. Held lateral input can
  legitimately postpone the jump, so test replays release steering during it.
- `01:5c8b` tests pose before upward velocity. Spread/dive contact breaks
  awnings even while rising; neutral upward contact does nothing. Four neutral
  rebounds have velocities -41, -37, -33, -29; the fifth breaks the awning.
- `01:5dbd/5dd7`: plane stun retains the definition's 0x40 countdown rather
  than resetting it to 0x20. Collision stays disabled after the plane resumes.
- `01:5722â€“584d`: only the main fall handler checks the ground row, snaps
  Y to the next tile row, and chooses a landing sequence. Bounce/rope-release
  handlers have their own updates. A head-first miss plays script `01:57cf`.
  A target landing spawns five body pieces; the upward piece's script reaches
  `01:59b6`, which starts the 64-update result delay. The player stays idle.
  Result flags are 0x81 for insufficient breaks, 0x03 for success, and 0x07
  for success with no remaining objects. Ten breaks leave the initial counter
  at zero: eleven are required to set its sign bit. Timeout/fire use 0x11/0x21.
- `01:5778` falls through to timeout movement on the same update; `01:59b6`
  similarly performs the first countdown decrement immediately.

Validation: eleven Python tests (including independent OAM-coordinate projection),
native regression checks and deterministic replays for all four roof lists.
Windows x64 GUI executable (PE subsystem 2), hidden-window smoke test and
local image capture passed. This is static source-derived validation, **not**
a frame-by-frame comparison to original hardware. No CPU emulator was run
for this continuation.

## Original roof HUD and clouds

`00:03a2` selects thirteen font tiles for tile IDs F3â€“FF. `00:2e54` supplies
the original 20-column window layout (`00:2ef5`), the 13 destination columns
(`00:2edb`) and bar/icon tiles (`03:5780/5800`). These are decoded locally into
an atlas; data format is now `TICDNAT3` (which also includes the sprite-origin
correction from version 2). No ROM code is included in this atlas.

`00:2e9b` formats player number, low four decimal score digits, remaining time
and a six-tile height bar. Its fill is `48 - floor(cameraRow * 48 / (mapRows-10))`.
`00:3198` copies just one of the thirteen changing tiles each update; the source
buffer is refreshed after a complete cycle. Native HUD updates preserve that
lag instead of immediately redrawing new numbers. The port currently fixes the
player number to 1 because the campaign and multiplayer loop are still absent.

`00:0997` creates cloud object 15. `01:5f40â€“5f8e` alternates two saved X positions
through one live slot, selecting it by frame parity; Y is -0x10 or 0x90 fixed
units. Speeds come from `01:5f8f`, and a saved position resets from 0x0d80 to
0x1a00 while advancing its speed index. Both motion and alternation are native
game logic. The initial global frame phase still starts at zero in this build;
the original menu/briefing duration determines it in the complete game.

## Unverified or incomplete

The runtime is not yet a matching reconstruction. In particular:

- Resource-transfer queues and animation waits are reconstructed, but hardware
  frame timing still needs reference validation.
- Roof frame ordering, offscreen lifecycle and all edge-case collisions need
  comparison with a reference execution; current tests only validate native
  invariants and selected translated rules.
- The corrected plane/landing rules above still need reference timing checks;
  balloon/rope interactions and several entity flags need further analysis.
- Some transient effects and exact presentation phase still need validation;
  sprite priority/capacity are now implemented for gameplay (see below).
- Palette register changes and intro/menu text are not fully reconstructed;
  the launcher explicitly identifies the build
  as work in progress.
- No original sound driver, other two stunts, campaign or ending.

Do not fill these gaps using guessed gameplay and then claim equivalence.
Record address-level evidence and add behavior comparisons as each subsystem
is reconstructed.

## Next entry points

The stage initialization table is at `00:33ce`:

1. Roof Jump: `00:08bb`
2. Air Bumper: `00:0b31`
3. Ski Slope: `00:0dc9`
4. Bomb Factory: `00:0fce`
5. Cruise Missile: `00:1245`

The instruction/briefing table is `00:33b0`. Sound entry points include
`00:362a` (music selection) and `00:3711` (effect selection). Full reverse
engineering and validation are still required.


## Air Bumper extraction and native entry points

Initialization `00:0b31` installs twelve dynamic sprite descriptors from
`03:608f`, 59 frame pointers from `03:60bf`, and static sprites from `05:4000`.
The background has 128 planar tiles at `04:688c`, collision flags at `04:784c`,
and four 128-byte metatile quadrant tables at `04:78cc`.

The four eight-byte records at `00:0c1f` supply camera X/Y, BCD time, quota,
map pointer and placement pointer. `00:1d41` expands pairs of circular X offset
and 16-by-4-metatile template index; `00:1d78` is the template pointer table.
Maps wrap at sixteen columns and occupy 184, 236, 256 and 256 metatile rows.
The original one-byte row count wraps at 256; native code must retain 256.
Placement lists contain 78, 131, 143 and 143 entries, kinds 18 through 30.
Their X coordinates receive a fixed-point offset of `0x4000`.

`tools/extract_air.py` writes the local-only `TICDAIR3` data pack. It includes
59 sprite composites, the four maps, 18 semantic object definitions, thirteen
animation graph roots, six collision probes for each of five tilt positions
(`01:648c`), a 32-entry signed speed curve (`01:6554`), and five motion/frame
records (`01:65f8`). The shared extraction helpers do not execute SM83 code.
Tests check template rotation, overflow rejection, deterministic extraction,
known map/list sizes and animation graph references. These are extraction
checks, not evidence of complete fidelity. The second stunt is now integrated
in the Windows development build.

Player states start at `01:5fa6`: rise (`5fae`), wait (`5fc9`), then gameplay
(`5fd6`). Gameplay updates the camera before movement (`659c`), damage (`6041`),
time, input, speed lookup (`6548`), map probes (`6459`), collision response
(`63de`), conveyors (`63af`), speed tiles (`6392`), walls (`6163`), finish gates
(`60a4`) and object collisions. The initial rise velocity is -40 fixed units,
increasing by one to zero, followed by a 224-tick wait. Tilt ranges from -2 to
2; speed index ranges from -20 to 11. Tilt input depends on the previous frame's
nonzero vertical rate. Held A reduces the index every four ticks; B increases
it every two. These details must not be replaced with guessed acceleration.

Other states are wall slide (`61c4`), crash (`6246`), explosion (`62a9`), hidden
return (`6336`), and finish motion (`6103`). Terrain impact adds 16 to an
unsigned damage byte, failing on overflow; bounce selects speed index -4 when
falling and +9 when rising. Finish gates award 50, or 150 for the bonus gate,
and compare collected items with the full quota and half-quota for result flags.
The ordinary global finish countdown is 128 updates. Native integration is implemented in `src/air.cpp`, including all eighteen
object definitions and the thirteen extracted animation roots. Audio remains unimplemented; reference timing is unverified.

The native Air HUD reconstructs `00:2f09` / `00:2f4c`: player number, four score
digits, BCD time, and six quota-bar tiles. It uses the original thirteen-column
update cycle, icons from `03:5820` / `03:5800`, and bar tiles at `03:5780`.
Unlike Roof Jump, this bar tracks `collected * 48 / quota`, not camera height.

Two easily missed ordering details are covered by native tests. The rise handler
falls into the first wait tick, leaving 223 after its final movement. The boost
countdown helper returns the zero flag of its old value, so a boost with one tick
left still uses the saved tilt for that frame. Input A and neutral vertical-axis
drag both execute on multiples of sixteen; simplifying this to a single choice
changes acceleration. Breaking the two-piece obstacle applies both a 16-point
terrain impact and a separate 32-point damage addition. Pickups encode decimal
score in BCD; they are not ordinary binary point values.

`00:1723` updates only the high byte of its two-byte random seed. The native
formula reproduces the subtract-with-borrow sequence, but starts each standalone
stunt with zero because the original menu seed/phase is not yet reconstructed.
Animation graphs use the original gameplay commands, not CPU instructions.
All world positions wrap at 16 bits; map lookup wraps at sixteen metatile columns.
Replay tests validate bounds and terminal states across all four difficulties;
these must not be presented as a reference-execution comparison.


## Asynchronous player sprite resources

Both native stunts now translate the original resource queue (`00:3f30`),
resource-copy budget (`00:1897`) and animation frame handshake (`00:3c74`).
A changed dynamic player frame keeps the old frame visible while copying up
to four 32-byte chunks per update. A pending background-row update has priority
(`00:09c9` / `00:0c3f`), detected when camera Y crosses bit 7 of its fixed-point
coordinate (`00:1ead`). On completion, the requested frame and flags install
together; status 2 remains visible to gameplay for one update and is then cleared.
Animation frame commands wait for that handshake before starting their delay.
Air tilt input and frame selection explicitly check this busy state. The roof
player's direct frame selection does not, so a newer request can replace a
pending one. Chunk counts are extracted as data, with no CPU execution.

Targeted tests cover row priority, four-chunk copying, atomic installation,
the completed-transfer input lock and animation delay ordering. With these rules,
the easy Air steering replay reaches result 03 with eight items. This is a native
regression result; no frame-by-frame original-execution comparison is claimed.


## Ski Slope

Initialization 00:0dc9 installs thirteen dynamic descriptors (03:66bc), 39
frame pointers (03:66f0), static sprites (05:6220), 127 background tiles
(05:67e0), four 64-entry metatile quadrants (05:7390) and collision flags
(05:7490). Four level records are at 00:0e9c. Template expansion 00:1db6
uses fifteen templates referenced at 00:1ded. Each list ends with an extra
(80,1f) band referencing RAM d5c5 beyond the declared map height. The extractor
retains only the declared playable rows: the extra band is outside the clamped
viewport. Its history-dependent RAM contents are not invented.

Player handlers: 01:697d initialization, 6986 skiing, 69fa jumping, 6e60 crash,
6e9c return. Turns skip neutral and wait for their animation; Down explicitly
returns to straight. Movement precedes velocity approach (6bc5); B performs
two approach steps per tick. Jump movement combines half the signed impulse
with +24 forward units; the shadow detects landing terrain. Finish requires
at least floor(initial flags / 2); collecting all flags yields result 07.
Collision handlers 6c45/6cbe collect flags, 6d1a kills, 6d39 awards a bonus,
and 6df8 starts crash/return. Return coordinates align to pixels to avoid
overshoot. HUD initialization/update is 00:2fb6/2fe7, with seven gradual fields.
Native tests derive from these rules but do not establish original equivalence.


## Bomb Factory

Initialization `00:0fce` loads 20 dynamic frame transfer descriptors at
`03:6aed`, 33 frame pointers at `03:6b3d`, static actor tiles `06:51a0`,
87 background tiles `06:57e0`, and a 7-by-17-tile belt room at `06:5d50`
repeated at columns 0, 7 and 14. Four six-byte records at `00:10cf` contain
three initial speeds, a BCD quota (40/50/60/70) and a 32-entry random-object
lookup table. Six marker actors advance with belt speed; wrapping from y=0x580
to y=0x180 requests one spawn for that lane on the next player update.

`01:6ef2` handles player input and quota. Left/right are press edges; vertical
walking and actions wait for a four-update cooldown. `01:6ff0` installs the
selected lane position only on the sprite-transfer completion handshake.
Punch/defuse sequences call collision only at their original animation events
(`0x94`, allowlisted callback `00:1747`). A defuses an armed bomb for 10 points;
a defused bomb reaching the end adds one to its belt count and five points.
B explodes a bomb and increases that belt's speed. B removes the three bonus
objects for 25/15/10; letting those fall increases speed and clears perfect.
The first missed armed bomb stops its belt and adds half its speed plus one
to both others. A second lost belt fails; reaching the quota returns 0x43 or
0x47 depending on the preserved perfect flag. The result delay is 64 updates.
Armed bombs on a stopped belt enter their original staggered explosion delay.

`tools/extract_bomb.py` produces local `TICDBOM1`; no ROM instructions are
executed. Native tests cover selected state transitions, bounds, replay
termination and synthetic success; they do not prove equivalence or a complete
successful run. Random state currently starts at zero until menus are ported.


## Cruise Missile

`00:1245` loads twelve transfer descriptors (`03:6fa8`), 42 frame pointers
(`03:6fd8`), 82 background tiles (`07:4980`), 2048 column-major map cells
(`07:4180`), 48 metatiles with four quadrants (`07:5940`), collision flags
(`07:5a00`), and static sprite tiles (`07:4ea0`). Four records at `00:1315`
select 60 seconds and object lists. Camera begins at (0,0x780); the player
begins at (0x410,0xd60), heading 4 and vertical velocity -24.

`01:73ed/73fd` implement the 32-update delay and ignition through counter 192.
Flight `01:744a` follows the camera, chooses the heading frame, moves using the
previous heading, then applies left/right turning every fourth update.
Sixteen records at `01:759e` contain frame, flags and thrust vector. A adds
acceleration every fourth update; without thrust, vertical speed approaches +8.
The original asymmetric negative saturation allows one overshoot below -16.
Four probes at `01:74bb` test terrain after actor collisions. Target collision
`01:7882` succeeds with result 0x23, or animated perfect result 0x27 at heading
12. Twelve-frame sprite transfers give map-column updates priority.

Actor handlers cover smoke, bouncing balls, rocket opening and launch,
magnetic attraction with a once-per-placement 75-point reward, oscillating
hazards, spring compression with a once-per-placement 50-point reward, and
extra-life pickups. The emitter's original difficulty check disables emission
when the stored byte equals one; the relevant actor only appears in the two
higher layouts. Native format `TICDCRU1` retains these data and animation graphs.
The out-of-map RAM behavior is not reconstructed: accesses outside the declared
128-by-16 cells return blank terrain. Natural successful runs and reference
frame/timing comparisons remain unverified.


## Shared collision rectangles

00:1747 independently masks world and camera coordinates to pixels, then retains
only byte-sized left/right/top/bottom values. 00:1834 compares unsigned edges:
player.right >= other.left, player.left < other.right, and the same for Y.
Far-edge overflow is not a conventional wrapping interval. All five native
stunts now use this explicit rule in `spriteBounds` / `spriteOverlap`.

## Outer loop and stationary title pages

00:0272 starts five lives per active player. 00:0465 chooses success by result
bit 1. Failure (00:059e) removes a life and retains day/difficulty without banking
stunt pay. Success (00:04c8,13ef,1415) transfers pay and seconds to six-digit BCD
savings, twice when bit 2 is set. Bit 6 suppresses time bonus. 00:0500 advances
through five days, then four difficulty levels. Players alternate at 00:0523;
inactive players are skipped. Completing difficulty four clears that player's
lives and shows the ending before returning to the remaining player.
`Campaign` translates these rules and is now wired to `UiFlow` and the Windows application.

Title scripts: 29ad,29bb,2a97,2a1b,2ade; options 2750. Durations at 2735 are
480/480/960/480/960 updates. A/B advances a title page; Select opens options;
Start begins play. Options toggle one/two players with Select/Up/Down. A/B returns
to the first title page; Start begins with the selected player count. Stable
raster phase (2502-2535) uses the unsigned font/window-map tiles at SCY=88 between
screen rows 24 and 103, with fixed signed-tile strips above and below. Page-change
scrolling and the intermediate dummy image still need runtime reconstruction.
The default eight high-score records are at 00:00a3 (three name tiles, three BCD
bytes each). They are copied during startup, not loaded from a cartridge save.
Result portraits load 07:72d2/76d2/7ad2 into tile 0x74; layout rectangles are
07:5df4/5e4e/5ea8. Stage instruction routines are indexed at 00:33b0;
success/failure text at 00:33ba/33c4. Text-language macros 89/8b insert player
name/number, 8a inserts Ski quota and 8c Bomb quota. This is a distinct layout
language, not CPU code. Unknown commands fail extraction.


## Native instruction and campaign presentation

`TICDUI02` retains five instruction atlases/maps/text streams, forty player/day/
difficulty headers, three result portrait atlases, sixteen result text maps,
result labels and both player variants of the ending. All content remains local.
Instruction tile ranges begin at 0x34; graphics are at 07:5f02/62d2/66d2/6ad2/6ed2.
Portrait layouts/text scripts are 06b7/06c5, 09fd/0a0b, 0c6d/0c7b,
0eea/0ef8 and 110b/1119. The original map pitch is 32 tiles.

Text routine 2154 waits five frames before each non-space glyph. Operation 85
(2219) scrolls by 1,2,3,1,1 pixels with two frame waits, then advances the text
row. The native renderer keeps screen lines 0-95 fixed and applies this scroll
to lines 96-143 (2556). Player names (2271/2277), quota macros (2296/22bb),
and the final start prompt (0332) are extracted rather than transcribed.
Start can skip instruction typing. The fixed headers and both name variants
are covered across every difficulty and day by native tests.

Failure text dispatch: Roof prioritizes bit 4, then bit 5, then bit 7; Air and
Cruise select by bit 4; Ski by bit 5; Bomb has one failure message. Result bit 2
selects the perfect portrait. Ending tiles are 06:6667 (44 tiles), layout/text
05e9 with its rectangle at 01:5526. The current native result screens show the
settled amounts immediately. Count-up, palette fades, raster/page transitions,
high-score name entry and exact phase timing still need implementation. The
ending is exercised through synthetic campaign success, not natural play.


## High-score input and result counting

`TICDUI03` adds the name-entry font patch (03:5840 into tile 0x26) and maps
from 322a/323c. Scores are eight six-byte records. The comparison at 31cf
inserts a score before the first record less than or equal to it, shifts later
records down and clears three initials. Scores survive campaigns within one
application session; the original has no persistent cartridge save.

The 32-glyph strip at 3390 contains letters, punctuation/space, backspace
(index 30) and finish (31). Native input follows 32c3: advance a pending signed
scroll by one pixel; approach its remaining eight-pixel motion to zero; start
another movement for held Left/Right when idle; process A/B edges. Selection
uses ((scroll + 76) & 248) / 8. Scroll starts at 180, selecting A. At most three
initials are stored; finish also accepts fewer. VBlank 24a5 and raster handlers
255d/256c horizontally scroll the lower strip and repeat its vertical lines.
Two original pointer tiles blink at x=76, y=112/136. Exact interrupt/draw phase
still needs reference comparison.

Result counting follows 0486-04fa/13ef/1415: 15-frame introduction, optional Ski
flag row plus 20 frames, savings plus 20 frames, one pay unit transferred each
frame, then (except Bomb) 15 frames and one remaining second each frame.
Perfect credit is two savings units for each consumed unit. A/B/Start accelerates
this presentation to its final total; a later press continues. The 600-frame
result timeout includes counting and never cuts it short. Game-over and ending
wait 480 frames before checking for a high score. Palette fades and exact
interrupt phase are not yet included in these counts.

Global timer phase C083 survives stage initialization and title return. The
application now carries it between timed campaign stunts; Bomb leaves it alone.
171c copies the global frame low byte into the high byte of the random seed.
Campaign starts now do this from the native global frame counter. Exact original
random sequences still differ when missing transitions change frame phase;
standalone tests retain explicit zero-phase deterministic starts.


## Title transition and audio data-language audit

27e6 closes the title center in 40 two-pixel updates (scroll 0 to -80); 27d4
opens it in another 40. Text maps change while closed, and the stationary page
timer starts only after opening. Native title changes now follow that sequence,
including options entry/exit. In 2502/2521 the upper part of the center uses
SCY=88+scroll until scanline 23-scroll, then SCY=88 through scanline 103. The
intermediate dummy tiles are already retained in each title map. Initial boot
and palette fades still need the full transition sequence. A hidden password/
cheat screen at 2b50 is also not yet ported.

Sound: 362a selects one of fourteen four-channel songs via eight 14-byte pointer
arrays at 3783-37f2. 3714 dispatches one of 26 effects at 37f3-385a, containing
pulse and/or noise streams (29 populated effect streams). VBlank calls the
bank-2 music update at 4000 after queuing effects. Music and effect voices are
separate software states; effect voices take over pulse 1/noise outputs.

`tools/analyze_audio.py` decodes the identified *music data language*, not SM83
instructions. All four music channels use commands 80-99, with separate handler
tables at 3986/39ba/39ee/3a22; effect tables are 3a56/3a8a. Commands cover counted
loops, duration mode, calls/returns, jumps, instrument parameters and termination.
Calls have up to three return slots. A zero per-note duration means 256 updates.
The tool follows all 56 music streams and 29 effect streams to termination or a
repeated control state. Instrument/wave references are recorded separately.
Title channel loops each span 2112 driver updates in this control analysis.
These counts do not establish waveform or exact playback equivalence. Native
synthesis/output, envelopes/modulation, register behavior and event wiring remain
unimplemented; the executable is still silent. Reports contain extracted data
and are written only locally (`local/audio-analysis.json` by default).


## Native sound driver and output

The extracted runtime commands are semantic records keyed by voice, stream
position and fixed-duration mode. Calls have three return slots; loop counts,
note durations and parameter arithmetic retain byte wrapping. The frequency
lookup preserves all 256 resolved indices: transposed silent notes can read past
the 97 musical entries in the original. Those resolved numbers are local data,
not executable instructions or a runtime ROM mapping.

02:404c/4330/4613/47ec update the four music voices; 49de/4cc8 update the two
effect voices afterward. Pulse envelopes (4165 onward), noise envelopes (48cc),
instrument hold/release tables, arpeggios, portamento and vibrato have initial
native translations. 46e3 unconditionally bypasses the wave modulation block;
the port retains that behavior. Wave volume selects a digital right shift.
00:3714 resets only specified effect fields. A missing effect root leaves its
other voice running, and 00:3711 is a single pending slot, not an event FIFO.

Sound generation uses pulse duty counters, a wave sample buffer and the noise
LFSR, integrating waveform edges over PCM samples before stereo mixing and a
DMG-style high-pass filter. Hardware basis: [Pan Docs audio details](https://github.com/gbdev/pandocs/blob/master/src/Audio_details.md)
and [audio registers](https://github.com/gbdev/pandocs/blob/master/src/Audio_Registers.md).
This does not reproduce every hardware quirk or intra-frame write timestamp;
precise reference audio comparison remains required. Buffer timing carries the
fractional 48 kHz sample count at 70,224 / 4,194,304 seconds per game update.

Music IDs come from 0261 (title), 031e (instructions), 09aa/0c1c/0e99/10cc/1312
(stunts), 0474/052e (success/perfect), 05ac (failure), 0694 (game over) and 32a6
(name entry). Animation opcode 93 queues effects. Direct stunt effect calls are
annotated by their associated original routines and use the same pending slot.


## Native gameplay sprite composition - September 30

The former flattened composites could not preserve raw transparent colors,
piece-level priority, or hardware sprite limits. Offline extraction now also
retains each frame's ordered 8x16 pieces: signed X/Y offsets, attribute flags,
and 128 unflipped color indices. No tile/code memory bus is used at runtime.
The five gameplay package versions are now `TICDNAT5`, `TICDAIR4`, `TICDSKI2`,
`TICDBOM2`, and `TICDCRU2`; old packages must be regenerated.

`src/sprites.h` directly composes a stored native sprite list. The ROM's
00:1bfb toggles allocation between ascending and descending slots. 00:1cfd
combines signed piece offsets with the frame origin/half extents, applies
entity flips, filters byte coordinates X>=168 / Y>=152, and XORs entity bits
5-7 with piece flags. Capacity is tested after each entity at 00:1c70; excess
pieces in the final entity fall outside the forty visible slots. This also
stops visibility/removal processing of later entities. Hidden or rejected
pieces do not advance allocation.

Selection takes the first ten vertical matches in slot order on each row,
then resolves opaque overlap by smaller X and smaller slot index. Color zero
is transparent. A nonzero color mapped to white remains opaque. Background
priority is checked only after the winning object pixel is chosen, so it can
mask lower-priority objects too. These display rules follow
[Pan Docs: OAM](https://github.com/gbdev/pandocs/blob/master/src/OAM.md).

All five stunts publish the list during the visibility pass, after their
handlers/resource completion and before placement scans (00:03de-03f9).
Windows repaint consumes this stored list; it neither advances allocation nor
makes newly scanned placements appear early. Palette selection uses OBP0=c4
and OBP1=e0. The gameplay/HUD boundary remains at row 136. Ski's former
whole-composite priority workaround was removed.

Validation includes 23 synthetic native rendering assertions, four native
simulation/publication assertions, raw-piece extraction compared with source
bytes, and the existing all-difficulty/campaign runs. Native screenshots were
inspected locally; these are not original-game image comparisons. Slot parity
is currently based on stage update parity. Exact first displayed frame,
menus/fades, video-transfer latency and global presentation phase remain open.


## Original boot presentation

00:280c displays the 20x18 copyright tilemap referenced by text script 2814.
Song 0 starts before the 20d1 fade-in. The palette table at 2118 is
E4/E4/E4/A4/90/50/50/00: fade-in traverses it backwards, fade-out forwards,
each entry lasting four updates. 25c4 waits a fixed 180 updates without reading
buttons. Native Boot reproduces these 32/180/32 update sections.

After that, 0217 installs the title background and blank/dummy center map.
0259 fades in, 025c waits once, 0261 starts song 1, and 26ea closes the center
for 40 updates, installs page zero while closed, then opens for 40 updates.
Native TitleIntro reproduces this order; the stationary page timer begins only
when opening finishes. Startup input is consumed and cannot skip the copyright
or start a campaign with a button held through the transition. The music is
not spuriously restarted when moving between these opening phases.

`TICDUI04` appends the copyright map, initial title map and palette sequence.
Normal Windows startup invokes `beginBoot`; F6 returns directly to the title,
and isolated UI/campaign harnesses start at the title unless testing boot.
Ten additional native UI assertions cover section boundaries and held input.
Copyright and title-closing captures were inspected locally. LCD enable/setup
waits, exact first-VBlank alignment and other inter-screen fades remain open;
357 modeled opening updates are not a claimed power-on reference timestamp.


## Shared gameplay frame counter

The counter at C00A/B increments in VBlank (00:2459-2467), including menus
and pauses. Periodic Air input branches explicitly read its low byte at
01:6504/6514/6520/6534. The Windows campaign now supplies the current global
UI frame to the selected stunt before each update instead of starting these
phases at zero on every stage. The native counter wraps at 16 bits. Isolated
stunt tests/development starts still use a deterministic zero initial phase.

Sprite allocation is a separate toggle at 00:1bfb, reset by the common stunt
setup at 00:0386. It now toggles per visibility pass independently of that
global counter. This preserves its direction when the global counter advances
while gameplay is paused. The campaign harness also passes the global frame;
its easy-Air pilot searches ordinary alternating input schedules on copies at
the actual phase instead of assuming a zero-phase start. No measured game state
is patched by the pilot. Missing fades/setup waits still prevent an exact
original power-on frame phase claim.
