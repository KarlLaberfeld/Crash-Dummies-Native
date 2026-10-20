#pragma once
#include "air_instruction_header.h"

namespace ticd {
// Bounded 031c..268b music/copy/picture prefix for Air's following instruction.
// Native decoded glyph pixels are repacked into their source tile bytes; no
// cartridge instructions, recorded transfer durations or readiness enter.
template<class Boundary,class Service,class Interrupt,class Poll,class Write>
AirResultHandoff airInstructionPicture(AirResultHandoff state,int stage,NativeAudio& sound,const UiAssets& ui,
    Boundary&& boundary,Service&& service,Interrupt&& interrupt,Poll&& poll,Write&& write,
    std::function<int()> sampleInput={},AirHeaderPresentation presentation=AirHeaderPresentation::Result){
    const bool instruction=presentation==AirHeaderPresentation::Instruction;
    if(state.result||stage<1||stage>2||sound.enabled||(instruction&&state.timing.perfect)||
       (presentation!=AirHeaderPresentation::Result&&!instruction))throw std::runtime_error("Unowned instruction picture entry");
    auto& timing=state.timing;AirClock clock;clock.now=timing.end;clock.nextStat=timing.nextStat;clock.nextVBlank=timing.nextVBlank;
    clock.displays=timing.displays;clock.statServices=timing.stats;clock.statBody=(timing.perfect||instruction)?288:248;
    clock.interrupt=[&](const char* kind,int64_t cycle,AirIrqOwner owner){interrupt(kind,cycle,owner);};
    if(instruction)clock.rasterWork=[&](int64_t start){write("scroll",start+216,0xff42,0);return 288;};
    AirPauseLcd* graphics=nullptr;
    auto updateGraphics=[&]{if(!graphics||!timing.perfect)return;
        graphics->objectsEnabled=true;graphics->objectHeight=8;graphics->objectDisableLine=120;
        for(int i=0;i<40;++i)graphics->objects[i]={timing.celebrationVisible[i*4+1],timing.celebrationVisible[i*4]};};
    auto display=[&](bool){
        timing.input.sample(sampleInput?sampleInput():timing.input.held);
        if(timing.input.held<0||timing.input.held>255||(timing.input.held&15)==15)throw std::runtime_error("Unowned instruction picture input/reset");
        int tick=timing.tick;timing.tick=(tick+1)&65535;
        if(timing.perfect){timing.celebrationVisible=timing.celebration.prepared;updateGraphics();}
        if(instruction)write("scroll",clock.now+20+1284,0xff42,0);
        int work=instruction?144:airResultCountdownWork(timing.countdown)+(timing.perfect?68:0);sound.tick();
        if(sound.effectWorkCycles<0||sound.musicWorkCycles<0)throw std::runtime_error("Unowned instruction picture audio");
        service(clock.displays,clock.now+20,tick,timing.countdown,work,sound.effectWorkCycles,sound.musicWorkCycles,timing.input);
        return 1592+work+sound.effectWorkCycles+sound.musicWorkCycles;
    };
    auto mapWrite=[&](int64_t cycle,int address,int value){write("map",cycle,address,value);};
    AirResultWriter writer(clock,timing.lcdEpoch,display,poll,mapWrite);graphics=&writer.lcd;updateGraphics();writer.layer=0x9800;
    auto work=[&](std::initializer_list<int> costs){writer.work(costs);};
    auto point=[&](const char* name){boundary(name,clock.now,timing.tick,timing.countdown,sound.enabled,timing.input);};
    point("begin");work({8});
    const int musicWork=airResultMusicStartWork();
    if(clock.now+musicWork>=std::min(clock.nextStat,clock.nextVBlank))throw std::runtime_error("Interrupted instruction music reset needs its own owner");
    clock.now+=musicWork;sound.playMusic(2);point("musicReady");
    work({24,16,4,4,4,8,4,8,16});point("stageReady");work({8,12});point("tableDispatch");
    work({24,4,16,4,4,20,8,8,4,4});point("resourceEntry");
    work({12,12,12,8});point("copyCall");work({24,12,12,16,12,16,12,16,16});
    for(int byte=0;byte<1024;++byte){
        int mode=-1;
        for(int attempt=0;;++attempt){
            if(attempt>32)throw std::runtime_error("Instruction tile readiness did not terminate");
            clock.accessWork(12,8,[&]{mode=writer.lcd.mode(clock.now-timing.lcdEpoch);},display,false);
            if(mode<0)throw std::runtime_error("Unowned instruction tile readiness at relative sample "+std::to_string(clock.now-timing.lcdEpoch-4));
            poll(clock.now,mode);work({8,mode&2?12:8});if(!(mode&2))break;
        }
        unsigned char value=0;
        clock.accessWork(8,4,[&]{int tile=52+byte/16,row=(byte%16)/2,plane=byte&1;
            for(int x=0;x<8;++x)value|=((ui.instructions[stage].tiles[tile*64+row*8+x]>>plane)&1)<<(7-x);},display,false);
        write("tile",clock.now,0x8340+byte,value);clock.accessWork(8,4,[]{},display,false);
        work({8,4,8,12,8,4,4,byte==1023?8:12});
    }
    work({12,16,12,16,16,16});point("copyReturned");
    work({16,16,12,16,4,16,4});writer.commandDispatch();work({12,8,4,16,8,4,24});writer.positionWork();work({16});
    writer.commandDispatch();work({12,8,4,8,4,8,12,8,12,8,12,16,16,4,16,4,12,24});
    work({12,12,16,12,16,12,16,16,16});
    for(int row=0;row<9;++row){
        work({16,16});writer.cursor=0x9800+(row+3)*32+5;
        for(int column=0;column<10;++column){work({8,24});writer.glyph(ui.instructions[stage].map[(row+3)*32+5+column]);work({4,column==9?8:12});}
        work({12,12,8,16,4,4,(writer.cursor-10)%256+32>255?8:20});
        if((writer.cursor-10)%256+32>255)work({4,16});
        work({4,row==8?8:12});
    }
    work({12,12,16,12,16,16,16});work({12,16});writer.commandDispatch();work({4,16,4,16,4,16,16,16,16});point("rectangleReady");
    work({24});point("end");
    timing.end=clock.now;timing.displays=clock.displays;timing.stats=clock.statServices;
    timing.nextStat=clock.nextStat;timing.nextVBlank=clock.nextVBlank;return state;
}
}
