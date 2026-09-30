"""Inspect the identified music data language; no cartridge CPU execution.

This is preparation for a native sequencer, not audio output or a fidelity claim.
Generated reports contain original data and must stay in local/ or build/.
"""
from pathlib import Path
import argparse
import json
import struct
from extract import address, read_rom

# Four channel families, with special wave/noise commands verified in 02:4ecf-541f.
NAMES=['loop_begin','loop_end','fixed_duration','stop','call','return',
       'transpose','fine_tune','jump','registers','envelope','envelope_mode',
       'pitch_slide','note_hold','duty','vibrato','no_transpose','pitch_modulation',
       'instrument_table','gate','release','pan','stereo_motion','unused','unused','stop_all']
LENGTHS=[1,0,1,0,2,0,1,1,2,None,3,1,3,1,1,4,0,3,3,1,1,1,None,0,0,0]

def music_roots(rom):
    return [[rom[0x3783+n+channel*28]+256*rom[0x3791+n+channel*28]
             for channel in range(4)] for n in range(14)]

def command(rom,pointer,channel,fixed):
    offset=address(2,pointer)
    if not 0x5584<=pointer<0x8000:raise ValueError(f'Music pointer outside data: {pointer:04x}')
    op=rom[offset]
    if op<128:
        size=1 if fixed else 2
        return 'note',[op,fixed if fixed else rom[offset+1]],pointer+size
    index=op-128
    if not 0<=index<26:raise ValueError(f'Unknown music command {op:02x} at {pointer:04x}')
    name=NAMES[index];size=LENGTHS[index]
    if channel==2:
        overrides={10:('wave',2),11:('wave',2),14:('wave_volume',1),18:('unused',0),19:('unused',0),20:('unused',0)}
        if index in overrides:name,size=overrides[index]
    if channel in (3,5) and index in (6,7):name,size=('noise_short' if index==6 else 'noise_long'),0
    if channel==5 and index in (13,14,15,16):name='unused'
    if name=='unused':raise ValueError(f'Unimplemented dispatch entry {op:02x}')
    if name=='registers':
        size=0
        while size<128:
            register=rom[offset+1+size];size+=1
            if register>=128:break
            if not 0x10<=register<=0x3f:raise ValueError(f'Unexpected audio register {register:02x}')
            size+=1
        else:raise ValueError('Unterminated audio register list')
    if name=='stereo_motion':size=3 if rom[offset+1] else 1
    if pointer+1+size>0x8000:raise ValueError('Music command crosses bank end')
    return name,list(rom[offset+1:offset+1+size]),pointer+1+size

def inspect_track(rom,start,channel):
    pointer=start;fixed=0;loop_start=0;loop_count=0;stack=[];frames=0;notes=0
    seen={};commands={};references=set();maximum_stack=0
    for step in range(100000):
        state=(pointer,fixed,loop_start,loop_count,tuple(stack))
        if state in seen:
            return dict(start=start,channel=channel,end='loop',intro_frames=seen[state],
                        loop_frames=frames-seen[state],notes=notes,max_stack=maximum_stack,
                        commands=list(commands.values()),references=sorted(references))
        seen[state]=frames
        name,args,nxt=command(rom,pointer,channel,fixed)
        commands[(pointer,fixed!=0)]=dict(address=pointer,operation=name,args=args)
        pointer=nxt
        if name=='note':frames+=args[1] or 256;notes+=1
        elif name=='fixed_duration':fixed=args[0]
        elif name=='loop_begin':loop_start=nxt;loop_count=args[0]
        elif name=='loop_end':
            loop_count=(loop_count-1)&255
            if loop_count:pointer=loop_start
        elif name in ('call','jump'):
            if name=='call':
                stack.append(nxt);maximum_stack=max(maximum_stack,len(stack))
                if len(stack)>3:raise ValueError('Music return stack exceeds original three slots')
            pointer=args[0]+256*args[1]
        elif name=='return':
            if not stack:raise ValueError('Music return stack underflow')
            pointer=stack.pop()
        elif name in ('stop','stop_all'):
            return dict(start=start,channel=channel,end=name,frames=frames,notes=notes,
                        max_stack=maximum_stack,commands=list(commands.values()),references=sorted(references))
        elif name=='wave':references.add(args[0]+256*args[1])
        elif name=='instrument_table':references.add(args[1]+256*args[2])
    raise ValueError('Music control-flow inspection exceeded bound')

def analyze(rom):
    songs=[]
    for index,roots in enumerate(music_roots(rom)):
        songs.append(dict(index=index,channels=[inspect_track(rom,pointer,channel) for channel,pointer in enumerate(roots)]))
    effects=[]
    for index in range(26):
        roots=struct.unpack_from('<HH',rom,0x37f3+index*4)
        effects.append(dict(index=index,channels=[inspect_track(rom,pointer,4+channel) for channel,pointer in enumerate(roots) if pointer]))
    return dict(format='TICD_AUDIO_ANALYSIS_1',status='data-language analysis only; no native sound output yet',songs=songs,effects=effects)

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('rom',type=Path)
    parser.add_argument('--out',type=Path,default=Path('local/audio-analysis.json'));args=parser.parse_args()
    result=analyze(read_rom(args.rom));args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    for song in result['songs']:
        print(song['index'],[(c['end'],c.get('loop_frames',c.get('frames')),c['notes']) for c in song['channels']])
