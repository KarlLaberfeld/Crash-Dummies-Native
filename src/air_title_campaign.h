#pragma once
#include "air_title_instruction.h"
#include "campaign.h"
namespace ticd {
struct AirTitleChoices {int day=0,difficulty=0;bool twoPlayers=false;};
struct AirTitleCampaign {AirTitleInstruction instruction;Campaign campaign;};
// 0292..02bc: retained native title choices, fresh lives, masked window clear
// and LCD restart. Ends before EI; pending service acceptance is separate.
template<class Boundary,class Poll,class Write>
AirTitleCampaign airTitleCampaign(AirTitleInstruction instruction,const Campaign& previous,AirTitleChoices choices,
    const NativeAudio& sound,Boundary&& boundary,Poll&& poll,Write&& write){
    const auto& l=instruction.start.menu.page.close.fade.layout;const auto& r=l.reset;const auto& t=r.timing;
    if(!r.servicesMasked||r.pendingRequests!=3||r.lcdc!=0x51||r.display!=5||r.stat!=5||l.lyc!=95||r.scrollX||r.scrollY||
       t.displays!=698||t.stats!=927||t.countdown!=54||sound.enabled||sound.song!=-1||previous.current||previous.active||
       previous.players[0].lives||previous.players[1].lives||previous.players[0].savings||previous.players[1].savings||
       previous.players[0].completed||previous.players[1].completed)throw std::runtime_error("Unowned title campaign setup entry");
    Campaign desired;desired.start(choices.twoPlayers,choices.day,choices.difficulty);
    AirTitleCampaign state;state.instruction=std::move(instruction);state.campaign=previous;
    auto& title=state.instruction.start.menu.page.close.fade.layout;auto& out=title.reset;auto& timing=out.timing;
    int64_t now=timing.end;auto point=[&](const char* name){boundary(name,now,state);};
    point("begin");now+=16;
    for(int i=0;i<2;++i){write(now,i?0xc090:0xc088,choices.day);now+=16;state.campaign.players[i].day=choices.day;}point("daysReady");
    now+=16;for(int i=0;i<2;++i){write(now,i?0xc091:0xc089,choices.difficulty);now+=16;state.campaign.players[i].difficulty=choices.difficulty;}point("difficultyReady");
    now+=16+4+8;write(now,0xc08a,5);now+=16;state.campaign.players[0].lives=5;timing.lives=5;
    now+=choices.twoPlayers?12:8;if(!choices.twoPlayers)now+=8;write(now,0xc092,choices.twoPlayers?5:0);now+=16;
    state.campaign=desired;point("livesReady");now+=8+24;point("clearEntry");write(now,0xc035,0x9c);now+=16+12+16+4+4;
    for(int cell=0;cell<1024;++cell){
        now+=4+24+16+12;poll(now,0);now+=8+8+12;write(now,0x9c00+cell,0);out.window[cell]=0;
        now+=8+8+16+8+4+4+(cell==1023?8:12);
    }
    now+=16;point("windowCleared");now+=24;point("lcdEnableEntry");now+=12+8;write(now,0xff40,0xd1);
    timing.lcdEpoch=now+8;now+=12;out.lcdc=0xd1;point("lcdWriteReturned");now+=16;
    timing.nextStat=timing.lcdEpoch+95*456;timing.nextVBlank=timing.lcdEpoch+144*456;
    point("end");timing.end=now;return state;
}
}
