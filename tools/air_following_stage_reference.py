"""Independent LCD-off following Air/Ski stage initialization through 039c."""
import argparse,csv,hashlib,json
from pathlib import Path
from extract import read_rom
from reference_backend import reference_class,require_matching_backend,require_capture_reference
from air_reference import write_json
from air_following_setup_reference import FIELDS
from air_following_scope import FollowingAirCaptureScope

COMMON={0x0367:'begin',0x036e:'stageReady',0x039c:'registersReady'}
AIR={0x0b31:'stageEntry',0x0b49:'rootsReady',0x0b6d:'terrainReady',0x0b96:'mapReady',0x0ba0:'placementsReady',
     0x0ba5:'offsetsReady',0x0bb8:'fixedTilesReady',0x0bf2:'scalarsReady',0x0c04:'playerReady',
     0x0c07:'spritesReady',0x0c17:'helperReady',0x0c1a:'mapPrepared'}
SKI={0x0dc9:'stageEntry',0x0de1:'rootsReady',0x0e15:'terrainReady',0x0e3e:'mapReady',0x0e48:'placementsReady',
     0x0e4d:'offsetsReady',0x0e80:'scalarsReady',0x0e91:'playerReady',0x0e94:'spritesReady',0x0e97:'mapPrepared'}

def capture(args):
    manifest=json.loads((args.capture/'capture-summary.json').read_text())
    if manifest['controlDifferences'] or hashlib.sha256(read_rom(args.rom)).hexdigest()!=manifest['romSha256']:raise ValueError('Changed original control')
    Reference,metadata=reference_class('sameboy');require_matching_backend(manifest,metadata)
    player=Reference(str(args.rom),window='null',sound_volume=0);active=False;armed=False;complete=False;points=[];interrupts=[]
    scope=FollowingAirCaptureScope(getattr(args,'next_retry',False))
    def word(a):return player.memory[a]+256*player.memory[a+1]
    def hook(pc):
        nonlocal active,armed,complete
        if complete:return
        scope.observe(pc,player.memory[0xc098])
        if pc==0x268b and player.memory[0xc098] in (2,10):armed=True
        if pc==0x0367 and scope.ready and armed:active=True
        if not active:return
        if pc in (0x0040,0x0048):interrupts.append(dict(cycles=player._cycles(),kind='vblank' if pc==0x0040 else 'stat'));return
        selected=player.memory[0xc082];stage=player.memory[0xc088+8*selected]
        names={**COMMON,**(AIR if stage==1 else SKI)}
        if pc not in names:return
        points.append(dict(name=names[pc],cycles=player._cycles(),tick=word(0xc00a),countdown=word(0xc0b7),player=selected,stage=stage,
            difficulty=player.memory[0xc089+8*selected],lives=player.memory[0xc08a+8*selected],display=player.memory[0xc098],stat=player.memory[0xc099],
            lcdc=player.memory[0xff40],lyc=player.memory[0xff45],pendingRequests=player.memory[0xff0f]&3,interruptEnable=player.memory[0xffff]&3,
            cameraX=word(0xff92),cameraY=word(0xff94),mapScratch=word(0xc00c),ready=player.memory[0xffae],musicEnabled=player.memory[0xffcf],reverse=int(bool(player.memory[0xff90]))))
        if pc==0x039c:active=False;complete=True
    try:
        with (args.capture/'setup.state').open('rb') as stream:player.load_state(stream)
        for pc in {*COMMON,*AIR,*SKI,0x268b,0x0040,0x0048,0x03d8}:player.hook_register(0,pc,hook,pc)
        for event in json.loads((args.capture/'events.json').read_text()):
            if event[0]=='tick':player.tick(event[1],event[2])
            elif event[0] in ('press','release'):getattr(player,'button_'+event[0])(event[1])
            else:raise ValueError('Unknown original control event')
        digest=hashlib.sha256(bytes(player.memory[0x8000:0x10000])).hexdigest()
    finally:player.stop(save=False)
    if not complete or digest!=manifest['controlMemorySha256']:raise ValueError('Incomplete following stage or changed original control')
    data=dict(version=1,reference=metadata,romSha256=manifest['romSha256'],controlMemorySha256=digest,points=points,interrupts=interrupts,productionSchedulerAccepted=False)
    if scope.following:data['nextRetry']=True
    analyze(data);args.out.mkdir(parents=True,exist_ok=True);write_json(args.out/'stage.json',data)
    print(json.dumps(dict(boundaries=len(points),interrupts=len(interrupts),controlDifferences=0),indent=2))

