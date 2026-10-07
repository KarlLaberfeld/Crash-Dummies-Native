#pragma once
#include "air_result_transition.h"
#include "air_pause_lcd.h"

namespace ticd {
struct AirResultTextCommand {int kind=0,a=0,b=0;};
struct AirResultTextAssets {
    std::array<std::vector<AirResultTextCommand>,3> layouts;
    static AirResultTextAssets load(const char* path){
        std::ifstream file(path,std::ios::binary);char magic[8];
        if(!file.read(magic,8)||std::string(magic,8)!="TICDRL01")throw std::runtime_error("Missing result text layouts");
        AirResultTextAssets data;
        for(auto& list:data.layouts){unsigned char bytes[2];if(!file.read(reinterpret_cast<char*>(bytes),2))throw std::runtime_error("Truncated result text count");
            int size=bytes[0]+256*bytes[1];if(size<1||size>4096)throw std::runtime_error("Invalid result text count");
            for(int i=0;i<size;++i){unsigned char args[3];if(!file.read(reinterpret_cast<char*>(args),3))throw std::runtime_error("Truncated result text");
                if(args[0]>4||(args[0]==4)!=(i==size-1)||(args[0]==0&&args[1]>127)||
                   (args[0]==1&&(args[1]>31||args[2]>31))||(args[0]==3&&args[1]>1))
                    throw std::runtime_error("Invalid result text command");
                list.push_back({args[0],args[1],args[2]});}
        }
        if(file.peek()!=std::char_traits<char>::eof())throw std::runtime_error("Trailing result text data");return data;
    }
};
// Identified native glyph and numeric formatting operations. The only command
// language is the decoded menu layout; no CPU register/instruction interpreter.
template<class Display,class Poll,class Write>
struct AirResultWriter {
    AirClock& clock;int64_t epoch;Display& display;Poll& poll;Write& write;
    AirPauseLcd lcd;int cursor=0x9c00,anchor=0,row=0,layer=0x9c00;bool leading=false;
    AirResultWriter(AirClock& c,int64_t e,Display& d,Poll& p,Write& w):clock(c),epoch(e),display(d),poll(p),write(w){lcd.objectsEnabled=false;lcd.windowEnabled=false;}
    void work(std::initializer_list<int> costs){for(int cost:costs)clock.atomicWork(cost,[]{},display,false);}
    void glyph(int value){
        if(cursor<0x9800||cursor>=0xa000||value<0||value>255)throw std::runtime_error("Unowned result glyph destination/value");
        work({16}); // Safe store's saved glyph.
        for(int attempt=0;;++attempt){
            if(attempt>32)throw std::runtime_error("Result glyph readiness did not terminate");
            int mode=-1;clock.accessWork(12,8,[&]{mode=lcd.mode(clock.now-epoch);},display,false);
            if(mode<0)throw std::runtime_error("Unowned first-frame result graphics readiness");
            poll(clock.now,mode);work({8,mode&2?12:8});if(!(mode&2))break;
        }
        work({12});write(clock.now,cursor,value);
        clock.accessWork(8,4,[]{},display,false);clock.atomicWork(8,[&]{++cursor;},display,false);work({16});
    }
    void positionWork(){work({4,4,4,4,4,8,4,4,4,4,4,4,16,4,4,16});}
    void text(const std::vector<AirResultTextCommand>& commands){
        work({16,16,12,16,4,16,4});
        for(const auto& command:commands){
            if(command.kind==0){
                work({8,8,8,16,8,command.a?8:12});if(command.a)work({16,4,12});
                work({12,24});glyph(command.a);work({12});continue;
            }
            // Identified layout-command dispatch with a non-crossing table.
            work({8,8,12,16,12,24,4,16,4,4,20,8,8,4,16,4});
            if(command.kind==4){work({4,16,4,16,4,16,16,16,16});return;}
            if(command.kind==1){work({12,8,4,16,8,4,24});anchor=command.a;row=command.b;cursor=layer+32*row+anchor;positionWork();work({16});}
            else if(command.kind==2){work({12,4,16,4,24});++row;cursor=layer+32*row+anchor;positionWork();work({16});}
            else if(command.kind==3){work({12,8,4,4,8,16,16});layer=0x9800+1024*command.a;}
            else throw std::runtime_error("Unowned result layout command");
        }
        throw std::runtime_error("Incomplete result text layout");
    }
    void digit(int n){
        work({8,n?8:12});
        if(!n){work({8,leading?12:8});if(!leading)work({4,12});glyph(leading?1:0);return;}
        work({8,leading?12:8});
        if(!leading){work({8,16,8,24});--cursor;glyph(0x33);work({12,8,12});leading=true;}
        glyph(n+1);
    }
    void pair(int value,bool force=false){
        if(force){work({8});leading=true;}
        work({8,8,8,4,24});digit(value/10);work({8,8,4,16});digit(value%10);
    }
    void money(int value,bool savings){
        if(value<0||value>=1000000)throw std::runtime_error("Invalid result amount");
        if(savings){work({24,12,24,16,4,4,4,8,4,8,16,4,4,8,24});cursor=0x9ded;}
        else{work({24,12,12,8,24});cursor=0x9e0d;}
        leading=false;pair(value/10000);
        work({24,8,8,8,4,24});digit((value/1000)%10);
        work({8,leading?12:8});
        if(!leading){work({8,8,8,24});leading=true;--cursor;glyph(0x33);}
        work({8,8,4,16});digit((value/100)%10);
        work({4,16});++cursor;pair(value%100,true);
    }
    void time(int seconds){
        if(seconds<0||seconds>99)throw std::runtime_error("Invalid result time");
        work({24,12,12,16});cursor=0x9e32;pair(seconds,true);
    }
};
struct AirResultAccounting {AirResultTransition timing;int pay=0,savings=0,seconds=0,stage=1;};
template<class Boundary,class Service,class Interrupt,class Poll,class Write>
AirResultAccounting airResultAccount(AirResultTransition state,int result,int held,int pay,int savings,int seconds,
    NativeAudio& sound,const AirResultTextAssets& texts,Boundary&& boundary,Service&& service,Interrupt&& interrupt,Poll&& poll,Write&& write,
    std::function<int()> sampleInput={}){
    if(result!=3||(held&15)==15||state.displays!=33||state.countdown!=567||pay<0||savings<0||seconds<0)
        throw std::runtime_error("Unowned successful result/accounting input");
    AirResultAccounting account;account.pay=pay;account.savings=savings;account.seconds=seconds;
    AirClock clock;clock.now=state.end;clock.nextStat=state.nextStat;clock.nextVBlank=state.nextVBlank;
    clock.displays=state.displays;clock.statServices=state.stats;clock.statBody=248;
    clock.interrupt=[&](const char* kind,int64_t cycle,AirIrqOwner owner){interrupt(kind,cycle,owner);};
    auto display=[&](bool){
        state.input.sample(sampleInput?sampleInput():state.input.held);
        if(state.input.held<0||state.input.held>255||(state.input.held&15)==15)throw std::runtime_error("Unowned accounting input/reset service");
        int tick=state.tick;state.tick=(state.tick+1)&65535;int work=airResultCountdownWork(state.countdown);sound.tick();
        if(sound.effectWorkCycles<0||sound.musicWorkCycles<0)throw std::runtime_error("Unowned accounting audio service");
        service(clock.displays,clock.now+20,tick,state.countdown,work,sound.effectWorkCycles,sound.musicWorkCycles,sound.enabled);
        return 1592+work+sound.effectWorkCycles+sound.musicWorkCycles;};
    AirResultWriter writer(clock,state.lcdEpoch,display,poll,write);
    auto point=[&](const char* name){boundary(name,clock.now,state.tick,state.countdown,account.pay,account.savings,account.seconds,account.stage,sound.enabled,state.skip);};
    auto works=[&](std::initializer_list<int> costs){writer.work(costs);};
    auto delay=[&](int count,bool ready){
        works({24});for(int i=0;i<count;++i){works({16,4,state.skip?20:8});if(state.skip)return;
            clock.wait(display,false);
            if(ready){works({12,16});state.skip=state.input.pressed;works({4,state.skip&11?20:8});if(state.skip&11)return;}
            works({8,4,4,i<count-1?12:8});if(i==count-1)works({16});}
    };
    auto savingsIncrement=[&]{works({24,16,4,4,4,8,4,8,8,8,4,8,8,8,4,8,8,8,4,8,16});account.savings=(account.savings+1)%1000000;};
    auto buttonWait=[&]{works({24});clock.wait(display,false);int edge=state.input.pressed&11;
        works({12,8,edge?8:20});if(edge){works({16});state.skip=edge;works({16});}};
    point("begin");works({8,12});point("readyWait");delay(15,true);point("readyReturned");
    works({8});clock.accessWork(12,8,[&]{
        auto frame=(clock.now-state.lcdEpoch)/AirClock::Frame;
        clock.nextStat=state.lcdEpoch+frame*AirClock::Frame+120*456;
        while(clock.nextStat<=clock.now)clock.nextStat+=AirClock::Frame;
    },display,false);point("detailSetup");works({24,16,4,4,4,8,4,8,16});point("dayReady");
    works({8,8,12});point("savingsLabel");writer.text(texts.layouts[0]);point("savingsNumber");writer.money(account.savings,true);
    point("savingsNumberReady");works({12});point("savingsDelay");delay(20,false);
    point("payLabel");works({24});writer.text(texts.layouts[1]);works({16,8,20});point("payNumber");writer.money(account.pay,false);
    point("payLoop");works({24});
    for(int iterations=0;;++iterations){
        if(iterations>1000000)throw std::runtime_error("Result pay accounting did not terminate");
        point("payTest");works({12,8,8,4,8,account.pay?8:20});if(!account.pay)break;
        works({16});point("savingsIncrement");savingsIncrement();point("payDecrement");
        works({24,12,8,8,4,8,8,8,4,8,8,8,4,8,16});--account.pay;point("payUpdated");
        works({16,8,12,16,4,state.skip?12:8});
        if(!state.skip){point("payWait");buttonWait();point("savingsRefresh");writer.money(account.savings,true);
            point("payRefresh");writer.money(account.pay,false);}
        point("payTail");works({12,12});
    }
    point("payDone");writer.money(account.savings,true);point("payTotal");writer.money(account.pay,false);point("payShowEnded");
    works({16,8,8,12});delay(15,false);point("timeLabel");works({24});writer.text(texts.layouts[2]);works({16,8,20});
    point("timeNumber");writer.time(account.seconds);point("timeLoop");works({24});
    for(;;){point("timeTest");works({16,4,account.seconds?8:20});if(!account.seconds)break;
        point("timeUnit");works({16});point("timeSavingsIncrement");savingsIncrement();point("timeDecrement");
        works({24,16,8,4,8,16,16});--account.seconds;point("timeResult");works({16,8,12,16,4,state.skip?12:8});
        if(!state.skip){point("timeWait");buttonWait();point("timeSavingsRefresh");writer.money(account.savings,true);point("timeRefresh");writer.time(account.seconds);}
        point("timeTail");works({12,12});}
    point("timeDone");writer.money(account.savings,true);point("finalSavings");writer.time(account.seconds);point("accountingComplete");
    int waitCount=state.countdown+60;works({8,16,4,16,4,8,16,4,4,(state.countdown&255)+60>255?8:20});
    if((state.countdown&255)+60>255)works({4,16});point("timerWait");works({24});
    for(int i=0;i<waitCount;++i){clock.wait(display,false);bool exit=state.input.pressed&11;
        works({12,4,exit?20:8});if(exit)break;
        works({8,4,4,i<waitCount-1?12:8});if(i==waitCount-1)works({16});}
    point("finalMusicStop");if(clock.now+audioStopWork()>=std::min(clock.nextStat,clock.nextVBlank))throw std::runtime_error("Interrupted accounting audio stop needs its owner");
    clock.now+=audioStopWork();sound.stop();point("musicStopped");works({24,16,4,4,4,8,4,8,16});point("dayAdvance");
    works({8,4,8,8,12});++account.stage;point("end");state.end=clock.now;state.displays=clock.displays;state.stats=clock.statServices;
    state.nextStat=clock.nextStat;state.nextVBlank=clock.nextVBlank;account.timing=state;return account;
}
}
