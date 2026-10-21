#pragma once
#include "air_title_menu.h"

namespace ticd {
struct AirTitlePassword {AirTitleMenu menu;int center=0,closed=0,cleared=0,opened=0,cursor=0;std::array<uint8_t,8> digits{};};
// First password presentation, 2b4f..2ba7. The menu continuation owns all
// storage/deadlines/input. Only decoded glyph data, never original clocks,
// initialize the native text writer. Later editing/submission is separate.
template<class Boundary,class Service,class Interrupt,class Raster,class Poll,class Write>
AirTitlePassword airTitlePassword(AirTitleMenu menu,NativeAudio& sound,const UiAssets& ui,
    Boundary&& boundary,Service&& service,Interrupt&& interrupt,Raster&& raster,Poll&& poll,Write&& write,std::function<int()> sample={}){
    const auto& initial=menu.page.close.fade.layout;const auto& before=initial.reset;const auto& t0=before.timing;
    if(menu.route!=4||menu.unlockProgress||(!menu.carouselOwned&&(menu.index||menu.waits<4||menu.remaining!=481-menu.waits))||(menu.carouselOwned&&!airLaterTitleBranch(menu,4,4))||menu.page.close.center||
       initial.windowY!=112||initial.windowX!=166||initial.lyc!=23||before.display!=0||before.stat!=1||before.lcdc!=0xc3||before.scrollX||before.scrollY||before.servicesMasked||before.pendingRequests||
       t0.countdown!=54||(!menu.carouselOwned&&(t0.displays!=(662+menu.waits)||t0.stats!=(854+2*menu.waits)))||t0.input.pressed!=16||!sound.enabled||sound.song!=1||sound.paused||sound.pendingEffect!=-1||
       std::any_of(before.objects.begin(),before.objects.end(),[](int value){return value!=0;}))throw std::runtime_error("Unowned password presentation entry");
    AirTitlePassword state;state.menu=std::move(menu);auto& title=state.menu.page.close.fade.layout;auto& r=title.reset;auto& t=r.timing;
    AirClock clock;clock.now=t.end;clock.nextStat=t.nextStat;clock.nextVBlank=t.nextVBlank;clock.displays=t.displays;clock.statServices=t.stats;
    clock.interrupt=[&](const char* name,int64_t cycle,AirIrqOwner owner){interrupt(name,cycle,owner);};bool resetting=false;
    auto display=[&](bool){
        if(resetting)throw std::runtime_error("Unowned display during password music reset");
        t.input.sample(sample?sample():t.input.held);if(t.input.held<0||t.input.held>255||(t.input.held&15)==15)throw std::runtime_error("Unowned password presentation input/reset");
        int tick=t.tick;t.tick=(tick+1)&65535;sound.tick();if(sound.effectWorkCycles<0||sound.musicWorkCycles<0)throw std::runtime_error("Unowned password audio");
        service(clock.displays,clock.now+20,tick,t.countdown,116,sound.effectWorkCycles,sound.musicWorkCycles,t.input);return 1592+116+sound.effectWorkCycles+sound.musicWorkCycles;
    };
    clock.rasterWork=[&](int64_t start){return airTitleRasterWork(clock,title,state.center,start,raster,write);};
    auto store=[&](int64_t cycle,int address,int value){if(address>=0x9c00&&address<0xa000)r.window.at(address-0x9c00)=static_cast<uint8_t>(value);write(cycle,address,value);};
    AirResultWriter writer(clock,t.lcdEpoch,display,poll,store);writer.lcd.windowEnabled=true;writer.lcd.windowX=166;writer.lcd.windowY=72;writer.lcd.objectHeight=8;writer.lcd.objectsEnabled=true;writer.lcd.titleRightEdge=true;
    auto work=[&](std::initializer_list<int> costs){writer.work(costs);};auto point=[&](const char* name){boundary(name,clock.now,state,sound.song,sound.enabled);};
    point("begin");work({12});point("closeCall");work({24});
    for(int step=0;step<40;++step){
        point("closeWait");clock.wait(display,false);point("closeReady");work({12});write(clock.now,0xff4a,title.windowY-1);
        clock.atomicWork(12,[&]{--title.windowY;},display,false);work({16,8});write(clock.now,0xc09c,(state.center-2)&255);
        clock.atomicWork(16,[&]{state.center=(state.center-2)&255;++state.closed;},display,false);point("centerStored");work({8,step==39?8:12});
    }
    for(int pass=0;pass<2;++pass){
        if(pass)work({24});point("clearEntry");work({12,12});
        for(int cell=0;cell<320;++cell){
            for(int attempt=0;;++attempt){
                if(attempt>32)throw std::runtime_error("Password clear readiness did not terminate");int mode=-1;
                clock.accessWork(12,8,[&]{mode=writer.lcd.mode(clock.now-t.lcdEpoch);},display,false);if(mode<0)throw std::runtime_error("Unowned password clear geometry");
                poll(clock.now,mode);work({8,mode&2?12:8});if(!(mode&2))break;
            }
            store(clock.now,0x9dc0+cell,0);clock.atomicWork(8,[]{},display,false);work({8,4,4,cell==319?8:12});
        }
        work({16});++state.cleared;point(pass?"clearReturned":"closeReturned");
    }
    std::vector<AirResultTextCommand> commands;
    for(const auto& row:std::array<std::array<int,3>,3>{{{5,16,10},{3,19,14},{6,21,8}}}){
        commands.push_back({1,row[0],row[1]});for(int i=0;i<row[2];++i){int value=ui.hiddenMaps[0][32*row[1]+row[0]+i];if(value>=128)throw std::runtime_error("Unowned password glyph");commands.push_back({0,value,0});}
    }
    commands.push_back({4,0,0});writer.text(commands);point("textReturned");clock.wait(display,false);point("musicWaitReturned");
    // 2b84 LD C,7 / CALL362a. Fixed native reset/copies expose individual
    // completion boundaries to the raster owner, just as title song 1 does.
    work({8,24,4,12,8,4,24});resetting=true;work({4,12,12,8});
    for(int i=0;i<44;++i)work({8,4,i==43?8:12});work({12,12});
    for(int i=0;i<250;++i)work({4,8,8,4,4,i==249?8:12});work({4});
    for(int i=0;i<7;++i)work({12,8});work({8});for(int i=0;i<4;++i)work({12,8});work({16,12,12,12,24});
    for(int i=0;i<16;++i)work({8,8,8,8,4,4,i==15?8:12});work({16,4,12,16});
    for(int i=0;i<8;++i)work({12,8,8,12});work({12,12,12,24});
    for(int i=0;i<23;++i)work({8,8,8,8,4,4,i==22?8:12});work({16,8,12,4,16,16,8,16,16});
    sound.playMusic(7);resetting=false;point("musicReady");work({24});
    for(int step=0;step<40;++step){
        point("openWait");clock.wait(display,false);point("openReady");work({12});write(clock.now,0xff4a,title.windowY+1);
        clock.atomicWork(12,[&]{++title.windowY;},display,false);work({16,8});write(clock.now,0xc09c,(state.center+2)&255);
        clock.atomicWork(16,[&]{state.center=(state.center+2)&255;++state.opened;},display,false);point("openStored");work({step==39?8:12});
    }
    work({16});point("openReturned");work({4,12});state.cursor=0;for(int i=0;i<8;++i)work({16});point("end");
    t.end=clock.now;t.displays=clock.displays;t.stats=clock.statServices;t.nextStat=clock.nextStat;t.nextVBlank=clock.nextVBlank;return state;
}
}
