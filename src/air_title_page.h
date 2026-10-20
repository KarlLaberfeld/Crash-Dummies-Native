#pragma once
#include "air_title_close.h"

namespace ticd {
struct AirTitlePage {AirTitleClose close;int cleared=0,rows=0,opened=0;};
// 27f9..2707: two closed-window clears, first page, forty reopening waits.
// WX=166 readiness is explicitly bounded to empty OAM/no horizontal scroll.
template<class Boundary,class Service,class Interrupt,class Raster,class Poll,class Write>
AirTitlePage airTitlePage(AirTitleClose close,NativeAudio& sound,const UiAssets& ui,Boundary&& boundary,
    Service&& service,Interrupt&& interrupt,Raster&& raster,Poll&& poll,Write&& write,std::function<int()> sample={},bool retainedClock=false,int pageIndex=0,const AirResultTextAssets* texts=nullptr){
    const auto& initial=close.fade.layout;const auto& before=initial.reset.timing;
    if(pageIndex<0||pageIndex>4||(pageIndex&&(!texts||!retainedClock))||close.center!=176||close.steps!=40||initial.windowY!=72||initial.windowX!=166||initial.reset.servicesMasked||initial.reset.pendingRequests||
       initial.reset.stat!=1||initial.reset.lcdc!=0xc3||initial.reset.scrollX||initial.reset.scrollY||initial.lyc!=23||
       (!retainedClock&&(before.displays!=620||before.stats!=731))||
       (retainedClock&&(before.displays<620||before.stats<731||before.end<before.lcdEpoch+AirClock::Frame||before.nextStat<=before.end||before.nextVBlank<=before.end))||before.countdown!=54||!sound.enabled||sound.song!=1||
       std::any_of(initial.reset.objects.begin(),initial.reset.objects.end(),[](int value){return value!=0;}))
        throw std::runtime_error("Unowned first title page entry");
    AirTitlePage state;state.close=std::move(close);auto& title=state.close.fade.layout;auto& r=title.reset;auto& t=r.timing;
    AirClock clock;clock.now=t.end;clock.nextStat=t.nextStat;clock.nextVBlank=t.nextVBlank;clock.displays=t.displays;clock.statServices=t.stats;
    clock.interrupt=[&](const char* kind,int64_t cycle,AirIrqOwner owner){interrupt(kind,cycle,owner);};
    auto display=[&](bool){
        t.input.sample(sample?sample():t.input.held);if(t.input.held<0||t.input.held>255||(t.input.held&15)==15)throw std::runtime_error("Unowned title page input/reset");
        int tick=t.tick;t.tick=(tick+1)&65535;sound.tick();
        if(sound.effectWorkCycles<0||sound.musicWorkCycles<0)throw std::runtime_error("Unowned title page audio");
        service(clock.displays,clock.now+20,tick,t.countdown,116,sound.effectWorkCycles,sound.musicWorkCycles,t.input);
        return 1592+116+sound.effectWorkCycles+sound.musicWorkCycles;
    };
    clock.rasterWork=[&](int64_t start){return airTitleRasterWork(clock,title,state.close.center,start,raster,write);};
    auto store=[&](int64_t cycle,int address,int value){if(address>=0x9c00&&address<0xa000)r.window.at(address-0x9c00)=static_cast<uint8_t>(value);write(cycle,address,value);};
    AirResultWriter writer(clock,t.lcdEpoch,display,poll,store);writer.lcd.windowEnabled=true;writer.lcd.windowX=166;writer.lcd.windowY=72;
    writer.lcd.objectHeight=8;writer.lcd.objectsEnabled=true;writer.lcd.titleRightEdge=true;
    auto work=[&](std::initializer_list<int> costs){writer.work(costs);};
    auto point=[&](const char* name){boundary(name,clock.now,state);};
    point("begin");
    for(int pass=0;pass<2;++pass){
        if(pass)work({24});point("clearEntry");work({12,12});
        for(int cell=0;cell<320;++cell){
            for(int attempt=0;;++attempt){
                if(attempt>32)throw std::runtime_error("Title clear readiness did not terminate");
                int mode=-1;clock.accessWork(12,8,[&]{mode=writer.lcd.mode(clock.now-t.lcdEpoch);},display,false);
                if(mode<0)throw std::runtime_error("Unowned title clear geometry");poll(clock.now,mode);work({8,mode&2?12:8});if(!(mode&2))break;
            }
            write(clock.now,0x9dc0+cell,0);clock.atomicWork(8,[&]{r.window[448+cell]=0;},display,false);
            work({8,4,4,cell==319?8:12});
        }
        work({16});++state.cleared;point(pass?"clearReturned":"closeReturned");
    }
    // Page-zero duration and static layout dispatch, including its RST JP.
    work({16,4,4,12,16,4,4,20,8,8,8,8,16,8,8,4});point("pageCall");work({24,4});point("pageEntry");
    if(pageIndex){
        writer.layer=0x9c00;writer.text(texts->layouts.at(pageIndex-1));
        if(pageIndex==2){
            // 2aac..2adc formats the eight retained native high-score records.
            // Each record is three glyphs and three packed BCD bytes. The
            // campaign path measured here leaves the initial table unchanged.
            work({12,8});
            for(int row=0;row<8;++row){
                point("scoreRow");work({8,4,24});writer.glyph(row+2);work({4});++writer.cursor;
                for(int i=0;i<3;++i){work({8,24});writer.glyph(ui.initialScores[6*row+i]);}
                work({4,4,8,24});writer.cursor+=2;writer.leading=false;
                auto bcd=[&](int i){int value=ui.initialScores[6*row+3+i];if((value&15)>9||(value>>4)>9)throw std::runtime_error("Invalid title score BCD");return 10*(value>>4)+(value&15);};
                writer.pair(bcd(0));work({24,8,8,8,4,24});writer.digit(bcd(1)/10);work({8,writer.leading?12:8});
                if(!writer.leading){work({8,8,8,24});--writer.cursor;writer.glyph(0x33);writer.leading=true;}
                work({8,8,4,16});writer.digit(bcd(1)%10);work({8,24});writer.glyph(0x2c);work({24});writer.pair(bcd(2),true);
                int carry=(writer.cursor&255)+18>255;work({8,16,4,4,carry?8:20});if(carry)work({4,16});writer.cursor+=18;
                work({4,row==7?8:12});
            }
        }
        point("pageReturn");work({16});
    }else{
    work({16,16,12,16,4,16,4});
    writer.commandDispatch();work({12,8,4,4,8,16,16});writer.layer=0x9c00;
    writer.commandDispatch();work({12,8,4,16,8,4,24});writer.anchor=0;writer.row=14;writer.cursor=0x9dc0;writer.positionWork();work({16});
    writer.commandDispatch();work({12,8,4,8,4,8,12,8,12,8,12,16,16,4,16,4,12,24});point("rectangleEntry");
    work({12,12,16,12,16,12,16,16,16});
    for(int row=0;row<10;++row){
        work({16,16});writer.cursor=0x9dc0+32*row;
        for(int column=0;column<20;++column){work({8,24});int value=ui.titleMaps[0][448+32*row+column];writer.glyph(value);
            r.window[448+32*row+column]=value;work({4,column==19?8:12});}
        state.rows=row+1;point("rowReady");int destination=0x9dc0+32*row;
        work({12,12,8,16,4,4,(destination&255)+32>255?8:20});
        if((destination&255)+32>255)work({4,16});
        work({4,row==9?8:12});
    }
    work({12,12,16,12,16,16});point("copyReturned");work({16,12,16});
    writer.commandDispatch();work({4,16,4,16,4,16,16,16,16});point("pageReturn");work({16});
    }
    point("pageReturned");work({24});
    for(int step=0;step<40;++step){
        point("openWait");clock.wait(display,false);point("openReady");work({12});
        write(clock.now,0xff4a,title.windowY+1);clock.atomicWork(12,[&]{++title.windowY;},display,false);work({16,8});
        write(clock.now,0xc09c,(state.close.center+2)&255);clock.atomicWork(16,[&]{state.close.center=(state.close.center+2)&255;++state.opened;},display,false);
        point("centerStored");work({step==39?8:12});
    }
    work({16});point("end");t.end=clock.now;t.displays=clock.displays;t.stats=clock.statServices;t.nextStat=clock.nextStat;t.nextVBlank=clock.nextVBlank;return state;
}
}
