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
        u.step(0);u.step(A);u.step(0);u.step(A);require(u.campaign.current==1&&u.stunt==0&&u.phase==UiPhase::Instructions,"Result passes to independent second player");
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
        for(int day=0;day<20;++day){solo.step(0);solo.step(UiStart);solo.finishStunt(solo.stunt==3?0x47:7,10,5);solo.step(0);solo.step(A);solo.step(0);solo.step(A);
            require(solo.phase==(day==19?UiPhase::Ending:UiPhase::Instructions),"All twenty successful stunts route through campaign screens");}
        for(int i=0;i<480;++i)solo.step(0);
        require(solo.phase==UiPhase::Title&&!solo.campaign.active,"Ending returns to title after surviving campaign");
        UiFlow failed(assets);failed.step(UiStart);
        for(int life=0;life<5;++life){failed.step(0);failed.step(UiStart);failed.finishStunt(1,99,10);failed.step(0);failed.step(B);}
        for(int i=0;i<480;++i)failed.step(0);
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
        UiFlow countup(assets);countup.campaign.start(false);countup.beginInstructions();countup.step(UiStart);countup.finishStunt(7,3,2);
        for(int i=0;i<14;++i)countup.step(0);require(!countup.showSavings,"Result has fifteen-frame introductory wait");
        countup.step(0);require(countup.showSavings&&countup.displaySavings==0,"Savings appear before transferring pay");
        for(int i=0;i<20;++i)countup.step(0);
        require(countup.showPay&&countup.displayPay==2&&countup.displaySavings==2,"First perfect pay tick credits two and consumes one");
        countup.step(0);countup.step(0);require(countup.displayPay==0&&countup.displaySavings==6,"Remaining perfect pay counts correctly");
        countup.step(0);for(int i=0;i<15;++i)countup.step(0);
        require(countup.showTime&&countup.displayTime==1&&countup.displaySavings==8,"Time bonus follows fifteen-frame wait and doubles perfect award");
        countup.step(0);countup.step(0);require(countup.resultStage==6&&countup.displaySavings==10,"Visible count converges to committed campaign savings");
        UiFlow skipped(assets);skipped.campaign.start(false,3);skipped.beginInstructions();skipped.step(UiStart);skipped.finishStunt(0x47,100,90);
        skipped.step(A);require(skipped.phase==UiPhase::Result&&skipped.resultStage==6&&skipped.displaySavings==200&&!skipped.showTime,"Action skips counts without leaving result, Bomb has no time bonus");
        skipped.step(0);skipped.step(A);require(skipped.phase==UiPhase::Instructions&&skipped.stunt==4,"Second action continues after accelerated result");
        UiFlow high(assets);high.campaign.start(false);high.campaign.players[0].savings=999999;high.campaign.players[0].lives=1;
        high.beginInstructions();high.step(UiStart);high.finishStunt(1,0,0);
        for(int i=0;i<479;++i)high.step(A);require(high.phase==UiPhase::Result,"Game over waits 480 frames regardless of action buttons");
        high.step(0);require(high.phase==UiPhase::NameEntry&&high.scoreRank==0,"High savings insert at first qualifying rank");
        require(high.scores[3]==0x99&&high.scores[4]==0x99&&high.scores[5]==0x99,"Savings convert to original BCD record");
        require(high.scores[6]==assets.initialScores[0]&&high.scores[9]==assets.initialScores[3],"Insertion shifts previous records down");
        high.step(A);high.step(0);high.step(B);high.step(0);high.step(A);high.step(0);high.step(B);
        require(high.nameLength==3&&high.scores[0]==11&&high.scores[2]==11,"A and B confirm a letter, capped at three initials");
        high.step(Left);require(high.nameMotion==-8&&high.nameScroll==180,"Left starts an eight-pixel alphabet movement");
        for(int i=0;i<8;++i)high.step(0);require(high.nameScroll==172&&high.nameMotion==0,"Alphabet moves one pixel for each of eight frames");
        high.step(Left);for(int i=0;i<8;++i)high.step(0);high.step(A);
        require(high.nameLength==2&&high.scores[2]==0,"Backspace symbol erases the last initial");
        high.step(Right);for(int i=0;i<8;++i)high.step(0);high.step(B);
        require(high.phase==UiPhase::Title&&high.scores[0]==11,"End symbol returns to title and preserves entered scores");
        high.step(UiSelect);high.step(UiStart);require(high.scores[0]==11,"Starting a new campaign preserves session high scores");
        fprintf(log,"PASS: %d UI flow/text assertions. Full original presentation timing remains pending.\n",count);fclose(log);return 0;
    }catch(const std::exception& e){fprintf(log,"FAIL after %d assertions: %s\n",count,e.what());fclose(log);return 1;}
}
}
