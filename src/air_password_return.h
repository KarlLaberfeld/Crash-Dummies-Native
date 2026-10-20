#pragma once
#include "air_password_feedback.h"
namespace ticd {
struct AirPasswordReturn {AirPasswordFeedback feedback;int target=0,center=0,closed=0,cleared=0,opened=0,rows=0,tune=0,effect=0,lastTune=255;};
// Complete return to page zero/password input, or first music-test display.
// Title composition reuses the existing page-zero owner with the retained
// caller clock; password/test layouts use their already decoded glyph data.
template<class Boundary,class Service,class Interrupt,class Raster,class Poll,class Write>
AirPasswordReturn airPasswordReturn(AirPasswordFeedback feedback,NativeAudio& sound,const UiAssets& ui,
    Boundary&& boundary,Service&& service,Interrupt&& interrupt,Raster&& raster,Poll&& poll,Write&& write,std::function<int()> sample={},bool afterMusicTest=false){
    const auto& l0=feedback.edit.password.menu.page.close.fade.layout;const auto& r0=l0.reset;
    if(feedback.remaining||feedback.center||feedback.closed!=40||feedback.cleared!=2||feedback.opened!=40||feedback.musicTest!=(feedback.action==9)||
       (afterMusicTest&&(!feedback.musicTest||!(feedback.edit.submit&8)))||
       l0.windowX!=166||l0.windowY!=112||l0.lyc!=23||r0.display||r0.stat!=1||r0.lcdc!=0xc3||r0.scrollX||r0.scrollY||r0.servicesMasked||r0.pendingRequests||r0.timing.countdown!=54||(!afterMusicTest&&sound.enabled)||sound.paused||sound.pendingEffect!=-1||
       std::any_of(r0.objects.begin(),r0.objects.end(),[](int v){return v!=0;}))throw std::runtime_error("Unowned password return entry");
    AirPasswordReturn state;state.feedback=std::move(feedback);state.target=!afterMusicTest&&state.feedback.musicTest?3:(state.feedback.edit.submit&8)?1:2;
    auto& p=state.feedback.edit.password;auto& title=p.menu.page.close.fade.layout;auto& r=title.reset;auto& t=r.timing;
    AirClock clock;clock.now=t.end;clock.nextStat=t.nextStat;clock.nextVBlank=t.nextVBlank;clock.displays=t.displays;clock.statServices=t.stats;
    clock.interrupt=[&](const char* name,int64_t cycle,AirIrqOwner owner){interrupt(name,cycle,owner);};bool resetting=false;
    auto display=[&](bool){
        if(resetting)throw std::runtime_error("Unowned display during return music reset");
        t.input.sample(sample?sample():t.input.held);if(t.input.held<0||t.input.held>255||(t.input.held&15)==15)throw std::runtime_error("Unowned return input/reset");
        int tick=t.tick;t.tick=(tick+1)&65535;sound.tick();if(sound.effectWorkCycles<0||sound.musicWorkCycles<0)throw std::runtime_error("Unowned return audio");
        service(clock.displays,clock.now+20,tick,t.countdown,116,sound.effectWorkCycles,sound.musicWorkCycles,t.input);return 1592+116+sound.effectWorkCycles+sound.musicWorkCycles;
    };
    clock.rasterWork=[&](int64_t start){return airTitleRasterWork(clock,title,state.center,start,raster,write);};
    auto store=[&](int64_t cycle,int address,int value){if(address>=0x9c00&&address<0xa000)r.window.at(address-0x9c00)=static_cast<uint8_t>(value);write(cycle,address,value);};
    AirResultWriter writer(clock,t.lcdEpoch,display,poll,store);writer.lcd.windowEnabled=true;writer.lcd.windowX=166;writer.lcd.windowY=72;writer.lcd.objectHeight=8;writer.lcd.objectsEnabled=true;writer.lcd.titleRightEdge=true;
    auto work=[&](std::initializer_list<int> costs){writer.work(costs);};auto point=[&](const char* name){boundary(name,clock.now,state,sound.enabled,sound.song);};
    auto sync=[&]{t.end=clock.now;t.displays=clock.displays;t.stats=clock.statServices;t.nextStat=clock.nextStat;t.nextVBlank=clock.nextVBlank;};
    auto music=[&](int song){
        work({8,24,4,12,8,4,24});resetting=true;work({4,12,12,8});
        for(int i=0;i<44;++i)work({8,4,i==43?8:12});work({12,12});for(int i=0;i<250;++i)work({4,8,8,4,4,i==249?8:12});work({4});
        for(int i=0;i<7;++i)work({12,8});work({8});for(int i=0;i<4;++i)work({12,8});work({16,12,12,12,24});for(int i=0;i<16;++i)work({8,8,8,8,4,4,i==15?8:12});work({16,4,12,16});
        for(int i=0;i<8;++i)work({12,8,8,12});work({12,12,12,24});for(int i=0;i<23;++i)work({8,8,8,8,4,4,i==22?8:12});work({16,8,12,4,16,16,8,16,16});sound.playMusic(song);resetting=false;
    };
    point("begin");
    if(state.target!=3){
        work({12,8,state.target==2?16:12});
        if(state.target==1){work({4});write(clock.now,0xc03e,0);clock.atomicWork(16,[&]{p.menu.index=0;},display,false);point("titleWait");clock.wait(display,false);point("titleWaitReturned");music(1);point("titleMusicReady");work({16});}
    }
    point("closeCall");work({24});
    for(int step=0;step<40;++step){point("closeWait");clock.wait(display,false);point("closeReady");work({12});write(clock.now,0xff4a,title.windowY-1);clock.atomicWork(12,[&]{--title.windowY;},display,false);work({16,8});write(clock.now,0xc09c,(state.center-2)&255);clock.atomicWork(16,[&]{state.center=(state.center-2)&255;++state.closed;},display,false);point("centerStored");work({8,step==39?8:12});}
    if(state.target==1){
        sync();AirTitleClose close;close.fade=p.menu.page.close.fade;close.center=176;close.steps=40;
        auto page=airTitlePage(close,sound,ui,
            [&](const char* name,int64_t cycle,const AirTitlePage& s){if(std::string(name)=="begin")return;state.center=s.close.center;state.cleared=s.cleared;state.opened=s.opened;state.rows=s.rows;p.menu.page.close.fade=s.close.fade;boundary(std::string(name)=="centerStored"?"openStored":std::string(name)=="end"?"end":name,cycle,state,sound.enabled,sound.song);},
            service,interrupt,raster,poll,write,sample,true);
        p.menu.page=std::move(page);p.menu.index=p.menu.route=p.menu.waits=p.menu.unlockProgress=0;p.menu.remaining=480;return state;
    }
    for(int pass=0;pass<2;++pass){
        if(pass)work({24});point("clearEntry");work({12,12});
        for(int cell=0;cell<320;++cell){for(int tries=0;;++tries){if(tries>32)throw std::runtime_error("Password return clear did not terminate");int mode=-1;clock.accessWork(12,8,[&]{mode=writer.lcd.mode(clock.now-t.lcdEpoch);},display,false);if(mode<0)throw std::runtime_error("Unowned password return graphics readiness");poll(clock.now,mode);work({8,mode&2?12:8});if(!(mode&2))break;}store(clock.now,0x9dc0+cell,0);clock.atomicWork(8,[]{},display,false);work({8,4,4,cell==319?8:12});}
        work({16});++state.cleared;point(pass?"clearReturned":"closeReturned");
    }
    std::vector<AirResultTextCommand> commands;auto row=[&](int x,int y,int length,int map){commands.push_back({1,x,y});for(int i=0;i<length;++i){int value=ui.hiddenMaps[map][32*y+x+i];if(value>=128)throw std::runtime_error("Unowned return/test glyph");commands.push_back({0,value,0});}};
    if(state.target==2){row(5,16,10,0);row(3,19,14,0);row(6,21,8,0);}else{row(5,16,10,3);row(2,19,16,3);row(2,21,16,3);}commands.push_back({4,0,0});writer.text(commands);point("textReturned");
    if(state.target==2){clock.wait(display,false);point("passwordWaitReturned");music(7);point("passwordMusicReady");}
    work({24});for(int step=0;step<40;++step){point("openWait");clock.wait(display,false);point("openReady");work({12});write(clock.now,0xff4a,title.windowY+1);clock.atomicWork(12,[&]{++title.windowY;},display,false);work({16,8});write(clock.now,0xc09c,(state.center+2)&255);clock.atomicWork(16,[&]{state.center=(state.center+2)&255;++state.opened;},display,false);point("openStored");work({step==39?8:12});}
    work({16});point("openReturned");work({4});write(clock.now,0xff9b,0);clock.atomicWork(12,[&]{p.cursor=0;},display,false);
    if(state.target==2){for(int i=0;i<8;++i){write(clock.now,0xc0a0+i,0);clock.atomicWork(16,[&]{p.digits[i]=0;},display,false);}}
    else{write(clock.now,0xff9c,0);work({12,4});write(clock.now,0xff9d,255);work({12});state.tune=state.effect=0;state.lastTune=255;}
    point("end");sync();return state;
}
}
