# Fresh first-page title actions

October 20, 2026. Extends the accepted [first-page reopening](AIR_TITLE_PAGE.md)
with separate single-button Start, Select, A and B cases in both existing
ordinary / earlier-paused easy Air histories. It qualifies the menu decision
and exact outgoing branch endpoint, not that branch's subsequent presentation.

All eight cases match: 218 boundaries / 24 displays / 72 vectors / 96 raster
boundaries / 236 stores / 16,384 unchanged final map bytes, zero differences.
Per history, Start has 25 boundaries / 29 stores, Select 26 / 29, and A/B each
29 / 30. Every case has three displays, nine vectors, twelve raster boundaries
and 2,048 map bytes. Each case preserves all 366 / 370 preceding complete
native page-prefix CSVs. The composite requalifies the entire attached original
clock/control chain through reopening.

## Branch scope

The first two host frames release all buttons; the next press is one action.
The original menu first checks the unlock sequence. An action cannot match its
initial Up step, so it writes both bytes of the unchanged initial selector.
Start takes precedence over Select, which takes precedence over A/B. Native
tests additionally cover that priority with combined masks, but original
comparison qualification here is restricted to the four individual buttons.

Start returns to 0269 before the outgoing fade call. Select reaches 2749 before
closing/preparing the player-selection page. A/B reach 26ea after advancing
the actual page index once, before closing page one. The native owner stops
at those respective boundaries. The [Start fade/stop follow-up](AIR_TITLE_START.md) now qualifies that branch
through 0272. No later menu rectangle, player toggle
or next instruction timing is implied by this result.

The first two iterations decrement the independent page duration from 480 to
478. The fresh-action iteration never decrements it. Game countdown remains
54, song 1 continues and cumulative display/STAT totals reach 665 / 860. The
native owner inherits actual page geometry, LCD epoch/deadlines, input/audio
state and native maps. Direction/unlock progression and reset chords reject
in this bounded action owner. No observed state, timestamps, event deadlines,
IRQ schedules or fitted work allowances initialize native execution.

The original reads direction and action halves separately. In the earlier-
paused history, a release near that read retains raw Left (32) in the first
sample, then zero in the second; the ordinary case reads zero twice. The
retained bit creates no fresh edge. Both histories produce precisely one fresh
action on the third sample. The comparison preserves those actual raw samples;
it does not substitute host key flags or the public UI's abstract button bits.
This does not qualify production host-input sampling at that sub-frame phase.

Direct original map storage at entry equals the accepted reopened page's final
maps. It stays unchanged at exit, and all native final map bytes are compared.
Empty object storage also stays unchanged in native tests. Register/storage/
timing agreement here does not establish full rendered pixels or PCM parity.

## Input-only original controls

Each control retains the complete existing original setup file and events
through a split of the last held-input frame block. The fork is a host-frame
boundary after reopening and less than one original frame later. Only the
identified release/press tail changes. There are no RAM edits, seed/life
overrides or native state imports.

The preparation tool first replays the original unhooked control and verifies
its accepted full-memory digest. Every new case then runs unhooked twice from
the unchanged original setup: both its pre-input prefix hash and complete new
control hash must agree. The observed replay verifies those same prefix/full
hashes, exact event split/tail, setup/ROM identities and attached page endpoint.
Input-only native replay files preserve every prior page sample and append
exactly three samples. Native execution never loads original snapshots or
emulator state. ROM, snapshots, controls and recordings remain local.

The additive title-map observer, pinned SameBoy revision, DMG-B model, boot ROM
and execution callback remain unchanged. The emulator is a separately authorized
comparison instrument and is absent from the Windows game/distribution.

## Reproduction and validation

Prepare controls with `tools/air_title_actions_reference.py prepare ROM
--capture ORIGINAL_CONTROL --page-out PAGE_REFERENCE --out CASE_ROOT`.
The tool creates `start`, `select`, `a` and `b` subdirectories beneath that local
root. Capture each with `tools/air_title_actions_reference.py capture ROM
--capture ORIGINAL_CONTROL --parent-out PAGE_REFERENCE --fade-out FADE_REFERENCE
--case-control CASE_ROOT/KEY --out ACTION_REFERENCE`.

Build using `tools/build_air_clock_probe.py --out local/air-title-actions-clock-probe.exe`.
Use the accepted first-page replay's initial inputs and complete attempt
extents, the action recording's `buttons.txt` for `--result-inputs`, and replace
`--title-page` with `--title-actions`. Explicit fifth entry and all preceding
owners remain required. New outputs use `.fifth.title-actions*`; the boundary
CSV includes an explicit outgoing route and the final snapshot covers both maps.

Compare with `tools/air_title_actions_reference.py compare NATIVE_BASE`, the same
arguments as `air_title_page_reference.py compare`, plus
`--case-control CASE_ROOT/KEY`, `--actions-out ACTION_REFERENCE` and
`--page-base ACCEPTED_PAGE_NATIVE_BASE`. Reports are `.title-actions.comparison.json`.
Local cases use `air-title-action-[pause-]KEY-reference` and matching services
CSVs, with `air-title-action[-pause]-controls/KEY` for source controls.

Validation: O2 native Windows diagnostic, all eight complete attached
comparisons, 44,343 native menu assertions, CLI guard and 982 Python tests.
Native tests include held-vs-fresh actions, priorities, partial release, correct
duration/page ownership, map preservation and rejection of direction/reset
branches. Synthetic evidence tests reject altered pre-fork input/setup/events,
unrepeatable controls, wrong routes/ticks/selector stores and detached/incomplete
storage/vector evidence. The tests run through the existing regular menu test
target; unchanged campaign/shared-clock checks retain their earlier scope.

Both complete [480-wait idle comparisons](AIR_TITLE_MENU.md) also pass. Their
summary proof now reads the LCD epoch from the independently accepted parent
page output. Previously it read the current menu summary, a circular provenance
check. Dedicated file-based tests ensure the current summary cannot supply its
own expected epoch. This correction changes no native execution, clocks or
accepted old CSVs; both stricter comparisons still have zero differences.
The earlier idle documentation's raw-33 direction label is corrected to Left.

Regular Windows EXE rebuilt from committed source; semantic timing remains
diagnostic and outside its production scheduler. No release or automation
change. Next: direction/unlock progression and subsequent page/player/Start-
fade work. Qualifying name entry, other menu/campaign/player/stunt/reset paths,
vacant flags, full graphics/pixels/PCM and final human/device/independent-Windows/
distribution gates remain open. [Final acceptance](ACCEPTANCE.md) is incomplete.
