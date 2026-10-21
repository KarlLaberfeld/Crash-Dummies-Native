#pragma once
#include "air_title_cycle.h"
#include "air_next_instruction_probe.h"
#include "air_instruction_voice_probe.h"
#include "native_ui_frame_probe.h"
namespace ticd {
inline void airProbeTitleCycle(const std::string& base,AirTitleMenu menu,NativeAudio& sound,const UiAssets& ui,std::function<int()> sample,int actionPage=0){
    if(actionPage<0||actionPage>4)throw std::runtime_error("Invalid later title action page");
    auto texts=AirResultTextAssets::load("build/title-text.dat");
    for(int pass=0;pass<5;++pass){
        std::string stem=base+".title-cycle."+std::to_string(pass);
        AirNextInstructionCsv page(stem+".page","boundary,cycle,index,center,closed,cleared,opened,rows,windowY,tick,countdown,stat,lcdc,scrollY,lyc,inputHeld,inputPressed");
        std::ofstream voices(stem+".page.voices.csv");airInstructionVoiceHeader(voices);
        std::ofstream raster(stem+".page.raster.csv");raster<<"boundary,cycle,stat,lcdc,scrollY,lyc\n";
        auto service=[&](unsigned index,int64_t cycle,int tick,int countdown,int display,int effects,int music,const DisplayInput& input){page.service(index,cycle,tick,countdown,display,effects,music,input);airInstructionVoiceRows(voices,index,sound,music);};
        menu=airTitleCycle(menu,sound,ui,texts,[&](const char* name,int64_t cycle,const AirTitleMenu& s,int center,int closed,int cleared,int opened,int rows){const auto& l=s.page.close.fade.layout;const auto& r=l.reset;const auto& t=r.timing;
            page.points<<name<<','<<cycle<<','<<s.index<<','<<center<<','<<closed<<','<<cleared<<','<<opened<<','<<rows<<','<<l.windowY<<','<<t.tick<<','<<t.countdown<<','<<r.stat<<','<<r.lcdc<<','<<r.scrollY<<','<<l.lyc<<','<<t.input.held<<','<<t.input.pressed<<'\n';},service,[&](auto... args){page.irq(args...);},[&](const char* name,auto... values){raster<<name;((raster<<','<<values),...);raster<<'\n';},[&](auto... args){page.poll(args...);},[&](auto... args){page.write(args...);},sample);
        auto finish=[&](AirNextInstructionCsv& output,const std::string& stem){const auto& r=menu.page.close.fade.layout.reset;const auto& t=r.timing;
            output.summary<<"end,lcdEpoch,tick,countdown,displays,stats,nextStat,nextVBlank,index,remaining,route,song\n"<<t.end<<','<<t.lcdEpoch<<','<<t.tick<<','<<t.countdown<<','<<t.displays<<','<<t.stats<<','<<t.nextStat<<','<<t.nextVBlank<<','<<menu.index<<','<<menu.remaining<<','<<menu.route<<','<<sound.song<<'\n';
            std::ofstream maps(stem+".maps.csv");maps<<"address,value\n";for(int i=0;i<2048;++i)maps<<(0x9800+i)<<','<<int(i<1024?r.background[i]:r.window[i-1024])<<'\n';};
        finish(page,stem+".page");
        UiFlow frame(ui);frame.phase=UiPhase::Title;frame.page=menu.index;frame.ticks=menu.page.close.fade.layout.reset.timing.tick;
        nativeUiFrame(stem+".page.frame.shades",frame.render());
        if(pass==4)break;
        AirNextInstructionCsv idle(stem+".idle","boundary,cycle,remaining,waits,index,tick,countdown,stat,lcdc,scrollY,lyc,inputHeld,inputPressed,route,pattern");
        std::ofstream idleVoices(stem+".idle.voices.csv");airInstructionVoiceHeader(idleVoices);
        std::ofstream idleRaster(stem+".idle.raster.csv");idleRaster<<"boundary,cycle,stat,lcdc,scrollY,lyc\n";
        auto inherited=menu;
        menu=airTitleMenuIdle(menu.page,sound,[&](const char* name,int64_t cycle,const AirTitleMenu& s){const auto& l=s.page.close.fade.layout;const auto& r=l.reset;const auto& t=r.timing;
            idle.points<<name<<','<<cycle<<','<<s.remaining<<','<<s.waits<<','<<s.index<<','<<t.tick<<','<<t.countdown<<','<<r.stat<<','<<r.lcdc<<','<<r.scrollY<<','<<l.lyc<<','<<t.input.held<<','<<t.input.pressed<<','<<s.route<<','<<s.unlockProgress<<'\n';},
            [&](unsigned index,int64_t cycle,int tick,int countdown,int display,int effects,int music,const DisplayInput& input){idle.service(index,cycle,tick,countdown,display,effects,music,input);airInstructionVoiceRows(idleVoices,index,sound,music);},[&](auto... args){idle.irq(args...);},[&](const char* name,auto... values){idleRaster<<name;((idleRaster<<','<<values),...);idleRaster<<'\n';},[&](auto... args){idle.write(args...);},sample,true,true,&inherited);
        if(actionPage==pass+1){if(menu.route<2||menu.route>4)throw std::runtime_error("Missing later title Start/Select/unlock route");finish(idle,stem+".idle");break;}
        if(menu.route!=1)throw std::runtime_error("Title cycle left the bounded automatic/action page route");finish(idle,stem+".idle");
    }
}
}
