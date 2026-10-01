#include "ui.h"
#include <cstdio>
#include <memory>
#include <stdexcept>
namespace ticd {
int runUiTests(const UiAssets& assets){
    FILE* log=fopen("ui-test.txt","w");if(!log)return 2;int count=0;
    auto require=[&](bool condition,const char* message){++count;if(!condition)throw std::runtime_error(message);};
    try{
        std::array<uint8_t,Width*Height> scene{};for(size_t i=0;i<scene.size();++i)scene[i]=(i/7)%4;
        const auto pausedScene=renderPausedGame(assets,scene);
        bool preserved=true,originalStrip=true;
        for(int i=0;i<Width*PlayHeight;++i)preserved&=scene[i]==pausedScene[i];
        for(int i=0;i<Width*8;++i)originalStrip&=pausedScene[Width*PlayHeight+i]==assets.pauseStrip[i];
        require(preserved&&originalStrip,"Pause changes only the original bottom HUD strip, preserving the whole playfield");
        require(scene!=pausedScene&&renderPausedGame(assets,scene)==pausedScene,"Pause display is stable and does not mutate the saved gameplay image");
        UiFlow gameplay(assets);gameplay.phase=UiPhase::Playing;gameplay.ticks=0;
        auto fadeScene=gameplay.renderGameplay(scene,false);bool allWhite=true;for(int shade:fadeScene)allWhite&=shade==0;
        require(allWhite,"Gameplay starts with the white palette before its asynchronous fade");
        for(int step=7;step>=0;--step){gameplay.step(0);require(gameplay.gameplayFade==step+1,"Odd global frames leave the gameplay fade counter unchanged");
            gameplay.step(0);require(gameplay.gameplayFade==step,"Even global frames advance the gameplay fade once");}
        require(gameplay.renderGameplay(scene,false)==scene,"Gameplay fade restores all four colors after sixteen global updates");
        gameplay.step(0);gameplay.step(0);require(gameplay.gameplayFade==0,"Gameplay fade counter stops at zero");
        gameplay.gameplayFade=4;gameplay.gameplayPaused=true;int pausedAt=gameplay.ticks;
        for(int i=0;i<5;++i)gameplay.step(0);
        require(gameplay.gameplayFade==4&&gameplay.ticks==pausedAt+5,"Pause freezes the fade while the shared global counter continues");
        gameplay.gameplayPaused=false;gameplay.step(0);require(gameplay.gameplayFade==3,"Resuming uses global parity rather than a restarted fade clock");
        UiFlow oddStart(assets);oddStart.step(UiStart);oddStart.step(0);oddStart.step(UiStart);
        require(oddStart.phase==UiPhase::Playing&&oddStart.gameplayFade==8,"Odd-phase stunt entry retains all eight palette steps");
        oddStart.step(0);require(oddStart.gameplayFade==7,"First even update advances an odd-phase stunt entry");
        UiFlow boot(assets);boot.beginBoot();
        auto white=boot.render();bool blank=true;for(int shade:white)blank&=shade==0;
        require(blank,"Boot starts at the original white palette");
        for(int i=0;i<32;++i)boot.step(UiStart|A|B);
        auto copyright=boot.render();bool ink=false;for(int shade:copyright)ink|=shade!=0;
        require(ink&&boot.phase==UiPhase::Boot,"Copyright fades in despite held buttons");
        for(int i=0;i<180;++i)boot.step(i%2?UiStart:0);
        require(boot.phase==UiPhase::Boot&&boot.phaseTicks==212,"Copyright hold lasts all 180 updates and cannot be skipped");
        for(int i=0;i<31;++i)boot.step(0);
        auto faded=boot.render();blank=true;for(int shade:faded)blank&=shade==0;
        require(blank&&boot.phase==UiPhase::Boot,"Copyright fade reaches white before switching maps");
        boot.step(0);require(boot.phase==UiPhase::TitleIntro&&boot.phaseTicks==0,"Copyright exits after its 32-update fade");
        for(int i=0;i<33;++i)boot.step(UiStart);
        require(boot.phase==UiPhase::TitleIntro&&boot.titleScroll==0,"Title intro completes fade and one wait before closing");
        for(int i=0;i<40;++i)boot.step(UiStart);
        require(boot.phase==UiPhase::TitleIntro&&boot.titleScroll==-80,"Title page is installed while fully closed");
        for(int i=0;i<40;++i)boot.step(UiStart);
        require(boot.phase==UiPhase::Title&&boot.phaseTicks==0&&boot.titleScroll==0,"Page timer starts only after the initial opening");
        boot.step(UiStart);require(boot.phase==UiPhase::Title,"Held boot input does not start a campaign");
        boot.step(0);boot.step(UiStart);require(boot.phase==UiPhase::Instructions,"A fresh Start works after the boot sequence");
        auto tap=[](UiFlow& flow,int key){flow.step(0);flow.step(key);};
        auto openPassword=[&](UiFlow& flow){for(int key:{Up,Down,Left,Right})tap(flow,key);
            for(int i=0;i<81;++i)flow.step(0);};
        auto enterPassword=[&](UiFlow& flow,int index){for(int digit=0;digit<8;++digit){
            for(int n=0;n<assets.passwords[index][digit];++n)tap(flow,Up);
            if(digit<7)tap(flow,Right);}};
        UiFlow secret(assets);tap(secret,Up);tap(secret,Up);tap(secret,Down);tap(secret,Left);tap(secret,Right);
        require(secret.phase==UiPhase::Title,"Wrong unlock input resets without treating it as a new first key");
        tap(secret,Up|Left);tap(secret,Down);tap(secret,Left);tap(secret,Right);
        require(secret.phase==UiPhase::Title,"Unlock compares the complete newly pressed button mask");
        for(int key:{Up,Down,Left,Right})tap(secret,key);
        for(int i=0;i<40;++i)secret.step(0);
        require(secret.titleScroll==-80&&secret.pendingMusic==-2,"Password closes the center before changing music");
        secret.step(0);require(secret.pendingMusic==7&&secret.titleScroll==-80,"Password song starts during the one closed-screen wait");
        for(int i=0;i<40;++i)secret.step(0);
        require(secret.phase==UiPhase::Password&&secret.passwordCursor==0,"Original directional sequence opens password entry after close/wait/open");
        require(secret.map[21*32+6]==0x26,"Untouched password digits retain original placeholder glyphs");
        tap(secret,Down);require(secret.password[0]==10,"Down from an untouched digit selects nine");
        tap(secret,Up);require(secret.password[0]==1,"Up wraps nine to zero");
        secret.step(Up);require(secret.password[0]==1,"Holding a direction does not repeat password editing");
        tap(secret,Left);require(secret.passwordCursor==0,"Password cursor stops at left edge");
        for(int i=0;i<9;++i)tap(secret,Right);
        require(secret.passwordCursor==7,"Password cursor stops at right edge");
        tap(secret,Left|Up);require(secret.passwordCursor==6&&secret.password[6]==1,"Cursor movement precedes digit editing in the same update");
        tap(secret,A);require(secret.phase==UiPhase::PasswordSubmit&&secret.pendingMusic==-2,"Submit waits once before stopping music and validating");
        secret.step(0);require(secret.pendingMusic==-1&&secret.passwordAction==-1,"Incomplete password is rejected and music stops");
        for(int i=0;i<80;++i)secret.step(0);
        require(secret.phase==UiPhase::PasswordFeedback&&secret.map==assets.hiddenMaps[1],"Invalid password opens original rejection map");
        for(int i=0;i<59;++i)secret.step(UiStart);
        require(secret.phase==UiPhase::PasswordFeedback,"Feedback hold cannot be skipped");
        secret.step(0);for(int i=0;i<81;++i)secret.step(0);
        require(secret.phase==UiPhase::Password&&secret.password==std::array<uint8_t,8>{},"A submission returns to fresh password entry after feedback");
        for(int action=0;action<10;++action){UiFlow selection(assets);openPassword(selection);enterPassword(selection,action);
            tap(selection,UiStart);selection.step(0);
            require(selection.passwordAction==action,"Every locally extracted password reaches its identified action");
            for(int i=0;i<80;++i)selection.step(0);
            require(selection.map==assets.hiddenMaps[2],"Valid password displays original acceptance text");
            for(int i=0;i<60;++i)selection.step(0);
            for(int i=0;i<(action==9?80:81);++i)selection.step(0);
            if(action<9){require(selection.phase==UiPhase::Title,"Start submission returns to title, not directly into a stunt");
                selection.twoPlayers=true;tap(selection,UiStart);
                require(selection.stunt==(action<5?action:0)&&selection.level==(action>=5?action-5:0),"Password sets campaign start stage or difficulty");
                require(selection.campaign.players[1].day==selection.stunt&&selection.campaign.players[1].difficulty==selection.level,"Password settings apply to both players");
            }else{
                require(selection.phase==UiPhase::MusicTest,"Music-test password opens original sound screen");
                tap(selection,Left);tap(selection,Down);
                require(selection.testTune==13&&selection.testEffect==25,"Sound selections wrap across all fourteen songs and twenty-six effects");
                selection.step(0);require(selection.map[19*32+17]==14&&selection.map[21*32+16]==2&&selection.map[21*32+17]==10,"Music-test counters display hexadecimal as the original nibble renderer");
                tap(selection,A);require(selection.pendingMusic==13&&selection.pendingSound<0,"First A starts the selected tune");
                selection.musicActive=true;tap(selection,A);require(selection.pendingMusic==-2&&selection.pendingSound==25,"A during the same active tune queues the chosen effect");
                selection.musicActive=false;tap(selection,A);require(selection.pendingMusic==13,"A restarts a tune after all four music voices finish");
                tap(selection,B);require(selection.pendingMusic==-1&&selection.testLastTune==-1,"B stops playback and resets the remembered tune");
                tap(selection,A|B);require(selection.pendingMusic==13,"Simultaneous B and A stop then restart in original order");
                tap(selection,UiStart);for(int i=0;i<81;++i)selection.step(0);
                require(selection.phase==UiPhase::Title,"Music-test return honors the Start used for password submission");
            }
        }
        UiFlow optionsSecret(assets);optionsSecret.page=5;openPassword(optionsSecret);
        require(optionsSecret.phase==UiPhase::Title,"Options page does not run the hidden unlock recognizer");
        UiFlow returnToPassword(assets);openPassword(returnToPassword);enterPassword(returnToPassword,9);tap(returnToPassword,B);returnToPassword.step(0);
        for(int i=0;i<220;++i)returnToPassword.step(0);
        require(returnToPassword.phase==UiPhase::MusicTest,"B can also submit the music-test password");
        tap(returnToPassword,UiStart);for(int i=0;i<81;++i)returnToPassword.step(0);
        require(returnToPassword.phase==UiPhase::Password,"Music-test exit returns to entry when password was submitted with an action button");
        UiFlow simultaneous(assets);simultaneous.page=5;simultaneous.step(Down|UiStart);
        require(simultaneous.phase==UiPhase::Instructions&&simultaneous.campaign.players[1].lives==5,"Options applies player toggle before simultaneous Start");
        UiFlow bothDirections(assets);bothDirections.page=5;bothDirections.step(Up|Down|UiSelect|UiStart);
        require(bothDirections.twoPlayers&&bothDirections.campaign.players[1].lives==5,"Combined option keys toggle once before starting");
        UiFlow outsideOptions(assets);outsideOptions.step(Down|UiStart);
        require(!outsideOptions.twoPlayers&&outsideOptions.campaign.players[1].lives==0,"Title directions do not change player count outside options");
        auto finishResultFade=[](UiFlow& flow){for(int i=0;i<32;++i)flow.step(0);};
        UiFlow u(assets);u.step(UiSelect);for(int i=0;i<80;++i)u.step(UiSelect);require(u.page==5,"Select opens original options");
        u.step(UiSelect);require(!u.twoPlayers,"Holding Select does not toggle repeatedly");
        u.step(0);u.step(Down);require(u.twoPlayers,"Down selects two players");
        u.step(UiStart);require(u.phase==UiPhase::Instructions&&u.campaign.players[1].lives==5,"Start opens first player's instructions");
        u.step(UiStart);require(u.phase==UiPhase::Instructions,"Held Start cannot skip a second screen");
        u.step(0);u.step(UiStart);require(u.phase==UiPhase::Playing,"Fresh Start skips instruction typing");
        u.finishStunt(3,25,10);require(u.campaign.players[0].savings==35&&u.phase==UiPhase::Result,"Gameplay result settles once and opens results");
        finishResultFade(u);u.step(0);u.step(A);u.step(0);u.step(A);require(u.campaign.current==1&&u.stunt==0&&u.phase==UiPhase::Instructions,"Result passes to independent second player");
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
        for(int day=0;day<20;++day){solo.step(0);solo.step(UiStart);solo.finishStunt(solo.stunt==3?0x47:7,10,5);finishResultFade(solo);solo.step(0);solo.step(A);solo.step(0);solo.step(A);
            require(solo.phase==(day==19?UiPhase::Ending:UiPhase::Instructions),"All twenty successful stunts route through campaign screens");}
        for(int i=0;i<480;++i)solo.step(0);
        require(solo.phase==UiPhase::Title&&!solo.campaign.active,"Ending returns to title after surviving campaign");
        UiFlow failed(assets);failed.step(UiStart);
        for(int life=0;life<5;++life){failed.step(0);failed.step(UiStart);failed.finishStunt(1,99,10);finishResultFade(failed);failed.step(0);failed.step(B);}
        for(int i=0;i<480;++i)failed.step(0);
        require(failed.phase==UiPhase::Title&&failed.campaign.players[0].savings==0,"Final lost life returns to title without banking failed pay");
        UiFlow titles(assets);for(int i=0;i<480;++i)titles.step(0);require(titles.page==0&&titles.titleDirection==-1,"Title starts closing after original 480-frame duration");
        for(int i=0;i<39;++i)titles.step(0);require(titles.titleScroll==-78&&titles.page==0,"Title closes two pixels per frame");
        titles.step(0);require(titles.titleScroll==-80&&titles.page==1&&titles.titleDirection==1,"Page changes only at closed position");
        for(int i=0;i<40;++i)titles.step(0);require(titles.titleScroll==0&&titles.titleDirection==0&&titles.phaseTicks==0,"New page opens over forty updates before its hold timer");
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
        UiFlow resultTiming(assets);resultTiming.campaign.start(false);resultTiming.beginInstructions();resultTiming.step(UiStart);resultTiming.finishStunt(3,10,0);
        auto whiteResult=resultTiming.render();bool whiteResultOnly=true;for(int shade:whiteResult)whiteResultOnly&=shade==0;
        require(whiteResultOnly,"Result fade starts with a white image");
        for(int i=0;i<32;++i)resultTiming.step(A);
        require(!resultTiming.resultFade&&resultTiming.resultStage==0&&resultTiming.displayPay==10,"Result fade consumes 32 updates without accepting skip or counting pay");
        resultTiming.step(A);require(resultTiming.resultStage==0,"A held through the fade does not become a fresh skip press");
        resultTiming.step(0);resultTiming.step(A);
        require(resultTiming.resultStage==6&&resultTiming.resultHold==60+600-resultTiming.phaseTicks,"Success hold adds sixty to the remaining budget, including fade and count-up time");
        while(resultTiming.phaseTicks<659)resultTiming.step(0);
        require(resultTiming.phase==UiPhase::Result,"Short success remains visible through the original budget plus sixty updates");
        resultTiming.step(0);require(resultTiming.phase==UiPhase::Instructions,"Short success expires at 660 updates without input");
        UiFlow longPay(assets);longPay.campaign.start(false);longPay.beginInstructions();longPay.step(UiStart);longPay.finishStunt(0x43,700,0);finishResultFade(longPay);
        for(int i=0;i<1000&&longPay.resultStage<6;++i)longPay.step(0);
        require(longPay.resultStage==6&&longPay.phaseTicks>600&&longPay.resultHold==61,"Expired background counter retains one, then adds sixty after long counting");
        for(int i=0;i<60;++i)longPay.step(0);
        require(longPay.phase==UiPhase::Result,"Minimum result hold does not expire one update early");
        longPay.step(0);require(longPay.phase==UiPhase::Instructions,"Long count-up continues after its minimum hold");
        UiFlow failureTiming(assets);failureTiming.campaign.start(false);failureTiming.beginInstructions();failureTiming.step(UiStart);failureTiming.finishStunt(1,0,0);
        for(int i=0;i<511;++i)failureTiming.step(0);
        require(failureTiming.phase==UiPhase::Result,"Failure waits all 480 updates after its 32-update fade");
        failureTiming.step(0);require(failureTiming.phase==UiPhase::Instructions,"Failure exits after fade plus fixed timeout");
        UiFlow countup(assets);countup.campaign.start(false);countup.beginInstructions();countup.step(UiStart);countup.finishStunt(7,3,2);finishResultFade(countup);
        for(int i=0;i<14;++i)countup.step(0);require(!countup.showSavings,"Result has fifteen-frame introductory wait");
        countup.step(0);require(countup.showSavings&&countup.displaySavings==0,"Savings appear before transferring pay");
        for(int i=0;i<20;++i)countup.step(0);
        require(countup.showPay&&countup.displayPay==2&&countup.displaySavings==2,"First perfect pay tick credits two and consumes one");
        countup.step(0);countup.step(0);require(countup.displayPay==0&&countup.displaySavings==6,"Remaining perfect pay counts correctly");
        countup.step(0);for(int i=0;i<15;++i)countup.step(0);
        require(countup.showTime&&countup.displayTime==1&&countup.displaySavings==8,"Time bonus follows fifteen-frame wait and doubles perfect award");
        countup.step(0);countup.step(0);require(countup.resultStage==6&&countup.displaySavings==10,"Visible count converges to committed campaign savings");
        UiFlow skipped(assets);skipped.campaign.start(false,3);skipped.beginInstructions();skipped.step(UiStart);skipped.finishStunt(0x47,100,90);finishResultFade(skipped);
        skipped.step(A);require(skipped.phase==UiPhase::Result&&skipped.resultStage==6&&skipped.displaySavings==200&&!skipped.showTime,"Action skips counts without leaving result, Bomb has no time bonus");
        skipped.step(0);skipped.step(A);require(skipped.phase==UiPhase::Instructions&&skipped.stunt==4,"Second action continues after accelerated result");
        UiFlow high(assets);high.campaign.start(false);high.campaign.players[0].savings=999999;high.campaign.players[0].lives=1;
        high.beginInstructions();high.step(UiStart);high.finishStunt(1,0,0);finishResultFade(high);
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
        high.step(UiSelect);for(int i=0;i<80;++i)high.step(0);high.step(UiStart);require(high.scores[0]==11,"Starting a new campaign preserves session high scores");
        fprintf(log,"PASS: %d UI flow/text assertions. Full original presentation timing remains pending.\n",count);fclose(log);return 0;
    }catch(const std::exception& e){fprintf(log,"FAIL after %d assertions: %s\n",count,e.what());fclose(log);return 1;}
}
}
