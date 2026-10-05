# Selected complete Air framebuffer comparisons

Three independent SameBoy controls now match **87 complete 160x144 images**:
29 per case, or **2,004,480 compared pixels**, with zero differences. The cases
are normal coast with a 31-frame pause hold, easy coast with a 120-frame hold,
and hardest boost with a 255-frame hold. They are the existing coupled pause
controls, not new input scenarios or original-hardware recordings.

Each selection includes the first twenty complete gameplay display frames,
then nine frames covering ordinary play, the visible pause, post-resume play
and later stunt motion. The first frames include the source-derived incoming
palette fade. Blank fade frames and repeated frozen pause images are included;
87 image checks do not mean 87 distinct situations. Other stunts, collisions,
success/result transitions, outgoing fades and partial visible writes are not
certified by this selection.

## Alignment and ownership

`air_pixels.py capture` reads the original completed framebuffer at the single
`00:2430` pre-DMA boundary. It also records the service index, selector, palette
and scroll metadata. Pixels are observations only. Every capture preserves
the existing uninstrumented 32,768-byte end-state digest and pinned reference
ROM/backend/model/revision provenance. No original memory writes are used.

`air_clock_probe --frames-dir ... --frame-services ...` projects the native
scene after its display callback. That publication is compared with the
completed original framebuffer before the following DMA: native service N
against original service N+1. This relation follows the publication order,
not a searched frame shift. Per-frame original worlds, palettes, OAM, tiles,
pixels, cycles or costs do not enter the native process. Only the established
initial clock/timer/RNG header and raw held-button samples drive the replay.

The native image uses `AirGame::render(false)`, its published sprite/camera/
HUD state, the existing native pause-strip compositor and locally extracted UI
fade palettes indexed by its own source-derived remaining-fade counter. The
optional image export leaves complete world and service logs byte-identical
to the coupled replay without image export. It does not change the Windows
runtime, its scheduler or existing preview package.

Both sides are normalized to the independent reference's four gray levels.
All 23,040 pixels are compared; no HUD, sprite, edge or blank region is masked.
The comparator verifies original image hashes, geometry and recording provenance,
and writes local difference images. `productionPixelsAccepted: false` remains
explicit: selected whole-frame agreement is not arbitrary scanline ownership.

## Local reproduction

Build the current clock probe as described in AIR_PAUSE_CANDIDATE.md. Create
the native output directory before running. Example for normal coast:

```powershell
python tools/air_pixels.py capture 'path/to/original.gb' --capture local/sameboy-air-pause-coast --out local/pause-pixels-coast-reference --services 1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,100,299,305,320,340,500,1000,2000,4000
./local/air-clock-probe.exe local/pause-coupled-coast/inputs.txt local/pause-pixels-coast-native/services.csv 1 --display-inputs local/pause-coupled-coast/buttons.txt --pause-replay --frames-dir local/pause-pixels-coast-native --frame-services 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,99,298,304,319,339,499,999,1999,3999 > local/pause-pixels-coast-native/states.csv
python tools/air_pixels.py compare --capture local/sameboy-air-pause-coast --out local/pause-pixels-coast-reference --native-dir local/pause-pixels-coast-native
```

The easy/hard cases use difficulty 0/3 and their matching input/control paths.
Both also select original services 1 through 20. Easy additionally selects
100,499,505,560,620,630,1000,2000,2900; hardest selects
99,105,200,300,370,500,750,980,985. Native selections are each original index
minus one. All images, input files, extracted graphics and measurements remain
ignored/local; only diagnostic source and this English report are published.

## Remaining image and timing qualification

The incoming whole frames agree, including their fade palette, but this does
not identify all first-LCD-frame access modes or preceding UI startup work.
The pause access model still rejects that first frame and unsupported special
window/line-135 edges. Mid-frame graphics changes around entering/leaving pause
are not covered by the selected steady frames. Arbitrary interrupt latency,
interrupted entity/resource/map owners, production clock integration and result
setup remain open. Original-hardware, PCM, other-stunt and independent Windows
acceptance remain required under ACCEPTANCE.md. This is not a final release.
