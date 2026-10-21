#pragma once
#include "air_next_instruction_probe.h"
#include "air_instruction_voice_probe.h"
#include "air_instruction_exit.h"
#include <algorithm>

namespace ticd {
// Post-result instruction continuation. This retains the actual live player's
// handoff, independent clock/audio state and map stores from its preceding picture.
inline AirInstructionTextState airProbeSelectedFollowingInstruction(const std::string& base,
    AirResultHandoff campaign,std::array<uint8_t,1024> background,int stage,int difficulty,
    NativeAudio& sound,const UiAssets& ui,std::function<int()> sample,int inheritedScroll){
    if(campaign.result||campaign.timing.perfect||stage!=1||difficulty||campaign.player<0||campaign.player>1||
       campaign.lives[0]!=4||(campaign.lives[1]!=0&&campaign.lives[1]!=5)||
       campaign.player!=(campaign.lives[1]?1:0)||!sound.enabled||sound.song!=2)
        throw std::runtime_error("Unowned selected post-result instruction campaign");
    std::array<uint8_t,1024> tiles{};
    for(int byte=0;byte<1024;++byte){int tile=52+byte/16,row=(byte%16)/2,plane=byte&1;
        for(int x=0;x<8;++x)tiles[byte]|=((ui.instructions[stage].tiles[tile*64+row*8+x]>>plane)&1)<<(7-x);}
    auto snapshot=[&](const std::string& stem,const std::array<uint8_t,1024>& map){
        std::ofstream maps(stem+".maps.csv"),graphics(stem+".tiles.csv");
        if(!maps||!graphics)throw std::runtime_error("Cannot open following instruction storage outputs");
        maps<<"address,value\n";graphics<<"address,value\n";
        for(int i=0;i<1024;++i){maps<<(0x9800+i)<<','<<int(map[i])<<'\n';graphics<<(0x8340+i)<<','<<int(tiles[i])<<'\n';}};
    auto publish=[&](int64_t,int address,int value){if(address>=0x9800&&address<0x9c00)background.at(address-0x9800)=static_cast<uint8_t>(value);};
    const std::string mapStem=base+".selected-next-map";
    AirNextInstructionCsv map(mapStem,"boundary,cycle,tick,countdown,lcdc,lyc,scroll,alternate,display,stat,inputHeld,inputPressed","cycle,address,value","ly");
    std::ofstream mapVoices(mapStem+".voices.csv");airInstructionVoiceHeader(mapVoices);
    auto prepared=airInstructionMap(campaign,sound,ui,
        [&](const char* name,int64_t cycle,int tick,int countdown,const AirInstructionMapState& s,const DisplayInput& input){map.points<<name<<','<<cycle<<','<<tick<<','<<countdown<<','<<s.lcdc<<','<<s.lyc<<','<<s.scroll<<','<<s.alternate<<','<<s.display<<','<<s.stat<<','<<input.held<<','<<input.pressed<<'\n';},
        [&](unsigned index,int64_t cycle,int tick,int countdown,int display,int effects,int music,const DisplayInput& input){map.service(index,cycle,tick,countdown,display,effects,music,input);airInstructionVoiceRows(mapVoices,index,sound,music);},
        [&](auto... args){map.irq(args...);},[&](auto... args){map.poll(args...);},sample,inheritedScroll);
    map.finish(prepared.campaign,stage,difficulty,prepared.scroll);snapshot(mapStem,background);
    const std::string textStem=base+".selected-next-text";
    AirNextInstructionCsv text(textStem,"boundary,cycle,tick,countdown,scroll,speed,delay,skipMask,layer,column,row,inputHeld,inputPressed,skipContext");
    std::ofstream textVoices(textStem+".voices.csv");airInstructionVoiceHeader(textVoices);
    auto typed=airInstructionText(prepared,stage,difficulty,sound,ui,
        [&](const char* name,int64_t cycle,int tick,int countdown,const AirInstructionTextState& s,const DisplayInput& input){text.points<<name<<','<<cycle<<','<<tick<<','<<countdown<<','<<s.map.scroll<<','<<s.speed<<','<<s.delay<<','<<s.skipMask<<",152,"<<s.anchor<<','<<s.row<<','<<input.held<<','<<input.pressed<<','<<s.skipContext<<'\n';},
        [&](unsigned index,int64_t cycle,int tick,int countdown,int display,int effects,int music,const DisplayInput& input){text.service(index,cycle,tick,countdown,display,effects,music,input);airInstructionVoiceRows(textVoices,index,sound,music);},
        [&](auto... args){text.irq(args...);},[&](auto... args){text.poll(args...);},[&](auto... args){publish(args...);text.write(args...);},sample,true);
    typed.background=background;typed.backgroundOwned=true;
    text.finish(typed.map.campaign,stage,difficulty,typed.map.scroll,typed.skipped);snapshot(textStem,typed.background);
    const std::string exitStem=base+".selected-next-exit";
    AirNextInstructionCsv exit(exitStem,"boundary,cycle,tick,countdown,scroll,bgp,obp0,obp1,musicEnabled,inputHeld,inputPressed");
    std::ofstream exitVoices(exitStem+".voices.csv");airInstructionVoiceHeader(exitVoices);
    auto ended=airInstructionExit(typed,sound,ui,
        [&](const char* name,int64_t cycle,int tick,int countdown,int scroll,int bgp,int obp0,int obp1,bool enabled,const DisplayInput& input){exit.points<<name<<','<<cycle<<','<<tick<<','<<countdown<<','<<scroll<<','<<bgp<<','<<obp0<<','<<obp1<<','<<enabled<<','<<input.held<<','<<input.pressed<<'\n';},
        [&](unsigned index,int64_t cycle,int tick,int countdown,int display,int effects,int music,const DisplayInput& input){exit.service(index,cycle,tick,countdown,display,effects,music,input);airInstructionVoiceRows(exitVoices,index,sound,music);},
        [&](auto... args){exit.irq(args...);},[&](auto... args){exit.poll(args...);},[&](auto... args){exit.write(args...);},sample,true);
    const auto& t=ended.map.campaign.timing;
    exit.summary<<"end,tick,countdown,scroll,displays,stats,lcdEpoch,nextStat,nextVBlank,musicEnabled,activeVoices,player,lives0,lives1\n"<<t.end<<','<<t.tick<<','<<t.countdown<<','<<ended.map.scroll<<','<<t.displays<<','<<t.stats<<','<<t.lcdEpoch<<','<<t.nextStat<<','<<t.nextVBlank<<','<<sound.enabled<<','<<std::count_if(sound.voices.begin(),sound.voices.end(),[](const MusicVoice& v){return v.active;})<<','<<ended.map.campaign.player<<','<<ended.map.campaign.lives[0]<<','<<ended.map.campaign.lives[1]<<'\n';
    snapshot(exitStem,ended.background);return ended;
}
}
