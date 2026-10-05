"""Local original Air audio-stop and outgoing-fade evidence.

Capture uses the separately authorized reference emulator. Native comparison
uses semantic phase boundaries, never original counters/costs as runtime input.
Original palette data, recordings and measurements remain local.
"""
import argparse
import csv
import hashlib
import importlib.metadata
import json
from pathlib import Path
import sys

from air_reference import write_json
from air_timing import elapsed_work,IRQ_PHASES,VBLANK_FIXED,vblank_work,vblank_bookkeeping_work,display_cycles
from air_loop_timing import wait_active_cycles,stat_cycles
from extract import read_rom
from reference_backend import reference_class,require_matching_backend,require_capture_reference

VERSION=2
POINTS={0x0403:'audioStop',0x0406:'fadeEntry',0x20b9:'palette',0x20c7:'wait',0x20ca:'tail',0x0409:'end'}


def stop_work():
    # Inclusive caller; 44 register bytes, 250 state bytes and 16 wave bytes.
    return 92+36+(44*24-4)+24+(250*40-4)+308+(16*52-4+16)+32


def intervals(data):
    if data.get('version')!=VERSION:raise ValueError('Recapture original exit boundaries')
    points=data['points'];interrupts=data['interrupts']
    if not points or points[0]['name']!='audioStop' or points[-1]['name']!='end':raise ValueError('Incomplete original audio-stop/fade interval')
    if any(p['cycles']>=q['cycles'] for p,q in zip(points,points[1:])):raise ValueError('Unordered exit boundaries')
    palettes=data['fadePalettes']
    if len(palettes)!=8 or any(not 0<=n<=255 for n in palettes):raise ValueError('Invalid source palette data')
    rows=[];segment=-1;wait=0;seen=[]
    for p,q in zip(points,points[1:]):
        name=p['name'];index=0
        if name=='audioStop':
            if q['name']!='fadeEntry':raise ValueError('Missing audio-stop return')
            predicted=stop_work()
        elif name=='fadeEntry':
            if q['name']!='palette':raise ValueError('Missing fade entry')
            predicted=44
        elif name=='palette':
            segment+=1;index=segment
            if q['name']!='wait' or segment>=8:raise ValueError('Invalid palette segment')
            predicted=76
        elif name=='wait':
            if q['name']!='tail':raise ValueError('Missing fade-wait return')
            index=wait;wait+=1
            included=[r for r in interrupts if p['cycles']<=r['start']-20 and r['end']+16<=q['cycles']]
            if sum(r['kind']=='vblank' for r in included)!=1:raise ValueError('Unsupported fade-wait display ownership')
            if any(r.get('returnAddress')!=0x261d for r in included):raise ValueError('Unsupported fade-wait interrupt boundary')
            wakes=sum(r['kind']=='stat' for r in included)
            predicted=wait_active_cycles(wakes)
        elif name=='tail':
            index=wait-1
            expected='wait' if wait%4 else 'end' if wait==32 else 'palette'
            if q['name']!=expected:raise ValueError('Invalid fade branch order')
            predicted=16 if wait%4 else 40 if wait==32 else 28
        else:raise ValueError('Unexpected original exit phase')
        active=elapsed_work(p['cycles'],q['cycles'],interrupts)
        idle=active-predicted if name=='wait' else 0
        if name=='wait' and (idle<0 or idle%4):raise ValueError('Invalid measured fade HALT idle')
        if name!='wait' and active!=predicted:raise ValueError(f'Exit work differs in {name}: {active} vs source {predicted}')
        if q['ready'] or q['musicEnabled']:raise ValueError('Outgoing fade enables resource gate or music')
        if segment>=0:
            palette=palettes[segment]
            if (q['bgp'],q['obp0'],q['obp1'])!=(palette,palette&0xcf,palette&0xf3):raise ValueError('Palette writes disagree with identified source table')
        rows.append(dict(phase=name,index=index,tickBefore=p['tick'],tickAfter=q['tick'],elapsed=q['cycles']-p['cycles'],
                         work=predicted,activeSource=predicted,idle=idle,
                         bgp=q['bgp'],obp0=q['obp0'],obp1=q['obp1'],musicEnabled=q['musicEnabled']))
        seen.append(name)
    if segment!=7 or wait!=32 or seen.count('tail')!=32:raise ValueError('Incomplete fade palette/wait sequence')
    return rows


