#pragma once
#include "air_instruction_text.h"
#include <fstream>

namespace ticd {
// Diagnostic output only. All execution remains in the native semantic owners;
// no reference observations are loaded by this continuation.
struct AirNextInstructionCsv {
    std::ofstream points,services,irqs,polls,writes,summary;
    AirNextInstructionCsv(const std::string& base,const std::string& columns,const char* access="cycle,address,value",const char* pollValue="mode"):
        points(base+".csv"),services(base+".services.csv"),irqs(base+".interrupts.csv"),polls(base+".polls.csv"),writes(base+".writes.csv"),summary(base+".summary.csv"){
        if(!points||!services||!irqs||!polls||!writes||!summary)throw std::runtime_error("Cannot open next instruction diagnostic outputs");
        points<<columns<<'\n';services<<"service,cycle,tick,countdown,display,effects,music,inputHeld,inputPressed\n";
        irqs<<"kind,vectorCycle,owner\n";polls<<"cycle,"<<pollValue<<'\n';writes<<access<<'\n';
    }
    void service(unsigned index,int64_t cycle,int tick,int countdown,int display,int effects,int music,const DisplayInput& input){services<<index<<','<<cycle<<','<<tick<<','<<countdown<<','<<display<<','<<effects<<','<<music<<','<<input.held<<','<<input.pressed<<'\n';}
    void irq(const char* kind,int64_t cycle,AirIrqOwner owner){irqs<<kind<<','<<cycle<<','<<int(owner)<<'\n';}
    void poll(int64_t cycle,int mode){polls<<cycle<<','<<mode<<'\n';}
    void write(int64_t cycle,int address,int value){writes<<cycle<<','<<address<<','<<value<<'\n';}
    void finish(const AirResultHandoff& state,int stage,int difficulty,int scroll,int skipped=0){
        const auto& t=state.timing;
        summary<<"end,tick,countdown,displays,stats,lcdEpoch,nextStat,nextVBlank,player,lives0,lives1,result,stage,difficulty,scroll,skipped\n"
            <<t.end<<','<<t.tick<<','<<t.countdown<<','<<t.displays<<','<<t.stats<<','<<t.lcdEpoch<<','<<t.nextStat<<','<<t.nextVBlank<<','<<state.player<<','<<state.lives[0]<<','<<state.lives[1]<<','<<state.result<<','<<stage<<','<<difficulty<<','<<scroll<<','<<skipped<<'\n';
    }
};

inline AirInstructionTextState airProbeNextInstruction(const std::string& base,AirResultHandoff campaign,AirResultTransition incoming,
    int result,int stage,int difficulty,int inheritedScroll,NativeAudio& sound,const UiAssets& ui,int extent,std::function<int()> sample){
    if(extent<1||extent>5||campaign.player<0||campaign.player>1||campaign.result||stage!=1||difficulty<0||difficulty>3||
       inheritedScroll<0||inheritedScroll>255||campaign.lives[campaign.player^1]||campaign.lives[campaign.player]!=incoming.lives||sound.enabled||result&6||!(result&1))
        throw std::runtime_error("Unowned post-retry campaign continuation");
    AirNextInstructionCsv hand(base+".next-handoff","boundary,cycle,tick,countdown,player,lives0,lives1,result,inputHeld,inputPressed");
    auto state=airResultHandoff(incoming,campaign.player,campaign.lives,result,sound,
        [&](const char* name,int64_t cycle,int tick,int countdown,int player,int lives0,int lives1,int value,const DisplayInput& input){hand.points<<name<<','<<cycle<<','<<tick<<','<<countdown<<','<<player<<','<<lives0<<','<<lives1<<','<<value<<','<<input.held<<','<<input.pressed<<'\n';},
        [&](auto... args){hand.service(args...);},[&](auto... args){hand.irq(args...);},[&](auto... args){hand.poll(args...);},[&](auto... args){hand.write(args...);},sample);
    hand.finish(state,stage,difficulty,inheritedScroll);if(extent==1)return {};
    auto headers=AirInstructionHeaderAssets::load("build/instruction-header.dat");
    AirNextInstructionCsv header(base+".next-header","boundary,cycle,tick,countdown,player,stage,difficulty,inputHeld,inputPressed,lives");
    state=airInstructionHeader(state,stage,difficulty,sound,headers,
        [&](const char* name,int64_t cycle,int tick,int countdown,int player,int stunt,int level,const DisplayInput& input){header.points<<name<<','<<cycle<<','<<tick<<','<<countdown<<','<<player<<','<<stunt<<','<<level<<','<<input.held<<','<<input.pressed<<','<<state.lives[player]<<'\n';},
        [&](auto... args){header.service(args...);},[&](auto... args){header.irq(args...);},[&](auto... args){header.poll(args...);},[&](auto... args){header.write(args...);},sample);
    header.finish(state,stage,difficulty,inheritedScroll);if(extent==2)return {};
    AirNextInstructionCsv picture(base+".next-picture","boundary,cycle,tick,countdown,musicEnabled,inputHeld,inputPressed","kind,cycle,address,value");
    state=airInstructionPicture(state,stage,sound,ui,
        [&](const char* name,int64_t cycle,int tick,int countdown,bool enabled,const DisplayInput& input){picture.points<<name<<','<<cycle<<','<<tick<<','<<countdown<<','<<enabled<<','<<input.held<<','<<input.pressed<<'\n';},
        [&](auto... args){picture.service(args...);},[&](auto... args){picture.irq(args...);},[&](auto... args){picture.poll(args...);},
        [&](const char* kind,int64_t cycle,int address,int value){picture.writes<<kind<<','<<cycle<<','<<address<<','<<value<<'\n';},sample);
    picture.finish(state,stage,difficulty,inheritedScroll);if(extent==3)return {};
    AirNextInstructionCsv map(base+".next-map","boundary,cycle,tick,countdown,lcdc,lyc,scroll,alternate,display,stat,inputHeld,inputPressed","cycle,address,value","ly");
    auto prepared=airInstructionMap(state,sound,ui,
        [&](const char* name,int64_t cycle,int tick,int countdown,const AirInstructionMapState& s,const DisplayInput& input){map.points<<name<<','<<cycle<<','<<tick<<','<<countdown<<','<<s.lcdc<<','<<s.lyc<<','<<s.scroll<<','<<s.alternate<<','<<s.display<<','<<s.stat<<','<<input.held<<','<<input.pressed<<'\n';},
        [&](auto... args){map.service(args...);},[&](auto... args){map.irq(args...);},[&](auto... args){map.poll(args...);},sample,inheritedScroll);
    map.finish(prepared.campaign,stage,difficulty,prepared.scroll);if(extent==4)return {};
    AirNextInstructionCsv text(base+".next-text","boundary,cycle,tick,countdown,scroll,speed,delay,skipMask,layer,column,row,inputHeld,inputPressed,skipContext");
    auto typed=airInstructionText(prepared,stage,difficulty,sound,ui,
        [&](const char* name,int64_t cycle,int tick,int countdown,const AirInstructionTextState& s,const DisplayInput& input){text.points<<name<<','<<cycle<<','<<tick<<','<<countdown<<','<<s.map.scroll<<','<<s.speed<<','<<s.delay<<','<<s.skipMask<<",152,"<<s.anchor<<','<<s.row<<','<<input.held<<','<<input.pressed<<','<<s.skipContext<<'\n';},
        [&](auto... args){text.service(args...);},[&](auto... args){text.irq(args...);},[&](auto... args){text.poll(args...);},[&](auto... args){text.write(args...);},sample);
    text.finish(typed.map.campaign,stage,difficulty,typed.map.scroll,typed.skipped);return typed;
}
}
