"""Bounded following Air quiet updates; original observations never drive native work."""
import argparse,csv,json
from pathlib import Path
from air_following_gameplay_reference import analyze as analyze_first,ORDER,FIELDS
from extract_air import HANDLERS
from air_timing import vblank_work,VBLANK_FIXED,vblank_bookkeeping_work
from air_reference import write_json
from reference_backend import require_capture_reference

def analyze(data,resources=False):
    n=data.get('updates',0);points=data.get('points',[]);irqs=data.get('interrupts',[])
    if data.get('version')!=1 or not isinstance(n,int) or n<2 or len(points)!=10*n or len(irqs)!=2*n or data.get('precedingDisplays',-1)<0:raise ValueError('Incomplete following quiet extent')
    first=dict(data,updates=1,points=points[:10],interrupts=irqs[:2]);analyze_first(first)
    for update in range(n):
        block=points[10*update:10*(update+1)];pair=irqs[2*update:2*(update+1)]
        if [p['name'] for p in block]!=ORDER or any(b['cycles']<=a['cycles'] for a,b in zip(block,block[1:])):raise ValueError('Incomplete/reordered following quiet boundaries')
        if update and dict(block[0],name='end')!=points[10*update-1]:raise ValueError('Detached following quiet update')
        if block[1]['cycles']-block[0]['cycles']!=96 or block[8]['cycles']-block[7]['cycles']!=32:raise ValueError('Unknown following quiet prefix/back-edge')
        for i,p in enumerate(block):
            if p['ready'] or p['display']!=4 or p['lcdc']!=0xe7 or (not resources and (p['transfer'] or p['remaining'])) or not -1<=p['effect']<26 or p['held']&15==15 or p['pressed']&~p['held'] or p['pressed']&8 and not(update==0 and i<9 and data.get('entryPauseConsumed') is True):raise ValueError('Unowned following quiet state/input: '+str(dict(update=update,boundary=p['name'],**{k:p[k] for k in ('ready','display','lcdc','transfer','remaining','effect','held','pressed')})))
            if p['tick']!=(block[0]['tick']+(i==9))&65535 or len(p['entities'])!=16:raise ValueError('Incomplete following quiet counter/actors')
            if not 0<=p['secondTicks']<60 or not 0<=p['seconds']<=99:raise ValueError('Invalid following quiet timer')
            if any(e['frame']!=255 and(e['handler'] not in HANDLERS or len(e['params'])!=7) for e in p['entities']):raise ValueError('Unknown following quiet actor')
        if [r['kind'] for r in pair]!=['stat','vblank']:raise ValueError('Reordered following quiet vectors')
        for r in pair:
            if not block[8]['cycles']<r['start']<r['end']<block[-1]['cycles'] or r['selector']!=4 or r['display']!=4 or r['returnAddress']!=0x261d or r['ready']!=1:raise ValueError('Following quiet body was interrupted')
        if pair[0]['end']-pair[0]['start']!=288 or pair[0]['end']+16>=pair[1]['start']:raise ValueError('Unowned following quiet STAT work')
        r=pair[1];work=vblank_work(r)
        expected={**VBLANK_FIXED,'bookkeeping':vblank_bookkeeping_work(r['resetEnabled'],r['held'],r['resetLatched'])}
        if r['tick']!=block[0]['tick'] or r['effectRequest']!=block[8]['effect'] or block[-1]['effect']!=-1 or work['effects']<64 or not r['musicEnabled'] or work['music']<60 or any(work[k]!=v for k,v in expected.items()) or r['pressed']!=r['held']&~block[0]['held']:raise ValueError('Unknown following quiet display/input/audio')
        if block[-1]['cycles']!=r['end']+16+56+48:raise ValueError('Unknown following quiet input gate')
    return [irqs[2*i+1] for i in range(n)]

