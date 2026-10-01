#include "ui.h"
#include <cstdio>
#include <memory>
#include <stdexcept>
namespace ticd {
int runUiTests(const UiAssets& assets){
    FILE* log=fopen("ui-test.txt","w");if(!log)return 2;int count=0;
    auto require=[&](bool condition,const char* message){++count;if(!condition)throw std::runtime_error(message);};
    auto finishTitleExit=[](UiFlow& flow){for(int i=0;i<66;++i)flow.step(UiStart);};
    auto finishOutro=[](UiFlow& flow){for(int i=0;i<34&&flow.phase==UiPhase::StuntOutro;++i)flow.step(0);};
    auto finishInstructionExit=[](UiFlow& flow){for(int i=0;i<33;++i)flow.step(0);};
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
        UiFlow oddStart(assets);oddStart.step(UiStart);finishTitleExit(oddStart);oddStart.step(0);oddStart.step(0);oddStart.step(UiStart);finishInstructionExit(oddStart);
        require(oddStart.phase==UiPhase::Playing&&oddStart.gameplayFade==8,"Odd-phase stunt entry retains all eight palette steps");
        oddStart.step(0);require(oddStart.gameplayFade==7,"First even update advances an odd-phase stunt entry");
        UiFlow exiting(assets);exiting.campaign.start(false);exiting.beginInstructions();
        for(int i=0;i<37;++i)exiting.step(0);
        const auto instructionImage=exiting.render();const auto frozenMap=exiting.map;
        int frozenScroll=exiting.scroll;size_t frozenCursor=exiting.cursor;int exitFrame=exiting.ticks;
        exiting.step(UiStart);
        require(exiting.render()==instructionImage,"Instruction exit starts at the unchanged full-color image");
        constexpr int exitPalette[]={0xe4,0xe4,0xe4,0xa4,0x90,0x50,0x50,0x00};
        for(int frame=1;frame<=32;++frame){
            exiting.step(frame%2?UiStart|A|B:0);
            require(exiting.phase==UiPhase::Instructions,"Fresh input cannot bypass any instruction fade update");
            auto expected=instructionImage;int palette=exitPalette[std::min(7,frame/4)];
            for(auto& shade:expected)shade=(palette>>(shade*2))&3;
            require(exiting.render()==expected,"Instruction fade follows all original four-update palette intervals");
        }
        require(exiting.map==frozenMap&&exiting.scroll==frozenScroll&&exiting.cursor==frozenCursor,"Instruction typing and scrolling freeze during exit");
        require(exiting.instructionExit==1&&exiting.ticks==exitFrame+33,"Fade completes before the additional white-screen wait");
        exiting.step(UiStart|A);
        require(exiting.phase==UiPhase::Playing&&exiting.phaseTicks==0&&exiting.ticks==exitFrame+34,"Stunt entry follows exactly 32 fade updates plus one wait");
        exiting.beginInstructions();require(exiting.instructionExit==0,"Next instruction screen resets the completed exit state");
        for(bool success:{false,true}){
            UiFlow outro(assets);outro.campaign.start(false);outro.phase=UiPhase::Playing;outro.gameplayFade=0;outro.outroScene=scene;
            outro.finishStunt(success?3:1,20,10);
            require(outro.phase==UiPhase::StuntOutro&&outro.render()==scene,"Terminal result preserves the full last scene for its initial wait");
            for(int frame=1;frame<=32;++frame){outro.step(frame%2?UiStart|A|B:0);
                auto expected=scene;int palette=exitPalette[(frame-1)/4];for(auto& shade:expected)shade=(palette>>(shade*2))&3;
                require(outro.phase==UiPhase::StuntOutro&&outro.render()==expected,"Stunt exit waits once before its four-update palette steps; input cannot skip it");
            }
            outro.step(0);
            require(outro.phase==(success?UiPhase::Result:UiPhase::StuntOutro),"Success opens results after 33 updates; failure retains one setup wait");
            if(!success)outro.step(0);
            require(outro.phase==UiPhase::Result&&outro.phaseTicks==0&&outro.resultFade==32,"Result fade and timeout start after all preceding waits");
            require(outro.campaign.players[0].savings==(success?30:0),"Outro does not settle the result more than once");
        }
        UiFlow lost(assets);lost.campaign.start(false);lost.campaign.players[0].lives=1;lost.phase=UiPhase::Playing;lost.finishStunt(1,0,0);
        for(int frame=0;frame<33;++frame)lost.step(0);
        require(lost.phase==UiPhase::StuntOutro&&lost.campaign.last.gameOver,"Game-over path also retains the one setup wait before its result song");
        lost.step(0);require(lost.phase==UiPhase::Result,"Game-over result begins after 34 exit updates");
        UiFlow titleExit(assets);const auto lastTitle=titleExit.render();titleExit.step(UiStart);
        require(titleExit.phase==UiPhase::TitleExit&&titleExit.render()==lastTitle,"Title exit preserves the last page before fading");
        for(int frame=1;frame<=32;++frame){titleExit.step(frame%2?UiStart|A|B:0);
            auto expected=lastTitle;int palette=exitPalette[std::min(7,frame/4)];for(auto& shade:expected)shade=(palette>>(shade*2))&3;
            require(titleExit.phase==UiPhase::TitleExit&&titleExit.render()==expected,"Title fade follows the source schedule and cannot be skipped");}
        titleExit.step(UiStart);
        require(titleExit.phase==UiPhase::Instructions&&titleExit.instructionEnter==33&&titleExit.cursor==0,"Extra title wait precedes the first instruction setup wait");
        auto firstMap=titleExit.map;
        for(int frame=0;frame<32;++frame)titleExit.step(UiStart|A|B);
        require(titleExit.instructionEnter==1&&titleExit.cursor==0&&titleExit.map==firstMap,"First instruction fade leaves all text and input processing suspended");
        titleExit.step(UiStart|A|B);require(titleExit.instructionEnter==0&&titleExit.phase==UiPhase::Instructions&&titleExit.cursor>0,"First instruction starts typing only after setup wait and 32 fade updates");
        titleExit.step(UiStart);require(titleExit.instructionExit==0,"Start held through title and instruction fades cannot immediately skip the instructions");
        titleExit.step(0);titleExit.step(UiStart);require(titleExit.instructionExit==33,"Releasing then pressing Start works after the first instruction fade");
        UiFlow heldInstruction(assets);heldInstruction.campaign.start(false);heldInstruction.beginInstructions(true);
        for(int frame=0;frame<3000&&!heldInstruction.instructionExit;++frame)heldInstruction.step(UiStart);
        require(heldInstruction.textDone&&heldInstruction.instructionExit==33&&heldInstruction.phase==UiPhase::Instructions,"Start held through entry exits only when the complete text script returns");
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
        boot.step(0);boot.step(UiStart);require(boot.phase==UiPhase::TitleExit,"A fresh Start begins title exit after the boot sequence");
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
                selection.twoPlayers=true;tap(selection,UiStart);finishTitleExit(selection);
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
        require(simultaneous.phase==UiPhase::TitleExit&&simultaneous.campaign.players[1].lives==5,"Options applies player toggle before simultaneous Start");
        UiFlow bothDirections(assets);bothDirections.page=5;bothDirections.step(Up|Down|UiSelect|UiStart);
        require(bothDirections.twoPlayers&&bothDirections.campaign.players[1].lives==5,"Combined option keys toggle once before starting");
        UiFlow outsideOptions(assets);outsideOptions.step(Down|UiStart);
        require(!outsideOptions.twoPlayers&&outsideOptions.campaign.players[1].lives==0,"Title directions do not change player count outside options");
        auto finishResultFade=[&](UiFlow& flow){finishOutro(flow);for(int i=0;i<32;++i)flow.step(0);};
        UiFlow u(assets);u.step(UiSelect);for(int i=0;i<80;++i)u.step(UiSelect);require(u.page==5,"Select opens original options");
        u.step(UiSelect);require(!u.twoPlayers,"Holding Select does not toggle repeatedly");
        u.step(0);u.step(Down);require(u.twoPlayers,"Down selects two players");
        u.step(UiStart);require(u.phase==UiPhase::TitleExit&&u.campaign.players[1].lives==5,"Start commits player count before title exit");finishTitleExit(u);
        u.step(UiStart);require(u.phase==UiPhase::Instructions,"Held Start cannot skip a second screen");
        u.step(0);u.step(UiStart);require(u.phase==UiPhase::Instructions&&u.instructionExit==33,"Fresh Start begins the blocking instruction exit");
        finishInstructionExit(u);require(u.phase==UiPhase::Playing,"Stunt begins only after instruction fade and final wait");
        u.finishStunt(3,25,10);require(u.campaign.players[0].savings==35&&u.phase==UiPhase::StuntOutro,"Gameplay result settles once before the original exit waits");
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
        UiFlow solo(assets);solo.step(UiStart);finishTitleExit(solo);
        for(int day=0;day<20;++day){while(solo.instructionEnter)solo.step(0);solo.step(0);solo.step(UiStart);finishInstructionExit(solo);solo.finishStunt(solo.stunt==3?0x47:7,10,5);finishResultFade(solo);solo.step(0);solo.step(A);solo.step(0);solo.step(A);
            require(solo.phase==(day==19?UiPhase::Ending:UiPhase::Instructions),"All twenty successful stunts route through campaign screens");}
        require(solo.endingEnter==65,"Ending begins with result fade, setup wait and ending fade");
        int oldY=solo.celebration[0].y;solo.step(A);
        require(solo.endingEnter==64&&solo.celebration[0].y!=oldY,"Perfect celebration keeps moving during the outgoing result fade");
        for(int i=0;i<31;++i)solo.step(A);
        require(solo.endingEnter==33,"Outgoing result fade lasts exactly 32 updates");
        auto isWhite=[](const auto& pixels){for(int shade:pixels)if(shade)return false;return true;};
        require(isWhite(solo.render()),"Ending setup is entirely white");
        oldY=solo.celebration[0].y;solo.step(A);
        require(solo.endingEnter==32&&solo.celebration[0].y==oldY&&isWhite(solo.render()),"Setup wait disables celebration before ending fade starts");
        for(int i=0;i<32;++i)solo.step(A);
        require(solo.endingEnter==0&&!isWhite(solo.render()),"Ending fade restores the completed player's screen");
        for(int i=0;i<479;++i)solo.step(i%2?A:0);
        require(solo.phase==UiPhase::Ending,"The unskippable 480-update ending hold starts after all entry waits");
        solo.step(0);
        require(solo.phase==UiPhase::TitleReturn&&solo.titleIntroMusic==13,"Unranked ending preserves its song during the return fade");
        for(int i=0;i<145;++i)solo.step(0);
        require(solo.phase==UiPhase::Title&&!solo.campaign.active,"Ending returns to title after surviving campaign");
        UiFlow failed(assets);failed.step(UiStart);finishTitleExit(failed);
        for(int life=0;life<5;++life){while(failed.instructionEnter)failed.step(0);failed.step(0);failed.step(UiStart);finishInstructionExit(failed);failed.finishStunt(1,99,10);finishResultFade(failed);failed.step(0);failed.step(B);}
        for(int i=0;i<480;++i)failed.step(0);
        for(int i=0;i<145&&failed.phase!=UiPhase::Title;++i)failed.step(0);
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
        UiFlow resultTiming(assets);resultTiming.campaign.start(false);resultTiming.beginInstructions();resultTiming.step(UiStart);finishInstructionExit(resultTiming);resultTiming.finishStunt(3,10,0);finishOutro(resultTiming);
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
        UiFlow perfectTiming(assets);perfectTiming.campaign.start(false);perfectTiming.phase=UiPhase::Playing;perfectTiming.finishStunt(7,10,0);finishOutro(perfectTiming);
        for(int frame=0;frame<779;++frame)perfectTiming.step(0);
        require(perfectTiming.phase==UiPhase::Result&&perfectTiming.resultStage==6,"Perfect results use the 720-update budget installed by the celebration setup");
        perfectTiming.step(0);require(perfectTiming.phase==UiPhase::Instructions,"Short perfect result expires at 780 updates including its added sixty");
        UiFlow celebration(assets);celebration.campaign.start(false);celebration.phase=UiPhase::Playing;celebration.finishStunt(7,0,0);finishOutro(celebration);celebration.ticks=0;
        require(celebration.celebrationCount==0&&celebration.celebration[3].delay==48,"Perfect result initializes four emitters spaced sixteen updates apart");
        int firstX=celebration.celebration[0].x;celebration.step(0);
        require(celebration.celebrationCount==10&&celebration.celebration[0].y==138,"First emitter draws ten pieces and moves its center upward by five");
        bool collapsed=true;for(int i=0;i<10;++i)collapsed&=celebration.celebrationSprites[i].x==firstX&&celebration.celebrationSprites[i].y==143;
        require(collapsed,"Zero-radius pieces use the center before movement, not after it");
        for(int i=1;i<16;++i)celebration.step(0);
        require(celebration.celebrationCount==10&&celebration.celebration[1].delay==0,"Second emitter consumes all sixteen wait updates");
        celebration.step(0);require(celebration.celebrationCount==20,"Second emitter starts on update seventeen");
        for(int i=17;i<24;++i)celebration.step(0);
        require(celebration.celebration[0].y==47&&celebration.celebration[0].velocity==254&&celebration.celebration[0].radius==1,"Global eighth-update acceleration starts expansion at velocity minus two");
        for(int i=24;i<49;++i)celebration.step(0);
        require(celebration.celebrationCount==40,"All four emitters fit exactly forty pieces");
        for(auto& emitter:celebration.celebration)emitter.delay=200;
        celebration.celebration[0].delay=0;celebration.celebration[0].y=192;int oldRandom=celebration.randomState;
        celebration.step(0);require(celebration.celebrationCount==0&&celebration.celebration[0].y==143&&celebration.celebration[0].velocity==251&&celebration.randomState!=oldRandom,"Emitter reaching the lower boundary respawns without drawing that update");
        // Synthetic tables isolate signed angle/radius arithmetic from ROM data.
        for(int i=0;i<256;++i)fixture->celebrationProducts[i]=(i*i/4)&255;
        fixture->celebrationWave.fill(5);fixture->celebrationWave[64]=7;
        UiFlow arithmetic(*fixture);arithmetic.campaign.start(false);arithmetic.phase=UiPhase::Playing;arithmetic.finishStunt(7,0,0);finishOutro(arithmetic);
        for(auto& emitter:arithmetic.celebration)emitter.delay=200;
        arithmetic.celebration[0]={40,50,0,6,0};arithmetic.ticks=65535;arithmetic.step(0);
        require(arithmetic.celebrationSprites[0].x==49&&arithmetic.celebrationSprites[0].y==56,"Celebration keeps table rounding at an odd factor difference");
        arithmetic.celebration[0]={40,50,0,250,0};arithmetic.ticks=65535;arithmetic.step(0);
        require(arithmetic.celebrationSprites[0].x==31&&arithmetic.celebrationSprites[0].y==44,"Negative radius reverses both signed offsets");
        arithmetic.celebration[0]={40,50,0,6,0};arithmetic.ticks=127;arithmetic.step(0);
        require(arithmetic.celebrationSprites[0].x==31&&arithmetic.celebrationSprites[0].y==44,"Opposite angle reverses both offsets without floating point");
        // An empty background plus one solid 8x8 tile exercises result-only
        // object height, transparency, background priority and the ten-slot limit.
        fixture->resultTiles[2].fill(0);fixture->resultTexts[0].fill(0);fixture->resultLayouts[2].fill(0);
        for(int i=0;i<64;++i)fixture->resultTiles[2][200*64+i]=3;
        arithmetic.resultFade=0;arithmetic.celebrationCount=1;arithmetic.celebrationSprites[0]={8,16,200};
        auto particle=arithmetic.render();require(particle[0]==3&&particle[7*Width+7]==3&&particle[8*Width]==0,"Result celebration draws 8x8 sprites rather than the stunt's 8x16 pieces");
        fixture->resultTiles[2][0]=1;particle=arithmetic.render();require(particle[0]==1,"Celebration sprites stay behind nonzero background colors");fixture->resultTiles[2][0]=0;
        arithmetic.celebrationCount=11;for(int i=0;i<10;++i)arithmetic.celebrationSprites[i]={0,16,200};arithmetic.celebrationSprites[10]={8,16,200};
        particle=arithmetic.render();require(particle[0]==0,"Ten offscreen-X sprites on a row still hide the eleventh sprite");
        UiFlow longPay(assets);longPay.campaign.start(false);longPay.beginInstructions();longPay.step(UiStart);finishInstructionExit(longPay);longPay.finishStunt(0x43,700,0);finishResultFade(longPay);
        for(int i=0;i<1000&&longPay.resultStage<6;++i)longPay.step(0);
        require(longPay.resultStage==6&&longPay.phaseTicks>600&&longPay.resultHold==61,"Expired background counter retains one, then adds sixty after long counting");
        for(int i=0;i<60;++i)longPay.step(0);
        require(longPay.phase==UiPhase::Result,"Minimum result hold does not expire one update early");
        longPay.step(0);require(longPay.phase==UiPhase::Instructions,"Long count-up continues after its minimum hold");
        UiFlow failureTiming(assets);failureTiming.campaign.start(false);failureTiming.beginInstructions();failureTiming.step(UiStart);finishInstructionExit(failureTiming);failureTiming.finishStunt(1,0,0);finishOutro(failureTiming);
        for(int i=0;i<511;++i)failureTiming.step(0);
        require(failureTiming.phase==UiPhase::Result,"Failure waits all 480 updates after its 32-update fade");
        failureTiming.step(0);require(failureTiming.phase==UiPhase::Instructions,"Failure exits after fade plus fixed timeout");
        UiFlow alternating(assets);alternating.campaign.start(false);alternating.phase=UiPhase::Playing;alternating.finishStunt(7,10,0);finishResultFade(alternating);
        alternating.step(A);alternating.step(0);auto previousMap=alternating.render(false);alternating.step(A);
        require(alternating.phase==UiPhase::Instructions&&alternating.instructionEnter==65&&alternating.instructionAlternate,"Later instructions wait once and alternate maps for sixty-four updates");
        require(alternating.outroScene==previousMap&&alternating.render()==previousMap,"Map transition removes result objects and preserves its background");
        alternating.instructionEnter=0;auto nextMap=alternating.render();alternating.instructionEnter=65;
        constexpr int mapPattern[]={0xff,0xf7,0xdb,0xb6,0xaa,0x49,0x24,0x08};
        alternating.step(UiStart);require(alternating.render()==previousMap&&alternating.cursor==0,"Setup wait preserves old map before alternation begins");
        for(int bit=0;bit<63;++bit){alternating.step(UiStart);bool oldMap=(mapPattern[bit/8]>>(bit%8))&1;
            require(alternating.render()==(oldMap?previousMap:nextMap)&&alternating.cursor==0,"Original least-significant-bit pattern selects complete maps before text runs");}
        alternating.step(UiStart);require(alternating.instructionEnter==0&&alternating.render()==nextMap&&alternating.cursor>0,"Final map bit leaves the new instruction screen ready for typing");
        alternating.step(UiStart);require(alternating.instructionExit==0,"Held Start cannot bypass map alternation and skip the next instruction screen");
        UiFlow countup(assets);countup.campaign.start(false);countup.beginInstructions();countup.step(UiStart);finishInstructionExit(countup);countup.finishStunt(7,3,2);finishResultFade(countup);
        for(int i=0;i<14;++i)countup.step(0);require(!countup.showSavings,"Result has fifteen-frame introductory wait");
        countup.step(0);require(countup.showSavings&&countup.displaySavings==0,"Savings appear before transferring pay");
        for(int i=0;i<20;++i)countup.step(0);
        require(countup.showPay&&countup.displayPay==2&&countup.displaySavings==2,"First perfect pay tick credits two and consumes one");
        countup.step(0);countup.step(0);require(countup.displayPay==0&&countup.displaySavings==6,"Remaining perfect pay counts correctly");
        countup.step(0);for(int i=0;i<15;++i)countup.step(0);
        require(countup.showTime&&countup.displayTime==1&&countup.displaySavings==8,"Time bonus follows fifteen-frame wait and doubles perfect award");
        countup.step(0);countup.step(0);require(countup.resultStage==6&&countup.displaySavings==10,"Visible count converges to committed campaign savings");
        UiFlow skipped(assets);skipped.campaign.start(false,3);skipped.beginInstructions();skipped.step(UiStart);finishInstructionExit(skipped);skipped.finishStunt(0x47,100,90);finishResultFade(skipped);
        skipped.step(A);require(skipped.phase==UiPhase::Result&&skipped.resultStage==6&&skipped.displaySavings==200&&!skipped.showTime,"Action skips counts without leaving result, Bomb has no time bonus");
        skipped.step(0);skipped.step(A);require(skipped.phase==UiPhase::Instructions&&skipped.stunt==4,"Second action continues after accelerated result");
        UiFlow high(assets);high.campaign.start(false);high.campaign.players[0].savings=999999;high.campaign.players[0].lives=1;
        high.beginInstructions();high.step(UiStart);finishInstructionExit(high);high.finishStunt(1,0,0);finishResultFade(high);
        for(int i=0;i<479;++i)high.step(A);require(high.phase==UiPhase::Result,"Game over waits 480 frames regardless of action buttons");
        high.step(0);require(high.phase==UiPhase::NameEntry&&high.scoreRank==0,"High savings insert at first qualifying rank");
        require(high.scores[3]==0x99&&high.scores[4]==0x99&&high.scores[5]==0x99,"Savings convert to original BCD record");
        require(high.scores[6]==assets.initialScores[0]&&high.scores[9]==assets.initialScores[3],"Insertion shifts previous records down");
        require(high.nameEnter==64&&high.render()==high.outroScene,"High-score entry retains the outgoing screen before fading it");
        auto nameFull=std::make_unique<UiFlow>(high);nameFull->nameEnter=0;
        const auto namePixels=nameFull->render();
        auto checkNamePalette=[&](int frame){auto expected=frame<32?high.outroScene:namePixels;
            int palette=exitPalette[frame<32?frame/4:(63-frame)/4];
            for(auto& shade:expected)shade=(palette>>(shade*2))&3;
            require(high.render()==expected,"Every high-score transition update uses the original four-update palette steps");};
        for(int i=0;i<32;++i){checkNamePalette(i);high.step(A|Left);}
        require(high.nameEnter==32&&isWhite(high.render()),"Name screen starts white after 32 outgoing updates");
        for(int i=32;i<64;++i){checkNamePalette(i);high.step(A|Left);}
        require(high.nameEnter==0&&high.nameLength==0&&high.nameScroll==180&&high.nameMotion==0&&!high.nameBlink,"Both name-entry fades block letters, movement and arrow blinking");
        require(!isWhite(high.render()),"Name-entry fade restores all screen colors");
        high.step(A);require(high.nameLength==0,"A held through name entry does not create a fresh letter press");
        bool blink=high.nameBlink;while(high.ticks&15)high.step(0);
        require(high.nameBlink!=blink,"Name arrows begin toggling at an active loop's sixteen-update boundary");
        high.step(0);
        high.step(A);high.step(0);high.step(B);high.step(0);high.step(A);high.step(0);high.step(B);
        require(high.nameLength==3&&high.scores[0]==11&&high.scores[2]==11,"A and B confirm a letter, capped at three initials");
        high.step(Left);require(high.nameMotion==-8&&high.nameScroll==180,"Left starts an eight-pixel alphabet movement");
        for(int i=0;i<8;++i)high.step(0);require(high.nameScroll==172&&high.nameMotion==0,"Alphabet moves one pixel for each of eight frames");
        high.step(Left);for(int i=0;i<8;++i)high.step(0);high.step(A);
        require(high.nameLength==2&&high.scores[2]==0,"Backspace symbol erases the last initial");
        high.step(Right);for(int i=0;i<8;++i)high.step(0);high.step(B);
        require(high.phase==UiPhase::TitleReturn&&high.scores[0]==11&&high.titleIntroMusic==-1,"End symbol stops music and starts return fade while preserving entered scores");
        for(int i=0;i<31;++i)high.step(UiStart);
        require(high.phase==UiPhase::TitleReturn&&isWhite(high.render()),"Return fade is white before title setup and ignores Start");
        high.step(UiStart);require(high.phase==UiPhase::TitleIntro&&high.phaseTicks==0,"Return skips copyright and enters initial title fade after 32 updates");
        for(int i=0;i<113;++i)high.step(UiStart);
        require(high.phase==UiPhase::Title&&high.scores[0]==11&&!high.campaign.active,"Title reopening completes without resetting high scores or accepting held Start");
        high.step(UiSelect);for(int i=0;i<80;++i)high.step(0);high.step(UiStart);require(high.scores[0]==11,"Starting a new campaign preserves session high scores");
        for(int player=0;player<2;++player){
            auto completed=std::make_unique<UiFlow>(assets);auto& c=*completed;
            c.campaign.start(true,4,3);c.campaign.current=player;
            if(player)c.campaign.players[0].lives=0;
            c.campaign.players[player].savings=999999;c.beginInstructions();c.step(UiStart);finishInstructionExit(c);
            c.finishStunt(7,0,0);finishResultFade(c);c.step(A);c.step(0);c.step(A);
            for(int i=0;i<544;++i)c.step(i%2?A:0);
            require(c.phase==UiPhase::Ending&&c.endingEnter==0,"Both players retain ending through the final hold update");
            const auto lastEnding=c.render();c.step(0);
            require(c.phase==UiPhase::NameEntry&&c.scoreRank==0&&c.nameEnter==64&&c.render()==lastEnding,"Both completed players reach high scores through the ending fade path");
            for(int i=0;i<64;++i)c.step(0);
            c.nameScroll=172;c.step(A);
            require(c.nameClosed&&c.pendingSound==9,"End symbol removes name-entry raster callbacks and queues the original effect");
            bool cleared=true;for(int y=120;y<128;++y)for(int x=0;x<Width;++x)cleared&=c.outroScene[y*Width+x]==0;
            require(cleared,"Outgoing name screen clears its alphabet row before the next transition");
            require(player?c.phase==UiPhase::TitleReturn:(c.phase==UiPhase::Instructions&&c.campaign.current==1&&c.instructionEnter==65),"Completed players either hand off to the surviving player or return to title");
        }
        fprintf(log,"PASS: %d UI flow/text assertions. Full original presentation timing remains pending.\n",count);fclose(log);return 0;
    }catch(const std::exception& e){fprintf(log,"FAIL after %d assertions: %s\n",count,e.what());fclose(log);return 1;}
}
}
