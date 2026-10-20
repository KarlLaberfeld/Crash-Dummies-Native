#pragma once
#include "audio.h"

namespace ticd {
// Source T-cycle sums for the identified music language. These functions use
// semantic voice state; no opcodes, CPU registers or cartridge code are run.
inline int audioCommandWork(MusicOp op,int loopCount=0,int firstArg=0,int argCount=0){
    switch(op){
    case MusicOp::Note:return 28;
    case MusicOp::LoopBegin:return 168;
    case MusicOp::LoopEnd:return loopCount==1?124:172;
    case MusicOp::Duration:case MusicOp::Stop:case MusicOp::Transpose:case MusicOp::FineTune:
    case MusicOp::EnvelopeMode:case MusicOp::Portamento:case MusicOp::Duty:
    case MusicOp::Gate:case MusicOp::Release:return 132;
    case MusicOp::Call:return 220;
    case MusicOp::Return:return 200;
    case MusicOp::Jump:return 136;
    case MusicOp::Envelope:return 292;
    case MusicOp::Arpeggio:case MusicOp::PitchDelay:return 196;
    case MusicOp::Vibrato:return 228;
    case MusicOp::NoTranspose:return 124;
    case MusicOp::Instrument:case MusicOp::Pan:return 212;
    case MusicOp::WaveVolume:return 192;
    case MusicOp::Wave:return 832;
    case MusicOp::NoiseShort:return 136;
    case MusicOp::NoiseLong:return 120;
    case MusicOp::StopAll:return 240;
    case MusicOp::Registers:return argCount>0&&argCount%2?124+100*((argCount-1)/2):-1;
    case MusicOp::StereoMotion:return firstArg?276:228;
    }
    return -1;
}
inline int audioEnvelopeWork(int index,const MusicVoice& v,int tableValue=-1,int tableNext=-1){
    if(index==2)return -1;
    int stage=v.stage,counter=v.envelopeCounter,volume=v.volume;
    bool noise=index==3||index==5;
    if(stage&128){
        int cost=36,release=v.releaseCounter;
        cost+=release?28:32;
        if(release){cost+=release==1?32:36;if(release==1){counter=1;cost+=48;}}
        cost+=counter==1?32:36;
        if(counter!=1)return cost;
        int value=release==1?tableNext:tableValue;
        if(value<0)return -1;
        // Both noise voices test bit 7 in A (8 cycles), whereas pulse
        // voices test [HL] (12). The lookup itself is otherwise shared.
        cost+=(index==3||index==5)?84:88;
        if(value&128)return cost+12;
        cost+=8;
        cost+=value<16?20:16+((index==0||index==4)?64:60);
        return cost+72;
    }
    int cost=32+(stage==0?12:16);
    if(stage==0){
        cost+=((counter-1)&128)?48:52;
        if(!((counter-1)&128))return cost;
        cost+=32+(noise?40:32);volume=(volume+1)&255;
        cost+=volume==15?24:28;if(volume!=15)return cost;
        cost+=noise?68:!v.decay?68:72;
        if(noise||v.decay)return cost;
        // CP 1 sees the zero decay in A, so the following branch is taken.
        return cost+(index==1?24:28);
    }
    cost+=index==1?(stage==1?20:24):(stage==1?24:28);
    if(stage!=1)return cost;
    cost+=index==1?(((counter-1)&128)?48:52):(((counter-1)&128)?44:48);
    if(!((counter-1)&128))return cost;
    cost+=68+(noise?4:0);
    if(volume==v.sustain)return cost+12+40;
    return cost+8+(((volume-1)&128)?84:48);
}
inline int audioNoteWork(int index,const MusicVoice& v,int note,int duration,int pointer){
    bool noise=index==3||index==5;int cost=48;
    if(noise)cost+=48;
    else{
        cost+=v.noTranspose==0?68:v.noTranspose==255?80:96;
        cost+=4+(v.portamento?68:32)+20+((index==0||index==4)?124:120);
    }
    cost+=v.fixed?32:88;cost+=index==2?20:16;
    int size=v.fixed?1:2;cost+=((pointer&255)+size>255)?56:48;cost+=44;
    if(noise)cost+=20;
    else cost+=index==2?(v.vibratoDelay?108:48):(v.vibratoDelay?112:52);
    if(index!=2){
        int mode=v.envelopeMode;cost+=mode?28:32;
        if(mode){
            if(mode&128){
                cost+=index==1?16:20;cost+=v.gate?28:32;
                bool selected=v.gate&&v.gate<duration;
                if(v.gate)cost+=selected?32:28;
                if(!selected){cost+=noise?(v.release?28:32):(v.release?32:36);if(v.release)cost+=40;}
                cost+=noise?112:index==1?108:104;
            }else cost+=(index==1?20:24)+(noise?132:116);
        }
    }
    if(noise){int frequency=((note<<4)|(note>>4)|v.noiseWidth)&255;
        cost+=frequency?24+(v.pitchDelay?76:44):28;cost+=80;
    }else if(index==2)cost+=(v.pitchDelay?104:68)+92;
    else cost+=(v.pitchDelay?(index==1?104:100):84)+20;
    return cost;
}
inline int audioOutputWork(int index,const MusicVoice& v,int hardwareVolume){
    if(index==0||index==1||index==4)return 172;
    if(index==3||index==5)return (v.volume&15)==hardwareVolume?84:136;
    return -1;
}
inline int audioPortamentoWork(int index,const MusicVoice& v){
    int step=v.portamento,note=v.note,target=v.targetNote;
    if(!step)return index==1?32:36;
    int cost=(index==1?28:32)+(note==target?48:44);
    if(note==target)return cost;
    if(note>target){
        cost+=8;int result=(note-step)&255;
        if(index==1)cost+=40+(result>=target?12:8+16+16);
        else{
            cost+=result==target?56:52;
            if(result==target){result=(result+step+1)&255;cost+=result<target?52:48+16;}
            else cost+=result>target?12:8+16+16;
        }
    }else{
        cost+=12;int result=(note+step)&255;
        if(index==1){cost+=44;cost+=result==target?12+16:result>target?8+12:8+8+16;}
        else cost+=result<target?52:48+16;
    }
    return cost+200;
}
inline int audioModulationWork(int index,const MusicVoice& v){
    if(index==2)return -1;
    bool noise=index==3||index==5;int cost=v.pitchDelay?28:32;
    if(v.pitchDelay){int wait=v.pitchWait;cost+=wait?28:32;
        if(wait){cost+=noise?(wait==1?32:36):(wait==1?36:40);if(wait!=1)return cost;cost+=noise?28:64;}}
    if(!noise&&v.vibratoDelay){
        cost+=28;int wait=v.vibratoWait;cost+=wait?28:32;
        if(wait){cost+=wait==1?36:40;if(wait!=1)return cost+audioPortamentoWork(index,v);}
        cost+=v.direction?64:68;
        cost+=v.direction&&(v.frequency&255)+v.vibratoStep>255?48:32;
        cost+=index==1?80:76;
        cost+=v.vibratoCounter!=1?36:32+(v.vibratoHalf?100:32);
        return cost+audioPortamentoWork(index,v);
    }
    if(!noise)cost+=32;
    int counter=v.arpCounter;cost+=counter?28:32;
    if(counter){cost+=counter==1?32:36;
        if(counter==1){bool down=v.direction==255;cost+=down?48:44;
            cost+=noise?(down?68:80):(down?84:80);return cost+(noise?28:200);}}
    return noise?cost:cost+audioPortamentoWork(index,v);
}
inline int audioMusicTailWork(int stereo,int counter,int direction){
    if(!stereo)return 40;if(counter!=1)return 72;return direction?248:256;
}
}
