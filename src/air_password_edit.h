#pragma once
#include "air_title_password.h"
namespace ticd {
struct AirPasswordEdit {AirTitlePassword password;int waits=0,submit=0;std::array<uint8_t,160> visibleObjects{};};
// 2ba7..2bcf: publish the cursor before handling fresh input, then edit in
// source Left/Right/Up/Down order. Stop before submission's push/final wait.
template<class Boundary,class Service,class Interrupt,class Raster,class Poll,class Write>
AirPasswordEdit airPasswordEdit(AirTitlePassword password,NativeAudio& sound,Boundary&& boundary,Service&& service,
    Interrupt&& interrupt,Raster&& raster,Poll&& poll,Write&& write,std::function<int()> sample={}){
    const auto& l=password.menu.page.close.fade.layout;const auto& initial=l.reset;
    if(password.closed!=40||password.cleared!=2||password.opened!=40||password.center||password.cursor||password.digits!=std::array<uint8_t,8>{}||
       l.windowX!=166||l.windowY!=112||l.lyc!=23||initial.display||initial.stat!=1||initial.lcdc!=0xc3||initial.scrollX||initial.scrollY||initial.servicesMasked||initial.pendingRequests||
       initial.timing.countdown!=54||!sound.enabled||sound.song!=7||sound.paused||sound.pendingEffect!=-1||std::any_of(initial.objects.begin(),initial.objects.end(),[](int value){return value!=0;}))throw std::runtime_error("Unowned initial password editing entry");
    AirPasswordEdit state;state.password=std::move(password);auto& p=state.password;auto& title=p.menu.page.close.fade.layout;auto& r=title.reset;auto& t=r.timing;
    AirClock clock;clock.now=t.end;clock.nextStat=t.nextStat;clock.nextVBlank=t.nextVBlank;clock.displays=t.displays;clock.statServices=t.stats;
    clock.interrupt=[&](const char* name,int64_t cycle,AirIrqOwner owner){interrupt(name,cycle,owner);};
    auto display=[&](bool){
        std::copy_n(r.objects.begin(),160,state.visibleObjects.begin());t.input.sample(sample?sample():t.input.held);
        if(t.input.held<0||t.input.held>255||(t.input.held&15)==15)throw std::runtime_error("Unowned password edit input/reset");
        int tick=t.tick;t.tick=(tick+1)&65535;sound.tick();if(sound.effectWorkCycles<0||sound.musicWorkCycles<0)throw std::runtime_error("Unowned password edit audio");
        service(clock.displays,clock.now+20,tick,t.countdown,116,sound.effectWorkCycles,sound.musicWorkCycles,t.input);return 1592+116+sound.effectWorkCycles+sound.musicWorkCycles;
    };
    clock.rasterWork=[&](int64_t start){return airTitleRasterWork(clock,title,0,start,raster,write);};
    auto store=[&](int64_t cycle,int address,int value){if(address>=0x9c00&&address<0xa000)r.window.at(address-0x9c00)=static_cast<uint8_t>(value);write(cycle,address,value);};
    AirResultWriter writer(clock,t.lcdEpoch,display,poll,store);writer.lcd.windowEnabled=true;writer.lcd.windowX=166;writer.lcd.windowY=112;writer.lcd.objectHeight=8;writer.lcd.objectsEnabled=true;writer.lcd.titleRightEdge=true;
    auto work=[&](std::initializer_list<int> costs){writer.work(costs);};auto point=[&](const char* name){boundary(name,clock.now,state);};
    auto object=[&](int slot,int value){write(clock.now,0xc100+slot,value);clock.atomicWork(16,[&]{r.objects.at(slot)=value;},display,false);};
    auto digit=[&](int value){write(clock.now,0xc0a0+p.cursor,value&255);clock.atomicWork(8,[&]{p.digits.at(p.cursor)=static_cast<uint8_t>(value);},display,false);};
    for(int iteration=0;;++iteration){
        if(iteration>=3000)throw std::runtime_error("Password edit exceeds diagnostic input extent");point("wait");clock.wait(display,false);++state.waits;point("ready");
        work({24,12,4,4,4,8});object(1,56+8*p.cursor);work({8});object(0,96);work({8});object(2,0x45);work({8});object(3,0x80);work({16});point("pointerReady");
        auto horizontal=[&](bool right){work({12,8,(t.input.pressed&(right?16:32))?24:12});if(t.input.pressed&(right?16:32)){
            work({12,8,right?8:4});bool bound=right?p.cursor==7:p.cursor==0;work({bound?20:8});if(!bound){write(clock.now,0xff9b,p.cursor+(right?1:-1));clock.atomicWork(12,[&]{p.cursor+=right?1:-1;},display,false);work({16});}
        }};
        horizontal(false);point("leftReturned");horizontal(true);point("rightReturned");
        auto vertical=[&](bool up){work({12,8,(t.input.pressed&(up?64:128))?24:12});if(!(t.input.pressed&(up?64:128)))return;
            work({12,12,16,4,4,20,8,12,8,4,8,up?4:8});int old=p.digits.at(p.cursor),value=up?old+1:(old-1)&255;digit(value);
            bool wrap=up?value==11:old<=1;
            if(up)work({8,wrap?12:16});else{work({old==0?12:8});if(old!=0)work({value?16:12});}
            if(wrap){work({8});value=up?1:10;digit(value);work({16});}
            writer.cursor=0x9ea6+p.cursor;for(int i=0;i<40;++i)writer.lcd.objects[i]={state.visibleObjects[4*i+1],state.visibleObjects[4*i]};writer.glyph(value);
        };
        vertical(true);point("upReturned");vertical(false);point("downReturned");work({12,8});point("submitDecision");state.submit=t.input.pressed&11;work({state.submit?8:12});if(state.submit)break;
    }
    point("end");t.end=clock.now;t.displays=clock.displays;t.stats=clock.statServices;t.nextStat=clock.nextStat;t.nextVBlank=clock.nextVBlank;return state;
}
}
