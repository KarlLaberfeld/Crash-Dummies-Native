"""Local reference timing measurements. Never imported by the Windows port.

Requires a capture from air_reference.py. Outputs contain original state and
must stay local. The report command needs only Python, not an emulator.
"""
import argparse
import csv
import hashlib
import importlib.metadata
import json
from pathlib import Path
import sys

from air_reference import write_json
from extract import read_rom


STAGES = {0x03d8: 'update', 0x03de: 'entitiesDone', 0x03e4: 'sprites',
          0x03e7: 'spritesDone', 0x03ed: 'mapCallback', 0x19a2: 'placements',
          0x03fa: 'done'}
IRQ_START = {0x0040: 'vblank', 0x0048: 'stat'}
IRQ_END = {0x2484: 'vblank', 0x2555: 'stat'}


def placement_cycles(camera_row, scan, placements, occupied):
    """Source-derived T-cycle cost of 00:19a2 through its return.

    Pure work accounting, not instruction execution. Records contain only the
    placement row and active flag; occupied is the 16-bit entity-slot mask.
    The caller owns the corresponding gameplay operations.
    """
    if not placements or not 0 <= scan < len(placements) or not 0 <= occupied <= 65535:
        raise ValueError('Invalid placement workload')
    active = [bool(p['active']) for p in placements]
    # Entry, eight loop wrappers (last JR not taken), and final RET.
    cycles = 52 + 8 * 68 - 4 + 16
    high = (camera_row + 14) & 255
    for _ in range(8):
        row = (placements[scan]['row'] + 3) & 255
        # CALL range test, then advance the seven-byte record pointer.
        cycles += 24 + 132
        if camera_row >= row:
            cycles += 144  # 19dd..19f2: first range return taken.
        elif high < row:
            cycles += 168  # 19f6: second range return taken.
        elif active[scan]:
            cycles += 188  # 19f9: already active.
        elif occupied == 65535:
            cycles += 272 + 868  # Failed allocation scans all sixteen slots.
        else:
            slot = next(i for i in range(16) if not (occupied >> i) & 1)
            # 1abc: 52 per occupied slot, fixed definition/parameter copy.
            cycles += 332 + 816 + 52 * slot
            occupied |= 1 << slot
            active[scan] = True
        scan += 1
        if scan == len(placements):
            scan = 0
            cycles += 84  # 19cf..19dc, replacing the taken RET at 19ce.
    return cycles


def map_cycles(previous_y, camera_y):
    # 03ed indirect callback, 09e8 call, 1ead row preparation, 09eb jump.
    if not (previous_y ^ camera_y) & 128:
        return 304
    return 2228 + (4 if (previous_y - camera_y) & 32768 else 0)


