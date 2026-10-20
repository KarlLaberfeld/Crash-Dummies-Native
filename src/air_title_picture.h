#pragma once
#include "air_title_header.h"
#include "air_instruction_picture.h"
namespace ticd {
struct AirTitlePicture {AirTitleResume title;std::array<uint8_t,1024> tiles{};};
// Post-title music selection and picture publication. Native campaign/assets
// supply the actual content. The separate original observer is never read.
template<class Boundary,class Service,class Interrupt,class Poll,class Write>
AirTitlePicture airTitlePicture(AirTitleResume title,NativeAudio& sound,const UiAssets& ui,
    Boundary&& boundary,Service&& service,Interrupt&& interrupt,Poll&& poll,Write&& write,std::function<int()> sample={}){
    const auto& l=title.fresh.instruction.start.menu.page.close.fade.layout;const auto& r=l.reset;const auto& t=r.timing;const auto& c=title.fresh.campaign;
    if(title.result||r.servicesMasked||r.pendingRequests||r.display!=5||r.stat!=5||r.lcdc!=0xd1||r.scrollX||r.scrollY||l.lyc!=95||!l.bootShown||
       title.fresh.instruction.start.menu.page.close.center||!c.active||c.current||c.players[0].lives!=5||t.lives!=5||
       c.players[0].day<1||c.players[0].day>2||(!title.fresh.instruction.start.menu.selectedPlayers&&(t.displays!=703||t.stats!=932))||t.countdown!=54||t.perfect||
       sound.enabled||sound.paused||sound.song!=-1||sound.pendingEffect!=-1||std::min(t.nextStat,t.nextVBlank)<=t.end||
       std::any_of(r.window.begin(),r.window.end(),[](int v){return v!=0;})||
       std::any_of(r.objects.begin(),r.objects.end(),[](int v){return v!=0;}))throw std::runtime_error("Unowned post-title instruction picture entry");
    AirTitlePicture state{std::move(title),{}};auto& out=state.title.fresh.instruction.start.menu.page.close.fade.layout.reset;const auto& campaign=state.title.fresh.campaign;
    AirResultHandoff hand{out.timing,campaign.current,{campaign.players[0].lives,campaign.players[1].lives},state.title.result};
    auto point=[&](const char* name,int64_t cycle,int tick,int countdown,bool,const DisplayInput& input){
        out.timing.end=cycle;out.timing.tick=tick;out.timing.countdown=countdown;out.timing.input=input;boundary(name,cycle,state);
    };
    auto store=[&](const char* kind,int64_t cycle,int address,int value){
        if(std::string(kind)=="map")out.background.at(address-0x9800)=static_cast<uint8_t>(value);
        if(std::string(kind)=="tile")state.tiles.at(address-0x8340)=static_cast<uint8_t>(value);
        write(kind,cycle,address,value);
    };
    hand=airInstructionPicture(hand,campaign.players[0].day,sound,ui,point,service,interrupt,poll,store,sample,AirHeaderPresentation::Instruction);
    out.timing=hand.timing;return state;
}
}
