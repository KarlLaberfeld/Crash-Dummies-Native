#pragma once
#include "air_title_instruction_exit.h"
#include "air_instruction_voice_probe.h"
namespace ticd {
inline AirTitleText airProbeTitleInstructionExit(const std::string& base,AirTitleText typed,NativeAudio& sound,const UiAssets& ui,std::function<int()> sample){
    AirNextInstructionCsv out(base+".title-instruction-exit","boundary,cycle,tick,countdown,scroll,bgp,obp0,obp1,musicEnabled,inputHeld,inputPressed");
    std::ofstream voices(base+".title-instruction-exit.voices.csv");airInstructionVoiceHeader(voices);
    auto state=airTitleInstructionExit(typed,sound,ui,
        [&](const char* name,int64_t cycle,int tick,int countdown,int scroll,int bgp,int obp0,int obp1,bool enabled,const DisplayInput& input){out.points<<name<<','<<cycle<<','<<tick<<','<<countdown<<','<<scroll<<','<<bgp<<','<<obp0<<','<<obp1<<','<<enabled<<','<<input.held<<','<<input.pressed<<'\n';},
        [&](unsigned index,int64_t cycle,int tick,int countdown,int display,int effects,int music,const DisplayInput& input){out.service(index,cycle,tick,countdown,display,effects,music,input);airInstructionVoiceRows(voices,index,sound,music);},
        [&](auto... args){out.irq(args...);},[&](auto... args){out.poll(args...);},[&](auto... args){out.write(args...);},sample);
    const auto& t=state.text.map.campaign.timing;
    out.summary<<"end,tick,countdown,scroll,displays,stats,lcdEpoch,nextStat,nextVBlank,musicEnabled,activeVoices\n"<<t.end<<','<<t.tick<<','<<t.countdown<<','<<state.text.map.scroll<<','<<t.displays<<','<<t.stats<<','<<t.lcdEpoch<<','<<t.nextStat<<','<<t.nextVBlank<<','<<sound.enabled<<','<<std::count_if(sound.voices.begin(),sound.voices.end(),[](const MusicVoice& v){return v.active;})<<'\n';
    const auto& r=state.picture.title.fresh.instruction.start.menu.page.close.fade.layout.reset;
    std::ofstream maps(base+".title-instruction-exit.maps.csv");maps<<"address,value\n";for(int i=0;i<2048;++i)maps<<(0x9800+i)<<','<<int(i<1024?r.background[i]:r.window[i-1024])<<'\n';
    std::ofstream tiles(base+".title-instruction-exit.tiles.csv");tiles<<"address,value\n";for(int i=0;i<1024;++i)tiles<<(0x8340+i)<<','<<int(state.picture.tiles[i])<<'\n';return state;
}
}
