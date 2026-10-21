#pragma once
#include "air_next_instruction_probe.h"
#include "air_following_setup.h"
#include "air_title_start.h"
#include "air_title_instruction.h"
#include "air_title_campaign.h"
#include "air_title_resume.h"
#include "air_title_header.h"
#include "air_title_picture_probe.h"
#include "air_title_entrance_probe.h"
#include "air_title_text_probe.h"
#include "air_title_instruction_exit_probe.h"
#include "air_instruction_voice_probe.h"
#include "selected_game_entry_probe.h"
namespace ticd {
inline void airProbeTitleStart(const std::string& base,AirTitleMenu waited,const AirFollowingSetup& state,const AirGame& game,int resultLives,
    NativeAudio& sound,const UiAssets& ui,std::function<int()> sample,bool titleInstruction=false,bool titleCampaign=false,bool titleResume=false,bool titleHeader=false,bool titlePicture=false,bool titleEntrance=false,bool titleText=false,bool titleInstructionExit=false,bool selectedEntry=false,bool selectedPlay=false,int selectedUpdates=32,bool selectedTerminal=false){
    AirNextInstructionCsv out(base+".title-start","boundary,cycle,palettes,waits,tick,countdown,stat,lcdc,scrollY,lyc,bgp,obp0,obp1,musicEnabled,inputHeld,inputPressed");
    std::ofstream raster(base+".title-start.raster.csv");raster<<"boundary,cycle,stat,lcdc,scrollY,lyc\n";
    std::ofstream voices(base+".title-start.voices.csv");airInstructionVoiceHeader(voices);
    auto started=airTitleStart(waited,sound,ui,
        [&](const char* name,int64_t cycle,const AirTitleStart& s,bool enabled){const auto& f=s.menu.page.close.fade;const auto& r=f.layout.reset;const auto& t=r.timing;
            out.points<<name<<','<<cycle<<','<<s.palettes<<','<<s.waits<<','<<t.tick<<','<<t.countdown<<','<<r.stat<<','<<r.lcdc<<','<<r.scrollY<<','<<f.layout.lyc<<','<<f.bgp<<','<<f.obp0<<','<<f.obp1<<','<<enabled<<','<<t.input.held<<','<<t.input.pressed<<'\n';},
        [&](unsigned index,int64_t cycle,int tick,int countdown,int display,int effects,int music,const DisplayInput& input){out.service(index,cycle,tick,countdown,display,effects,music,input);airInstructionVoiceRows(voices,index,sound,music);},[&](auto... args){out.irq(args...);},
        [&](const char* name,auto... values){raster<<name;((raster<<','<<values),...);raster<<'\n';},[&](auto... args){out.write(args...);},sample);
    const auto& t=started.menu.page.close.fade.layout.reset.timing;
    out.summary<<"end,lcdEpoch,tick,countdown,displays,stats,nextStat,nextVBlank,musicEnabled\n"<<t.end<<','<<t.lcdEpoch<<','<<t.tick<<','<<t.countdown<<','<<t.displays<<','<<t.stats<<','<<t.nextStat<<','<<t.nextVBlank<<','<<sound.enabled<<'\n';
    std::ofstream maps(base+".title-start.maps.csv");maps<<"address,value\n";const auto& r=started.menu.page.close.fade.layout.reset;
    for(int i=0;i<2048;++i)maps<<(0x9800+i)<<','<<int(i<1024?r.background[i]:r.window[i-1024])<<'\n';
    if(titleInstruction){
        AirNextInstructionCsv out(base+".title-instruction","boundary,cycle,tick,countdown,inputHeld,inputPressed,display,stat,lcdc,scrollY,lyc","cycle,address,value","ly");
        auto prepared=airTitleInstruction(started,sound,
            [&](const char* name,int64_t cycle,const AirTitleInstruction& s){const auto& l=s.start.menu.page.close.fade.layout;const auto& r=l.reset;const auto& t=r.timing;
                out.points<<name<<','<<cycle<<','<<t.tick<<','<<t.countdown<<','<<t.input.held<<','<<t.input.pressed<<','<<r.display<<','<<r.stat<<','<<r.lcdc<<','<<r.scrollY<<','<<l.lyc<<'\n';},
            [&](auto... args){out.poll(args...);},[&](auto... args){out.write(args...);});
        const auto& r=prepared.start.menu.page.close.fade.layout.reset;
        out.summary<<"end,lcdDisabled,polls,pendingRequests,servicesMasked\n"<<r.timing.end<<','<<prepared.lcdDisabled<<','<<prepared.polls<<','<<r.pendingRequests<<','<<r.servicesMasked<<'\n';
        if(titleCampaign){
            // This diagnostic began with native Air (day index one) password selection,
            // and only failed retries. Stage/difficulty remain retained; a
            // qualified player-selection continuation may change player count.
            if(state.stage!=1||state.difficulty!=0||state.instruction.map.campaign.player||state.instruction.map.campaign.lives[1]||resultLives)throw std::runtime_error("Unowned retained title choices");
            Campaign previous;for(auto& p:previous.players){p.day=state.stage;p.difficulty=state.difficulty;}
            AirTitleChoices choices{state.stage,state.difficulty,waited.playerChoice!=0};
            AirNextInstructionCsv out(base+".title-campaign","boundary,cycle,tick,countdown,inputHeld,inputPressed,day0,day1,difficulty0,difficulty1,lives0,lives1,lcdc,pendingRequests","cycle,address,value","mode");
            auto fresh=airTitleCampaign(prepared,previous,choices,sound,
                [&](const char* name,int64_t cycle,const AirTitleCampaign& s){const auto& t=s.instruction.start.menu.page.close.fade.layout.reset.timing;const auto& p=s.campaign.players;
                    out.points<<name<<','<<cycle<<','<<t.tick<<','<<t.countdown<<','<<t.input.held<<','<<t.input.pressed<<','<<p[0].day<<','<<p[1].day<<','<<p[0].difficulty<<','<<p[1].difficulty<<','<<p[0].lives<<','<<p[1].lives<<','<<s.instruction.start.menu.page.close.fade.layout.reset.lcdc<<','<<s.instruction.start.menu.page.close.fade.layout.reset.pendingRequests<<'\n';},
                [&](auto... args){out.poll(args...);},[&](auto... args){out.write(args...);});
            const auto& r=fresh.instruction.start.menu.page.close.fade.layout.reset;const auto& t=r.timing;
            out.summary<<"end,lcdEpoch,nextStat,nextVBlank,pendingRequests,servicesMasked,active,player\n"<<t.end<<','<<t.lcdEpoch<<','<<t.nextStat<<','<<t.nextVBlank<<','<<r.pendingRequests<<','<<r.servicesMasked<<','<<fresh.campaign.active<<','<<fresh.campaign.current<<'\n';
            std::ofstream maps(base+".title-campaign.maps.csv");maps<<"address,value\n";
            for(int i=0;i<2048;++i)maps<<(0x9800+i)<<','<<int(i<1024?r.background[i]:r.window[i-1024])<<'\n';
            if(titleResume){
                AirNextInstructionCsv resume(base+".title-resume","boundary,cycle,tick,countdown,inputHeld,inputPressed,lcdc,scrollY,display,stat,pendingRequests,lives,result");
                auto resumed=airTitleResume(fresh,game.result,sound,
                    [&](const char* name,int64_t cycle,const AirTitleResume& s){const auto& r=s.fresh.instruction.start.menu.page.close.fade.layout.reset;const auto& t=r.timing;
                        resume.points<<name<<','<<cycle<<','<<t.tick<<','<<t.countdown<<','<<t.input.held<<','<<t.input.pressed<<','<<r.lcdc<<','<<r.scrollY<<','<<r.display<<','<<r.stat<<','<<r.pendingRequests<<','<<s.fresh.campaign.players[0].lives<<','<<s.result<<'\n';},
                    [&](auto... args){resume.service(args...);},[&](auto... args){resume.irq(args...);},[&](auto... args){resume.poll(args...);},[&](auto... args){resume.write(args...);},sample);
                const auto& r=resumed.fresh.instruction.start.menu.page.close.fade.layout.reset;const auto& t=r.timing;
                resume.summary<<"end,lcdEpoch,nextStat,nextVBlank,displays,stats,pendingRequests,servicesMasked,result\n"<<t.end<<','<<t.lcdEpoch<<','<<t.nextStat<<','<<t.nextVBlank<<','<<t.displays<<','<<t.stats<<','<<r.pendingRequests<<','<<r.servicesMasked<<','<<resumed.result<<'\n';
                std::ofstream maps(base+".title-resume.maps.csv");maps<<"address,value\n";
                for(int i=0;i<2048;++i)maps<<(0x9800+i)<<','<<int(i<1024?r.background[i]:r.window[i-1024])<<'\n';
                if(titleHeader){
                    const auto assets=AirInstructionHeaderAssets::load("build/instruction-header.dat");
                    AirNextInstructionCsv header(base+".title-header","boundary,cycle,tick,countdown,player,stage,difficulty,lives,display,stat,result,musicEnabled,inputHeld,inputPressed,lcdc,scrollY,pendingRequests");
                    auto headed=airTitleHeader(resumed,sound,assets,
                        [&](const char* name,int64_t cycle,const AirTitleResume& s){const auto& r=s.fresh.instruction.start.menu.page.close.fade.layout.reset;const auto& t=r.timing;const auto& c=s.fresh.campaign;const auto& p=c.players[c.current];
                            header.points<<name<<','<<cycle<<','<<t.tick<<','<<t.countdown<<','<<c.current<<','<<p.day<<','<<p.difficulty<<','<<p.lives<<','<<r.display<<','<<r.stat<<','<<s.result<<','<<sound.enabled<<','<<t.input.held<<','<<t.input.pressed<<','<<r.lcdc<<','<<r.scrollY<<','<<r.pendingRequests<<'\n';},
                        [&](auto... args){header.service(args...);},[&](auto... args){header.irq(args...);},[&](auto... args){header.poll(args...);},[&](auto... args){header.write(args...);},sample);
                    const auto& r=headed.fresh.instruction.start.menu.page.close.fade.layout.reset;const auto& t=r.timing;
                    header.summary<<"end,tick,countdown,displays,lcdEpoch,nextStat,nextVBlank,stats,pendingRequests,servicesMasked,result\n"<<t.end<<','<<t.tick<<','<<t.countdown<<','<<t.displays<<','<<t.lcdEpoch<<','<<t.nextStat<<','<<t.nextVBlank<<','<<t.stats<<','<<r.pendingRequests<<','<<r.servicesMasked<<','<<headed.result<<'\n';
                    std::ofstream maps(base+".title-header.maps.csv");maps<<"address,value\n";
                    for(int i=0;i<2048;++i)maps<<(0x9800+i)<<','<<int(i<1024?r.background[i]:r.window[i-1024])<<'\n';
                    if(titlePicture){auto pictured=airProbeTitlePicture(base,headed,sound,ui,sample);
                        if(titleEntrance){auto entered=airProbeTitleEntrance(base,pictured,sound,ui,sample);
                            if(titleText){auto typed=airProbeTitleText(base,entered,sound,ui,sample);
                                if(titleInstructionExit){auto exited=airProbeTitleInstructionExit(base,typed,sound,ui,sample);if(selectedEntry)airProbeSelectedGameEntry(base,exited.text,sound,sample,&game,selectedPlay,selectedUpdates,selectedTerminal);}}}}
                }
            }
        }
    }

}
}
