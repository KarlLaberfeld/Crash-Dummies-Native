#pragma once
#include "air_title_players_exit.h"
#include "air_instruction_voice_probe.h"
namespace ticd {
inline AirTitlePlayersExit airProbeTitlePlayersExit(const std::string& base,AirTitlePlayers entered,NativeAudio& sound,const UiAssets& ui,std::function<int()> sample){
    AirNextInstructionCsv csv(base+".players-exit","boundary,cycle,tick,countdown,center,windowY,closed,cleared,opened,rows,page,players,route,song,musicEnabled,held,pressed,stat,lcdc,scrollY,lyc");
    std::ofstream raster(base+".players-exit.raster.csv"),voices(base+".players-exit.voices.csv");raster<<"boundary,cycle,stat,lcdc,scrollY,lyc\n";airInstructionVoiceHeader(voices);
    auto result=airTitlePlayersExit(entered,sound,ui,
        [&](const char* name,int64_t cycle,const AirTitlePlayersExit& s,int song,bool enabled){const auto& l=s.selection.menu.page.close.fade.layout;const auto& r=l.reset;const auto& t=r.timing;
            csv.points<<name<<','<<cycle<<','<<t.tick<<','<<t.countdown<<','<<s.center<<','<<l.windowY<<','<<s.closed<<','<<s.cleared<<','<<s.opened<<','<<s.rows<<','<<s.page<<','<<s.selection.players<<','<<s.selection.route<<','<<song<<','<<enabled<<','<<t.input.held<<','<<t.input.pressed<<','<<r.stat<<','<<r.lcdc<<','<<r.scrollY<<','<<l.lyc<<'\n';},
        [&](unsigned index,int64_t cycle,int tick,int countdown,int display,int effects,int music,const DisplayInput& input){csv.service(index,cycle,tick,countdown,display,effects,music,input);airInstructionVoiceRows(voices,index,sound,music);},
        [&](auto... args){csv.irq(args...);},[&](const char* name,auto... values){raster<<name;((raster<<','<<values),...);raster<<'\n';},[&](auto... args){csv.poll(args...);},[&](auto... args){csv.write(args...);},sample);
    const auto& r=result.selection.menu.page.close.fade.layout.reset;const auto& t=r.timing;
    csv.summary<<"end,tick,countdown,displays,stats,lcdEpoch,nextStat,nextVBlank,center,closed,cleared,opened,rows,page,players,route,song,musicEnabled,titleReturned\n"<<t.end<<','<<t.tick<<','<<t.countdown<<','<<t.displays<<','<<t.stats<<','<<t.lcdEpoch<<','<<t.nextStat<<','<<t.nextVBlank<<','<<result.center<<','<<result.closed<<','<<result.cleared<<','<<result.opened<<','<<result.rows<<','<<result.page<<','<<result.selection.players<<','<<result.selection.route<<','<<sound.song<<','<<sound.enabled<<','<<result.titleReturned<<'\n';
    std::ofstream maps(base+".players-exit.maps.csv"),objects(base+".players-exit.objects.csv");maps<<"address,value\n";objects<<"address,value\n";for(int i=0;i<2048;++i)maps<<(0x9800+i)<<','<<int(i<1024?r.background[i]:r.window[i-1024])<<'\n';for(int i=0;i<256;++i)objects<<(0xc100+i)<<','<<int(r.objects[i])<<'\n';return result;
}
}
