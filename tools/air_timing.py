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
from reference_backend import reference_class,require_matching_backend


STAGES = {0x03d8: 'update', 0x03de: 'entitiesDone', 0x03e4: 'sprites',
          0x03e7: 'spritesDone', 0x03ed: 'mapCallback', 0x19a2: 'placements',
          0x03fa: 'done'}
IRQ_START = {0x0040: 'vblank', 0x0048: 'stat'}
IRQ_END = {0x2484: 'vblank', 0x2555: 'stat'}
IRQ_PHASES = {0x2430: 'dma', 0x2433: 'joypad', 0x2436: 'display',
              0x2455: 'bookkeeping', 0x2475: 'effects', 0x2478: 'audioBank',
              0x247b: 'music', 0x247e: 'restore'}
# Routine bodies plus their source callers; no measured allowance or emulator
# state feeds these constants. Variable display/effect/music work is separate.
VBLANK_FIXED = dict(prefix=180, dma=704, joypad=280, audioBank=68, restore=120)
DISPLAY_PHASES = {0x0c3f: 'map', 0x0c42: 'resources', 0x0c49: 'hud',
                  0x0c4c: 'scroll', 0x0c4f: 'lcd', 0x0c55: 'fade',
                  0x0c58: 'refresh', 0x0c5b: 'tail'}
ENTITY_HOOKS = (0x1b25, 0x1b26)
ANIMATION_ENTRY = 0x3bb3
ANIMATION_RETURNS = (0x6249, 0x6625, 0x667e, 0x675c, 0x67c4,
                     0x682f, 0x6857, 0x6894, 0x693e, 0x695f)
COLLISION_ENTRY = 0x1747
COLLISION_RETURNS = (0x61e8, 0x626c)
COLLISION_CALLBACK_HOOKS = (0x17b8, 0x184f, 0x1852)
MOTION_ENTRY, MOTION_RETURN = 0x659c, 0x5fe2
INPUT_ENTRY, INPUT_RETURN = 0x5fef, 0x6026
CAPTURE_VERSION = 9


def placement_cycles(camera_row, scan, placements, occupied, range_reads=None):
    """Source-derived T-cycle cost of 00:19a2 through its return.

    Pure work accounting, not instruction execution. Records contain only the
    placement row and active flag; occupied is the 16-bit entity-slot mask.
    The caller owns the corresponding gameplay operations.
    Optional range reads are observed targets for this reference audit. The
    native clock independently derives its scratch and reads none of these.
    """
    if not placements or not 0 <= scan < len(placements) or not 0 <= occupied <= 65535:
        raise ValueError('Invalid placement workload')
    if range_reads is not None and (len(range_reads)!=8 or any(not 0<=r.get('low',-1)<=255 for r in range_reads)):
        raise ValueError('Incomplete placement range-read observations')
    active = [bool(p['active']) for p in placements]
    # Entry, eight loop wrappers (last JR not taken), and final RET.
    cycles = 52 + 8 * 68 - 4 + 16
    high = (camera_row + 14) & 255
    for index in range(8):
        row = (placements[scan]['row'] + 3) & 255
        low=camera_row if range_reads is None else range_reads[index]['low']
        upper=high if range_reads is None else range_reads[index].get('high',-1)
        if low<row and not 0<=upper<=255:raise ValueError('Missing upper placement range read')
        # CALL range test, then advance the seven-byte record pointer.
        cycles += 24 + 132
        if low >= row:
            cycles += 144  # 19dd..19f2: first range return taken.
        elif upper < row:
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


def resource_cycles(frame, old_frame, state, queued_frame, chunks):
    # 03de..03e4: 3f30 resource-queue path and switch back to sprite bank.
    cost = 24 + 68 + 24 + (56 if state == 2 else 40)
    if state == 2:
        state = 0
    if frame >= 12:
        return cost + 56
    cost += 44
    if frame == old_frame:
        return cost + 52
    cost += 40
    if not state:
        cost += 24 + 92 + 28  # RST 20 pointer addition has no carry.
        return cost if not chunks else cost - 12 + 316
    cost += 28
    if frame == queued_frame:
        return cost + 44 + 72
    cost += 40 + 76 + 28
    return cost if not chunks else cost - 12 + 244 + 72


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


