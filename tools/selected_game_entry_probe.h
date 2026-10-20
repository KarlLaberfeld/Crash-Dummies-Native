#pragma once
#include "air_following_setup.h"
#include "air_next_instruction_probe.h"
#include "air_instruction_voice_probe.h"
namespace ticd {
inline void airProbeSelectedGameEntry(const std::string& base,const AirInstructionTextState& instruction,NativeAudio& sound,std::function<int()> sample){
    AirNextInstructionCsv prefix(base+".title-game-prefix","boundary,cycle,tick,countdown,player,stage,difficulty,lives,display,stat,lcdc,lyc,pendingRequests","cycle,address,value","ly");
    auto setup=airFollowingSetupPrefix(instruction,1,0,sound,[&](const char* name,int64_t cycle,const AirFollowingSetup& s){const auto& c=s.instruction.map.campaign;prefix.points<<name<<','<<cycle<<','<<c.timing.tick<<','<<c.timing.countdown<<','<<c.player<<','<<s.stage<<','<<s.difficulty<<','<<c.lives[c.player]<<','<<s.display<<','<<s.stat<<','<<s.lcdc<<','<<s.lyc<<','<<s.pendingRequests<<'\n';},[&](auto... args){prefix.poll(args...);},[&](auto... args){prefix.write(args...);});
    const auto& p=setup.instruction.map.campaign.timing;prefix.summary<<"end,tick,countdown,displays,stats,pollReads,lcdDisabled,pendingRequests\n"<<p.end<<','<<p.tick<<','<<p.countdown<<','<<p.displays<<','<<p.stats<<','<<setup.pollReads<<','<<setup.lcdDisabled<<','<<setup.pendingRequests<<'\n';
    auto profiles=AirFollowingStageAssets::load("build/following-setup.dat");
    AirNextInstructionCsv stage(base+".title-game-stage","boundary,cycle,tick,countdown,player,stage,difficulty,lives,display,stat,lcdc,lyc,pendingRequests,cameraX,cameraY,mapScratch,ready,musicEnabled");
    auto prepared=airFollowingStageSetup(setup,profiles.profiles[0],sound,[&](const char* name,int64_t cycle,const AirFollowingSetup& s){const auto& c=s.instruction.map.campaign;stage.points<<name<<','<<cycle<<','<<c.timing.tick<<','<<c.timing.countdown<<','<<c.player<<','<<s.stage<<','<<s.difficulty<<','<<c.lives[c.player]<<','<<s.display<<','<<s.stat<<','<<s.lcdc<<','<<s.lyc<<','<<s.pendingRequests<<','<<s.cameraX<<','<<s.cameraY<<','<<s.mapScratch<<','<<s.ready<<','<<sound.enabled<<'\n';});
    stage.finish(prepared.instruction.map.campaign,1,0,prepared.instruction.map.scroll);
    AirNextInstructionCsv entry(base+".title-game-entry","boundary,cycle,tick,countdown,display,stat,lcdc,lyc,pendingRequests,cameraX,cameraY,mapScratch,randomState,ready,musicEnabled,inputHeld,inputPressed");
    std::ofstream voices(base+".title-game-entry.voices.csv");airInstructionVoiceHeader(voices);
    auto entered=airFollowingEntry(prepared,sound,[&](const char* name,int64_t cycle,const AirFollowingSetup& s){const auto& t=s.instruction.map.campaign.timing;entry.points<<name<<','<<cycle<<','<<t.tick<<','<<t.countdown<<','<<s.display<<','<<s.stat<<','<<s.lcdc<<','<<s.lyc<<','<<s.pendingRequests<<','<<s.cameraX<<','<<s.cameraY<<','<<s.mapScratch<<','<<s.randomState<<','<<s.ready<<','<<sound.enabled<<','<<t.input.held<<','<<t.input.pressed<<'\n';},[&](unsigned index,int64_t cycle,int tick,int display,int effects,int music,const DisplayInput& input){entry.service(index,cycle,tick,p.countdown,display,effects,music,input);airInstructionVoiceRows(voices,index,sound,music);},[&](auto... args){entry.irq(args...);},sample);
    const auto& e=entered.instruction.map.campaign.timing;entry.summary<<"end,tick,countdown,displays,stats,lcdEpoch,nextStat,nextVBlank,randomState,hudCursor,fadeRemaining,entryPauseComplete\n"<<e.end<<','<<e.tick<<','<<e.countdown<<','<<e.displays<<','<<e.stats<<','<<e.lcdEpoch<<','<<e.nextStat<<','<<e.nextVBlank<<','<<entered.randomState<<','<<entered.hudCursor<<','<<entered.fadeRemaining<<','<<entered.entryPauseComplete<<'\n';
}
}
