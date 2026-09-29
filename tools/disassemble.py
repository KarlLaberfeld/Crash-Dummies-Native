"""Offline SM83 disassembly helper. Does not execute cartridge instructions."""
from pathlib import Path
import argparse

REG = ['b','c','d','e','h','l','[hl]','a']
PAIR = ['bc','de','hl','sp']
COND = ['nz','z','nc','c']

def decode(data, offset, address):
    op = data[offset]
    n = data[offset+1] if offset+1 < len(data) else 0
    nn = n | ((data[offset+2] if offset+2 < len(data) else 0) << 8)
    x,y,z,p,q = op>>6,(op>>3)&7,op&7,(op>>4)&3,(op>>3)&1
    imm,word = f'${n:02x}',f'${nn:04x}'
    rel = f'${(address+2+(n if n<128 else n-256))&65535:04x}'
    if x == 0:
        if z == 0:
            return (
                (1,'nop') if y==0 else (3,f'ld [{word}],sp') if y==1 else (2,'stop') if y==2 else (2,f'jr {rel}') if y==3 else (2,f'jr {COND[y-4]},{rel}'))
        if z == 1: return (1,f'add hl,{PAIR[p]}') if q else (3,f'ld {PAIR[p]},{word}')
        if z == 2:
            r=['bc','de','hl+','hl-'][p]
            return 1, f'ld a,[{r}]' if q else f'ld [{r}],a'
        if z == 3: return 1,f'{"dec" if q else "inc"} {PAIR[p]}'
        if z == 4: return 1,f'inc {REG[y]}'
        if z == 5: return 1,f'dec {REG[y]}'
        if z == 6: return 2,f'ld {REG[y]},{imm}'
        return 1,['rlca','rrca','rla','rra','daa','cpl','scf','ccf'][y]
    if x == 1: return 1,'halt' if op==0x76 else f'ld {REG[y]},{REG[z]}'
    alu=['add a,','adc a,','sub ','sbc a,','and ','xor ','or ','cp ']
    if x == 2: return 1,alu[y]+REG[z]
    if z == 0:
        if y<4:return 1,'ret '+COND[y]
        return [(2,f'ldh [$ff{n:02x}],a'),(2,f'add sp,{imm}'),(2,f'ldh a,[$ff{n:02x}]'),(2,f'ld hl,sp+{imm}')][y-4]
    if z == 1:
        if not q:return 1,'pop '+['bc','de','hl','af'][p]
        return 1,['ret','reti','jp hl','ld sp,hl'][p]
    if z == 2:
        if y<4:return 3,f'jp {COND[y]},{word}'
        return [(1,'ld [$ff00+c],a'),(3,f'ld [{word}],a'),(1,'ld a,[$ff00+c]'),(3,f'ld a,[{word}]')][y-4]
    if z == 3:
        if y==0:return 3,f'jp {word}'
        if y==1:
            a,b,c=n>>6,(n>>3)&7,n&7
            return 2, (['rlc ','rrc ','rl ','rr ','sla ','sra ','swap ','srl '][b]+REG[c]) if a==0 else f'{["","bit","res","set"][a]} {b},{REG[c]}'
        if y in (6,7):return 1,'di' if y==6 else 'ei'
    if z == 4 and y<4:return 3,f'call {COND[y]},{word}'
    if z == 5:
        if not q:return 1,'push '+['bc','de','hl','af'][p]
        if p==0:return 3,f'call {word}'
    if z == 6:return 2,alu[y]+imm
    if z == 7:return 1,f'rst ${y*8:02x}'
    return 1,f'db ${op:02x}'

def listing(data, start, end):
    offset=start
    while offset<end:
        address=offset if offset<0x4000 else 0x4000+offset%0x4000
        length,text=decode(data,offset,address)
        yield f'{offset//0x4000:02x}:{address:04x} {data[offset:offset+length].hex(" "):8s} {text}'
        offset+=length

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('rom',type=Path)
    p.add_argument('--start',type=lambda s:int(s,0),default=0)
    p.add_argument('--end',type=lambda s:int(s,0))
    a=p.parse_args(); data=a.rom.read_bytes()
    print('\n'.join(listing(data,a.start,a.end or len(data))))
