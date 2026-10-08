"""Independent held-Start/prompt/input/fade/audio-stop instruction exit through 0355."""
import argparse,csv,hashlib,json
from pathlib import Path
from extract import read_rom
from reference_backend import reference_class,require_matching_backend,require_capture_reference
from air_timing import IRQ_PHASES,vblank_work,VBLANK_FIXED,vblank_bookkeeping_work,elapsed_work
from air_reference import write_json

def capture(args):
    folder=args.capture;target=args.out;target.mkdir(parents=True,exist_ok=True)
    manifest=json.loads((folder/'capture-summary.json').read_text());rom=str(args.rom)
    if manifest['controlDifferences'] or hashlib.sha256(read_rom(rom)).hexdigest()!=manifest['romSha256']:raise ValueError('Changed original control')
    Reference,metadata=reference_class('sameboy');require_matching_backend(manifest,metadata)
    p=Reference(rom,window='null',sound_volume=0);active=False;armed=False;complete=False;points=[];irqs=[];opened=None;polls=[];writes=[];buttons=[]
    names={0x032b:'begin',0x0331:'prompt',0x0347:'promptReady',0x0349:'inputCall',0x25da:'inputWait',0x25dd:'inputReady',
     0x034c:'fadeCall',0x034f:'fadeReturned',0x0352:'audioStop',0x0355:'end',0x20b9:'fadePalette',0x20bc:'bgpReady',0x20c7:'fadeWait',0x20ca:'fadeReady'}
    def word(a):return p.memory[a]+256*p.memory[a+1]
    def hook(pc):
     nonlocal active,armed,complete,opened
     if complete:return
     if pc==0x268b and p.memory[0xc098] in (2,10):armed=True
     if pc==0x2436 and (p.memory[0xc098] in (2,10) or armed and p.memory[0xc098]==5):buttons.append(p.memory[0xff8a])
     if pc==0x032b and armed and p.memory[0xc098]==5:active=True
     if not active:return
     now=p._cycles()
     if pc in names:
      points.append(dict(name=names[pc],cycles=now,tick=word(0xc00a),countdown=word(0xc0b7),scroll=p.memory[0xc09c],
       bgp=p.memory[0xff47],obp0=p.memory[0xff48],obp1=p.memory[0xff49],musicEnabled=p.memory[0xffcf],inputHeld=p.memory[0xff8a],inputPressed=p.memory[0xff8b]))
      if pc==0x0355:active=False;complete=True
     elif pc in (0x0040,0x0048):
      if opened:raise ValueError('Nested exit interrupt')
      opened=dict(kind='vblank' if pc==0x0040 else 'stat',start=now,selector=p.memory[0xc099],display=p.memory[0xc098],returnAddress=word(p.register_file.SP),tick=word(0xc00a),countdown=word(0xc0b7),phases={})
     elif pc in IRQ_PHASES and opened and opened['kind']=='vblank':
      name=IRQ_PHASES[pc];opened['phases'][name]=now
      if name=='display':opened.update(held=p.memory[0xff8a],pressed=p.memory[0xff8b])
      if name=='bookkeeping':opened.update(resetEnabled=p.memory[0xc005],resetLatched=p.memory[0xc004])
      if name=='effects':opened['effectRequest']=-1 if p.memory[0xffc6]==255 else p.memory[0xffc6]
      if name=='music':opened['musicEnabled']=p.memory[0xffcf]
     elif pc in (0x2484,0x2555) and opened:
      opened['end']=now;irqs.append(opened);opened=None
     elif pc==0x2123:polls.append(dict(cycles=now,mode=p.register_file.A&3))
     elif pc==0x2128:writes.append(dict(cycles=now,address=256*p.register_file.D+p.register_file.E,value=p.register_file.A))
    try:
     with (folder/'setup.state').open('rb') as f:p.load_state(f)
     for pc in (*names,*IRQ_PHASES,0x0040,0x0048,0x2484,0x2555,0x2123,0x2128,0x268b):p.hook_register(0,pc,hook,pc)
     for e in json.loads((folder/'events.json').read_text()):
      if e[0]=='tick':p.tick(e[1],e[2])
      else:getattr(p,'button_'+e[0])(e[1])
     digest=hashlib.sha256(bytes(p.memory[0x8000:0x10000])).hexdigest()
    finally:p.stop(save=False)
    if not complete or opened or digest!=manifest['controlMemorySha256']:raise ValueError('Incomplete exit or changed original control')
    data=dict(version=1,reference=metadata,romSha256=manifest['romSha256'],controlMemorySha256=digest,
     precedingDisplays=len(buttons)-sum(r['kind']=='vblank' for r in irqs),points=points,interrupts=irqs,polls=polls,writes=writes,productionSchedulerAccepted=False)
    analyze(data);write_json(target/'exit.json',data);(target/'buttons.txt').write_text(''.join(str(b)+'\n' for b in buttons))
    print(json.dumps(dict(boundaries=len(points),interrupts=len(irqs),polls=len(polls),writes=len(writes),first=points[0],last=points[-1],controlDifferences=0,productionSchedulerAccepted=False),indent=2))

