"""Compare a restarted Air terminal wait's attached audio stop/outgoing fade.

Reference observations are verification targets only; no native replay reads
palette measurements, cycles, actor snapshots or original memory states.
"""
import argparse,csv,json
from pathlib import Path
from air_exit_timing import intervals,display_services
from air_timing import vblank_work
from air_reference import write_json
from reference_backend import require_capture_reference


def analyze(data,gameplay):
    from air_following_scene_reference import analyze as scenes
    scenes(gameplay)
    if gameplay.get('terminalWait') is not True:raise ValueError('Outgoing fade lacks terminal gameplay ownership')
    points=data['points'];irqs=data['interrupts'];phases=intervals(data);services=display_services(data)
    terminal=gameplay['points'][-1]
    if points[0]['cycles']!=terminal['cycles'] or points[0]['tick']!=terminal['tick'] or points[0]['musicEnabled']!=1 or points[0]['ready']:
        raise ValueError('Outgoing fade is detached from terminal update/wait')
    preceding=gameplay['precedingDisplays']+sum(r['kind']=='vblank' for r in gameplay['interrupts'])
    if data.get('precedingDisplays')!=preceding:raise ValueError('Outgoing display numbering is detached')
    waits=[(p,q) for p,q in zip(points,points[1:]) if p['name']=='wait']
    if len(irqs)!=64 or len(services)!=32:raise ValueError('Incomplete outgoing vector coverage')
    previous=terminal['held'];counts={'stat':0,'vblank':0};last=points[0]['cycles']
    for r in irqs:
        if r['kind'] not in counts or not last<r['start']<r['end']<points[-1]['cycles'] or r['ready'] or r['selector']!=4 or r['display']!=4 or r['returnAddress']!=0x261d:
            raise ValueError('Unowned outgoing vector')
        last=r['end']+16;counts[r['kind']]+=1
        if not any(p['cycles']<=r['start']-20<r['end']+16<=q['cycles'] for p,q in waits):raise ValueError('Outgoing interrupt outside counter wait')
        if r['kind']=='stat':
            if r['end']-r['start']!=288:raise ValueError('Unknown outgoing STAT work')
        else:
            if r['tick']!=(terminal['tick']+counts['vblank']-1)&65535 or r['pressed']!=r['held']&~previous or r['held']&15==15:
                raise ValueError('Outgoing input/counter continuity differs')
            if len(r.get('oam',[]))!=160 or any(type(v) is not int or not 0<=v<=255 for v in r['oam']):raise ValueError('Incomplete outgoing sprite publication')
            previous=r['held']
    if counts!={'stat':32,'vblank':32}:raise ValueError('Incomplete outgoing vector pairs')
    for p in points:
        elapsed=sum(r['end']+16<=p['cycles'] for r in services)
        if p['tick']!=(terminal['tick']+elapsed)&65535:raise ValueError('Outgoing phase counter lacks its display')
    return phases,services


def compare_outro(data,gameplay,phases,services,irqs,sprites,summary,entry,epoch):
    from air_clock_compare import compare_sprites
    expected,displays=analyze(data,gameplay)
    if [len(v) for v in (phases,services,irqs,sprites,summary,entry)]!=[74,32,64,1280,1,1]:raise ValueError('Incomplete native outgoing coverage')
    differences=[]
    def check(category,index,wanted,actual):
        delta={k:[v,actual[k]] for k,v in wanted.items() if actual[k]!=v}
        if delta:differences.append(dict(category=category,index=index,fields=delta))
    first=gameplay['points'][-1];end=data['points'][-1];start=entry[0]
    if start['end']!=first['cycles']-epoch or start['tick']!=first['tick'] or start['displays']!=data['precedingDisplays']:
        raise ValueError('Native outgoing entry lacks its terminal wait')
    for i,(wanted,row) in enumerate(zip(expected,phases)):
        if set(row)!={'phase','index','start','end','tickBefore','tickAfter','elapsed','work','bgp','obp0','obp1','musicEnabled'}:raise ValueError('Incomplete native outgoing phase fields')
        check('phase',i,{**{k:wanted[k] for k in row if k not in ('start','end')},'start':data['points'][i]['cycles']-epoch,'end':data['points'][i+1]['cycles']-epoch},row)
    for i,(r,row) in enumerate(zip(displays,services)):
        work=vblank_work(r)
        check('service',i,dict(service=data['precedingDisplays']+i,cycle=r['start']-epoch,tick=r['tick'],display=work['display'],effects=work['effects'],music=work['music'],inputHeld=r['held'],inputPressed=r['pressed']),row)
    counts={'stat':0,'vblank':0}
    for i,(r,row) in enumerate(zip(data['interrupts'],irqs)):
        key='nextStat' if r['kind']=='stat' else 'nextVBlank'
        if r['start']!=start[key]+epoch+20+70224*counts[r['kind']]:raise ValueError('Outgoing deadline is detached from terminal wait')
        counts[r['kind']]+=1
        check('interrupt',i,dict(kind=r['kind'],vectorCycle=r['start']-epoch,owner=2),row)
    normalized=[]
    for i,row in enumerate(sprites):
        if row['service']!=data['precedingDisplays']+i//40 or row['slot']!=i%40:raise ValueError('Reordered outgoing sprite publication')
        normalized.append(dict(row,service=i//40))
    differences.extend(dict(category='spritePublication',**d) for d in compare_sprites(displays,normalized,expected_services=32))
    check('summary',0,dict(end=end['cycles']-epoch,tick=end['tick'],countdown=start['countdown'],displays=start['displays']+32,stats=start['stats']+32,lcdEpoch=start['lcdEpoch'],nextStat=start['nextStat']+32*70224,nextVBlank=start['nextVBlank']+32*70224),summary[0])
    return differences


def compare(args):
    manifest=json.loads((args.capture/'capture-summary.json').read_text())
    data=json.loads((args.out/'outro.json').read_text());gameplay=json.loads((args.out/'gameplay.json').read_text());startup=json.loads((args.startup/'startup.json').read_text())
    for record in (data,gameplay,startup):
        require_capture_reference(manifest,record)
        if manifest['controlDifferences'] or any(record[k]!=manifest[k] for k in ('romSha256','controlMemorySha256')):raise ValueError('Mixed outgoing controls')
    from air_startup_reference import analyze as startup_epoch
    epoch=startup_epoch(startup)['epoch']
    def rows(path):
        with path.open(encoding='utf-8-sig',newline='') as stream:
            return [{k:v if k in ('phase','kind') else int(v) for k,v in row.items()} for row in csv.DictReader(stream)]
    path=args.native_csv
    values=[rows(path)]+[rows(path.with_suffix('.'+key+'.csv')) for key in ('services','interrupts','sprites','summary')]+[rows(args.entry_summary)]
    differences=compare_outro(data,gameplay,*values,epoch)
    report=dict(comparedPhases=74,comparedServices=32,comparedInterrupts=64,comparedPublishedSpriteSlots=1280,differences=len(differences),firstDifference=differences[:1],productionSchedulerAccepted=False)
    write_json(path.with_suffix('.comparison.json'),report);print(json.dumps(report,indent=2))
    if differences:raise ValueError('Native following outgoing fade differs')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('native_csv',type=Path)
    for key in ('capture','out','startup','entry-summary'):parser.add_argument('--'+key,type=Path,required=True)
    compare(parser.parse_args())
