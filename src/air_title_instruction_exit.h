#pragma once
#include "air_title_text.h"
#include "air_instruction_exit.h"
namespace ticd {
template<class Boundary,class Service,class Interrupt,class Poll,class Write>
AirTitleText airTitleInstructionExit(AirTitleText state,NativeAudio& sound,const UiAssets& ui,
    Boundary&& boundary,Service&& service,Interrupt&& interrupt,Poll&& poll,Write&& write,std::function<int()> sample={}){
    const auto& c=state.picture.title.fresh.campaign;const auto& f=state.picture.title.fresh.instruction.start.menu.page.close.fade;
    if(!state.text.backgroundOwned||state.text.speed||state.text.skipMask||state.text.map.lcdc!=0xd1||state.text.map.alternate!=1||
       f.bgp!=0xe4||f.obp0!=0xc4||f.obp1!=0xe0||state.text.map.campaign.result||state.text.map.campaign.timing.countdown!=54||
       !c.active||c.current||c.players[0].day!=1||c.players[0].difficulty||c.players[0].lives!=5||!sound.enabled||sound.song!=2||sound.paused)
        throw std::runtime_error("Unowned first-instruction exit entry");
    auto& r=state.picture.title.fresh.instruction.start.menu.page.close.fade.layout.reset;
    auto store=[&](int64_t cycle,int address,int value){if(address>=0x9800&&address<0x9c00)r.background.at(address-0x9800)=static_cast<uint8_t>(value);if(address==0xff42)r.scrollY=value;write(cycle,address,value);};
    state.text=airInstructionExit(state.text,sound,ui,boundary,service,interrupt,poll,store,sample,true);r.timing=state.text.map.campaign.timing;
    auto& after=state.picture.title.fresh.instruction.start.menu.page.close.fade;after.bgp=after.obp0=after.obp1=0;return state;
}
}
