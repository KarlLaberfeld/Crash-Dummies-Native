"""Compare an experimental native ordinary-clock replay with local originals.

Partial captures remain explicitly partial. This does not certify the Windows
loop, subinstruction interrupt latency, input sampling, pixels or PCM.
"""
import argparse
from bisect import bisect_left, bisect_right
import csv
import json
from pathlib import Path

from air_reference import write_json
from extract_air import HANDLERS
from air_timing import elapsed_work, STAGES


def compare_states(original,native):
    if not native or len(native)>len(original):raise ValueError('Invalid native update count')
    required=('tick','handler','frame','flags','x','y','cameraX','cameraY','speed','rate','tilt',
        'count','crash','done','waiting','delay','period','transfer','remaining','map','result',
        'seconds','secondTicks','random')
    differences=[]
    for index,(raw,row) in enumerate(zip(original,native)):
        source=dict(raw)
        source['handler']=HANDLERS[source['handler']]
        source['seconds']=(source['seconds']>>4)*10+(source['seconds']&15)
        source['map']=int(bool(source['map']))
        delta={name:[source[name],row[name]] for name in required if source[name]!=row[name]}
        if delta:differences.append(dict(update=index,fields=delta))
    return differences


def compare_services(original,native,compare_inputs=False):
    if not native or len(native)>len(original):raise ValueError('Invalid native display count')
    differences=[]
    for index,(q,row) in enumerate(zip(original,native)):
        if row['service']!=index:raise ValueError('Unordered native display service')
        expected=dict(tick=q['tick'],ready=q['transfer'],display=q['phases']['bookkeeping']-q['phases']['display'],
            effects=q['phases']['audioBank']-q['phases']['effects'],music=q['phases']['restore']-q['phases']['music'],
            cursor=(q['displayWorkload']['cursor']+1)%13,
            pending=-1 if q['effectWorkload']['pending']==255 else q['effectWorkload']['pending'])
        expected.update({'bar'+str(i):v for i,v in enumerate(q['hudBar'])})
        if compare_inputs:
            if 'inputHeld' not in row or 'held' not in q:raise ValueError('Missing display button sample coverage')
            expected['inputHeld']=q['held']
        delta={name:[value,row[name]] for name,value in expected.items() if value!=row[name]}
        if delta:differences.append(dict(service=index,fields=delta))
    return differences