FIELDS=('tick','countdown','scroll','bgp','obp0','obp1','musicEnabled','inputHeld','inputPressed')
def analyze(data):
    points=data.get('points',[]);irqs=data.get('interrupts',[]);services=[]
    if data.get('version')!=1 or not isinstance(data.get('precedingDisplays'),int) or data['precedingDisplays']<0 or len(points)<85:raise ValueError('Incomplete exit boundaries')
    prefix=['begin']
    if not points[0]['inputHeld']&8:
        prefix+=['prompt','promptReady','inputCall']
        i=4
        while i<len(points) and points[i]['name']=='inputWait':prefix+=['inputWait','inputReady'];i+=2
        if i==4:raise ValueError('Missing fresh-Start wait')
    expected=prefix+['fadeCall']+(['fadePalette','bgpReady']+['fadeWait','fadeReady']*4)*8+['fadeReturned','audioStop','end']
    if [p['name'] for p in points]!=expected or any(b['cycles']<=a['cycles'] for a,b in zip(points,points[1:])):raise ValueError('Incomplete/reordered exit phases')
    ready=[p for p in points if p['name']=='inputReady']
    if ready and (not ready[-1]['inputPressed']&8 or any(p['inputPressed']&8 for p in ready[:-1])):raise ValueError('Unowned fresh-Start exit')
    first=points[0];previous=first['inputHeld'];last=first['cycles']
    for i,p in enumerate(points):
        if p['countdown']!=first['countdown'] or p['scroll']!=first['scroll'] or bool(p['musicEnabled'])!=(i<len(points)-1) or (p['inputHeld']&15)==15 or p['inputPressed']&~p['inputHeld']:raise ValueError('Unowned exit mutation/reset')
    if any(points[-1][k] for k in ('bgp','obp0','obp1','musicEnabled')):raise ValueError('Incomplete exit palette/audio reset')
    for r in irqs:
        if not last<=r['start']<r['end'] or r['end']+16>points[-1]['cycles'] or r['selector']!=5:raise ValueError('Incomplete/unowned exit IRQ')
        last=r['end']+16
        if r['kind']=='stat':
            if r['end']-r['start']!=288:raise ValueError('Unowned exit STAT work')
        elif r['kind']=='vblank':
            w=vblank_work(r);wanted={**VBLANK_FIXED,'display':144,'bookkeeping':vblank_bookkeeping_work(r['resetEnabled'],r['held'],r['resetLatched']),'effects':64}
            if r['display']!=5 or r['countdown']!=first['countdown'] or any(w[k]!=v for k,v in wanted.items()) or w['music']<60 or r['effectRequest']!=-1 or not r['musicEnabled'] or r['pressed']!=r['held']&~previous or (r['held']&15)==15:raise ValueError('Unowned exit display/input/audio')
            previous=r['held'];services.append(r)
        else:raise ValueError('Unknown exit interrupt')
    if (points[-1]['tick']-first['tick'])%65536!=len(services):raise ValueError('Missing exit counter services')
    for i,p in enumerate(points):
        if p['name'] in ('fadeWait','inputWait','fadeReturned'):
            if sum(p['cycles']<r['start']<points[i+1]['cycles'] for r in services)!=1:raise ValueError('Incomplete exit counter wait')
    stop=points[-2]
    if points[-1]['cycles']-stop['cycles']!=12384 or any(r['start']>stop['cycles'] for r in irqs):raise ValueError('Unowned interrupted audio reset')
    polls=data.get('polls',[]);writes=data.get('writes',[])
    if len(writes)!=(20 if len(prefix)>1 else 0):raise ValueError('Incomplete prompt glyphs')
    for rows in (polls,writes):
        if any(not first['cycles']<r['cycles']<points[-1]['cycles'] for r in rows) or any(b['cycles']<=a['cycles'] for a,b in zip(rows,rows[1:])):raise ValueError('Reordered exit access')
    if any(p['mode'] not in (0,1,2,3) for p in polls) or any(not 0x9800<=p['address']<0x9c00 or not 0<=p['value']<128 for p in writes):raise ValueError('Invalid exit access')
    return services