def report(args):
    data=json.loads((args.out/'exit.json').read_text());rows=intervals(data)
    unknown=[i for i,q in enumerate(data['interrupts']) if q['kind']=='stat' and stat_cycles(q['selector'])!=q['end']-q['start']]
    if unknown:raise ValueError('Unreconstructed/mismatched exit STAT services')
    services=display_services(data)
    result=dict(phases=len(rows),palettes=8,waits=32,sourceWorkDifferences=0,
                displayServices=len(services),displayComponentDifferences=0,
                runtimeSchedulingFixed=False,evidenceLimit='Bounded audio-stop/fade work and palette-register ownership; original software audio-reset state, pixels, PCM, result setup and Windows integration remain unverified.')
    write_json(args.out/'summary.json',result);print(json.dumps(result,indent=2))


def capture(args):
    rom=read_rom(args.rom);manifest=json.loads((args.capture/'capture-summary.json').read_text())
    if manifest['controlDifferences'] or manifest['romSha256']!=hashlib.sha256(rom).hexdigest():raise ValueError('Requires matching control-verified replay')
    PyBoy,metadata=reference_class(getattr(args,'reference_backend','pyboy'),args.reference_lib)
    require_matching_backend(manifest,metadata)
    p=PyBoy(str(args.rom),window='null',sound_volume=0);p.set_emulation_speed(0)
    points=[];interrupts=[];opened=None;active=False
    def word(a):return p.memory[a]+256*p.memory[a+1]
    def hook(a):
        nonlocal opened,active
        now=p._cycles()
        if a==0x0403 and p.memory[0xc098]==4:active=True
        if a in IRQ_PHASES and opened is not None and opened['kind']=='vblank':
            name=IRQ_PHASES[a];opened['phases'][name]=now
            if name=='display':
                opened['held']=p.memory[0xff8a]
                opened['displayWorkload']=dict(map_pending=p.memory[0xc00d],ready=p.memory[0xffae],chunks=p.memory[0xffb5],cursor=p.memory[0xc04c],tick=word(0xc00a),fade_remaining=p.memory[0xffc9],collected=p.memory[0xc20a],quota=p.memory[0xffab])
            if name=='bookkeeping':
                opened.update(resetEnabled=p.memory[0xc005],resetLatched=p.memory[0xc004],hudBar=list(p.memory[0xc046:0xc04c]))
            if name=='effects':opened['effectRequest']=-1 if p.memory[0xffc6]==255 else p.memory[0xffc6]
            if name=='music':opened['musicEnabled']=p.memory[0xffcf]
            return
        if a in POINTS and active:
            points.append(dict(name=POINTS[a],cycles=now,tick=word(0xc00a),counter=p.memory[0xc009],
                               ready=p.memory[0xffae],musicEnabled=p.memory[0xffcf],bgp=p.memory[0xff47],obp0=p.memory[0xff48],obp1=p.memory[0xff49]))
            if a==0x0409:active=False
        elif active and a in (0x0040,0x0048):
            if opened is not None:raise ValueError('Nested exit interrupt')
            opened=dict(kind='vblank' if a==0x0040 else 'stat',start=now,selector=p.memory[0xc099],returnAddress=word(p.register_file.SP),tick=word(0xc00a),ready=p.memory[0xffae],phases={})
        elif a in (0x2484,0x2555) and opened is not None:
            if opened['kind']!=('vblank' if a==0x2484 else 'stat'):raise ValueError('Unexpected exit interrupt return')
            opened['end']=now;interrupts.append(opened);opened=None
    try:
        with (args.capture/'setup.state').open('rb') as f:p.load_state(f)
        for a in (*POINTS,*IRQ_PHASES,0x0040,0x0048,0x2484,0x2555):p.hook_register(0,a,hook,a)
        for e in json.loads((args.capture/'events.json').read_text()):
            if e[0]=='tick':p.tick(e[1],e[2])
            elif e[0] in ('press','release'):getattr(p,'button_'+e[0])(e[1])
            else:raise ValueError('Unknown replay event')
        control=hashlib.sha256(bytes(p.memory[0x8000:0x10000])).hexdigest()
    finally:p.stop(save=False)
    if control!=manifest['controlMemorySha256'] or opened is not None or active:raise ValueError('Changed control or incomplete exit capture')
    args.out.mkdir(parents=True,exist_ok=True)
    write_json(args.out/'exit.json',dict(version=VERSION,romSha256=manifest['romSha256'],controlMemorySha256=control,
                                      reference=metadata,fadePalettes=list(rom[0x2118:0x2120]),points=points,interrupts=interrupts))
    report(args)


