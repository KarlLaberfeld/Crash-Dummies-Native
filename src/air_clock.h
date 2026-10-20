#pragma once
#include <cstdint>
#include <algorithm>
#include <functional>
#include <stdexcept>

namespace ticd {
// Input belongs to display sampling, including displays without a game update.
// Extra samples can clear a fresh edge before gameplay next reads the buttons.
struct DisplayInput {
    int held=0,previous=0,pressed=0;
    void sample(int buttons){previous=held;held=buttons;pressed=held&~previous;}
};
enum class AirIrqOwner { Unqualified, SourceBoundary, CounterWait, PendingStartup, ProtectedResume };
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
    bool servicesHeld=false;
    int statBody=288; // Air objects (288), or the identified result pop-only callback (248).
    int heldFollower=0;
    // Optional bounded image observer. It charges no work and executes no IRQ
    // instructions. Ownership distinguishes completed identified source
    // boundaries from aggregate budgets with unqualified acceptance latency.
    std::function<void(int64_t,AirIrqOwner)> objectDisable;
    std::function<void(const char*,int64_t,AirIrqOwner)> interrupt;
    // Optional identified raster callback. It owns native display state and
    // future compare deadlines, and returns source work excluding RETI. The
    // existing fixed Air/result callbacks remain unchanged when absent.
    std::function<int(int64_t)> rasterWork;
    template<class Display>void vblank(Display&& display,bool ready,AirIrqOwner owner=AirIrqOwner::Unqualified){
        if(interrupt)interrupt("vblank",now+20,owner);
        int work=display(ready);
        if(work<0)throw std::runtime_error("Unreconstructed Air display/audio work");
        now+=20+work+16;++displays;
    }
    void stat(AirIrqOwner owner=AirIrqOwner::Unqualified){
        if(rasterWork){
            if(interrupt)interrupt("stat",now+20,owner);
            int work=rasterWork(now+20);
            if(work<0)throw std::runtime_error("Unreconstructed raster callback work");
            now+=20+work+16;++statServices;return;
        }
        if(statBody!=288&&statBody!=248)throw std::runtime_error("Unowned display STAT callback");
        if(interrupt)interrupt("stat",now+20,owner);
        // 0048..254f: source body prefix 228, then LCDC write sample at +8.
        // The pinned DMG bus observer exposes that sample two cycles earlier.
        if(objectDisable&&statBody==288)objectDisable(now+20+228+8-2,owner);
        now+=20+statBody+16;++statServices;
    }
    template<class Display,class Boundary>void startup(Display&& display,Boundary&& boundary){
        // EI(4) takes effect after LD(8), following the completed access/return.
        // Source IF/IE retain both pending services. The ready store costs 12.
        boundary("enableReturned",now);
        now+=4+8;boundary("displayEntry",now+20);vblank(display,true,AirIrqOwner::PendingStartup);
        boundary("displayReturned",now);boundary("statEntry",now+20);stat(AirIrqOwner::PendingStartup);
        boundary("statReturned",now);now+=12;boundary("readyStored",now);
    }
    template<class Display>void startup(Display&& display){
        startup(display,[](const char*,int64_t){});
    }
    template<class Display>void work(int cost,Display&& display,bool ready,AirIrqOwner owner=AirIrqOwner::Unqualified){
        if(servicesHeld)throw std::runtime_error("Air work attempted before protected completion");
        if(cost<0)throw std::runtime_error("Unreconstructed Air game work");
        while(cost||(nextStat<nextVBlank?nextStat:nextVBlank)<=now){
            int64_t deadline=nextStat<nextVBlank?nextStat:nextVBlank;
            if(now+cost<deadline){now+=cost;return;}
            int before=static_cast<int>(deadline-now);
            if(before>0){cost-=before;now=deadline;}
            if(nextStat<nextVBlank){nextStat+=Frame;stat(owner);}
            else{nextVBlank+=Frame;vblank(display,ready,owner);}
        }
    }
    template<class Effect,class Display>void atomicWork(int cost,Effect&& effect,Display&& display,bool ready){
        if(servicesHeld)throw std::runtime_error("Air access attempted before protected completion");
        if(cost<4||cost>24||cost%4)throw std::runtime_error("Unreconstructed Air atomic work");
        now+=cost;effect();work(0,display,ready,AirIrqOwner::SourceBoundary);
    }
    // One identified graphics access: its bus sample occurs before the end
    // of the access, while a pending interrupt waits until completion. This
    // is a semantic boundary, not an opcode/register execution interface.
    template<class Effect,class Display>void accessWork(int cost,int sampleOffset,Effect&& effect,Display&& display,bool ready){
        if(servicesHeld)throw std::runtime_error("Air access attempted before protected completion");
        if(cost<=0||sampleOffset<0||sampleOffset>cost)
            throw std::runtime_error("Invalid Air graphics access boundary");
        now+=sampleOffset;effect();now+=cost-sampleOffset;
        work(0,display,ready,AirIrqOwner::SourceBoundary);
    }
    // Identified short source critical sections defer the two periodic
    // services until the following operation completes. This is a native
    // service gate, not CPU state or a generic instruction execution API.
    void holdServices(int cost){
        if(servicesHeld||(cost!=192&&cost!=140)||std::min(nextStat,nextVBlank)<=now)
            throw std::runtime_error("Unowned Air protected entry");
        now+=cost;servicesHeld=true;heldFollower=cost==192?12:16;
    }
    template<class Display>void resumeServices(int followerCost,Display&& display,bool ready){
        if(!servicesHeld||followerCost!=heldFollower)
            throw std::runtime_error("Unowned Air protected follower");
        now+=followerCost;servicesHeld=false;heldFollower=0;
        // Pending VBlank has source priority over STAT, even if STAT's
        // request was earlier while services were held. Ordinary work uses
        // chronological deadlines only while both requests are not pending.
        while(nextStat<=now||nextVBlank<=now){
            if(nextVBlank<=now){nextVBlank+=Frame;vblank(display,ready,AirIrqOwner::ProtectedResume);}
            else{nextStat+=Frame;stat(AirIrqOwner::ProtectedResume);}
        }
    }
    template<class Display>void wait(Display&& display,bool ready=true){
        if(servicesHeld)throw std::runtime_error("Air wait attempted before protected completion");
        lastWaitWork=60;
        // CALL/PUSH precede the counter read. A display during that prefix
        // must belong to the new snapshot, so the wait needs a later VBlank.
        // The 16-cycle read commits before a pending service; LD B costs 4.
        atomicWork(24,[]{},display,ready);
        atomicWork(16,[]{},display,ready);
        unsigned counter=displays;
        atomicWork(16,[&]{counter=displays;},display,ready);
        atomicWork(4,[]{},display,ready);
        do{
            now+=4;lastWaitWork+=4;
            int64_t deadline=nextStat<nextVBlank?nextStat:nextVBlank;
            // A STAT request exactly at the initial HALT completion returns
            // to HALT itself. It does not execute the counter-read/test tail.
            // This is a native wait boundary, selected by its own deadline.
            const bool statAtHaltEntry=nextStat<nextVBlank&&now==deadline;
            if(now<deadline)now=deadline;
            if(nextStat<nextVBlank){nextStat+=Frame;stat(AirIrqOwner::CounterWait);
                if(!statAtHaltEntry){now+=16+4+12;lastWaitWork+=32;}}
            else{nextVBlank+=Frame;vblank(display,ready,AirIrqOwner::CounterWait);now+=16+4+8+12+16;lastWaitWork+=56;}
        }while(displays==counter);
    }
};
}
