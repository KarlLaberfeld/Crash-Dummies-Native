#pragma once
#include "air_instruction_map.h"

namespace ticd {
struct AirInstructionTextState {
    AirInstructionMapState map;
    int speed=0,delay=0,skipMask=0,anchor=0,row=0;
    bool skipped=false;int skipContext=0;
};
// Identified timed UI language, not cartridge instructions. Glyph delays,
// five-part row scrolls and substitutions own their source operations. The
// preceding instruction's unused cursor/delay are overwritten by its layout.
template<class Boundary,class Service,class Interrupt,class Poll,class Write>
AirInstructionTextState airInstructionText(AirInstructionMapState map,int stage,int difficulty,NativeAudio& sound,const UiAssets& ui,
    Boundary&& boundary,Service&& service,Interrupt&& interrupt,Poll&& poll,Write&& write,std::function<int()> sampleInput={}){
    if(stage<1||stage>2||difficulty<0||difficulty>3||map.display!=5||map.stat!=5||map.lyc!=95||
        map.scroll||map.lcdc&2||map.campaign.result||!sound.enabled)throw std::runtime_error("Unowned instruction text entry");
    AirInstructionTextState state;state.map=map;auto& timing=state.map.campaign.timing;
    AirClock clock;clock.now=timing.end;clock.nextStat=timing.nextStat;clock.nextVBlank=timing.nextVBlank;
    clock.displays=timing.displays;clock.statServices=timing.stats;clock.statBody=288;
    clock.interrupt=[&](const char* kind,int64_t cycle,AirIrqOwner owner){interrupt(kind,cycle,owner);};
    auto display=[&](bool){
        timing.input.sample(sampleInput?sampleInput():timing.input.held);
        if(timing.input.held<0||timing.input.held>255||(timing.input.held&15)==15)throw std::runtime_error("Unowned instruction text input/reset");
        int tick=timing.tick;timing.tick=(tick+1)&65535;sound.tick();
        if(sound.effectWorkCycles<0||sound.musicWorkCycles<0)throw std::runtime_error("Unowned instruction text audio");
        service(clock.displays,clock.now+20,tick,timing.countdown,144,sound.effectWorkCycles,sound.musicWorkCycles,timing.input);
        return 1592+144+sound.effectWorkCycles+sound.musicWorkCycles;
    };
    AirResultWriter writer(clock,timing.lcdEpoch,display,poll,write);writer.layer=0x9800;
    auto work=[&](std::initializer_list<int> costs){writer.work(costs);};
    auto point=[&](const char* name){state.anchor=writer.anchor;state.row=writer.row;boundary(name,clock.now,timing.tick,timing.countdown,state,timing.input);};
    const auto& script=ui.instructions[stage].text;size_t cursor=0,saved=0;std::vector<unsigned char> word;
    bool inWord=false;size_t wordCursor=0;int wordKind=0;
    auto byte=[&](){
        if(inWord){if(wordCursor<word.size())return int(word[wordCursor++]);inWord=false;cursor=saved;return 0x88;}
        if(cursor>=script.size())throw std::runtime_error("Truncated instruction text");return int(script[cursor++]);
    };
    auto finish=[&]{point("textFinish");work({4,16,4,16,4,16,16,16,16});state.speed=state.skipMask=0;writer.anchor=0;work({16});point("end");};
    auto skip=[&]{
        state.skipped=true;state.skipContext=inWord?wordKind:0;point("skip");work({12,12});
        for(int count=0;;++count){
            if(count>4096)throw std::runtime_error("Instruction skip did not terminate");
            int next=byte();work({8,8,next==0x88?12:8});
            if(next==0x88){work({16,4,16,4,12});continue;}
            work({8,next==0x80?8:12});if(next==0x80){work({16,12});break;}
        }
    };
    auto delay=[&]{
        if(state.speed!=5||state.delay<1||state.delay>5||state.skipMask!=8)throw std::runtime_error("Unowned instruction glyph delay");
        for(;;){point("glyphWait");clock.wait(display,false);point("glyphReady");
            bool abort=timing.input.pressed&state.skipMask;
            work({16,16,16,4,12,4,12,12,abort?12:8});
            if(abort){skip();return false;}
            work({16,4,16});--state.delay;work({state.delay?12:8});if(state.delay)continue;
            point("delayExpired");work({16,16,16});state.delay=state.speed;return true;
        }
    };
    point("begin");work({16,16,12,16,4,16,4});
    for(int operations=0;;++operations){
        if(operations>4096)throw std::runtime_error("Instruction text did not terminate");
        point("textNext");int op=byte();
        if(op<128){
            work({8,8,8,16,8,op?8:12});
            if(op){work({16,4,state.speed?24:12});if(state.speed&&!delay()){finish();break;}}
            work({12,24});writer.glyph(op);work({12});continue;
        }
        writer.commandDispatch();
        if(op==0x80){finish();break;}
        if(op==0x81){int column=byte(),row=byte();if(column>31||row>31)throw std::runtime_error("Invalid instruction anchor");
            work({12,8,4,16,8,4,24});writer.anchor=column;writer.row=row;writer.cursor=writer.layer+32*row+column;writer.positionWork();work({16});}
        else if(op==0x82){int layer=byte();if(layer)throw std::runtime_error("Unowned instruction text layer");work({12,8,4,4,8,16,16});writer.layer=0x9800;}
        else if(op==0x84){work({12,4,16,4,24});++writer.row;writer.cursor=writer.layer+32*writer.row+writer.anchor;writer.positionWork();work({16});}
        else if(op==0x85){
            point("scrollBegin");work({16,16,8,12,12});
            for(int step=0;step<5;++step){
                point("scrollWait");clock.wait(display,false);clock.wait(display,false);point("scrollReady");
                work({8,8,8});clock.atomicWork(8,[&]{state.map.scroll=(state.map.scroll+std::array<int,5>{1,2,3,1,1}[step])&255;},display,false);point("scrollStored");
                work({4,step==4?8:12});
            }
            point("scrollEnd");work({12,12,12,12,4,16,4,24});++writer.row;writer.cursor=writer.layer+32*writer.row+writer.anchor;writer.positionWork();work({16});
        }
        else if(op==0x86){int speed=byte();if(speed!=5)throw std::runtime_error("Unowned instruction text speed");work({12,8,16,16,16});state.speed=state.delay=speed;}
        else if(op==0x87){int mask=byte();if(mask!=8)throw std::runtime_error("Unowned instruction skip mask");work({12,8,16,16});state.skipMask=mask;}
        else if(op==0x88){work({12,16,4,16,4,16});}
        else if(op==0x89){
            int player=state.map.campaign.player;if(inWord||player<0||player>1)throw std::runtime_error("Unowned instruction name substitution");
            work({12,4,16,4,16,12,16,4,player?12:16});if(player)work({12,16});
            saved=cursor;inWord=true;wordCursor=0;wordKind=1;word.assign(ui.names.begin()+5*player,ui.names.begin()+5*player+5);
        }
        else if(op==0x8a){
            if(inWord||stage!=2)throw std::runtime_error("Unowned instruction quota substitution");
            work({12,4,16,4,16,16,24,16,4,4,4,8,4,8,16,8,4,12,4,4,12,16,4,4,20,16});
            saved=cursor;inWord=true;wordCursor=0;wordKind=2;word.assign(ui.skiQuotas.begin()+3*difficulty,ui.skiQuotas.begin()+3*difficulty+2);
        }
        else throw std::runtime_error("Unowned instruction text command");
    }
    timing.end=clock.now;timing.displays=clock.displays;timing.stats=clock.statServices;
    timing.nextStat=clock.nextStat;timing.nextVBlank=clock.nextVBlank;return state;
}
}
