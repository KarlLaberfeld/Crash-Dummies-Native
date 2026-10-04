"""Local original-driver measurements; never imported by the native runtime.

Requires the control-verified Air replay. Original state/music stay under local/.
Report is independent of PyBoy. Capture uses only measurement hooks.
"""
import argparse
import csv
import hashlib
import importlib.metadata
import json
from pathlib import Path
import sys

from air_reference import write_json
from analyze_audio import command
from extract import read_rom
from audio_work import command_cycles, envelope_cycles, note_cycles, output_cycles, modulation_cycles, voice_cycles, service_cycles

VERSION = 1
VOICE_STARTS = (0x404c, 0x4330, 0x4613, 0x47ec, 0x49de, 0x4cc8)
FETCH = (0x4062, 0x4346, 0x4629, 0x4802, 0x49fa, 0x4ce4)
NOTE = (0x4072, 0x4356, 0x4639, 0x4812, 0x4a0a, 0x4cf4)
# The wave voice jumps directly to the following voice; placing a hook on
# that JP and its target stalls PyBoy 2.7.0. It has no envelope/output phase.
ENVELOPE = (0x4165, 0x4449, None, 0x48cc, 0x4afd, 0x4dae)
OUTPUT = (0x420d, 0x44f0, None, 0x4975, 0x4ba5, 0x4e57)
MODULATION = (0x422f, 0x4512, None, 0x4991, 0x4bc7, 0x4e73)
BYTE_FIELDS = {
    'active': (0xdea9,0xdeaa,0xdeab,0xdeac,0xdeae,0xdead),
    'remaining': (0xdeec,0xdeed,0xdeee,0xdeef,0xdef1,0xdef0),
    'fixed': (0xdebd,0xdebe,0xdebf,0xdec0,0xdec2,0xdec1),
    'loopCount': (0xdeb3,0xdeb4,0xdeb5,0xdeb6,0xdeb8,0xdeb7),
    'stage': (0xde3d,0xde3e,None,0xde3f,0xde41,0xde40),
    'envelopeCounter': (0xde42,0xde43,None,0xde44,0xde46,0xde45),
    'attack': (0xde29,0xde2b,None,0xde2d,0xde31,0xde2f),
    'decay': (0xde2a,0xde2c,None,0xde2e,0xde32,0xde30),
    'initialStage': (0xde38,0xde39,None,0xde3a,0xde3c,0xde3b),
    'initialVolume': (0xde24,0xde25,None,0xde26,0xde28,0xde27),
    'sustain': (0xde33,0xde34,None,0xde35,0xde37,0xde36),
    'volume': (0xdecc,0xdecd,None,0xdece,0xded0,0xdecf),
    'releaseCounter': (0xdee7,0xdee8,None,0xdee9,0xdeeb,0xdeea),
    'instrumentPeriod': (0xdea4,0xdea5,None,0xdea6,0xdea8,0xdea7),
    'tableIndex': (0xde2a,0xde2c,None,0xde2e,0xde32,0xde30),
    'envelopeMode': (0xdec7,0xdec8,None,0xdec9,0xdecb,0xdeca),
    'gate': (0xdedd,0xdede,None,0xdedf,0xdee1,0xdee0),
    'release': (0xdee2,0xdee3,None,0xdee4,0xdee6,0xdee5),
    'transpose': (0xdeaf,0xdeb0,0xdeb1,None,0xdeb2,None),
    'noTranspose': (0xded9,0xdeda,0xdedb,None,0xdedc,None),
    'note': (0xfff5,0xfff6,0xfff7,None,0xfffa,None),
    'fineTune': (0xdeb9,0xdeba,0xdebb,None,0xdebc,None),
    'noiseWidth': (None,None,None,0xded7,None,0xded8),
    'vibratoDelay': (0xde6a,0xde6b,0xde6c,None,0xde6d,None),
    'vibratoWait': (0xde6e,0xde6f,0xde70,None,0xde71,None),
    'vibratoStep': (0xde72,0xde73,0xde74,None,0xde75,None),
    'vibratoHalf': (0xde7a,0xde7b,0xde7c,None,0xde7d,None),
    'vibratoCounter': (0xde76,0xde77,0xde78,None,0xde79,None),
    'direction': (0xded1,0xded2,0xded3,0xded4,0xded6,0xded5),
    'arpAmount': (0xde59,0xde5a,0xde5b,0xde5c,0xde5e,0xde5d),
    'arpUp': (0xde4d,0xde4e,0xde4f,0xde50,0xde52,0xde51),
    'arpDown': (0xde53,0xde54,0xde55,0xde56,0xde58,0xde57),
    'arpCounter': (0xde47,0xde48,0xde49,0xde4a,0xde4c,0xde4b),
    'portamento': (0xde5f,0xde60,0xde61,None,0xde62,None),
    'targetNote': (0xde63,0xde64,0xde65,None,0xde66,None),
    'pitchDelay': (0xde82,0xde83,0xde84,0xde85,0xde87,0xde86),
    'pitchWait': (0xde92,0xde93,0xde94,0xde95,0xde97,0xde96),
}
WORD_FIELDS = {
    'position': (0xffd1,0xffd3,0xffd5,0xffd7,0xffdb,0xffd9),
    'frequency': (0xffed,0xffef,0xfff1,None,0xfff3,None),
    'instrument': (0xffdd,0xffdf,None,0xffe1,0xffe5,0xffe3),
}

