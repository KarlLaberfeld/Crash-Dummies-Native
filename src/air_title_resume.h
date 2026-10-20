#pragma once
#include "air_title_campaign.h"
namespace ticd {
struct AirTitleResume {AirTitleCampaign fresh;int result=0;};
// 02bc..02ce: EI's completed CALL follower, the two inherited requests,
// native current-player lives and the first LCD-on background clear.
template<class Boundary,class Service,class Interrupt,class Poll,class Write>
AirTitleResume airTitleResume(AirTitleCampaign fresh,int result,NativeAudio& sound,
    Boundary&& boundary,Service&& service,Interrupt&& interrupt,Poll&& poll,Write&& write,std::function<int()> sample={}){
    const auto& l=fresh.instruction.start.menu.page.close.fade.layout;const auto& r=l.reset;const auto& t=r.timing;
    if(!r.servicesMasked||r.pendingRequests!=3||r.lcdc!=0xd1||r.display!=5||r.stat!=5||r.scrollX||r.scrollY||l.lyc!=95||!l.bootShown||
       t.end!=t.lcdEpoch+20||t.nextStat!=t.lcdEpoch+95*456||t.nextVBlank!=t.lcdEpoch+144*456||
       sound.enabled||sound.paused||sound.song!=-1||sound.pendingEffect!=-1||fresh.instruction.start.menu.page.close.center||!fresh.campaign.active||fresh.campaign.current!=0||
       fresh.campaign.players[0].lives!=5||t.lives!=5||result!=33||
       std::any_of(r.objects.begin(),r.objects.end(),[](int v){return v!=0;})||
       std::any_of(r.window.begin(),r.window.end(),[](int v){return v!=0;}))throw std::runtime_error("Unowned instruction resume entry");
    AirTitleResume state{std::move(fresh),result};auto& out=state.fresh.instruction.start.menu.page.close.fade.layout.reset;auto& timing=out.timing;
    AirClock clock;clock.now=timing.end;clock.nextStat=timing.nextStat;clock.nextVBlank=timing.nextVBlank;clock.displays=timing.displays;clock.statServices=timing.stats;
    clock.interrupt=[&](const char* kind,int64_t cycle,AirIrqOwner owner){interrupt(kind,cycle,owner);};
    auto display=[&](bool){
        timing.input.sample(sample?sample():timing.input.held);
        if(timing.input.held<0||timing.input.held>255||(timing.input.held&15)==15)throw std::runtime_error("Unowned instruction resume input/reset");
        // Callback 5 clears vertical scroll; it never decrements countdown.
        // DMA/joypad prefix 1164 + callback dispatch 116 + XOR 4 = 1284
        // before the SCY store. These are source work, not observed padding.
        write(clock.now+20+1284,0xff42,0);out.scrollY=0;
        int tick=timing.tick;timing.tick=(tick+1)&65535;sound.tick();
        if(sound.effectWorkCycles<0||sound.musicWorkCycles<0)throw std::runtime_error("Unowned instruction resume audio");
        service(clock.displays,clock.now+20,tick,timing.countdown,144,sound.effectWorkCycles,sound.musicWorkCycles,timing.input);
        return 1592+144+sound.effectWorkCycles+sound.musicWorkCycles;
    };
    clock.rasterWork=[&](int64_t start){
        // Callback 5 copies the retained zero center into SCY. Prefix 200,
        // center read 16, store 12, jump 12 and four pops 48 precede RETI.
        write(start+216,0xff42,0);out.scrollY=0;return 288;
    };
    auto store=[&](int64_t cycle,int address,int value){write(cycle,address,value);
        if(address>=0x9800&&address<0x9c00)out.background[address-0x9800]=static_cast<unsigned char>(value);};
    AirResultWriter writer(clock,timing.lcdEpoch,display,poll,store);writer.cursor=writer.layer=0x9800;
    // Complete original polls qualify empty, unscrolled, window-disabled
    // later visible lines, line 143 and VBlank of the restart frame. No
    // first-line owner is implied. Every mode read is still independent.
    writer.lcd.instructionRestartFrame=true;
    auto work=[&](std::initializer_list<int> costs){writer.work(costs);};
    auto point=[&](const char* name){boundary(name,clock.now,state);};
    point("begin");clock.now+=4+24;out.servicesMasked=false;out.pendingRequests=0;
    clock.vblank(display,false,AirIrqOwner::PendingStartup);clock.stat(AirIrqOwner::PendingStartup);point("selectionEntry");
    // Select current player's native life record; CALL already completed.
    work({16,4,4,4,8,4,8,16});point("livesTest");work({8,4,12});point("backgroundClear");
    work({8,24});point("clearEntry");write(clock.now,0xc035,0x98);work({16,12,16,4,4});
    for(int cell=0;cell<1024;++cell){work({4,24});writer.glyph(0);work({8,4,4,cell==1023?8:12});}
    work({16});point("backgroundCleared");work({4});write(clock.now,0xc095,0);clock.atomicWork(16,[&]{state.result=0;},display,false);point("end");
    timing.end=clock.now;timing.displays=clock.displays;timing.stats=clock.statServices;timing.nextStat=clock.nextStat;timing.nextVBlank=clock.nextVBlank;return state;
}
}
