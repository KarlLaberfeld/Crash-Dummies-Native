#pragma once
#include "air_final_result.h"

namespace ticd {
// Non-qualifying score and no surviving players only. Name insertion and title
// reset have separate owners; this ends at the title-reset entry, before DI.
template<class Boundary,class Service,class Interrupt>
AirResultTransition airGameOverReturn(AirResultTransition state,int savings,std::array<int,2> lives,
    const std::array<uint8_t,48>& scores,NativeAudio& sound,const UiAssets& ui,
    Boundary&& boundary,Service&& service,Interrupt&& interrupt,std::function<int()> sample={}){
    if(state.lives||lives[0]||lives[1]||state.displays!=514||state.stats!=514||state.countdown!=86||
        !sound.enabled||sound.song!=13||savings<0||savings>=1000000)
        throw std::runtime_error("Unowned game-over ranking/return entry");
    std::array<int,3> packed{};int value=savings;
    for(int i=2;i>=0;--i){int pair=value%100;value/=100;packed[i]=(pair/10)*16+pair%10;}
    for(int row=0;row<8;++row)for(int byte=0;byte<3;++byte){int n=scores[6*row+3+byte];
        if((n&15)>9||(n>>4)>9)throw std::runtime_error("Invalid native high-score BCD");}
    AirClock clock;clock.now=state.end;clock.nextStat=state.nextStat;clock.nextVBlank=state.nextVBlank;
    clock.displays=state.displays;clock.statServices=state.stats;clock.statBody=248;
    clock.interrupt=[&](const char* name,int64_t cycle,AirIrqOwner owner){interrupt(name,cycle,owner);};
    int bgp=ui.fadePalettes[0],obp0=bgp&0xcf,obp1=bgp&0xf3;
    auto display=[&](bool){
        state.input.sample(sample?sample():state.input.held);
        if(state.input.held<0||state.input.held>255||(state.input.held&15)==15)throw std::runtime_error("Unowned game-over return input/reset");
        int tick=state.tick;state.tick=(tick+1)&65535;int work=airResultCountdownWork(state.countdown);sound.tick();
        if(sound.effectWorkCycles<0||sound.musicWorkCycles<0)throw std::runtime_error("Unowned game-over return audio");
        service(clock.displays,clock.now+20,tick,state.countdown,work,sound.effectWorkCycles,sound.musicWorkCycles,state.input);
        return 1592+work+sound.effectWorkCycles+sound.musicWorkCycles;
    };
    auto point=[&](const char* name,int row=-1,int byte=-1,int amount=-1,int target=-1,int carry=-1){
        boundary(name,clock.now,state.tick,state.countdown,row,byte,amount,target,carry,bgp,obp0,obp1,sound.enabled);};
    auto work=[&](std::initializer_list<int> costs){for(int cost:costs)clock.atomicWork(cost,[]{},display,false);};
    point("begin");work({24});point("rankEntry");work({12,12,8});
    for(int row=0;row<8;++row){
        point("row",row);work({16,16,24});point("compareEntry",row);
        work({24,16,4,4,4,8,4,8,16,4,4,4});bool lower=false;
        for(int byte=0;byte<3;++byte){
            int target=scores[6*row+3+byte],amount=packed[byte];point("compare",row,byte,amount,target);
            work({8,8});lower=amount<target;
            if(byte==2){work({16});break;}
            work({amount!=target?20:8});if(amount!=target)break;work({8,8});
        }
        point("rowDone",row,-1,-1,-1,lower);work({12,12,lower?8:12});
        if(!lower)throw std::runtime_error("Qualifying score requires insertion/name-entry ownership");
        work({8,4,row<7?12:8});if(row==7)work({16});
    }
    point("rankReturned");work({16});point("resultReturned");work({12,16,8,8});point("fadeCall");
    work({24});point("fadeEntry");work({12,8});
    for(int segment=0;segment<8;++segment){
        point("palette");int palette=ui.fadePalettes[segment];work({8});clock.accessWork(12,8,[&]{bgp=palette;},display,false);work({8});
        clock.accessWork(12,8,[&]{obp1=palette&0xf3;},display,false);work({8,8});clock.accessWork(12,8,[&]{obp0=palette&0xcf;},display,false);work({8});
        for(int wait=0;wait<4;++wait){point("wait");clock.wait(display,false);point("tail");work({4,wait<3?12:8});}
        work({4,segment<7?12:8});
    }
    work({16});point("fadeReturned");work({16});point("titleResetEntry");
    state.end=clock.now;state.displays=clock.displays;state.stats=clock.statServices;state.nextStat=clock.nextStat;state.nextVBlank=clock.nextVBlank;return state;
}
}
