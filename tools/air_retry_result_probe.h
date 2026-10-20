#pragma once
#include "air_next_instruction_probe.h"
#include "air_following_setup.h"
#include "air_result_accounting.h"
#include "air_final_result.h"
#include "air_game_over_return.h"
#include "air_title_reset.h"
#include "air_title_layout.h"
#include "air_title_fade.h"
#include "air_title_close.h"
#include "air_title_page.h"
#include "air_title_menu.h"
#include "air_title_start.h"
#include "air_title_password_probe.h"
#include "air_title_instruction.h"
#include "air_title_campaign.h"
#include "air_title_resume.h"
#include "air_title_header.h"
#include "air_title_picture_probe.h"
#include "air_title_entrance_probe.h"
#include "air_title_text_probe.h"
#include "air_title_instruction_exit_probe.h"

namespace ticd {
// Adapter around the existing native result owners. The current stunt's LCD,
// campaign, input and random state are the only continuation state supplied.
inline AirResultPrefix airProbeRetryPrefix(const std::string& base,const AirFollowingSetup& state,const AirGame& game){
    const auto& c=state.instruction.map.campaign;const auto& end=c.timing;
    int player=c.player,lives=c.lives.at(player);
    AirClock clock;clock.now=end.end;clock.nextStat=end.nextStat;clock.nextVBlank=end.nextVBlank;
    AirNextInstructionCsv prefix(base+".next-result","boundary,cycle","cycle,address,value","ly");
    auto prepared=airResultSetupPrefix(clock,game.result,
        [&](const char* name,int64_t cycle){prefix.points<<name<<','<<cycle<<'\n';},
        [&](auto... args){prefix.poll(args...);},game.randomState,end.lcdEpoch);
    prefix.summary<<"end,lcdDisabled,pollReads,pendingRequests,display,stat,countdown,random,tick,player,lives,inputHeld,inputPressed\n"<<prepared.end<<','<<prepared.lcdDisabled<<','<<prepared.pollReads<<','<<prepared.pendingRequests<<','<<prepared.display<<','<<prepared.stat<<','<<prepared.countdown<<','<<prepared.celebration.randomState<<','<<end.tick<<','<<player<<','<<lives<<','<<end.input.held<<','<<end.input.pressed<<'\n';
    return prepared;
}
inline AirResultTransition airProbeRetryResult(const std::string& base,const AirFollowingSetup& state,
    const AirGame& game,NativeAudio& sound,const UiAssets& ui,std::function<int()> sample){
    const auto& c=state.instruction.map.campaign;const auto& end=c.timing;
    int player=c.player,lives=c.lives.at(player);
    if((game.result&6)||!(game.result&1)||lives<=1||sound.enabled)
        throw std::runtime_error("Subsequent result requires its non-final failure owner");
    auto prepared=airProbeRetryPrefix(base,state,game);
    auto layouts=AirResultLayoutAssets::load("build/result-timing.dat");
    AirNextInstructionCsv incoming(base+".next-incoming","boundary,cycle,tick,countdown,bgp,obp0,obp1,musicEnabled,inputHeld,inputPressed",
        "cycle,address,value","mode","service,cycle,tick,countdown,display,effects,music,musicEnabled,inputHeld,inputPressed");
    DisplayInput input=end.input;
    auto read=[&]{int raw=sample?sample():input.held;input.sample(raw);return raw;};
    auto point=[&](const char* name,int64_t cycle,int tick,int countdown,int bgp,int obp0,int obp1,bool enabled){incoming.points<<name<<','<<cycle<<','<<tick<<','<<countdown<<','<<bgp<<','<<obp0<<','<<obp1<<','<<enabled<<','<<input.held<<','<<input.pressed<<'\n';};
    auto service=[&](unsigned index,int64_t cycle,int tick,int countdown,int display,int effects,int music,bool enabled){incoming.services<<index<<','<<cycle<<','<<tick<<','<<countdown<<','<<display<<','<<effects<<','<<music<<','<<enabled<<','<<input.held<<','<<input.pressed<<'\n';};
    auto irq=[&](auto... args){incoming.irq(args...);};
    auto result=airResultIncoming(prepared,game.result,end.tick,lives,end.input.held,sound,layouts,ui,point,service,irq,read);
    result=airResultFailureHold(result,game.result,result.input.held,sound,ui,point,service,irq,read);
    incoming.summary<<"end,lcdEpoch,tick,countdown,displays,stats,nextStat,nextVBlank,player,lives\n"<<result.end<<','<<result.lcdEpoch<<','<<result.tick<<','<<result.countdown<<','<<result.displays<<','<<result.stats<<','<<result.nextStat<<','<<result.nextVBlank<<','<<player<<','<<result.lives<<'\n';
    return result;
}
inline AirResultTransition airProbeFinalResult(const std::string& base,const AirFollowingSetup& state,
    const AirGame& game,NativeAudio& sound,const UiAssets& ui,std::function<int()> sample,bool titleReturn=false,bool titleReset=false,bool titleLayout=false,bool titleFade=false,bool titleClose=false,bool titlePage=false,bool titleMenu=false,bool titleActions=false,bool titleStart=false,bool titleInstruction=false,bool titleCampaign=false,bool titleResume=false,bool titleHeader=false,bool titlePicture=false,bool titleUnlock=false,bool titleEntrance=false,bool titleText=false,bool titleInstructionExit=false,bool titlePassword=false){
    const auto& c=state.instruction.map.campaign;const auto& end=c.timing;
    int player=c.player,lives=c.lives.at(player);
    if(game.result!=33||lives!=1||sound.enabled)throw std::runtime_error("Final result requires actual final Air failure ownership");
    auto prepared=airProbeRetryPrefix(base,state,game);
    auto layouts=AirResultLayoutAssets::load("build/result-timing.dat");auto texts=AirResultTextAssets::load("build/result-layouts.dat");
    AirNextInstructionCsv out(base+".final-result","boundary,cycle,tick,countdown,bgp,obp0,obp1,musicEnabled,lives,savings,inputHeld,inputPressed",
        "cycle,address,value","mode","service,cycle,tick,countdown,display,effects,music,musicEnabled,inputHeld,inputPressed");
    DisplayInput input=end.input;
    auto read=[&]{int raw=sample?sample():input.held;input.sample(raw);return raw;};
    auto point=[&](const char* name,int64_t cycle,int tick,int countdown,int bgp,int obp0,int obp1,bool enabled,int lives,int savings){
        out.points<<name<<','<<cycle<<','<<tick<<','<<countdown<<','<<bgp<<','<<obp0<<','<<obp1<<','<<enabled<<','<<lives<<','<<savings<<','<<input.held<<','<<input.pressed<<'\n';};
    auto service=[&](unsigned index,int64_t cycle,int tick,int countdown,int display,int effects,int music,bool enabled){
        out.services<<index<<','<<cycle<<','<<tick<<','<<countdown<<','<<display<<','<<effects<<','<<music<<','<<enabled<<','<<input.held<<','<<input.pressed<<'\n';};
    // This diagnostic's five attempts all failed: native campaign savings
    // start at zero and no successful payout owner has run along this route.
    constexpr int failedCampaignSavings=0;
    auto result=airFinalResult(prepared,game.result,end.tick,lives,end.input.held,failedCampaignSavings,sound,layouts,texts,ui,
        point,service,[&](auto... args){out.irq(args...);},[&](auto... args){out.poll(args...);},[&](auto... args){out.write(args...);},read);
    out.summary<<"end,lcdEpoch,tick,countdown,displays,stats,nextStat,nextVBlank,player,lives,savings\n"<<result.end<<','<<result.lcdEpoch<<','<<result.tick<<','<<result.countdown<<','<<result.displays<<','<<result.stats<<','<<result.nextStat<<','<<result.nextVBlank<<','<<player<<','<<result.lives<<','<<failedCampaignSavings<<'\n';
    if(titleReturn){
        AirNextInstructionCsv returned(base+".game-over-return","boundary,cycle,tick,countdown,row,byte,amount,target,carry,bgp,obp0,obp1,musicEnabled");
        auto remaining=c.lives;remaining[player]=result.lives;
        result=airGameOverReturn(result,failedCampaignSavings,remaining,ui.initialScores,sound,ui,
            [&](const char* name,auto... values){returned.points<<name;((returned.points<<','<<values),...);returned.points<<'\n';},
            [&](unsigned index,int64_t cycle,int tick,int countdown,int display,int effects,int music,const DisplayInput& input){returned.service(index,cycle,tick,countdown,display,effects,music,input);},
            [&](auto... args){returned.irq(args...);},sample);
        returned.summary<<"end,lcdEpoch,tick,countdown,displays,stats,nextStat,nextVBlank,lives0,lives1,savings\n"<<result.end<<','<<result.lcdEpoch<<','<<result.tick<<','<<result.countdown<<','<<result.displays<<','<<result.stats<<','<<result.nextStat<<','<<result.nextVBlank<<",0,0,"<<failedCampaignSavings<<'\n';
    }
    if(titleReset){
        if(!titleReturn)throw std::runtime_error("Title reset requires full game-over return");
        AirNextInstructionCsv reset(base+".title-reset","boundary,cycle,tick,countdown,inputHeld,inputPressed,lcdc,bank","cycle,address,value","ly");
        auto prepared=airTitleResetPrefix(result,sound,
            [&](const char* name,int64_t cycle,const AirTitleReset& r){reset.points<<name<<','<<cycle<<','<<r.timing.tick<<','<<r.timing.countdown<<','<<r.timing.input.held<<','<<r.timing.input.pressed<<','<<r.lcdc<<','<<r.bank<<'\n';},
            [&](auto... args){reset.poll(args...);},[&](auto... args){reset.write(args...);});
        reset.summary<<"end,lcdEpoch,lcdDisabled,pollReads,pendingRequests,tick,countdown,displays,stats,display,stat,servicesMasked\n"<<prepared.timing.end<<','<<prepared.timing.lcdEpoch<<','<<prepared.lcdDisabled<<','<<prepared.pollReads<<','<<prepared.pendingRequests<<','<<prepared.timing.tick<<','<<prepared.timing.countdown<<','<<prepared.timing.displays<<','<<prepared.timing.stats<<','<<prepared.display<<','<<prepared.stat<<','<<prepared.servicesMasked<<'\n';
        if(titleLayout){
            AirNextInstructionCsv layout(base+".title-layout","boundary,cycle,command,row,tick,countdown,inputHeld,inputPressed,lcdc,bank,display,stat");
            const auto assets=AirTitleLayoutAssets::load("build/title-layout.dat");
            // This actual completed campaign is downstream of the one-time
            // boot screen. No observed C005 byte is supplied to native code.
            auto titled=airTitleLayout(prepared,true,sound,assets,
                [&](const char* name,int64_t cycle,int command,int row,const AirTitleLayout& s){const auto& r=s.reset;const auto& t=r.timing;
                    layout.points<<name<<','<<cycle<<','<<command<<','<<row<<','<<t.tick<<','<<t.countdown<<','<<t.input.held<<','<<t.input.pressed<<','<<r.lcdc<<','<<r.bank<<','<<r.display<<','<<r.stat<<'\n';},
                [&](auto... args){layout.write(args...);});
            const auto& t=titled.reset.timing;
            layout.summary<<"end,lcdEpoch,tick,countdown,displays,stats,nextStat,nextVBlank,display,stat,lyc,windowX,windowY,servicesMasked\n"<<t.end<<','<<t.lcdEpoch<<','<<t.tick<<','<<t.countdown<<','<<t.displays<<','<<t.stats<<','<<t.nextStat<<','<<t.nextVBlank<<','<<titled.reset.display<<','<<titled.reset.stat<<','<<titled.lyc<<','<<titled.windowX<<','<<titled.windowY<<','<<titled.reset.servicesMasked<<'\n';
            std::ofstream maps(base+".title-layout.maps.csv");maps<<"address,value\n";
            for(int i=0;i<2048;++i)maps<<(0x9800+i)<<','<<int(i<1024?titled.reset.background[i]:titled.reset.window[i-1024])<<'\n';
            if(titleFade){
                AirNextInstructionCsv fade(base+".title-fade","boundary,cycle,tick,countdown,lcdc,stat,lyc,scrollY,bgp,obp0,obp1,inputHeld,inputPressed");
                std::ofstream raster(base+".title-fade.raster.csv");raster<<"boundary,cycle,stat,lcdc,scrollY,lyc\n";
                auto faded=airTitleFade(titled,sound,ui,
                    [&](const char* name,int64_t cycle,int tick,int countdown,const AirTitleFade& s){const auto& r=s.layout.reset;fade.points<<name<<','<<cycle<<','<<tick<<','<<countdown<<','<<r.lcdc<<','<<r.stat<<','<<s.layout.lyc<<','<<r.scrollY<<','<<s.bgp<<','<<s.obp0<<','<<s.obp1<<','<<r.timing.input.held<<','<<r.timing.input.pressed<<'\n';},
                    [&](auto... args){fade.service(args...);},[&](auto... args){fade.irq(args...);},
                    [&](const char* name,auto... values){raster<<name;((raster<<','<<values),...);raster<<'\n';},
                    [&](auto... args){fade.write(args...);},sample);
                const auto& f=faded.layout.reset.timing;
                fade.summary<<"end,lcdEpoch,tick,countdown,displays,stats,nextStat,nextVBlank,servicesMasked,pendingRequests\n"<<f.end<<','<<f.lcdEpoch<<','<<f.tick<<','<<f.countdown<<','<<f.displays<<','<<f.stats<<','<<f.nextStat<<','<<f.nextVBlank<<','<<faded.layout.reset.servicesMasked<<','<<faded.layout.reset.pendingRequests<<'\n';
                if(titleClose){
                    AirNextInstructionCsv close(base+".title-close","boundary,cycle,center,steps,windowY,tick,countdown,stat,lcdc,scrollY,lyc,song,inputHeld,inputPressed");
                    std::ofstream raster(base+".title-close.raster.csv");raster<<"boundary,cycle,stat,lcdc,scrollY,lyc\n";
                    auto closed=airTitleClose(faded,sound,
                        [&](const char* name,int64_t cycle,const AirTitleClose& s,int song){const auto& r=s.fade.layout.reset;const auto& t=r.timing;
                            close.points<<name<<','<<cycle<<','<<s.center<<','<<s.steps<<','<<s.fade.layout.windowY<<','<<t.tick<<','<<t.countdown<<','<<r.stat<<','<<r.lcdc<<','<<r.scrollY<<','<<s.fade.layout.lyc<<','<<song<<','<<t.input.held<<','<<t.input.pressed<<'\n';},
                        [&](auto... args){close.service(args...);},[&](auto... args){close.irq(args...);},
                        [&](const char* name,auto... values){raster<<name;((raster<<','<<values),...);raster<<'\n';},[&](auto... args){close.write(args...);},sample);
                    const auto& c=closed.fade.layout.reset.timing;
                    close.summary<<"end,lcdEpoch,tick,countdown,displays,stats,nextStat,nextVBlank,center,steps,windowY,song\n"<<c.end<<','<<c.lcdEpoch<<','<<c.tick<<','<<c.countdown<<','<<c.displays<<','<<c.stats<<','<<c.nextStat<<','<<c.nextVBlank<<','<<closed.center<<','<<closed.steps<<','<<closed.fade.layout.windowY<<','<<sound.song<<'\n';
                    if(titlePage){
                        AirNextInstructionCsv page(base+".title-page","boundary,cycle,cleared,rows,opened,center,windowY,tick,countdown,stat,lcdc,scrollY,lyc,inputHeld,inputPressed","cycle,address,value","mode");
                        std::ofstream raster(base+".title-page.raster.csv");raster<<"boundary,cycle,stat,lcdc,scrollY,lyc\n";
                        auto installed=airTitlePage(closed,sound,ui,
                            [&](const char* name,int64_t cycle,const AirTitlePage& s){const auto& l=s.close.fade.layout;const auto& r=l.reset;const auto& t=r.timing;
                                page.points<<name<<','<<cycle<<','<<s.cleared<<','<<s.rows<<','<<s.opened<<','<<s.close.center<<','<<l.windowY<<','<<t.tick<<','<<t.countdown<<','<<r.stat<<','<<r.lcdc<<','<<r.scrollY<<','<<l.lyc<<','<<t.input.held<<','<<t.input.pressed<<'\n';},
                            [&](auto... args){page.service(args...);},[&](auto... args){page.irq(args...);},
                            [&](const char* name,auto... values){raster<<name;((raster<<','<<values),...);raster<<'\n';},[&](auto... args){page.poll(args...);},[&](auto... args){page.write(args...);},sample);
                        const auto& p=installed.close.fade.layout.reset.timing;
                        page.summary<<"end,lcdEpoch,tick,countdown,displays,stats,nextStat,nextVBlank,center,cleared,rows,opened,windowY,song\n"<<p.end<<','<<p.lcdEpoch<<','<<p.tick<<','<<p.countdown<<','<<p.displays<<','<<p.stats<<','<<p.nextStat<<','<<p.nextVBlank<<','<<installed.close.center<<','<<installed.cleared<<','<<installed.rows<<','<<installed.opened<<','<<installed.close.fade.layout.windowY<<','<<sound.song<<'\n';
                        std::ofstream maps(base+".title-page.maps.csv");maps<<"address,value\n";const auto& r=installed.close.fade.layout.reset;
                        for(int i=0;i<2048;++i)maps<<(0x9800+i)<<','<<int(i<1024?r.background[i]:r.window[i-1024])<<'\n';
                        if(titleMenu){
                            std::string menuBase=base+(titleUnlock?".title-unlock":titleActions?".title-actions":".title-menu");
                            AirNextInstructionCsv menu(menuBase,std::string("boundary,cycle,remaining,waits,index,tick,countdown,stat,lcdc,scrollY,lyc,inputHeld,inputPressed")+(titleActions?",route":"")+(titleUnlock?",pattern":""));
                            std::ofstream raster(menuBase+".raster.csv");raster<<"boundary,cycle,stat,lcdc,scrollY,lyc\n";
                            auto waited=airTitleMenuIdle(installed,sound,
                                [&](const char* name,int64_t cycle,const AirTitleMenu& s){const auto& l=s.page.close.fade.layout;const auto& r=l.reset;const auto& t=r.timing;
                                    menu.points<<name<<','<<cycle<<','<<s.remaining<<','<<s.waits<<','<<s.index<<','<<t.tick<<','<<t.countdown<<','<<r.stat<<','<<r.lcdc<<','<<r.scrollY<<','<<l.lyc<<','<<t.input.held<<','<<t.input.pressed;if(titleActions)menu.points<<','<<s.route;if(titleUnlock)menu.points<<','<<s.unlockProgress;menu.points<<'\n';},
                                [&](auto... args){menu.service(args...);},[&](auto... args){menu.irq(args...);},
                                [&](const char* name,auto... values){raster<<name;((raster<<','<<values),...);raster<<'\n';},[&](auto... args){menu.write(args...);},sample,titleActions,titleUnlock);
                            const auto& t=waited.page.close.fade.layout.reset.timing;
                            menu.summary<<"end,lcdEpoch,tick,countdown,displays,stats,nextStat,nextVBlank,remaining,waits,index,song\n"<<t.end<<','<<t.lcdEpoch<<','<<t.tick<<','<<t.countdown<<','<<t.displays<<','<<t.stats<<','<<t.nextStat<<','<<t.nextVBlank<<','<<waited.remaining<<','<<waited.waits<<','<<waited.index<<','<<sound.song<<'\n';
                            std::ofstream maps(menuBase+".maps.csv");maps<<"address,value\n";const auto& storage=waited.page.close.fade.layout.reset;
                            for(int i=0;i<2048;++i)maps<<(0x9800+i)<<','<<int(i<1024?storage.background[i]:storage.window[i-1024])<<'\n';
                            if(titlePassword)airProbeTitlePassword(base,waited,sound,ui,sample);
                            if(titleStart){
                                AirNextInstructionCsv out(base+".title-start","boundary,cycle,palettes,waits,tick,countdown,stat,lcdc,scrollY,lyc,bgp,obp0,obp1,musicEnabled,inputHeld,inputPressed");
                                std::ofstream raster(base+".title-start.raster.csv");raster<<"boundary,cycle,stat,lcdc,scrollY,lyc\n";
                                auto started=airTitleStart(waited,sound,ui,
                                    [&](const char* name,int64_t cycle,const AirTitleStart& s,bool enabled){const auto& f=s.menu.page.close.fade;const auto& r=f.layout.reset;const auto& t=r.timing;
                                        out.points<<name<<','<<cycle<<','<<s.palettes<<','<<s.waits<<','<<t.tick<<','<<t.countdown<<','<<r.stat<<','<<r.lcdc<<','<<r.scrollY<<','<<f.layout.lyc<<','<<f.bgp<<','<<f.obp0<<','<<f.obp1<<','<<enabled<<','<<t.input.held<<','<<t.input.pressed<<'\n';},
                                    [&](auto... args){out.service(args...);},[&](auto... args){out.irq(args...);},
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
                                        // one player, and only failed retries. No successful settlement or
                                        // title-selection change has altered those retained session choices.
                                        if(state.stage!=1||state.difficulty!=0||state.instruction.map.campaign.player||state.instruction.map.campaign.lives[1]||result.lives)throw std::runtime_error("Unowned retained title choices");
                                        Campaign previous;for(auto& p:previous.players){p.day=state.stage;p.difficulty=state.difficulty;}
                                        AirTitleChoices choices{state.stage,state.difficulty,false};
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
                                                            if(titleInstructionExit)airProbeTitleInstructionExit(base,typed,sound,ui,sample);}}}
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    return result;
}
}
