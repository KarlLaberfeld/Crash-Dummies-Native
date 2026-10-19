"""Compare post-retry handoff/instruction work and continuing state attachment."""
import argparse,csv,json
from pathlib import Path
from air_reference import write_json
from reference_backend import require_capture_reference
from air_handoff_reference import compare_handoff
from air_instruction_header_reference import compare_header
from air_instruction_picture_reference import compare_picture
from air_instruction_map_reference import compare_map
from air_instruction_text_reference import compare_text

PARTS=('handoff','header','picture','map','text')
COMPARATORS=(compare_handoff,compare_header,compare_picture,compare_map,compare_text)


def attachments(result,records):
    if result.get('followingResult') is not True or result.get('failureHold') is not True or result['points'][-1]['name']!='failureResultReturned':
        raise ValueError('Next instruction requires the completed restarted failure hold')
    previous=result['points'][-1];player=previous['player'];lives=previous['lives']
    if player not in (0,1) or not 1<=lives<=254 or previous['result']&6 or not previous['result']&1:raise ValueError('Unowned next campaign entry')
    displays=sum(r['kind']=='vblank' for r in result['interrupts']);stats=len(result['interrupts'])-displays
    result_enable=next(p for p in result['points'] if p['name']=='enable');epoch=result_enable['cycles']-20
    stage=difficulty=None;states=[]
    for part in PARTS:
        data=records[part]
        if data.get('followingResult') is not True:raise ValueError('Missing post-retry instruction capture scope')
        first=data['points'][0];last=data['points'][-1]
        if any(first[k]!=previous[k] for k in ('cycles','tick','countdown','inputHeld','inputPressed')):raise ValueError('Detached post-retry instruction endpoint/input')
        if data.get('precedingDisplays')!=displays:raise ValueError('Instruction displays lost their restarted result origin')
        if part=='handoff':
            if first['player']!=player or first['result']!=previous['result'] or first['lives'+str(player)]!=lives:raise ValueError('Handoff lost the consumed campaign life')
            player=last['player']
            if last['result'] or last['lives'+str(player)]!=lives:raise ValueError('Handoff changed the surviving campaign')
        if part=='header':
            stage=first['stage'];difficulty=first['difficulty']
            if any(p['player']!=player or p['lives']!=lives or p['stage']!=stage or p['difficulty']!=difficulty or p['result'] for p in data['points']):raise ValueError('Instruction header lost its campaign selection')
        if part=='picture' and first['stage']!=stage:raise ValueError('Picture selected another stunt')
        if part=='text' and data['campaign']!=dict(player=player,stage=stage,difficulty=difficulty):raise ValueError('Text selected another campaign')
        services=sum(r['kind']=='vblank' for r in data['interrupts']);stat_services=len(data['interrupts'])-services
        if last['tick']!=(first['tick']+services)&65535:raise ValueError('Instruction endpoint lost display counters')
        states.append(dict(part=part,first=first,last=last,firstDisplays=displays,firstStats=stats,player=player,lives=lives))
        displays+=services;stats+=stat_services;states[-1].update(displays=displays,stats=stats)
        previous=last
    return states,epoch,stage,difficulty


def compare_chain(result,records,native,entry,prior_scroll,epoch):
    states,lcd_epoch,stage,difficulty=attachments(result,records)
    if len(entry)!=1 or len(prior_scroll)!=1:raise ValueError('Missing native result/scroll inheritance endpoint')
    differences=[]
    def check(where,expected,actual):
        if any(k not in actual for k in expected):raise ValueError('Incomplete native continuation state')
        delta={k:[v,int(actual[k])] for k,v in expected.items() if int(actual[k])!=v}
        if delta:differences.append(dict(category=where,fields=delta))
    first=result['points'][-1]
    check('entry',dict(end=first['cycles']-epoch,tick=first['tick'],countdown=first['countdown'],displays=states[0]['firstDisplays'],stats=states[0]['firstStats'],player=first['player'],lives=first['lives']),entry[0])
    inherited=records['map']['points'][0]['scroll']
    check('inheritedScroll',dict(scroll=inherited),prior_scroll[0])
    for i,state in enumerate(states):
        part=state['part'];data=records[part];rows=native[part]
        args=[rows[k] for k in ('points','services','irqs','polls')]
        if part!='map':args.append(rows['writes'])
        differences.extend(dict(part=part,detail=d) for d in COMPARATORS[i](data,*args,rows['summary'],epoch))
        if len(rows['summary'])!=1:raise ValueError('Missing native next instruction summary')
        for index,row in enumerate(rows['services']):check(part+'Service',dict(service=state['firstDisplays']+index),row)
        last=state['last'];compare_line=95 if part in ('map','text') else 143
        def future(line):
            now=last['cycles'];deadline=lcd_epoch+(now-lcd_epoch)//70224*70224+line*456
            if deadline<=now:deadline+=70224
            return deadline-epoch
        expected=dict(end=last['cycles']-epoch,tick=last['tick'],countdown=last['countdown'],displays=state['displays'],stats=state['stats'],lcdEpoch=lcd_epoch-epoch,nextStat=future(compare_line),nextVBlank=future(144),player=state['player'],lives0=records['handoff']['points'][-1]['lives0'],lives1=records['handoff']['points'][-1]['lives1'],result=0,stage=stage,difficulty=difficulty)
        expected['scroll']=inherited if part in ('handoff','header','picture') else last['scroll']
        check(part+'Summary',expected,rows['summary'][0])
        if part=='header':
            for row in rows['points']:check('headerLives',dict(lives=state['lives']),row)
    return differences


