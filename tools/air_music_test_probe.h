#pragma once
#include "air_music_test.h"
#include "air_instruction_voice_probe.h"
namespace ticd {
inline AirMusicTest airProbeMusicTest(const std::string& base,AirPasswordReturn entered,NativeAudio& sound,std::function<int()> sample){
    AirNextInstructionCsv csv(base+".music-test","boundary,cycle,tick,countdown,tune,effect,lastTune,musicEnabled,song,musicActive,pending,held,pressed,day,difficulty,center,windowY,stat,lcdc,scrollY,lyc");
    std::ofstream raster(base+".music-test.raster.csv"),voices(base+".music-test.voices.csv");raster<<"boundary,cycle,stat,lcdc,scrollY,lyc\n";airInstructionVoiceHeader(voices);
    auto result=airMusicTest(entered,sound,
        [&](const char* name,int64_t cycle,const AirMusicTest& s,const NativeAudio& audio){const auto& l=s.screen.feedback.edit.password.menu.page.close.fade.layout;const auto& r=l.reset;const auto& t=r.timing;csv.points<<name<<','<<cycle<<','<<t.tick<<','<<t.countdown<<','<<s.screen.tune<<','<<s.screen.effect<<','<<s.screen.lastTune<<','<<audio.enabled<<','<<audio.song<<','<<(audio.enabled&&audio.musicPlaying())<<','<<audio.pendingEffect<<','<<t.input.held<<','<<t.input.pressed<<','<<s.screen.feedback.startDay<<','<<s.screen.feedback.startDifficulty<<",0,"<<l.windowY<<','<<r.stat<<','<<r.lcdc<<','<<r.scrollY<<','<<l.lyc<<'\n';},
        [&](unsigned index,int64_t cycle,int tick,int countdown,int display,int effects,int music,const DisplayInput& input){csv.service(index,cycle,tick,countdown,display,effects,music,input);airInstructionVoiceRows(voices,index,sound,music);},
        [&](auto... args){csv.irq(args...);},[&](const char* name,auto... values){raster<<name;((raster<<','<<values),...);raster<<'\n';},[&](auto... args){csv.poll(args...);},[&](auto... args){csv.write(args...);},sample);
    const auto& r=result.screen.feedback.edit.password.menu.page.close.fade.layout.reset;const auto& t=r.timing;
    csv.summary<<"end,tick,countdown,displays,stats,lcdEpoch,nextStat,nextVBlank,waits,tune,effect,lastTune,musicEnabled,song,musicActive,pending,plays,effects,stops,exited\n"<<t.end<<','<<t.tick<<','<<t.countdown<<','<<t.displays<<','<<t.stats<<','<<t.lcdEpoch<<','<<t.nextStat<<','<<t.nextVBlank<<','<<result.waits<<','<<result.screen.tune<<','<<result.screen.effect<<','<<result.screen.lastTune<<','<<sound.enabled<<','<<sound.song<<','<<(sound.enabled&&sound.musicPlaying())<<','<<sound.pendingEffect<<','<<result.plays<<','<<result.effects<<','<<result.stops<<','<<result.exited<<'\n';
    std::ofstream maps(base+".music-test.maps.csv"),objects(base+".music-test.objects.csv");maps<<"address,value\n";objects<<"address,value\n";for(int i=0;i<2048;++i)maps<<(0x9800+i)<<','<<int(i<1024?r.background[i]:r.window[i-1024])<<'\n';for(int i=0;i<256;++i)objects<<(0xc100+i)<<','<<int(r.objects[i])<<'\n';return result;
}
}