def compare_quiet(data,points,entities,services,irqs,summary,entry,epoch,resources=False,scene_analysis=None):
    expected=scene_analysis(data) if scene_analysis else analyze(data,resources=resources);n=data['updates']
    nv=len(expected);ns=len(data['interrupts'])-nv
    if [len(rows) for rows in (points,entities,services,irqs,summary,entry)]!=[10*n,160*n,nv,len(data['interrupts']),1,1]:raise ValueError('Incomplete native following quiet coverage')
    differences=[];occupied=0
    def check(category,index,wanted,actual):
        fields={k:[v,int(actual[k])] for k,v in wanted.items() if int(actual[k])!=v}
        if fields:differences.append(dict(category=category,index=index,fields=fields))
    for i,(p,q) in enumerate(zip(data['points'],points)):
        if q['boundary']!=p['name']:raise ValueError('Reordered native following quiet boundary')
        check('boundary',i,dict(cycle=p['cycles']-epoch,**{k:p[k] for k in FIELDS}),q)
        for slot,e in enumerate(p['entities']):
            native=entities[16*i+slot]
            if native['boundary']!=p['name'] or int(native['slot'])!=slot:raise ValueError('Reordered native following quiet actors')
            values=dict(alive=int(e['frame']!=255),frame=e['frame'])
            if e['frame']!=255:
                occupied+=1;values.update(flags=e['flags'],handler=HANDLERS[e['handler']],x=e['x'],y=e['y'],done=int(bool(e['state']&128)),waiting=int(bool(e['state']&64)),delay=e['delay'],period=e['period'],**{f'param{j}':v for j,v in enumerate(e['params'])})
            check('actor',16*i+slot,values,native)
    for i,(p,q) in enumerate(zip(expected,services)):
        work=vblank_work(p);check('service',i,dict(service=data['precedingDisplays']+i,cycle=p['start']-epoch,tick=p['tick'],display=work['display'],effects=work['effects'],music=work['music'],inputHeld=p['held'],inputPressed=p['pressed']),q)
    vectorCounts={'stat':0,'vblank':0}
    for i,(p,q) in enumerate(zip(data['interrupts'],irqs)):
        owner=2 if not scene_analysis or p['returnAddress']==0x261d else 1
        if q['kind']!=p['kind'] or int(q['owner'])!=owner:raise ValueError('Unknown native following quiet vector owner')
        check('interrupt',i,dict(vectorCycle=p['start']-epoch),q)
        key='nextStat' if p['kind']=='stat' else 'nextVBlank'
        lag=p['start']-(int(entry[0][key])+epoch+20+vectorCounts[p['kind']]*70224)
        if (lag!=0 if not scene_analysis or owner==2 else not 0<=lag<=20 or lag%4):raise ValueError('Detached following quiet deadline')
        vectorCounts[p['kind']]+=1
    first=data['points'][0];end=data['points'][-1]
    if any(int(entry[0][k])!=v for k,v in dict(end=first['cycles']-epoch,tick=first['tick'],randomState=first['random'],displays=data['precedingDisplays'],entryPauseComplete=int(data.get('entryPauseConsumed',False))).items()):raise ValueError('Detached native following quiet entry')
    check('summary',0,dict(end=end['cycles']-epoch,tick=end['tick'],countdown=int(entry[0]['countdown']),displays=int(entry[0]['displays'])+nv,stats=int(entry[0]['stats'])+ns,lcdEpoch=int(entry[0]['lcdEpoch']),nextStat=int(entry[0]['nextStat'])+ns*70224,nextVBlank=int(entry[0]['nextVBlank'])+nv*70224),summary[0])
    return differences,occupied

def compare(args):
    manifest=json.loads((args.capture/'capture-summary.json').read_text());data=json.loads((args.out/'gameplay.json').read_text());startup=json.loads((args.startup/'startup.json').read_text())
    for record in(data,startup):
        require_capture_reference(manifest,record)
        if any(record[k]!=manifest[k] for k in('romSha256','controlMemorySha256')):raise ValueError('Mixed following quiet controls')
    if manifest['controlDifferences']:raise ValueError('Changed following quiet control')
    from air_startup_reference import analyze as startup_epoch
    epoch=startup_epoch(startup)['epoch']
    def rows(path):
        with path.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
    path=args.native_csv;values=[rows(path)]+[rows(path.with_suffix('.'+key+'.csv')) for key in('entities','services','interrupts','summary')]+[rows(args.entry_summary)]
    differences,occupied=compare_quiet(data,*values,epoch)
    report=dict(comparedUpdates=data['updates'],comparedBoundaries=len(values[0]),comparedActorSlots=len(values[1]),comparedOccupiedActors=occupied,comparedServices=len(values[2]),comparedInterrupts=len(values[3]),differences=len(differences),firstDifference=differences[:1],productionSchedulerAccepted=False)
    write_json(path.with_suffix('.comparison.json'),report);print(json.dumps(report,indent=2))
    if differences:raise ValueError('Native following quiet gameplay differs')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('native_csv',type=Path)
    for key in('capture','out','startup','entry-summary'):parser.add_argument('--'+key,type=Path,required=True)
    compare(parser.parse_args())