def sprite_cycles(entities, camera_x, camera_y, reverse, frames):
    """Cost at 03e4..03e7, using decoded layouts and semantic entity state."""
    def signed8(n):
        return (n + 128) % 256 - 128

    def relative(n, camera):
        return ((n & 65520) - (camera & 65520) + 32768) % 65536 // 16 - 2048

    def add_cost(value, offset):
        # RST 20/28/30 body, including its conditional return.
        return 28 + (8 if (value & 255) + offset > 255 else 0)

    def signed_cost(value, offset):
        carry = (value & 255) + offset > 255
        # 23c2/23cc signed addition, excluding CALL at the caller.
        return (48 if carry else 56) if offset & 128 else (60 if carry else 52)

    cycles = 24 + 88  # CALL and routine entry.
    cursor = 156 if reverse else 0
    for index, entity in enumerate(entities):
        last = index == 15
        cycles += 76
        if entity['frame'] == 255:
            cycles += 4 + 40 + (12 if last else 0)
            continue
        frame = frames[str(entity['frame'])]
        meta = frame['meta']
        flags = entity['flags']
        cycles += (56 if entity['frame'] < 12 else 48) + 348
        if flags & 8:
            cycles += 4 + 40 + (12 if last else 0)
            continue
        x, y = relative(entity['x'], camera_x), relative(entity['y'], camera_y)
        cycles += 24 + 132 + 84 + signed_cost(x, meta[0]) + signed_cost(y, meta[1])
        x += signed8(meta[0]); y += signed8(meta[1])
        cycles += 72 + add_cost(x, 2 * meta[6] + 16)
        rejected = x < -2 * meta[6] - 16 or x > 176
        if (x + 2 * meta[6] + 16) & 65280:
            cycles += 4
        else:
            cycles += 32 + (4 if rejected else 0)
        if not rejected:
            cycles += 44 + add_cost(x, meta[6] + 8)
            cycles += 72 + add_cost(y, 2 * meta[7] + 16)
            rejected = y < -2 * meta[7] - 16 or y > 152
            if (y + 2 * meta[7] + 16) & 65280:
                cycles += 4
            else:
                cycles += 36 + (4 if rejected else 0)
        if rejected:
            if flags & 16:
                cycles += 76 + 52 + (112 if flags & 4 else 0) + 56
            else:
                cycles += 72 + 48
            if last:
                cycles += 12
            continue
        cycles += 72 + add_cost(y, meta[7] + 16)
        x += meta[6] + 8; y += meta[7] + 16
        for px, py in frame['pieces']:
            sx = (x + (-px - 8 if flags & 32 else px)) & 255
            sy = (y + (-py - 16 if flags & 64 else py)) & 255
            cycles += 20 + (64 if flags & 64 else 56) + (64 if flags & 32 else 56)
            if sx >= 168:
                cycles += 20 + 28
            elif sy >= 152:
                cycles += 48 + 28
            else:
                cycles += 44 + 156
                cursor = (cursor + (-4 if reverse else 4)) & 255
        cycles += 32  # End-of-layout return at 1cff.
        if cursor >= 160:
            return cycles + 36 + 28, cursor
        cycles += 32 + 40 + (12 if last else 0)
    return cycles, cursor


def clear_cycles(cursor, reverse):
    # 03e7 CALL, 1bd5..1bfa plus unrolled unused-OAM clear, bank switch to 1.
    if reverse:
        if cursor > 156:
            return 172
        return 92 + 32 + 12 + 8 + 8 + 8 + 12 + 12 + 16 + 28 + 16 + 4 + 16 + 8 * (4 + cursor) + 20
    if cursor >= 160:
        return 168
    return 92 + 28 + 8 + 12 + 8 + 8 + 4 + 12 + 16 + 28 + 16 + 4 + 16 + 8 * (160 - cursor) + 20


def elapsed_work(start, end, interrupts):
    """Subtract complete IRQ intervals, including entry and RETI overhead.

    Entry hooks run at the vector, 20 T-cycles after IRQ entry begins. Exit
    hooks run before RETI, which takes another 16. Reject incomplete boundaries
    rather than silently reporting interrupted work as routine execution.
    """
    if end < start:
        raise ValueError('Reversed work interval')
    cost = end - start
    previous_end = None
    for irq in interrupts:
        a, b = irq['start'] - 20, irq['end'] + 16
        if b <= a or (previous_end is not None and a < previous_end):
            raise ValueError('Invalid or overlapping interrupt intervals')
        previous_end = b
        if a < end and b > start:
            if a < start or b > end:
                raise ValueError('Work boundary lies inside an interrupt')
            cost -= b - a
    if cost < 0:
        raise ValueError('Interrupt time exceeds work interval')
    return cost


