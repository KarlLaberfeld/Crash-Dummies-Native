#pragma once
#include "air_title_menu.h"

namespace ticd {
struct AirTitlePlayers {AirTitleMenu menu;int center=0,closed=0,cleared=0,opened=0,players=0,waits=0,route=0;};
// Select page, toggle/cursor loop and outgoing object-clear entry.
template<class Boundary,class Service,class Interrupt,class Raster,class Poll,class Write>
AirTitlePlayers airTitlePlayers(AirTitleMenu menu,NativeAudio& sound,const UiAssets& ui,
    Boundary&& boundary,Service&& service,Interrupt&& interrupt,Raster&& raster,Poll&& poll,Write&& write,std::function<int()> sample={}){
    const auto& initial=menu.page.close.fade.layout;const auto& before=initial.reset;const auto& t0=before.timing;
    if(menu.route!=3||menu.index||menu.unlockProgress||menu.waits!=3||menu.remaining!=478||menu.page.close.center||
       initial.windowY!=112||initial.windowX!=166||initial.lyc!=23||before.display!=0||before.stat!=1||before.lcdc!=0xc3||before.scrollX||before.scrollY||before.servicesMasked||before.pendingRequests||
       t0.countdown!=54||t0.displays!=(662+menu.waits)||t0.stats!=(854+2*menu.waits)||t0.input.pressed!=4||!sound.enabled||sound.song!=1||sound.paused||sound.pendingEffect!=-1||
       std::any_of(before.objects.begin(),before.objects.end(),[](int value){return value!=0;}))throw std::runtime_error("Unowned player-selection presentation entry");
    AirTitlePlayers state;state.menu=std::move(menu);auto& title=state.menu.page.close.fade.layout;auto& r=title.reset;auto& t=r.timing;
    AirClock clock;clock.now=t.end;clock.nextStat=t.nextStat;clock.nextVBlank=t.nextVBlank;clock.displays=t.displays;clock.statServices=t.stats;
    clock.interrupt=[&](const char* name,int64_t cycle,AirIrqOwner owner){interrupt(name,cycle,owner);};
    auto display=[&](bool){
        t.input.sample(sample?sample():t.input.held);if(t.input.held<0||t.input.held>255||(t.input.held&15)==15)throw std::runtime_error("Unowned player-selection presentation input/reset");
        int tick=t.tick;t.tick=(tick+1)&65535;sound.tick();if(sound.effectWorkCycles<0||sound.musicWorkCycles<0)throw std::runtime_error("Unowned player-selection audio");
        service(clock.displays,clock.now+20,tick,t.countdown,116,sound.effectWorkCycles,sound.musicWorkCycles,t.input);return 1592+116+sound.effectWorkCycles+sound.musicWorkCycles;
    };
    clock.rasterWork=[&](int64_t start){return airTitleRasterWork(clock,title,state.center,start,raster,write);};
    auto store=[&](int64_t cycle,int address,int value){if(address>=0x9c00&&address<0xa000)r.window.at(address-0x9c00)=static_cast<uint8_t>(value);write(cycle,address,value);};
    AirResultWriter writer(clock,t.lcdEpoch,display,poll,store);writer.lcd.windowEnabled=true;writer.lcd.windowX=166;writer.lcd.windowY=72;writer.lcd.objectHeight=8;writer.lcd.objectsEnabled=true;writer.lcd.titleRightEdge=true;
    auto work=[&](std::initializer_list<int> costs){writer.work(costs);};auto point=[&](const char* name){boundary(name,clock.now,state,sound.song,sound.enabled);};
    point("begin");work({24});
    for(int step=0;step<40;++step){
        point("closeWait");clock.wait(display,false);point("closeReady");work({12});write(clock.now,0xff4a,title.windowY-1);
        clock.atomicWork(12,[&]{--title.windowY;},display,false);work({16,8});write(clock.now,0xc09c,(state.center-2)&255);
        clock.atomicWork(16,[&]{state.center=(state.center-2)&255;++state.closed;},display,false);point("centerStored");work({8,step==39?8:12});
    }
    for(int pass=0;pass<2;++pass){
        if(pass)work({24});point("clearEntry");work({12,12});
        for(int cell=0;cell<320;++cell){
            for(int attempt=0;;++attempt){
                if(attempt>32)throw std::runtime_error("Player-selection clear readiness did not terminate");int mode=-1;
                clock.accessWork(12,8,[&]{mode=writer.lcd.mode(clock.now-t.lcdEpoch);},display,false);if(mode<0)throw std::runtime_error("Unowned player-selection clear geometry");
                poll(clock.now,mode);work({8,mode&2?12:8});if(!(mode&2))break;
            }
            store(clock.now,0x9dc0+cell,0);clock.atomicWork(8,[]{},display,false);work({8,4,4,cell==319?8:12});
        }
        work({16});++state.cleared;point(pass?"clearReturned":"closeReturned");
    }
    std::vector<AirResultTextCommand> commands;
    for(const auto& row:std::array<std::array<int,3>,3>{{{3,15,14},{3,18,15},{3,20,15}}}){
        commands.push_back({1,row[0],row[1]});for(int i=0;i<row[2];++i){int value=ui.titleMaps[5][32*row[1]+row[0]+i];if(value>=128)throw std::runtime_error("Unowned player-selection glyph");commands.push_back({0,value,0});}
    }
    commands.push_back({4,0,0});writer.text(commands);point("textReturned");work({24});
    for(int step=0;step<40;++step){
        point("openWait");clock.wait(display,false);point("openReady");work({12});write(clock.now,0xff4a,title.windowY+1);
        clock.atomicWork(12,[&]{++title.windowY;},display,false);work({16,8});write(clock.now,0xc09c,(state.center+2)&255);
        clock.atomicWork(16,[&]{state.center=(state.center+2)&255;++state.opened;},display,false);point("openStored");work({step==39?8:12});
    }
    work({16});
    for(int iteration=0;;++iteration){
        if(iteration>=20000)throw std::runtime_error("Player selection did not leave its bounded loop");
        point("wait");clock.wait(display,false);++state.waits;point("ready");work({24});point("cursorEntry");
        auto byte=[&](int address,int value){write(clock.now,address,value);clock.atomicWork(16,[&]{r.objects.at(address-0xc100)=static_cast<uint8_t>(value);},display,false);};
        work({16,8,8});byte(0xc100,72+16*state.players);work({8});byte(0xc101,24);
        work({16,8,8,8});byte(0xc102,254+((t.tick&16)>>4));work({8});byte(0xc103,128);work({16});point("cursorReturned");
        work({12,8,(t.input.pressed&196)?24:12});
        if(t.input.pressed&196){point("toggleEntry");work({16,8});write(clock.now,0xc081,state.players^1);clock.atomicWork(16,[&]{state.players^=1;},display,false);work({16});}
        point("toggleReturned");work({12,8,(t.input.pressed&8)?16:12});
        if(t.input.pressed&8){state.route=2;break;}
        work({8,(t.input.pressed&3)?8:12});if(t.input.pressed&3){work({24});state.route=1;break;}
    }
    point("end");
    t.end=clock.now;t.displays=clock.displays;t.stats=clock.statServices;t.nextStat=clock.nextStat;t.nextVBlank=clock.nextVBlank;return state;
}
}
