#pragma once
#include "air_result_accounting.h"

namespace ticd {
// Separate final-life owner. Stops before high-score selection/name entry.
// Savings are native campaign state, never an original observation.
template<class Boundary,class Service,class Interrupt,class Poll,class Write>
AirResultTransition airFinalResult(const AirResultPrefix& prefix,int result,int tick,int lives,int held,int savings,
    NativeAudio& sound,const AirResultLayoutAssets& layouts,const AirResultTextAssets& texts,const UiAssets& ui,
    Boundary&& boundary,Service&& service,Interrupt&& interrupt,Poll&& poll,Write&& write,std::function<int()> sampleInput={}){
    if(!texts.finalLabel||texts.layouts[5].empty()||savings<0||savings>=1000000)
        throw std::runtime_error("Final result requires its decoded banner and native savings");
    int observedLives=lives;
    auto incomingPoint=[&](const char* name,int64_t cycle,int tick,int countdown,int bgp,int obp0,int obp1,bool enabled){
        boundary(name,cycle,tick,countdown,bgp,obp0,obp1,enabled,observedLives,savings);};
    auto state=airResultIncomingOwned<true>(prefix,result,tick,lives,held,sound,layouts,ui,incomingPoint,service,interrupt,sampleInput,{},[&](int value){observedLives=value;});
    if(state.lives||state.displays!=1||state.stats!=1||sound.enabled)throw std::runtime_error("Missing native zero-life result entry");
    AirClock clock;clock.now=state.end;clock.nextStat=state.nextStat;clock.nextVBlank=state.nextVBlank;
    clock.displays=state.displays;clock.statServices=state.stats;clock.statBody=248;
    clock.interrupt=[&](const char* kind,int64_t cycle,AirIrqOwner owner){interrupt(kind,cycle,owner);};
    int bgp=ui.fadePalettes[7],obp0=bgp&0xcf,obp1=bgp&0xf3;
    auto display=[&](bool){
        state.input.sample(sampleInput?sampleInput():state.input.held);
        if(state.input.held<0||state.input.held>255||(state.input.held&15)==15)throw std::runtime_error("Unowned game-over input/reset");
        int before=state.tick;state.tick=(before+1)&65535;int work=airResultCountdownWork(state.countdown);sound.tick();
        if(sound.effectWorkCycles<0||sound.musicWorkCycles<0)throw std::runtime_error("Unowned game-over audio");
        service(clock.displays,clock.now+20,before,state.countdown,work,sound.effectWorkCycles,sound.musicWorkCycles,sound.enabled);
        return 1592+work+sound.effectWorkCycles+sound.musicWorkCycles;
    };
    AirResultWriter writer(clock,state.lcdEpoch,display,poll,write);
    writer.lcd.resultFirstVisibleFrame=true;
    auto work=[&](std::initializer_list<int> costs){writer.work(costs);};
    auto point=[&](const char* name){boundary(name,clock.now,state.tick,state.countdown,bgp,obp0,obp1,sound.enabled,state.lives,savings);};
    writer.text(texts.layouts[5]);point("bannerReady");
    work({24,16,4,4,4,8,4,8,16});point("savingsPointer");work({4,4,8});point("savingsDigits");
    writer.leading=false;work({24});writer.pair(savings/10000);point("savingsMiddle");
    work({24,8,8,8,4,24});writer.digit((savings/1000)%10);work({8,writer.leading?12:8});
    if(!writer.leading){work({8,8,8,24});writer.leading=true;--writer.cursor;writer.glyph(0x33);}
    work({8,8,4,16});writer.digit((savings/100)%10);point("savingsComma");
    work({8,24});writer.glyph(0x2c);point("savingsCents");work({24});writer.pair(savings%100,true);point("savingsReady");
    clock.wait(display,false);point("musicSelect");work({8});point("musicEntry");
    if(clock.now+airResultMusicStartWork()>=std::min(clock.nextStat,clock.nextVBlank))throw std::runtime_error("Interrupted game-over music reset needs its completion owner");
    clock.now+=airResultMusicStartWork();sound.playMusic(13);point("musicReady");work({24});point("fadeEntry");work({12,8});
    for(int segment=0;segment<8;++segment){
        point("palette");int palette=ui.fadePalettes[7-segment];work({8});clock.accessWork(12,8,[&]{bgp=palette;},display,false);work({8});
        clock.accessWork(12,8,[&]{obp1=palette&0xf3;},display,false);work({8,8});clock.accessWork(12,8,[&]{obp0=palette&0xcf;},display,false);work({8});
        for(int wait=0;wait<4;++wait){
            point("wait");clock.wait(display,false);point("tail");work({4,wait<3?12:8});
            if(wait==3){work({4,segment<7?12:8});if(segment==7)work({16});}
        }
    }
    point("fadeReturned");work({8,12,24});
    // 25c4 tests only the loop count, never the action edge/mask in L.
    for(int wait=0;wait<480;++wait){
        point("holdWait");clock.wait(display,false);point("holdTail");work({8,4,4,wait<479?12:8});if(wait==479)work({16});
    }
    point("gameOverHoldReturned");state.end=clock.now;state.displays=clock.displays;state.stats=clock.statServices;
    state.nextStat=clock.nextStat;state.nextVBlank=clock.nextVBlank;return state;
}
}
