#pragma once
#include "air_result_clock.h"
#include "audio.h"
#include "audio_work.h"
#include "ui.h"
#include <fstream>

namespace ticd {
struct AirResultLayoutProfile {
    int zero=0,nonzero=0,anchors=0,rows=0,layers=0,width=0,height=0,carries=0;
    int work()const{
        if(zero<0||nonzero<0||anchors<0||rows<0||layers<0||width<0||height<0||carries<0||
           width>32||height>32||carries>height||bool(width)!=bool(height))
            throw std::runtime_error("Unowned result layout profile");
        // 0010/2146 entry, command 80's finish; identified glyph/anchor/row/
        // layer paths at text speed zero and LCD-off. A rectangle includes
        // 22e4's bank save/restore and each destination-row carry.
        return 84+276+196*zero+224*nonzero+352*anchors+336*rows+236*layers+
            (width?608+height*(120+136*width)+8*carries:0);
    }
};
struct AirResultLayoutAssets {
    std::array<AirResultLayoutProfile,5> profiles{};
    static AirResultLayoutAssets load(const char* path){
        std::ifstream file(path,std::ios::binary);char magic[8];
        if(!file.read(magic,8)||std::string(magic,8)!="TICDRT01")throw std::runtime_error("Missing result layout profiles");
        AirResultLayoutAssets data;
        for(auto& p:data.profiles){
            int* fields[]={&p.zero,&p.nonzero,&p.anchors,&p.rows,&p.layers,&p.width,&p.height,&p.carries};
            for(int* field:fields){unsigned char bytes[2];if(!file.read(reinterpret_cast<char*>(bytes),2))throw std::runtime_error("Truncated result layout profiles");*field=bytes[0]+256*bytes[1];}
            p.work();
        }
        if(file.peek()!=std::char_traits<char>::eof())throw std::runtime_error("Trailing result layout data");
        return data;
    }
};
// 362a caller, shared fixed reset, eight song roots and 23 hardware bytes.
// The same native music reset/start is used; this is work, not a CPU model.
inline constexpr int airResultMusicStartWork(){
    return audioStopWork()-60-32+76+8*40+60+23*52-4+16+96;
}
struct AirResultTransition {int64_t end=0,lcdEpoch=0,nextStat=0,nextVBlank=0;int tick=0,countdown=600,displays=0,stats=0;};
template<class Boundary,class Service,class Interrupt>
AirResultTransition airResultIncoming(const AirResultPrefix& prefix,int result,int tick,int lives,int held,NativeAudio& sound,
    const AirResultLayoutAssets& layouts,const UiAssets& ui,Boundary&& boundary,Service&& service,Interrupt&& interrupt){
    if(!(result&1)||result&4||prefix.pendingRequests!=3||prefix.end<=prefix.lcdDisabled||sound.enabled)
        throw std::runtime_error("Unowned Air result transition/celebration/startup");
    if((held&15)==15||(!(result&2)&&lives<=1))
        throw std::runtime_error("Result reset/final-life transition needs its separate owner");
    AirResultTransition state;state.tick=tick;int64_t now=prefix.end;
    const bool success=result&2;int bgp=ui.fadePalettes[7],obp0=bgp&0xcf,obp1=bgp&0xf3;
    auto point=[&](const char* name,int64_t cycle){boundary(name,cycle,state.tick,state.countdown,bgp,obp0,obp1,sound.enabled);};
    point("playerReady",now);
    if(success){
        // 0462 predicates, table dispatch, successful Air text and its RET.
        now+=44+108+layouts.profiles[0].work()+16;point("successTextReady",now);
        now+=56+68+36+24+(1024*104-4+16)+68+layouts.profiles[3].work()+24;
        point("portraitReady",now);now+=airResultMusicStartWork();sound.playMusic(4);point("musicReady",now);
    }else{
        now+=48;point("failurePortrait",now);
        now+=16+68+36+24+(1024*104-4+16)+68+layouts.profiles[4].work();point("failurePortraitReady",now);
        const bool timeout=result&16;
        now+=12+108+16+8+(timeout?12:8)+layouts.profiles[timeout?2:1].work()+16;
        point("failureTextReady",now);
    }
    // Inclusive LCD-on caller, then access completion and return. Oscillator
    // deadlines are restarted from the identified last-access epoch.
    now+=56;point("lcdWriteReturned",now);now+=16;point("enable",now);
    state.lcdEpoch=now-20;AirClock clock;clock.now=now;
    clock.nextStat=state.lcdEpoch+143*456;clock.nextVBlank=state.lcdEpoch+AirClock::VBlankLine;clock.statBody=248;
    clock.interrupt=[&](const char* kind,int64_t time,AirIrqOwner owner){interrupt(kind,time,owner);};
    auto display=[&](bool){
        int before=state.tick;state.tick=(state.tick+1)&65535;
        // 24cf decrements 600, with the source's zero-store guard.
        if(state.countdown<=1)throw std::runtime_error("Result countdown expiry needs its separate owner");
        --state.countdown;sound.tick();
        if(sound.effectWorkCycles<0||sound.musicWorkCycles<0)throw std::runtime_error("Unowned result audio service");
        int body=1592+272+sound.effectWorkCycles+sound.musicWorkCycles;
        service(clock.displays,clock.now+20,before,state.countdown,272,sound.effectWorkCycles,sound.musicWorkCycles,sound.enabled);
        return body;
    };
    clock.now+=4;point("enableFollower",clock.now);clock.now+=24;
    // Source EI follower is this identified CALL; both already pending
    // services run in source priority before the callee's first operation.
    clock.vblank(display,false,AirIrqOwner::PendingStartup);clock.stat(AirIrqOwner::PendingStartup);
    if(!success){
        // Current-player pointer, decrement of a non-final life and branch.
        // Life exhaustion is a separate result/ending transition.
        clock.atomicWork(16,[]{},display,false);for(int cost:{4,4,4,8,4,8,16,8,4,8,12})clock.atomicWork(cost,[]{},display,false);
        point("failureWait",clock.now);clock.wait(display,false);point("failureWaitReturned",clock.now);
        clock.atomicWork(8,[]{},display,false);point("musicEntry",clock.now);
        // At the captured source phase the entire reset precedes the next
        // request. Do not certify partially reset audio by aggregation.
        if(clock.now+airResultMusicStartWork()>=std::min(clock.nextStat,clock.nextVBlank))
            throw std::runtime_error("Interrupted result music reset needs its completion owner");
        clock.now+=airResultMusicStartWork();sound.playMusic(3);point("musicReady",clock.now);
        clock.atomicWork(24,[]{},display,false);
    }
    point("fadeEntry",clock.now);
    // CALL 20d1 has already completed (possibly before the pending services).
    clock.atomicWork(12,[]{},display,false);clock.atomicWork(8,[]{},display,false);
    for(int segment=0;segment<8;++segment){
        point("palette",clock.now);
        int palette=ui.fadePalettes[7-segment];
        clock.atomicWork(8,[]{},display,false);
        clock.accessWork(12,8,[&]{bgp=palette;},display,false);
        clock.atomicWork(8,[]{},display,false);
        clock.accessWork(12,8,[&]{obp1=palette&0xf3;},display,false);
        clock.atomicWork(8,[]{},display,false);clock.atomicWork(8,[]{},display,false);
        clock.accessWork(12,8,[&]{obp0=palette&0xcf;},display,false);
        clock.atomicWork(8,[]{},display,false);
        for(int wait=0;wait<4;++wait){
            point("wait",clock.now);clock.wait(display,false);point("tail",clock.now);
            clock.atomicWork(4,[]{},display,false);clock.atomicWork(wait<3?12:8,[]{},display,false);
            if(wait==3){clock.atomicWork(4,[]{},display,false);clock.atomicWork(segment<7?12:8,[]{},display,false);if(segment==7)clock.atomicWork(16,[]{},display,false);}
        }
    }
    point("fadeReturned",clock.now);state.end=clock.now;state.displays=clock.displays;state.stats=clock.statServices;
    state.nextStat=clock.nextStat;state.nextVBlank=clock.nextVBlank;return state;
}

template<class Boundary,class Service,class Interrupt>
AirResultTransition airResultFailureHold(AirResultTransition state,int result,int held,NativeAudio& sound,
    const UiAssets& ui,Boundary&& boundary,Service&& service,Interrupt&& interrupt){
    if(!(result&1)||result&6||state.displays!=34||state.countdown!=566||(held&15)==15)
        throw std::runtime_error("Unowned result hold/skip/reset transition");
    AirClock clock;clock.now=state.end;clock.nextStat=state.nextStat;clock.nextVBlank=state.nextVBlank;
    clock.statBody=248;clock.displays=state.displays;clock.statServices=state.stats;
    clock.interrupt=[&](const char* kind,int64_t cycle,AirIrqOwner owner){interrupt(kind,cycle,owner);};
    int bgp=ui.fadePalettes[0],obp0=bgp&0xcf,obp1=bgp&0xf3;
    auto point=[&](const char* name){boundary(name,clock.now,state.tick,state.countdown,bgp,obp0,obp1,sound.enabled);};
    auto display=[&](bool){
        if(state.countdown<=1)throw std::runtime_error("Result countdown expiry needs its separate owner");
        int tick=state.tick;state.tick=(state.tick+1)&65535;--state.countdown;sound.tick();
        if(sound.effectWorkCycles<0||sound.musicWorkCycles<0)throw std::runtime_error("Unowned result hold audio work");
        service(clock.displays,clock.now+20,tick,state.countdown,272,sound.effectWorkCycles,sound.musicWorkCycles,sound.enabled);
        return 1592+272+sound.effectWorkCycles+sound.musicWorkCycles;
    };
    for(int cost:{8,12,24})clock.atomicWork(cost,[]{},display,false);
    for(int wait=0;wait<480;++wait){
        point("holdWait");clock.wait(display,false);point("holdTail");
        // Fresh input is sampled every display. This bounded hold keeps the
        // already held post-stunt buttons; new edges require an input owner.
        for(int cost:{12,4,8,8,4,4})clock.atomicWork(cost,[]{},display,false);
        clock.atomicWork(wait<479?12:8,[]{},display,false);
        if(wait==479)clock.atomicWork(16,[]{},display,false);
    }
    point("holdReturned");
    if(clock.now+audioStopWork()>=std::min(clock.nextStat,clock.nextVBlank))
        throw std::runtime_error("Interrupted post-result stop needs its completion owner");
    clock.now+=audioStopWork();sound.stop();point("musicStopped");
    clock.atomicWork(16,[]{},display,false);point("failureResultReturned");
    state.end=clock.now;state.displays=clock.displays;state.stats=clock.statServices;
    state.nextStat=clock.nextStat;state.nextVBlank=clock.nextVBlank;return state;
}
}
