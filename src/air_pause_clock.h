#pragma once
#include "air_clock.h"
#include <array>

namespace ticd {
// Work owners for the identified pause graphics routines. A native LCD owner
// must provide STAT at the actual sample time and must enforce accessibility
// again at the data access. No captured mode, poll count or idle drives these
// routines. They are not yet connected to the production Windows scheduler.
struct AirPauseWork {
    int cycles=0,polls=0,failedPolls=0,bytes=0,destinationWraps=0;
};
template<class Display>struct AirPauseAccess {
    AirClock& clock;
    Display& display;
    AirPauseWork result;
    void work(int cost){result.cycles+=cost;clock.work(cost,display,false);}
    template<class Effect>void access(int cost,int offset,Effect&& effect){
        result.cycles+=cost;clock.accessWork(cost,offset,effect,display,false);
    }
    template<class Status>void poll(Status& status){
        for(;;){
            int mode=-1;
            // LDH's bus read is in the last four-cycle part of its 12-cycle
            // access. BIT and the conditional branch retain that sample.
            access(12,8,[&]{mode=status(clock.now);});
            if(mode<0||mode>3)throw std::runtime_error("Unreconstructed pause LCD readiness");
            ++result.polls;work(8);
            if(!(mode&2)){work(8);return;}
            ++result.failedPolls;work(12);
            // A fault guard rejects incomplete work; it supplies no time or
            // success allowance. A valid native LCD periodically clears bit 1.
            if(result.failedPolls>=1000000)
                throw std::runtime_error("Pause LCD polling did not complete");
        }
    }
};

// 2359's source read and destination write are separate bus owners. In
// particular a successful STAT read does not certify a later VRAM access.
// Callback indices describe this copy's bytes; addresses are graphics copy
// destinations, not a general emulated address space.
template<class Display,class Status,class Read,class Write>
AirPauseWork airPauseCopy(AirClock& clock,int size,unsigned destination,
                         Display&& display,Status&& status,Read&& read,Write&& write){
    if(size<=0||size>65535||destination>65535)
        throw std::runtime_error("Invalid pause graphics copy");
    AirPauseAccess<Display> run{clock,display,{}};
    run.work(112); // Bank-selection prefix, 2359..2361.
    for(int i=0;i<size;++i){
        run.poll(status);unsigned char value=0;
        run.access(8,4,[&]{value=read(i,clock.now);});
        run.access(8,4,[&]{write(destination,value,clock.now);});
        destination=(destination+1)&65535;
        run.work(8+4+8); // Destination increment and high-byte comparison.
        if((destination>>8)==0x98){
            run.work(8+8);destination=0x8800|(destination&255);
            ++run.result.destinationWraps;
        }else run.work(12);
        ++run.result.bytes;
        run.work(8+4+4+(i+1==size?8:12));
    }
    run.work(88); // Bank restore and return.
    return run.result;
}

// Identified 14ac layout: window layer, position (0,0), one twenty-column
// rectangle and end. The caller supplies its locally extracted twenty bytes;
// this is not an interpreter for cartridge code or a generic script engine.
template<class Display,class Status,class Write>
AirPauseWork airPauseText(AirClock& clock,const std::array<unsigned char,20>& text,
                         Display&& display,Status&& status,Write&& write){
    AirPauseAccess<Display> run{clock,display,{}};
    run.work(84); // RST10 entry.
    run.work(168+68); // Window-layer command, 21e1.
    run.work(168+184); // Position command, 21d3/2302.
    run.work(168+188); // Rectangle dispatch and argument/setup before 22e4.
    run.work(160); // Bank selection and rectangle row saves, 22e4..22ef.
    for(unsigned i=0;i<text.size();++i){
        run.work(8+24+16); // Local byte, identified store call, saved byte.
        run.poll(status);
        run.work(12); // Restore the saved byte after STAT sampling.
        run.access(8,4,[&]{write(0x9c00+i,text[i],clock.now);});
        run.work(8+16+4+(i+1==text.size()?8:12));
        ++run.result.bytes;
    }
    run.work(188); // Rectangle row/end, bank restore and return.
    run.work(28); // Restore script position and dispatch, 2209..214f.
    run.work(168+108); // End command.
    return run.result;
}
}
