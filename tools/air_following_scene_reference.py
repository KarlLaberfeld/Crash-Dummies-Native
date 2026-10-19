"""Original comparison for restarted Air scene/placement completion interrupts.

The native clock selects operations from game state. Observed return addresses
here constrain comparison scope only; they are never native scheduling inputs.
"""
from air_following_gameplay_reference import analyze as analyze_first,ORDER,TERMINAL_ORDER
from extract_air import HANDLERS
from air_timing import vblank_work,VBLANK_FIXED,vblank_bookkeeping_work


def scene_owner(block,irq):
    phase=next((i for i in range(9) if block[i]['cycles']<irq['start']<block[i+1]['cycles']),None)
    pc=irq['returnAddress'];ready=irq['ready']
    terminal=block[-1]['name']=='terminalEnd'
    if phase==8:
        if terminal:
            if pc==0x261d and ready==0:return 2
            if pc==0x2617 and ready==0:return 1
            raise ValueError('Unknown terminal counter-wait completion')
        if pc==0x261d and ready==1:return 2
        if (pc==0x03c9 and ready==0) or (pc in (0x03cb,0x2617) and ready==1):return 1
        raise ValueError('Unknown following wait-prefix completion')
    if phase==7:
        if pc in ((0x03fd,0x03fe,0x0400) if terminal else (0x03fd,0x03fe,0x03c7)) and ready==0:return 1
        raise ValueError('Unknown following result-test completion')
    if ready!=0:raise ValueError('Scene interrupt opened the resource gate')
    # Identified source helpers represented by airSprite/Map/PlacementClock.
    ranges={3:((0x1bfb,0x1d3f),(0x23dd,0x241d),(0x03e7,0x03e7)),
            4:((0x1b90,0x1bfa),(0x03ea,0x03ed)),
            5:((0x1ead,0x1f16),),6:((0x19a2,0x1b02),(0x03fa,0x03fa))}
    if phase not in ranges or not any(a<=pc<=b for a,b in ranges[phase]):
        raise ValueError('Interrupt outside identified following scene completion')
    if irq['kind']=='vblank' and phase==5 and pc!=0x1f16:
        raise ValueError('Display during partial row preparation needs a row-storage owner')
    return 1


