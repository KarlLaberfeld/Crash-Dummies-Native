"""Original perfect-result celebration component capture/comparison.

Only capture uses the separately authorized pinned reference. Native replay
inherits native stunt/prefix state and uses the recorded extent only as a bound.
This component qualification does not establish result IRQ/LCD scheduling.
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path

from air_reference import write_json
from extract import read_rom
from reference_backend import reference_class,require_matching_backend,require_capture_reference


def capture(args):
    manifest=json.loads((args.capture/'capture-summary.json').read_text())
    if manifest['controlDifferences'] or manifest['result']!=7 or manifest['romSha256']!=hashlib.sha256(read_rom(args.rom)).hexdigest():
        raise ValueError('Requires a genuine independently controlled perfect original')
    Reference,metadata=reference_class('sameboy');require_matching_backend(manifest,metadata)
    player=Reference(str(args.rom),window='null',sound_volume=0);player.set_emulation_speed(0)
    active=False;complete=False;opened=None;rows=[]
    def word(a):return player.memory[a]+256*player.memory[a+1]
    def state():return dict(random=word(0xc09e),emitters=[list(player.memory[0xc200+16*i:0xc205+16*i]) for i in range(4)])
    def hook(pc):
        nonlocal active,complete,opened
        if complete:return
        if pc==0x0462 and player.memory[0xc095]==7 and player.memory[0xc098]==2:active=True
        if not active:return
        if pc==0x151e:
            if opened is not None or player.memory[0xc095]!=7:raise ValueError('Unexpected celebration entry')
            opened=dict(start=player._cycles(),tick=word(0xc00a),before=state())
        elif pc==0x249b and opened is not None:
            opened.update(end=player._cycles(),after=state(),prepared=list(player.memory[0xc100:0xc1a0]))
            rows.append(opened);opened=None
        elif pc==0x02ce:
            if opened is not None or player.memory[0xc095]!=0:raise ValueError('Incomplete celebration handoff')
            active=False;complete=True
    try:
        with (args.capture/'setup.state').open('rb') as stream:player.load_state(stream)
        for pc in (0x0462,0x151e,0x249b,0x02ce):player.hook_register(0,pc,hook,pc)
        for event in json.loads((args.capture/'events.json').read_text()):
            if event[0]=='tick':player.tick(event[1],event[2])
            elif event[0] in ('press','release'):getattr(player,'button_'+event[0])(event[1])
            else:raise ValueError('Unknown original event')
        control=hashlib.sha256(bytes(player.memory[0x8000:0x10000])).hexdigest()
    finally:player.stop(save=False)
    if control!=manifest['controlMemorySha256'] or not complete:raise ValueError('Changed control or missing full celebration extent')
    data=dict(version=1,romSha256=manifest['romSha256'],controlMemorySha256=control,reference=metadata,
              terminal='nextInstruction',services=rows)
    analyze(data);args.out.mkdir(parents=True,exist_ok=True);write_json(args.out/'celebration.json',data)
    print(json.dumps(dict(services=len(rows),preparedBytes=160*len(rows),controlDifferences=0),indent=2))


def analyze(data):
    rows=data.get('services',[])
    if data.get('version')!=1 or data.get('terminal') not in ('nextInstruction','incomingFade') or not rows:
        raise ValueError('Missing complete celebration component extent')
    previous=None
    for row in rows:
        if not 0<row['end']-row['start']<70224 or not 0<=row['tick']<=65535:
            raise ValueError('Invalid celebration work/counter')
        if previous and (row['start']<=previous['end'] or row['tick']!=((previous['tick']+1)&65535) or row['before']!=previous['after']):
            raise ValueError('Missing/reordered celebration state continuity')
        for stage in ('before','after'):
            state=row[stage]
            if not 0<=state.get('random',-1)<=65535 or len(state.get('emitters',[]))!=4 or any(
                    len(e)!=5 or any(not 0<=v<=255 for v in e) for e in state['emitters']):
                raise ValueError('Incomplete celebration state')
        if (row['before']['random']&255)!=(row['after']['random']&255):raise ValueError('Celebration changed random low byte')
        prepared=row.get('prepared',[])
        if len(prepared)!=160 or any(not 0<=v<=255 for v in prepared):raise ValueError('Missing complete prepared sprite list')
        count=sum(prepared[i+3]==128 for i in range(0,160,4))
        if count%10 or any(prepared[i*4+3]!=128 for i in range(count)) or any(prepared[count*4:]):
            raise ValueError('Prepared celebration sprites/tail are not contiguous')
        previous=row
    return rows


def compare_component(data,native):
    rows=analyze(data)
    if len(native)!=len(rows):raise ValueError('Truncated native celebration extent')
    differences=[]
    for index,(target,row) in enumerate(zip(rows,native)):
        expected=dict(service=index,tick=target['tick'],work=target['end']-target['start'],random=target['after']['random'],
            spriteCount=sum(target['prepared'][i+3]==128 for i in range(0,160,4)))
        for i,emitter in enumerate(target['after']['emitters']):
            expected.update({f'emitter{i}{key}':value for key,value in zip(('x','y','velocity','radius','delay'),emitter)})
        expected.update({f'prepared{i}':value for i,value in enumerate(target['prepared'])})
        if any(key not in row for key in expected):raise ValueError('Missing native celebration component fields')
        delta={key:[value,int(row[key])] for key,value in expected.items() if int(row[key])!=value}
        if delta:differences.append(dict(service=index,fields=delta))
    return differences


def compare(args):
    manifest=json.loads((args.capture/'capture-summary.json').read_text());data=json.loads((args.out/'celebration.json').read_text())
    require_capture_reference(manifest,data)
    if manifest['controlDifferences'] or any(data.get(k)!=manifest.get(k) for k in ('romSha256','controlMemorySha256')):
        raise ValueError('Mixed celebration component control')
    with args.native_csv.open(encoding='utf-8-sig',newline='') as stream:native=list(csv.DictReader(stream))
    differences=compare_component(data,native)
    result=dict(comparedServices=len(native),preparedBytes=160*len(native),differences=len(differences),
        firstDifference=differences[0] if differences else None,productionSchedulerAccepted=False,
        evidenceLimit='Complete isolated native celebration component: emitters, shared RNG, prepared sprite bytes and source body work through first result handoff. Inherits native gameplay/prefix state; extent is only a replay bound. Excludes publication/IRQ/LCD/readiness timing, result accounting/layout/music, complete images/PCM and Windows scheduling.')
    write_json(args.native_csv.with_suffix('.comparison.json'),result);print(json.dumps(result,indent=2))
    if differences:raise ValueError('Native celebration component differs')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='mode',required=True)
    record=sub.add_parser('capture');record.add_argument('rom',type=Path)
    diff=sub.add_parser('compare');diff.add_argument('native_csv',type=Path)
    for command in (record,diff):
        command.add_argument('--capture',type=Path,required=True);command.add_argument('--out',type=Path,required=True)
    args=parser.parse_args();{'capture':capture,'compare':compare}[args.mode](args)
