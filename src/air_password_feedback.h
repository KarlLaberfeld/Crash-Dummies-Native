#pragma once
#include "air_password_edit.h"
namespace ticd {
struct AirPasswordFeedback {AirPasswordEdit edit;int candidate=-1,action=-1,center=0,closed=0,cleared=0,opened=0,remaining=60,startDay=1,startDifficulty=0;bool musicTest=false;};
// Submission through feedback and its handler return. Ten decoded password
// rows are compared as data. The music-test action stops before its screen.
template<class Boundary,class Service,class Interrupt,class Raster,class Poll,class Write>
AirPasswordFeedback airPasswordFeedback(AirPasswordEdit edit,NativeAudio& sound,const UiAssets& ui,int startDay,int startDifficulty,
    Boundary&& boundary,Service&& service,Interrupt&& interrupt,Raster&& raster,Poll&& poll,Write&& write,std::function<int()> sample={}){
    const auto& l=edit.password.menu.page.close.fade.layout;const auto& r0=l.reset;
    if(!edit.submit||(edit.submit&~11)||edit.submit!=(r0.timing.input.pressed&11)||edit.password.cursor<0||edit.password.cursor>7||l.windowX!=166||l.windowY!=112||l.lyc!=23||
       r0.display||r0.stat!=1||r0.lcdc!=0xc3||r0.scrollX||r0.scrollY||r0.servicesMasked||r0.pendingRequests||r0.timing.countdown!=54||!sound.enabled||sound.song!=7||sound.paused||sound.pendingEffect!=-1||startDay<0||startDay>4||startDifficulty<0||startDifficulty>3||
       std::any_of(edit.password.digits.begin(),edit.password.digits.end(),[](int v){return v>10;}))throw std::runtime_error("Unowned password feedback entry");
    AirPasswordFeedback state;state.edit=std::move(edit);state.startDay=startDay;state.startDifficulty=startDifficulty;
    auto& p=state.edit.password;auto& title=p.menu.page.close.fade.layout;auto& r=title.reset;auto& t=r.timing;
    AirClock clock;clock.now=t.end;clock.nextStat=t.nextStat;clock.nextVBlank=t.nextVBlank;clock.displays=t.displays;clock.statServices=t.stats;
    clock.interrupt=[&](const char* name,int64_t cycle,AirIrqOwner owner){interrupt(name,cycle,owner);};
    bool resetting=false;
    auto display=[&](bool){
        if(resetting)throw std::runtime_error("Unowned display during password stop reset");
        std::copy_n(r.objects.begin(),160,state.edit.visibleObjects.begin());t.input.sample(sample?sample():t.input.held);if(t.input.held<0||t.input.held>255||(t.input.held&15)==15)throw std::runtime_error("Unowned password feedback input/reset");
        int tick=t.tick;t.tick=(tick+1)&65535;sound.tick();if(sound.effectWorkCycles<0||sound.musicWorkCycles<0)throw std::runtime_error("Unowned password feedback audio");
        service(clock.displays,clock.now+20,tick,t.countdown,116,sound.effectWorkCycles,sound.musicWorkCycles,t.input);return 1592+116+sound.effectWorkCycles+sound.musicWorkCycles;
    };
    clock.rasterWork=[&](int64_t start){return airTitleRasterWork(clock,title,state.center,start,raster,write);};
    auto store=[&](int64_t cycle,int address,int value){if(address>=0x9c00&&address<0xa000)r.window.at(address-0x9c00)=static_cast<uint8_t>(value);write(cycle,address,value);};
    AirResultWriter writer(clock,t.lcdEpoch,display,poll,store);writer.lcd.windowEnabled=true;writer.lcd.windowX=166;writer.lcd.windowY=72;writer.lcd.objectHeight=8;writer.lcd.objectsEnabled=true;writer.lcd.titleRightEdge=true;
    auto work=[&](std::initializer_list<int> costs){writer.work(costs);};auto point=[&](const char* name){boundary(name,clock.now,state,sound.enabled);};
    point("begin");work({16});point("finalWait");clock.wait(display,false);point("waitReturned");
    // Fixed reset operations allow the title raster to interrupt at their
    // actual completions. No display may observe partially reset voices.
    resetting=true;work({24,8,4,24,4,12,12,8});
    for(int i=0;i<44;++i)work({8,4,i==43?8:12});work({12,12});
    for(int i=0;i<250;++i)work({4,8,8,4,4,i==249?8:12});work({4});
    for(int i=0;i<7;++i)work({12,8});work({8});for(int i=0;i<4;++i)work({12,8});work({16,12,12,12,24});
    for(int i=0;i<16;++i)work({8,8,8,8,4,4,i==15?8:12});work({16,4,12,16,4,12,16});
    sound.stop();resetting=false;point("audioStopped");
    work({24,8,4,4});for(int i=0;i<160;++i){write(clock.now,0xc100+i,0);clock.atomicWork(8,[&]{r.objects[i]=0;},display,false);}work({4,16});point("objectsCleared");work({24});point("validate");work({12});
    for(int candidate=0;candidate<=10;++candidate){
        state.candidate=candidate;point("check");work({8,8,candidate==10?12:8});if(candidate==10)break;
        work({12,24,8,8});bool equal=true;
        for(int i=0;i<8;++i){bool same=p.digits[i]==ui.passwords[candidate][i];equal&=same;work({8,8,same?12:8});if(!same)work({4});work({8,8,4,i==7?8:12});}
        work({4,4,16});point("compareReturned");work({equal?12:8});if(equal){state.action=candidate;break;}work({8,8,12});
    }
    point(state.action<0?"rejected":"accepted");if(state.action>=0)work({16});work({24});
    for(int step=0;step<40;++step){point("closeWait");clock.wait(display,false);point("closeReady");work({12});write(clock.now,0xff4a,title.windowY-1);clock.atomicWork(12,[&]{--title.windowY;},display,false);work({16,8});write(clock.now,0xc09c,(state.center-2)&255);clock.atomicWork(16,[&]{state.center=(state.center-2)&255;++state.closed;},display,false);point("centerStored");work({8,step==39?8:12});}
    for(int pass=0;pass<2;++pass){
        if(pass)work({24});point("clearEntry");work({12,12});
        for(int cell=0;cell<320;++cell){for(int tries=0;;++tries){if(tries>32)throw std::runtime_error("Password feedback clear did not terminate");int mode=-1;clock.accessWork(12,8,[&]{mode=writer.lcd.mode(clock.now-t.lcdEpoch);},display,false);if(mode<0)throw std::runtime_error("Unowned feedback clear geometry");poll(clock.now,mode);work({8,mode&2?12:8});if(!(mode&2))break;}store(clock.now,0x9dc0+cell,0);clock.atomicWork(8,[]{},display,false);work({8,4,4,cell==319?8:12});}
        work({16});++state.cleared;point(pass?"clearReturned":"closeReturned");
    }
    std::vector<AirResultTextCommand> commands{{1,1,19}};for(int i=0;i<18;++i){int value=ui.hiddenMaps[state.action<0?1:2][19*32+1+i];if(value>=128)throw std::runtime_error("Unowned password feedback glyph");commands.push_back({0,value,0});}commands.push_back({4,0,0});writer.text(commands);point("textReturned");work({24});
    for(int step=0;step<40;++step){point("openWait");clock.wait(display,false);point("openReady");work({12});write(clock.now,0xff4a,title.windowY+1);clock.atomicWork(12,[&]{++title.windowY;},display,false);work({16,8});write(clock.now,0xc09c,(state.center+2)&255);clock.atomicWork(16,[&]{state.center=(state.center+2)&255;++state.opened;},display,false);point("openStored");work({step==39?8:12});}
    work({16});point("opened");work({12,state.action<0?16:24});
    for(int i=0;i<60;++i){point("holdWait");clock.wait(display,false);point("holdReady");work({8,4,4,i==59?8:12});--state.remaining;}
    work({16});if(state.action>=0){point("handlerDispatch");work({12,8,8,4,4});if(state.action<9){point("actionEntry");work({8});write(clock.now,state.action<5?0xc006:0xc007,state.action<5?state.action:state.action-5);clock.atomicWork(16,[&]{if(state.action<5)state.startDay=state.action;else state.startDifficulty=state.action-5;},display,false);work({16});}else state.musicTest=true;}
    point("end");t.end=clock.now;t.displays=clock.displays;t.stats=clock.statServices;t.nextStat=clock.nextStat;t.nextVBlank=clock.nextVBlank;return state;
}
}
