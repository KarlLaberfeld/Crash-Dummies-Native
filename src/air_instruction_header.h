#pragma once
#include "air_result_handoff.h"

namespace ticd {
struct AirInstructionHeaderAssets {
    std::array<std::array<unsigned char,3>,2> playerNames{};
    std::array<std::vector<AirResultTextCommand>,12> layouts;
    static AirInstructionHeaderAssets load(const char* path){
        std::ifstream file(path,std::ios::binary);char magic[8];AirInstructionHeaderAssets assets;
        if(!file.read(magic,8)||std::string(magic,8)!="TICDIH01"||
            !file.read(reinterpret_cast<char*>(assets.playerNames.data()),6))throw std::runtime_error("Missing instruction header assets");
        for(auto& name:assets.playerNames)for(int value:name)if(value<1||value>127)throw std::runtime_error("Invalid player-name glyph");
        for(auto& list:assets.layouts){unsigned char bytes[2];
            if(!file.read(reinterpret_cast<char*>(bytes),2))throw std::runtime_error("Truncated instruction header count");
            int count=bytes[0]+256*bytes[1];if(count<1||count>4096)throw std::runtime_error("Invalid instruction header count");
            for(int i=0;i<count;++i){unsigned char args[3];
                if(!file.read(reinterpret_cast<char*>(args),3)||args[0]>5||(args[0]==4)!=(i==count-1)||
                    (args[0]==0&&args[1]>127)||(args[0]==1&&(args[1]>31||args[2]>31))||
                    (args[0]==3&&args[1]>1)||(args[0]==5&&(args[1]||args[2])))throw std::runtime_error("Invalid instruction header command");
                list.push_back({args[0],args[1],args[2]});}
        }
        if(file.peek()!=std::char_traits<char>::eof())throw std::runtime_error("Trailing instruction header assets");return assets;
    }
};
enum class AirHeaderPresentation { Result, Instruction };
// Identified cleared-result 02ce..031c header and its first counter wait.
// Campaign values and LCD/list state come from the native preceding handoff.
// The post-title wrapper separately owns callback 5's zero center/scroll and
// empty maps/objects; Result retains the original success/failure callbacks.
// Instruction music/text/fades and next LCD/gameplay setup remain separate.
template<class Boundary,class Service,class Interrupt,class Poll,class Write>
AirResultHandoff airInstructionHeader(AirResultHandoff state,int stage,int difficulty,NativeAudio& sound,
    const AirInstructionHeaderAssets& assets,Boundary&& boundary,Service&& service,Interrupt&& interrupt,
    Poll&& poll,Write&& write,std::function<int()> sampleInput={},AirHeaderPresentation presentation=AirHeaderPresentation::Result){
    const bool instruction=presentation==AirHeaderPresentation::Instruction;
    if(state.result||state.player<0||state.player>1||state.lives[state.player]<1||state.lives[state.player]>255||
        stage<0||stage>4||difficulty<0||difficulty>3||sound.enabled||(instruction&&state.timing.perfect)||
        (presentation!=AirHeaderPresentation::Result&&!instruction))
        throw std::runtime_error("Unowned instruction header campaign state");
    auto& timing=state.timing;
    AirClock clock;clock.now=timing.end;clock.nextStat=timing.nextStat;clock.nextVBlank=timing.nextVBlank;
    clock.displays=timing.displays;clock.statServices=timing.stats;clock.statBody=(timing.perfect||instruction)?288:248;
    clock.interrupt=[&](const char* kind,int64_t cycle,AirIrqOwner owner){interrupt(kind,cycle,owner);};
    if(instruction)clock.rasterWork=[&](int64_t start){write(start+216,0xff42,0);return 288;};
    AirPauseLcd* graphics=nullptr;
    auto updateGraphics=[&]{if(!graphics||!timing.perfect)return;
        graphics->objectsEnabled=true;graphics->objectHeight=8;graphics->objectDisableLine=120;
        for(int i=0;i<40;++i)graphics->objects[i]={timing.celebrationVisible[i*4+1],timing.celebrationVisible[i*4]};};
    auto display=[&](bool){
        timing.input.sample(sampleInput?sampleInput():timing.input.held);
        if(timing.input.held<0||timing.input.held>255||(timing.input.held&15)==15)throw std::runtime_error("Unowned instruction header input/reset");
        int tick=timing.tick;timing.tick=(tick+1)&65535;
        if(timing.perfect){timing.celebrationVisible=timing.celebration.prepared;updateGraphics();}
        if(instruction)write(clock.now+20+1284,0xff42,0);
        int work=instruction?144:airResultCountdownWork(timing.countdown)+(timing.perfect?68:0);sound.tick();
        if(sound.effectWorkCycles<0||sound.musicWorkCycles<0)throw std::runtime_error("Unowned instruction header audio");
        service(clock.displays,clock.now+20,tick,timing.countdown,work,sound.effectWorkCycles,sound.musicWorkCycles,timing.input);
        return 1592+work+sound.effectWorkCycles+sound.musicWorkCycles;
    };
    AirResultWriter writer(clock,timing.lcdEpoch,display,poll,write);graphics=&writer.lcd;updateGraphics();writer.layer=0x9800;
    auto work=[&](std::initializer_list<int> costs){writer.work(costs);};
    auto point=[&](const char* name){boundary(name,clock.now,timing.tick,timing.countdown,state.player,stage,difficulty,timing.input);};
    point("begin");writer.text(assets.layouts[0],&assets.playerNames[state.player]);point("playerLabelReady");
    work({24,16,4,4,4,8,4,8,16});point("livesReady");
    work({8,8,state.lives[state.player]<9?12:8});if(state.lives[state.player]>=9)work({8});point("livesClamped");
    work({4,24});writer.glyph(std::min(state.lives[state.player],9)+1);point("livesPrinted");
    writer.text(assets.layouts[1]);point("stageLabelReady");work({24,16,4,4,4,8,4,8,16});point("stageReady");
    work({8,24,12,16,4,16,4,4,20,8,8,4,4});writer.text(assets.layouts[3+stage]);work({16});point("stagePrinted");
    writer.text(assets.layouts[2]);point("difficultyLabelReady");work({24,16,4,4,4,8,4,8,16});point("difficultyReady");
    work({8,24,12,16,4,16,4,4,20,8,8,4,4});writer.text(assets.layouts[8+difficulty]);work({16});point("difficultyPrinted");
    clock.wait(display,false);point("end");
    timing.end=clock.now;timing.displays=clock.displays;timing.stats=clock.statServices;
    timing.nextStat=clock.nextStat;timing.nextVBlank=clock.nextVBlank;return state;
}
}
