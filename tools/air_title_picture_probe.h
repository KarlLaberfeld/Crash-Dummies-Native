#pragma once
#include "air_title_picture.h"
namespace ticd {
inline AirTitlePicture airProbeTitlePicture(const std::string& base,AirTitleResume headed,NativeAudio& sound,const UiAssets& ui,std::function<int()> sample){
    AirNextInstructionCsv picture(base+".title-picture","boundary,cycle,tick,countdown,musicEnabled,inputHeld,inputPressed,stage,display,stat,lcdc,scrollY,pendingRequests,song","kind,cycle,address,value");
    std::ofstream voices(base+".title-picture.voices.csv");
    voices<<"service,voice,musicCost,active,position,remaining,fixed,loopCount,transpose,noTranspose,fineTune,note,targetNote,frequency,stage,envelopeCounter,volume,releaseCounter,tableIndex,arpCounter,direction,vibratoWait,vibratoCounter,pitchWait\n";
    auto state=airTitlePicture(headed,sound,ui,
        [&](const char* name,int64_t cycle,const AirTitlePicture& s){const auto& r=s.title.fresh.instruction.start.menu.page.close.fade.layout.reset;const auto& t=r.timing;
            picture.points<<name<<','<<cycle<<','<<t.tick<<','<<t.countdown<<','<<sound.enabled<<','<<t.input.held<<','<<t.input.pressed<<','<<s.title.fresh.campaign.players[0].day<<','<<r.display<<','<<r.stat<<','<<r.lcdc<<','<<r.scrollY<<','<<r.pendingRequests<<','<<sound.song<<'\n';},
        [&](unsigned index,int64_t cycle,int tick,int countdown,int display,int effects,int music,const DisplayInput& input){picture.service(index,cycle,tick,countdown,display,effects,music,input);
            for(int i=0;i<6;++i){const auto& v=sound.voices[i];voices<<index<<','<<i<<','<<music<<','<<int(v.active)<<','<<v.position<<','<<v.remaining<<','<<v.fixed<<','<<v.loopCount<<','<<v.transpose<<','<<v.noTranspose<<','<<v.fineTune<<','<<v.note<<','<<v.targetNote<<','<<v.frequency<<','<<v.stage<<','<<v.envelopeCounter<<','<<v.volume<<','<<v.releaseCounter<<','<<v.tableIndex<<','<<v.arpCounter<<','<<v.direction<<','<<v.vibratoWait<<','<<v.vibratoCounter<<','<<v.pitchWait<<'\n';}},
        [&](auto... args){picture.irq(args...);},[&](auto... args){picture.poll(args...);},
        [&](const char* kind,auto... values){picture.writes<<kind;((picture.writes<<','<<values),...);picture.writes<<'\n';},sample);
    const auto& r=state.title.fresh.instruction.start.menu.page.close.fade.layout.reset;const auto& t=r.timing;
    picture.summary<<"end,tick,countdown,displays,stats,lcdEpoch,nextStat,nextVBlank,song\n"<<t.end<<','<<t.tick<<','<<t.countdown<<','<<t.displays<<','<<t.stats<<','<<t.lcdEpoch<<','<<t.nextStat<<','<<t.nextVBlank<<','<<sound.song<<'\n';
    std::ofstream maps(base+".title-picture.maps.csv");maps<<"address,value\n";
    for(int i=0;i<2048;++i)maps<<(0x9800+i)<<','<<int(i<1024?r.background[i]:r.window[i-1024])<<'\n';
    std::ofstream tiles(base+".title-picture.tiles.csv");tiles<<"address,value\n";
    for(int i=0;i<1024;++i)tiles<<(0x8340+i)<<','<<int(state.tiles[i])<<'\n';
    return state;
}
}
