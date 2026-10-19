#pragma once
#include "air_next_instruction_probe.h"
#include "air_following_setup.h"
#include "air_result_accounting.h"

namespace ticd {
// Adapter around the existing native result owners. The current stunt's LCD,
// campaign, input and random state are the only continuation state supplied.
inline AirResultTransition airProbeRetryResult(const std::string& base,const AirFollowingSetup& state,
    const AirGame& game,NativeAudio& sound,const UiAssets& ui,std::function<int()> sample){
    const auto& c=state.instruction.map.campaign;const auto& end=c.timing;
    int player=c.player,lives=c.lives.at(player);
    if((game.result&6)||!(game.result&1)||lives<=1||sound.enabled)
        throw std::runtime_error("Subsequent result requires its non-final failure owner");
    AirClock clock;clock.now=end.end;clock.nextStat=end.nextStat;clock.nextVBlank=end.nextVBlank;
    AirNextInstructionCsv prefix(base+".next-result","boundary,cycle","cycle,address,value","ly");
    auto prepared=airResultSetupPrefix(clock,game.result,
        [&](const char* name,int64_t cycle){prefix.points<<name<<','<<cycle<<'\n';},
        [&](auto... args){prefix.poll(args...);},game.randomState,end.lcdEpoch);
    prefix.summary<<"end,lcdDisabled,pollReads,pendingRequests,display,stat,countdown,random,tick,player,lives,inputHeld,inputPressed\n"<<prepared.end<<','<<prepared.lcdDisabled<<','<<prepared.pollReads<<','<<prepared.pendingRequests<<','<<prepared.display<<','<<prepared.stat<<','<<prepared.countdown<<','<<prepared.celebration.randomState<<','<<end.tick<<','<<player<<','<<lives<<','<<end.input.held<<','<<end.input.pressed<<'\n';
    auto layouts=AirResultLayoutAssets::load("build/result-timing.dat");
    AirNextInstructionCsv incoming(base+".next-incoming","boundary,cycle,tick,countdown,bgp,obp0,obp1,musicEnabled,inputHeld,inputPressed",
        "cycle,address,value","mode","service,cycle,tick,countdown,display,effects,music,musicEnabled,inputHeld,inputPressed");
    DisplayInput input=end.input;
    auto read=[&]{int raw=sample?sample():input.held;input.sample(raw);return raw;};
    auto point=[&](const char* name,int64_t cycle,int tick,int countdown,int bgp,int obp0,int obp1,bool enabled){incoming.points<<name<<','<<cycle<<','<<tick<<','<<countdown<<','<<bgp<<','<<obp0<<','<<obp1<<','<<enabled<<','<<input.held<<','<<input.pressed<<'\n';};
    auto service=[&](unsigned index,int64_t cycle,int tick,int countdown,int display,int effects,int music,bool enabled){incoming.services<<index<<','<<cycle<<','<<tick<<','<<countdown<<','<<display<<','<<effects<<','<<music<<','<<enabled<<','<<input.held<<','<<input.pressed<<'\n';};
    auto irq=[&](auto... args){incoming.irq(args...);};
    auto result=airResultIncoming(prepared,game.result,end.tick,lives,end.input.held,sound,layouts,ui,point,service,irq,read);
    result=airResultFailureHold(result,game.result,result.input.held,sound,ui,point,service,irq,read);
    incoming.summary<<"end,lcdEpoch,tick,countdown,displays,stats,nextStat,nextVBlank,player,lives\n"<<result.end<<','<<result.lcdEpoch<<','<<result.tick<<','<<result.countdown<<','<<result.displays<<','<<result.stats<<','<<result.nextStat<<','<<result.nextVBlank<<','<<player<<','<<result.lives<<'\n';
    return result;
}
}
