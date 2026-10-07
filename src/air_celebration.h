#pragma once
#include <array>
#include <stdexcept>

namespace ticd {
// Native state for the four identified perfect-result emitters. The shared
// random state comes from the native completed stunt, never a reference read.
struct AirCelebrationEmitter {int x=0,y=0,velocity=0,radius=0,delay=0;};
struct AirCelebration {
    std::array<AirCelebrationEmitter,4> emitters{};
    int randomState=0;
    static constexpr int ResetWork=328;
    void reset(int index){
        if(index<0||index>=4||randomState<0||randomState>65535)
            throw std::runtime_error("Invalid native celebration seed/emitter");
        // 1723 preserves the low byte. Both carry branches consume the same
        // 172 cycles; 157f's native field initialization consumes 156 more.
        int swapped=((randomState&255)<<8)|(randomState>>8);
        int first=(randomState-swapped)&65535;
        int value=(first-swapped-(randomState<swapped)+254)&65535;
        int lo=value&255,hi=value>>8,out=(lo-hi-(lo>=hi))&255;
        randomState=(randomState&255)|(out<<8);
        emitters[index]={(out&127)+16,143,251,0,index*16};
    }
};
}
