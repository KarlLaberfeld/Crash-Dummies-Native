#pragma once
#include "air_title_menu.h"
namespace ticd {
// A page-advance return owns the following close, both clears, decoded page
// composition and reopen. It never resets title music or loads a source clock.
template<class Boundary,class Service,class Interrupt,class Raster,class Poll,class Write>
AirTitleMenu airTitleCycle(AirTitleMenu menu,NativeAudio& sound,const UiAssets& ui,const AirResultTextAssets& texts,
    Boundary&& boundary,Service&& service,Interrupt&& interrupt,Raster&& raster,Poll&& poll,Write&& write,std::function<int()> sample={}){
    auto& l=menu.page.close.fade.layout;auto& r=l.reset;auto& t=r.timing;
    if(menu.route!=1||menu.index<0||menu.index>4||menu.unlockProgress||menu.page.close.center||menu.page.cleared!=2||menu.page.opened!=40||l.windowX!=166||l.windowY!=112||l.lyc!=23||
       r.stat!=1||r.lcdc!=195||r.scrollX||r.scrollY||r.servicesMasked||r.pendingRequests||t.countdown!=54||t.displays<662||t.stats<854||t.nextStat<=t.end||t.nextVBlank<=t.end||
       !sound.enabled||sound.song!=1||sound.paused||sound.pendingEffect!=-1||std::any_of(r.objects.begin(),r.objects.end(),[](int v){return v!=0;}))throw std::runtime_error("Unowned next title page");
    AirClock clock;clock.now=t.end;clock.nextStat=t.nextStat;clock.nextVBlank=t.nextVBlank;clock.displays=t.displays;clock.statServices=t.stats;int center=0,steps=0;
    clock.interrupt=[&](const char* name,int64_t cycle,AirIrqOwner owner){interrupt(name,cycle,owner);};
    auto display=[&](bool){t.input.sample(sample?sample():t.input.held);if(t.input.held<0||t.input.held>255||(t.input.held&15)==15)throw std::runtime_error("Unowned title-cycle reset input");
        int tick=t.tick;t.tick=(tick+1)&65535;sound.tick();if(sound.effectWorkCycles<0||sound.musicWorkCycles<0)throw std::runtime_error("Unowned title-cycle audio");
        service(clock.displays,clock.now+20,tick,t.countdown,116,sound.effectWorkCycles,sound.musicWorkCycles,t.input);return 1592+116+sound.effectWorkCycles+sound.musicWorkCycles;};
    clock.rasterWork=[&](int64_t start){return airTitleRasterWork(clock,l,center,start,raster,write);};
    auto work=[&](std::initializer_list<int> costs){for(int cost:costs)clock.atomicWork(cost,[]{},display,false);};
    auto point=[&](const char* name){boundary(name,clock.now,menu,center,steps,0,0,0);};
    point("begin");work({24});
    for(int i=0;i<40;++i){point("closeWait");clock.wait(display,false);point("closeReady");work({12});write(clock.now,0xff4a,l.windowY-1);clock.atomicWork(12,[&]{--l.windowY;},display,false);work({16,8});write(clock.now,0xc09c,(center-2)&255);clock.atomicWork(16,[&]{center=(center-2)&255;++steps;},display,false);point("centerStored");work({8,i==39?8:12});}
    t.end=clock.now;t.displays=clock.displays;t.stats=clock.statServices;t.nextStat=clock.nextStat;t.nextVBlank=clock.nextVBlank;
    auto closed=menu.page.close;closed.center=center;closed.steps=steps;
    auto page=airTitlePage(closed,sound,ui,[&](const char* name,int64_t cycle,const AirTitlePage& s){if(std::string(name)=="begin")return;menu.page=s;boundary(std::string(name)=="centerStored"?"openStored":name,cycle,menu,s.close.center,40,s.cleared,s.opened,s.rows);},service,interrupt,raster,poll,write,sample,true,menu.index,&texts);
    menu.page=std::move(page);menu.route=0;menu.waits=0;menu.remaining=std::array<int,5>{480,480,960,480,960}.at(menu.index);return menu;
}
}
