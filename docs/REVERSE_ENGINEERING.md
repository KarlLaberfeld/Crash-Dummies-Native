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
  Native repaint frequency does not affect this state. Original OAM capacity,
  per-scanline sprite limits and alternating priority are still unimplemented.
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

- The original asynchronous graphics-transfer stalls are not reproduced.
- Roof frame ordering, offscreen lifecycle and all edge-case collisions need
  comparison with a reference execution; current tests only validate native
  invariants and selected translated rules.
- The corrected plane/landing rules above still need reference timing checks;
  balloon/rope interactions and several entity flags need further analysis.
- Some transient effects and original sprite priority/capacity are absent.
- Palette register changes and intro/menu text are not fully reconstructed;
  the launcher explicitly identifies the build
  as work in progress.
- No original sound driver, other three stunts, campaign or ending.

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

`tools/extract_air.py` writes the local-only `TICDAIR2` data pack. It includes
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
object definitions and the thirteen extracted animation roots. Audio and original
graphics-transfer delays remain unimplemented; reference timing is unverified.

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
