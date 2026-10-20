#pragma once
#include "air_password_edit.h"
#include "air_instruction_voice_probe.h"
namespace ticd {
inline AirPasswordEdit airProbePasswordEdit(const std::string& base,AirTitlePassword entered,NativeAudio& sound,std::function<int()> sample){
    AirNextInstructionCsv csv(base+".password-edit","boundary,cycle,tick,countdown,cursor,submit,held,pressed,digit0,digit1,digit2,digit3,digit4,digit5,digit6,digit7");
    std::ofstream raster(base+".password-edit.raster.csv"),voices(base+".password-edit.voices.csv");raster<<"boundary,cycle,stat,lcdc,scrollY,lyc\n";airInstructionVoiceHeader(voices);
    auto result=airPasswordEdit(entered,sound,
        [&](const char* name,int64_t cycle,const AirPasswordEdit& s){const auto& t=s.password.menu.page.close.fade.layout.reset.timing;csv.points<<name<<','<<cycle<<','<<t.tick<<','<<t.countdown<<','<<s.password.cursor<<','<<(std::string(name)=="end"?s.submit:0)<<','<<t.input.held<<','<<t.input.pressed;for(int value:s.password.digits)csv.points<<','<<value;csv.points<<'\n';},
        [&](unsigned index,int64_t cycle,int tick,int countdown,int display,int effects,int music,const DisplayInput& input){csv.service(index,cycle,tick,countdown,display,effects,music,input);airInstructionVoiceRows(voices,index,sound,music);},
        [&](auto... args){csv.irq(args...);},[&](const char* name,auto... values){raster<<name;((raster<<','<<values),...);raster<<'\n';},[&](auto... args){csv.poll(args...);},[&](auto... args){csv.write(args...);},sample);
    const auto& r=result.password.menu.page.close.fade.layout.reset;const auto& t=r.timing;
    csv.summary<<"end,tick,countdown,displays,stats,lcdEpoch,nextStat,nextVBlank,cursor,submit,waits\n"<<t.end<<','<<t.tick<<','<<t.countdown<<','<<t.displays<<','<<t.stats<<','<<t.lcdEpoch<<','<<t.nextStat<<','<<t.nextVBlank<<','<<result.password.cursor<<','<<result.submit<<','<<result.waits<<'\n';
    std::ofstream maps(base+".password-edit.maps.csv"),objects(base+".password-edit.objects.csv");maps<<"address,value\n";objects<<"address,value\n";
    for(int i=0;i<2048;++i)maps<<(0x9800+i)<<','<<int(i<1024?r.background[i]:r.window[i-1024])<<'\n';for(int i=0;i<256;++i)objects<<(0xc100+i)<<','<<int(r.objects[i])<<'\n';return result;
}
}
