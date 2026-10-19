# Complete final Air gameplay and outgoing fade

October 19, 2026. Continues the two accepted
[one-life instruction/final entries](AIR_FIFTH_ENTRY.md) through terminal
gameplay, audio stop and the outgoing fade. The subsequent result, consumption
of the final life and game-over flow remain unqualified. Production Windows
EXE/scheduler and the alpha release are unchanged.

## Compared scope

| Scope | Ordinary | Earlier second-entry pause | Combined |
|---|---:|---:|---:|
| Gameplay updates | 1,789 | 1,762 | 3,551 |
| Gameplay boundaries | 17,890 | 17,620 | 35,510 |
| Actor slots | 286,240 | 281,920 | 568,160 |
| Gameplay displays | 1,792 | 1,767 | 3,559 |
| Complete gameplay vectors | 3,584 | 3,534 | 7,118 |
| Published object slots | 71,680 | 70,680 | 142,360 |
| Complete row boundaries, including entry | 3,590 | 3,540 | 7,130 |
| Compared row bytes | 3,791,040 | 3,738,240 | 7,529,280 |
| Separate side-push boundaries | 17,890 | 17,620 | 35,510 |
| Outgoing phases | 74 | 74 | 148 |
| Outgoing displays / vectors | 32 / 64 | 32 / 64 | 64 / 128 |
| Outgoing object slots | 1,280 | 1,280 | 2,560 |

All compared fields have zero differences. These complete gameplay totals
include the previously accepted first update. Row coverage includes the two
entry displays in each case. The ordinary blocked terminal tile endpoint
retains the preceding unblocked tile storage only across the independently
observed interval with zero tile-write attempts; the paused endpoint is read
unblocked. This does not qualify arbitrary blocked storage reads or pixels.

The timer retains phases 33 / 43 from the current fourth game, advances
1,400 / 1,373 times, and rolls over 23 times in each history. Resource proof
covers 46 / 45 requests and completions, 174 / 170 uploads and 25 / 27 deferred
map displays. The separately observed inherited side push is zero; its first
Play steering branch takes 92 cycles and the later scratch values match all
gameplay boundaries, including the terminal wait/end.

The native adapter now accepts explicit fifth update extent and terminal
ownership, using the same native update/outgoing owners as earlier attempts.
It continues the actual completed fourth game through its one-life instruction
and fifth entry. No source timestamps, snapshots, addresses or per-update
schedules drive this continuation. The diagnostic's existing initial
phase/counter/seed header, decoded assets and raw display button samples remain
its input; this adds no new original-state initialization. No semantic core
timing or gameplay owner changed in this checkpoint.

The original controls preserve the complete accepted final-entry events and
append 1,800 frames with unchanged buttons. Two uninstrumented repetitions per
case match both the parent's RAM digest and the child final digest. Every
hooked recording matches the same child digest and pinned reference backend.
No life, seed or RAM injection is used. The original first ten boundaries and
first two vectors are identical to the accepted first update. All 305 / 309
earlier native CSV scopes retain their complete bytes or their explicit
first-update prefix; only that gameplay's summary and terminal map marker are
allowed to extend. Earlier fourth-result and one-life UI outputs stay exact.

## Reproduction

Keep the original controls, observations, assets and binaries local. Extend
each `sameboy-air-fifth[-pause]-entry-control` by the unchanged-button event
`tick 1800`, preserving `setup.state`, `inputs.txt`, explicit parent identity,
both repeated final hashes and parent-prefix hashes.

Capture initial startup into a fresh startup folder, then capture into a fresh
reference folder with the usual ROM, `--capture` and `--out` arguments:

- `tools/air_startup_reference.py capture`
- `tools/air_following_gameplay_reference.py capture --next-retry --after-retry 3 --updates N --outro --busy-scenes --partial-rows`
- `tools/air_map_reference.py capture --next-retry --after-retry 3`
- `tools/air_side_push_reference.py capture`

`N` is 1,789 ordinary or 1,762 paused, as independently counted at the original
terminal return. Source side-push capture now observes the terminal wait/end
in addition to the ordinary named boundaries. Earlier nonterminal recording
behavior remains unchanged. Fifth map selection is explicit; result-capture
selection is not implicitly extended to a final-life owner.

Build with `tools/build_air_clock_probe.py --out local/air-fifth-terminal-clock-probe.exe`.
Use the new gameplay `buttons.txt` and original initial input file, difficulty
zero, the existing display input file, and:

```text
--following-gameplay --following-updates SECOND
--next-retry --next-updates THIRD
--fourth-updates FOURTH
--fifth-entry --fifth-updates FIFTH --fifth-terminal
```

Ordinary second/third/fourth/fifth extents are 1,788 / 1,789 / 1,788 / 1,789;
paused extents are 1,767 / 1,604 / 1,764 / 1,762 with
`--following-entry-pause`. Fifth extent must be 1..100,000 and requires explicit
fifth entry. Terminal ownership requires the exact native terminal update;
the adapter also completes its outgoing fade. Default `--fifth-entry` still
stops after its single accepted update and does not consume the final life.

Compare with `tools/air_fifth_gameplay_reference.py NATIVE_BASE`, supplying:

- New child `--capture`, `--out`, `--startup`.
- Accepted final entry `--first-base`, `--start-capture`, `--start-out`, `--start-startup`.
- Fourth-result/one-life instruction `--parent-capture`, `--parent-out`, `--parent-startup`, `--parent-result-out`.
- Accepted complete fourth-result native `--instruction-base`.

The composite first requalifies the accepted entry and its actual parent,
requires generation three and exact control/first-update attachment, verifies
native prefix retention, then compares gameplay/resources/objects/rows,
outgoing phases and side push. Reports are
`.fifth-gameplay.comparison.json` plus individual `.fifth.next-*` comparisons.
Local evidence uses `air-fifth[-pause]-result-reference/startup` and
`air-fifth[-pause]-terminal-services.csv`; these folder names do not imply that
the result itself is accepted.

Validation: optimized native Windows diagnostic, both complete attached
comparisons, 810 Python tests and seven CLI extent/ownership guards. The earlier
native semantic result/work/pause/handoff assertion scopes retain their
coverage; those unchanged owners were not retested without a new hypothesis.
ROM, extracted assets, original recordings and executable diagnostics remain
ignored/local. Automation settings were not changed.

Follow-up: [final-life result and game-over hold](AIR_FINAL_RESULT.md) now
match both histories. Next: high-score/name entry, then eliminated-player
selection/game over. The original takes the zero-life branch after decrement
instead of the non-final failure wait/music/hold sequence. Existing non-final
native guards remain strict. Never-allocated vacant done flags, other
campaigns/stunts/players, earlier UI/reset/unobserved work, production scheduler
integration, complete images/PCM and human/controller/independent-Windows/
distribution checks remain open. Timing point 1 and
[final acceptance](ACCEPTANCE.md) remain incomplete.