def capture(args):
    rom = read_rom(args.rom)
    manifest = json.loads((args.capture/'capture-summary.json').read_text())
    if manifest['romSha256'] != hashlib.sha256(rom).hexdigest() or manifest['controlDifferences']:
        raise ValueError('Requires a matching control-verified replay')
    if args.reference_lib:
        sys.path.insert(0, str(args.reference_lib.resolve()))
    if importlib.metadata.version('pyboy') != '2.7.0':
        raise ValueError('Reference hooks require PyBoy 2.7.0')
    from pyboy import PyBoy
    p = PyBoy(str(args.rom), window='null', sound_volume=0)
    p.set_emulation_speed(0)
    rows, current, voice = [], None, None
    hook_count = 0
    phases = {a:(i,n) for n, addresses in [('fetch',FETCH),('note',NOTE),
              ('envelope',ENVELOPE),('output',OUTPUT),('modulation',MODULATION)]
              for i,a in enumerate(addresses) if a is not None}
    def word(a):
        return p.memory[a] + 256*p.memory[a+1]
    def state(i):
        s={name:p.memory[a[i]] if a[i] else 0 for name,a in BYTE_FIELDS.items()}
        s.update({name:word(a[i]) if a[i] else 0 for name,a in WORD_FIELDS.items()})
        if i in (3,5):s['frequency']=p.memory[0xfff8 if i==3 else 0xfff9]
        if i!=2:
            s['tableValue']=p.memory[s['instrument']+s['tableIndex']]
            s['tableNext']=p.memory[s['instrument']+((s['tableIndex']+1)&255)]
            s['tableFirst']=p.memory[s['instrument']]
        s['hardwareVolume']=p.memory[0xff21 if i in (3,5) else 0xff17 if i==1 else 0xff12]>>4
        return s
    def point(i,now):
        return dict(cycles=now,state=state(i))
    def hook(a):
        nonlocal current, voice, hook_count
        if p.memory[0xc098]!=4:return
        hook_count += 1
        now=p._cycles()
        if a==0x247b:
            if current is not None:raise ValueError('Nested music service')
            current=dict(start=now,enabled=p.memory[0xffcf],stereo=p.memory[0xdef7],
                         stereoCounter=p.memory[0xdef6],stereoDirection=p.memory[0xdef5],voices=[])
            return
        if current is None:raise ValueError('Music boundary outside service')
        if a==0x247e:
            current['end']=now;rows.append(current);current=voice=None
        elif a in VOICE_STARTS or a==0x4ec0:
            if voice is not None:
                voice['end']=now;voice['post']=state(voice['index'])
            voice=None
            if a==0x4ec0:current['finalization']=now
            else:
                i=VOICE_STARTS.index(a);voice=dict(index=i,start=point(i,now),fetch=[])
                current['voices'].append(voice)
        elif a==0x400a:current['tail']=now
        else:
            i,name=phases[a]
            if voice is None or voice['index']!=i:raise ValueError('Wrong music voice boundary')
            item=point(i,now)
            if name=='fetch':
                pointer=p.register_file.D*256+p.register_file.E
                op,arg,nxt=command(rom,pointer,i,item['state']['fixed'])
                item.update(operation=op,args=arg,pointer=pointer,next=nxt)
                voice['fetch'].append(item)
            else:
                if name in voice:raise ValueError('Repeated music phase')
                voice[name]=item
    try:
        with (args.capture/'setup.state').open('rb') as stream:p.load_state(stream)
        for a in (0x247b,0x247e):p.hook_register(0,a,hook,a)
        for a in (*VOICE_STARTS,0x4ec0,0x400a,*phases):p.hook_register(2,a,hook,a)
        for event_index,e in enumerate(json.loads((args.capture/'events.json').read_text())):
            if args.progress and event_index%100==0:print(f'event {event_index}, music services {len(rows)}',flush=True)
            if e[0]=='tick':p.tick(e[1],e[2])
            elif e[0] in ('press','release'):getattr(p,'button_'+e[0])(e[1])
            else:raise ValueError('Unknown replay event')
        memory=bytes(p.memory[0x8000:0x10000])
    finally:p.stop(save=False)
    if current is not None or hashlib.sha256(memory).hexdigest()!=manifest['controlMemorySha256']:
        raise ValueError('Incomplete capture or changed reference control memory')
    args.out.mkdir(parents=True,exist_ok=True)
    write_json(args.out/'music.json',dict(version=VERSION,romSha256=manifest['romSha256'],
        controlMemorySha256=manifest['controlMemorySha256'],emulator='PyBoy 2.7.0',services=rows))
    report(args)

