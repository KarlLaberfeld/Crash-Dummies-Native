#pragma once
#include <cstdint>
#include <stdexcept>

namespace ticd {
// Input belongs to display sampling, including displays without a game update.
// Extra samples can clear a fresh edge before gameplay next reads the buttons.
struct DisplayInput {
    int held=0,previous=0,pressed=0;
    void sample(int buttons){previous=held;held=buttons;pressed=held&~previous;}
};
// Semantic Air display clock, measured in original oscillator cycles. It runs
// no opcodes or CPU state. The callback owns display/audio services and returns
// source-derived work. Unknown work is a hard boundary, never an allowance.
struct AirClock {
    static constexpr int Frame=70224,StatLine=135*456,VBlankLine=144*456;
    int64_t now=16,nextStat=StatLine,nextVBlank=VBlankLine;
    unsigned displays=0,statServices=0;
    template<class Display>void vblank(Display&& display,bool ready){
        int work=display(ready);
        if(work<0)throw std::runtime_error("Unreconstructed Air display/audio work");
        now+=20+work+16;++displays;
    }
    void stat(){now+=20+288+16;++statServices;}
    template<class Display>void startup(Display&& display){
        // LCD enable completes before RET(16). EI(4) takes effect after LD(8).
        // Source IF/IE retain both pending services. The ready store costs 12.
        now+=4+8;vblank(display,true);stat();now+=12;
    }
    template<class Display>void work(int cost,Display&& display,bool ready){
        if(cost<0)throw std::runtime_error("Unreconstructed Air game work");
        while(cost||(nextStat<nextVBlank?nextStat:nextVBlank)<=now){
            int64_t deadline=nextStat<nextVBlank?nextStat:nextVBlank;
            if(now+cost<deadline){now+=cost;return;}
            int before=static_cast<int>(deadline-now);
            if(before>0){cost-=before;now=deadline;}
            if(nextStat<nextVBlank){nextStat+=Frame;stat();}
            else{nextVBlank+=Frame;vblank(display,ready);}
        }
    }
    template<class Effect,class Display>void atomicWork(int cost,Effect&& effect,Display&& display,bool ready){
        if(cost<0)throw std::runtime_error("Unreconstructed Air atomic work");
        now+=cost;effect();work(0,display,ready);
    }
    template<class Display>void wait(Display&& display,bool ready=true){
        // CALL/PUSH precede the counter read. A display during that prefix
        // must belong to the new snapshot, so the wait needs a later VBlank.
        // The 16-cycle read commits before a pending service; LD B costs 4.
        work(40,display,ready);
        unsigned counter=displays;
        atomicWork(16,[&]{counter=displays;},display,ready);
        work(4,display,ready);
        do{
            now+=4;
            int64_t deadline=nextStat<nextVBlank?nextStat:nextVBlank;
            if(now<deadline)now=deadline;
            if(nextStat<nextVBlank){nextStat+=Frame;stat();now+=16+4+12;}
            else{nextVBlank+=Frame;vblank(display,ready);now+=16+4+8+12+16;}
        }while(displays==counter);
    }
};
}