def require_generation(result,records,after_retry):
    if after_retry not in (1,2,3):raise ValueError('Unknown instruction generation')
    if after_retry>=2 and (result.get('nextRetry') is not True or result.get('afterRetry',1)!=after_retry-1):raise ValueError('Missing completed preceding retry result')
    if any(data.get('afterRetry',1)!=after_retry for data in records.values()):raise ValueError('Mixed instruction generations')


def compare(args):
    manifest=json.loads((args.capture/'capture-summary.json').read_text());startup=json.loads((args.startup/'startup.json').read_text())
    result=json.loads(((getattr(args,'result_out',None) or args.out)/'result-transition.json').read_text())
    files=dict(handoff='handoff.json',header='header.json',picture='picture.json',map='transition.json',text='text.json')
    records={part:json.loads((args.out/name).read_text()) for part,name in files.items()}
    after_retry=getattr(args,'after_retry',1);require_generation(result,records,after_retry)
    for record in [startup,result,*records.values()]:
        require_capture_reference(manifest,record)
        if manifest['controlDifferences'] or any(record[k]!=manifest[k] for k in ('romSha256','controlMemorySha256')):raise ValueError('Mixed next instruction controls')
    from air_startup_reference import analyze as startup_epoch
    epoch=startup_epoch(startup)['epoch']
    def rows(path):
        with path.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
    base=str(args.native_base);instruction_base=base+{1:'',2:'.third',3:'.fifth'}[after_retry];native={}
    for part in PARTS:
        keys=('services','irqs','polls','summary')+(('writes',) if part!='map' else ())
        native[part]={'points':rows(Path(instruction_base+'.next-'+part+'.csv'))}
        for key in keys:native[part][key]=rows(Path(instruction_base+'.next-'+part+'.'+('interrupts' if key=='irqs' else key)+'.csv'))
    entry=rows(Path(base+{1:'.following-incoming.summary.csv',2:'.next-incoming.summary.csv',3:'.fourth.next-incoming.summary.csv'}[after_retry]));prior=rows(Path(base+{1:'.instruction-exit.csv',2:'.next-exit.csv',3:'.fourth.next-exit.csv'}[after_retry]))[-1:]
    differences=compare_chain(result,records,native,entry,prior,epoch)
    report=dict(comparedBoundaries=sum(len(v['points']) for v in native.values()),comparedServices=sum(len(v['services']) for v in native.values()),comparedInterrupts=sum(len(v['irqs']) for v in native.values()),comparedPolls=sum(len(v['polls']) for v in native.values()),comparedWrites=sum(len(v.get('writes',[])) for v in native.values()),mapSelections=64,differences=len(differences),firstDifference=differences[:1],productionSchedulerAccepted=False)
    report.update(afterRetry=after_retry,lives=result['points'][-1]['lives'])
    write_json(Path(base+{1:'.next-instruction.comparison.json',2:'.third-instruction.comparison.json',3:'.fifth-instruction.comparison.json'}[after_retry]),report);print(json.dumps(report,indent=2))
    if differences:raise ValueError('Native next instruction continuation differs')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('native_base',type=Path)
    for key in ('capture','out','startup'):parser.add_argument('--'+key,type=Path,required=True)
    parser.add_argument('--result-out',type=Path)
    parser.add_argument('--after-retry',type=int,choices=(1,2,3),default=1)
    compare(parser.parse_args())
