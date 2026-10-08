#pragma once
#include "air_instruction_picture.h"

namespace ticd {
struct AirInstructionMapState {
    AirResultHandoff campaign;
    int lcdc=0,lyc=120,scroll=0,alternate=1,display=0,stat=0;
};
// Subsequent instruction's identified 268b..timed-text map transition. The
// source changes callbacks and retains the countdown, rather than requesting
// another game update. The eight pattern bytes are local UI assets.
template<class Boundary,class Service,class Interrupt,class Poll>
AirInstructionMapState airInstructionMap(AirResultHandoff campaign,NativeAudio& sound,const UiAssets& ui,
    Boundary&& boundary,Service&& service,Interrupt&& interrupt,Poll&& poll,std::function<int()> sampleInput={}){
    if(campaign.result||!sound.enabled)throw std::runtime_error("Unowned instruction map entry");
    AirInstructionMapState state;state.campaign=campaign;
    auto& timing=state.campaign.timing;
    state.lyc=static_cast<int>((timing.nextStat-timing.lcdEpoch)%AirClock::Frame)/456;
    if(state.lyc!=120&&state.lyc!=143)throw std::runtime_error("Unowned inherited instruction compare line");
    // Result LCD restart selects 9c00 with eight-pixel objects in both paths;
    // ordinary results publish a blank list rather than clearing LCDC's bits.
    state.lcdc=0xdb;state.display=timing.perfect?2:10;state.stat=timing.perfect?4:0;
    AirClock clock;clock.now=timing.end;clock.nextStat=timing.nextStat;clock.nextVBlank=timing.nextVBlank;
    clock.displays=timing.displays;clock.statServices=timing.stats;clock.statBody=timing.perfect?288:248;
    clock.interrupt=[&](const char* kind,int64_t cycle,AirIrqOwner owner){interrupt(kind,cycle,owner);};
    clock.objectDisable=[&](int64_t,AirIrqOwner){if(state.stat==4)state.lcdc&=~2;};
    auto display=[&](bool){
        timing.input.sample(sampleInput?sampleInput():timing.input.held);
        if(timing.input.held<0||timing.input.held>255||(timing.input.held&15)==15)throw std::runtime_error("Unowned instruction map input/reset");
        int tick=timing.tick;timing.tick=(tick+1)&65535;
        int work=144;
        if(state.display!=5){work=airResultCountdownWork(timing.countdown)+(timing.perfect?68:0);
            if(timing.perfect){timing.celebrationVisible=timing.celebration.prepared;state.lcdc|=2;}}
        sound.tick();if(sound.effectWorkCycles<0||sound.musicWorkCycles<0)throw std::runtime_error("Unowned instruction map audio");
        service(clock.displays,clock.now+20,tick,timing.countdown,work,sound.effectWorkCycles,sound.musicWorkCycles,timing.input);
        return 1592+work+sound.effectWorkCycles+sound.musicWorkCycles;
    };
    auto work=[&](std::initializer_list<int> costs){for(int cost:costs)clock.atomicWork(cost,[]{},display,false);};
    auto point=[&](const char* name){boundary(name,clock.now,timing.tick,timing.countdown,state,timing.input);};
    point("begin");work({16,4,8});point("lineWait");work({24});
    for(int attempts=0;;++attempts){
        if(attempts>5000)throw std::runtime_error("Instruction line wait did not terminate");
        int line=-1;clock.accessWork(12,8,[&]{line=airResultScanline(clock.now-timing.lcdEpoch);},display,false);
        poll(clock.now,line);work({8,line==144?8:12});if(line==144)break;
    }
    work({16,12});clock.atomicWork(16,[&]{state.lcdc&=~2;},display,false);point("objectsDisabled");
    // Identified 2699..26a9 critical section. Its controls do not cross a
    // periodic request. A crossing needs a separate pending-service owner.
    if(clock.now+76>=std::min(clock.nextStat,clock.nextVBlank))throw std::runtime_error("Unowned instruction callback critical crossing");
    clock.now+=4+4+16;state.scroll=0;point("scrollCleared");
    clock.now+=8+16;state.display=5;point("callbacksReady");
    clock.now+=16+4;state.stat=5;clock.statBody=288;point("enabled");
    work({8});clock.accessWork(12,8,[&]{state.lyc=95;
        clock.nextStat=timing.lcdEpoch+(clock.now-timing.lcdEpoch)/AirClock::Frame*AirClock::Frame+95*456;
        while(clock.nextStat<=clock.now)clock.nextStat+=AirClock::Frame;
    },display,false);point("compareReady");work({8});
    // Pinned DMG STAT-write request in horizontal/vertical blank: the write temporarily
    // asserts all STAT sources. The preceding LY read can retain 144 across
    // a display service, so the write itself can occur on the following frame.
    // The request is accepted at
    // the identified write completion, before 26af's map jump.
    AirPauseLcd lcd;lcd.objectsEnabled=false;lcd.windowEnabled=false;
    int mode=lcd.mode(clock.now+8-timing.lcdEpoch);
    if(mode!=0&&mode!=1)throw std::runtime_error("Unowned instruction STAT-write mode");
    work({12});clock.stat(AirIrqOwner::SourceBoundary);point("mapJump");work({16});point("mapBegin");
    work({12,8});
    for(int row=0;row<8;++row){
        work({8,8,8});int pattern=ui.instructionPattern[row];
        for(int bit=0;bit<8;++bit){
            bool alternate=pattern&1;pattern=(pattern>>1)|((pattern&1)<<7);
            work({8,8,alternate?8:12});if(alternate)work({8});point("stepWait");
            clock.wait(display,false);point("stepReady");work({12,8,4});point("mapWrite");
            clock.accessWork(12,8,[&]{state.lcdc=(state.lcdc&~8)|(alternate?8:0);},display,false);point("stepComplete");
            work({4,bit==7?8:12});
        }
        work({4,row==7?8:12});
    }
    point("mapReturn");work({16});point("end");
    timing.end=clock.now;timing.displays=clock.displays;timing.stats=clock.statServices;
    timing.nextStat=clock.nextStat;timing.nextVBlank=clock.nextVBlank;return state;
}
}
