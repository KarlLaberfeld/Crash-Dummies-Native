#pragma once
#include "air_result_accounting.h"

namespace ticd {
// Campaign state is supplied by the native campaign, never by an original
// result recording. Lives have already been decremented by the result owner.
struct AirResultHandoff {AirResultTransition timing;int player=0;std::array<int,2> lives{};int result=0;};
// Identified 0514..02ce: skip an eliminated player, select the next live player,
// and clear the background through the LCD-safe glyph writer. The following
// day/stunt/instruction screen is a separate owner; this does not certify it.
template<class Boundary,class Service,class Interrupt,class Poll,class Write>
AirResultHandoff airResultHandoff(AirResultTransition state,int player,std::array<int,2> lives,int result,
    NativeAudio& sound,Boundary&& boundary,Service&& service,Interrupt&& interrupt,Poll&& poll,Write&& write,
    std::function<int()> sampleInput={}){
    if(player<0||player>1||lives[0]<0||lives[1]<0||lives[0]>255||lives[1]>255||
       !(lives[0]|lives[1])||sound.enabled||!(result&1)||result&4)
        throw std::runtime_error("Unowned result handoff/ending/special result");
    AirClock clock;clock.now=state.end;clock.nextStat=state.nextStat;clock.nextVBlank=state.nextVBlank;
    clock.statBody=248;clock.displays=state.displays;clock.statServices=state.stats;
    clock.interrupt=[&](const char* kind,int64_t cycle,AirIrqOwner owner){interrupt(kind,cycle,owner);};
    auto point=[&](const char* name){boundary(name,clock.now,state.tick,state.countdown,player,lives[0],lives[1],result,state.input);};
    auto display=[&](bool){
        state.input.sample(sampleInput?sampleInput():state.input.held);
        if(state.input.held<0||state.input.held>255||(state.input.held&15)==15)
            throw std::runtime_error("Unowned handoff input/reset service");
        int before=state.tick;state.tick=(state.tick+1)&65535;int work=airResultCountdownWork(state.countdown);sound.tick();
        if(sound.effectWorkCycles<0||sound.musicWorkCycles<0)throw std::runtime_error("Unowned handoff audio work");
        service(clock.displays,clock.now+20,before,state.countdown,work,sound.effectWorkCycles,sound.musicWorkCycles,state.input);
        return 1592+work+sound.effectWorkCycles+sound.musicWorkCycles;
    };
    AirResultWriter<decltype(display),Poll,Write> writer(clock,state.lcdEpoch,display,poll,write);
    auto work=[&](std::initializer_list<int> costs){writer.work(costs);};
    for(int selection=0;;++selection){
        if(selection>1)throw std::runtime_error("Live player handoff did not terminate");
        point("begin");work({12,16,8,12});point("switchEntry");
        work({16,8});clock.atomicWork(16,[&]{player^=1;},display,false);work({16});point("selectionEntry");
        work({24,16,4,4,4,8,4,8,16});point("livesTest");
        work({8,4,lives[player]?12:16});
        if(lives[player])break;
    }
    point("backgroundClear");
    // CALL 25af, retained map address, the 1024 blank glyphs and loop tails.
    work({8,24,16,12,16,4,4});writer.cursor=0x9800;
    for(int cell=0;cell<1024;++cell){work({4,24});writer.glyph(0);work({8,4,4,cell==1023?8:12});}
    work({16});point("backgroundCleared");
    work({4});clock.atomicWork(16,[&]{result=0;},display,false);point("instructionEntry");
    state.end=clock.now;state.displays=clock.displays;state.stats=clock.statServices;
    state.nextStat=clock.nextStat;state.nextVBlank=clock.nextVBlank;
    return {state,player,lives,result};
}
}