def compare_sprites(original,native,expected_services=None):
    if not native or len(native)%40 or len(native)//40>len(original):raise ValueError('Invalid native sprite publication count')
    if expected_services is not None and len(native)!=expected_services*40:raise ValueError('Sprite publications must cover every compared display service')
    differences=[]
    for service,q in enumerate(original[:len(native)//40]):
        if len(q.get('oam',[]))!=160:raise ValueError('Missing original sprite publication snapshot')
        for slot in range(40):
            row=native[service*40+slot]
            if row['service']!=service or row['slot']!=slot:raise ValueError('Unordered native sprite publication')
            y,x,tile,flags=q['oam'][4*slot:4*slot+4]
            expected=dict(present=int(y!=0))
            if y:expected.update(x=x,y=y,flags=flags)
            delta={name:[value,row[name]] for name,value in expected.items() if value!=row[name]}
            if delta:differences.append(dict(service=service,slot=slot,fields=delta))
    return differences


def compare_input_samples(original,native):
    if not native or len(native)>len(original):raise ValueError('Incomplete original display input coverage')
    differences=[]
    for i,(q,row) in enumerate(zip(original,native)):
        if q['service']!=i or row['service']!=i:raise ValueError('Unordered display input comparison')
        if 'inputHeld' not in row or 'inputPressed' not in row:raise ValueError('Missing native display sampler fields')
        expected=dict(tick=q['tick'],inputHeld=q['held'],inputPressed=q['pressed'])
        delta={name:[value,row[name]] for name,value in expected.items() if value!=row[name]}
        if delta:differences.append(dict(service=i,fields=delta))
    return differences


def compare_phase_work(original,interrupts,native,completed_updates):
    if len(native)!=completed_updates*6 or not 0<completed_updates<=len(original):raise ValueError('Incomplete native phase-work coverage')
    names=list(STAGES.values())
    starts=[q['start']-20 for q in interrupts];ends=[q['end']+16 for q in interrupts]
    if any(a>=b for a,b in zip(starts,ends)) or any(ends[i]>starts[i+1] for i in range(len(starts)-1)):
        raise ValueError('Unordered or overlapping phase interrupts')
    differences=[]
    for update in range(completed_updates):
        for phase in range(6):
            row=native[update*6+phase]
            if row['update']!=update or row['phase']!=phase:raise ValueError('Unordered native phase work')
            a=original[update][names[phase]];b=original[update][names[phase+1]]
            relevant=interrupts[bisect_right(ends,a['cycles']):bisect_left(starts,b['cycles'])]
            expected=dict(tick=a['tick'],work=elapsed_work(a['cycles'],b['cycles'],relevant))
            delta={name:[value,row[name]] for name,value in expected.items() if value!=row[name]}
            if delta:differences.append(dict(update=update,phase=phase,fields=delta))
    return differences


def main(args):
    def rows(path):
        with path.open(encoding='utf-8-sig',newline='') as stream:
            return [{k:int(v) for k,v in row.items()} for row in csv.DictReader(stream)]
    manifest=json.loads((args.capture/'capture-summary.json').read_text())
    timing=json.loads((args.timing/'timing.json').read_text())
    if manifest['controlDifferences'] or timing['romSha256']!=manifest['romSha256'] or timing['controlMemorySha256']!=manifest['controlMemorySha256']:
        raise ValueError('Unverified or mismatched original capture')
    original=json.loads((args.capture/'trace.json').read_text())['post']
    native=rows(args.native_csv);services=rows(args.services_csv)
    state_differences=compare_states(original,native)
    service_differences=compare_services([q for q in timing['interrupts'] if q['kind']=='vblank'],services,args.display_inputs)
    phase_differences=compare_phase_work(timing['updates'],timing['interrupts'],rows(args.phase_csv),len(native)) if args.phase_csv else None
    sprite_differences=None
    input_differences=None
    if args.input_reference:
        ref=json.loads(args.input_reference.read_text())
        if ref.get('version')!=1 or ref['controlMemorySha256']!=manifest['controlMemorySha256'] or ref['romSha256']!=manifest['romSha256']:raise ValueError('Unverified input reference')
        input_differences=compare_input_samples(ref['samples'],services)
    if args.sprite_reference:
        sprite_reference=json.loads(args.sprite_reference.read_text())
        if sprite_reference['controlMemorySha256']!=manifest['controlMemorySha256'] or sprite_reference['romSha256']!=manifest['romSha256']:raise ValueError('Unverified sprite reference')
        sprite_differences=compare_sprites([q for q in sprite_reference['interrupts'] if q['kind']=='vblank'],rows(args.sprite_csv),len(services))
    result=dict(comparedUpdates=len(native),originalUpdates=len(original),captureComplete=len(native)==len(original),
        comparedDisplayServices=len(services),differingUpdates=len(state_differences),differingDisplayServices=len(service_differences),
        differingSpriteSlots=len(sprite_differences) if sprite_differences is not None else None,
        differingWorkPhases=len(phase_differences) if phase_differences is not None else None,
        differingInputSamples=len(input_differences) if input_differences is not None else None,
        firstUpdateDifference=state_differences[0] if state_differences else None,
        firstDisplayDifference=service_differences[0] if service_differences else None,
        firstWorkPhaseDifference=phase_differences[0] if phase_differences else None,
        firstInputDifference=input_differences[0] if input_differences else None,
        suppliesPerUpdateClock=False,runtimeSchedulingFixed=False,
        inputMode='display-sampled' if args.display_inputs else 'update-aligned',
        evidenceLimit='Experimental semantic-phase replay. Initial clock/timer/random phase and '+
            ('per-display button samples' if args.display_inputs else 'update-aligned buttons')+
            ' are supplied; per-update counters, costs and world outcomes are not. Physical input timing, pause/exit/outro, pixels, PCM and the Windows loop remain unverified.')
    write_json(args.native_csv.with_suffix('.clock-comparison.json'),result)
    write_json(args.native_csv.with_suffix('.clock-differences.json'),dict(updates=state_differences,services=service_differences,sprites=sprite_differences,phases=phase_differences,inputs=input_differences))
    print(json.dumps(result,indent=2))
    if state_differences or service_differences or sprite_differences or phase_differences or input_differences:raise ValueError('Ordinary-clock state, service, sprite, phase or input differences')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('native_csv',type=Path);parser.add_argument('services_csv',type=Path)
    parser.add_argument('--capture',type=Path,default=Path('local/original-air-verified'))
    parser.add_argument('--timing',type=Path,default=Path('local/air-display-effect-timing'))
    parser.add_argument('--sprite-reference',type=Path);parser.add_argument('--sprite-csv',type=Path)
    parser.add_argument('--phase-csv',type=Path)
    parser.add_argument('--display-inputs',action='store_true',help='Require matching per-display button samples in the service CSV')
    parser.add_argument('--input-reference',type=Path,help='Independent original held/fresh button samples, for comparison only')
    args=parser.parse_args()
    if bool(args.sprite_reference)!=bool(args.sprite_csv):parser.error('Sprite reference and native sprite CSV are required together')
    if args.input_reference and not args.display_inputs:parser.error('Input reference requires display-sampled mode')
    main(args)