def validate_services(data):
    """Reject incomplete intervals before attributing measured work to source."""
    if data.get('version')!=VERSION:raise ValueError('Recapture with current music hooks')
    if not data['services']:raise ValueError('Empty music capture cannot certify work')
    previous=-1
    for r in data['services']:
        if not previous<=r['start']<r['end']:raise ValueError('Unordered music service interval')
        previous=r['end']
        if not r['enabled']:
            if r['voices']:raise ValueError('Disabled service contains music voices')
            continue
        if [v['index'] for v in r['voices']]!=list(range(6)):
            raise ValueError('Incomplete or unordered music voice chain')
        boundaries=[r['start']]+[v['start']['cycles'] for v in r['voices']]+[r['finalization'],r['tail'],r['end']]
        if any(a>=b for a,b in zip(boundaries,boundaries[1:])):raise ValueError('Unordered music body boundaries')
        for i,v in enumerate(r['voices']):
            if v['end']!=boundaries[i+2]:raise ValueError('Music voice does not end at its successor')
            names=[name for name in ('note','envelope','output','modulation') if name in v]
            active=bool(v['start']['state']['active']&128)
            fresh=active and v['start']['state']['remaining']==1
            if bool(v['fetch'])!=fresh:raise ValueError('Missing or unexpected command fetch')
            if not active and names:raise ValueError('Inactive voice has active phases')
            if i==2 and any(name!='note' for name in names):raise ValueError('Wave voice has a bypassed phase')
            if any(name in v for name in ('envelope','output','modulation')) and not all(name in v for name in ('envelope','output','modulation')):
                raise ValueError('Incomplete music envelope/output/modulation chain')
            if active and not fresh and i!=2 and 'envelope' not in v:raise ValueError('Missing continuing voice phases')
            if fresh:
                terminal=v['fetch'][-1]['operation']
                if terminal not in ('note','stop','stop_all'):raise ValueError('Unfinished music command chain')
                if ('note' in v)!=(terminal=='note'):raise ValueError('Missing or unexpected note initialization')
                if terminal=='note' and i!=2 and 'envelope' not in v:raise ValueError('Missing fresh note phases')
            points=[v['start']['cycles']]+[f['cycles'] for f in v['fetch']]+[v[name]['cycles'] for name in names]+[v['end']]
            if any(a>=b for a,b in zip(points,points[1:])):raise ValueError('Unordered music voice phases')