def analyze(data):
    rows, interrupts = data['updates'], data['interrupts']
    if not rows:
        raise ValueError('No completed updates')
    overruns, mismatches, map_mismatches, sprite_mismatches, clear_mismatches, costs = [], [], [], [], [], []
    prior_end = None
    for i, row in enumerate(rows):
        if any(k not in row for k in STAGES.values()):
            raise ValueError(f'Incomplete update {i}')
        times = [row[k]['cycles'] for k in STAGES.values()]
        if times != sorted(times) or (prior_end is not None and times[0] <= prior_end):
            raise ValueError(f'Unordered update {i}')
        prior_end = times[-1]
        a, b = row['placements']['cycles'], row['done']['cycles']
        work = elapsed_work(a, b, interrupts)
        workload = row['placements']['workload']
        predicted = placement_cycles(**workload)
        if work != predicted:
            mismatches.append(dict(update=i, measured=work, predicted=predicted))
        stage_costs = {name: elapsed_work(row[name]['cycles'], row[next_name]['cycles'], interrupts)
                       for name, next_name in zip(STAGES.values(), list(STAGES.values())[1:])}
        predicted_map = map_cycles(**row['mapCallback']['workload'])
        if predicted_map != stage_costs['mapCallback']:
            map_mismatches.append(dict(update=i, measured=stage_costs['mapCallback'], predicted=predicted_map))
        predicted_sprites, cursor = sprite_cycles(**row['sprites']['workload'], frames=data['frames'])
        if predicted_sprites != stage_costs['sprites']:
            sprite_mismatches.append(dict(update=i, measured=stage_costs['sprites'], predicted=predicted_sprites))
        predicted_clear = clear_cycles(cursor, row['sprites']['workload']['reverse'])
        if predicted_clear != stage_costs['spritesDone']:
            clear_mismatches.append(dict(update=i, measured=stage_costs['spritesDone'], predicted=predicted_clear))
        costs.append(dict(update=i, stages=stage_costs))
        delta = (row['done']['tick'] - row['update']['tick']) & 65535
        vb = [irq for irq in interrupts if irq['kind'] == 'vblank'
              and times[0] < irq['start'] < times[-1]]
        if len(vb) != delta:
            raise ValueError(f'Counter change and VBlank count disagree at update {i}')
        if delta:
            overruns.append(dict(update=i, counterBefore=row['update']['tick'],
                                 counterAfter=row['done']['tick'], interrupts=vb,
                                 stages=stage_costs, placementCycles=predicted))
    durations = [irq['end'] + 16 - (irq['start'] - 20)
                 for irq in interrupts if irq['kind'] == 'vblank']
    summary = dict(completedUpdates=len(rows), overruns=overruns,
                   placementModelMismatches=mismatches,
                   mapModelMismatches=map_mismatches,
                   spriteModelMismatches=sprite_mismatches,
                   clearModelMismatches=clear_mismatches,
                   vblankCyclesMin=min(durations) if durations else None,
                   vblankCyclesMax=max(durations) if durations else None,
                   runtimeSchedulingFixed=False,
                   evidenceLimit='Source costs of sprite preparation, unused-tail clearing, map preparation and placement scanning; no complete gameplay/audio '
                                 'cost model or native scheduling parity is established.')
    return summary, costs


