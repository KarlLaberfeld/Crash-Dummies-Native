#pragma once
#include "air_password_return.h"
namespace ticd {
struct AirMusicTest {AirPasswordReturn screen;int waits=0,plays=0,effects=0,stops=0;bool exited=false;};
// 2dab..2bdc: numbers are rendered before fresh input. B precedes A;
// A restarts a completed/different tune or queues an effect on a live tune.
template<class Boundary,class Service,class Interrupt,class Raster,class Poll,class Write>
AirMusicTest airMusicTest(AirPasswordReturn screen,NativeAudio& sound,Boundary&& boundary,Service&& service,
    Interrupt&& interrupt,Raster&& raster,Poll&& poll,Write&& write,std::function<int()> sample={}){
    const auto& l0=screen.feedback.edit.password.menu.page.close.fade.layout;const auto& r0=l0.reset;
    if(screen.target!=3||screen.center||screen.closed!=40||screen.cleared!=2||screen.opened!=40||screen.tune||screen.effect||screen.lastTune!=255||
       l0.windowX!=166||l0.windowY!=112||l0.lyc!=23||r0.display||r0.stat!=1||r0.lcdc!=0xc3||r0.scrollX||r0.scrollY||r0.servicesMasked||r0.pendingRequests||r0.timing.countdown!=54||sound.enabled||sound.paused||sound.pendingEffect!=-1||
       std::any_of(r0.objects.begin(),r0.objects.end(),[](int value){return value!=0;}))throw std::runtime_error("Unowned music-test entry");
    AirMusicTest state;state.screen=std::move(screen);auto& s=state.screen;auto& title=s.feedback.edit.password.menu.page.close.fade.layout;auto& r=title.reset;auto& t=r.timing;
    AirClock clock;clock.now=t.end;clock.nextStat=t.nextStat;clock.nextVBlank=t.nextVBlank;clock.displays=t.displays;clock.statServices=t.stats;bool resetting=false;
    clock.interrupt=[&](const char* name,int64_t cycle,AirIrqOwner owner){interrupt(name,cycle,owner);};
    auto display=[&](bool){if(resetting)throw std::runtime_error("Unowned display during music-test reset");t.input.sample(sample?sample():t.input.held);if(t.input.held<0||t.input.held>255||(t.input.held&15)==15)throw std::runtime_error("Unowned music-test input/reset");int tick=t.tick;t.tick=(tick+1)&65535;sound.tick();if(sound.effectWorkCycles<0||sound.musicWorkCycles<0)throw std::runtime_error("Unowned music-test audio work");service(clock.displays,clock.now+20,tick,t.countdown,116,sound.effectWorkCycles,sound.musicWorkCycles,t.input);return 1592+116+sound.effectWorkCycles+sound.musicWorkCycles;};
    clock.rasterWork=[&](int64_t start){return airTitleRasterWork(clock,title,0,start,raster,write);};
    auto store=[&](int64_t cycle,int address,int value){if(address>=0x9c00&&address<0xa000)r.window.at(address-0x9c00)=static_cast<uint8_t>(value);write(cycle,address,value);};
    AirResultWriter writer(clock,t.lcdEpoch,display,poll,store);writer.lcd.windowEnabled=true;writer.lcd.windowX=166;writer.lcd.windowY=112;writer.lcd.objectHeight=8;writer.lcd.objectsEnabled=true;writer.lcd.titleRightEdge=true;
    auto work=[&](std::initializer_list<int> costs){writer.work(costs);};auto point=[&](const char* name){boundary(name,clock.now,state,sound);};
    auto byte=[&](int address,int value,int& field){write(clock.now,address,value&255);clock.atomicWork(12,[&]{field=value&255;},display,false);};
    auto reset=[&](bool start){
        resetting=true;if(start)work({16,4,12,8,4,24});else work({16,8,4,24});work({4,12,12,8});
        for(int i=0;i<44;++i)work({8,4,i==43?8:12});work({12,12});for(int i=0;i<250;++i)work({4,8,8,4,4,i==249?8:12});work({4});
        for(int i=0;i<7;++i)work({12,8});work({8});for(int i=0;i<4;++i)work({12,8});work({16,12,12,12,24});for(int i=0;i<16;++i)work({8,8,8,8,4,4,i==15?8:12});work({16,4,12,16});
        if(start){for(int i=0;i<8;++i)work({12,8,8,12});work({12,12,12,24});for(int i=0;i<23;++i)work({8,8,8,8,4,4,i==22?8:12});work({16,8,12,4,16,16,8,16,16});sound.playMusic(s.tune);++state.plays;}
        else{work({4,12,16});sound.stop();++state.stops;}resetting=false;
    };
    auto number=[&](int value){work({12,24,8,8,8,8,4,24});writer.leading=true;writer.digit(value>>4);work({8,8,4,16});writer.digit(value&15);};
    for(int iteration=0;;++iteration){
        if(iteration>=20000)throw std::runtime_error("Music test exceeds diagnostic input extent");point("wait");clock.wait(display,false);++state.waits;point("ready");
        writer.text({{1,16,19},{4,0,0}});point("tunePositioned");number(s.tune);point("tuneRendered");writer.text({{1,16,21},{4,0,0}});point("effectPositioned");number(s.effect);point("numbersReady");
        auto select=[&](int mask,int address,int maximum,bool increment,int& field){work({12,8,(t.input.pressed&mask)?24:12});if(!(t.input.pressed&mask))return;
            int old=field;work({12,increment?4:8});byte(address,increment?old+1:(old-1)&255,field);
            if(increment){work({8,field==maximum+1?8:20});if(field==maximum+1){byte(address,0,field);work({16});}}
            else{work({old==0?8:20});if(old==0){work({8});byte(address,maximum,field);work({16});}}
        };
        select(32,0xff9b,13,false,s.tune);point("leftReturned");select(16,0xff9b,13,true,s.tune);point("rightReturned");select(128,0xff9c,25,false,s.effect);point("downReturned");select(64,0xff9c,25,true,s.effect);point("upReturned");
        work({12,8,(t.input.pressed&2)?24:12});if(t.input.pressed&2){point("stopEntry");work({8});byte(0xff9d,255,s.lastTune);reset(false);}point("bReturned");
        work({12,8,(t.input.pressed&1)?24:12});if(t.input.pressed&1){
            point("playEntry");work({12,12,8});bool same=s.lastTune==s.tune;work({same?8:12});bool active=sound.musicPlaying();
            if(same){work({12,8,8,4,8,4,8,active?8:12});}
            if(same&&active){point("effectEntry");work({12,16});write(clock.now,0xffc6,s.effect);clock.atomicWork(12,[&]{sound.queueEffect(s.effect);},display,false);work({16});++state.effects;}
            else{point("startEntry");work({12});byte(0xff9d,s.tune,s.lastTune);work({4});reset(true);}
        }
        point("aReturned");work({12,8});point("exitDecision");bool leave=t.input.pressed&8;work({leave?8:12});if(leave){work({16});state.exited=true;break;}
    }
    point("end");t.end=clock.now;t.displays=clock.displays;t.stats=clock.statServices;t.nextStat=clock.nextStat;t.nextVBlank=clock.nextVBlank;return state;
}
}
