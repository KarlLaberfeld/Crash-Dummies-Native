# Selected complete Air framebuffer comparisons

October 7 follow-up: the successful control's staged/published background now
has a native completion owner, including its formerly rejected interruption.
Three consecutive neighboring images match exactly; all 262 prior selections
pass again. Total: 265 complete images / 6,105,600 pixels. See
[row publication and bounds](AIR_MAP_PUBLICATION.md). Production scheduling
remains unchanged. The six-control counts below describe the earlier selection.

The six existing independent SameBoy controls now match **262 unique complete
160x144 images**, or **6,036,480 compared pixels**, with zero differences.
The earlier 258-image selection and five consecutive late images overlap once.
This closes the three known differing sprite pixels and the outgoing-palette
qualification for this selection. It is a correction to the bounded native
clock/image probe, not production Windows scheduler integration or final acceptance.

| Control | Selected images | Coverage |
|---|---:|---|
| Normal coast, 31-frame pause hold | 29 | Incoming fade, play, pause, resume and later motion |
| Easy coast, 120-frame pause hold | 29 | Same boundaries on easy |
| Hardest boost, 255-frame pause hold | 29 | Same boundaries on hardest |
| Normal timeout | 57 | Incoming fade, play and outgoing fade |
| Easy damage/explosion | 57 | Incoming fade, play and outgoing fade |
| Easy alternating steering, period 44 / offset 12 | 61 | Incoming fade, five consecutive late object-cancellation images and outgoing fade after damage |

These extend the existing controls; they are not six new scenarios. Blank
fade images and repeated frozen scenes are included, so 262 image checks do
not mean 262 distinct situations. The last original capture's historical
directory suffix is `win`, but this SameBoy control ends in damage, not success.
Do not count it as a successful-finish image comparison. Earlier successful
PyBoy timing evidence remains separate.

## Alignment and ownership

`air_pixels.py capture` reads the original completed framebuffer at the single
`00:2430` pre-DMA boundary. It records service, selector, palettes, scroll and
selected read-only LCDC-disable observations. Every capture preserves its
uninstrumented 32,768-byte end-state digest and pinned ROM/backend/model/revision
provenance. No original memory writes are used. This is emulator reference
evidence; no original hardware has been measured.

`air_clock_probe --frames-dir ... --frame-services ...` projects the native
scene after its display callback. That publication is compared with the
completed original framebuffer before the following DMA: native service N
against original service N+1. This relation follows publication order, not
a searched frame shift. Per-frame original worlds, palettes, OAM, pixels,
edges, costs or cycles do not enter the native process. Only the established
initial clock/timer/RNG header and raw held-button samples drive the replay.
Graphics and palette tables come from the local extracted native assets.

Both sides use the reference's four gray levels. All 23,040 pixels of every
image are compared; no HUD, sprite, edge or blank region is masked. The
comparator verifies original hashes, geometry and provenance and writes local
difference images. `productionPixelsAccepted: false` remains explicit.

## Final gameplay row: the three differing pixels

The previous easy alternating-steering projection drew three extra black
pixels at (108,135), (109,135) and (110,135), original service 1500 / native
publication 1499. The original shows the background there. Its source STAT
handler (`0048`, `24e4`, then `2549..254f`) clears LCDC object enable while
line 135 is still drawing. A fetch in progress is cancelled at that edge.

The optional clock observer derives the write from the native STAT entry:
20 cycles of interrupt entry, a 228-cycle identified source prefix, the
8-cycle register access and the pinned bus observer's two-cycle sampling
convention. In the accepted counter-wait/HALT witness this gives line dot
262 after the established eight-cycle LCD phase adjustment. The read-only
original bus witness independently agrees. Its coordinates and timing are
comparison targets, never native inputs.

`airLastLineObjectLimit` uses native published geometry, SCX and the first ten
selected objects to derive the per-row fetch stalls and cancellation position.
Transparent selected pieces still contribute fetch work. The source-owned
edge cancels the object starting at x=108; only later object output is omitted,
while the actual native background is retained. This changes no earlier row
or HUD pixel. The complete original image now agrees.

