#pragma once
#include "air_password_feedback.h"
#include "air_instruction_voice_probe.h"
namespace ticd {
inline AirPasswordFeedback airProbePasswordFeedback(const std::string& base,AirPasswordEdit entered,NativeAudio& sound,const UiAssets& ui,std::function<int()> sample){
    AirNextInstructionCsv csv(base+".password-feedback","boundary,cycle,tick,countdown,center,windowY,candidate,action,remaining,day,difficulty,musicEnabled,held,pressed,stat,lcdc,scrollY,lyc");
    std::ofstream raster(base+".password-feedback.raster.csv"),voices(base+".password-feedback.voices.csv");raster<<"boundary,cycle,stat,lcdc,scrollY,lyc\n";airInstructionVoiceHeader(voices);
    auto result=airPasswordFeedback(entered,sound,ui,1,0,
        [&](const char* name,int64_t cycle,const AirPasswordFeedback& s,bool enabled){const auto& l=s.edit.password.menu.page.close.fade.layout;const auto& r=l.reset;const auto& t=r.timing;
            csv.points<<name<<','<<cycle<<','<<t.tick<<','<<t.countdown<<','<<s.center<<','<<l.windowY<<','<<s.candidate<<','<<s.action<<','<<s.remaining<<','<<s.startDay<<','<<s.startDifficulty<<','<<enabled<<','<<t.input.held<<','<<t.input.pressed<<','<<r.stat<<','<<r.lcdc<<','<<r.scrollY<<','<<l.lyc<<'\n';},
        [&](unsigned index,int64_t cycle,int tick,int countdown,int display,int effects,int music,const DisplayInput& input){csv.service(index,cycle,tick,countdown,display,effects,music,input);airInstructionVoiceRows(voices,index,sound,music);},
        [&](auto... args){csv.irq(args...);},[&](const char* name,auto... values){raster<<name;((raster<<','<<values),...);raster<<'\n';},[&](auto... args){csv.poll(args...);},[&](auto... args){csv.write(args...);},sample);
    const auto& r=result.edit.password.menu.page.close.fade.layout.reset;const auto& t=r.timing;
    csv.summary<<"end,tick,countdown,displays,stats,lcdEpoch,nextStat,nextVBlank,action,day,difficulty,musicTest,musicEnabled,remaining\n"<<t.end<<','<<t.tick<<','<<t.countdown<<','<<t.displays<<','<<t.stats<<','<<t.lcdEpoch<<','<<t.nextStat<<','<<t.nextVBlank<<','<<result.action<<','<<result.startDay<<','<<result.startDifficulty<<','<<result.musicTest<<','<<sound.enabled<<','<<result.remaining<<'\n';
    std::ofstream maps(base+".password-feedback.maps.csv"),objects(base+".password-feedback.objects.csv");maps<<"address,value\n";objects<<"address,value\n";for(int i=0;i<2048;++i)maps<<(0x9800+i)<<','<<int(i<1024?r.background[i]:r.window[i-1024])<<'\n';for(int i=0;i<256;++i)objects<<(0xc100+i)<<','<<int(r.objects[i])<<'\n';return result;
}
}
