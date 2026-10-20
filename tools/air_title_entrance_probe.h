#pragma once
#include "air_title_entrance.h"
#include "air_instruction_voice_probe.h"
namespace ticd {
inline AirTitlePicture airProbeTitleEntrance(const std::string& base,AirTitlePicture pictured,NativeAudio& sound,const UiAssets& ui,std::function<int()> sample){
    AirNextInstructionCsv out(base+".title-entrance","boundary,cycle,palettes,waits,tick,countdown,alternate,bgp,obp0,obp1,inputHeld,inputPressed,display,stat,lcdc,lyc,musicEnabled");
    std::ofstream voices(base+".title-entrance.voices.csv");airInstructionVoiceHeader(voices);
    auto state=airTitleEntrance(pictured,sound,ui,
        [&](const char* name,int64_t cycle,int palettes,int waits,const AirTitlePicture& s){const auto& f=s.title.fresh.instruction.start.menu.page.close.fade;const auto& r=f.layout.reset;const auto& t=r.timing;
            out.points<<name<<','<<cycle<<','<<palettes<<','<<waits<<','<<t.tick<<','<<t.countdown<<','<<r.alternate<<','<<f.bgp<<','<<f.obp0<<','<<f.obp1<<','<<t.input.held<<','<<t.input.pressed<<','<<r.display<<','<<r.stat<<','<<r.lcdc<<','<<f.layout.lyc<<','<<sound.enabled<<'\n';},
        [&](unsigned index,int64_t cycle,int tick,int countdown,int display,int effects,int music,const DisplayInput& input){out.service(index,cycle,tick,countdown,display,effects,music,input);airInstructionVoiceRows(voices,index,sound,music);},
        [&](auto... args){out.irq(args...);},[&](auto... args){out.write(args...);},sample);
    const auto& f=state.title.fresh.instruction.start.menu.page.close.fade;const auto& r=f.layout.reset;const auto& t=r.timing;
    out.summary<<"end,tick,countdown,displays,stats,lcdEpoch,nextStat,nextVBlank,alternate,bgp,obp0,obp1\n"<<t.end<<','<<t.tick<<','<<t.countdown<<','<<t.displays<<','<<t.stats<<','<<t.lcdEpoch<<','<<t.nextStat<<','<<t.nextVBlank<<','<<r.alternate<<','<<f.bgp<<','<<f.obp0<<','<<f.obp1<<'\n';
    std::ofstream maps(base+".title-entrance.maps.csv");maps<<"address,value\n";for(int i=0;i<2048;++i)maps<<(0x9800+i)<<','<<int(i<1024?r.background[i]:r.window[i-1024])<<'\n';
    std::ofstream tiles(base+".title-entrance.tiles.csv");tiles<<"address,value\n";for(int i=0;i<1024;++i)tiles<<(0x8340+i)<<','<<int(state.tiles[i])<<'\n';
    return state;
}
}