def analyze(data):
    points=data.get('points',[])
    if data.get('version')!=1 or not points or points[0]['stage'] not in (1,2):raise ValueError('Invalid following stage recording')
    first=points[0];air=first['stage']==1
    expected=['begin',*(AIR.values() if air else SKI.values()),'stageReady','registersReady']
    if [p['name'] for p in points]!=expected or any(b['cycles']<=a['cycles'] for a,b in zip(points,points[1:])):raise ValueError('Incomplete/reordered following stage')
    if data.get('interrupts')!=[]:raise ValueError('Unexpected masked stage service')
    if data.get('nextRetry') and any('reverse' not in p for p in points):raise ValueError('Missing next-retry allocation selector')
    if 'reverse' in points[-1] and points[-1]['reverse']!=0:raise ValueError('0387 did not reset sprite allocation')
    scalar=expected.index('scalarsReady');sprite=expected.index('spritesReady');song=expected.index('stageReady')
    for i,p in enumerate(points):
        if any(p[k]!=first[k] for k in ('tick','countdown','player','stage','difficulty','lives')) or p['pendingRequests']!=3 or p['interruptEnable']!=3:
            raise ValueError('Unowned stage campaign/service mutation')
        if p['display']!=(5 if i<scalar else 4 if air else 6) or p['stat']!=(4 if i==len(points)-1 else 5) or p['lyc']!=(135 if i==len(points)-1 else 95):raise ValueError('Unowned following callback transition')
        if p['lcdc']!=(0x67 if i==len(points)-1 else 0x51) or bool(p['musicEnabled'])!=(i>=song) or bool(p['ready'])!=(i>=sprite):raise ValueError('Unowned following LCD/resource/music state')
    if points[-2]['cycles']-points[-3]['cycles']!=14052 or points[-1]['cycles']-points[-2]['cycles']!=240:raise ValueError('Unowned stage music/register work')
    return dict(boundaries=len(points),stage=first['stage'])

def compare_stage(data,points,summary,prefix_summary,epoch):
    analyze(data);expected=data['points'][1:] # begin is the separately compared 0367 endpoint.
    if len(points)!=len(expected) or len(summary)!=1 or len(prefix_summary)!=1:raise ValueError('Incomplete native following-stage coverage')
    differences=[];names=[p['name'] for p in expected];scalar=names.index('scalarsReady');mapped=names.index('mapPrepared');sprite=names.index('spritesReady')
    def check(category,index,wanted,actual):
        delta={k:[v,int(actual[k])] for k,v in wanted.items() if int(actual[k])!=v}
        if delta:differences.append(dict(category=category,index=index,fields=delta))
    for i,(p,q) in enumerate(zip(expected,points)):
        if q['boundary']!=p['name']:raise ValueError('Reordered native stage phases')
        fields=list(FIELDS)+['musicEnabled']
        if i>=scalar:fields+=['cameraX','cameraY']
        if i>=mapped:fields+=['mapScratch']
        if i>=sprite:fields+=['ready']
        check('boundary',i,dict(cycle=p['cycles']-epoch,**{k:p[k] for k in fields}),q)
    end=expected[-1];check('summary',0,dict(end=end['cycles']-epoch,tick=end['tick'],countdown=end['countdown']),summary[0])
    if int(prefix_summary[0]['end'])!=data['points'][0]['cycles']-epoch or any(int(summary[0][k])!=int(prefix_summary[0][k]) for k in ('tick','countdown','displays','stats')):
        raise ValueError('Native stage is not attached to its masked prefix')
    return differences

def compare(args):
    manifest=json.loads((args.capture/'capture-summary.json').read_text());data=json.loads((args.out/'stage.json').read_text());startup=json.loads((args.startup/'startup.json').read_text())
    for recording in (data,startup):
        require_capture_reference(manifest,recording)
        if any(recording[k]!=manifest[k] for k in ('romSha256','controlMemorySha256')):raise ValueError('Mixed following stage controls')
    if manifest['controlDifferences']:raise ValueError('Changed original control')
    from air_startup_reference import analyze as startup_epoch
    epoch=startup_epoch(startup)['epoch']
    def rows(path):
        with path.open(encoding='utf-8-sig',newline='') as stream:return list(csv.DictReader(stream))
    points=rows(args.native_csv);summary=rows(args.native_csv.with_suffix('.summary.csv'));prefix=rows(args.prefix_summary)
    differences=compare_stage(data,points,summary,prefix,epoch)
    report=dict(comparedBoundaries=len(points),comparedInterrupts=0,differences=len(differences),firstDifference=differences[:1],productionSchedulerAccepted=False,
        evidenceLimit='0367..039c masked Air/Ski setup source work, selected camera/map scratch after overwrite, callbacks, resource readiness and quiet song startup. Excludes untouched inherited scratch/camera low bytes, copied buffer contents/actors, Ski offscreen RAM-template contents, subsequent resources/HUD/LCD restart, pixels/PCM and production scheduling.')
    write_json(args.native_csv.with_suffix('.comparison.json'),report);print(json.dumps(report,indent=2))
    if differences:raise ValueError('Native following-stage setup differs')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='mode',required=True)
    record=sub.add_parser('capture');record.add_argument('rom',type=Path);record.add_argument('--next-retry',action='store_true')
    verify=sub.add_parser('compare');verify.add_argument('native_csv',type=Path);verify.add_argument('--startup',type=Path,required=True);verify.add_argument('--prefix-summary',type=Path,required=True)
    for command in (record,verify):command.add_argument('--capture',type=Path,required=True);command.add_argument('--out',type=Path,required=True)
    args=parser.parse_args();(capture if args.mode=='capture' else compare)(args)
