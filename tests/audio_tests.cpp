#include "audio.h"
#include "audio_work.h"
#include "audio_music_work.h"
#include <algorithm>
#include <cstdio>
#include <stdexcept>

namespace ticd {
namespace {
void command(AudioAssets& a,int voice,int position,MusicOp op,int next,std::initializer_list<uint8_t> args,bool fixed=false){a.commands[AudioAssets::key(voice,position,fixed)]={op,next,args};}
AudioAssets fixture(){
    AudioAssets a;for(int i=0;i<256;++i)a.frequencies[i]=1000+i;
    for(auto& song:a.songs)song={1,1,1,1};for(int voice=0;voice<4;++voice)command(a,voice,1,MusicOp::Stop,2,{});return a;
}
void saveWave(const char* path,const std::vector<int16_t>& samples){
    FILE* f=fopen(path,"wb");if(!f)throw std::runtime_error("Cannot save local audio preview.");
    auto word=[&](uint16_t v){fputc(v&255,f);fputc(v>>8,f);};auto dword=[&](uint32_t v){word(v&65535);word(v>>16);};
    fwrite("RIFF",1,4,f);dword(36+static_cast<uint32_t>(samples.size()*2));fwrite("WAVEfmt ",1,8,f);dword(16);word(1);word(2);dword(48000);dword(192000);word(4);word(16);fwrite("data",1,4,f);dword(static_cast<uint32_t>(samples.size()*2));
    for(auto sample:samples)word(static_cast<uint16_t>(sample));fclose(f);
}
}
int runAudioTests(const AudioAssets& assets){
    FILE* log=fopen("audio-test.txt","w");if(!log)return 2;int assertions=0;
    auto check=[&](bool valid,const char* message){++assertions;if(!valid)throw std::runtime_error(message);};
    try{
        auto setup=fixture();setup.effects[0]={1,1};setup.effects[1]={1,0};setup.effects[2]={0,1};
        command(setup,4,1,MusicOp::Stop,2,{});command(setup,5,1,MusicOp::Stop,2,{});
        NativeAudio work(setup);work.measureWork=true;work.playMusic(0);work.tick();
        check(work.effectWorkCycles==64,"No pending effect pays only the original setup early return");
        for(int effect=0;effect<4;++effect){work.queueEffect(effect);work.tick();
            check(work.effectWorkCycles==(effect==0?620:effect==1?472:effect==2?368:220),"Only selected square/noise effect roots require voice initialization");}
        work.setPaused(true);work.queueEffect(0);work.tick();
        check(work.effectWorkCycles==-1&&work.pendingEffect==0,"Paused native sequencing cannot certify an original setup interval");
        work.setPaused(false);work.tick();check(work.effectWorkCycles==620&&work.pendingEffect==-1,"Resume consumes the retained request and accounts for both roots");
        check(work.musicWorkCycles==904&&work.voiceWorkCycles[4]==272&&work.voiceWorkCycles[5]==272,"Stopped music retains the entry-enabled voice scan and both fresh effect stops");
        work.stop();work.tick();check(work.musicWorkCycles==60,"Disabled driver uses the original early return");
        work.setPaused(true);work.tick();check(work.musicWorkCycles==-1,"Native pause does not certify an original driver call");
        check(audioCommandWork(MusicOp::LoopEnd,1)==124&&audioCommandWork(MusicOp::LoopEnd,2)==172,"Counted-loop completion and repetition have different source work");
        check(audioCommandWork(MusicOp::Registers,0,0,2)==-1&&audioCommandWork(MusicOp::Registers,0,0,5)==324,"Malformed register data cannot certify work");
        check(audioCommandWork(static_cast<MusicOp>(255))==-1,"Unknown music operation cannot certify work");
        check(audioCommandWork(MusicOp::NoiseShort)==136,"Noise-width command skips the other handler's XOR");
        check(audioMusicTailWork(0,1,0)==40&&audioMusicTailWork(1,2,0)==72&&audioMusicTailWork(1,1,0)==256&&audioMusicTailWork(1,1,255)==248,"Stereo-tail source branches remain distinct (synthetic evidence)");
        MusicVoice synthetic;synthetic.stage=128;synthetic.envelopeCounter=1;
        check(audioEnvelopeWork(0,synthetic)==-1,"Missing instrument lookup retains unknown work");
        check(audioEnvelopeWork(0,synthetic,255)==200,"Instrument hold returns before writing a new level");
        synthetic.releaseCounter=1;
        check(audioEnvelopeWork(0,synthetic,255,4)==364,"Release expiration uses the following instrument value");
        synthetic=MusicVoice{};synthetic.envelopeCounter=0;synthetic.volume=14;synthetic.sustain=0;
        check(audioEnvelopeWork(0,synthetic)==440&&audioEnvelopeWork(3,synthetic)==256,"Square attack can fall through into decay while noise retains INC flags");
        synthetic=MusicVoice{};
        check(audioNoteWork(0,synthetic,24,3,255)-audioNoteWork(0,synthetic,24,3,100)==8,"Note stream pointer carries independently of pitch");
        check(audioEnvelopeWork(2,synthetic)==-1&&audioModulationWork(2,synthetic)==-1,"Wave voice bypass cannot masquerade as a measured phase");
        auto modulationFixture=fixture();NativeAudio modulation(modulationFixture);modulation.playMusic(0);
        auto& arp=modulation.voices[1];arp.remaining=2;arp.stage=2;arp.note=39;arp.arpAmount=19;arp.arpCounter=1;arp.direction=255;
        auto& slide=modulation.voices[4];slide.active=true;slide.remaining=2;slide.stage=2;slide.note=2;slide.targetNote=1;slide.portamento=4;
        modulation.measureWork=true;modulation.tick();
        check(arp.note==20&&arp.frequency==1021,"Voice-one descending arpeggio includes the source low-byte ADC carry");
        check(slide.note==254&&slide.frequency==1254,"Effect portamento preserves original byte wrap instead of clamping");
        check(modulation.musicWorkCycles>=0&&modulation.voiceWorkCycles[1]>=0&&modulation.voiceWorkCycles[4]>=0,"Corrected modulation still exposes semantic source work");
        NativeAudio attackFallthrough(modulationFixture);attackFallthrough.playMusic(0);
        for(int i:{0,3}){auto& voice=attackFallthrough.voices[i];voice.remaining=2;voice.stage=0;voice.envelopeCounter=0;voice.volume=14;}
        attackFallthrough.tick();
        check(attackFallthrough.voices[0].volume==14&&attackFallthrough.voices[0].stage==1,"Square zero-decay attack falls through in the same call (source/synthetic)");
        check(attackFallthrough.voices[3].volume==15&&attackFallthrough.voices[3].stage==1,"Noise zero-decay attack returns before decrementing (source/synthetic)");
        check(audioEffectSetupWork(26,true,true)==-1,"Invalid effect index never reports a completed cost");
        NativeAudio measured(assets),unmeasured(assets);measured.measureWork=true;
        measured.playMusic(1);unmeasured.playMusic(1);std::vector<int16_t> measuredPcm,unmeasuredPcm;
        bool sameWorkAudio=true;
        for(int frame=0;frame<240;++frame){
            if(frame%40==0){measured.queueEffect(frame/40);unmeasured.queueEffect(frame/40);}
            measured.tick();unmeasured.tick();measured.render(measuredPcm);unmeasured.render(unmeasuredPcm);
            sameWorkAudio&=measuredPcm==unmeasuredPcm;
        }
        check(sameWorkAudio,"Optional effect work accounting preserves PCM through music and overlapping effects");
        auto a=fixture();
        command(a,0,1,MusicOp::Envelope,2,{0x40,1,1});command(a,0,2,MusicOp::EnvelopeMode,3,{1});
        command(a,0,3,MusicOp::Note,4,{24,3});command(a,0,4,MusicOp::Note,5,{25,0});command(a,0,5,MusicOp::Stop,6,{});
        NativeAudio n(a);n.playMusic(0);n.tick();check(n.voices[0].notes==1&&n.voices[0].volume==4,"Envelope starts at four and waits its first decay tick");
        n.tick();check(n.voices[0].volume==3,"Software decay decrements after period underflow");n.tick();check(n.voices[0].notes==1,"Three-update note retains its full duration");n.tick();
        check(n.voices[0].notes==2&&n.voices[0].remaining==0,"Zero-length byte starts a 256-update note");
        for(int i=0;i<255;++i)n.tick();check(n.voices[0].active,"Zero duration does not terminate one update early");n.tick();check(!n.voices[0].active,"Zero duration ends after 256 updates");

        NativeAudio suspended(a);suspended.playMusic(0);suspended.tick();suspended.setPaused(true);
        std::vector<int16_t> silence;uint64_t silentFrames=0;bool zero=true;
        for(int i=0;i<120;++i){suspended.tick();suspended.render(silence);silentFrames+=silence.size()/2;for(int sample:silence)zero&=sample==0;}
        check(zero&&silentFrames==uint64_t(120)*48000*70224/4194304,"Pause submits silence at the continuing device sample rate");
        check(suspended.ticks==1&&suspended.voices[0].notes==1&&suspended.voices[0].remaining==3&&suspended.voices[0].volume==4,"Pause freezes note duration, sequence and software envelope");
        check(!suspended.outputs[0].enabled&&suspended.musicPlaying(),"Power-off clears output channels without discarding software song state");
        suspended.setPaused(false);suspended.tick();
        check(suspended.voices[0].notes==1&&suspended.voices[0].remaining==2&&suspended.voices[0].volume==3,"Resume continues the retained note and envelope instead of restarting the song");
        suspended.tick();suspended.tick();check(suspended.voices[0].notes==2&&suspended.outputs[0].enabled,"Next note retriggers output after pause power-off");
        NativeAudio effectPause(assets);effectPause.playMusic(1);effectPause.queueEffect(1);effectPause.tick();
        auto savedEffect=effectPause.voices[4];effectPause.setPaused(true);effectPause.queueEffect(2);effectPause.tick();
        check(effectPause.voices[4].position==savedEffect.position&&effectPause.voices[4].remaining==savedEffect.remaining&&effectPause.pendingEffect==2,"Pause retains active effects and does not consume pending requests");
        effectPause.setPaused(false);effectPause.tick();check(effectPause.pendingEffect==-1,"Resume processes the retained effect request");

        auto waveFixture=fixture();waveFixture.waves[100]=std::vector<uint8_t>(16,0x1f);
        command(waveFixture,2,1,MusicOp::Wave,2,{100,0});command(waveFixture,2,2,MusicOp::WaveVolume,3,{1});
        command(waveFixture,2,3,MusicOp::Note,4,{24,1});command(waveFixture,2,4,MusicOp::Note,5,{25,1});
        command(waveFixture,2,5,MusicOp::Wave,6,{100,0});command(waveFixture,2,6,MusicOp::WaveVolume,7,{1});
        command(waveFixture,2,7,MusicOp::Note,8,{26,1});command(waveFixture,2,8,MusicOp::Stop,9,{});
        NativeAudio wavePause(waveFixture);wavePause.playMusic(0);wavePause.tick();auto waveData=wavePause.wave;
        wavePause.setPaused(true);check(wavePause.wave==waveData&&!wavePause.waveDac&&wavePause.outputs[2].waveShift==4,"Pause preserves wave data but clears its DAC enable and volume");
        wavePause.setPaused(false);wavePause.tick();check(!wavePause.outputs[2].enabled,"A wave note alone cannot re-enable the DAC cleared by pause");
        wavePause.tick();check(wavePause.outputs[2].enabled&&wavePause.outputs[2].waveShift==2,"Later wave upload and volume command restore the wave output");

        auto b=fixture();command(b,0,1,MusicOp::Instrument,2,{1,100,0});b.instruments[100]={4,255,2,0,255};
        command(b,0,2,MusicOp::Gate,3,{3});command(b,0,3,MusicOp::Note,4,{24,8});command(b,0,4,MusicOp::Stop,5,{});
        NativeAudio e(b);e.playMusic(0);e.tick();check(e.voices[0].volume==4,"Instrument envelope reads first level on note tick");e.tick();check(e.voices[0].volume==4,"Instrument holds at high-bit marker");e.tick();check(e.voices[0].volume==2,"Gate skips hold marker and enters release tail");e.tick();check(e.voices[0].volume==0,"Release tail reaches silence");

        auto c=fixture();command(c,0,1,MusicOp::Transpose,2,{12});command(c,0,2,MusicOp::NoTranspose,3,{});command(c,0,3,MusicOp::Note,4,{20,1});command(c,0,4,MusicOp::Note,5,{20,1});command(c,0,5,MusicOp::Stop,6,{});
        NativeAudio t(c);t.playMusic(0);t.tick();check(t.voices[0].note==20,"No-transpose suppresses exactly one note");t.tick();check(t.voices[0].note==32,"Transposition returns for the following note");

        std::vector<int16_t> buffer,preview;NativeAudio title(assets);title.playMusic(1);uint64_t frames=0;long long energy=0;
        for(int i=0;i<480;++i){title.tick();title.render(buffer);frames+=buffer.size()/2;for(int sample:buffer)energy+=static_cast<long long>(sample)*sample;preview.insert(preview.end(),buffer.begin(),buffer.end());}
        check(frames==uint64_t(480)*48000*70224/4194304,"Fractional PCM buffer lengths preserve original video rate");check(energy>1000000000,"Title sequence produces audible nonzero PCM");saveWave("audio-title-preview.wav",preview);
        for(int song=0;song<14;++song){NativeAudio first(assets),second(assets);first.playMusic(song);second.playMusic(song);
            for(int frame=0;frame<12000;++frame){first.tick();second.tick();}
            check(first.voices[0].notes>0&&first.voices[2].notes>0,"Every original song reaches pulse and wave notes");
            bool same=true;for(int voice=0;voice<6;++voice)same&=first.voices[voice].position==second.voices[voice].position&&first.voices[voice].frequency==second.voices[voice].frequency&&first.voices[voice].volume==second.voices[voice].volume;
            check(same,"Native song sequencing is deterministic through long playback");
        }
        for(int effect=0;effect<26;++effect){NativeAudio audio(assets),reference(assets);audio.playMusic(1);reference.playMusic(1);audio.queueEffect(effect);
            for(int frame=0;frame<2000;++frame){audio.tick();reference.tick();}
            check(!audio.voices[4].active&&!audio.voices[5].active,"Every original sound effect terminates");
            check(audio.voices[0].notes==reference.voices[0].notes&&audio.voices[3].notes==reference.voices[3].notes,"Effects leave underlying music sequencing running");
        }
        NativeAudio stopped(assets);stopped.playMusic(1);stopped.queueEffect(1);stopped.tick();
        check(stopped.musicPlaying(),"Playing song exposes active music voices to the music-test UI");
        stopped.queueEffect(2);stopped.stop();stopped.tick();stopped.render(buffer);
        bool silent=true;for(int sample:buffer)silent&=sample==0;
        check(silent&&!stopped.musicPlaying()&&!stopped.voices[4].active&&!stopped.voices[5].active,"Stop clears music, effects, pending request and audible output");
        stopped.playMusic(1);stopped.tick();check(stopped.musicPlaying(),"Music can restart after explicit stop");
        NativeAudio last(assets),single(assets);last.playMusic(1);single.playMusic(1);last.queueEffect(0);last.queueEffect(1);single.queueEffect(1);last.tick();single.tick();
        check(last.voices[4].position==single.voices[4].position&&last.voices[5].position==single.voices[5].position,"Same-update effect requests use the last original queue value");
        for(int song=0;song<14;++song){NativeAudio audio(assets);audio.playMusic(song);std::vector<int16_t> pcm;
            for(int frame=0;frame<60;++frame){audio.tick();audio.render(pcm);}
            check(pcm.size()==1606||pcm.size()==1608,"Every song produces correctly sized stereo device buffers");}
        fprintf(log,"PASS: %d native audio assertions. All 14 songs and 26 effects traverse identified data; waveform/reference equivalence remains unverified.\n",assertions);fclose(log);return 0;
    }catch(const std::exception& e){fprintf(log,"FAIL after %d audio assertions: %s\n",assertions,e.what());fclose(log);return 1;}
}
}
