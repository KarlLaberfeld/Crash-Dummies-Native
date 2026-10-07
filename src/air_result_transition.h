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
    std::array<AirResultLayoutProfile,6> profiles{};
    bool perfectProfile=false;
    static AirResultLayoutAssets load(const char* path){
        std::ifstream file(path,std::ios::binary);char magic[8];
        if(!file.read(magic,8)||(std::string(magic,8)!="TICDRT01"&&std::string(magic,8)!="TICDRT02"))throw std::runtime_error("Missing result layout profiles");
        AirResultLayoutAssets data;
        data.perfectProfile=std::string(magic,8)=="TICDRT02";
        for(int i=0;i<(data.perfectProfile?6:5);++i){auto& p=data.profiles[i];
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
struct AirResultTransition {
    int64_t end=0,lcdEpoch=0,nextStat=0,nextVBlank=0;
    int tick=0,countdown=600,displays=0,stats=0,skip=0;
    DisplayInput input;
    bool perfect=false;
    AirCelebration celebration;
    std::array<unsigned char,160> celebrationVisible{};
};
inline int airResultCountdownWork(int& countdown){
    if(countdown<1||countdown>720)throw std::runtime_error("Invalid result countdown");
    // 24cf retains one when decrement would reach zero: the taken conditional
    // return omits the stores. This is distinct from an expired gameplay timer.
    if(countdown==1)return 228;
    --countdown;return 272;
}
template<class Boundary,class Service,class Interrupt>
AirResultTransition airResultIncoming(const AirResultPrefix& prefix,int result,int tick,int lives,int held,NativeAudio& sound,
    const AirResultLayoutAssets& layouts,const UiAssets& ui,Boundary&& boundary,Service&& service,Interrupt&& interrupt,
    std::function<int()> sampleInput={},
    std::function<void(unsigned,int,const AirCelebration&,const std::array<unsigned char,160>&,int)> celebrationObserver={}){
    const bool perfect=result&4;
    if(!(result&1)||prefix.pendingRequests!=3||prefix.end<=prefix.lcdDisabled||sound.enabled||
       (perfect&&(result!=7||!layouts.perfectProfile||prefix.display!=2||prefix.stat!=4||prefix.countdown!=720)))
        throw std::runtime_error("Unowned Air result transition/celebration/startup");
    if((held&15)==15||(!(result&2)&&lives<=1))
        throw std::runtime_error("Result reset/final-life transition needs its separate owner");
    if(perfect){
        if(prefix.celebration.randomState<0||prefix.celebration.randomState>65535)
            throw std::runtime_error("Invalid perfect-result native seed");
        for(int i=0;i<4;++i){const auto& e=prefix.celebration.emitters[i];
            if(e.x<16||e.x>143||e.y!=143||e.velocity!=251||e.radius||e.delay!=i*16)
                throw std::runtime_error("Incomplete native perfect-result initialization");}
    }
    AirResultTransition state;state.tick=tick;state.input.held=state.input.previous=held;int64_t now=prefix.end;
    state.perfect=perfect;state.celebration=prefix.celebration;state.countdown=perfect?720:600;
    const bool success=result&2;int bgp=ui.fadePalettes[7],obp0=bgp&0xcf,obp1=bgp&0xf3;
    auto point=[&](const char* name,int64_t cycle){boundary(name,cycle,state.tick,state.countdown,bgp,obp0,obp1,sound.enabled);};
    point("playerReady",now);
    if(success){
        // 0462 predicates, table dispatch, successful Air text and its RET.
        now+=44+108+layouts.profiles[0].work()+16;point("successTextReady",now);
        now+=(perfect?60:56)+68+36+24+(1024*104-4+16)+68+layouts.profiles[perfect?5:3].work()+24;
        point("portraitReady",now);now+=airResultMusicStartWork();sound.playMusic(perfect?5:4);point("musicReady",now);
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
    clock.nextStat=state.lcdEpoch+143*456;clock.nextVBlank=state.lcdEpoch+AirClock::VBlankLine;clock.statBody=perfect?288:248;
    clock.interrupt=[&](const char* kind,int64_t time,AirIrqOwner owner){interrupt(kind,time,owner);};
    auto display=[&](bool){
        state.input.sample(sampleInput?sampleInput():state.input.held);
        if(state.input.held<0||state.input.held>255||(state.input.held&15)==15)
            throw std::runtime_error("Unowned result input/reset service");
        int before=state.tick;int celebrationWork=0;
        if(perfect){state.celebrationVisible=state.celebration.prepared;celebrationWork=state.celebration.advance(before,ui);
            if(celebrationObserver)celebrationObserver(clock.displays,before,state.celebration,state.celebrationVisible,celebrationWork);}
        state.tick=(state.tick+1)&65535;
        // Countdown bookkeeping follows perfect sprite preparation; the
        // preparation uses the old display counter and prior list is visible.
        int displayWork=airResultCountdownWork(state.countdown)+(perfect?80+celebrationWork:0);sound.tick();
        if(sound.effectWorkCycles<0||sound.musicWorkCycles<0)throw std::runtime_error("Unowned result audio service");
        int body=1592+displayWork+sound.effectWorkCycles+sound.musicWorkCycles;
        service(clock.displays,clock.now+20,before,state.countdown,displayWork,sound.effectWorkCycles,sound.musicWorkCycles,sound.enabled);
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
    const UiAssets& ui,Boundary&& boundary,Service&& service,Interrupt&& interrupt,std::function<int()> sampleInput={}){
    if(!(result&1)||result&6||state.displays!=34||state.countdown!=566||(held&15)==15)
        throw std::runtime_error("Unowned result hold/skip/reset transition");
    AirClock clock;clock.now=state.end;clock.nextStat=state.nextStat;clock.nextVBlank=state.nextVBlank;
    clock.statBody=248;clock.displays=state.displays;clock.statServices=state.stats;
    clock.interrupt=[&](const char* kind,int64_t cycle,AirIrqOwner owner){interrupt(kind,cycle,owner);};
    int bgp=ui.fadePalettes[0],obp0=bgp&0xcf,obp1=bgp&0xf3;
    auto point=[&](const char* name){boundary(name,clock.now,state.tick,state.countdown,bgp,obp0,obp1,sound.enabled);};
    auto display=[&](bool){
        state.input.sample(sampleInput?sampleInput():state.input.held);
        if(state.input.held<0||state.input.held>255||(state.input.held&15)==15)throw std::runtime_error("Unowned failure hold input/reset service");
        int tick=state.tick;state.tick=(state.tick+1)&65535;int displayWork=airResultCountdownWork(state.countdown);sound.tick();
        if(sound.effectWorkCycles<0||sound.musicWorkCycles<0)throw std::runtime_error("Unowned result hold audio work");
        service(clock.displays,clock.now+20,tick,state.countdown,displayWork,sound.effectWorkCycles,sound.musicWorkCycles,sound.enabled);
        return 1592+displayWork+sound.effectWorkCycles+sound.musicWorkCycles;
    };
    for(int cost:{8,12,24})clock.atomicWork(cost,[]{},display,false);
    for(int wait=0;wait<480;++wait){
        point("holdWait");clock.wait(display,false);point("holdTail");
        bool exit=state.input.pressed&11;
        for(int cost:{12,4,exit?20:8})clock.atomicWork(cost,[]{},display,false);
        if(exit)break;
        for(int cost:{8,4,4})clock.atomicWork(cost,[]{},display,false);
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
