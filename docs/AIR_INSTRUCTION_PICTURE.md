# Native instruction music and picture prefix

The diagnostic continues from the completed header at 031c through instruction
music startup, the 1,024-byte tile copy and the ten-by-nine picture rectangle,
ending explicitly at transition entry 268b. Both following Air instructions
(retry Air and success-to-Ski) use source-derived native operations. Tile bytes
are repacked from locally decoded native pixel assets; the rectangle uses its
native instruction map. No original cost, mode, byte stream or outcome drives
execution, and no Game Boy CPU is executed.

Five existing originals match with zero differences:

| Control | Boundaries | Displays | Vectors | LCD polls | Intended writes |
|---|---:|---:|---:|---:|---:|
| Perfect success | 9 | 4 | 8 | 5,282 | 1,114 |
| Ordinary success | 9 | 4 | 8 | 5,255 | 1,114 |
| Damage | 9 | 4 | 8 | 5,276 | 1,114 |
| Timeout | 9 | 4 | 8 | 5,276 | 1,114 |
| Alternating-steering damage (`win` directory) | 9 | 4 | 8 | 5,276 | 1,114 |
| Total | 45 | 20 | 40 | 26,365 | 5,570 |

The 1,114 writes in each control contain 1,024 tile bytes and 90 map glyphs;
the counts extend those controls and do not represent new gameplay patterns.
Every absolute source boundary, full IRQ vector, display/audio work component,
held/fresh input, timer/tick and intended byte/destination agrees. Original
instrumentation preserves the full 32,768-byte control hash and pinned reference
provenance. The separately qualified startup epoch and global result-service
index prevent prefix-only or relative-delay acceptance.

The song-two reset/start has a complete source-work owner only when no display
request crosses it. The five controls witness that interval; unknown crossings
reject before starting the song. Each tile and glyph polls readiness separately.
The copy retains each source byte across pending services, while the rectangle
retains its source row pitch and row-carry branch. Native accesses service IRQs
only at identified completed operations. Observed LCD readbacks and intended
writes qualify this source timeline, not physical bus acceptance, complete
images, PCM or Windows presentation scheduling.

The optimized diagnostic, 31,103 ROM-free result assertions and 320 Python
tests pass. Synthetic cases independently exercise plane/pixel ordering,
complete tile/map destinations and rejection of interrupted music startup.
Local evidence: `local/air-perfect-picture-reference/`,
`local/air-perfect-picture-services.csv.picture*`,
`local/air-picture-{success,damage,timeout,win}-{reference,native}/`,
`local/air-picture-original-comparisons.log`, `local/air-picture-result-tests.log`
and `local/air-picture-python-tests.log`. ROM/assets/captures remain local.

```text
python tools/air_instruction_picture_reference.py capture <local.gb> --capture local/sameboy-air-perfect --out local/air-perfect-picture-reference
local/air-clock-probe.exe local/sameboy-air-perfect/inputs.txt local/air-perfect-picture-services.csv 0 --display-inputs local/air-perfect-buttons.txt --result-inputs local/air-perfect-picture-reference/buttons.txt --instruction-picture
python tools/air_instruction_picture_reference.py compare local/air-perfect-picture-services.csv.picture.csv --capture local/sameboy-air-perfect --out local/air-perfect-picture-reference --startup local/air-perfect-startup
```

Next is the 64-step background-map transition, followed by timed instruction
text, input/exit fade and subsequent LCD/gameplay entry. Final-life/reset,
earlier UI/LCD, unobserved interrupted owners and production integration remain
required. The production EXE is unchanged; point 1 and final acceptance remain
incomplete.