def analyze(data):
    points=data.get('points',[]);irqs=data.get('interrupts',[]);n=data.get('updates',0)
    if data.get('busyScenes') is not True or data.get('version')!=1 or type(n) is not int or n<2 or len(points)!=10*n or data.get('precedingDisplays',-1)<0:
        raise ValueError('Incomplete following scene extent/scope')
    first_irqs=[r for r in irqs if points[0]['cycles']<r['start']<points[9]['cycles']]
    analyze_first(dict(data,updates=1,points=points[:10],interrupts=first_irqs))
    cursor=0;services=[];nonwait=0;counts={'stat':0,'vblank':0}
    for update in range(n):
        block=points[10*update:10*(update+1)]
        terminal=data.get('terminalWait') is True and update==n-1
        if [p['name'] for p in block]!=(TERMINAL_ORDER if terminal else ORDER) or any(b['cycles']<=a['cycles'] for a,b in zip(block,block[1:])):raise ValueError('Reordered following scene boundaries')
        if data.get('terminalWait') is True:
            for i,p in enumerate(block):
                value=p.get('result')
                # Terminal actor completion must own the newly set bit.
                if type(value) is not int or not 0<=value<=255 or (not value&1 if terminal and i>=2 else value!=0):
                    raise ValueError('Unowned terminal result publication')
            if terminal and any(p['result']!=block[2]['result'] for p in block[2:]):raise ValueError('Terminal result changed after actor completion')
        if update and dict(block[0],name='end')!=points[10*update-1]:raise ValueError('Detached following scene update')
        if block[1]['cycles']-block[0]['cycles']!=96:raise ValueError('Unknown following saved-player work')
        local=[]
        while cursor<len(irqs) and irqs[cursor]['start']<block[-1]['cycles']:
            r=irqs[cursor];cursor+=1
            if r['kind'] not in counts or not block[0]['cycles']<r['start']<r['end']<block[-1]['cycles'] or r['selector']!=4 or r['display']!=4:
                raise ValueError('Incomplete following scene interrupt')
            if local and r['start']<=local[-1]['end']+16:raise ValueError('Overlapping following scene interrupts')
            owner=scene_owner(block,r);nonwait+=owner==1;counts[r['kind']]+=1
            if r['kind']=='stat' and r['end']-r['start']!=288:raise ValueError('Unknown scene STAT work')
            local.append(r)
        if not local or local[-1]['kind']!='vblank' or local[-1]['returnAddress']!=0x261d or local[-1]['ready']!=int(not terminal):
            raise ValueError('Following scene lacks its completed final counter wait')
        result_interrupts=sum(20+r['end']-r['start']+16 for r in local if block[7]['cycles']<r['start']<block[8]['cycles'])
        if block[8]['cycles']-block[7]['cycles']!=(28 if terminal else 32)+result_interrupts:raise ValueError('Unknown following result-test work')
        if block[-1]['cycles']!=local[-1]['end']+(72 if terminal else 120):raise ValueError('Unknown following scene input gate')
        prior_input=block[0]['held'];tick=block[0]['tick'];lcd=block[0]['lcdc'];pending=block[2]['effect'];taken=0
        for i,p in enumerate(block):
            while taken<len(local) and local[taken]['end']<p['cycles']:
                r=local[taken];taken+=1
                if p['cycles']<r['end']+16:raise ValueError('Scene boundary precedes interrupt return completion')
                if r['kind']=='stat':lcd&=~2;continue
                work=vblank_work(r);fixed={**VBLANK_FIXED,'bookkeeping':vblank_bookkeeping_work(r['resetEnabled'],r['held'],r['resetLatched'])}
                if len(r.get('oam',[]))!=160 or any(type(v) is not int or not 0<=v<=255 for v in r['oam']):raise ValueError('Incomplete scene sprite publication')
                if r['tick']!=tick or r['pressed']!=r['held']&~prior_input or r['effectRequest']!=pending or work['effects']<64 or not r['musicEnabled'] or work['music']<60 or any(work[k]!=v for k,v in fixed.items()):
                    raise ValueError('Unknown following scene input/audio/counter work')
                services.append(r);prior_input=r['held'];tick=(tick+1)&65535;lcd|=2;pending=-1
            if taken<len(local) and local[taken]['start']<=p['cycles']<=local[taken]['end']:raise ValueError('Source boundary inside an interrupt body')
            input_irq=next((r for r in reversed(local[:taken]) if r['kind']=='vblank'),None)
            held=input_irq['held'] if input_irq else block[0]['held'];pressed=input_irq['pressed'] if input_irq else block[0]['pressed']
            effect=block[0]['effect'] if i<2 else pending
            if p['ready'] or p['display']!=4 or p['lcdc']!=lcd or p['tick']!=tick or p['held']!=held or p['pressed']!=pressed or p['effect']!=effect or not -1<=effect<26:
                raise ValueError('Following scene publication/counter/input state differs from its services')
            if p['held']&15==15 or p['pressed']&~p['held'] or p['pressed']&8 and not(update==0 and i<9 and data.get('entryPauseConsumed') is True):raise ValueError('Unowned scene pause/reset input')
            if not 0<=p['secondTicks']<60 or not 0<=p['seconds']<=99 or len(p['entities'])!=16:raise ValueError('Incomplete scene timer/actors')
            if any(e['frame']!=255 and(e['handler'] not in HANDLERS or len(e['params'])!=7) for e in p['entities']):raise ValueError('Unknown scene actor')
    if cursor!=len(irqs) or not nonwait or counts['stat']!=counts['vblank']:raise ValueError('Incomplete following scene vector coverage')
    return services


def compare_publications(data,rows):
    from air_clock_compare import compare_sprites
    services=analyze(data)
    if len(rows)!=40*len(services):raise ValueError('Incomplete native scene sprite publication')
    normalized=[]
    for index,row in enumerate(rows):
        if row['service']!=data['precedingDisplays']+index//40 or row['slot']!=index%40:
            raise ValueError('Detached/reordered native scene sprite publication')
        normalized.append(dict(row,service=index//40))
    return compare_sprites(services,normalized,expected_services=len(services))
