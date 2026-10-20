#pragma once
#include "air_password_return.h"
#include "air_instruction_voice_probe.h"
namespace ticd {
inline AirPasswordReturn airProbePasswordReturn(const std::string& base,AirPasswordFeedback entered,NativeAudio& sound,const UiAssets& ui,std::function<int()> sample,bool afterMusicTest=false){
    AirNextInstructionCsv csv(base+".password-return","boundary,cycle,target,tick,countdown,center,windowY,rows,day,difficulty,musicEnabled,song,held,pressed,cursor,digit0,digit1,digit2,digit3,digit4,digit5,digit6,digit7,stat,lcdc,scrollY,lyc");
    std::ofstream raster(base+".password-return.raster.csv"),voices(base+".password-return.voices.csv");raster<<"boundary,cycle,stat,lcdc,scrollY,lyc\n";airInstructionVoiceHeader(voices);
    auto result=airPasswordReturn(entered,sound,ui,
        [&](const char* name,int64_t cycle,const AirPasswordReturn& s,bool enabled,int song){const auto& p=s.feedback.edit.password;const auto& l=p.menu.page.close.fade.layout;const auto& r=l.reset;const auto& t=r.timing;
            csv.points<<name<<','<<cycle<<','<<s.target<<','<<t.tick<<','<<t.countdown<<','<<s.center<<','<<l.windowY<<','<<s.rows<<','<<s.feedback.startDay<<','<<s.feedback.startDifficulty<<','<<enabled<<','<<song<<','<<t.input.held<<','<<t.input.pressed<<','<<p.cursor;for(int value:p.digits)csv.points<<','<<value;csv.points<<','<<r.stat<<','<<r.lcdc<<','<<r.scrollY<<','<<l.lyc<<'\n';},
        [&](unsigned index,int64_t cycle,int tick,int countdown,int display,int effects,int music,const DisplayInput& input){csv.service(index,cycle,tick,countdown,display,effects,music,input);airInstructionVoiceRows(voices,index,sound,music);},
        [&](auto... args){csv.irq(args...);},[&](const char* name,auto... values){raster<<name;((raster<<','<<values),...);raster<<'\n';},[&](auto... args){csv.poll(args...);},[&](auto... args){csv.write(args...);},sample,afterMusicTest);
    const auto& p=result.feedback.edit.password;const auto& r=p.menu.page.close.fade.layout.reset;const auto& t=r.timing;
    csv.summary<<"end,tick,countdown,displays,stats,lcdEpoch,nextStat,nextVBlank,target,center,closed,cleared,opened,rows,day,difficulty,cursor,musicEnabled,song,tune,effect,lastTune\n"<<t.end<<','<<t.tick<<','<<t.countdown<<','<<t.displays<<','<<t.stats<<','<<t.lcdEpoch<<','<<t.nextStat<<','<<t.nextVBlank<<','<<result.target<<','<<result.center<<','<<result.closed<<','<<result.cleared<<','<<result.opened<<','<<result.rows<<','<<result.feedback.startDay<<','<<result.feedback.startDifficulty<<','<<p.cursor<<','<<sound.enabled<<','<<sound.song<<','<<result.tune<<','<<result.effect<<','<<result.lastTune<<'\n';
    std::ofstream maps(base+".password-return.maps.csv"),objects(base+".password-return.objects.csv");maps<<"address,value\n";objects<<"address,value\n";for(int i=0;i<2048;++i)maps<<(0x9800+i)<<','<<int(i<1024?r.background[i]:r.window[i-1024])<<'\n';for(int i=0;i<256;++i)objects<<(0xc100+i)<<','<<int(r.objects[i])<<'\n';return result;
}
}
