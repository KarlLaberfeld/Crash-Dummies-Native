"""Read-only original pause graphics-bus observations; never native inputs.

Requires the independent SameBoy reference and an input-only control recording.
Actual STAT read bytes/time are observed without replacing memory or opcodes.
Write notifications describe attempts before the reference's access decision.
"""
import argparse
import hashlib
import json
from pathlib import Path

from air_reference import write_json
from extract import read_rom
from reference_backend import reference_class,require_matching_backend

VERSION=1


def capture(args):
    rom=read_rom(args.rom);manifest=json.loads((args.capture/'capture-summary.json').read_text())
    if hashlib.sha256(rom).hexdigest()!=manifest['romSha256'] or manifest['controlDifferences'] or not manifest.get('pauseSamples'):
        raise ValueError('Requires a matching control-verified pause recording')
    Reference,metadata=reference_class('sameboy');require_matching_backend(manifest,metadata)
    p=Reference(str(args.rom),window='null',sound_volume=0);p.set_emulation_speed(0)
    pauses=[];current=None;phase=None;copy_index=0;startup=[];lcd_writes=[]
    def point(address):
        nonlocal current,phase,copy_index
        if address==0x1476 and p.memory[0xc098]==4:
            if current is not None:raise ValueError('Nested pause')
            # The shared C100 DMA source remains readable during mode 2.
            # CPU-addressed OAM reads here would be blocked and return FF.
            current=dict(points=[],bus=[],branches=[],entryDmaSourceObjects=[dict(y=p.memory[0xc100+4*i],x=p.memory[0xc101+4*i],
                tile=p.memory[0xc102+4*i],flags=p.memory[0xc103+4*i]) for i in range(40)])
            pauses.append(current);phase='entry';copy_index=0
        if address==0x03c6 and p.memory[0xc098]==4:
            startup.append(dict(cycles=p._cycles(),lcd=p.lcd_snapshot()))
        if current is None:return
        if address==0x2359:phase='copy'+str(copy_index);copy_index+=1
        elif address==0x14ac:phase='script'
        elif address==0x14b9:phase='wait'
        elif address==0x14c2:phase='restore'
        elif address==0x14dc:phase='audio'
        if address==0x1476 or address==0x14dc or (address==0x14b9 and not any(s['pc']==0x14b9 for s in current.get('graphicsStates',[]))):
            # Accepted storage after writes, including boundaries where a CPU
            # read would be blocked. The observer never changes time or data.
            current.setdefault('graphicsStates',[]).append(dict(pc=address,cycles=p._cycles(),**p.pause_graphics_storage()))
        if address in (0x2365,0x2125):
            current['branches'].append(dict(phase=phase,cycles=p._cycles(),blocked=not bool(p.register_file.F&128),pc=address))
        else:current['points'].append(dict(pc=address,cycles=p._cycles(),lcd=p.lcd_snapshot(),phase=phase))
        if address==0x03d8:
            if copy_index!=4:raise ValueError('Incomplete copies')
            current=None;phase=None
    def bus(event):
        if event['kind']=='write' and event['address']==0xff40 and event['pc']==0x25ae:
            lcd_writes.append(dict(**event,lcd=p.lcd_snapshot()))
        if current is None:return
        # These PC values identify the actual register/data bus access. They
        # are observer filters, not instructions interpreted by the port.
        if event['address']==0xff41 and event['pc'] not in (0x2363,0x2123):return
        if event['address']!=0xff41 and event['address']!=0xff40 and event['pc'] not in (0x2368,0x2369,0x2129):return
        current['bus'].append(dict(**event,phase=phase,lcd=p.lcd_snapshot()))
    try:
        with (args.capture/'setup.state').open('rb') as stream:p.load_state(stream)
        p.observe_graphics_bus(bus)
        for address in (0x03c6,0x1476,0x2359,0x14ac,0x14b9,0x14c2,0x14dc,0x03d8,0x2365,0x2125):p.hook_register(0,address,point,address)
        for event in json.loads((args.capture/'events.json').read_text()):
            if event[0]=='tick':p.tick(event[1],event[2])
            elif event[0] in ('press','release'):getattr(p,'button_'+event[0])(event[1])
            else:raise ValueError('Unknown replay event')
        control=hashlib.sha256(bytes(p.memory[0x8000:0x10000])).hexdigest()
    finally:p.stop(save=False)
    if not pauses or current is not None or control!=manifest['controlMemorySha256']:raise ValueError('Incomplete pause or altered control state')
    args.out.mkdir(parents=True,exist_ok=True)
    data=dict(version=VERSION,reference=metadata,romSha256=manifest['romSha256'],controlMemorySha256=control,pauses=pauses,startup=startup,lcdEnableWrites=lcd_writes)
    write_json(args.out/'lcd.json',data);report_data(data,args.out)


def analyze(data):
    if data.get('version')!=VERSION or not data.get('pauses'):raise ValueError('Requires current complete pause bus capture')
    groups=[]
    for pi,pause in enumerate(data['pauses']):
        for phase in ('copy0','copy1','script','copy2','copy3'):
            events=[e for e in pause['bus'] if e['phase']==phase]
            polls=[e for e in events if e['kind']=='read' and e['address']==0xff41]
            branches=[e for e in pause['branches'] if e['phase']==phase]
            if not polls or len(polls)!=len(branches):raise ValueError('Missing poll/branch observations')
            for poll,branch in zip(polls,branches):
                if poll['cycles']>=branch['cycles'] or bool(poll['data']&2)!=branch['blocked']:
                    raise ValueError('Observed STAT byte does not own its subsequent branch')
            counts=[sum((e['data']&3)==mode for e in polls) for mode in range(4)]
            accesses=[e for e in events if 0x8000<=e['address']<0xa000]
            reads=[e for e in accesses if e['kind']=='read']
            groups.append(dict(pause=pi,phase=phase,polls=len(polls),failedPolls=counts[2]+counts[3],
                statModes=counts,successfulPolls=counts[0]+counts[1],vramReads=len(reads),
                blockedVramReads=sum(e['lcd']['readBlocked'] for e in reads),
                attemptedVramWrites=sum(e['kind']=='write' for e in accesses),
                scanlines=sorted(set(e['lcd']['line'] for e in polls)),
                scrollX=sorted(set(e['lcd']['scx'] for e in polls)),windowX=sorted(set(e['lcd']['wx'] for e in polls))))
    return dict(pauses=len(data['pauses']),groups=groups,nativePollingAccepted=False,
        evidenceLimit='Actual STAT bytes own recorded branches. LCD/internal fields are independent reference targets, never native inputs. Writes are attempts before reference LCD synchronization; no successful-write, pixels, PCM or hardware claim.')


def report_data(data,out):
    result=analyze(data);write_json(out/'summary.json',result);print(json.dumps(result,indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='mode',required=True)
    rec=sub.add_parser('capture');rec.add_argument('rom',type=Path);rec.add_argument('--capture',type=Path,required=True)
    for mode in (rec,sub.add_parser('report')):mode.add_argument('--out',type=Path,default=Path('local/air-pause-lcd'))
    args=parser.parse_args()
    if args.mode=='capture':capture(args)
    else:report_data(json.loads((args.out/'lcd.json').read_text()),args.out)
