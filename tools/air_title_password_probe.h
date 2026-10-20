#pragma once
#include "air_title_password.h"
#include "air_instruction_voice_probe.h"
namespace ticd {
inline AirTitlePassword airProbeTitlePassword(const std::string& base,AirTitleMenu menu,NativeAudio& sound,const UiAssets& ui,std::function<int()> sample){
    AirNextInstructionCsv csv(base+".title-password","boundary,cycle,tick,countdown,center,windowY,stat,display,lyc,lcdc,scrollY,held,pressed,song,musicEnabled");
    std::ofstream raster(base+".title-password.raster.csv"),voices(base+".title-password.voices.csv");raster<<"boundary,cycle,stat,lcdc,scrollY,lyc\n";airInstructionVoiceHeader(voices);
    auto result=airTitlePassword(menu,sound,ui,
        [&](const char* name,int64_t cycle,const AirTitlePassword& s,int song,bool enabled){const auto& l=s.menu.page.close.fade.layout;const auto& r=l.reset;const auto& t=r.timing;
            csv.points<<name<<','<<cycle<<','<<t.tick<<','<<t.countdown<<','<<s.center<<','<<l.windowY<<','<<r.stat<<','<<r.display<<','<<l.lyc<<','<<r.lcdc<<','<<r.scrollY<<','<<t.input.held<<','<<t.input.pressed<<','<<song<<','<<enabled<<'\n';},
        [&](unsigned index,int64_t cycle,int tick,int countdown,int display,int effects,int music,const DisplayInput& input){csv.service(index,cycle,tick,countdown,display,effects,music,input);airInstructionVoiceRows(voices,index,sound,music);},
        [&](auto... args){csv.irq(args...);},[&](const char* name,auto... values){raster<<name;((raster<<','<<values),...);raster<<'\n';},[&](auto... args){csv.poll(args...);},[&](auto... args){csv.write(args...);},sample);
    const auto& r=result.menu.page.close.fade.layout.reset;const auto& t=r.timing;
    csv.summary<<"end,tick,countdown,displays,stats,lcdEpoch,nextStat,nextVBlank,center,closed,cleared,opened,cursor,song\n"<<t.end<<','<<t.tick<<','<<t.countdown<<','<<t.displays<<','<<t.stats<<','<<t.lcdEpoch<<','<<t.nextStat<<','<<t.nextVBlank<<','<<result.center<<','<<result.closed<<','<<result.cleared<<','<<result.opened<<','<<result.cursor<<','<<sound.song<<'\n';
    std::ofstream maps(base+".title-password.maps.csv");maps<<"address,value\n";for(int i=0;i<2048;++i)maps<<(0x9800+i)<<','<<int(i<1024?r.background[i]:r.window[i-1024])<<'\n';return result;
}
}
