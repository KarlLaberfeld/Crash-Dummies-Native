#pragma once
#include "air_instruction_text.h"

namespace ticd {
template<class Boundary,class Service,class Interrupt,class Poll,class Write>
AirInstructionTextState airInstructionExit(AirInstructionTextState state,NativeAudio& sound,const UiAssets& ui,
    Boundary&& boundary,Service&& service,Interrupt&& interrupt,Poll&& poll,Write&& write,std::function<int()> sampleInput={}){
    if(state.speed||state.skipMask||state.map.display!=5||state.map.stat!=5||state.map.lyc!=95||!sound.enabled)
        throw std::runtime_error("Unowned instruction exit entry");
    auto& timing=state.map.campaign.timing;AirClock clock;
    clock.now=timing.end;clock.nextStat=timing.nextStat;clock.nextVBlank=timing.nextVBlank;
    clock.displays=timing.displays;clock.statServices=timing.stats;clock.statBody=288;
    clock.interrupt=[&](const char* kind,int64_t cycle,AirIrqOwner owner){interrupt(kind,cycle,owner);};
    auto display=[&](bool){
        timing.input.sample(sampleInput?sampleInput():timing.input.held);
        if(timing.input.held<0||timing.input.held>255||(timing.input.held&15)==15)throw std::runtime_error("Unowned instruction exit input/reset");
        int tick=timing.tick;timing.tick=(tick+1)&65535;sound.tick();
        if(sound.effectWorkCycles<0||sound.musicWorkCycles<0)throw std::runtime_error("Unowned instruction exit audio");
        service(clock.displays,clock.now+20,tick,timing.countdown,144,sound.effectWorkCycles,sound.musicWorkCycles,timing.input);
        return 1592+144+sound.effectWorkCycles+sound.musicWorkCycles;
    };
    auto store=[&](int64_t cycle,int address,int value){
        if(state.backgroundOwned&&address>=0x9800&&address<0x9c00)state.background[address-0x9800]=value;
        write(cycle,address,value);};
    AirResultWriter writer(clock,timing.lcdEpoch,display,poll,store);writer.layer=0x9800;writer.cursor=state.cursor;writer.row=state.row;
    int bgp=0xe4,obp0=0xc4,obp1=0xe0;
    auto work=[&](std::initializer_list<int> costs){writer.work(costs);};
    auto point=[&](const char* name){boundary(name,clock.now,timing.tick,timing.countdown,state.map.scroll,bgp,obp0,obp1,sound.enabled,timing.input);};
    point("begin");work({12,8,timing.input.held&8?12:8});
    if(!(timing.input.held&8)){
        point("prompt");std::vector<AirResultTextCommand> prompt;
        for(int glyph:ui.startPrompt){if(glyph>=128)throw std::runtime_error("Unowned instruction prompt glyph");prompt.push_back({0,glyph,0});}
        prompt.push_back({4,0,0});writer.text(prompt);point("promptReady");work({8});point("inputCall");work({24});
        for(int attempts=0;;++attempts){
            if(attempts>3000)throw std::runtime_error("Instruction fresh-Start wait exceeds diagnostic input extent");
            point("inputWait");clock.wait(display,false);point("inputReady");bool start=timing.input.pressed&8;
            work({12,4,start?20:8});if(start)break;work({12});
        }
    }
    point("fadeCall");work({24,12,8});
    for(int segment=0;segment<8;++segment){
        point("fadePalette");int value=ui.fadePalettes[segment];work({8});
        clock.accessWork(12,8,[&]{bgp=value;},display,false);point("bgpReady");work({8});
        clock.accessWork(12,8,[&]{obp1=value&0xf3;},display,false);work({8,8});
        clock.accessWork(12,8,[&]{obp0=value&0xcf;},display,false);work({8});
        for(int wait=0;wait<4;++wait){
            point("fadeWait");clock.wait(display,false);point("fadeReady");work({4,wait==3?8:12});
        }
        work({4,segment==7?8:12});
    }
    work({16});point("fadeReturned");clock.wait(display,false);point("audioStop");
    int stop=audioStopWork();
    if(clock.now+stop>=std::min(clock.nextStat,clock.nextVBlank))throw std::runtime_error("Interrupted instruction audio reset requires a completion owner");
    clock.now+=stop;sound.stop();point("end");
    state.cursor=writer.cursor;timing.end=clock.now;timing.displays=clock.displays;timing.stats=clock.statServices;
    timing.nextStat=clock.nextStat;timing.nextVBlank=clock.nextVBlank;return state;
}
}
