# Following instruction-to-stunt startup timing

The diagnostic native clock now owns the complete following startup from 0355
to 03d8, immediately before the next stunt's first update. Four existing,
input-only SameBoy controls qualify one easy Air retry and three easy Ski starts
(ordinary success and held Start after name/quota skipping). Each recording
replays the full original control and preserves its 32,768-byte terminal-memory
hash. The separate reference remains outside the native game.

| Interval | Boundary comparisons | Display services | Complete vectors | LY reads | Intended stores |
|---|---:|---:|---:|---:|---:|
| 0355..0367, LCD-off and clears | 20 | 0 | 0 | 6,941 | 2,048 |
| 0367..039c, masked stage setup | 50 | 0 | 0 | — | Not compared |
| 039c..03d8, resources/HUD/restart | 48 | 8 | 16 | — | Not compared |

All comparisons have zero differences. The 118 boundary comparisons include
four repeated 039c handoff endpoints: there are 114 distinct boundary samples
across these intervals. They extend the four instruction-exit controls, rather
than adding four independent main-gameplay cases. All preceding instruction-exit
comparisons pass again on these complete native replays.

## Native ownership

`airFollowingSetupPrefix` inherits the native instruction LCD epoch and waits
for equality with LY 145. Reads occur at identified sample/completion boundaries,
including LY's line-153 behavior. Services are masked while the LCD is disabled.
Both complete 256-byte buffers are then filled (objects with zero, actors with
the vacant sentinel). Every intended store and destination agrees independently.
Counter and countdown remain frozen. The pending requests are derived from
native deadlines; the observed qualifying paths retain both requests.

`airFollowingStageSetup` accounts for the Air/Ski resource-root copies, terrain
and quadrant copies, rotated 16-column/four-row map bands, placement expansion
and coordinate offset, initial actors/sprite copy, all 32 initial map rows and
quiet music startup. Work follows decoded data lengths and carry branches.
The initial-row direction uses word-wrapped world coordinates, including the
shorter high-difficulty Air branch; that branch has a synthetic regression,
not a new original-control qualification.

`extract_following_setup.py` writes the ignored `following-setup.dat`: eight
fixed semantic metadata records (band/table-carry/placement/chunk counts and
world coordinates). It reads no reference capture or timing. The binary contains
no instructions, observed budgets, counters, native outcomes or audio seeds.
Ski's extra offscreen RAM-template band is counted for its fixed work only;
its unestablished data contents are not fabricated or certified.

`airFollowingEntry` derives the scene seed from the native pre-service tick,
owns thirteen 16-byte glyph copies and the different Air/Ski HUD setup, restarts
the LCD, and retains VBlank-before-STAT priority for the pending requests.
The first counter wait has separate periodic STAT/VBlank vectors. The two
display callbacks own the native row upload, HUD columns, alternating fade,
raw held/fresh input and software music/effect work. No entity update occurs.
Their selected source body costs are 1,508/1,676 according to native tick parity.
The ready flag is cleared before the final input/pause test.

C00C/D has a map-row publication role in this interval. It is compared after
native map preparation, independently of the scene RNG state at C09E/F.
Inherited unused camera/scratch values before their owners overwrite them are
excluded from comparison; completed camera values, map scratch, seed reset and
derived scene seed are compared explicitly.

## Reproduction and checks

Extract the diagnostic workload metadata locally:

```powershell
python tools/extract_following_setup.py 'Incredible Crash Dummies, The (USA, Europe).gb' --out build/following-setup.dat
```

The optimized native probe accepts `--following-setup-prefix`,
`--following-stage-setup` and `--following-entry`; each includes its preceding
native instruction/result owners. The full entry consumes the two additional
raw display-button samples exported by `air_following_entry_reference.py`.
The three reference tools have separate `capture`/`compare` commands. Comparisons
check backend and ROM/control identities, complete explicit interval coverage,
absolute times against the independently recorded initial LCD epoch, continuing
result-service indices, all vectors, masked counters and handoff attachment.
Missing/reordered boundaries, native truncation and unknown owners reject.

Latest validation: optimized Windows diagnostic; 52,850 ROM-free native result
assertions and 394 Python tests, including coverage/identity checks, lost or
reordered stores/vectors, row/RNG role separation, missing workload records,
native counter wrap and first-entry pause rejection. The temporary binary test
uses the writable local test directory; an initial sandbox temp-directory
permission failure was repaired and the complete suite passes.

Local evidence: `local/air-following-{retry,ski,name,quota}-prefix-reference/`,
the matching `*-prefix-services.csv.following-*` outputs,
`local/air-following-final-original-comparisons.log`,
`local/air-following-result-tests.log` and `local/air-following-python-tests.log`.
ROM, decoded data, captures and original recordings remain ignored/local.

## Remaining scope

These controls qualify easy following-startup timing and selected semantic
states. Stage resource/HUD/actor buffer contents, physical bus writes, complete
startup images/PCM and subsequent restarted gameplay are not certified here.
Fresh Start at 03d5 needs the separate entry-pause owner and currently rejects.
Earlier boot/title/first-instruction startup, genuine final-life/reset paths,
unobserved interrupted owners and production Windows scheduling remain open.
The production `CrashDummies.exe` is unchanged (SHA-256
`e8cf2b18eed34d86220f074b51310dbe3c61923cabe4062defa0bf729d3272d3`).
Point 1 and final-release acceptance remain incomplete. No final package or
release is produced and the continuation automation remains required.