def scoped_work(calls, start, end, interrupts):
    """Reject missing, overlapping or escaped component boundaries."""
    previous_end, total = start, 0
    for call in calls:
        a, b = call.get('start'), call.get('end')
        if a is None or b is None or not previous_end <= a < b <= end:
            raise ValueError('Invalid component scope')
        total += elapsed_work(a, b, interrupts)
        previous_end = b
    return total


def collision_work(calls, start, end, interrupts):
    total = scoped_work(calls, start, end, interrupts)
    callbacks = 0
    for call in calls:
        callbacks += scoped_work(call['callbacks'], call['start'], call['end'], interrupts)
        scoped_work(call['slots'], call['start'], call['end'], interrupts)
    return total-callbacks, callbacks


def vblank_work(irq):
    if set(irq.get('phases', {})) != set(IRQ_PHASES.values()):
        raise ValueError('Incomplete VBlank phases')
    names = ['prefix', *IRQ_PHASES.values()]
    times = [irq['start'], *(irq['phases'][name] for name in IRQ_PHASES.values()), irq['end']]
    if any(a >= b for a, b in zip(times, times[1:])):
        raise ValueError('Invalid VBlank phase order')
    return {name: b-a for name, a, b in zip(names, times, times[1:])}


def vblank_bookkeeping_work(reset_enabled, held, reset_latched):
    # 2455..2475 and conditional 24b4. Reset initialization never returns to
    # this interval, so do not certify that path as a normal completed service.
    if not reset_enabled:
        return 160
    if held & 15 != 15:
        return 240
    return 248 if reset_latched else -1