def compare_exit(data,points,services,irqs,polls,writes,summary,epoch):
    expected_services=analyze(data);differences=[]
    if [len(r) for r in (points,services,irqs,polls,writes,summary)]!=[len(data['points']),len(expected_services),len(data['interrupts']),len(data['polls']),len(data['writes']),1]:raise ValueError('Incomplete native exit coverage')
    def check(category,index,expected,row):
        delta={k:[v,int(row[k])] for k,v in expected.items() if int(row[k])!=v}
        if delta:differences.append(dict(category=category,index=index,fields=delta))
    for i,(p,q) in enumerate(zip(data['points'],points)):
        if q['boundary']!=p['name']:raise ValueError('Reordered native exit')
        check('boundary',i,dict(cycle=p['cycles']-epoch,**{k:p[k] for k in FIELDS}),q)
    for i,(p,q) in enumerate(zip(expected_services,services)):
        w=vblank_work(p);check('service',i,dict(service=data['precedingDisplays']+i,cycle=p['start']-epoch,tick=p['tick'],countdown=p['countdown'],display=w['display'],effects=w['effects'],music=w['music'],inputHeld=p['held'],inputPressed=p['pressed']),q)
    for i,(p,q) in enumerate(zip(data['interrupts'],irqs)):
        if q['kind']!=p['kind'] or int(q['owner'])!=(2 if p['returnAddress']==0x261d else 1):raise ValueError('Unowned exit IRQ')
        check('interrupt',i,dict(vectorCycle=p['start']-epoch),q)
    for key,rows,fields in [('polls',polls,('mode',)),('writes',writes,('address','value'))]:
        for i,(p,q) in enumerate(zip(data[key],rows)):check(key,i,dict(cycle=p['cycles']-epoch,**{k:p[k] for k in fields}),q)
    end=data['points'][-1];check('summary',0,dict(end=end['cycles']-epoch,tick=end['tick'],countdown=end['countdown']),summary[0])
    if int(summary[0]['displays'])!=int(services[-1]['service'])+1:raise ValueError('Exit terminal service differs')
    return differences

def compare(args):
    manifest=json.loads((args.capture/'capture-summary.json').read_text());data=json.loads((args.out/'exit.json').read_text());startup=json.loads((args.startup/'startup.json').read_text())
    for recording in (data,startup):
        require_capture_reference(manifest,recording)
        if any(recording[k]!=manifest[k] for k in ('romSha256','controlMemorySha256')):raise ValueError('Mixed instruction exit controls')
    if manifest['controlDifferences']:raise ValueError('Changed original control')
    from air_startup_reference import analyze as startup_epoch
    epoch=startup_epoch(startup)['epoch']
    def rows(path):
        with path.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
    path=args.native_csv;values=[rows(path)]+[rows(path.with_suffix('.'+key+'.csv')) for key in ('services','interrupts','polls','writes','summary')]
    differences=compare_exit(data,*values,epoch)
    report=dict(comparedBoundaries=len(values[0]),comparedServices=len(values[1]),comparedInterrupts=len(values[2]),comparedPolls=len(values[3]),comparedWrites=len(values[4]),differences=len(differences),firstDifference=differences[:1],productionSchedulerAccepted=False,
        evidenceLimit='Held-Start/prompt/fresh-input wait, eight palette segments, 32 fade waits, final wait and quiet audio reset through 0355. Excludes interrupted reset, pixels/PCM/hardware, following LCD/gameplay entry and production scheduling.')
    write_json(path.with_suffix('.comparison.json'),report);print(json.dumps(report,indent=2))
    if differences:raise ValueError('Native instruction exit differs')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='mode',required=True)
    record=sub.add_parser('capture');record.add_argument('rom',type=Path)
    verify=sub.add_parser('compare');verify.add_argument('native_csv',type=Path);verify.add_argument('--startup',type=Path,required=True)
    for command in (record,verify):command.add_argument('--capture',type=Path,required=True);command.add_argument('--out',type=Path,required=True)
    args=parser.parse_args();(capture if args.mode=='capture' else compare)(args)