def report(args):
    data=json.loads((args.out/'music.json').read_text())
    validate_services(data)
    mismatches=[]
    counts=dict(voices=0,commands=0,notes=0,envelopes=0,outputs=0,modulation=0)
    def compare(service, voice, name, measured, source):
        if measured!=source:mismatches.append(dict(service=service,voice=voice,phase=name,measured=measured,source=source))
    for ri,r in enumerate(data['services']):
        for v in r['voices']:
            i=v['index'];counts['voices']+=1
            compare(ri,i,'voice',v['end']-v['start']['cycles'],voice_cycles(v))
            for j,f in enumerate(v['fetch']):
                counts['commands']+=1
                end=v['fetch'][j+1]['cycles'] if j+1<len(v['fetch']) else v['note']['cycles'] if f['operation']=='note' else v['end']
                compare(ri,i,'command',end-f['cycles'],command_cycles(f['operation'],f['args'],f['state']['loopCount']))
            if 'note' in v:
                counts['notes']+=1;f=v['fetch'][-1]
                end=v['envelope']['cycles'] if i!=2 else v['end']
                compare(ri,i,'note',end-v['note']['cycles'],note_cycles(i,v['note']['state'],f['args'],f['pointer']))
            if 'envelope' in v:
                for name,following,model in [('envelope','output',envelope_cycles),('output','modulation',output_cycles),('modulation',None,modulation_cycles)]:
                    counts[name+'s' if name!='modulation' else name]+=1
                    end=v[following]['cycles'] if following else v['end']
                    compare(ri,i,name,end-v[name]['cycles'],model(i,v[name]['state']))
        compare(ri,None,'service',r['end']-r['start'],service_cycles(r))
    summary=dict(services=len(data['services']),counts=counts,sourceModelMismatches=mismatches,
                 runtimeSchedulingFixed=False,evidenceLimit='Original semantic workloads only; source work agreement does not establish native audio state, PCM or real-time scheduling parity.')
    write_json(args.out/'summary.json',summary)
    print(json.dumps(summary,indent=2))
    if mismatches:raise ValueError('Music source work differs from reference measurement')

def compare_native(args):
    data=json.loads((args.out/'music.json').read_text())
    validate_services(data)
    if any(not r['enabled'] for r in data['services']):
        raise ValueError('Disabled original services need additional post-state capture for native comparison')
    with args.native_csv.open(encoding='utf-8-sig',newline='') as stream:
        rows=[{k:int(v) for k,v in r.items()} for r in csv.DictReader(stream)]
    if len(rows)!=len(data['services'])*6:raise ValueError('Expected six native voice rows per service')
    fields=('position','remaining','fixed','loopCount','transpose','noTranspose','fineTune',
            'note','targetNote','frequency','stage','envelopeCounter','volume','releaseCounter',
            'tableIndex','arpCounter','direction','vibratoWait','vibratoCounter','pitchWait')
    differences=[];first={}
    for ri,r in enumerate(data['services']):
        for vi,v in enumerate(r['voices']):
            row=rows[6*ri+vi]
            if row['service']!=ri or row['voice']!=vi:raise ValueError('Unordered native voice row')
            post=v['post'];active=int(bool(post['active']&128))
            expected=dict(active=active,voiceCost=v['end']-v['start']['cycles'],musicCost=r['end']-r['start'])
            if active:
                for name in fields:
                    if vi==2 and name in ('stage','envelopeCounter','volume','releaseCounter','tableIndex'):continue
                    if vi in (3,5) and name in ('transpose','noTranspose','fineTune','note','targetNote','vibratoWait','vibratoCounter'):continue
                    if name=='tableIndex' and not post['stage']&128:continue
                    expected[name]=post[name]
            delta={name:[value,row[name]] for name,value in expected.items() if value!=row[name]}
            if delta:
                differences.append(dict(service=ri,voice=vi,fields=delta))
                for name,values in delta.items():first.setdefault(name,dict(service=ri,voice=vi,original=values[0],native=values[1]))
    summary=dict(services=len(data['services']),differingVoiceRows=len(differences),firstDifferences=first,
        runtimeSchedulingFixed=False,evidenceLimit='Isolated native song/effect-request replay only. No original voice state drives it. This does not compare native gameplay effect requests, PCM waveform or Windows scheduling.')
    write_json(args.out/'native-comparison.json',summary)
    write_json(args.out/'native-differences.json',differences)
    print(json.dumps(summary,indent=2))
    if differences:raise ValueError('Native music state or work differs from original')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest='mode',required=True)
    rec=sub.add_parser('capture');rec.add_argument('rom',type=Path)
    rec.add_argument('--reference-lib',type=Path)
    rec.add_argument('--progress',action='store_true')
    rec.add_argument('--capture',type=Path,default=Path('local/original-air-verified'))
    comp=sub.add_parser('compare');comp.add_argument('native_csv',type=Path)
    for p in (rec,sub.add_parser('report'),comp):p.add_argument('--out',type=Path,default=Path('local/air-music-timing'))
    args=parser.parse_args();{'capture':capture,'report':report,'compare':compare_native}[args.mode](args)
