#pragma once
#include "air_title_players.h"
namespace ticd {
struct AirTitlePlayersExit {AirTitlePlayers selection;int center=0,closed=0,cleared=0,opened=0,rows=0,page=0;bool titleReturned=false;};
// 1b2f..0269 after Start, or through the complete 2707 page-zero return
// after A/B. The selection's native state owns every clock and object byte.
template<class Boundary,class Service,class Interrupt,class Raster,class Poll,class Write>
AirTitlePlayersExit airTitlePlayersExit(AirTitlePlayers selection,NativeAudio& sound,const UiAssets& ui,
    Boundary&& boundary,Service&& service,Interrupt&& interrupt,Raster&& raster,Poll&& poll,Write&& write,std::function<int()> sample={}){
    const auto& l0=selection.menu.page.close.fade.layout;const auto& r0=l0.reset;const auto& t0=r0.timing;
    if((selection.route!=1&&selection.route!=2)||selection.players<0||selection.players>1||selection.closed!=40||selection.cleared!=2||selection.opened!=40||selection.center||
       selection.waits<1||l0.windowX!=166||l0.windowY!=112||l0.lyc!=23||r0.display||r0.stat!=1||r0.lcdc!=195||r0.scrollX||r0.scrollY||r0.servicesMasked||r0.pendingRequests||
       t0.countdown!=54||t0.nextStat<=t0.end||t0.nextVBlank<=t0.end||!sound.enabled||sound.song!=1||sound.paused||sound.pendingEffect!=-1||
       (selection.route==2?!(t0.input.pressed&8):((t0.input.pressed&8)||!(t0.input.pressed&3))))throw std::runtime_error("Unowned player-selection continuation");
    AirTitlePlayersExit state;state.selection=std::move(selection);auto& p=state.selection;state.page=p.menu.index;auto& title=p.menu.page.close.fade.layout;auto& r=title.reset;auto& t=r.timing;
    AirClock clock;clock.now=t.end;clock.nextStat=t.nextStat;clock.nextVBlank=t.nextVBlank;clock.displays=t.displays;clock.statServices=t.stats;
    clock.interrupt=[&](const char* name,int64_t cycle,AirIrqOwner owner){interrupt(name,cycle,owner);};
    auto display=[&](bool){
        t.input.sample(sample?sample():t.input.held);if(t.input.held<0||t.input.held>255||(t.input.held&15)==15)throw std::runtime_error("Unowned player continuation input/reset");
        int tick=t.tick;t.tick=(tick+1)&65535;sound.tick();if(sound.effectWorkCycles<0||sound.musicWorkCycles<0)throw std::runtime_error("Unowned player continuation audio");
        service(clock.displays,clock.now+20,tick,t.countdown,116,sound.effectWorkCycles,sound.musicWorkCycles,t.input);return 1592+116+sound.effectWorkCycles+sound.musicWorkCycles;
    };
    clock.rasterWork=[&](int64_t start){return airTitleRasterWork(clock,title,state.center,start,raster,write);};
    auto work=[&](std::initializer_list<int> costs){for(int cost:costs)clock.atomicWork(cost,[]{},display,false);};
    auto sync=[&]{t.end=clock.now;t.displays=clock.displays;t.stats=clock.statServices;t.nextStat=clock.nextStat;t.nextVBlank=clock.nextVBlank;};
    auto point=[&](const char* name){boundary(name,clock.now,state,sound.song,sound.enabled);};
    point("begin");work({8,4,4});
    for(int i=0;i<160;++i){write(clock.now,0xc100+i,0);clock.atomicWork(8,[&]{r.objects[i]=0;},display,false);}point("objectsCleared");work({4,16});p.menu.playerChoice=p.players;p.menu.selectedPlayers=true;
    if(p.route==2){p.menu.route=2;point("end");sync();return state;}
    point("objectsReturned");write(clock.now,0xc03e,0);clock.atomicWork(16,[&]{p.menu.index=state.page=0;},display,false);point("pageStored");work({16});point("closeCall");work({24});
    for(int i=0;i<40;++i){point("closeWait");clock.wait(display,false);point("closeReady");work({12});write(clock.now,0xff4a,title.windowY-1);clock.atomicWork(12,[&]{--title.windowY;},display,false);work({16,8});write(clock.now,0xc09c,(state.center-2)&255);clock.atomicWork(16,[&]{state.center=(state.center-2)&255;++state.closed;},display,false);point("centerStored");work({8,i==39?8:12});}
    sync();AirTitleClose close=p.menu.page.close;close.center=176;close.steps=40;
    auto page=airTitlePage(close,sound,ui,
        [&](const char* name,int64_t cycle,const AirTitlePage& s){if(std::string(name)=="begin")return;state.center=s.close.center;state.cleared=s.cleared;state.opened=s.opened;state.rows=s.rows;p.menu.page.close.fade=s.close.fade;if(std::string(name)=="end")state.titleReturned=true;boundary(std::string(name)=="centerStored"?"openStored":name,cycle,state,sound.song,sound.enabled);},
        service,interrupt,raster,poll,write,sample,true);
    p.menu.page=std::move(page);p.menu.remaining=480;p.menu.waits=p.menu.index=p.menu.route=p.menu.unlockProgress=0;p.menu.carouselOwned=false;return state;
}
}
