#include "audio.h"
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
        auto a=fixture();
        command(a,0,1,MusicOp::Envelope,2,{0x40,1,1});command(a,0,2,MusicOp::EnvelopeMode,3,{1});
        command(a,0,3,MusicOp::Note,4,{24,3});command(a,0,4,MusicOp::Note,5,{25,0});command(a,0,5,MusicOp::Stop,6,{});
        NativeAudio n(a);n.playMusic(0);n.tick();check(n.voices[0].notes==1&&n.voices[0].volume==4,"Envelope starts at four and waits its first decay tick");
        n.tick();check(n.voices[0].volume==3,"Software decay decrements after period underflow");n.tick();check(n.voices[0].notes==1,"Three-update note retains its full duration");n.tick();
        check(n.voices[0].notes==2&&n.voices[0].remaining==0,"Zero-length byte starts a 256-update note");
        for(int i=0;i<255;++i)n.tick();check(n.voices[0].active,"Zero duration does not terminate one update early");n.tick();check(!n.voices[0].active,"Zero duration ends after 256 updates");

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
        NativeAudio last(assets),single(assets);last.playMusic(1);single.playMusic(1);last.queueEffect(0);last.queueEffect(1);single.queueEffect(1);last.tick();single.tick();
        check(last.voices[4].position==single.voices[4].position&&last.voices[5].position==single.voices[5].position,"Same-update effect requests use the last original queue value");
        for(int song=0;song<14;++song){NativeAudio audio(assets);audio.playMusic(song);std::vector<int16_t> pcm;
            for(int frame=0;frame<60;++frame){audio.tick();audio.render(pcm);}
            check(pcm.size()==1606||pcm.size()==1608,"Every song produces correctly sized stereo device buffers");}
        fprintf(log,"PASS: %d native audio assertions. All 14 songs and 26 effects traverse identified data; waveform/reference equivalence remains unverified.\n",assertions);fclose(log);return 0;
    }catch(const std::exception& e){fprintf(log,"FAIL after %d audio assertions: %s\n",assertions,e.what());fclose(log);return 1;}
}
}
