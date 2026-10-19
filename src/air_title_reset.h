#pragma once
#include "air_game_over_return.h"

namespace ticd {
struct AirTitleReset {
    AirResultTransition timing;
    UiMap background{},window{};
    std::array<uint8_t,256> objects{};
    int64_t lcdDisabled=0;
    int pollReads=0,pendingRequests=0,display=0,stat=0,bank=1,lcdc=0x5b;
    int scrollX=0,scrollY=0,objectCount=0;
    bool servicesMasked=true;
};
// 019c..0206 only: the post-game-over masked reset, blank maps/objects and
// fixed title graphics copy work. Graphics payload/pixels and the subsequent
// first-boot decision/title layout have separate owners. No services run or
// audio advances while masked; the old LCD epoch is retained as history only.
template<class Boundary,class Poll,class Write>
AirTitleReset airTitleResetPrefix(AirResultTransition timing,const NativeAudio& sound,
    Boundary&& boundary,Poll&& poll,Write&& write){
    if(timing.lives||timing.displays!=546||timing.stats!=546||timing.countdown!=54||
       timing.lcdEpoch<0||timing.end-timing.lcdEpoch<AirClock::Frame||
       std::min(timing.nextStat,timing.nextVBlank)<=timing.end||!sound.enabled||sound.song!=13)
        throw std::runtime_error("Unowned post-game-over title reset");
    // Result setup's 0421 LCD value is 5b, then its owned restart sets bit 7.
    AirTitleReset state;state.timing=timing;state.bank=1;state.lcdc=0xdb;
    int64_t now=timing.end;
    auto point=[&](const char* name){state.timing.end=now;boundary(name,now,state);};
    point("begin");now+=4+100;
    for(;;){
        if(state.pollReads>=2200)throw std::runtime_error("Title LCD-off equality wait did not terminate");
        int line=airResultScanline(now+8-timing.lcdEpoch);now+=12;++state.pollReads;poll(now,line);
        now+=8;if(line==145){now+=8;break;}now+=12;
    }
    now+=12+8+12;state.lcdc&=127;state.lcdDisabled=now;
    state.pendingRequests=(timing.nextStat<=now?2:0)|(timing.nextVBlank<=now?1:0);
    now+=16+12+16;point("lcdOffReturned");
    // 25af's two 1024-cell clears, with the LCD-off 2120 access owner.
    for(int map=0;map<2;++map){
        now+=8+24+16+12+16+4+4;
        auto& cells=map?state.background:state.window;
        for(int i=0;i<1024;++i){
            now+=4+24+16+12+8+8+12;write(now,(map?0x9800:0x9c00)+i,0);
            cells[i]=0;now+=8+8+16+8+4+4+(i==1023?8:12);
        }
        now+=16;point(map?"backgroundCleared":"windowCleared");
    }
    now+=12+24+4;
    for(int i=0;i<256;++i){write(now,0xc100+i,0);state.objects[i]=0;now+=8+4+(i==255?8:12);}
    now+=16;point("objectsCleared");
    // Object count, scroll and the fixed title/campaign selector clears.
    for(int address:{0xff8f,0xff42,0xff43,0xc03e,0xc09c,0xc09d,0xc085,0xc086,0xc087,0xc08d,0xc08e,0xc08f,0xc098,0xc099,0xc082}){
        write(now,address,0);now+=address>=0xff00?12:16;
    }
    now+=4;write(now,0xff8a,255);now+=12;state.timing.input.held=255;point("stateReset");
    // Title script selection, decoded graphics bank, two fixed copy wrappers.
    now+=12+4+16+4+16+8+16+12+16+16;state.bank=3;point("tilesBank");
    now+=12+12+12+24+1920*104-4+16;point("upperTilesReady");
    now+=12+12+12+24+4096*104-4+16;point("lowerTilesReady");
    now+=8+16+12+16+16;state.bank=1;point("dataBank");return state;
}
}
