#pragma once
#include "air_title_instruction_exit.h"
#include "air_instruction_voice_probe.h"
#include "native_ui_frame_probe.h"
namespace ticd {
inline AirTitleText airProbeTitleInstructionExit(const std::string& base,AirTitleText typed,NativeAudio& sound,const UiAssets& ui,std::function<int()> sample){
    AirNextInstructionCsv out(base+".title-instruction-exit","boundary,cycle,tick,countdown,scroll,bgp,obp0,obp1,musicEnabled,inputHeld,inputPressed");
    std::ofstream voices(base+".title-instruction-exit.voices.csv");airInstructionVoiceHeader(voices);
    auto canvas=typed.text.background;int inputWaits=0;
    auto state=airTitleInstructionExit(typed,sound,ui,
        [&](const char* name,int64_t cycle,int tick,int countdown,int scroll,int bgp,int obp0,int obp1,bool enabled,const DisplayInput& input){out.points<<name<<','<<cycle<<','<<tick<<','<<countdown<<','<<scroll<<','<<bgp<<','<<obp0<<','<<obp1<<','<<enabled<<','<<input.held<<','<<input.pressed<<'\n';
            if(std::string(name)=="inputReady"&&++inputWaits==2){UiFlow frame(ui);frame.phase=UiPhase::Instructions;frame.stunt=1;frame.map=canvas;frame.scroll=scroll;nativeUiFrame(base+".title-instruction-exit.prompt.frame.shades",frame.render());}},
        [&](unsigned index,int64_t cycle,int tick,int countdown,int display,int effects,int music,const DisplayInput& input){out.service(index,cycle,tick,countdown,display,effects,music,input);airInstructionVoiceRows(voices,index,sound,music);},
        [&](auto... args){out.irq(args...);},[&](auto... args){out.poll(args...);},[&](int64_t cycle,int address,int value){if(address>=0x9800&&address<0x9c00)canvas.at(address-0x9800)=static_cast<uint8_t>(value);out.write(cycle,address,value);},sample);
    const auto& t=state.text.map.campaign.timing;
    out.summary<<"end,tick,countdown,scroll,displays,stats,lcdEpoch,nextStat,nextVBlank,musicEnabled,activeVoices\n"<<t.end<<','<<t.tick<<','<<t.countdown<<','<<state.text.map.scroll<<','<<t.displays<<','<<t.stats<<','<<t.lcdEpoch<<','<<t.nextStat<<','<<t.nextVBlank<<','<<sound.enabled<<','<<std::count_if(sound.voices.begin(),sound.voices.end(),[](const MusicVoice& v){return v.active;})<<'\n';
    const auto& r=state.picture.title.fresh.instruction.start.menu.page.close.fade.layout.reset;
    std::ofstream maps(base+".title-instruction-exit.maps.csv");maps<<"address,value\n";for(int i=0;i<2048;++i)maps<<(0x9800+i)<<','<<int(i<1024?r.background[i]:r.window[i-1024])<<'\n';
    std::ofstream tiles(base+".title-instruction-exit.tiles.csv");tiles<<"address,value\n";for(int i=0;i<1024;++i)tiles<<(0x8340+i)<<','<<int(state.picture.tiles[i])<<'\n';return state;
}
}
