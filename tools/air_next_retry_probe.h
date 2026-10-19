#pragma once
#include "air_next_instruction_probe.h"
#include "air_following_gameplay.h"
#include <memory>

namespace ticd {
// Output adapter only: each continuation uses the preceding native owner's
// returned state. Original observations never enter this execution path.
inline void airProbeNextRetry(const std::string& base,AirInstructionTextState text,
    const AirGame& preceding,const AirAssets& assets,const Assets& shared,
    int stage,int difficulty,NativeAudio& sound,const UiAssets& ui,std::function<int()> sample){
    AirNextInstructionCsv exit(base+".next-exit","boundary,cycle,tick,countdown,scroll,bgp,obp0,obp1,musicEnabled,inputHeld,inputPressed");
    auto exited=airInstructionExit(text,sound,ui,
        [&](const char* name,int64_t cycle,int tick,int countdown,int scroll,int bgp,int obp0,int obp1,bool enabled,const DisplayInput& input){exit.points<<name<<','<<cycle<<','<<tick<<','<<countdown<<','<<scroll<<','<<bgp<<','<<obp0<<','<<obp1<<','<<enabled<<','<<input.held<<','<<input.pressed<<'\n';},
        [&](auto... args){exit.service(args...);},[&](auto... args){exit.irq(args...);},[&](auto... args){exit.poll(args...);},[&](auto... args){exit.write(args...);},sample);
    exit.finish(exited.map.campaign,stage,difficulty,exited.map.scroll);
    AirNextInstructionCsv prefix(base+".next-prefix","boundary,cycle,tick,countdown,player,stage,difficulty,lives,display,stat,lcdc,lyc,pendingRequests","cycle,address,value","ly");
    auto setup=airFollowingSetupPrefix(exited,stage,difficulty,sound,
        [&](const char* name,int64_t cycle,const AirFollowingSetup& s){const auto& c=s.instruction.map.campaign;prefix.points<<name<<','<<cycle<<','<<c.timing.tick<<','<<c.timing.countdown<<','<<c.player<<','<<s.stage<<','<<s.difficulty<<','<<c.lives[c.player]<<','<<s.display<<','<<s.stat<<','<<s.lcdc<<','<<s.lyc<<','<<s.pendingRequests<<'\n';},
        [&](auto... args){prefix.poll(args...);},[&](auto... args){prefix.write(args...);});
    const auto& p=setup.instruction.map.campaign.timing;
    prefix.summary<<"end,tick,countdown,displays,stats,pollReads,lcdDisabled,pendingRequests\n"<<p.end<<','<<p.tick<<','<<p.countdown<<','<<p.displays<<','<<p.stats<<','<<setup.pollReads<<','<<setup.lcdDisabled<<','<<setup.pendingRequests<<'\n';
    auto profiles=AirFollowingStageAssets::load("build/following-setup.dat");
    AirNextInstructionCsv staged(base+".next-stage","boundary,cycle,tick,countdown,player,stage,difficulty,lives,display,stat,lcdc,lyc,pendingRequests,cameraX,cameraY,mapScratch,ready,musicEnabled");
    auto prepared=airFollowingStageSetup(setup,profiles.profiles.at((stage-1)*4+difficulty),sound,
        [&](const char* name,int64_t cycle,const AirFollowingSetup& s){const auto& c=s.instruction.map.campaign;staged.points<<name<<','<<cycle<<','<<c.timing.tick<<','<<c.timing.countdown<<','<<c.player<<','<<s.stage<<','<<s.difficulty<<','<<c.lives[c.player]<<','<<s.display<<','<<s.stat<<','<<s.lcdc<<','<<s.lyc<<','<<s.pendingRequests<<','<<s.cameraX<<','<<s.cameraY<<','<<s.mapScratch<<','<<s.ready<<','<<sound.enabled<<'\n';});
    staged.finish(prepared.instruction.map.campaign,stage,difficulty,prepared.instruction.map.scroll);
    AirNextInstructionCsv entry(base+".next-entry","boundary,cycle,tick,countdown,display,stat,lcdc,lyc,pendingRequests,cameraX,cameraY,mapScratch,randomState,ready,musicEnabled,inputHeld,inputPressed");
    auto entered=airFollowingEntry(prepared,sound,
        [&](const char* name,int64_t cycle,const AirFollowingSetup& s){const auto& t=s.instruction.map.campaign.timing;entry.points<<name<<','<<cycle<<','<<t.tick<<','<<t.countdown<<','<<s.display<<','<<s.stat<<','<<s.lcdc<<','<<s.lyc<<','<<s.pendingRequests<<','<<s.cameraX<<','<<s.cameraY<<','<<s.mapScratch<<','<<s.randomState<<','<<s.ready<<','<<sound.enabled<<','<<t.input.held<<','<<t.input.pressed<<'\n';},
        [&](unsigned index,int64_t cycle,int tick,int display,int effects,int music,const DisplayInput& input){entry.service(index,cycle,tick,0,display,effects,music,input);},
        [&](auto... args){entry.irq(args...);},sample);
    const auto& e=entered.instruction.map.campaign.timing;
    entry.summary<<"end,tick,countdown,displays,stats,lcdEpoch,nextStat,nextVBlank,randomState,hudCursor,fadeRemaining,entryPauseComplete\n"<<e.end<<','<<e.tick<<','<<e.countdown<<','<<e.displays<<','<<e.stats<<','<<e.lcdEpoch<<','<<e.nextStat<<','<<e.nextVBlank<<','<<entered.randomState<<','<<entered.hudCursor<<','<<entered.fadeRemaining<<','<<entered.entryPauseComplete<<'\n';
    auto game=std::make_unique<AirGame>(assets,shared);airFollowingAirHandoff(*game,preceding,entered);
    AirNextInstructionCsv play(base+".next-gameplay","boundary,cycle,tick,secondTicks,seconds,random,ready,map,lastMapCamera,mapScratch,cameraX,cameraY,hudCursor,fadeRemaining,held,pressed,lcdc,display,transfer,remaining,effect,reverse,transferFrame,transferFlags,result");
    std::ofstream actors(base+".next-gameplay.entities.csv");if(!actors)throw std::runtime_error("Cannot open next retry actors");
    actors<<"boundary,slot,alive,frame,flags,handler,x,y,done,waiting,delay,period";for(int i=0;i<7;++i)actors<<",param"<<i;actors<<'\n';
    auto updated=airFollowingAirFirstUpdate(entered,*game,sound,
        [&](const char* name,int64_t cycle,const AirFollowingSetup& s,const AirGame& g){const auto& input=s.instruction.map.campaign.timing.input;
            play.points<<name<<','<<cycle<<','<<g.ticks<<','<<g.secondTicks<<','<<g.seconds<<','<<g.randomState<<','<<s.ready<<','<<g.mapTransfer<<','<<g.lastMapCamera<<','<<s.mapScratch<<','<<g.cameraX<<','<<g.cameraY<<','<<g.hudCursor<<','<<g.displayFadeRemaining<<','<<input.held<<','<<input.pressed<<','<<s.lcdc<<','<<s.display<<','<<g.transferState<<','<<g.transferRemaining<<','<<g.pendingSound<<','<<g.reverseSprites<<','<<g.transferFrame<<','<<g.transferFlags<<','<<g.result<<'\n';
            for(int i=0;i<16;++i){const auto& a=g.entities[i];actors<<name<<','<<i<<','<<a.alive<<','<<(a.alive?a.frame:255)<<','<<((a.flags&~2)|(a.offscreen?2:0))<<','<<int(a.handler)<<','<<a.x<<','<<a.y<<','<<a.animDone<<','<<a.frameWaiting<<','<<a.delay<<','<<a.period;for(int value:a.params)actors<<','<<value;actors<<'\n';}},
        [&](unsigned index,int64_t cycle,int tick,int display,int effects,int music,const DisplayInput& input){play.service(index,cycle,tick,0,display,effects,music,input);},
        [&](auto... args){play.irq(args...);},sample);
    play.finish(updated.instruction.map.campaign,stage,difficulty,updated.instruction.map.scroll);
}
}