def display_services(data):
    services=[q for q in data['interrupts'] if q['kind']=='vblank']
    if len(services)!=32:raise ValueError('Requires all outgoing-fade display services')
    for q in services:
        if q['ready'] or q['effectRequest']!=-1 or q['musicEnabled']:raise ValueError('Unsupported fade resource/effect/music ownership')
        expected={**VBLANK_FIXED,'display':sum(display_cycles(**q['displayWorkload']).values()),'bookkeeping':vblank_bookkeeping_work(q['resetEnabled'],q['held'],q['resetLatched']),'effects':64,'music':60}
        measured=vblank_work(q)
        if measured!=expected or any(n<0 for n in expected.values()):raise ValueError('Outgoing display components disagree with source')
    return services


def compare_service_rows(data,native):
    services=display_services(data)
    if len(native)<len(services):raise ValueError('Incomplete native fade services')
    differences=[]
    for index,(q,row) in enumerate(zip(services,native[-len(services):])):
        b=vblank_work(q)
        expected=dict(tick=q['tick'],ready=0,display=b['display'],effects=b['effects'],music=b['music'],cursor=(q['displayWorkload']['cursor']+1)%13,pending=-1,inputHeld=q['held'])
        expected.update({'bar'+str(i):v for i,v in enumerate(q['hudBar'])})
        if any(name not in row for name in expected):raise ValueError('Incomplete native fade-service fields')
        delta={name:[value,row[name]] for name,value in expected.items() if value!=row[name]}
        if delta:differences.append(dict(service=index,fields=delta))
    return differences


def compare(args):
    data=json.loads((args.out/'exit.json').read_text());expected=intervals(data)
    if getattr(args,'capture',None):
        manifest=json.loads((args.capture/'capture-summary.json').read_text());require_capture_reference(manifest,data)
        if manifest['controlDifferences'] or any(data[k]!=manifest[k] for k in ('romSha256','controlMemorySha256')):
            raise ValueError('Exit recording differs from the verified original control')
    elif data.get('reference',{}).get('emulator')=='SameBoy':
        raise ValueError('Independent exit comparison requires --capture provenance')
    with args.native_csv.open(encoding='utf-8-sig',newline='') as f:
        native=[{k:v if k=='phase' else int(v) for k,v in row.items()} for row in csv.DictReader(f)]
    if len(native)!=len(expected):raise ValueError('Incomplete native exit phase coverage')
    differences=[]
    for i,(q,row) in enumerate(zip(expected,native)):
        if len(row)!=10 or any(name not in row for name in ('phase','index','tickBefore','tickAfter','elapsed','work','bgp','obp0','obp1','musicEnabled')):raise ValueError('Incomplete native exit fields')
        delta={name:[q[name],value] for name,value in row.items() if q[name]!=value}
        if delta:differences.append(dict(phase=i,fields=delta))
    result=dict(comparedPhases=len(native),differences=len(differences),firstDifference=differences[0] if differences else None,
                runtimeSchedulingFixed=False,evidenceLimit='Exact phase spans, counters and source costs/register palettes; no original timing or outcome drives native execution. Pixels, PCM, reset voice state, result setup and production loop remain unverified.')
    service_differences=[]
    if args.services_csv:
        with args.services_csv.open(encoding='utf-8-sig',newline='') as f:services=[{k:int(v) for k,v in row.items()} for row in csv.DictReader(f)]
        service_differences=compare_service_rows(data,services)
        result.update(comparedDisplayServices=32,displayDifferences=len(service_differences),firstDisplayDifference=service_differences[0] if service_differences else None)
    write_json(args.native_csv.with_suffix('.comparison.json'),result);print(json.dumps(result,indent=2))
    if differences or service_differences:raise ValueError('Native audio-stop/fade differs from original')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='mode',required=True)
    rec=sub.add_parser('capture');rec.add_argument('rom',type=Path);rec.add_argument('--reference-lib',type=Path);rec.add_argument('--capture',type=Path,required=True)
    rec.add_argument('--reference-backend',choices=('pyboy','sameboy'),default='pyboy')
    diff=sub.add_parser('compare');diff.add_argument('native_csv',type=Path);diff.add_argument('--services-csv',type=Path)
    diff.add_argument('--capture',type=Path,help='Original control manifest; required for independent exit records')
    for q in (rec,diff,sub.add_parser('report')):q.add_argument('--out',type=Path,default=Path('local/air-exit-timing'))
    args=parser.parse_args();{'capture':capture,'report':report,'compare':compare}[args.mode](args)