def capture(args):
    rom = read_rom(args.rom)
    manifest = json.loads((args.capture / 'capture-summary.json').read_text(encoding='utf-8'))
    if manifest['romSha256'] != hashlib.sha256(rom).hexdigest() or manifest['controlDifferences']:
        raise ValueError('Requires a matching, control-verified reference capture')
    if args.reference_lib:
        sys.path.insert(0, str(args.reference_lib.resolve()))
    if importlib.metadata.version('pyboy') != '2.7.0':
        raise ValueError('Cycle instrumentation is validated with PyBoy 2.7.0 only')
    from pyboy import PyBoy
    player = PyBoy(str(args.rom), window='null', sound_volume=0)
    player.set_emulation_speed(0)
    rows, interrupts, frames = [], [], {}
    current, irq_open = None, None

    def word(a):
        return player.memory[a] | player.memory[a + 1] << 8

    def hook(address):
        nonlocal current, irq_open
        if player.memory[0xc098] != 4:
            return
        now = player._cycles()  # Measurement API, pinned above; not wall time.
        state = dict(cycles=now, tick=word(0xc00a), transfer=player.memory[0xffae])
        if address in IRQ_START:
            if irq_open is not None:
                raise ValueError('Unexpected nested IRQ')
            sp = player.register_file.SP
            irq_open = dict(kind=IRQ_START[address], start=now, tick=word(0xc00a),
                            transfer=player.memory[0xffae], returnAddress=word(sp))
        elif address in IRQ_END:
            if irq_open is None or irq_open['kind'] != IRQ_END[address]:
                raise ValueError('Unmatched interrupt return')
            irq_open['end'] = now
            interrupts.append(irq_open)
            irq_open = None
        else:
            name = STAGES[address]
            if name == 'update':
                if current is not None:
                    raise ValueError('Previous update has no completion')
                current = {}
            if current is None:
                return
            if name in current:
                raise ValueError('Duplicate stage in one update')
            if name == 'update':
                state['entities'] = [dict(frame=player.memory[0xc200 + i * 16],
                    flags=player.memory[0xc205 + i * 16], x=word(0xc201 + i * 16),
                    y=word(0xc203 + i * 16)) for i in range(16)]
            if name == 'mapCallback':
                state['workload'] = dict(previous_y=word(0xff96), camera_y=word(0xff94))
            if name == 'sprites':
                entities = []
                for i in range(16):
                    at = 0xc200 + 16 * i
                    f = player.memory[at]
                    entities.append(dict(frame=f, x=word(at + 1), y=word(at + 3), flags=player.memory[at + 5]))
                    if f != 255 and str(f) not in frames:
                        ptr = word(0xdc00 + 2 * f)
                        meta = list(player.memory[ptr:ptr + 8])
                        ptr += 8
                        pieces = []
                        while player.memory[ptr] != 255:
                            if len(pieces) >= 40:
                                raise ValueError('Unterminated sprite layout')
                            pieces.append([(player.memory[ptr + 1] + 128) % 256 - 128,
                                           (player.memory[ptr] + 128) % 256 - 128])
                            ptr += 4
                        frames[str(f)] = dict(meta=meta, pieces=pieces)
                state['workload'] = dict(entities=entities, camera_x=word(0xff92), camera_y=word(0xff94),
                                        reverse=bool(player.memory[0xff90] ^ 156))
            if name == 'placements':
                entries = []
                at = 0xd800
                while player.memory[at] != 255:
                    if len(entries) >= 512:
                        raise ValueError('Unterminated placement table')
                    entries.append(dict(row=player.memory[at + 3], active=player.memory[at + 4]))
                    at += 7
                state['workload'] = dict(camera_row=player.memory[0xff95],
                    scan=(word(0xc033) - 0xd800) // 7, placements=entries,
                    occupied=sum(1 << i for i in range(16) if player.memory[0xc200 + i * 16] != 255))
            current[name] = state
            if name == 'done':
                rows.append(current)
                current = None

    try:
        with (args.capture / 'setup.state').open('rb') as stream:
            player.load_state(stream)
        for address in (*STAGES, *IRQ_START, *IRQ_END):
            player.hook_register(0, address, hook, address)
        events = json.loads((args.capture / 'events.json').read_text(encoding='utf-8'))
        for event in events:
            if event[0] == 'tick':
                player.tick(event[1], event[2])
            elif event[0] in ('press', 'release'):
                getattr(player, 'button_' + event[0])(event[1])
            else:
                raise ValueError('Unknown replay event')
        memory = bytes(player.memory[0x8000:0x10000])
    finally:
        player.stop(save=False)
    expected = (args.capture / 'hooked-end.bin').read_bytes()
    if memory != expected or hashlib.sha256(memory).hexdigest() != manifest['controlMemorySha256']:
        raise ValueError('Timing instrumentation changed the verified final memory state')
    trace = json.loads((args.capture / 'trace.json').read_text(encoding='utf-8'))
    if len(rows) != len(trace['post']):
        raise ValueError('Timing replay update count differs from verified capture')
    for row, pre, post in zip(rows, trace['pre'], trace['post']):
        if row['update']['tick'] != pre['tick'] or row['done']['tick'] != post['tick']:
            raise ValueError('Timing replay counter differs from verified capture')
    data = dict(updates=rows, interrupts=interrupts, frames=frames, romSha256=manifest['romSha256'],
                controlMemorySha256=manifest['controlMemorySha256'], emulator='PyBoy 2.7.0')
    args.out.mkdir(parents=True, exist_ok=True)
    write_json(args.out / 'timing.json', data)
    report(argparse.Namespace(out=args.out))


def report(args):
    data = json.loads((args.out / 'timing.json').read_text(encoding='utf-8'))
    summary, costs = analyze(data)
    write_json(args.out / 'summary.json', summary)
    write_json(args.out / 'costs.json', costs)
    print(json.dumps(summary, indent=2))
    if any(summary[k] for k in ('placementModelMismatches', 'mapModelMismatches', 'spriteModelMismatches', 'clearModelMismatches')):
        raise ValueError('Source-derived workload does not match reference routine cost')


