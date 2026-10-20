#pragma once
#include "air_title_menu.h"

namespace ticd {
struct AirTitleStart {AirTitleMenu menu;int palettes=0,waits=0;};
// 0269..0272: Start's outgoing fade, final wait and fixed audio reset.
// Only raster work may observe the intermediate reset. Logical native audio
// stops on completion; intermediate voice RAM/PCM parity is not asserted.
template<class Boundary,class Service,class Interrupt,class Raster,class Write>
AirTitleStart airTitleStart(AirTitleMenu menu,NativeAudio& sound,const UiAssets& ui,
    Boundary&& boundary,Service&& service,Interrupt&& interrupt,Raster&& raster,Write&& write,std::function<int()> sample={}){
    const auto& l=menu.page.close.fade.layout;const auto& r=l.reset;const auto& t=r.timing;const auto& f=menu.page.close.fade;
    if(menu.route!=2||menu.waits!=3||menu.remaining!=478||menu.index||menu.page.close.center||l.windowY!=112||l.windowX!=166||l.lyc!=23||
       r.stat!=1||r.lcdc!=0xc3||r.scrollX||r.scrollY||r.servicesMasked||r.pendingRequests||t.displays!=665||t.stats!=860||t.countdown!=54||
       t.input.held!=8||t.input.pressed!=8||f.bgp!=0xe4||f.obp0!=0xc4||f.obp1!=0xe0||!sound.enabled||sound.song!=1||
       std::any_of(r.objects.begin(),r.objects.end(),[](int value){return value!=0;}))throw std::runtime_error("Unowned title Start transition entry");
    AirTitleStart state;state.menu=std::move(menu);auto& fade=state.menu.page.close.fade;auto& title=fade.layout;auto& timing=title.reset.timing;
    AirClock clock;clock.now=timing.end;clock.nextStat=timing.nextStat;clock.nextVBlank=timing.nextVBlank;
    clock.displays=timing.displays;clock.statServices=timing.stats;bool resetting=false;
    clock.interrupt=[&](const char* name,int64_t cycle,AirIrqOwner owner){interrupt(name,cycle,owner);};
    auto display=[&](bool){
        if(resetting)throw std::runtime_error("Unowned display/audio observation during title stop reset");
        int held=sample?sample():timing.input.held;
        if(held<0||held>255||(held&15)==15)throw std::runtime_error("Unowned title Start reset input");
        timing.input.sample(held);int tick=timing.tick;timing.tick=(tick+1)&65535;sound.tick();
        if(sound.effectWorkCycles<0||sound.musicWorkCycles<0)throw std::runtime_error("Unowned title Start audio");
        service(clock.displays,clock.now+20,tick,timing.countdown,116,sound.effectWorkCycles,sound.musicWorkCycles,timing.input);
        return 1592+116+sound.effectWorkCycles+sound.musicWorkCycles;
    };
    clock.rasterWork=[&](int64_t start){return airTitleRasterWork(clock,title,0,start,raster,write);};
    auto point=[&](const char* name){boundary(name,clock.now,state,sound.enabled);};
    auto work=[&](std::initializer_list<int> costs){for(int cost:costs)clock.atomicWork(cost,[]{},display,false);};
    point("begin");work({24});point("fadeEntry");work({12,8});
    for(int i=0;i<8;++i){
        ++state.palettes;point("palette");int palette=ui.fadePalettes[i];work({8});write(clock.now,0xff47,palette);
        clock.accessWork(12,8,[&]{fade.bgp=palette;},display,false);work({8});write(clock.now,0xff49,palette&0xf3);
        clock.accessWork(12,8,[&]{fade.obp1=palette&0xf3;},display,false);work({8,8});write(clock.now,0xff48,palette&0xcf);
        clock.accessWork(12,8,[&]{fade.obp0=palette&0xcf;},display,false);work({8});
        for(int j=0;j<4;++j){point("wait");clock.wait(display,false);++state.waits;point("tail");work({4,j<3?12:8});}
        work({4,i<7?12:8});
    }
    work({16});point("fadeReturned");clock.wait(display,false);point("audioStop");resetting=true;
    work({24});point("stopEntry");work({8,4,24});point("resetEntry");work({4});write(clock.now,0xff26,0);work({12,12,8});
    for(int i=0;i<44;++i)work({8,4,i==43?8:12});work({12,12});
    for(int i=0;i<250;++i)work({4,8,8,4,4,i==249?8:12});point("stateCleared");
    work({4});for(int i=0;i<7;++i)work({12,8});work({8});for(int i=0;i<4;++i)work({12,8});point("presetsReady");
    work({16,12,12,12,24});for(int i=0;i<16;++i)work({8,8,8,8,4,4,i==15?8:12});work({16,4,12});point("waveReady");
    work({16});point("resetReturned");work({4});write(clock.now,0xffcf,0);
    clock.accessWork(12,8,[&]{sound.stop();},display,false);point("audioDisabled");work({16});resetting=false;point("end");
    timing.end=clock.now;timing.displays=clock.displays;timing.stats=clock.statServices;timing.nextStat=clock.nextStat;timing.nextVBlank=clock.nextVBlank;return state;
}
}
