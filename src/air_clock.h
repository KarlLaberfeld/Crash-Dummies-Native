#pragma once
#include <cstdint>
#include <functional>
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
    // Epoch: beginning of LCD-on's last access portion. Its remaining four
    // cycles and the identified return (16) precede 03c6's EI. The old epoch
    // omitted that access tail; HALT hid it in ordinary-update comparisons.
    int64_t now=4+16,nextStat=StatLine,nextVBlank=VBlankLine;
    unsigned displays=0,statServices=0;
    int lastWaitWork=0;
    // Optional bounded image observer. It charges no work and executes no IRQ
    // instructions; halted distinguishes accepted counter-wait ownership.
    std::function<void(int64_t,bool)> objectDisable;
    template<class Display>void vblank(Display&& display,bool ready){
        int work=display(ready);
        if(work<0)throw std::runtime_error("Unreconstructed Air display/audio work");
        now+=20+work+16;++displays;
    }
    void stat(bool halted=false){
        // 0048..254f: source body prefix 228, then LCDC write sample at +8.
        // The pinned DMG bus observer exposes that sample two cycles earlier.
        if(objectDisable)objectDisable(now+20+228+8-2,halted);
        now+=20+288+16;++statServices;
    }
    template<class Display,class Boundary>void startup(Display&& display,Boundary&& boundary){
        // EI(4) takes effect after LD(8), following the completed access/return.
        // Source IF/IE retain both pending services. The ready store costs 12.
        boundary("enableReturned",now);
        now+=4+8;boundary("displayEntry",now+20);vblank(display,true);
        boundary("displayReturned",now);boundary("statEntry",now+20);stat();
        boundary("statReturned",now);now+=12;boundary("readyStored",now);
    }
    template<class Display>void startup(Display&& display){
        startup(display,[](const char*,int64_t){});
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
    // One identified graphics access: its bus sample occurs before the end
    // of the access, while a pending interrupt waits until completion. This
    // is a semantic boundary, not an opcode/register execution interface.
    template<class Effect,class Display>void accessWork(int cost,int sampleOffset,Effect&& effect,Display&& display,bool ready){
        if(cost<=0||sampleOffset<0||sampleOffset>cost)
            throw std::runtime_error("Invalid Air graphics access boundary");
        now+=sampleOffset;effect();now+=cost-sampleOffset;
        work(0,display,ready);
    }
    template<class Display>void wait(Display&& display,bool ready=true){
        lastWaitWork=60;
        // CALL/PUSH precede the counter read. A display during that prefix
        // must belong to the new snapshot, so the wait needs a later VBlank.
        // The 16-cycle read commits before a pending service; LD B costs 4.
        work(40,display,ready);
        unsigned counter=displays;
        atomicWork(16,[&]{counter=displays;},display,ready);
        work(4,display,ready);
        do{
            now+=4;lastWaitWork+=4;
            int64_t deadline=nextStat<nextVBlank?nextStat:nextVBlank;
            if(now<deadline)now=deadline;
            if(nextStat<nextVBlank){nextStat+=Frame;stat(true);now+=16+4+12;lastWaitWork+=32;}
            else{nextVBlank+=Frame;vblank(display,ready);now+=16+4+8+12+16;lastWaitWork+=56;}
        }while(displays==counter);
    }
};
}
