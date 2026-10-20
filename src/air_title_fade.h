#pragma once
#include "air_title_layout.h"

namespace ticd {
struct AirTitleFade {AirTitleLayout layout;int bgp=0,obp0=0,obp1=0;};
// 0258..025f, post-campaign title only. Initial pending services, the blank
// center's two raster branches, complete incoming fade and one final wait.
// Song selection, center motion/page install and menu input remain separate.
template<class Boundary,class Service,class Interrupt,class Raster,class Write>
AirTitleFade airTitleFade(AirTitleLayout layout,NativeAudio& sound,const UiAssets& ui,
    Boundary&& boundary,Service&& service,Interrupt&& interrupt,Raster&& raster,Write&& write,std::function<int()> sample={}){
    const auto& initial=layout.reset;const auto& before=initial.timing;
    if(!initial.servicesMasked||initial.pendingRequests!=3||initial.lcdc!=0xc3||initial.display||initial.stat!=1||initial.scrollY||initial.scrollX||
       before.end!=before.lcdEpoch+20||before.nextStat!=before.lcdEpoch+23*456||before.nextVBlank!=before.lcdEpoch+144*456||
       before.displays!=546||before.stats!=546||before.countdown!=54||before.input.held!=255||
       layout.lyc!=23||layout.windowX!=166||layout.windowY!=112||!sound.enabled||sound.song!=13)
        throw std::runtime_error("Unowned title fade/startup geometry");
    AirTitleFade state;state.layout=std::move(layout);auto& title=state.layout;auto& r=title.reset;auto& t=r.timing;
    AirClock clock;clock.now=t.end;clock.nextStat=t.nextStat;clock.nextVBlank=t.nextVBlank;clock.displays=t.displays;clock.statServices=t.stats;
    clock.interrupt=[&](const char* name,int64_t cycle,AirIrqOwner owner){interrupt(name,cycle,owner);};
    auto point=[&](const char* name){boundary(name,clock.now,t.tick,t.countdown,state);};
    auto display=[&](bool){
        t.input.sample(sample?sample():t.input.held);
        if(t.input.held<0||t.input.held>255||(t.input.held&15)==15)throw std::runtime_error("Unowned title input/reset service");
        int tick=t.tick;t.tick=(tick+1)&65535;sound.tick();
        if(sound.effectWorkCycles<0||sound.musicWorkCycles<0)throw std::runtime_error("Unowned title audio work");
        service(clock.displays,clock.now+20,tick,t.countdown,116,sound.effectWorkCycles,sound.musicWorkCycles,t.input);
        return 1592+116+sound.effectWorkCycles+sound.musicWorkCycles;
    };
    clock.rasterWork=[&](int64_t start){
        const bool top=r.stat==1;
        if((!top&&r.stat!=2)||title.lyc!=(top?23:103)||r.scrollX||r.scrollY!=(top?0:88))
            throw std::runtime_error("Unowned title raster center/compare branch");
        raster("begin",start,r.stat,r.lcdc,r.scrollY,title.lyc);
        // Common 0048 vector/dispatch reaches the selected handler at +200.
        int64_t operation=start+200;
        if(top){
            operation+=20;write(operation,0xff40,r.lcdc|0x38);r.lcdc|=0x38;
            operation+=36;write(operation,0xff42,88);r.scrollY=88;
            operation+=88;write(operation,0xff42,88);
            operation+=20;write(operation,0xff45,103);title.lyc=103;
            operation+=24;write(operation,0xc099,2);r.stat=2;
        }else{
            operation+=52;write(operation,0xff40,r.lcdc&0xc7);r.lcdc&=0xc7;
            operation+=16;write(operation,0xff42,0);r.scrollY=0;
            operation+=20;write(operation,0xff45,23);title.lyc=23;
            operation+=20;write(operation,0xc099,1);r.stat=1;
        }
        const int body=248+(top?212:136);
        int64_t deadline=t.lcdEpoch+(start-t.lcdEpoch)/AirClock::Frame*AirClock::Frame+title.lyc*456;
        while(deadline<=operation)deadline+=AirClock::Frame;clock.nextStat=deadline;
        raster("end",start+body,r.stat,r.lcdc,r.scrollY,title.lyc);return body;
    };
    auto work=[&](std::initializer_list<int> costs){for(int cost:costs)clock.atomicWork(cost,[]{},display,false);};
    point("begin");clock.now+=4+24;r.servicesMasked=false;r.pendingRequests=0;
    clock.vblank(display,false,AirIrqOwner::PendingStartup);clock.stat(AirIrqOwner::PendingStartup);point("fadeEntry");
    work({12,8});
    for(int segment=0;segment<8;++segment){
        point("palette");int palette=ui.fadePalettes[7-segment];work({8});write(clock.now,0xff47,palette);
        clock.accessWork(12,8,[&]{state.bgp=palette;},display,false);work({8});write(clock.now,0xff49,palette&0xf3);
        clock.accessWork(12,8,[&]{state.obp1=palette&0xf3;},display,false);work({8,8});write(clock.now,0xff48,palette&0xcf);
        clock.accessWork(12,8,[&]{state.obp0=palette&0xcf;},display,false);work({8});
        for(int wait=0;wait<4;++wait){point("wait");clock.wait(display,false);point("tail");work({4,wait<3?12:8});}
        work({4,segment<7?12:8});
    }
    work({16});point("fadeReturned");clock.wait(display,false);point("end");
    t.end=clock.now;t.displays=clock.displays;t.stats=clock.statServices;t.nextStat=clock.nextStat;t.nextVBlank=clock.nextVBlank;return state;
}
}
