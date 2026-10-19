#pragma once
#include "air_clock.h"
#include "air_celebration.h"

namespace ticd {
struct AirResultPrefix {
    int64_t end=0,lcdDisabled=0;
    int pollReads=0,pendingRequests=0,display=10,stat=0,countdown=600;
    AirCelebration celebration;
};
// The identified common result setup, 0409..0462. Native fixed-size graphics
// operations run with the LCD/services disabled. Neither source instructions
// nor observed clocks are executed. The perfect branch initializes native
// emitters while services are masked; later celebration display is separate.
inline int airResultScanline(int64_t sampleTime){
    int position=static_cast<int>((sampleTime+8)%AirClock::Frame),line=position/456,dot=position%456;
    // Pinned DMG source: LY changes two dots into a line; on line 153 it
    // briefly reads 153, then resets to zero after four more dots. This is a
    // read-only line owner, not a pixel/STAT/CPU implementation.
    if(line==153)return dot<=2?152:dot<=6?153:0;
    return dot<=2&&line?line-1:line;
}
template<class Boundary,class Poll>
AirResultPrefix airResultSetupPrefix(const AirClock& gameClock,int result,Boundary&& boundary,Poll&& poll,int randomState=-1,int64_t lcdEpoch=0){
    if(gameClock.servicesHeld||lcdEpoch<0||gameClock.now-lcdEpoch<AirClock::Frame||!(result&1)||
       ((result&4)&&(result!=7||randomState<0||randomState>65535)))
        throw std::runtime_error("Unowned Air result/celebration prefix");
    AirResultPrefix prefix;int64_t now=gameClock.now;
    if(randomState>=0&&randomState<=65535)prefix.celebration.randomState=randomState;
    boundary("begin",now);
    // DI, caller, LCD-on test and saved IE / VBlank mask before the LY poll.
    now+=4+100;
    for(;;){
        if(prefix.pollReads>=2200)throw std::runtime_error("Air LCD-off equality wait did not terminate");
        // Absolute completion times continue across result/instruction/retry
        // cycles; scanline reads belong to the most recent native LCD start.
        int line=airResultScanline(now+8-lcdEpoch);now+=12;++prefix.pollReads;poll(now,line);
        now+=8;if(line==145){now+=8;break;}now+=12;
    }
    // LCD read/mask/write complete before IE restoration and the return.
    now+=12+8+12;prefix.lcdDisabled=now;
    prefix.pendingRequests=(gameClock.nextStat<=now?2:0)|(gameClock.nextVBlank<=now?1:0);
    now+=16+12+16;boundary("lcdOffReturned",now);
    // 195c clears all 256 bytes, including the unused OAM-list tail.
    now+=12+24+4+256*24-4+16;boundary("objectsCleared",now);
    now+=96;boundary("registersReady",now);
    // Each map: caller/setup 84, 1024 identified blank stores through 2120
    // (144 each at LCD-off), last branch -4, return 16.
    now+=2*(84+1024*144-4+16);boundary("mapsCleared",now);
    now+=144;
    if(result&4){
        // Taken conditional call adds 12; four selector/countdown stores cost
        // 96. Calls for emitters 0..2 have a 36-cycle pointer/call prefix;
        // emitter 3 is a tail call with a 28-cycle prefix.
        now+=12+96;prefix.display=2;prefix.stat=4;prefix.countdown=720;
        boundary("celebrationSelected",now);
        static constexpr const char* names[]={"emitter0Ready","emitter1Ready","emitter2Ready"};
        for(int i=0;i<4;++i){prefix.celebration.reset(i);now+=(i==3?28:36)+AirCelebration::ResetWork;
            if(i<3)boundary(names[i],now);}
    }
    boundary("flagsReady",now);
    now+=68;boundary("tilesBank",now);
    // Fixed 4096-byte copy to 8000..8fff, with the LCD-off access test. The
    // destination does not reach 9800's wrap branch in this copy.
    now+=60+4096*104-4+16;boundary("tilesReady",now);
    now+=68;boundary("dataBank",now);
    now+=88;boundary("playerReady",now);
    prefix.end=now;boundary("lcdDisabled",prefix.lcdDisabled);return prefix;
}
}
