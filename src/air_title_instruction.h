#pragma once
#include "air_title_start.h"
namespace ticd {
struct AirTitleInstruction {AirTitleStart start;int polls=0;int64_t lcdDisabled=0;};
// 0272..0292: masked LCD-off equality wait and instruction register setup.
// Campaign configuration, map clearing and LCD restart remain separate.
template<class Boundary,class Poll,class Write>
AirTitleInstruction airTitleInstruction(AirTitleStart start,const NativeAudio& sound,Boundary&& boundary,Poll&& poll,Write&& write){
    const auto& l=start.menu.page.close.fade.layout;const auto& r=l.reset;const auto& t=r.timing;
    if(start.menu.route!=2||start.palettes!=8||start.waits!=32||r.servicesMasked||r.pendingRequests||r.display||r.stat!=2||r.lcdc!=0xfb||
       r.scrollX||r.scrollY!=88||l.lyc!=103||(!start.menu.selectedPlayers&&!start.menu.carouselOwned&&(t.displays!=698||t.stats!=927))||t.countdown!=54||sound.enabled||sound.song!=-1||
       std::min(t.nextStat,t.nextVBlank)<=t.end)throw std::runtime_error("Unowned masked instruction setup entry");
    AirTitleInstruction state;state.start=std::move(start);auto& title=state.start.menu.page.close.fade.layout;auto& out=title.reset;auto& timing=out.timing;
    int64_t now=timing.end;auto point=[&](const char* name){boundary(name,now,state);};
    point("begin");out.servicesMasked=true;now+=4+100;
    for(;;){
        if(state.polls>=2200)throw std::runtime_error("Instruction LCD-off equality wait did not terminate");
        int line=airResultScanline(now+8-timing.lcdEpoch);now+=12;++state.polls;poll(now,line);now+=8;
        if(line==145){now+=8;break;}now+=12;
    }
    now+=12+8;write(now,0xff40,out.lcdc&127);now+=12;out.lcdc&=127;state.lcdDisabled=now;
    out.pendingRequests=(timing.nextStat<=now?2:0)|(timing.nextVBlank<=now?1:0);now+=16+12+16;point("lcdOffReturned");
    now+=8;write(now,0xc098,5);now+=16;out.display=5;write(now,0xc099,5);now+=16;out.stat=5;now+=4;
    write(now,0xff43,0);now+=12;out.scrollX=0;write(now,0xff42,0);now+=12;out.scrollY=0;
    write(now,0xc09c,0);now+=16;now+=8;write(now,0xff45,95);now+=12;title.lyc=95;
    now+=8;write(now,0xff41,0x44);now+=12;now+=8;write(now,0xff40,0x51);now+=12;out.lcdc=0x51;
    point("end");timing.end=now;return state;
}
}
