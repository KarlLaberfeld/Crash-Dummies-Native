#pragma once
#include "air_title_picture.h"
namespace ticd {
// First instruction's native alternate flag is zero after title reset, so
// 268b takes the incoming fade, not the later patterned map transition.
template<class Boundary,class Service,class Interrupt,class Write>
AirTitlePicture airTitleEntrance(AirTitlePicture state,NativeAudio& sound,const UiAssets& ui,
    Boundary&& boundary,Service&& service,Interrupt&& interrupt,Write&& write,std::function<int()> sample={}){
    auto& fade=state.title.fresh.instruction.start.menu.page.close.fade;auto& l=fade.layout;auto& r=l.reset;auto& t=r.timing;
    if(state.title.result||r.alternate||r.servicesMasked||r.pendingRequests||r.display!=5||r.stat!=5||r.lcdc!=0xd1||r.scrollX||r.scrollY||l.lyc!=95||
       state.title.fresh.instruction.start.menu.page.close.center||!sound.enabled||sound.song!=2||sound.paused||sound.pendingEffect!=-1||
       !state.title.fresh.campaign.active||state.title.fresh.campaign.current||state.title.fresh.campaign.players[0].lives!=5||t.lives!=5||
       (!state.title.fresh.instruction.start.menu.selectedPlayers&&(t.displays!=707||t.stats!=936))||t.countdown!=54||t.perfect||fade.bgp||fade.obp0||fade.obp1||std::min(t.nextStat,t.nextVBlank)<=t.end||
       std::any_of(r.objects.begin(),r.objects.end(),[](int v){return v!=0;})||std::any_of(r.window.begin(),r.window.end(),[](int v){return v!=0;}))
        throw std::runtime_error("Unowned first-instruction incoming fade");
    AirClock clock;clock.now=t.end;clock.nextStat=t.nextStat;clock.nextVBlank=t.nextVBlank;clock.displays=t.displays;clock.statServices=t.stats;
    clock.interrupt=[&](const char* kind,int64_t cycle,AirIrqOwner owner){interrupt(kind,cycle,owner);};
    clock.rasterWork=[&](int64_t start){write(start+216,0xff42,0);return 288;};
    auto display=[&](bool){
        t.input.sample(sample?sample():t.input.held);
        if(t.input.held<0||t.input.held>255||(t.input.held&15)==15)throw std::runtime_error("Unowned first-instruction fade input/reset");
        write(clock.now+20+1284,0xff42,0);int tick=t.tick;t.tick=(tick+1)&65535;sound.tick();
        if(sound.effectWorkCycles<0||sound.musicWorkCycles<0)throw std::runtime_error("Unowned first-instruction fade audio");
        service(clock.displays,clock.now+20,tick,t.countdown,144,sound.effectWorkCycles,sound.musicWorkCycles,t.input);
        return 1592+144+sound.effectWorkCycles+sound.musicWorkCycles;
    };
    auto work=[&](std::initializer_list<int> costs){for(int cost:costs)clock.atomicWork(cost,[]{},display,false);};
    int palettes=0,waits=0;auto point=[&](const char* name){t.end=clock.now;boundary(name,clock.now,palettes,waits,state);};
    point("begin");work({16,4,12});point("firstInstruction");work({8});write(clock.now,0xc09d,1);clock.atomicWork(16,[&]{r.alternate=1;},display,false);work({16});point("fadeEntry");work({12,8});
    for(int segment=0;segment<8;++segment){++palettes;point("palette");int value=ui.fadePalettes[7-segment];work({8});write(clock.now,0xff47,value);
        clock.accessWork(12,8,[&]{fade.bgp=value;},display,false);work({8});write(clock.now,0xff49,value&0xf3);
        clock.accessWork(12,8,[&]{fade.obp1=value&0xf3;},display,false);work({8,8});write(clock.now,0xff48,value&0xcf);
        clock.accessWork(12,8,[&]{fade.obp0=value&0xcf;},display,false);work({8});
        for(int step=0;step<4;++step){point("wait");clock.wait(display,false);++waits;point("tail");work({4,step<3?12:8});}
        work({4,segment<7?12:8});
    }
    work({16});point("end");t.end=clock.now;t.displays=clock.displays;t.stats=clock.statServices;t.nextStat=clock.nextStat;t.nextVBlank=clock.nextVBlank;return state;
}
}
