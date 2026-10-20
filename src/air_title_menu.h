#pragma once
#include "air_title_page.h"

namespace ticd {
struct AirTitleMenu {AirTitlePage page;int remaining=480,waits=0,index=0,route=0;};
// 2707..26ea: page-zero's full idle duration and automatic page advance.
// The title reset established an empty unlock sequence. Optional action
// ownership ends at the Start/Select/page branch, before its next UI operation.
// Direction/unlock progression remains separate. Held input creates no edge.
template<class Boundary,class Service,class Interrupt,class Raster,class Write>
AirTitleMenu airTitleMenuIdle(AirTitlePage page,NativeAudio& sound,Boundary&& boundary,
    Service&& service,Interrupt&& interrupt,Raster&& raster,Write&& write,std::function<int()> sample={},bool actions=false){
    const auto& l=page.close.fade.layout;const auto& r=l.reset;const auto& t=r.timing;
    if(page.cleared!=2||page.rows!=10||page.opened!=40||page.close.center||l.windowY!=112||l.windowX!=166||l.lyc!=23||
       r.stat!=1||r.lcdc!=0xc3||r.scrollX||r.scrollY||r.servicesMasked||r.pendingRequests||t.countdown!=54||
       t.displays!=662||t.stats!=854||!sound.enabled||sound.song!=1||
       std::any_of(r.objects.begin(),r.objects.end(),[](int value){return value!=0;}))
        throw std::runtime_error("Unowned first title-menu idle entry");
    AirTitleMenu state;state.page=std::move(page);auto& title=state.page.close.fade.layout;auto& timing=title.reset.timing;
    AirClock clock;clock.now=timing.end;clock.nextStat=timing.nextStat;clock.nextVBlank=timing.nextVBlank;
    clock.displays=timing.displays;clock.statServices=timing.stats;
    clock.interrupt=[&](const char* kind,int64_t cycle,AirIrqOwner owner){interrupt(kind,cycle,owner);};
    auto display=[&](bool){
        int held=sample?sample():timing.input.held;
        if(held<0||held>255||(held&15)==15)throw std::runtime_error("Unowned title-menu reset input");
        timing.input.sample(held);int tick=timing.tick;timing.tick=(tick+1)&65535;sound.tick();
        if(sound.effectWorkCycles<0||sound.musicWorkCycles<0)throw std::runtime_error("Unowned title-menu audio");
        service(clock.displays,clock.now+20,tick,timing.countdown,116,sound.effectWorkCycles,sound.musicWorkCycles,timing.input);
        return 1592+116+sound.effectWorkCycles+sound.musicWorkCycles;
    };
    clock.rasterWork=[&](int64_t start){return airTitleRasterWork(clock,title,0,start,raster,write);};
    auto work=[&](std::initializer_list<int> costs){for(int cost:costs)clock.atomicWork(cost,[]{},display,false);};
    auto point=[&](const char* name){boundary(name,clock.now,state);};
    auto finish=[&]{point("end");timing.end=clock.now;timing.displays=clock.displays;timing.stats=clock.statServices;
        timing.nextStat=clock.nextStat;timing.nextVBlank=clock.nextVBlank;return state;};
    point("begin");work({12});
    while(state.remaining){
        point("wait");clock.wait(display,false);++state.waits;point("ready");work({24});point("unlockEntry");
        // Read the native reset's sequence selector, then the fresh-input byte.
        work({16,4,16,4,12,4});
        if(timing.input.pressed){
            if(!actions||(timing.input.pressed&0xf0))throw std::runtime_error("Fresh title-menu direction branch is not qualified");
            // An action cannot match the initial Up unlock step. The original
            // stores both bytes of the unchanged selector on every mismatch.
            work({8,8,8,12,4});write(clock.now,0xc0b5,0x15);work({16,4});
            write(clock.now,0xc0b6,0x2b);work({16,16});
        }else work({20});
        point("unlockReturned");work({12,8});point("startDecision");
        if(timing.input.pressed&8){work({20});state.route=2;return finish();}
        work({8,12,8});point("selectDecision");
        if(timing.input.pressed&4){work({16});state.route=3;return finish();}
        work({12,12,8});point("actionDecision");
        if(timing.input.pressed&3){work({12});break;}
        work({8});point("timer");
        clock.atomicWork(8,[&]{--state.remaining;},display,false);point("timerStored");
        work({4,4,state.remaining?12:8});
    }
    point("advance");work({16,4});write(clock.now,0xc03e,1);
    clock.atomicWork(16,[&]{state.index=1;},display,false);point("pageStored");work({8,12});state.route=1;return finish();
}
}
