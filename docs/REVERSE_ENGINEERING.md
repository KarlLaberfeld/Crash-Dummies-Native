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

- `01:55da–563a`: flyover, waiting and roof start sequence.
- `01:56de`: main falling update, held lateral input and pressed posture input.
- `01:5748`: Q12.4 position updates and X clamp to 0x1040–0x1880.
- `01:59cc/59d2`: lateral velocity -10/+10 fixed-point units.
- `01:5a0e–5a81`: neutral/spread/head-first target velocities 24/20/28.
- `01:5a8b`: vertical velocity moves one unit toward pose target.
- `01:5c8b`: awning damage count; head-first/spread break, neutral bounces.
- `01:5ef3`: solid balcony breaks once; neutral bounce -4, reward 5/10.
- `01:5f29`: landing target, reward 100, one-time removal.
- `00:312d`: BCD timer decremented after 60 updates.
- `00:3b80–3cfa`: animation commands, loops, positions, frame changes and native-handler transitions.
- `00:3e75`: camera tracking expressed directly in native integer arithmetic.

## Corrections verified against static routines, 2026-09-29

- Sprite origin: `00:1cdb/1cf3` adds header bytes 6/7 (half extents) to
  the display offset before the piece offsets. Hardware coordinate biases
  +8/+16 cancel when drawing the screen. Whole-frame mirroring uses that
  same center. The previous extraction omitted the half extents, displacing
  graphics relative to their collision boxes. Data format `TICDNAT2` prevents
  silently loading old images; regenerate `crash.dat` after updating.
- `00:1cb6–1cf6`: padded visibility bounds, after display offset, are
  X [-2*halfWidth-16, 176], Y [-2*halfHeight-16, 152], inclusive.
  Offscreen flags are updated after entity handlers and before placement scans.
  Native repaint frequency does not affect this state. Original OAM capacity,
  per-scanline sprite limits and alternating priority are still unimplemented.
- `00:3da5` removes a live entity without resetting its placement's active
  byte. Only visibility eviction with flag bits 4 and 2 clears that byte
  (`00:1c91–1cb2`). A collected target therefore cannot reappear on a later scan.
- `01:55fe` activates balloons/planes at the end of the intro camera rise;
  this is separate from animation command 0x92 (`00:3cf1`, sound-driver gate).
  `01:563a` processes walking before the jump button. Held lateral input can
  legitimately postpone the jump, so test replays release steering during it.
- `01:5c8b` tests pose before upward velocity. Spread/dive contact breaks
  awnings even while rising; neutral upward contact does nothing. Four neutral
  rebounds have velocities -41, -37, -33, -29; the fifth breaks the awning.
- `01:5dbd/5dd7`: plane stun retains the definition's 0x40 countdown rather
  than resetting it to 0x20. Collision stays disabled after the plane resumes.
- `01:5722–584d`: only the main fall handler checks the ground row, snaps
  Y to the next tile row, and chooses a landing sequence. Bounce/rope-release
  handlers have their own updates. A head-first miss plays script `01:57cf`.
  A target landing spawns five body pieces; the upward piece's script reaches
  `01:59b6`, which starts the 64-update result delay. The player stays idle.
  Result flags are 0x81 for insufficient breaks, 0x03 for success, and 0x07
  for success with no remaining objects. Ten breaks leave the initial counter
  at zero: eleven are required to set its sign bit. Timeout/fire use 0x11/0x21.
- `01:5778` falls through to timeout movement on the same update; `01:59b6`
  similarly performs the first countdown decrement immediately.

Validation: ten Python tests (including independent OAM-coordinate projection),
native regression checks and deterministic replays for all four roof lists.
Windows x64 GUI executable (PE subsystem 2), hidden-window smoke test and
local image capture passed. This is static source-derived validation, **not**
a frame-by-frame comparison to original hardware. No CPU emulator was run
for this continuation.

## Unverified or incomplete

The runtime is not yet a matching reconstruction. In particular:

- The original asynchronous graphics-transfer stalls are not reproduced.
- Roof frame ordering, offscreen lifecycle and all edge-case collisions need
  comparison with a reference execution; current tests only validate native
  invariants and selected translated rules.
- The corrected plane/landing rules above still need reference timing checks;
  balloon/rope interactions and several entity flags need further analysis.
- Decorative cloud entities and some transient effects are absent.
- Palette register changes, original status-bar layout and intro/menu text
  are not fully reconstructed; the launcher explicitly identifies the build
  as work in progress.
- No original sound driver, other four stunts, campaign or ending.

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
