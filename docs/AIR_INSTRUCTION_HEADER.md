# Native result-cleared instruction header

The diagnostic now extends the native result handoff through 02ce..031c:
player name, lives, stunt and difficulty labels, their LCD-safe glyph stores,
and the first counter wait before instruction music starts. Campaign values,
clock, held/fresh inputs and published geometry come from native preceding
gameplay/result/handoff. The original recording supplies comparison targets.

Five existing original controls agree with zero differences:

| Control | Boundaries | Displays | Vectors | LCD polls | Intended glyph writes |
|---|---:|---:|---:|---:|---:|
| Perfect success | 12 | 1 | 2 | 283 | 41 |
| Ordinary success | 12 | 1 | 2 | 290 | 41 |
| Damage | 12 | 1 | 2 | 278 | 39 |
| Timeout, difficulty one | 12 | 1 | 2 | 262 | 37 |
| Alternating-steering damage (`win` directory) | 12 | 1 | 2 | 278 | 39 |
| Total | 60 | 5 | 10 | 1,391 | 197 |

These extend the same existing input-only controls, not five new gameplay
patterns. Every instrumented original retains its full 32,768-byte terminal
control hash, pinned reference provenance and separately qualified startup
epoch. The comparator requires complete boundaries/accesses/vectors and the
actual global result-service index; a truncated common prefix cannot pass.

`air_instruction_header.h` owns the identified header sequence. Its locally
decoded TICDIH01 package contains twelve semantic layout lists and six player
glyphs. It contains no cartridge instructions, code pointers, reference times
or modes. The ordinary result writer retains its existing behavior; its new
word substitution reproduces the identified three-glyph branch and its saved
text cursor. Lives clamp to nine for display while the campaign retains its
actual value. Both player names and lives 1/9/255 have synthetic checks; the
original controls witness the first player with four or five lives only.

Music remains stopped. Perfect selector two publishes its retained sprite list
but omits emitter advancement after the result clear, charging the shorter
68-cycle branch. Its STAT remains selector four. Ordinary controls retain
selector ten / zero. The header's original comparison covers scalar state/work,
full IRQ times, LCD-mode polls and intended glyph bytes/destinations. It does
not independently certify complete pictures, bus acceptance, PCM, physical
hardware, or Windows presentation timing.

Local evidence: `local/air-perfect-header-reference/`,
`local/air-perfect-header-services.csv.header*`,
`local/air-header-{success,damage,timeout,win}-{reference,native}/`,
`local/air-header-original-comparisons.log` and matching comparison logs.
The optimized diagnostic, 18,720 ROM-free result assertions and 308 Python
tests pass. The production Windows EXE/scheduler remains unchanged.

```text
python tools/extract_ui.py <local.gb> --out build
python tools/air_instruction_header_reference.py capture <local.gb> --capture local/sameboy-air-perfect --out local/air-perfect-header-reference
local/air-clock-probe.exe local/sameboy-air-perfect/inputs.txt local/air-perfect-header-services.csv 0 --display-inputs local/air-perfect-buttons.txt --result-inputs local/air-perfect-header-reference/buttons.txt --instruction-header
python tools/air_instruction_header_reference.py compare local/air-perfect-header-services.csv.header.csv --capture local/sameboy-air-perfect --out local/air-perfect-header-reference --startup local/air-perfect-startup
```

Next: instruction music, graphics copy, picture/map transition, timed text,
input-driven exit/fade and following LCD/gameplay setup. Final-life/reset,
earlier UI/LCD entry, unobserved interrupted owners and production integration
also remain required. Timing point 1 and final-release acceptance are incomplete.
