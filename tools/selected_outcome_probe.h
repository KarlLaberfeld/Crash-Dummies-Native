#pragma once
#include "air_following_gameplay.h"
#include "air_next_instruction_probe.h"
#include "air_instruction_voice_probe.h"
#include "selected_following_instruction_probe.h"
#include "selected_game_entry_probe.h"

namespace ticd {
// Initial selected Air failure, from its actual native terminal state through
// life consumption and the next live player's instruction music/picture.
inline void airProbeSelectedOutcome(const std::string& base,AirFollowingSetup state,AirGame& game,
    const Campaign& fresh,NativeAudio& sound,const UiAssets& ui,std::function<int()> sample,int followingExtent=0){
    if(followingExtent<0||followingExtent>3)throw std::runtime_error("Unowned selected next-turn extent");
    auto& campaign=state.instruction.map.campaign;
    if(!fresh.active||fresh.current||campaign.player||game.playerNumber||game.result!=1||
       fresh.players[0].day!=1||fresh.players[0].difficulty||fresh.players[0].lives!=5||campaign.lives[0]!=5||
       fresh.players[1].day!=1||fresh.players[1].difficulty||
       (fresh.players[1].lives!=0&&fresh.players[1].lives!=5)||campaign.lives[1]!=fresh.players[1].lives)
        throw std::runtime_error("Initial selected outcome lacks its actual fresh campaign");
    AirNextInstructionCsv outro(base+".selected-outro","phase,index,start,end,tickBefore,tickAfter,elapsed,work,bgp,obp0,obp1,musicEnabled");
    std::ofstream sprites(base+".selected-outro.sprites.csv");sprites<<"service,slot,present,x,y,flags\n";
    state=airFollowingAirOutro(state,game,sound,ui,
        [&](const char* name,int index,int64_t begin,int64_t end,int before,int after,int work,int bgp,int obp0,int obp1,bool enabled){outro.points<<name<<','<<index<<','<<begin<<','<<end<<','<<before<<','<<after<<','<<end-begin<<','<<work<<','<<bgp<<','<<obp0<<','<<obp1<<','<<enabled<<'\n';},
        [&](unsigned index,int64_t cycle,int tick,int display,int effects,int music,const DisplayInput& input){outro.service(index,cycle,tick,0,display,effects,music,input);for(int slot=0;slot<40;++slot){const auto& s=game.visibleSprites.slots[slot];sprites<<index<<','<<slot<<','<<(s.present&&s.y!=0)<<','<<s.x<<','<<s.y<<','<<s.flags<<'\n';}},
        [&](auto... args){outro.irq(args...);},sample);
    outro.finish(state.instruction.map.campaign,1,0,state.instruction.map.scroll);
    const auto c=state.instruction.map.campaign;const auto& end=c.timing;
    AirClock clock;clock.now=end.end;clock.nextStat=end.nextStat;clock.nextVBlank=end.nextVBlank;
    AirNextInstructionCsv prefix(base+".selected-result-prefix","boundary,cycle","cycle,address,value","ly");
    auto prepared=airResultSetupPrefix(clock,game.result,[&](const char* name,int64_t cycle){prefix.points<<name<<','<<cycle<<'\n';},[&](auto... args){prefix.poll(args...);},game.randomState,end.lcdEpoch);
    prefix.summary<<"end,lcdDisabled,pollReads,pendingRequests,display,stat,countdown,random,tick,player,lives,inputHeld,inputPressed\n"<<prepared.end<<','<<prepared.lcdDisabled<<','<<prepared.pollReads<<','<<prepared.pendingRequests<<','<<prepared.display<<','<<prepared.stat<<','<<prepared.countdown<<','<<prepared.celebration.randomState<<','<<end.tick<<','<<c.player<<','<<c.lives[c.player]<<','<<end.input.held<<','<<end.input.pressed<<'\n';
    auto layouts=AirResultLayoutAssets::load("build/result-timing.dat");
    AirNextInstructionCsv incoming(base+".selected-result","boundary,cycle,tick,countdown,bgp,obp0,obp1,musicEnabled,inputHeld,inputPressed,player,lives,song","cycle,address,value","mode","service,cycle,tick,countdown,display,effects,music,musicEnabled,inputHeld,inputPressed");
    std::ofstream resultVoices(base+".selected-result.voices.csv");airInstructionVoiceHeader(resultVoices);
    DisplayInput input=end.input;int lives=c.lives[c.player];auto read=[&]{int raw=sample?sample():input.held;input.sample(raw);return raw;};
    auto point=[&](const char* name,int64_t cycle,int tick,int countdown,int bgp,int obp0,int obp1,bool enabled){incoming.points<<name<<','<<cycle<<','<<tick<<','<<countdown<<','<<bgp<<','<<obp0<<','<<obp1<<','<<enabled<<','<<input.held<<','<<input.pressed<<','<<c.player<<','<<lives<<','<<(sound.enabled?sound.song:-1)<<'\n';};
    auto service=[&](unsigned index,int64_t cycle,int tick,int countdown,int display,int effects,int music,bool enabled){incoming.services<<index<<','<<cycle<<','<<tick<<','<<countdown<<','<<display<<','<<effects<<','<<music<<','<<enabled<<','<<input.held<<','<<input.pressed<<'\n';airInstructionVoiceRows(resultVoices,index,sound,music);};
    auto result=airResultIncomingOwned<false>(prepared,game.result,end.tick,lives,end.input.held,sound,layouts,ui,point,service,[&](auto... args){incoming.irq(args...);},read,{},[&](int value){lives=value;});
    result=airResultFailureHold(result,game.result,result.input.held,sound,ui,point,service,[&](auto... args){incoming.irq(args...);},read);
    incoming.summary<<"end,lcdEpoch,tick,countdown,displays,stats,nextStat,nextVBlank,player,lives\n"<<result.end<<','<<result.lcdEpoch<<','<<result.tick<<','<<result.countdown<<','<<result.displays<<','<<result.stats<<','<<result.nextStat<<','<<result.nextVBlank<<','<<c.player<<','<<result.lives<<'\n';
    auto remaining=c.lives;remaining[c.player]=result.lives;
    std::array<uint8_t,1024> background{};auto publish=[&](int64_t,int address,int value){if(address>=0x9800&&address<0x9c00)background.at(address-0x9800)=static_cast<uint8_t>(value);};
    AirNextInstructionCsv hand(base+".selected-handoff","boundary,cycle,tick,countdown,player,lives0,lives1,result,inputHeld,inputPressed");
    auto next=airResultHandoff(result,c.player,remaining,game.result,sound,
        [&](const char* name,int64_t cycle,int tick,int countdown,int player,int l0,int l1,int value,const DisplayInput& buttons){hand.points<<name<<','<<cycle<<','<<tick<<','<<countdown<<','<<player<<','<<l0<<','<<l1<<','<<value<<','<<buttons.held<<','<<buttons.pressed<<'\n';},
        [&](auto... args){hand.service(args...);},[&](auto... args){hand.irq(args...);},[&](auto... args){hand.poll(args...);},[&](auto... args){publish(args...);hand.write(args...);},sample);
    const int stage=fresh.players[next.player].day,difficulty=fresh.players[next.player].difficulty;
    hand.finish(next,stage,difficulty,0);
    auto headers=AirInstructionHeaderAssets::load("build/instruction-header.dat");
    AirNextInstructionCsv header(base+".selected-next-header","boundary,cycle,tick,countdown,player,stage,difficulty,inputHeld,inputPressed,lives");
    next=airInstructionHeader(next,stage,difficulty,sound,headers,
        [&](const char* name,int64_t cycle,int tick,int countdown,int player,int stunt,int level,const DisplayInput& buttons){header.points<<name<<','<<cycle<<','<<tick<<','<<countdown<<','<<player<<','<<stunt<<','<<level<<','<<buttons.held<<','<<buttons.pressed<<','<<next.lives[player]<<'\n';},
        [&](auto... args){header.service(args...);},[&](auto... args){header.irq(args...);},[&](auto... args){header.poll(args...);},[&](auto... args){publish(args...);header.write(args...);},sample);
    header.finish(next,stage,difficulty,0);
    AirNextInstructionCsv picture(base+".selected-next-picture","boundary,cycle,tick,countdown,musicEnabled,inputHeld,inputPressed,song","kind,cycle,address,value");
    std::ofstream pictureVoices(base+".selected-next-picture.voices.csv");airInstructionVoiceHeader(pictureVoices);
    next=airInstructionPicture(next,stage,sound,ui,
        [&](const char* name,int64_t cycle,int tick,int countdown,bool enabled,const DisplayInput& buttons){picture.points<<name<<','<<cycle<<','<<tick<<','<<countdown<<','<<enabled<<','<<buttons.held<<','<<buttons.pressed<<','<<(sound.enabled?sound.song:-1)<<'\n';},
        [&](unsigned index,int64_t cycle,int tick,int countdown,int display,int effects,int music,const DisplayInput& buttons){picture.service(index,cycle,tick,countdown,display,effects,music,buttons);airInstructionVoiceRows(pictureVoices,index,sound,music);},
        [&](auto... args){picture.irq(args...);},[&](auto... args){picture.poll(args...);},[&](const char* kind,int64_t cycle,int address,int value){publish(cycle,address,value);picture.writes<<kind<<','<<cycle<<','<<address<<','<<value<<'\n';},sample);
    picture.finish(next,stage,difficulty,0);
    if(followingExtent){auto instruction=airProbeSelectedFollowingInstruction(base,next,background,stage,difficulty,sound,ui,sample,state.instruction.map.scroll);
        if(followingExtent>=2)airProbeSelectedGameEntry(base+".turn",instruction,sound,sample,&game,followingExtent==3,32,false,{},
            next.player==game.playerNumber?AirFollowingAirRoute::SamePlayer:AirFollowingAirRoute::SelectedNextPlayer,true);}
}
}
