#pragma once
#include "air_title_fade.h"

namespace ticd {
struct AirTitleClose {AirTitleFade fade;int center=0,steps=0;};
// 025f..27f9: song 1 reset/start, then 40 center-closing waits. Stops before
// clearing/installing the next window page. Only STAT may interrupt reset:
// an audio/display observation of partially reset voices still rejects.
template<class Boundary,class Service,class Interrupt,class Raster,class Write>
AirTitleClose airTitleClose(AirTitleFade fade,NativeAudio& sound,Boundary&& boundary,Service&& service,
    Interrupt&& interrupt,Raster&& raster,Write&& write,std::function<int()> sample={}){
    const auto& initial=fade.layout.reset;const auto& before=initial.timing;
    if(initial.servicesMasked||initial.pendingRequests||initial.stat!=1||initial.lcdc!=0xc3||initial.scrollX||initial.scrollY||
       before.displays!=580||before.stats!=612||before.countdown!=54||fade.layout.lyc!=23||fade.layout.windowY!=112||
       fade.bgp!=0xe4||fade.obp0!=0xc4||fade.obp1!=0xe0||!sound.enabled||sound.song!=13)
        throw std::runtime_error("Unowned title music/close entry");
    AirTitleClose state;state.fade=std::move(fade);auto& title=state.fade.layout;auto& r=title.reset;auto& t=r.timing;
    AirClock clock;clock.now=t.end;clock.nextStat=t.nextStat;clock.nextVBlank=t.nextVBlank;clock.displays=t.displays;clock.statServices=t.stats;
    clock.interrupt=[&](const char* kind,int64_t cycle,AirIrqOwner owner){interrupt(kind,cycle,owner);};
    bool resetting=true;
    auto display=[&](bool){
        if(resetting)throw std::runtime_error("Unowned display/audio observation during title music reset");
        t.input.sample(sample?sample():t.input.held);
        if(t.input.held<0||t.input.held>255||(t.input.held&15)==15)throw std::runtime_error("Unowned title closing input/reset");
        int tick=t.tick;t.tick=(tick+1)&65535;sound.tick();
        if(sound.effectWorkCycles<0||sound.musicWorkCycles<0)throw std::runtime_error("Unowned title closing audio");
        service(clock.displays,clock.now+20,tick,t.countdown,116,sound.effectWorkCycles,sound.musicWorkCycles,t.input);
        return 1592+116+sound.effectWorkCycles+sound.musicWorkCycles;
    };
    clock.rasterWork=[&](int64_t start){return airTitleRasterWork(clock,title,state.center,start,raster,write);};
    auto point=[&](const char* name){boundary(name,clock.now,state,sound.song);};
    auto work=[&](std::initializer_list<int> costs){for(int cost:costs)clock.atomicWork(cost,[]{},display,false);};
    point("begin");work({8,24});point("musicEntry");work({4,12,8,4,24});point("resetEntry");work({4,12,12,8});
    // Fixed clears/copies expose their native source boundaries to STAT.
    for(int i=0;i<44;++i)work({8,4,i==43?8:12});work({12,12});
    for(int i=0;i<250;++i)work({4,8,8,4,4,i==249?8:12});point("stateCleared");
    work({4});for(int i=0;i<7;++i)work({12,8});work({8});for(int i=0;i<4;++i)work({12,8});point("presetsReady");
    work({16,12,12,12,24});
    for(int i=0;i<16;++i)work({8,8,8,8,4,4,i==15?8:12});work({16,4,12});point("waveReady");work({16});point("resetReturned");
    for(int i=0;i<8;++i)work({12,8,8,12});point("rootsReady");work({12,12,12,24});
    for(int i=0;i<23;++i)work({8,8,8,8,4,4,i==22?8:12});work({16});point("hardwareReady");
    work({8,12,4,16,16,8,16,16});sound.playMusic(1);resetting=false;point("musicReturned");
    work({8,24});point("menuEntry");work({24});
    for(int i=0;i<40;++i){
        point("closeWait");clock.wait(display,false);point("closeReady");work({12});
        write(clock.now,0xff4a,title.windowY-1);clock.atomicWork(12,[&]{--title.windowY;},display,false);work({16,8});
        write(clock.now,0xc09c,(state.center-2)&255);clock.atomicWork(16,[&]{state.center=(state.center-2)&255;++state.steps;},display,false);
        point("centerStored");work({8,i==39?8:12});
    }
    point("end");t.end=clock.now;t.displays=clock.displays;t.stats=clock.statServices;t.nextStat=clock.nextStat;t.nextVBlank=clock.nextVBlank;return state;
}
}