The identified placement accesses and conditional returns now complete before
pending interrupt acceptance. Original services 1498 and 1499, previously
rejected, independently match the native object-disable edge at dot 270 and
their complete images. Services 1500..1502 match the counter-wait edge at dot
262. One overlaps the earlier image selection, giving four additional unique
images. All 77 placement interrupt vectors separately agree exactly; see
[completion evidence](AIR_IRQ_BOUNDARIES.md).

Other aggregate acceptance remains unqualified. Such an edge is accepted only
when a conservative 24-cycle range changes none of that scene's actual object
pixels; otherwise it rejects. Pending protected pause crossings also reject
without independent evidence. General interrupt acceptance is still open.

## Outgoing fade: visible palette writes

The earlier image export used the gameplay fade palette throughout the outro.
Replacing it with a single new palette per image is also insufficient: an
outgoing HUD refresh can delay the main-thread palette change until part of
the next visible frame has already been drawn. The source at `20b9..20c5`
writes BGP, OBP1 and OBP0 at separate offsets of 16, 36 and 64 cycles.
The pinned bus observer samples each two cycles earlier.

The projection retains a native palette owner for each visible pixel:
background/window, OBP0 or OBP1. It derives output time from its own line phase,
scroll and selected object geometry, and applies the corresponding source
palette write only to pixels that have not yet been output. Already drawn
pixels keep the previous palette. Background-masked and cancelled objects
do not claim object-palette ownership. An interruption of the palette prefix
still rejects; no observed prefix timing is supplied as a scheduling delay.

The 32 consecutive images selected around each outgoing interval now agree,
alongside the other 25 selected images. They cover every palette stage; the
last publication has no following pre-DMA target and is not an extra image
comparison. The same replays retain exact agreement for all 222 exit
phases and 96 outgoing display services, including the register palettes,
work, waits, counters, HUD and held buttons. This does not compare the result
screen after `0409`, audio PCM or a successful result transition.

## Local reproduction

Build the clock probe as described in AIR_PAUSE_CANDIDATE.md. Create the native
output directory first. Normal-coast pause example:

```powershell
python tools/air_pixels.py capture 'path/to/original.gb' --capture local/sameboy-air-pause-coast --out local/pause-pixels-coast-reference --services 1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,100,299,305,320,340,500,1000,2000,4000
./local/air-clock-probe.exe local/pause-coupled-coast/inputs.txt local/pause-pixels-coast-native/services.csv 1 --display-inputs local/pause-coupled-coast/buttons.txt --pause-replay --frames-dir local/pause-pixels-coast-native --frame-services 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,99,298,304,319,339,499,999,1999,3999 > local/pause-pixels-coast-native/states.csv
python tools/air_pixels.py compare --capture local/sameboy-air-pause-coast --out local/pause-pixels-coast-reference --native-dir local/pause-pixels-coast-native
```

Easy/hard pause cases use difficulty 0/3 and matching input/control paths.
Both select original services 1 through 20. Easy additionally selects
100,499,505,560,620,630,1000,2000,2900; hardest selects
99,105,200,300,370,500,750,980,985.

For each outgoing control use `local/sameboy-air-outro-{timeout,damage,win}`,
its `inputs.txt` and `local/sameboy-outro-{case}-buttons.txt`, difficulty 1/0/0,
and `--outro-fade`. Select original services 1..20,100,500,1000,1500,1800
and 32 consecutive services n-32..n-1, where n is respectively 4023/1902/1866.
The native selection is each original index minus one. Capture/compare into
`local/outro-pixels-{case}-reference/` and matching `-native/` folders.
For the extra LCDC bus witness use the `win` control with original services
1498,1499,1500,1501,1502 and inspect `objectDisableWrites` in `frames.json`.
The native `edges.csv` records only native-derived edges and cancellation limits.
All images, measurements, ROM and extracted assets remain ignored/local.

## Remaining qualification

The Windows application retains its existing scheduler and default rendering
cadence; the optional publication cutoff/owner plane is used by this clock
probe. Integrating the accepted owners requires the production clock work,
not copying original measurements into the game. Initial LCD-enable access,
arbitrary IRQ acceptance, interrupted entity/resource owners, pause-entry
visible changes and result setup remain open. Wider collisions/success cases,
other stunts, PCM, human play and independent Windows/hardware acceptance
remain required under ACCEPTANCE.md. This is not a final release.
