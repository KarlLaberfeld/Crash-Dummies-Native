#include "audio.h"
#include <cstdio>
#include <fstream>
#include <stdexcept>
using namespace ticd;
// Diagnostic replay of music/effect requests only. Does not accept original
// voice state, register values, ROM code or precomputed timing allowances.
int main(int argc,char** argv){
    try{
        if(argc!=3)throw std::runtime_error("Usage: audio-reference-probe song effects.txt");
        int song=std::stoi(argv[1]);auto assets=AudioAssets::load(L"build/audio.dat");
        NativeAudio audio(assets);audio.measureWork=true;audio.playMusic(song);
        std::ifstream requests(argv[2]);if(!requests)throw std::runtime_error("Cannot open effect requests");
        puts("service,voice,musicCost,voiceCost,active,position,remaining,fixed,loopCount,transpose,noTranspose,fineTune,note,targetNote,frequency,stage,envelopeCounter,volume,releaseCounter,tableIndex,arpCounter,direction,vibratoWait,vibratoCounter,pitchWait");
        int effect,service=0;
        while(requests>>effect){if(effect>=0)audio.queueEffect(effect);audio.tick();
            for(int i=0;i<6;++i){const auto& v=audio.voices[i];
                printf("%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d\n",
                    service,i,audio.musicWorkCycles,audio.voiceWorkCycles[i],int(v.active),v.position,v.remaining,v.fixed,v.loopCount,
                    v.transpose,v.noTranspose,v.fineTune,v.note,v.targetNote,v.frequency,v.stage,v.envelopeCounter,v.volume,
                    v.releaseCounter,v.tableIndex,v.arpCounter,v.direction,v.vibratoWait,v.vibratoCounter,v.pitchWait);
            }++service;
        }
        if(!requests.eof())throw std::runtime_error("Malformed effect request");
        return 0;
    }catch(const std::exception& e){fprintf(stderr,"Audio replay failed: %s\n",e.what());return 1;}
}
