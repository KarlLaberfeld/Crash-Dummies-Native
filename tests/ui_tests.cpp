#include "ui.h"
#include <cstdio>
#include <memory>
#include <stdexcept>
namespace ticd {
int runUiTests(const UiAssets& assets){
    FILE* log=fopen("ui-test.txt","w");if(!log)return 2;int count=0;
    auto require=[&](bool condition,const char* message){++count;if(!condition)throw std::runtime_error(message);};
    try{
        UiFlow u(assets);u.step(UiSelect);require(u.page==5,"Select opens original options");
        u.step(UiSelect);require(!u.twoPlayers,"Holding Select does not toggle repeatedly");
        u.step(0);u.step(Down);require(u.twoPlayers,"Down selects two players");
        u.step(UiStart);require(u.phase==UiPhase::Instructions&&u.campaign.players[1].lives==5,"Start opens first player's instructions");
        u.step(UiStart);require(u.phase==UiPhase::Instructions,"Held Start cannot skip a second screen");
        u.step(0);u.step(UiStart);require(u.phase==UiPhase::Playing,"Fresh Start skips instruction typing");
        u.finishStunt(3,25,10);require(u.campaign.players[0].savings==35&&u.phase==UiPhase::Result,"Gameplay result settles once and opens results");
        u.step(0);u.step(A);require(u.campaign.current==1&&u.stunt==0&&u.phase==UiPhase::Instructions,"Result passes to independent second player");
        require(u.map[7]==30&&u.map[8]==33&&u.map[9]==25,"Second player's header says TWO");
        for(int player=0;player<2;++player)for(int day=0;day<5;++day)for(int difficulty=0;difficulty<4;++difficulty){
            UiFlow v(assets);v.campaign.start(true,day,difficulty);v.campaign.current=player;v.beginInstructions();
            for(int i=0;i<2500&&!v.textDone;++i)v.step(0);
            require(v.textDone,"Every original instruction script terminates");
            require(v.scroll>0&&v.scroll%8==0,"Instructions finish on a whole text row after original scrolling");
            int prompt=v.position-20;require(v.map[prompt]==26&&v.map[prompt+19]==44,"Original start prompt is appended after typing");
            require(v.map[17*32]==29&&v.map[17*32+1]==(player?26:22),"Player-name macro resolves SLICK or SPIN");
            auto screen=v.render();for(int shade:screen)if(shade>3)throw std::runtime_error("Invalid instruction shade");
        }
        UiFlow solo(assets);solo.step(UiStart);
        for(int day=0;day<20;++day){solo.step(0);solo.step(UiStart);solo.finishStunt(solo.stunt==3?0x47:7,10,5);solo.step(0);solo.step(A);
            require(solo.phase==(day==19?UiPhase::Ending:UiPhase::Instructions),"All twenty successful stunts route through campaign screens");}
        for(int i=0;i<480;++i)solo.step(0);
        require(solo.phase==UiPhase::Title&&!solo.campaign.active,"Ending returns to title after surviving campaign");
        UiFlow failed(assets);failed.step(UiStart);
        for(int life=0;life<5;++life){failed.step(0);failed.step(UiStart);failed.finishStunt(1,99,10);failed.step(0);failed.step(B);}
        require(failed.phase==UiPhase::Title&&failed.campaign.players[0].savings==0,"Final lost life returns to title without banking failed pay");
        UiFlow titles(assets);for(int i=0;i<480;++i)titles.step(0);require(titles.page==1,"Title page uses original 480-frame duration");
        // Independent small text fixture exercises delay-before-write and each
        // two-frame scroll increment, not only final screenshot contents.
        auto fixture=std::make_unique<UiAssets>(assets);
        fixture->instructions[0].text={0x81,0,17,0x86,5,11,0,0x85,12,0x80};
        UiFlow timed(*fixture);timed.campaign.start(false);timed.beginInstructions();
        for(int i=0;i<4;++i)timed.step(0);require(timed.map[544]==0,"Glyph remains absent for first four wait frames");
        timed.step(0);require(timed.map[544]==11&&timed.position==546,"Fifth frame writes glyph and immediate following space");
        constexpr int scrollAfter[]={0,1,1,3,3,6,6,7,7,8};
        for(int expected:scrollAfter){timed.step(0);require(timed.scroll==expected,"Scroll follows 1/2/3/1/1 increments every two frames");}
        for(int i=0;i<5;++i)timed.step(0);require(timed.map[576]==12&&timed.textDone,"Typing resumes on next anchored row");
        bool rejected=false;fixture->instructions[0].text={0x94,0x80};
        try{UiFlow bad(*fixture);bad.campaign.start(false);bad.beginInstructions();}catch(const std::runtime_error&){rejected=true;}
        require(rejected,"Unrecognized text operations fail closed");
        fprintf(log,"PASS: %d UI flow/text assertions. Full original presentation timing and high-score entry remain pending.\n",count);fclose(log);return 0;
    }catch(const std::exception& e){fprintf(log,"FAIL after %d assertions: %s\n",count,e.what());fclose(log);return 1;}
}
}
