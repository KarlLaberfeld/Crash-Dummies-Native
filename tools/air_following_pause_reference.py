"""Complete following Air entry pause; original recordings remain local."""
import argparse,csv,json
from pathlib import Path
from air_following_entry_reference import capture as capture_entry,POINTS,FIELDS
from air_timing import vblank_work,VBLANK_FIXED,vblank_bookkeeping_work
from air_pause_compare import compare_bus,compare_graphics,compare_intervals
from air_reference import write_json
from reference_backend import require_capture_reference

def analyze_paused_entry(data):
    points=data.get('points',[]);irqs=data.get('interrupts',[]);names=list(POINTS.values());names.insert(-1,'pauseEntry')
    if data.get('version')!=1 or [p['name'] for p in points]!=names or any(b['cycles']<=a['cycles'] for a,b in zip(points,points[1:])):raise ValueError('Incomplete/reordered paused entry')
    if len(irqs)<6 or len(irqs)%2 or [r['kind'] for r in irqs]!=['vblank','stat','stat','vblank']+['stat','vblank']*((len(irqs)-4)//2):raise ValueError('Incomplete following pause vectors')
    first=points[0];previous=first['inputHeld'];services=[];last=first['cycles'];paused=0
    if first['randomState'] or data.get('precedingDisplays',-1)<0:raise ValueError('Missing following seed reset/service attachment')
    for i,p in enumerate(points):
        if any(p[k]!=first[k] for k in ('countdown','display','stat','lyc','cameraX','cameraY','mapScratch','musicEnabled')) or p['stat']!=4 or p['display']!=4 or p['lyc']!=135 or not p['musicEnabled']:raise ValueError('Unowned following paused-entry state')
        if p['ready']!=(1 if i<11 else 0) or p['pendingRequests']!=(3 if i<9 else 0) or p['inputPressed']&~p['inputHeld'] or p['inputHeld']&15==15:raise ValueError('Unowned following pause ready/input gate')
        if i and p['randomState']!=(first['tick']&255)<<8:raise ValueError('Changed paused-entry native scene seed')
        lcd=0x67 if i<7 else 0xe5 if i in (9,10) else 0xe7
        if p['lcdc']!=lcd:raise ValueError(f"Unowned following pause LCD objects at {p['name']}: {p['lcdc']:02x} vs {lcd:02x}")
    if not points[11]['inputPressed']&8 or points[-1]['hudCursor']!=2 or points[-1]['fadeRemaining']!=7:raise ValueError('Missing first-entry pause or changed paused HUD/fade')
    epoch=points[7]['cycles']-4
    if irqs[0]['start']!=points[8]['cycles']+32 or irqs[1]['start']!=irqs[0]['end']+36:raise ValueError('Lost following pending priority')
    for i,r in enumerate(irqs):
        if not last<=r['start']<r['end'] or r['end']+16>points[-1]['cycles'] or r['selector']!=4:raise ValueError('Unordered following paused-entry vectors')
        if i>=2:
            frame=(i-2)//2;line=135 if r['kind']=='stat' else 144
            if r['start']!=epoch+frame*70224+line*456+20 or r['returnAddress']!=0x261d:raise ValueError('Unowned following pause deadline/acceptance')
        elif r['returnAddress']!=0x03c9:raise ValueError('Unowned following pending return')
        last=r['end']+16
        if r['kind']=='stat':
            if r['end']-r['start']!=288:raise ValueError('Unowned following paused STAT work')
        else:
            is_paused=i>=4;work=vblank_work(r);wanted={**VBLANK_FIXED,'display':160 if is_paused else 1508 if r['tick']&1 else 1676,'bookkeeping':vblank_bookkeeping_work(r['resetEnabled'],r['held'],r['resetLatched']),'effects':64}
            if is_paused:wanted['music']=60
            if r['display']!=(1 if is_paused else 4) or r['ready']!=(0 if is_paused else 1) or bool(r['musicEnabled'])==is_paused or r['effectRequest']!=-1 or r['pressed']!=r['held']&~previous or any(work[k]!=v for k,v in wanted.items()) or work['music']<60:raise ValueError('Unowned following paused display/input/audio')
            if r['tick']!=(first['tick']+len(services))&65535:raise ValueError('Following pause counter did not continue')
            paused+=is_paused;previous=r['held'];services.append(r)
    if points[11]['cycles']!=irqs[3]['end']+16+56+60 or points[11]['tick']!=(first['tick']+2)&65535 or points[-1]['tick']!=(first['tick']+len(services))&65535 or not paused:raise ValueError('Unowned first-entry pause call/terminal')
    return services

def compare_paused_entry(data,points,services,irqs,summary,stage,epoch):
    expected=analyze_paused_entry(data)
    if [len(rows) for rows in (points,services,irqs,summary,stage)]!=[13,len(expected),len(data['interrupts']),1,1]:raise ValueError('Incomplete native following pause coverage')
    differences=[]
    def check(category,index,wanted,actual):
        fields={k:[v,int(actual[k])] for k,v in wanted.items() if int(actual[k])!=v}
        if fields:differences.append(dict(category=category,index=index,fields=fields))
    for i,(p,q) in enumerate(zip(data['points'],points)):
        if q['boundary']!=p['name']:raise ValueError('Reordered native paused-entry boundary')
        check('boundary',i,dict(cycle=p['cycles']-epoch,**{k:p[k] for k in (*FIELDS,'randomState')}),q)
    for i,(p,q) in enumerate(zip(expected,services)):
        work=vblank_work(p);check('service',i,dict(service=data['precedingDisplays']+i,cycle=p['start']-epoch,tick=p['tick'],display=work['display'],effects=work['effects'],music=work['music'],inputHeld=p['held'],inputPressed=p['pressed']),q)
    for i,(p,q) in enumerate(zip(data['interrupts'],irqs)):
        if q['kind']!=p['kind'] or int(q['owner'])!=(3 if i<2 else 2):raise ValueError('Unowned native following pause vector')
        check('interrupt',i,dict(vectorCycle=p['start']-epoch),q)
    end=data['points'][-1];new_epoch=data['points'][7]['cycles']-4-epoch;n=len(expected)
    check('summary',0,dict(end=end['cycles']-epoch,tick=end['tick'],countdown=end['countdown'],displays=int(stage[0]['displays'])+n,stats=int(stage[0]['stats'])+n,lcdEpoch=new_epoch,nextStat=new_epoch+135*456+(n-1)*70224,nextVBlank=new_epoch+144*456+(n-1)*70224,randomState=end['randomState'],hudCursor=2,fadeRemaining=7,entryPauseComplete=1),summary[0])
    if int(stage[0]['end'])!=data['points'][0]['cycles']-epoch or int(stage[0]['displays'])!=data['precedingDisplays']:raise ValueError('Following pause detached from masked stage')
    return differences

def compare(args):
    manifest=json.loads((args.capture/'capture-summary.json').read_text());data=json.loads((args.out/'entry.json').read_text());startup=json.loads((args.startup/'startup.json').read_text());timing=json.loads((args.timing/'pause.json').read_text());lcd=json.loads((args.lcd/'lcd.json').read_text())
    for record in (data,startup,timing,lcd):
        require_capture_reference(manifest,record)
        if any(record[k]!=manifest[k] for k in ('romSha256','controlMemorySha256')):raise ValueError('Mixed following pause controls')
    if manifest['controlDifferences']:raise ValueError('Changed following pause control')
    from air_startup_reference import analyze as startup_epoch
    epoch=startup_epoch(startup)['epoch']
    def rows(path):
        with path.open(encoding='utf-8-sig',newline='') as stream:return list(csv.DictReader(stream))
    path=args.native_csv;values=[rows(path)]+[rows(path.with_suffix('.'+key+'.csv')) for key in ('services','interrupts','summary')]+[rows(args.stage_summary)]
    differences=compare_paused_entry(data,*values,epoch)
    native_prefix=rows(args.prefix)[0]
    prefix={k:int(v) for k,v in native_prefix.items()};prefix['objects']=[dict(x=prefix[f'objectX{i}'],y=prefix[f'objectY{i}'],flags=0) for i in range(40)]
    def numeric(path):return [{k:v if k in ('phase','kind') else int(v) for k,v in r.items()} for r in rows(path)]
    bus=numeric(args.bus);graphics=numeric(args.graphics);phases=numeric(args.phases)
    bus_difference=compare_bus(lcd,prefix,bus);graphics_difference=compare_graphics(lcd,prefix,graphics);phase_difference=compare_intervals(timing['pauses'][0],prefix,phases)
    report=dict(comparedBoundaries=13,comparedServices=len(values[1]),comparedInterrupts=len(values[2]),comparedBusEvents=len(bus),comparedStorageBytes=444,comparedPauseIntervals=len(phases),differences=len(differences),busDifferences=len(bus_difference),storageDifferences=len(graphics_difference),phaseDifferences=len(phase_difference),firstDifference=(differences+bus_difference+graphics_difference+phase_difference)[:1],productionSchedulerAccepted=False)
    write_json(path.with_suffix('.comparison.json'),report);print(json.dumps(report,indent=2))
    if differences or bus_difference or graphics_difference or phase_difference:raise ValueError('Native following entry pause differs')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='mode',required=True)
    record=sub.add_parser('capture');record.add_argument('rom',type=Path)
    verify=sub.add_parser('compare');verify.add_argument('native_csv',type=Path)
    for key in ('startup','stage-summary','timing','lcd','prefix','bus','graphics','phases'):verify.add_argument('--'+key,type=Path,required=True)
    for command in (record,verify):command.add_argument('--capture',type=Path,required=True);command.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    if args.mode=='capture':args.include_entry_pause=True;capture_entry(args)
    else:compare(args)
