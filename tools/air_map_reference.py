"""Read-only original Air row staging/publication; all captured bytes stay local.

Capture alone uses the separately authorized pinned SameBoy reference. Native
maps, staged rows, write completion and publication come from native assets.
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path
from air_reference import write_json
from extract import read_rom
from reference_backend import reference_class,require_matching_backend,require_capture_reference
from air_following_scope import FollowingAirCaptureScope


def capture(args):
    manifest=json.loads((args.capture/'capture-summary.json').read_text())
    following=getattr(args,'next_retry',False)
    if manifest['controlDifferences'] or hashlib.sha256(read_rom(args.rom)).hexdigest()!=manifest['romSha256'] or manifest.get('pauseAfter',0) and not following:
        raise ValueError('Requires a matching original control without pause')
    Reference,metadata=reference_class('sameboy');require_matching_backend(manifest,metadata)
    p=Reference(str(args.rom),window='null',sound_volume=0);p.set_emulation_speed(0)
    active=False;complete=False;service=-1;points=[];armed=False;scope=FollowingAirCaptureScope(following);tile_writes=0;last_tile_writes=0
    def bus(event):
        nonlocal tile_writes
        if active and not complete and event['kind']=='write' and 0x9800<=event['address']<0x9c00:tile_writes+=1
    def word(a):return p.memory[a]+256*p.memory[a+1]
    def snapshot(name):
        nonlocal last_tile_writes
        lcd=p.lcd_snapshot()
        retained=following and name=='end' and points and points[-1]['boundary']=='after' and tile_writes==last_tile_writes
        if lcd['readBlocked'] and not retained:raise ValueError('Blocked CPU-style tile storage snapshot requires another owner')
        row=dict(boundary=name,service=service+1 if name=='end' else max(service,0),cycles=p._cycles(),camera=word(0xff94),lastCamera=word(0xff96),
            pending=p.memory[0xc00d],row=p.memory[0xc00c]//8,buffer=list(p.memory[0xc00e:0xc02e]),
            tiles=points[-1]['tiles'][:] if lcd['readBlocked'] else list(p.memory[0x9800:0x9c00]),lcd=lcd)
        if lcd['readBlocked']:row.update(tilesReadOwner='retained-unblocked-vram-v1',tilesObservedAt=points[-1]['cycles'],tilesWriteAttemptsSince=0)
        points.append(row);last_tile_writes=tile_writes
    def hook(pc):
        nonlocal active,complete,service,armed
        if complete:return
        if pc==0x268b and scope.ready and p.memory[0xc098] in (2,10):armed=True
        scope.observe(pc,p.memory[0xc098])
        if pc==0x03c6 and (not following or armed) and p.memory[0xc098]==4:
            if active:raise ValueError('Multiple Air starts require another control')
            active=True;snapshot('startup')
        if not active or p.memory[0xc098]!=4:return
        if pc==(0x0403 if following else 0x0409):snapshot('end');active=False;complete=True;return
        if pc==0x2436:service+=1
        elif pc==0x0c3f:snapshot('before')
        elif pc==0x0c42:snapshot('after')
    try:
        with (args.capture/'setup.state').open('rb') as f:p.load_state(f)
        if following:p.observe_graphics_bus(bus)
        for pc in (0x03c6,0x03d8,0x268b,0x2436,0x0c3f,0x0c42,0x0403,0x0409):p.hook_register(0,pc,hook,pc)
        for event in json.loads((args.capture/'events.json').read_text()):
            if event[0]=='tick':p.tick(event[1],event[2])
            elif event[0] in ('press','release'):getattr(p,'button_'+event[0])(event[1])
            else:raise ValueError('Unknown original input event')
        control=hashlib.sha256(bytes(p.memory[0x8000:0x10000])).hexdigest()
    finally:p.stop(save=False)
    if control!=manifest['controlMemorySha256'] or not complete:raise ValueError('Changed original row control or missing result boundary')
    data=dict(version=1,reference=metadata,romSha256=manifest['romSha256'],controlMemorySha256=control,points=points)
    if following:data['nextRetry']=True
    analyze(data);args.out.mkdir(parents=True,exist_ok=True);write_json(args.out/'map.json',data)
    print(json.dumps(dict(boundaries=len(points),services=service+1,controlDifferences=0,nativeCompared=False)))


def analyze(data):
    points=data.get('points',[])
    if data.get('version')!=1 or len(points)<4 or len(points)%2 or points[0]['boundary']!='startup' or points[-1]['boundary']!='end':
        raise ValueError('Incomplete native row publication evidence')
    count=(len(points)-2)//2
    expected=['startup']+['before','after']*count+['end']
    if [p['boundary'] for p in points]!=expected or any(b['cycles']<=a['cycles'] for a,b in zip(points,points[1:])):
        raise ValueError('Row publication order differs')
    for i,p in enumerate(points):
        service=count if p['boundary']=='end' else max(0,(i-1)//2)
        retained=i==len(points)-1 and data.get('nextRetry') and p.get('tilesReadOwner')=='retained-unblocked-vram-v1' and p.get('tilesObservedAt')==points[-2]['cycles'] and p.get('tilesWriteAttemptsSince')==0 and p['tiles']==points[-2]['tiles'] and not points[-2]['lcd']['readBlocked']
        if p['service']!=service or p['pending'] not in (0,1) or not 0<=p['row']<32 or p['lcd']['readBlocked'] and not retained:
            raise ValueError('Invalid row publication owner/storage read')
        if len(p['buffer'])!=32 or len(p['tiles'])!=1024 or any(not 0<=v<128 for v in p['buffer']+p['tiles']):
            raise ValueError('Incomplete/invalid row bytes')
    for before,after in zip(points[1:-1:2],points[2:-1:2]):
        if any(before[k]!=after[k] for k in ('service','row','buffer','pending','camera','lastCamera')):
            raise ValueError('Display transfer changed native staging state')
        if after['cycles']-before['cycles']!=24+(736 if before['pending'] else 40):
            raise ValueError('Row transfer source work differs')
        expected=before['tiles'][:]
        if before['pending']:expected[32*before['row']:32*(before['row']+1)]=before['buffer']
        if after['tiles']!=expected:raise ValueError('Original transferred row bytes differ')
    return points


def compare_rows(data,native,epoch):
    points=analyze(data)
    if len(points)!=len(native):raise ValueError('Truncated native row comparison')
    differences=[]
    for i,(p,n) in enumerate(zip(points,native)):
        if n['boundary']!=p['boundary']:raise ValueError('Reordered native row comparison')
        target=dict(cycle=p['cycles']-epoch,service=p['service'],pending=p['pending'],row=p['row'])
        target.update({'buffer'+str(i):v for i,v in enumerate(p['buffer'])})
        target.update({'tile'+str(i):v for i,v in enumerate(p['tiles'])})
        changed={k:[v,int(n[k])] for k,v in target.items() if v!=int(n[k])}
        if changed:differences.append(dict(boundary=i,fields=changed))
    return differences


def compare(args):
    manifest=json.loads((args.capture/'capture-summary.json').read_text());data=json.loads((args.out/'map.json').read_text())
    startup=json.loads((args.startup/'startup.json').read_text())
    for item in (data,startup):require_capture_reference(manifest,item)
    if manifest['controlDifferences'] or any(item.get(k)!=manifest.get(k) for item in (data,startup) for k in ('romSha256','controlMemorySha256')):
        raise ValueError('Mixed row publication controls')
    from air_startup_reference import analyze as startup_epoch
    epoch=startup_epoch(startup)['epoch']
    with args.native_csv.open(newline='',encoding='utf-8-sig') as f:native=list(csv.DictReader(f))
    differences=compare_rows(data,native,epoch)
    result=dict(comparedBoundaries=len(native),comparedBytes=len(native)*1056,differences=len(differences),
        retainedTerminalTiles=bool(data['points'][-1].get('tilesReadOwner')),
        firstDifference=differences[0] if differences else None,productionSchedulerAccepted=False,
        evidenceLimit='Complete row staging/destination and unblocked tile storage before/after each captured Air display, with native source times. A marked blocked terminal endpoint retains the last unblocked tiles only across an observed zero-write-attempt interval; RAM is read at the endpoint. Does not certify arbitrary blocked reads, pixels, entities/resources, hardware or Windows scheduling.')
    write_json(args.native_csv.with_suffix('.comparison.json'),result);print(json.dumps(result,indent=2))
    if differences:raise ValueError('Native row publication differs from original')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='mode',required=True)
    record=sub.add_parser('capture');record.add_argument('rom',type=Path)
    record.add_argument('--next-retry',action='store_true')
    diff=sub.add_parser('compare');diff.add_argument('native_csv',type=Path);diff.add_argument('--startup',type=Path,required=True)
    for command in (record,diff):command.add_argument('--capture',type=Path,required=True);command.add_argument('--out',type=Path,required=True)
    args=parser.parse_args();{'capture':capture,'compare':compare}[args.mode](args)