def progress_bar_tiles(value):
    value &= 255
    if not value:
        return [0]*6
    full = min(value//8, 6)
    return [0xe9]*full + ([0xe9+((value%8)^7)] + [0]*(5-full) if full < 6 else [])


def display_cycles(map_pending, ready, chunks, cursor, tick, fade_remaining, collected, quota):
    """Source-derived display work, without executing instructions or copying pixels."""
    if not 0 <= cursor < 13 or not 0 <= collected <= 255 or not 1 <= quota <= 255 or chunks < 0:
        raise ValueError('Invalid display workload')
    upload = 36 if not ready else 60 if not chunks else 3112 if chunks > 4 else 456+672*chunks
    quotient = 48*collected//quota
    full = min((quotient & 255)//8, 6)
    bar_work = 172 if not quotient & 255 else 288 if full == 6 else 304 if full == 5 else 208+20*full
    refresh = 708 + (8 if ((2*collected)&255)+collected > 255 else 0) + 2632 - 20*quotient.bit_count() + bar_work
    return dict(prefix=116, map=24+(736 if map_pending else 40),
                resources=32 if map_pending else 44+upload, hud=248+(12 if cursor == 12 else 0),
                scroll=176, lcd=32, fade=24+(40 if tick & 1 else 208 if fade_remaining else 68),
                refresh=24+(refresh if cursor == 12 else 40), tail=16)


def display_work(irq):
    if set(irq.get('displayPhases', {})) != set(DISPLAY_PHASES.values()):
        raise ValueError('Incomplete display phases')
    names = ['prefix', *DISPLAY_PHASES.values()]
    times = [irq['phases']['display'], *(irq['displayPhases'][name] for name in DISPLAY_PHASES.values()), irq['phases']['bookkeeping']]
    if any(a >= b for a, b in zip(times, times[1:])):
        raise ValueError('Invalid display phase order')
    return {name: b-a for name, a, b in zip(names, times, times[1:])}


def effect_cycles(pending, square_root, noise_root):
    if pending == 255:
        return 64
    if not 0 <= pending < 26:
        raise ValueError('Invalid effect index')
    return 220 + 252*bool(square_root) + 148*bool(noise_root)


def analyze(data):
    if data.get('version') not in (8,CAPTURE_VERSION):
        raise ValueError('Timing capture schema changed; repeat capture with the current tool')
    rows, interrupts = data['updates'], data['interrupts']
    if not rows:
        raise ValueError('No completed updates')
    overruns, mismatches, map_mismatches, sprite_mismatches, clear_mismatches, costs = [], [], [], [], [], []
    resource_mismatches, dispatch_mismatches, handlers = [], [], {}
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
        if data['version']==CAPTURE_VERSION and 'range_reads' not in workload:
            raise ValueError('Current placement capture requires independent range reads')
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
        start, end = row['update']['cycles'], row['entitiesDone']['cycles']
        animation_work = scoped_work(row['animations'], start, end, interrupts)
        scan_work, callback_work = collision_work(row['collisions'], start, end, interrupts)
        costs.append(dict(update=i, stages=stage_costs, components=dict(animation=animation_work,
                         collisionScan=scan_work, collisionCallbacks=callback_work,
                         playerMotion=scoped_work(row['motion'], start, end, interrupts),
                         playerInput=scoped_work(row['input'], start, end, interrupts))))
        predicted_resource = resource_cycles(**row['entitiesDone']['workload'])
        if predicted_resource != stage_costs['entitiesDone']:
            resource_mismatches.append(dict(update=i, measured=stage_costs['entitiesDone'], predicted=predicted_resource))
        # 03d8 frame save + 1b0f's sixteen-slot dispatch. Empty slots cost 92;
        # live dispatch adds 60. Handler entries are after JP HL at 1b25.
        handler_work = 0
        for entry in row['handlers']:
            work = elapsed_work(entry['start'], entry['end'], interrupts)
            handler_work += work
            group = handlers.setdefault(f"{entry['handler']:04x}", dict(calls=0, min=work, max=work, total=0))
            group['calls'] += 1; group['min'] = min(group['min'], work); group['max'] = max(group['max'], work); group['total'] += work
        predicted_dispatch = 1612 + 60 * len(row['handlers']) + handler_work
        if predicted_dispatch != stage_costs['update']:
            dispatch_mismatches.append(dict(update=i, measured=stage_costs['update'], predicted=predicted_dispatch))
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
    vblank_parts = [vblank_work(irq) for irq in interrupts if irq['kind'] == 'vblank']
    fixed_irq_mismatches = [dict(interrupt=i, phase=name, original=parts[name], source=cost)
                           for i, parts in enumerate(vblank_parts) for name, cost in VBLANK_FIXED.items()
                           if parts[name] != cost]
    display_mismatches, bar_mismatches, effect_mismatches = [], [], []
    for i, (irq, parts) in enumerate(zip((irq for irq in interrupts if irq['kind'] == 'vblank'), vblank_parts)):
        predicted = vblank_bookkeeping_work(irq['resetEnabled'], irq['held'], irq['resetLatched'])
        if predicted != parts['bookkeeping']:
            fixed_irq_mismatches.append(dict(interrupt=i, phase='bookkeeping', original=parts['bookkeeping'], source=predicted))
        predicted_display, measured_display = display_cycles(**irq['displayWorkload']), display_work(irq)
        if sum(measured_display.values()) != parts['display']:
            raise ValueError('Display decomposition does not add to its measured interval')
        for name, cost in predicted_display.items():
            if cost != measured_display[name]:
                display_mismatches.append(dict(interrupt=i, phase=name, original=measured_display[name], source=cost))
        w = irq['displayWorkload']
        if w['cursor'] == 12:
            expected_bar = progress_bar_tiles(48*w['collected']//w['quota'])
            if irq['hudBar'] != expected_bar:
                bar_mismatches.append(dict(interrupt=i, original=irq['hudBar'], source=expected_bar))
        predicted_effect = effect_cycles(**irq['effectWorkload'])
        if predicted_effect != parts['effects']:
            effect_mismatches.append(dict(interrupt=i, original=parts['effects'], source=predicted_effect))
    summary = dict(completedUpdates=len(rows), overruns=overruns,
                   placementModelMismatches=mismatches,
                   mapModelMismatches=map_mismatches,
                   spriteModelMismatches=sprite_mismatches,
                   clearModelMismatches=clear_mismatches,
                   resourceModelMismatches=resource_mismatches,
                   dispatchModelMismatches=dispatch_mismatches, handlerProfile=handlers,
                   vblankCyclesMin=min(durations) if durations else None,
                   vblankCyclesMax=max(durations) if durations else None,
                   fixedVBlankModelMismatches=fixed_irq_mismatches,
                   displayModelMismatches=display_mismatches, progressBarMismatches=bar_mismatches,
                   effectModelMismatches=effect_mismatches,
                   vblankPhaseRanges={name: dict(min=min(p[name] for p in vblank_parts), max=max(p[name] for p in vblank_parts))
                                      for name in ['prefix', *IRQ_PHASES.values()]} if vblank_parts else {},
                   runtimeSchedulingFixed=False,
                   evidenceLimit='Source costs of five complete phases, plus measured handler, animation, collision, motion and input components. '
                                 'The dispatcher decomposition includes measured body costs; it is not a complete '
                                 'source model. No native scheduling parity is established.')
    return summary, costs


def capture(args):
    rom = read_rom(args.rom)
    manifest = json.loads((args.capture / 'capture-summary.json').read_text(encoding='utf-8'))
    if manifest['romSha256'] != hashlib.sha256(rom).hexdigest() or manifest['controlDifferences']:
        raise ValueError('Requires a matching, control-verified reference capture')
    PyBoy,metadata=reference_class(getattr(args,'reference_backend','pyboy'),args.reference_lib)
    require_matching_backend(manifest,metadata)
    player = PyBoy(str(args.rom), window='null', sound_volume=0)
    player.set_emulation_speed(0)
    rows, interrupts, frames = [], [], {}
    current, irq_open, handler_open, animation_open, collision_open, callback_open = None, None, None, None, None, None
    motion_open = input_open = None

    def word(a):
        return player.memory[a] | player.memory[a + 1] << 8

    def hook(address):
        nonlocal current, irq_open, handler_open, animation_open, collision_open, callback_open
        nonlocal motion_open, input_open
        if player.memory[0xc098] != 4:
            return
        now = player._cycles()  # Measurement API, pinned above; not wall time.
        state = dict(cycles=now, tick=word(0xc00a), transfer=player.memory[0xffae])
        if address in DISPLAY_PHASES:
            if irq_open is None or irq_open['kind'] != 'vblank':
                raise ValueError('Display phase outside VBlank')
            name = DISPLAY_PHASES[address]
            if name in irq_open['displayPhases']:
                raise ValueError('Repeated display phase')
            irq_open['displayPhases'][name] = now
            if name == 'map':
                irq_open['displayWorkload'] = dict(map_pending=player.memory[0xc00d], ready=player.memory[0xffae],
                    chunks=player.memory[0xffb5], cursor=player.memory[0xc04c], tick=word(0xc00a),
                    fade_remaining=player.memory[0xffc9], collected=player.memory[0xc20a], quota=player.memory[0xffab])
            if name == 'tail':
                irq_open['hudBar'] = list(player.memory[0xc046:0xc04c])
            return
        if address in (0x19ef,0x19f3):
            if current is None or 'placements' not in current:return
            reads=current['placements']['workload']['range_reads']
            if address==0x19ef:
                if len(reads)>=8:raise ValueError('Too many placement range reads')
                reads.append(dict(low=player.memory[0xff9c]))
            else:
                if not reads or 'high' in reads[-1]:raise ValueError('Unmatched upper placement range read')
                reads[-1]['high']=player.memory[0xff9e]
            return
        if address in IRQ_PHASES:
            if irq_open is None or irq_open['kind'] != 'vblank':
                raise ValueError('VBlank phase outside its interrupt')
            name = IRQ_PHASES[address]
            if name in irq_open['phases']:
                raise ValueError('Repeated VBlank phase')
            irq_open['phases'][name] = now
            if name == 'display':
                irq_open['held'] = player.memory[0xff8a]
            if name == 'effects':
                pending = player.memory[0xffc6]
                root = 0x37f3+4*pending
                irq_open['effectWorkload'] = dict(pending=pending,
                    square_root=int(pending != 255 and word(root) != 0),
                    noise_root=int(pending != 255 and word(root+2) != 0))
            return
        if address == INPUT_ENTRY:
            if current is None or input_open is not None:
                raise ValueError('Unexpected player input entry')
            input_open = dict(start=now)
            return
        if address == INPUT_RETURN:
            if input_open is None:
                raise ValueError('Player input returned without an entry')
            input_open['end'] = now
            current['input'].append(input_open)
            input_open = None
            return
        if address == MOTION_ENTRY:
            if current is None or motion_open is not None:
                raise ValueError('Unexpected player motion entry')
            motion_open = dict(start=now)
            return
        if address == MOTION_RETURN:
            if motion_open is None:
                raise ValueError('Player motion returned without an entry')
            motion_open['end'] = now
            current['motion'].append(motion_open)
            motion_open = None
            return
        if collision_open is not None and address == collision_open['returnAddress']:
            if callback_open is not None:
                raise ValueError('Collision returned inside an unfinished callback')
            collision_open['end'] = now
            current['collisions'].append(collision_open)
            collision_open = None
        if address == COLLISION_ENTRY:
            if current is None:
                return
            if collision_open is not None:
                raise ValueError('Nested collision scan')
            collision_open = dict(start=now, returnAddress=word(player.register_file.SP), callbacks=[], slots=[])
            return
        if address in COLLISION_CALLBACK_HOOKS:
            if collision_open is None:
                raise ValueError('Callback hook outside a collision scan')
            if address == 0x17b8:
                slot = player.register_file.A//16
                at = 0xc200 + slot*16
                collision_open['slots'].append(dict(slot=slot, start=now,
                    entity=list(player.memory[at:at+16]), cameraX=word(0xff92), cameraY=word(0xff94)))
            elif address == 0x184f and player.memory[0xffa3] != 255:
                if callback_open is not None:
                    raise ValueError('Nested collision callback')
                callback_open = dict(start=now, slot=player.memory[0xff8d]//16,
                                     kind=player.memory[0xffa3])
            elif address == 0x1852 and callback_open is not None:
                callback_open['end'] = now
                collision_open['callbacks'].append(callback_open)
                callback_open = None
            if address == 0x1852:
                collision_open['slots'][-1]['end'] = now
            return
        if address in COLLISION_RETURNS:
            return
        if animation_open is not None and address == animation_open['returnAddress']:
            animation_open['end'] = now
            current['animations'].append(animation_open)
            animation_open = None
        if address == ANIMATION_ENTRY:
            if current is None:
                return
            if animation_open is not None:
                raise ValueError('Nested animation call or unknown animation return')
            slot = player.memory[0xff8c] // 16
            at = 0xc200 + slot * 16
            animation_open = dict(slot=slot, start=now, returnAddress=word(player.register_file.SP),
                entity=list(player.memory[at:at + 16]),
                animation=list(player.memory[at + 256:at + 272]))
            return
        if address in ANIMATION_RETURNS:
            return
        if address in ENTITY_HOOKS:
            if current is None:
                return
            slot = player.memory[0xff8c] // 16
            if address == 0x1b25:
                if handler_open is not None:
                    raise ValueError('Nested entity dispatch')
                at = 0xc200 + slot * 16
                handler_open = dict(slot=slot, handler=word(at + 6), start=now + 4,
                                    entity=list(player.memory[at:at + 16]),
                                    animation=list(player.memory[at + 256:at + 272]))
            elif handler_open is not None:
                if handler_open['slot'] != slot:
                    raise ValueError('Entity dispatch returned to a different slot')
                handler_open['end'] = now
                current['handlers'].append(handler_open)
                handler_open = None
        elif address in IRQ_START:
            if irq_open is not None:
                raise ValueError('Unexpected nested IRQ')
            sp = player.register_file.SP
            irq_open = dict(kind=IRQ_START[address], start=now, tick=word(0xc00a),
                            transfer=player.memory[0xffae], returnAddress=word(sp), phases={}, displayPhases={},
                            resetEnabled=player.memory[0xc005], resetLatched=player.memory[0xc004])
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
                current = dict(handlers=[], animations=[], collisions=[], motion=[], input=[])
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
            if name == 'entitiesDone':
                frame = player.memory[0xc200]
                state['workload'] = dict(frame=frame, old_frame=player.memory[0xffc2],
                    state=player.memory[0xffb6], queued_frame=player.memory[0xffb9],
                    chunks=player.memory[0xdd00 + frame * 4] if frame < 12 else 0)
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
                    range_reads=[],
                    occupied=sum(1 << i for i in range(16) if player.memory[0xc200 + i * 16] != 255))
            current[name] = state
            if name == 'done':
                if any(c is not None for c in (animation_open, handler_open, collision_open, callback_open, motion_open, input_open)):
                    raise ValueError('Unfinished animation or entity at update end')
                rows.append(current)
                current = None

    try:
        with (args.capture / 'setup.state').open('rb') as stream:
            player.load_state(stream)
        for address in (*STAGES, *IRQ_START, *IRQ_END, *IRQ_PHASES, *DISPLAY_PHASES, *ENTITY_HOOKS, ANIMATION_ENTRY,0x19ef,0x19f3,
                        COLLISION_ENTRY, *COLLISION_CALLBACK_HOOKS):
            player.hook_register(0, address, hook, address)
        for address in (*ANIMATION_RETURNS, *COLLISION_RETURNS, MOTION_ENTRY, MOTION_RETURN, INPUT_ENTRY, INPUT_RETURN):
            player.hook_register(1, address, hook, address)
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
    data = dict(version=CAPTURE_VERSION, updates=rows, interrupts=interrupts, frames=frames, romSha256=manifest['romSha256'],
                controlMemorySha256=manifest['controlMemorySha256'], reference=metadata)
    args.out.mkdir(parents=True, exist_ok=True)
    write_json(args.out / 'timing.json', data)
    report(argparse.Namespace(out=args.out))


def report(args):
    data = json.loads((args.out / 'timing.json').read_text(encoding='utf-8'))
    summary, costs = analyze(data)
    write_json(args.out / 'summary.json', summary)
    write_json(args.out / 'costs.json', costs)
    print(json.dumps(summary, indent=2))
    if any(summary[k] for k in ('placementModelMismatches', 'mapModelMismatches', 'spriteModelMismatches', 'clearModelMismatches', 'resourceModelMismatches', 'dispatchModelMismatches', 'fixedVBlankModelMismatches', 'displayModelMismatches', 'progressBarMismatches', 'effectModelMismatches')):
        raise ValueError('Source-derived workload does not match reference routine cost')


def compare(args):
    costs = json.loads((args.out / 'costs.json').read_text(encoding='utf-8'))
    with args.native_csv.open(encoding='utf-8-sig', newline='') as stream:
        native = [{k: int(v) for k, v in row.items()} for row in csv.DictReader(stream)]
    if len(costs) != len(native) or not costs:
        raise ValueError('Expected one native workload row per original update')
    first, differences = {}, []
    for i, (original, row) in enumerate(zip(costs, native)):
        expected = {**original['stages'], **original.get('components', {})}
        delta = {k: [expected[k], v] for k, v in row.items() if expected[k] != v}
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


def compare_display(args):
    data = json.loads((args.out / 'timing.json').read_text(encoding='utf-8'))
    if data.get('version') not in (8,CAPTURE_VERSION):
        raise ValueError('Repeat capture with the current tool before comparing display work')
    with args.native_csv.open(encoding='utf-8-sig', newline='') as stream:
        native = [{k: int(v) for k, v in row.items()} for row in csv.DictReader(stream)]
    if len(native) != len(data['updates']):
        raise ValueError('Expected one native display row per game update')
    services = [irq for irq in data['interrupts'] if irq['kind'] == 'vblank']
    at, differences, first = -1, [], {}
    for i, (row, update) in enumerate(zip(native, data['updates'])):
        if row['update'] != i:
            raise ValueError('Unordered native display rows')
        while at+1 < len(services) and services[at+1]['end']+16 <= update['update']['cycles']:
            at += 1
        if at < 0 or (services[at]['tick']+1)&65535 != update['update']['tick']:
            raise ValueError('No matching pre-update display service')
        irq = services[at]
        w = irq['displayWorkload']
        expected = dict(cost=sum(display_work(irq).values()), cursor=(w['cursor']+1)%13,
                        fade=w['fade_remaining']-int(not w['tick']&1 and bool(w['fade_remaining'])))
        expected.update({f'bar{j}': value for j, value in enumerate(irq['hudBar'])})
        delta = {name: [value, row[name]] for name, value in expected.items() if value != row[name]}
        for name, value in delta.items():
            first.setdefault(name, dict(update=i, original=value[0], native=value[1]))
        if delta:
            differences.append(dict(update=i, fields=delta))
    summary = dict(comparedUpdates=len(native), firstDifferences=first,
                   matchingPrefix=differences[0]['update'] if differences else len(native),
                   runtimeSchedulingFixed=False,
                   evidenceLimit='Native display work before each recorded-clock game update only. '
                                 'Pending startup VBlank and extra original VBlanks during work '
                                 'still require independent scheduling; recorded counters do not align HUD phase.')
    write_json(args.native_csv.with_suffix('.comparison.json'), summary)
    write_json(args.native_csv.with_suffix('.differences.json'), differences)
    print(json.dumps(summary, indent=2))


def entity_difference(original, native):
    # Unoccupied original records retain old bytes that are not active state.
    fields = ('frame',) if original['frame'] == native['frame'] == 255 else ('frame', 'flags', 'x', 'y')
    return {key: [original[key], native[key]] for key in fields if original[key] != native[key]}


def compare_handlers(args):
    from extract_air import HANDLERS
    data = json.loads((args.out / 'timing.json').read_text(encoding='utf-8'))
    if data.get('version') not in (8,CAPTURE_VERSION):
        raise ValueError('Repeat capture with the current tool before comparing handler costs')
    original = {(i, h['slot']): h for i, update in enumerate(data['updates']) for h in update['handlers']}
    with args.native_csv.open(encoding='utf-8-sig', newline='') as stream:
        native = [{k: int(v) for k, v in row.items()} for row in csv.DictReader(stream)]
    seen, differences, coverage = set(), [], {}
    for row in native:
        key = row['update'], row['slot']
        if key in seen or not 0 <= key[0] < len(data['updates']) or not 0 <= key[1] < 16:
            raise ValueError('Duplicate or invalid native handler row')
        seen.add(key)
        old = original.get(key)
        if old is None or HANDLERS[old['handler']] != row['handler']:
            differences.append(dict(update=key[0], slot=key[1], kind='dispatch'))
            continue
        profile = coverage.setdefault(f"{old['handler']:04x}", dict(modeled=0, unmodeled=0, mismatched=0))
        if row['cost'] == -1:
            profile['unmodeled'] += 1
            continue
        if row['cost'] <= 0:
            raise ValueError('Invalid handler cost; use -1 for an unmodeled body')
        profile['modeled'] += 1
        measured = elapsed_work(old['start'], old['end'], data['interrupts'])
        if measured != row['cost']:
            profile['mismatched'] += 1
            differences.append(dict(update=key[0], slot=key[1], kind='cost',
                                    handler=f"{old['handler']:04x}", original=measured, native=row['cost']))
    for key in original.keys() - seen:
        differences.append(dict(update=key[0], slot=key[1], kind='missing'))
    differences.sort(key=lambda d: (d['update'], d['slot']))
    summary = dict(updates=len(data['updates']), coverage=coverage,
                   firstDifference=differences[0] if differences else None,
                   differingCalls=len(differences), runtimeSchedulingFixed=False,
                   evidenceLimit='Only modeled, identically dispatched handler bodies are compared; '
                                 'unknown bodies are counted, never assumed to cost zero.')
    write_json(args.native_csv.with_suffix('.comparison.json'), summary)
    write_json(args.native_csv.with_suffix('.differences.json'), differences)
    print(json.dumps(summary, indent=2))


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
    record.add_argument('--reference-backend',choices=('pyboy','sameboy'),default='pyboy')
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
    handler_diff = sub.add_parser('compare-handlers')
    handler_diff.add_argument('native_csv', type=Path)
    handler_diff.add_argument('--out', type=Path, default=Path('local/air-timing'))
    display_diff = sub.add_parser('compare-display')
    display_diff.add_argument('native_csv', type=Path)
    display_diff.add_argument('--out', type=Path, default=Path('local/air-timing'))
    args = parser.parse_args()
    {'capture': capture, 'report': report, 'compare': compare, 'compare-entities': compare_entities,
     'compare-handlers': compare_handlers, 'compare-display': compare_display}[args.mode](args)
