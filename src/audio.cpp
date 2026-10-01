#include "audio.h"
#include <algorithm>
#include <cmath>
#include <cstdio>
#include <cstring>
#include <stdexcept>

namespace ticd {
namespace {
int byte(int value){return value&255;}
int hardware(int voice){return voice==4?0:voice==5?3:voice;}
struct Reader {
    std::vector<uint8_t> bytes;size_t at=0;
    explicit Reader(const std::wstring& path){
        FILE* f=_wfopen(path.c_str(),L"rb");if(!f)throw std::runtime_error("audio.dat is missing. Rebuild assets from the original ROM.");
        fseek(f,0,SEEK_END);long size=ftell(f);rewind(f);
        if(size<8||size>1024*1024){fclose(f);throw std::runtime_error("Invalid audio package size.");}
        bytes.resize(size);auto read=fread(bytes.data(),1,bytes.size(),f);fclose(f);if(read!=bytes.size())throw std::runtime_error("Cannot read audio package.");
    }
    int take(){if(at>=bytes.size())throw std::runtime_error("Truncated audio package.");return bytes[at++];}
    int word(){int lo=take();return lo+256*take();}
    std::vector<uint8_t> data(int size){std::vector<uint8_t> result;for(int i=0;i<size;++i)result.push_back(static_cast<uint8_t>(take()));return result;}
};
void require(bool valid){if(!valid)throw std::runtime_error("Invalid native audio data.");}
}
AudioAssets AudioAssets::load(const std::wstring& path){
    Reader r(path);auto magic=r.data(8);require(!memcmp(magic.data(),"TICDAUD1",8));AudioAssets a;
    for(auto& f:a.frequencies)f=r.word();for(auto& b:a.initialWave)b=static_cast<uint8_t>(r.take());
    for(auto& song:a.songs)for(auto& root:song)root=r.word();for(auto& effect:a.effects)for(auto& root:effect)root=r.word();
    int count=r.word();require(count>0&&count<16000);
    for(int i=0;i<count;++i){int voice=r.take(),position=r.word(),fixed=r.take(),op=r.take(),next=r.word(),size=r.take();
        require(voice<6&&fixed<2&&op<=int(MusicOp::NoiseLong)&&size<=128);MusicCommand command{static_cast<MusicOp>(op),next,r.data(size)};
        require(a.commands.emplace(key(voice,position,fixed!=0),std::move(command)).second);}
    for(auto* collection:{&a.instruments,&a.waves}){int n=r.word();require(n<128);for(int i=0;i<n;++i){int pointer=r.word(),size=r.word();require(size>0&&size<=256);require(collection->emplace(pointer,r.data(size)).second);}}
    require(r.at==r.bytes.size());return a;
}
void NativeAudio::installWave(const std::vector<uint8_t>& bytes){
    require(bytes.size()==16);for(int i=0;i<16;++i){wave[i*2]=bytes[i]>>4;wave[i*2+1]=bytes[i]&15;}
    waveDac=true; // 02:51de re-enables the wave DAC after copying its data.
    outputs[2].enabled=true;outputs[2].phase=0;outputs[2].timer=2*(2048-(outputs[2].frequency&2047));
}
void NativeAudio::playMusic(int index){
    if(index<0||index>=14)throw std::invalid_argument("Invalid original song index.");
    voices={};outputs={};song=index;pendingEffect=-1;routing=255;master=0x77;enabled=true;waveTrigger=true;waveDac=true;
    stereoIndex=stereoDirection=stereoPeriod=stereoCounter=0;capacitor={};
    for(int i=0;i<16;++i){wave[i*2]=assets.initialWave[i]>>4;wave[i*2+1]=assets.initialWave[i]&15;}
    for(int i=0;i<4;++i){voices[i].active=true;voices[i].position=assets.songs[index][i];}
}
void NativeAudio::stop(){voices={};outputs={};pendingEffect=-1;song=-1;enabled=false;capacitor={};}
void NativeAudio::setPaused(bool value){
    if(value&&!paused){outputs={};outputs[2].waveShift=4;waveDac=false;capacitor={};} // 148f powers off the output channels.
    paused=value; // 1485/1488 suspend the music driver, retaining software voices.
}
void NativeAudio::queueEffect(int index){if(index<0||index>=26)throw std::invalid_argument("Invalid original effect index.");pendingEffect=index;}
void NativeAudio::startEffect(int index){
    // 00:3714 resets only selected effect parameters; envelope/duty remain until
    // the effect stream replaces them. An absent root leaves that voice alone.
    for(int i=0;i<2;++i)if(int root=assets.effects[index][i]){auto& v=voices[4+i];v.position=root;v.active=true;v.fixed=0;v.remaining=1;
        v.arpAmount=v.arpUp=v.arpDown=0;
        if(i==0){v.transpose=0;v.portamento=0;v.vibratoDelay=v.vibratoStep=v.vibratoHalf=v.vibratoInitialDirection=0;}}
}
int NativeAudio::noteFrequency(const MusicVoice& v) const {
    if(v.note<0||v.note>=int(assets.frequencies.size()))throw std::runtime_error("Music note leaves identified frequency table.");
    return (assets.frequencies[v.note]+v.fineTune)&65535;
}
void NativeAudio::noteOn(int index,int note,int duration){
    auto& v=voices[index];auto& out=outputs[hardware(index)];bool noise=index==3||index==5;
    v.remaining=duration;++v.notes;
    if(noise)v.frequency=((note<<4)|(note>>4)|v.noiseWidth)&255;
    else{
        bool skip=v.noTranspose&&byte(v.noTranspose+1)==0;if(v.noTranspose)v.noTranspose=byte(v.noTranspose+1);
        int value=byte(note+(skip?0:v.transpose));
        if(v.portamento)v.targetNote=value;else v.note=value;
        v.frequency=noteFrequency(v);
    }
    v.arpCounter=byte(v.arpUp+1);v.direction=0;
    if(!noise&&v.vibratoDelay){v.vibratoWait=v.vibratoDelay;v.vibratoCounter=v.vibratoHalf;v.direction=v.vibratoInitialDirection;}
    if(index!=2&&v.envelopeMode){
        if(v.envelopeMode&128){v.releaseCounter=(v.gate&&v.gate<duration)?v.gate:v.release?byte(duration-v.release):0;
            v.envelopeCounter=1;v.tableIndex=0;v.stage=255;
        }else{v.stage=v.initialStage;v.envelopeCounter=v.stage==0?v.attack:v.stage==1?v.decay:v.sustain;v.volume=v.initialVolume;}
    }
    out.frequency=v.frequency;out.enabled=index!=2||waveDac;
    if(v.pitchDelay){v.pitchWait=v.pitchDelay;out.frequency=v.delayedFrequency;}
    if(index==2){if(waveTrigger){out.phase=0;out.timer=2*(2048-(out.frequency&2047));waveTrigger=false;}}
    else if(noise){out.volume=15;out.noise=out.frequency;out.lfsr=0x7fff;out.timer=0;}
    else out.timer=4*(2048-(out.frequency&2047));
}
void NativeAudio::envelope(MusicVoice& v){
    if(v.stage&128){
        if(v.releaseCounter&&--v.releaseCounter==0){v.envelopeCounter=1;v.tableIndex=byte(v.tableIndex+1);}
        v.envelopeCounter=byte(v.envelopeCounter-1);if(v.envelopeCounter)return;
        const auto& table=assets.instruments.at(v.instrument);require(v.tableIndex<int(table.size()));int value=table[v.tableIndex];
        if(value&128)return;
        if(value>=16){v.tableIndex=0;value=table[0];}
        v.volume=value;v.envelopeCounter=v.instrumentPeriod;v.tableIndex=byte(v.tableIndex+1);return;
    }
    if(v.stage>1)return;
    v.envelopeCounter=byte(v.envelopeCounter-1);if(!(v.envelopeCounter&128))return;
    if(v.stage==0){v.envelopeCounter=v.attack;v.volume=byte(v.volume+1);if(v.volume==15){v.stage=1;v.envelopeCounter=v.decay;}}
    else{v.envelopeCounter=v.decay;if(v.volume==v.sustain){v.stage=2;return;}v.volume=byte(v.volume-1);if(v.volume&128)v.stage=2;}
}
void NativeAudio::modulation(int index){
    auto& v=voices[index];auto& out=outputs[hardware(index)];bool noise=index==3||index==5;
    if(v.pitchDelay&&v.pitchWait){if(--v.pitchWait)return;out.frequency=v.frequency;if(noise)out.noise=v.frequency;}
    bool newNote=false;
    if(!noise&&v.vibratoDelay){
        if(!v.vibratoWait||--v.vibratoWait==0){v.frequency=(v.frequency+(v.direction?v.vibratoStep:-v.vibratoStep))&65535;out.frequency=v.frequency;
            v.vibratoCounter=byte(v.vibratoCounter-1);if(!v.vibratoCounter&&v.vibratoHalf){v.vibratoCounter=byte(v.vibratoHalf*2);v.direction^=255;}}
    }else if(v.arpCounter&&--v.arpCounter==0){
        v.direction^=255;v.arpCounter=v.direction?v.arpUp:v.arpDown;
        int delta=v.direction?v.arpAmount:-v.arpAmount;
        if(noise){v.frequency=byte(v.frequency+delta);out.noise=v.frequency;return;}
        v.note=byte(v.note+delta);newNote=true;
    }
    if(!noise&&!newNote&&v.portamento&&v.note!=v.targetNote){v.note=v.note<v.targetNote?std::min(v.targetNote,v.note+v.portamento):std::max(v.targetNote,v.note-v.portamento);newNote=true;}
    if(newNote){v.frequency=noteFrequency(v);out.frequency=v.frequency;out.timer=4*(2048-(out.frequency&2047));}
}
void NativeAudio::updateVoice(int index){
    auto& v=voices[index];if(!v.active)return;int channel=hardware(index);auto& out=outputs[channel];
    if(index>=4)routing|=index==4?0x11:0x88;
    v.remaining=byte(v.remaining-1);
    if(!v.remaining){
        bool played=false;
        for(int guard=0;guard<2048&&!played;++guard){
            auto found=assets.commands.find(AudioAssets::key(index,v.position,v.fixed!=0));
            if(found==assets.commands.end())throw std::runtime_error("Music command missing from identified graph.");
            const auto& c=found->second;auto arg=[&](size_t n){return int(c.args.at(n));};v.position=c.next;
            switch(c.op){
            case MusicOp::Note:noteOn(index,arg(0),v.fixed?v.fixed:arg(1));played=true;break;
            case MusicOp::LoopBegin:v.loopCount=arg(0);v.loopStart=c.next;break;
            case MusicOp::LoopEnd:v.loopCount=byte(v.loopCount-1);if(v.loopCount)v.position=v.loopStart;break;
            case MusicOp::Duration:v.fixed=arg(0);break;
            case MusicOp::Stop:v.active=false;return;
            case MusicOp::Call:if(v.returns.size()>=3)throw std::runtime_error("Music call depth exceeds original slots.");v.returns.push_back(c.next);v.position=arg(0)+256*arg(1);break;
            case MusicOp::Return:if(v.returns.empty())throw std::runtime_error("Music return without call.");v.position=v.returns.back();v.returns.pop_back();break;
            case MusicOp::Jump:v.position=arg(0)+256*arg(1);break;
            case MusicOp::Transpose:v.transpose=arg(0);break;
            case MusicOp::FineTune:v.fineTune=arg(0);break;
            case MusicOp::Envelope:v.initialVolume=arg(0)>>4;v.sustain=arg(0)&15;v.attack=arg(1)>>4;v.decay=arg(1)&15;v.initialStage=arg(2);break;
            case MusicOp::EnvelopeMode:v.envelopeMode=arg(0);break;
            case MusicOp::Arpeggio:v.arpAmount=arg(0);v.arpUp=arg(1);v.arpDown=arg(2);break;
            case MusicOp::Portamento:v.portamento=arg(0);break;
            case MusicOp::Duty:v.duty=arg(0);break;
            case MusicOp::Vibrato:v.vibratoDelay=arg(0);v.vibratoStep=arg(1);v.vibratoHalf=arg(2);v.vibratoInitialDirection=arg(3);break;
            case MusicOp::NoTranspose:v.noTranspose=255;break;
            case MusicOp::PitchDelay:v.pitchDelay=arg(0);v.delayedFrequency=arg(1)+256*arg(2);break;
            case MusicOp::Instrument:v.instrumentPeriod=arg(0);v.instrument=arg(1)+256*arg(2);v.envelopeMode=255;break;
            case MusicOp::Gate:v.gate=arg(0);break;
            case MusicOp::Release:v.release=arg(0);break;
            case MusicOp::Pan:{int value=arg(0);require(value<4);routing=(routing&~(0x11<<channel))|(((value&1)|((value&2)<<3))<<channel);break;}
            case MusicOp::Wave:installWave(assets.waves.at(arg(0)+256*arg(1)));break;
            case MusicOp::WaveVolume:require(arg(0)<4);out.waveShift=arg(0)==0?4:3-arg(0);break;
            case MusicOp::NoiseShort:v.noiseWidth=8;break;
            case MusicOp::NoiseLong:v.noiseWidth=0;break;
            case MusicOp::StopAll:enabled=false;for(auto& voice:voices)voice.active=false;for(auto& output:outputs)output.enabled=false;return;
            // These commands do not occur in the documented cartridge streams.
            // Reject unsupported data instead of silently inventing behavior.
            case MusicOp::Registers:case MusicOp::StereoMotion:throw std::runtime_error("Unimplemented optional music command.");
            }
        }
        if(!played)throw std::runtime_error("Music stream failed to yield a note.");
    }
    // The wave modulation block is bypassed by the original jump at 02:46e3.
    if(index==2)return;
    envelope(v);
    if(channel==3){if(out.volume!=(v.volume&15)){out.volume=v.volume&15;out.noise=v.frequency;out.lfsr=0x7fff;out.timer=0;}}
    else{out.volume=v.volume&15;out.duty=v.duty>>6;out.frequency=v.frequency;out.timer=4*(2048-(out.frequency&2047));}
    modulation(index);
}
void NativeAudio::tick(){
    if(paused)return;
    if(pendingEffect>=0){startEffect(pendingEffect);pendingEffect=-1;}
    if(enabled)for(int i=0;i<6;++i)updateVoice(i);
    ++ticks;
}
void NativeAudio::render(std::vector<int16_t>& stereo,int sampleRate){
    if(sampleRate<8000||sampleRate>192000)throw std::invalid_argument("Invalid audio sample rate.");
    // One original video update is 70,224 oscillator cycles. Carry the sample
    // fraction so pitch and track duration do not drift across buffers.
    sampleRemainder+=uint64_t(sampleRate)*70224;int count=int(sampleRemainder/4194304);sampleRemainder%=4194304;
    stereo.resize(count*2);double cycles=4194304.0/sampleRate,charge=std::pow(.999958,cycles);
    if(paused){std::fill(stereo.begin(),stereo.end(),0);return;}
    constexpr int dutyBits[]={0x80,0x81,0xe1,0x7e};
    for(int sample=0;sample<count;++sample){double mixed[2]={0,0};
        for(int c=0;c<4;++c){auto& out=outputs[c];if(!enabled||!out.enabled)continue;
            int period=c<2?4*(2048-(out.frequency&2047)):c==2?2*(2048-(out.frequency&2047)):((out.noise&7)?(out.noise&7)*16:8)<<(out.noise>>4);
            // Integrate every waveform edge over the output sample. Point
            // sampling produces severe aliasing for the original high notes.
            double remaining=cycles,total=0;
            bool clocked=c!=3||(out.noise>>4)<14;
            while(remaining>0){
                if(clocked&&out.timer<=0){out.timer+=period;
                    if(c==3){int bit=(out.lfsr^(out.lfsr>>1))&1;out.lfsr=static_cast<uint16_t>((out.lfsr>>1)|(bit<<14));if(out.noise&8)out.lfsr=static_cast<uint16_t>((out.lfsr&~64)|(bit<<6));}
                    else{out.phase=(out.phase+1)&(c==2?31:7);if(c==2)out.waveSample=wave[out.phase];}}
                double interval=clocked?std::min(remaining,out.timer):remaining;
                int digital=c<2?((dutyBits[out.duty&3]>>out.phase)&1)*out.volume:c==2?(out.waveSample>>out.waveShift):((~out.lfsr)&1)*out.volume;
                total+=digital*interval;remaining-=interval;if(clocked)out.timer-=interval;
            }
            double value=1.0-total/(cycles*7.5);
            if(routing&(1<<(c+4)))mixed[0]+=value;if(routing&(1<<c))mixed[1]+=value;
        }
        for(int side=0;side<2;++side){double value=mixed[side]*(((master>>(side==0?4:0))&7)+1)/8.;double filtered=value-capacitor[side];capacitor[side]=value-filtered*charge;
            stereo[sample*2+side]=static_cast<int16_t>(std::clamp(filtered*6000.,-32768.,32767.));}
    }
}
}
