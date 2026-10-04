"""Source-derived semantic music work. No CPU state or instruction execution."""

def command_cycles(operation, args, loop_count=0):
    # 4062 / 4346 / 4629 / 4802 / 49fa / 4ce4 dispatch costs 84.
    fixed = {'note':28, 'loop_begin':168, 'fixed_duration':132, 'stop':132,
             'call':220, 'return':200, 'jump':136, 'transpose':132,
             'fine_tune':132, 'envelope':292, 'envelope_mode':132,
             'pitch_slide':196, 'note_hold':132, 'duty':132, 'vibrato':228,
             'no_transpose':124, 'pitch_modulation':196, 'instrument_table':212,
             'gate':132, 'release':132, 'pan':212, 'wave_volume':192,
             'wave':832, 'noise_short':136, 'noise_long':120, 'stop_all':240}
    if operation == 'loop_end':return 124 if loop_count == 1 else 172
    if operation == 'registers':return 124+100*((len(args)-1)//2) if args and len(args)%2 else -1
    if operation == 'stereo_motion':return (276 if args[0] else 228) if args else -1
    return fixed.get(operation, -1)

def envelope_cycles(index, state):
    if index == 2:return -1 # The wave voice bypasses this block.
    stage, counter, volume = state['stage'], state['envelopeCounter'], state['volume']
    noise = index in (3,5)
    if stage & 128:
        cost=36
        release=state['releaseCounter']
        cost+=28 if release else 32
        if release:
            cost+=32 if release==1 else 36
            if release==1:counter=1;cost+=48
        cost+=32 if counter==1 else 36
        if counter!=1:return cost
        value=state['tableValue']
        # A release expiration advances the table index before its lookup.
        if release==1:value=state['tableNext']
        cost+=84 if index==5 else 88
        if value & 128:return cost+12
        cost+=8
        if value<16:cost+=20
        else:cost+=16+(64 if index in (0,4) else 60)
        return cost+72
    cost=32+(12 if stage==0 else 16)
    if stage==0:
        cost+=48 if (counter-1)&128 else 52
        if not (counter-1)&128:return cost
        cost+=32+(40 if noise else 32)
        volume=(volume+1)&255
        cost+=24 if volume==15 else 28
        if volume!=15:return cost
        # Noise branches preserve INC stage's flags; they do not test decay.
        cost+=68 if noise else 68 if not state['decay'] else 72
        if noise or state['decay']:return cost
        stage=1;counter=0
    cost+=(20 if stage==1 else 24) if index==1 else (24 if stage==1 else 28)
    if stage!=1:return cost
    cost+=(48 if (counter-1)&128 else 52) if index==1 else (44 if (counter-1)&128 else 48)
    if not (counter-1)&128:return cost
    cost+=68+(4 if noise else 0)
    if volume==state['sustain']:return cost+12+40
    cost+=8
    return cost+(84 if (volume-1)&128 else 48)

def note_cycles(index, state, args, pointer):
    noise = index in (3,5)
    cost=48 # Publish stream pointer and clear the note-byte offset.
    if noise:
        cost+=48 # Noise width, nibble swap and captured frequency.
    else:
        nt=state['noTranspose']
        cost+=68 if nt==0 else 80 if nt==255 else 96
        cost+=4+(68 if state['portamento'] else 32)
        cost+=20+ (124 if index in (0,4) else 120)
    cost+=32 if state['fixed'] else 88
    cost+=20 if index==2 else 16
    size=1 if state['fixed'] else 2
    cost+=56 if (pointer&255)+size>255 else 48
    cost+=44
    if noise:cost+=20
    else:cost+=(108 if state['vibratoDelay'] else 48) if index==2 else (112 if state['vibratoDelay'] else 52)
    if index!=2:
        mode=state['envelopeMode']
        cost+=32 if not mode else 28
        if mode:
            if mode&128:
                cost+=16 if index==1 else 20 # Voice one uses JR instead of JP.
                duration=state['fixed'] or args[1]
                gate=state['gate']
                cost+=28 if gate else 32
                selected=gate and gate<duration
                if gate:cost+=32 if selected else 28
                if not selected:
                    cost+=(28 if state['release'] else 32) if noise else (32 if state['release'] else 36)
                    if state['release']:cost+=40
                cost+=112 if noise else 108 if index==1 else 104
            else:cost+=(20 if index==1 else 24)+(132 if noise else 116)
    if noise:
        frequency=((args[0]<<4)|(args[0]>>4)|state['noiseWidth'])&255
        cost+=28 if not frequency else 24+(76 if state['pitchDelay'] else 44)
        cost+=80
    elif index==2:
        cost+=(104 if state['pitchDelay'] else 68)+92
    else:
        cost+=(104 if index==1 else 100) if state['pitchDelay'] else 84
        cost+=20
    return cost

def output_cycles(index, state):
    if index in (0,1,4):return 172
    if index in (3,5):return 84 if (state['volume']&15)==state['hardwareVolume'] else 136
    return -1

def portamento_cycles(index, state):
    step,note,target=state['portamento'],state['note'],state['targetNote']
    if not step:return 32 if index==1 else 36
    cost=28 if index==1 else 32
    cost+=48 if note==target else 44
    if note==target:return cost
    if note>target:
        cost+=8
        result=(note-step)&255
        if index==1:
            cost+=40+(12 if result>=target else 8+16+16)
        else:
            cost+=56 if result==target else 52
            if result==target:
                result=(result+step+1)&255
                cost+=52 if result<target else 48+16
            elif result>target:cost+=12
            else:cost+=8+16+16
    else:
        cost+=12
        result=(note+step)&255
        if index==1:
            cost+=44
            if result==target:cost+=12+16
            elif result>target:cost+=8+12
            else:cost+=8+8+16
        else:cost+=52 if result<target else 48+16
    return cost+200

def modulation_cycles(index, state):
    if index==2:return -1
    noise=index in (3,5)
    cost=28 if state['pitchDelay'] else 32
    if state['pitchDelay']:
        wait=state['pitchWait']
        cost+=28 if wait else 32
        if wait:
            cost+=(32 if wait==1 else 36) if noise else (36 if wait==1 else 40)
            if wait!=1:return cost
            cost+=28 if noise else 64
    if not noise and state['vibratoDelay']:
        cost+=28
        wait=state['vibratoWait']
        cost+=28 if wait else 32
        if wait:
            cost+=36 if wait==1 else 40
            if wait!=1:return cost+portamento_cycles(index,state)
        direction=state['direction']
        cost+=64 if direction else 68
        cost+=48 if direction and (state['frequency']&255)+state['vibratoStep']>255 else 32
        cost+=80 if index==1 else 76
        if state['vibratoCounter']!=1:cost+=36
        else:
            cost+=32+(100 if state['vibratoHalf'] else 32)
        return cost+portamento_cycles(index,state)
    if not noise:cost+=32 # Disabled vibrato.
    counter=state['arpCounter']
    cost+=28 if counter else 32
    if counter:
        cost+=32 if counter==1 else 36
        if counter==1:
            down=state['direction']==255
            cost+=48 if down else 44
            cost+=(68 if down else 80) if noise else (84 if down else 80)
            return cost+(28 if noise else 200)
    return cost if noise else cost+portamento_cycles(index,state)

def music_tail_cycles(stereo, counter, direction):
    if not stereo:return 40
    if counter!=1:return 72
    return 248 if direction else 256

def voice_cycles(voice):
    i=voice['index'];s=voice['start']['state']
    if not s['active']&128:return 36
    fresh=s['remaining']==1
    cost=(108 if fresh else 72)+(32 if i>=4 else 0)
    if fresh:
        for f in voice['fetch']:
            c=command_cycles(f['operation'],f['args'],f['state']['loopCount'])
            if c<0:return -1
            cost+=c
        if 'note' in voice:
            f=voice['fetch'][-1]
            cost+=note_cycles(i,voice['note']['state'],f['args'],f['pointer'])
    if i==2:
        return cost if fresh else cost+16
    if 'envelope' not in voice:return cost
    return cost+envelope_cycles(i,voice['envelope']['state'])+output_cycles(i,voice['output']['state'])+modulation_cycles(i,voice['modulation']['state'])

def service_cycles(service):
    if not service['enabled']:return 60
    costs=[voice_cycles(v) for v in service['voices']]
    if any(c<0 for c in costs):return -1
    return 84+sum(costs)+92+music_tail_cycles(service['stereo'],service['stereoCounter'],service['stereoDirection'])
