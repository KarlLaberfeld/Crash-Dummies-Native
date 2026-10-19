"""Verify restarted Air result setup/incoming/hold attachment to native exit.

Only comparison: the native diagnostic reads decoded assets and raw inputs,
never this module's original clocks, life counts or memory snapshots.
"""
import argparse,csv,json
from pathlib import Path
from air_reference import write_json
from reference_backend import require_capture_reference
from air_result_prefix_reference import analyze as prefix_scope,compare_prefix
from air_result_transition_reference import analyze as transition_scope,compare_transition


def analyze(prefix,transition,gameplay,outro):
    from air_following_outro_reference import analyze as outgoing_scope
    _,outgoing=outgoing_scope(outro,gameplay)
    prefix_scope(prefix);services=transition_scope(transition)
    if prefix.get('followingResult') is not True or transition.get('followingResult') is not True:
        raise ValueError('Restarted result requires explicit following capture scope')
    first=prefix['points'][0];last=prefix['points'][-1];terminal=gameplay['points'][-1];exit_point=outro['points'][-1]
    if first['cycles']!=exit_point['cycles'] or first['result']!=terminal['result'] or first['result']&6:
        raise ValueError('Result prefix is detached from its non-perfect failure exit')
    state=first.get('state',{});required=('tick','random','player','lives','held','pressed','display','stat','countdown')
    if any(type(state.get(k)) is not int for k in required) or state['player'] not in (0,1) or not 1<state['lives']<=255:
        raise ValueError('Unowned inherited result campaign/input state')
    if state['tick']!=exit_point['tick'] or state['random']!=terminal['random'] or state['held']!=outgoing[-1]['held'] or state['pressed']!=outgoing[-1]['pressed']:
        raise ValueError('Result prefix lost outgoing counter/input/seed ownership')
    for i,p in enumerate(prefix['points']):
        s=p.get('state',{})
        if p['result']!=first['result'] or any(s.get(k)!=state[k] for k in ('tick','random','player','lives','held','pressed')):
            raise ValueError('Masked result setup changed campaign/input/seed state')
        if (s.get('display'),s.get('stat'),s.get('countdown'))!=((4,4,state['countdown']) if i<5 else (10,0,600)):
            raise ValueError('Result setup callback/countdown publication differs')
    incoming=transition['points'][0]
    wanted=dict(cycles=last['cycles'],tick=state['tick'],result=first['result'],countdown=600,player=state['player'],lives=state['lives'],inputHeld=state['held'],inputPressed=state['pressed'])
    if any(incoming.get(k)!=v for k,v in wanted.items()):raise ValueError('Incoming result is detached from common setup')
    consumed=False
    for p in transition['points']:
        if p['name']=='failureWait':consumed=True
        if p.get('player')!=state['player'] or p.get('lives')!=state['lives']-int(consumed):
            raise ValueError('Restarted failure must consume exactly one inherited life')
    if not consumed:raise ValueError('Restarted result omits life consumption')
    return services


def compare_result(prefix,transition,gameplay,outro,native,epoch):
    services=analyze(prefix,transition,gameplay,outro)
    differences=compare_prefix(prefix,native['prefix'],native['polls'],native['prefixSummary'],epoch)
    differences+=compare_transition(transition,native['points'],native['services'],native['irqs'],native['summary'],epoch)
    if len(native['entry'])!=1:raise ValueError('Missing native outgoing-result attachment')
    first=prefix['points'][0];state=first['state']
    entry=native['entry'][0]
    if int(entry['end'])!=first['cycles']-epoch or int(entry['tick'])!=state['tick']:
        raise ValueError('Native result setup lacks its outgoing endpoint')
    def check(category,wanted,row):
        if any(k not in row for k in wanted):raise ValueError('Incomplete native result attachment fields')
        delta={k:[v,int(row[k])] for k,v in wanted.items() if int(row[k])!=v}
        if delta:differences.append(dict(category=category,fields=delta))
    check('inheritedState',dict(countdown=state['countdown']),entry)
    check('prefixState',dict(display=10,stat=0,countdown=600,random=state['random'],tick=state['tick'],player=state['player'],lives=state['lives'],inputHeld=state['held'],inputPressed=state['pressed']),native['prefixSummary'][0])
    enable=next(p for p in transition['points'] if p['name']=='enable');lcd_epoch=enable['cycles']-20-epoch
    periodic=len(services)-1
    check('resultState',dict(player=state['player'],lives=state['lives']-1,nextStat=lcd_epoch+143*456+periodic*70224,nextVBlank=lcd_epoch+144*456+periodic*70224),native['summary'][0])
    return differences


def compare(args):
    manifest=json.loads((args.capture/'capture-summary.json').read_text())
    names=('result-prefix','result-transition','gameplay','outro')
    records=[json.loads((args.out/(name+'.json')).read_text()) for name in names]
    startup=json.loads((args.startup/'startup.json').read_text())
    for record in [*records,startup]:
        require_capture_reference(manifest,record)
        if manifest['controlDifferences'] or any(record[k]!=manifest[k] for k in ('romSha256','controlMemorySha256')):raise ValueError('Mixed following-result controls')
    from air_startup_reference import analyze as startup_epoch
    epoch=startup_epoch(startup)['epoch']
    def rows(path):
        with path.open(encoding='utf-8-sig',newline='') as stream:return list(csv.DictReader(stream))
    base=str(args.native_base)
    scope=getattr(args,'native_scope','following')
    if scope not in ('following','next'):raise ValueError('Unknown subsequent result scope')
    if scope=='next' and any(not r.get('nextRetry') for r in records[:3]):raise ValueError('Missing third-attempt result scope')
    files=dict(prefix='.following-result.csv',polls='.following-result.polls.csv',prefixSummary='.following-result.summary.csv',points='.following-incoming.csv',services='.following-incoming.services.csv',irqs='.following-incoming.interrupts.csv',summary='.following-incoming.summary.csv',entry='.following-outro.summary.csv')
    files={key:suffix.replace('.following-','.'+scope+'-') for key,suffix in files.items()}
    native={k:rows(Path(base+suffix)) for k,suffix in files.items()}
    differences=compare_result(*records,native,epoch)
    report=dict(comparedPrefixBoundaries=len(native['prefix']),comparedPolls=len(native['polls']),comparedResultBoundaries=len(native['points']),comparedServices=len(native['services']),comparedInterrupts=len(native['irqs']),failureHoldAccepted=records[1].get('failureHold',False),livesBefore=records[0]['points'][0]['state']['lives'],livesAfter=records[1]['points'][-1]['lives'],differences=len(differences),firstDifference=differences[:1],productionSchedulerAccepted=False)
    write_json(Path(base+'.'+scope+'-result.comparison.json'),report);print(json.dumps(report,indent=2))
    if differences:raise ValueError('Native restarted result setup/transition differs')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('native_base',type=Path)
    for key in ('capture','out','startup'):parser.add_argument('--'+key,type=Path,required=True)
    parser.add_argument('--native-scope',choices=('following','next'),default='following')
    compare(parser.parse_args())
