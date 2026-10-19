"""Bounded restarted Air resource requests and wait-owned display uploads.

Recordings are comparison targets only. Native playback reads decoded assets
and raw buttons; it never reads this module's observed queue or timing fields.
"""
import argparse,csv,json
from pathlib import Path
from air_following_quiet_reference import analyze as analyze_quiet,compare_quiet
from air_reference import write_json
from reference_backend import require_capture_reference

QUEUE=('transfer','remaining','transferFrame','transferFlags')


def analyze(data):
    if data.get('resourceTransfers') is not True:
        raise ValueError('Resource continuation requires explicit capture scope')
    chunks=data.get('resourceChunks',[])
    if len(chunks)!=12 or any(type(n) is not int or not 0<=n<=255 for n in chunks):
        raise ValueError('Missing decoded resource descriptors')
    if data.get('busyScenes'):
        from air_following_scene_reference import analyze as analyze_scenes
        services=analyze_scenes(data)
    else:services=analyze_quiet(data,resources=True)
    requests=uploads=completions=deferred=0
    for update in range(data['updates']):
        block=data['points'][10*update:10*(update+1)]
        for p in block:
            if any(type(p.get(k)) is not int for k in QUEUE):raise ValueError('Incomplete resource queue snapshot')
            state,remaining,frame,flags=(p[k] for k in QUEUE)
            if state not in (0,1,2) or not 0<=remaining<=255 or (state==1)!=(remaining>0) or not 0<=frame<=255 or not 0<=flags<=255:
                raise ValueError('Invalid resource queue state')
            if state and (frame>=12 or remaining>chunks[frame]):raise ValueError('Resource queue exceeds decoded descriptor')
        begin,actors,prepared,end=block[0],block[2],block[3],block[9]
        if any(any(p[k]!=begin[k] for k in QUEUE) for p in block[1:3]):raise ValueError('Resource queue committed before callback')
        expected={k:begin[k] for k in QUEUE};expected['transfer']=0 if begin['transfer']==2 else begin['transfer']
        old=begin['entities'][0];requested=actors['entities'][0];frame=requested['frame']
        visible=dict(requested)
        if frame<12 and frame!=old['frame']:
            if not expected['transfer']:expected['transfer']=1;replace=True
            else:replace=frame!=expected['transferFrame']
            if replace:
                if not chunks[frame]:raise ValueError('Zero-chunk dynamic request needs separate ownership')
                expected.update(remaining=chunks[frame],transferFrame=frame,transferFlags=requested['flags']);requests+=1
            visible.update(frame=old['frame'],flags=old['flags'])
        if any(prepared[k]!=v for k,v in expected.items()):raise ValueError('Resource callback outcome disagrees with native descriptor semantics')
        if prepared['entities'][0]!=visible or prepared['entities'][1:]!=actors['entities'][1:]:
            raise ValueError('Resource callback changed unrelated actor state or published requested frame early')
        if any(any(p[k]!=prepared[k] for k in QUEUE) for p in block[4:9]):raise ValueError('Resource queue changed outside its completion owner')
        after=dict(expected)
        display_services=[r for r in services if block[0]['cycles']<r['start']<block[-1]['cycles']]
        for r in display_services:
            if after['remaining']:
                # A display during sprite clearing still sees the preceding
                # row gate; map preparation has not committed its new gate.
                map_gate=block[4]['map'] if r['start']<block[5]['cycles'] else block[8]['map']
                if map_gate:deferred+=1
                elif r['ready']:
                    uploads+=1;after['remaining']=max(0,after['remaining']-4)
                    if not after['remaining']:after['transfer']=2;completions+=1
        if any(end[k]!=v for k,v in after.items()):raise ValueError('Display upload did not retain/decrement/complete its resource queue')
        pose=(after['transferFrame'],after['transferFlags']) if expected['remaining'] and not after['remaining'] else (prepared['entities'][0]['frame'],prepared['entities'][0]['flags'])
        if (end['entities'][0]['frame'],end['entities'][0]['flags'])!=pose:raise ValueError('Display resource completion published the wrong player pose')
    if not requests or not uploads or not completions:raise ValueError('Resource capture omits request/upload/completion coverage')
    return dict(requests=requests,uploads=uploads,completions=completions,mapDeferredDisplays=deferred,services=services)


def compare_resources(data,points,entities,services,irqs,summary,entry,epoch):
    extent=analyze(data)
    scene_analysis=None
    if data.get('busyScenes'):
        from air_following_scene_reference import analyze as scene_analysis
    differences,occupied=compare_quiet(data,points,entities,services,irqs,summary,entry,epoch,resources=True,scene_analysis=scene_analysis)
    for index,(p,q) in enumerate(zip(data['points'],points)):
        # Before the first request, these two original queue bytes are unused
        # retained scratch. Once busy, both are part of the owned transfer.
        if p['transfer']:
            values={k:[p[k],int(q[k])] for k in ('transferFrame','transferFlags') if int(q[k])!=p[k]}
            if values:differences.append(dict(category='resource',index=index,fields=values))
    return differences,occupied,extent


def compare(args):
    manifest=json.loads((args.capture/'capture-summary.json').read_text())
    data=json.loads((args.out/'gameplay.json').read_text());startup=json.loads((args.startup/'startup.json').read_text())
    for record in (data,startup):
        require_capture_reference(manifest,record)
        if any(record[k]!=manifest[k] for k in ('romSha256','controlMemorySha256')):raise ValueError('Mixed resource continuation controls')
    if manifest['controlDifferences']:raise ValueError('Changed original resource control')
    from air_startup_reference import analyze as startup_epoch
    epoch=startup_epoch(startup)['epoch']
    def rows(path):
        with path.open(encoding='utf-8-sig',newline='') as stream:return list(csv.DictReader(stream))
    path=args.native_csv
    values=[rows(path)]+[rows(path.with_suffix('.'+key+'.csv')) for key in ('entities','services','interrupts','summary')]+[rows(args.entry_summary)]
    differences,occupied,extent=compare_resources(data,*values,epoch)
    sprite_slots=0
    if data.get('busyScenes'):
        from air_following_scene_reference import compare_publications
        sprites=[{k:int(v) for k,v in row.items()} for row in rows(path.with_suffix('.sprites.csv'))]
        sprite_slots=len(sprites)
        differences.extend(dict(category='spritePublication',**difference) for difference in compare_publications(data,sprites))
    report=dict(comparedUpdates=data['updates'],comparedBoundaries=len(values[0]),comparedActorSlots=len(values[1]),
        comparedOccupiedActors=occupied,comparedServices=len(values[2]),comparedInterrupts=len(values[3]),
        **{k:v for k,v in extent.items() if k!='services'},comparedPublishedSpriteSlots=sprite_slots,differences=len(differences),firstDifference=differences[:1],productionSchedulerAccepted=False)
    write_json(path.with_suffix('.resource-comparison.json'),report);print(json.dumps(report,indent=2))
    if differences:raise ValueError('Native restarted Air resource continuation differs')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('native_csv',type=Path)
    for key in ('capture','out','startup','entry-summary'):parser.add_argument('--'+key,type=Path,required=True)
    compare(parser.parse_args())
