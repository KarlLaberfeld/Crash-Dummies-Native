#pragma once
#include "air_title_text.h"
#include "air_instruction_voice_probe.h"
namespace ticd {
inline AirTitleText airProbeTitleText(const std::string& base,AirTitlePicture entered,NativeAudio& sound,const UiAssets& ui,std::function<int()> sample){
    AirNextInstructionCsv text(base+".title-text","boundary,cycle,tick,countdown,scroll,speed,delay,skipMask,layer,column,row,inputHeld,inputPressed,skipContext");
    std::ofstream voices(base+".title-text.voices.csv");airInstructionVoiceHeader(voices);
    auto typed=airTitleText(entered,sound,ui,
        [&](const char* name,int64_t cycle,int tick,int countdown,const AirInstructionTextState& s,const DisplayInput& input){text.points<<name<<','<<cycle<<','<<tick<<','<<countdown<<','<<s.map.scroll<<','<<s.speed<<','<<s.delay<<','<<s.skipMask<<",152,"<<s.anchor<<','<<s.row<<','<<input.held<<','<<input.pressed<<','<<s.skipContext<<'\n';},
        [&](unsigned index,int64_t cycle,int tick,int countdown,int display,int effects,int music,const DisplayInput& input){text.service(index,cycle,tick,countdown,display,effects,music,input);airInstructionVoiceRows(voices,index,sound,music);},
        [&](auto... args){text.irq(args...);},[&](auto... args){text.poll(args...);},[&](auto... args){text.write(args...);},sample);
    const auto& t=typed.text.map.campaign.timing;
    text.summary<<"end,tick,countdown,scroll,skipped,displays,stats,lcdEpoch,nextStat,nextVBlank\n"<<t.end<<','<<t.tick<<','<<t.countdown<<','<<typed.text.map.scroll<<','<<typed.text.skipped<<','<<t.displays<<','<<t.stats<<','<<t.lcdEpoch<<','<<t.nextStat<<','<<t.nextVBlank<<'\n';
    std::ofstream maps(base+".title-text.maps.csv");maps<<"address,value\n";const auto& r=typed.picture.title.fresh.instruction.start.menu.page.close.fade.layout.reset;
    for(int i=0;i<2048;++i)maps<<(0x9800+i)<<','<<int(i<1024?r.background[i]:r.window[i-1024])<<'\n';
    std::ofstream tiles(base+".title-text.tiles.csv");tiles<<"address,value\n";for(int i=0;i<1024;++i)tiles<<(0x8340+i)<<','<<int(typed.picture.tiles[i])<<'\n';return typed;
}
}