def compare(args):
    costs = json.loads((args.out / 'costs.json').read_text(encoding='utf-8'))
    with args.native_csv.open(encoding='utf-8-sig', newline='') as stream:
        native = [{k: int(v) for k, v in row.items()} for row in csv.DictReader(stream)]
    if len(costs) != len(native) or not costs:
        raise ValueError('Expected one native workload row per original update')
    first, differences = {}, []
    for i, (original, row) in enumerate(zip(costs, native)):
        delta = {k: [original['stages'][k], v] for k, v in row.items() if original['stages'][k] != v}
        for k, v in delta.items():
            first.setdefault(k, dict(update=i, original=v[0], native=v[1]))
        if delta:
            differences.append(dict(update=i, fields=delta))
    summary = dict(comparedUpdates=len(costs), fields=list(native[0]), firstDifferences=first,
                   matchingPrefix=differences[0]['update'] if differences else len(costs),
                   differingUpdates=len(differences), runtimeSchedulingFixed=False)
    write_json(args.native_csv.with_suffix('.comparison.json'), summary)
    write_json(args.native_csv.with_suffix('.differences.json'), differences)
    print(json.dumps(summary, indent=2))


def entity_difference(original, native):
    # Unoccupied original records retain old bytes that are not active state.
    fields = ('frame',) if original['frame'] == native['frame'] == 255 else ('frame', 'flags', 'x', 'y')
    return {key: [original[key], native[key]] for key in fields if original[key] != native[key]}


def compare_entities(args):
    data = json.loads((args.out / 'timing.json').read_text(encoding='utf-8'))
    with args.native_csv.open(encoding='utf-8-sig', newline='') as stream:
        native = [{k: int(v) for k, v in row.items()} for row in csv.DictReader(stream)]
    if not data['updates'] or len(native) != len(data['updates']) * 16:
        raise ValueError('Expected sixteen native entity rows per original update')
    differences = []
    for i, update in enumerate(data['updates']):
        for slot in range(16):
            row = native[i * 16 + slot]
            if row['update'] != i or row['slot'] != slot:
                raise ValueError('Unordered or duplicate native entity row')
            # The player upload can complete in the VBlank preceding 03d8;
            # native pre-step logging precedes that callback. Other slots have
            # equivalent boundaries. air_reference.py compares the player post-step.
            if slot == 0:
                continue
            delta = entity_difference(update['update']['entities'][slot], row)
            if delta:
                differences.append(dict(update=i, slot=slot, fields=delta))
    summary = dict(comparedUpdates=len(data['updates']), slots=list(range(1, 16)),
                   matchingPrefix=differences[0]['update'] if differences else len(data['updates']),
                   firstDifference=differences[0] if differences else None,
                   evidenceLimit='Frame, normalized flags and positions of occupied non-player slots only; '
                                 'recorded-clock replay does not establish real-time scheduling parity.')
    write_json(args.native_csv.with_suffix('.comparison.json'), summary)
    write_json(args.native_csv.with_suffix('.differences.json'), differences)
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='mode', required=True)
    record = sub.add_parser('capture')
    record.add_argument('rom', type=Path)
    record.add_argument('--reference-lib', type=Path)
    record.add_argument('--capture', type=Path, default=Path('local/original-air-verified'))
    record.add_argument('--out', type=Path, default=Path('local/air-timing'))
    view = sub.add_parser('report')
    view.add_argument('--out', type=Path, default=Path('local/air-timing'))
    diff = sub.add_parser('compare')
    diff.add_argument('native_csv', type=Path)
    diff.add_argument('--out', type=Path, default=Path('local/air-timing'))
    entity_diff = sub.add_parser('compare-entities')
    entity_diff.add_argument('native_csv', type=Path)
    entity_diff.add_argument('--out', type=Path, default=Path('local/air-timing'))
    args = parser.parse_args()
    {'capture': capture, 'report': report, 'compare': compare, 'compare-entities': compare_entities}[args.mode](args)
