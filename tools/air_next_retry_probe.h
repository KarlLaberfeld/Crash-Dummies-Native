#pragma once
#include "air_next_instruction_probe.h"
#include "air_following_gameplay.h"
#include "air_retry_result_probe.h"
#include <memory>

namespace ticd {
struct AirRetryProbeResult {
    std::unique_ptr<AirGame> game;
    AirFollowingSetup state;
    AirResultTransition transition;
    bool resultOwned=false;
};
// Output adapter only: each continuation uses the preceding native owner's
// returned state. Original observations never enter this execution path.
inline AirRetryProbeResult airProbeNextRetry(const std::string& base,AirInstructionTextState text,
    const AirGame& preceding,const AirAssets& assets,const Assets& shared,
    int stage,int difficulty,NativeAudio& sound,const UiAssets& ui,std::function<int()> sample,int updates=1,bool terminal=false,bool result=false,int thirdInstructionExtent=0,bool fourthEntry=false,int fourthUpdates=1,bool fourthResult=false,int fifthInstructionExtent=0,bool fifthEntry=false,int fifthUpdates=1,bool fifthTerminal=false,bool fifthResult=false,bool fifthReturn=false){
    if(updates<1||updates>100000)throw std::runtime_error("Invalid second-retry update extent");
    if(result&&!terminal)throw std::runtime_error("Subsequent result requires terminal ownership");
    if(thirdInstructionExtent<0||thirdInstructionExtent>5||(thirdInstructionExtent&&!result))throw std::runtime_error("Subsequent instruction requires complete result ownership");
    if(fourthEntry&&thirdInstructionExtent!=5)throw std::runtime_error("Fourth entry requires complete two-life instruction ownership");
    if(fourthResult&&!fourthEntry)throw std::runtime_error("Fourth result requires entry ownership");
    if(fifthInstructionExtent<0||fifthInstructionExtent>5||(fifthInstructionExtent&&!fourthResult)|| (fifthEntry&&fifthInstructionExtent!=5))throw std::runtime_error("Fifth entry/instruction requires complete fourth-result ownership");
    if(fourthUpdates<1||fourthUpdates>100000||(fourthUpdates!=1&&!fourthEntry))throw std::runtime_error("Fourth gameplay extent requires entry ownership");
    if(fifthUpdates<1||fifthUpdates>100000||((fifthUpdates!=1||fifthTerminal)&&!fifthEntry))throw std::runtime_error("Fifth gameplay extent requires entry ownership");
    if(fifthResult&&!fifthTerminal)throw std::runtime_error("Final result requires terminal ownership");
    if(fifthReturn&&!fifthResult)throw std::runtime_error("Game-over return requires complete final result");
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
    // Stage setup already owns the LCD-off map workload. Materialize its
    // decoded storage here, before observing the two initial display copies.
    auto mapSeed=std::make_unique<AirGame>(assets,shared);mapSeed->start(difficulty,prepared.instruction.map.campaign.player);
    if(!exited.backgroundOwned)throw std::runtime_error("Subsequent row storage lacks its native instruction background");
    AirMapPublication entryMap;entryMap.initialize(*mapSeed,&exited.background);
    std::ofstream map(base+".next-gameplay.map.csv");if(!map)throw std::runtime_error("Cannot open subsequent row publication");
    map<<"boundary,service,cycle,pending,row";for(int i=0;i<32;++i)map<<",buffer"<<i;for(int i=0;i<1024;++i)map<<",tile"<<i;map<<'\n';
    const unsigned mapOrigin=prepared.instruction.map.campaign.timing.displays;
    auto writeMap=[&](const char* name,unsigned index,int64_t cycle,bool pending,const AirMapPublication& row){map<<name<<','<<(index-mapOrigin)<<','<<cycle<<','<<pending<<','<<row.destination;
        for(int value:row.buffer)map<<','<<value;for(int value:row.tiles)map<<','<<value;map<<'\n';};
    AirNextInstructionCsv entry(base+".next-entry","boundary,cycle,tick,countdown,display,stat,lcdc,lyc,pendingRequests,cameraX,cameraY,mapScratch,randomState,ready,musicEnabled,inputHeld,inputPressed");
    auto entered=airFollowingEntry(prepared,sound,
        [&](const char* name,int64_t cycle,const AirFollowingSetup& s){const auto& t=s.instruction.map.campaign.timing;entry.points<<name<<','<<cycle<<','<<t.tick<<','<<t.countdown<<','<<s.display<<','<<s.stat<<','<<s.lcdc<<','<<s.lyc<<','<<s.pendingRequests<<','<<s.cameraX<<','<<s.cameraY<<','<<s.mapScratch<<','<<s.randomState<<','<<s.ready<<','<<sound.enabled<<','<<t.input.held<<','<<t.input.pressed<<'\n';
            if(std::string(name)=="enableReturned")writeMap("startup",mapOrigin,cycle,true,entryMap);},
        [&](unsigned index,int64_t cycle,int tick,int display,int effects,int music,const DisplayInput& input){entry.service(index,cycle,tick,0,display,effects,music,input);
            auto before=cycle+180+704+280+116;writeMap("before",index,before,true,entryMap);entryMap.publish();writeMap("after",index,before+24+736,true,entryMap);},
        [&](auto... args){entry.irq(args...);},sample);
    entered.rowPublication=entryMap;entered.rowPublicationReady=true;
    const auto& e=entered.instruction.map.campaign.timing;
    entry.summary<<"end,tick,countdown,displays,stats,lcdEpoch,nextStat,nextVBlank,randomState,hudCursor,fadeRemaining,entryPauseComplete\n"<<e.end<<','<<e.tick<<','<<e.countdown<<','<<e.displays<<','<<e.stats<<','<<e.lcdEpoch<<','<<e.nextStat<<','<<e.nextVBlank<<','<<entered.randomState<<','<<entered.hudCursor<<','<<entered.fadeRemaining<<','<<entered.entryPauseComplete<<'\n';
    auto game=std::make_unique<AirGame>(assets,shared);airFollowingAirHandoff(*game,preceding,entered);
    std::ofstream sidePush(base+".next-gameplay.side-push.csv");if(!sidePush)throw std::runtime_error("Cannot open inherited side-push observations");
    sidePush<<"boundary,cycle,lastForce\n";
    AirNextInstructionCsv play(base+".next-gameplay","boundary,cycle,tick,secondTicks,seconds,random,ready,map,lastMapCamera,mapScratch,cameraX,cameraY,hudCursor,fadeRemaining,held,pressed,lcdc,display,transfer,remaining,effect,reverse,transferFrame,transferFlags,result");
    std::ofstream actors(base+".next-gameplay.entities.csv"),sprites(base+".next-gameplay.sprites.csv");if(!actors||!sprites)throw std::runtime_error("Cannot open next retry actors/sprites");
    sprites<<"service,slot,present,x,y,flags\n";
    actors<<"boundary,slot,alive,frame,flags,handler,x,y,done,waiting,delay,period";for(int i=0;i<7;++i)actors<<",param"<<i;actors<<'\n';
    if(game->entities[0].handler!=AirHandler::Intro)throw std::runtime_error("Second retry requires native intro entry");
    auto mapSnapshot=[&](const char* name,unsigned index,int64_t cycle,const AirFollowingSetup& s,const AirGame& g){writeMap(name,index,cycle,g.mapTransfer,s.rowPublication);};
    auto updated=entered;
    for(int update=0;update<updates;++update)updated=airFollowingAirQuietUpdate(updated,*game,sound,
        [&](const char* name,int64_t cycle,const AirFollowingSetup& s,const AirGame& g){const auto& input=s.instruction.map.campaign.timing.input;
            sidePush<<name<<','<<cycle<<','<<g.lastForce<<'\n';
            play.points<<name<<','<<cycle<<','<<g.ticks<<','<<g.secondTicks<<','<<g.seconds<<','<<g.randomState<<','<<s.ready<<','<<g.mapTransfer<<','<<g.lastMapCamera<<','<<s.mapScratch<<','<<g.cameraX<<','<<g.cameraY<<','<<g.hudCursor<<','<<g.displayFadeRemaining<<','<<input.held<<','<<input.pressed<<','<<s.lcdc<<','<<s.display<<','<<g.transferState<<','<<g.transferRemaining<<','<<g.pendingSound<<','<<g.reverseSprites<<','<<g.transferFrame<<','<<g.transferFlags<<','<<g.result<<'\n';
            for(int i=0;i<16;++i){const auto& a=g.entities[i];actors<<name<<','<<i<<','<<a.alive<<','<<(a.alive?a.frame:255)<<','<<((a.flags&~2)|(a.offscreen?2:0))<<','<<int(a.handler)<<','<<a.x<<','<<a.y<<','<<a.animDone<<','<<a.frameWaiting<<','<<a.delay<<','<<a.period;for(int value:a.params)actors<<','<<value;actors<<'\n';}},
        [&](unsigned index,int64_t cycle,int tick,int display,int effects,int music,const DisplayInput& input){play.service(index,cycle,tick,0,display,effects,music,input);
            for(int slot=0;slot<40;++slot){const auto& s=game->visibleSprites.slots[slot];sprites<<index<<','<<slot<<','<<(s.present&&s.y!=0)<<','<<s.x<<','<<s.y<<','<<s.flags<<'\n';}},
        [&](auto... args){play.irq(args...);},sample,terminal&&update==updates-1,mapSnapshot);
    mapSnapshot("end",updated.instruction.map.campaign.timing.displays,updated.instruction.map.campaign.timing.end,updated,*game);
    play.finish(updated.instruction.map.campaign,stage,difficulty,updated.instruction.map.scroll);
    AirResultTransition completed{};bool resultOwned=false;
    if(terminal){
        AirNextInstructionCsv outro(base+".next-outro","phase,index,start,end,tickBefore,tickAfter,elapsed,work,bgp,obp0,obp1,musicEnabled");
        std::ofstream objects(base+".next-outro.sprites.csv");if(!objects)throw std::runtime_error("Cannot open subsequent outgoing objects");
        objects<<"service,slot,present,x,y,flags\n";
        updated=airFollowingAirOutro(updated,*game,sound,ui,
            [&](const char* name,int index,int64_t begin,int64_t end,int before,int after,int work,int bgp,int obp0,int obp1,bool enabled){outro.points<<name<<','<<index<<','<<begin<<','<<end<<','<<before<<','<<after<<','<<(end-begin)<<','<<work<<','<<bgp<<','<<obp0<<','<<obp1<<','<<enabled<<'\n';},
            [&](unsigned index,int64_t cycle,int tick,int display,int effects,int music,const DisplayInput& input){outro.service(index,cycle,tick,0,display,effects,music,input);
                for(int slot=0;slot<40;++slot){const auto& s=game->visibleSprites.slots[slot];objects<<index<<','<<slot<<','<<(s.present&&s.y!=0)<<','<<s.x<<','<<s.y<<','<<s.flags<<'\n';}},
            [&](auto... args){outro.irq(args...);},sample);
        outro.finish(updated.instruction.map.campaign,stage,difficulty,updated.instruction.map.scroll);
        if(result){auto incoming=airProbeRetryResult(base,updated,*game,sound,ui,sample);completed=incoming;resultOwned=true;
            if(thirdInstructionExtent){auto campaign=updated.instruction.map.campaign;campaign.lives[campaign.player]=incoming.lives;
                auto typed=airProbeNextInstruction(base+".third",campaign,incoming,game->result,stage,difficulty,updated.instruction.map.scroll,sound,ui,thirdInstructionExtent,sample);
                // Retain the actual completed fourth game/result while its
                // one-life instruction and bounded fifth entry are observed.
                if(fourthEntry){auto fourth=airProbeNextRetry(base+".fourth",typed,*game,assets,shared,stage,difficulty,sound,ui,sample,fourthUpdates,fourthResult,fourthResult);
                    if(fifthInstructionExtent){
                        if(!fourth.resultOwned)throw std::runtime_error("Missing completed fourth result");
                        auto campaign=fourth.state.instruction.map.campaign;campaign.lives[campaign.player]=fourth.transition.lives;
                        auto fifth=airProbeNextInstruction(base+".fifth",campaign,fourth.transition,fourth.game->result,stage,difficulty,fourth.state.instruction.map.scroll,sound,ui,fifthInstructionExtent,sample);
                        if(fifthEntry){auto final=airProbeNextRetry(base+".fifth",fifth,*fourth.game,assets,shared,stage,difficulty,sound,ui,sample,fifthUpdates,fifthTerminal);
                            if(fifthResult)airProbeFinalResult(base+".fifth",final.state,*final.game,sound,ui,sample,fifthReturn);}
                    }}
            }}
    }
    return {std::move(game),updated,completed,resultOwned};
}
}
