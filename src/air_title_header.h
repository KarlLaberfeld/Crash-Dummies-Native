#pragma once
#include "air_title_resume.h"
#include "air_instruction_header.h"
namespace ticd {
// First instruction header after title Start. Uses the shared decoded layout
// writer with native campaign state and callback 5, never result callbacks.
template<class Boundary,class Service,class Interrupt,class Poll,class Write>
AirTitleResume airTitleHeader(AirTitleResume state,NativeAudio& sound,const AirInstructionHeaderAssets& assets,
    Boundary&& boundary,Service&& service,Interrupt&& interrupt,Poll&& poll,Write&& write,std::function<int()> sample={}){
    auto& l=state.fresh.instruction.start.menu.page.close.fade.layout;auto& r=l.reset;auto& t=r.timing;
    const auto& c=state.fresh.campaign;
    if(state.result||r.servicesMasked||r.pendingRequests||r.display!=5||r.stat!=5||r.lcdc!=0xd1||r.scrollX||r.scrollY||l.lyc!=95||!l.bootShown||
       state.fresh.instruction.start.menu.page.close.center||sound.enabled||sound.paused||sound.pendingEffect!=-1||sound.song!=-1||
       !c.active||c.current!=0||c.players[0].lives!=5||t.lives!=5||t.displays!=702||t.stats!=931||t.countdown!=54||t.perfect||
       t.end-t.lcdEpoch<AirClock::Frame||std::min(t.nextStat,t.nextVBlank)<=t.end||
       std::any_of(r.background.begin(),r.background.end(),[](int v){return v!=0;})||
       std::any_of(r.window.begin(),r.window.end(),[](int v){return v!=0;})||
       std::any_of(r.objects.begin(),r.objects.end(),[](int v){return v!=0;}))throw std::runtime_error("Unowned post-title instruction header entry");
    AirResultHandoff campaign{t,c.current,{c.players[0].lives,c.players[1].lives},state.result};
    auto point=[&](const char* name,int64_t cycle,int tick,int countdown,int,int,int,const DisplayInput& input){
        t.end=cycle;t.tick=tick;t.countdown=countdown;t.input=input;boundary(name,cycle,state);
    };
    auto store=[&](int64_t cycle,int address,int value){
        if(address>=0x9800&&address<0x9c00)r.background[address-0x9800]=static_cast<unsigned char>(value);
        write(cycle,address,value);
    };
    campaign=airInstructionHeader(campaign,c.players[0].day,c.players[0].difficulty,sound,assets,point,service,interrupt,poll,store,sample,AirHeaderPresentation::Instruction);
    t=campaign.timing;return state;
}
}
