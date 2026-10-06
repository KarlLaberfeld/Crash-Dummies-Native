"""Coupled native gameplay/pause/graphics/audio comparison, measurements local.

Uses existing control-verified original cases. Only initial phase and raw held
buttons enter the native process. Original effects, voices, modes, poll counts,
work and worlds are comparison targets, never replay inputs.
"""
import argparse
import json
from pathlib import Path
import subprocess
from types import SimpleNamespace

from air_clock_compare import compare_states,compare_input_samples,compare_sprites,compare_services,compare_phase_work,compare_entity_states
from air_pause_compare import load,rows,compare_bus,compare_graphics,compare_intervals
from air_reference import write_json
from audio_timing import compare_native
from air_startup_reference import compare as compare_startup
from reference_backend import require_capture_reference


def compare(case,out):
    capture=Path('local/sameboy-air-pause-'+case);manifest=load(capture/'capture-summary.json')
    if manifest.get('controlDifferences') or not manifest.get('pauseReached'):raise ValueError('Requires a verified original pause')
    def reference(path):
        data=load(path)
        require_capture_reference(manifest,data)
        if any(data.get(k)!=manifest.get(k) for k in ('romSha256','controlMemorySha256')):raise ValueError('Mixed original controls')
        return data
    # Large recordings are checked sequentially. Keeping work, sprites and
    # music (and a second music decode) together exhausts Windows commit.
    inputs=reference(Path('local/pause-prefix-'+case+'-input/inputs.json'))
    states=rows(out/'states.csv');services=rows(out/'services.csv')
    original=load(capture/'trace.json')['post']
    if len(states)!=len(original) or len(services)!=len(inputs['samples']):raise ValueError('Incomplete coupled game/input coverage')
    state=compare_states(original,states);buttons=compare_input_samples(inputs['samples'],services)
    update_count=len(states);service_count=len(services)
    del original,states,inputs
    work=reference(Path('local/pause-coupled-'+case+'-work-reference/timing.json'))
    ordinary=[dict(row,service=i) for i,row in enumerate(s for s in services if s['displaySelector']==4)]
    original_services=[q for q in work['interrupts'] if q['kind']=='vblank']
    if work.get('version')!=9 or len(work['updates'])!=update_count or len(original_services)!=len(ordinary):
        raise ValueError('Incomplete coupled phase/display coverage')
    display=compare_services(original_services,ordinary,True)
    phase_rows=[dict(row,phase=int(row['phase'])) for row in rows(out/'services.csv.phases.csv')]
    phases=compare_phase_work(work['updates'],work['interrupts'],phase_rows,update_count)
    entities=rows(out/'entities.csv');entity=compare_entity_states(work['updates'],entities,update_count)
    ordinary_count=len(ordinary);entity_count=len(entities)
    del work,ordinary,original_services,phase_rows,entities
    sprites=reference(Path('local/pause-coupled-'+case+'-sprites-reference/sprites.json'))
    published=rows(out/'sprites.csv')
    sprite=compare_sprites(sprites['interrupts'],published,service_count)
    sprite_count=len(published)
    del sprites,published
    lcd=reference(Path('local/sameboy-air-pause-'+case+'-lcd-data/lcd.json'))
    prefix=load(Path('local/pause-native-'+case+'-data/graphics.json'))
    bus=compare_bus(lcd,prefix,rows(out/'services.csv.pause.bus.csv'))
    storage=compare_graphics(lcd,prefix,rows(out/'services.csv.pause.graphics.csv'))
    del lcd
    timing=reference(Path('local/sameboy-air-pause-'+case+'-timing/pause.json'))
    intervals=compare_intervals(timing['pauses'][0],prefix,rows(out/'services.csv.pause.phases.csv'))
    del timing,prefix
    music_root=Path('local/pause-coupled-'+case+'-audio-reference');music=reference(music_root/'music.json')
    if not music.get('captureComplete'):raise ValueError('Coupled comparison requires complete music services')
    compare_native(SimpleNamespace(native_csv=out/'voices.csv',out=music_root,gameplay=True),music)
    del music
    audio=load(music_root/'native-comparison.json')
    if audio['services']!=service_count:raise ValueError('Incomplete coupled audio coverage')
    startup=compare_startup(SimpleNamespace(capture=capture,out=Path('local/pause-coupled-'+case+'-startup-reference'),native_csv=out/'services.csv'))
    result=dict(comparedUpdates=update_count,comparedDisplayServices=service_count,comparedInputSamples=service_count,
        comparedSpriteSlots=sprite_count,comparedVoiceRows=audio['services']*6,pausedServices=audio['pausedServices'],
        comparedStartupPoints=startup['comparedStartupPoints'],startupDifferences=startup['differences'],
        comparedOrdinaryServices=ordinary_count,comparedWorkPhases=update_count*6,comparedPreUpdateEntitySlots=entity_count,
        displayWorkDifferences=display,phaseWorkDifferences=phases,entityDifferences=entity,
        stateDifferences=state,inputDifferences=buttons,spriteDifferences=sprite,pauseBusDifferences=bus,
        pauseStorageDifferences=storage,pauseIntervalDifferences=intervals,audioDifferences=audio['differingVoiceRows'],productionSchedulerAccepted=False,
        evidenceLimit='Complete bounded gameplay/pause/audio replay including post-resume selected worlds, held/fresh buttons, sprite geometry/flags, software voice fields/work and native effect requests. No original world/mode/cost/voice/effect values drive it. Full pixels/PCM, unowned startup/IRQ/critical paths, other stunts, production scheduling and independent hardware/Windows acceptance remain open.')
    write_json(out/'comparison.json',result);print(json.dumps(result,indent=2))
    if state or buttons or sprite or bus or storage or intervals or display or phases or entity or audio['differingVoiceRows']:
        raise ValueError('Coupled native replay differs from original')


def run(case,out):
    out.mkdir(parents=True,exist_ok=True);capture=Path('local/sameboy-air-pause-'+case)
    manifest=load(capture/'capture-summary.json');trace=load(capture/'trace.json')
    inputs=load(Path('local/pause-prefix-'+case+'-input/inputs.json'));require_capture_reference(manifest,inputs)
    if manifest.get('controlDifferences') or any(inputs.get(k)!=manifest.get(k) for k in ('romSha256','controlMemorySha256')):
        raise ValueError('Requires matching verified display samples')
    header=(capture/'inputs.txt').read_text().splitlines()[0]
    (out/'inputs.txt').write_text(header+'\n'+'0 0\n'*len(trace['pre']))
    (out/'buttons.txt').write_text(''.join(str(s['held'])+'\n' for s in inputs['samples']))
    with (out/'states.csv').open('w') as stream:
        subprocess.run([str(Path('local/air-clock-probe.exe').resolve()),str(out/'inputs.txt'),str(out/'services.csv'),str(manifest['difficulty']),
            str(out/'sprites.csv'),'--display-inputs',str(out/'buttons.txt'),'--pause-replay','--audio-csv',str(out/'voices.csv'),
            '--entities-csv',str(out/'entities.csv')],stdout=stream,check=True)
    compare(case,out)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('mode',choices=('run','compare'))
    parser.add_argument('case',choices=('coast','easy','hard'));parser.add_argument('--out',type=Path)
    args=parser.parse_args();out=args.out or Path('local/pause-coupled-'+args.case)
    {'run':run,'compare':compare}[args.mode](args.case,out)
