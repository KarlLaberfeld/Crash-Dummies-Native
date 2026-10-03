"""Optional original-ROM measurement, separate from the native Windows runtime.

PyBoy is used only by the capture command and is not a port dependency.
All recordings, state files and extracted inputs must remain local.
"""
import argparse
import csv
import hashlib
import importlib.metadata
import json
import platform
import sys
from pathlib import Path

from extract import read_rom
from extract_air import HANDLERS


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')


def capture(args):
    data = read_rom(args.rom)
    if args.reference_lib:
        sys.path.insert(0, str(args.reference_lib.resolve()))
    from pyboy import PyBoy

    out = args.out
    out.mkdir(parents=True, exist_ok=True)
    original = PyBoy(str(args.rom), window='null', sound_volume=0)
    original.set_emulation_speed(0)
    pre, post, events = [], [], []

    def press(key):
        original.button_press(key)
        original.tick(2, False)
        original.button_release(key)
        original.tick(2, False)

    def password(index):
        for key in ('up', 'down', 'left', 'right'):
            press(key)
        original.tick(100, False)
        # Read the user's cartridge's identified password data; do not embed it.
        for i, digit in enumerate(data[0x2cca + index * 10:0x2cd2 + index * 10]):
            for _ in range(digit):
                press('up')
            if i < 7:
                press('right')
        press('start')
        original.tick(240, False)

    def word(address):
        return original.memory[address] | original.memory[address + 1] << 8

    def signed(address):
        return (original.memory[address] + 128) % 256 - 128

    def sample():
        m = original.memory
        return dict(tick=word(0xc00a), held=m[0xff8a], handler=word(0xc206),
                    frame=m[0xc200], flags=m[0xc205], x=word(0xc201), y=word(0xc203),
                    cameraX=word(0xff92), cameraY=word(0xff94), speed=signed(0xffa6),
                    rate=signed(0xffa5), tilt=signed(0xffa4), count=m[0xc209],
                    crash=m[0xc20b], anim=word(0xc300), done=int(bool(m[0xc302] & 128)),
                    waiting=int(bool(m[0xc302] & 64)), delay=m[0xc303], period=m[0xc304],
                    transfer=m[0xffb6], remaining=m[0xffb5], map=m[0xc00d],
                    result=m[0xc095], seconds=m[0xc084], secondTicks=m[0xc083],
                    random=word(0xc09e), params=list(m[0xc209:0xc210]))

    def tick(count=1, render=True):
        events.append(['tick', count, render])
        original.tick(count, render)

    def button(action, key):
        events.append([action, key])
        getattr(original, 'button_' + action)(key)

    try:
        original.tick(600, False)
        password(1)  # Air Bumper through the original UI.
        password(6)  # Normal difficulty through the original UI.
        if original.memory[0xc006] != 1 or original.memory[0xc007] != 1:
            raise RuntimeError('Original UI did not select the requested stunt/difficulty')
        # Save before hooks are registered: the control run has no instrumentation.
        with (out / 'setup.state').open('wb') as stream:
            original.save_state(stream)

        def before(_):
            if original.memory[0xc098] == 4:
                pre.append(sample())

        def after(_):
            if original.memory[0xc098] == 4:
                post.append(sample())

        original.hook_register(0, 0x03d8, before, None)
        original.hook_register(0, 0x03fa, after, None)
        button('press', 'start'); tick(2, False)
        button('release', 'start'); tick(82, False)
        button('press', 'start'); tick(2, False)
        button('release', 'start'); tick(2, False)
        for _ in range(1000):
            if post:
                break
            tick(1, False)
        if not post:
            raise RuntimeError('Original Air gameplay did not start')
        last = None
        stall = None
        for _ in range(6000):
            direction = 'left' if ((len(post) + 24) // 24) % 2 else 'right'
            button('press', 'a')
            if direction != last:
                if last:
                    button('release', last)
                button('press', direction)
                last = direction
            tick()
            if post[-1]['handler'] == 0x3bb3 and post[-1]['done']:
                stall = len(post) - 1
                original.screen.image.save(str(out / 'stalled.png'))
                break
            if post[-1]['result']:
                break
        if stall is not None:
            tick(600)
        original.screen.image.save(str(out / 'last.png'))
        expected = bytes(original.memory[0x8000:0x10000])
        (out / 'hooked-end.bin').write_bytes(expected)
    finally:
        original.stop(save=False)

    write_json(out / 'events.json', events)
    # A final pre-update hook may have fired before the last hardware frame ended.
    write_json(out / 'trace.json', dict(pre=pre[:len(post)], post=post))
    first = pre[0]
    with (out / 'inputs.txt').open('w', encoding='utf-8') as stream:
        stream.write(f"{first['tick'] - 1} {first['secondTicks']} {first['random']}\n")
        for row in pre[:len(post)]:
            stream.write(f"{row['tick']} {row['held']}\n")

    control = PyBoy(str(args.rom), window='null', sound_volume=0)
    control.set_emulation_speed(0)
    try:
        with (out / 'setup.state').open('rb') as stream:
            control.load_state(stream)
        for event in events:
            if event[0] == 'tick':
                control.tick(event[1], event[2])
            else:
                getattr(control, 'button_' + event[0])(event[1])
        actual = bytes(control.memory[0x8000:0x10000])
        control.screen.image.save(str(out / 'control-no-hooks.png'))
    finally:
        control.stop(save=False)
    differences = [hex(0x8000 + i) for i, (a, b) in enumerate(zip(expected, actual)) if a != b]
    frozen_fields = ('handler', 'done', 'x', 'y', 'cameraX', 'cameraY', 'seconds', 'secondTicks')
    frozen = stall is not None and all(all(row[k] == post[stall][k] for k in frozen_fields)
                                      for row in post[stall:])
    summary = dict(romSha256=hashlib.sha256(data).hexdigest(), python=platform.python_version(),
                   emulator='PyBoy', version=importlib.metadata.version('pyboy'),
                   bootRom='PyBoy bundled boot ROM', soundEmulated=True, soundVolume=0,
                   setup='Original password and Start inputs; no gameplay RAM writes',
                   hookAddresses=['00:03d8', '00:03fa'], completedUpdates=len(post),
                   stallUpdate=stall, frozenAfterStall=frozen,
                   observedUpdatesAfterStall=len(post) - stall - 1 if stall is not None else 0,
                   controlComparedBytes=len(actual), controlDifferences=differences,
                   controlMemorySha256=hashlib.sha256(actual).hexdigest(),
                   hardwareVerified=False)
    write_json(out / 'capture-summary.json', summary)
    print(json.dumps(summary, indent=2))
    if differences or not frozen:
        raise RuntimeError('Reference scenario or uninstrumented control did not match; inspect local evidence')


def compare(args):
    trace = json.loads((args.out / 'trace.json').read_text(encoding='utf-8'))
    post = trace['post']
    with args.native_csv.open(encoding='utf-8-sig', newline='') as stream:
        native = [{k: int(v) for k, v in row.items()} for row in csv.DictReader(stream)]
    if len(native) != len(post) or not post:
        raise ValueError('Expected exactly one native row for each completed original update')
    # Compare all observable fields exported by the probe except differently
    # represented script pointers, the native-only safeguard and the clock.
    fields = [k for k in native[0] if k not in ('anim', 'pending', 'tick')]
    first, mismatches = {}, []
    for index, (raw, row) in enumerate(zip(post, native)):
        source = dict(raw)
        source['handler'] = HANDLERS[source['handler']]
        source['seconds'] = (source['seconds'] >> 4) * 10 + (source['seconds'] & 15)
        source['map'] = int(bool(source['map']))
        delta = {k: [source[k], row[k]] for k in fields if source[k] != row[k]}
        for key, value in delta.items():
            first.setdefault(key, dict(update=index, original=value[0], native=value[1]))
        if delta:
            mismatches.append(dict(update=index, fields=delta))
    gaps = [dict(update=i, before=a['tick'], after=b['tick'])
            for i, (a, b) in enumerate(zip(trace['pre'], post)) if a['tick'] != b['tick']]
    prefix = mismatches[0]['update'] if mismatches else len(post)
    summary = dict(comparedUpdates=len(post), fields=fields, matchingPrefix=prefix,
                   firstDifferences=first, originalCounterChangesDuringUpdate=gaps,
                   firstDeferredRequest=next((i for i, row in enumerate(native) if row['pending']), None),
                   evidenceLimit='Recorded-clock mode supplies the original counter per update; '
                                 'it does not establish native real-time cadence or image/audio parity.')
    write_json(args.native_csv.with_suffix('.comparison.json'), summary)
    write_json(args.native_csv.with_suffix('.differences.json'), mismatches)
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='mode', required=True)
    record = sub.add_parser('capture')
    record.add_argument('rom', type=Path)
    record.add_argument('--reference-lib', type=Path)
    record.add_argument('--out', type=Path, default=Path('local/original-air'))
    diff = sub.add_parser('compare')
    diff.add_argument('native_csv', type=Path)
    diff.add_argument('--out', type=Path, default=Path('local/original-air'))
    options = parser.parse_args()
    (capture if options.mode == 'capture' else compare)(options)
