#pragma once
#include "air_title_entrance.h"
#include "air_instruction_text.h"
namespace ticd {
struct AirTitleText {AirTitlePicture picture;AirInstructionTextState text;};
template<class Boundary,class Service,class Interrupt,class Poll,class Write>
AirTitleText airTitleText(AirTitlePicture picture,NativeAudio& sound,const UiAssets& ui,
    Boundary&& boundary,Service&& service,Interrupt&& interrupt,Poll&& poll,Write&& write,std::function<int()> sample={}){
    const auto& f=picture.title.fresh.instruction.start.menu.page.close.fade;const auto& r=f.layout.reset;const auto& t=r.timing;const auto& c=picture.title.fresh.campaign;
    if(picture.title.result||r.alternate!=1||r.servicesMasked||r.pendingRequests||r.display!=5||r.stat!=5||r.lcdc!=0xd1||r.scrollX||r.scrollY||f.layout.lyc!=95||
       f.bgp!=0xe4||f.obp0!=0xc4||f.obp1!=0xe0||!c.active||c.current||c.players[0].day!=1||c.players[0].difficulty||c.players[0].lives!=5||t.lives!=5||
       t.displays!=739||t.stats!=968||t.countdown!=54||!sound.enabled||sound.song!=2||sound.paused||sound.pendingEffect!=-1)
        throw std::runtime_error("Unowned first-instruction text entry");
    AirTitleText state{std::move(picture),{}};auto& out=state.picture.title.fresh.instruction.start.menu.page.close.fade.layout.reset;
    const auto& campaign=state.picture.title.fresh.campaign;
    AirInstructionMapState map;map.campaign={out.timing,0,{5,campaign.players[1].lives},0};map.lcdc=0xd1;map.lyc=95;map.scroll=0;map.alternate=1;map.display=map.stat=5;
    auto store=[&](int64_t cycle,int address,int value){if(address>=0x9800&&address<0x9c00)out.background.at(address-0x9800)=static_cast<uint8_t>(value);if(address==0xff42)out.scrollY=value;write(cycle,address,value);};
    state.text=airInstructionText(map,1,0,sound,ui,boundary,service,interrupt,poll,store,sample,true);
    state.text.background=out.background;state.text.backgroundOwned=true;out.timing=state.text.map.campaign.timing;return state;
}
}
