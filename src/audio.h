#pragma once
#include <array>
#include <cstdint>
#include <string>
#include <unordered_map>
#include <vector>

namespace ticd {
// This is the game's identified music language, not CPU instructions.
enum class MusicOp { Note,LoopBegin,LoopEnd,Duration,Stop,Call,Return,Transpose,
    FineTune,Jump,Registers,Envelope,EnvelopeMode,Arpeggio,Portamento,Duty,
    Vibrato,NoTranspose,PitchDelay,Instrument,Gate,Release,Pan,StereoMotion,
    StopAll,Wave,WaveVolume,NoiseShort,NoiseLong };
struct MusicCommand { MusicOp op{};int next=0;std::vector<uint8_t> args; };
struct AudioAssets {
    std::array<int,256> frequencies{};
    std::array<uint8_t,16> initialWave{};
    std::array<std::array<int,4>,14> songs{};
    std::array<std::array<int,2>,26> effects{};
    std::unordered_map<int,MusicCommand> commands;
    std::unordered_map<int,std::vector<uint8_t>> instruments,waves;
    static int key(int voice,int position,bool fixed){return voice*131072+int(fixed)*65536+position;}
    static AudioAssets load(const std::wstring& path);
};
struct MusicVoice {
    bool active=false;
    int position=0,fixed=0,remaining=1,loopStart=0,loopCount=0;
    std::vector<int> returns;
    int transpose=0,noTranspose=0,fineTune=0,note=0,targetNote=0,frequency=0;
    int initialVolume=0,sustain=0,attack=0,decay=0,initialStage=0;
    int envelopeMode=0,stage=0,envelopeCounter=0,volume=0;
    int instrument=0,instrumentPeriod=0,tableIndex=0,gate=0,release=0,releaseCounter=0;
    int duty=0,noiseWidth=0;
    int arpAmount=0,arpUp=0,arpDown=0,arpCounter=0,direction=0,portamento=0;
    int vibratoDelay=0,vibratoStep=0,vibratoHalf=0,vibratoInitialDirection=0,vibratoWait=0,vibratoCounter=0;
    int pitchDelay=0,delayedFrequency=0,pitchWait=0;
    unsigned notes=0;
};
struct SoundChannel {
    int frequency=0,volume=0,duty=0,noise=0,waveShift=0;
    bool enabled=false;
    double timer=0;
    int phase=0,waveSample=0;
    uint16_t lfsr=0x7fff;
};
struct NativeAudio {
    const AudioAssets& assets;
    std::array<MusicVoice,6> voices{};
    std::array<SoundChannel,4> outputs{};
    std::array<uint8_t,32> wave{};
    int song=-1,pendingEffect=-1,routing=255,master=0x77;
    int stereoIndex=0,stereoDirection=0,stereoPeriod=0,stereoCounter=0;
    bool enabled=false;
    bool waveTrigger=true;
    uint64_t ticks=0,sampleRemainder=0;
    std::array<double,2> capacitor{};
    explicit NativeAudio(const AudioAssets& a):assets(a){}
    void playMusic(int index);
    void queueEffect(int index);
    void tick();
    void render(std::vector<int16_t>& stereo,int sampleRate=48000);
private:
    void startEffect(int index);
    void updateVoice(int index);
    void noteOn(int index,int note,int duration);
    void envelope(MusicVoice& voice);
    void modulation(int index);
    int noteFrequency(const MusicVoice& voice) const;
    void installWave(const std::vector<uint8_t>& bytes);
};
int runAudioTests(const AudioAssets& assets);
}
