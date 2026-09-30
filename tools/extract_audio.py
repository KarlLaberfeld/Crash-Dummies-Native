"""Extract identified music commands and instruments for the native sound driver.

No CPU code or general cartridge memory is included in the runtime package.
"""
from pathlib import Path
import argparse
import struct
from analyze_audio import analyze, music_roots
from extract import address, read_rom

OPERATIONS=['note','loop_begin','loop_end','fixed_duration','stop','call','return',
            'transpose','fine_tune','jump','registers','envelope','envelope_mode',
            'pitch_slide','note_hold','duty','vibrato','no_transpose',
            'pitch_modulation','instrument_table','gate','release','pan',
            'stereo_motion','stop_all','wave','wave_volume','noise_short','noise_long']

def extract_audio(rom,output):
    report=analyze(rom);commands={};instruments={};waves={}
    for group in ('songs','effects'):
        for track in report[group]:
            for channel in track['channels']:
                for command in channel['commands']:
                    commands[(channel['channel'],command['address'],command['fixed'])]=command
                    args=command['args']
                    if command['operation']=='wave':
                        pointer=args[0]+args[1]*256
                        waves[pointer]=rom[address(2,pointer):address(2,pointer)+16]
                    if command['operation']=='instrument_table':
                        pointer=args[1]+args[2]*256;data=bytearray();stops=0
                        # Hold marker then release tail: every identified envelope
                        # has two high-bit terminators. A >=16 loop marker is kept.
                        for pos in range(pointer,0x8000):
                            value=rom[address(2,pos)];data.append(value)
                            if value>=128:stops+=1
                            if stops==2:break
                        if stops!=2 or len(data)>256:raise ValueError('Invalid instrument envelope')
                        instruments[pointer]=data
    payload=bytearray(b'TICDAUD1')
    # The original uses byte-wrapped indices, including transposed silent notes
    # beyond the 97 musical entries. Store the resolved numeric lookup values.
    for index in range(256):payload+=struct.pack('<H',rom[0x3b1f+index]+256*rom[0x3abe+index])
    payload+=rom[0x36f7:0x3707]
    for roots in music_roots(rom):payload+=struct.pack('<4H',*roots)
    payload+=rom[0x37f3:0x385b]
    payload+=struct.pack('<H',len(commands))
    for (channel,pointer,fixed),command in sorted(commands.items()):
        args=command['args']
        payload+=struct.pack('<BHBBHB',channel,pointer,fixed,OPERATIONS.index(command['operation']),command['next_address'],len(args))+bytes(args)
    for collection in (instruments,waves):
        payload+=struct.pack('<H',len(collection))
        for pointer,data in sorted(collection.items()):payload+=struct.pack('<HH',pointer,len(data))+data
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    (output/'audio.dat').write_bytes(payload)
    return dict(commands=len(commands),instruments=len(instruments),waves=len(waves),bytes=len(payload))

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('rom',type=Path)
    parser.add_argument('--out',type=Path,default=Path('build'));args=parser.parse_args()
    print(extract_audio(read_rom(args.rom),args.out))
