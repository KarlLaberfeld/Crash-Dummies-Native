#include "game.h"
#include "air.h"
#include "ski.h"
#include "bomb.h"
#include "cruise.h"
#include "ui.h"
#include <cstdio>
namespace ticd {
int roofTestInput(const Game&);
int airTestInput(const AirGame&);
void prepareAirTestInput(const AirGame&);
int skiTestInput(const SkiGame&);
int bombTestInput(const BombGame&);
int cruiseTestInput(const CruiseGame&);
void prepareCruiseTestInput(const CruiseGame&);
// Native integration harness: real outcomes and carried timer/random phase.
// Predictive pilots provide only button inputs; this is not an original-game oracle.
// Instructions/results are skipped, and one UI tick separates start and first play.
int runPlaythroughTests(const Assets& shared,const AirAssets& aa,const SkiAssets& sa,const BombAssets& ba,const CruiseAssets& ca,const UiAssets& ua){
 FILE* log=fopen("playthrough-test.txt","w");if(!log)return 2;
 Game roofGame(shared);AirGame airGame(aa,shared);SkiGame skiGame(sa,shared);BombGame bombGame(ba,shared);CruiseGame cruiseGame(ca,shared);UiFlow ui(ua);ui.step(UiStart);for(int wait=0;wait<66;++wait)ui.step(0);
 auto verifyBoundary=[&](auto& game){
  game.start(0);UiFlow flow(ua);flow.campaign.start(false);flow.beginInstructions();
  flow.step(UiStart|A);for(int t=0;t<33;++t)flow.step(A);
  int before=game.ticks;flow.stepStunt(game);
  if(game.ticks!=before||flow.phase!=UiPhase::Playing||flow.gameplayFade!=8)return false;
  flow.step(A);flow.stepStunt(game);
  if(game.ticks!=flow.ticks||game.held!=A||game.pressed!=0)return false;
  flow.step(0);flow.stepStunt(game);flow.step(A);flow.stepStunt(game);
  if(game.pressed!=A)return false;
  game.paused=true;flow.gameplayPaused=true;flow.step(B);flow.stepStunt(game);
  flow.step(B);flow.stepStunt(game);game.paused=false;flow.gameplayPaused=false;
  flow.step(B);flow.stepStunt(game);if(game.pressed!=0||game.held!=B||game.ticks!=flow.ticks)return false;
  flow.step(0);flow.stepStunt(game);flow.step(B);flow.stepStunt(game);
  return game.pressed==B;
 };
 if(!verifyBoundary(roofGame)||!verifyBoundary(airGame)||!verifyBoundary(skiGame)||!verifyBoundary(bombGame)||!verifyBoundary(cruiseGame)){
  fprintf(log,"FAIL: campaign input/start/pause boundary\n");fclose(log);return 1;}
 fprintf(log,"PASS: start wait and held/fresh input across entry and pause for all five stunts\n");
 int wins=0;
 for(int attempt=0;attempt<40&&ui.phase==UiPhase::Instructions;++attempt){while(ui.instructionEnter)ui.step(0);ui.step(0);ui.step(UiStart);for(int wait=0;wait<33;++wait)ui.step(0);int d=ui.level,stage=ui.stunt,player=ui.campaign.current;int flags=0,money=0,seconds=0,extra=0,collected=0,elapsed=0;int buttons=0,left=0;
 switch(stage){case 0:roofGame.start(d,player);roofGame.secondTicks=ui.timerPhase;break;case 1:airGame.start(d,player);airGame.secondTicks=ui.timerPhase;airGame.randomState=(ui.ticks&255)<<8;break;case 2:skiGame.start(d,player);skiGame.secondTicks=ui.timerPhase;break;case 3:bombGame.start(d,player);bombGame.randomState=(ui.ticks&255)<<8;break;case 4:cruiseGame.start(d,player);cruiseGame.secondTicks=ui.timerPhase;cruiseGame.randomState=(ui.ticks&255)<<8;prepareCruiseTestInput(cruiseGame);break;}
 switch(stage){case 0:roofGame.ticks=ui.ticks;break;case 1:airGame.ticks=ui.ticks;prepareAirTestInput(airGame);break;case 2:skiGame.ticks=ui.ticks;break;case 3:bombGame.ticks=ui.ticks;break;case 4:cruiseGame.ticks=ui.ticks;break;}
 for(;elapsed<10000&&!flags;++elapsed){
  if(left==0){left=stage==3||(stage==1&&d==0)?1:stage==4?4:8;buttons=stage==0?roofTestInput(roofGame):stage==1?airTestInput(airGame):stage==2?skiTestInput(skiGame):stage==3?bombTestInput(bombGame):cruiseTestInput(cruiseGame);}--left;
  ui.step(buttons);
  switch(stage){case 0:ui.stepStunt(roofGame);flags=roofGame.terminalFlags();money=roofGame.money;seconds=roofGame.seconds;ui.timerPhase=roofGame.secondTicks;break;case 1:ui.stepStunt(airGame);flags=airGame.result;money=airGame.money;seconds=airGame.seconds;ui.timerPhase=airGame.secondTicks;extra=airGame.livesEarned;break;case 2:ui.stepStunt(skiGame);flags=skiGame.result;money=skiGame.money;seconds=skiGame.seconds;ui.timerPhase=skiGame.secondTicks;collected=skiGame.collected;break;case 3:ui.stepStunt(bombGame);flags=bombGame.result;money=bombGame.money;break;case 4:ui.stepStunt(cruiseGame);flags=cruiseGame.result;money=cruiseGame.money;seconds=cruiseGame.seconds;ui.timerPhase=cruiseGame.secondTicks;extra=cruiseGame.extraLives;break;}
 }
 fprintf(log,"attempt=%d d=%d stage=%d elapsed=%d flags=%02x pay=%d seconds=%d global=%d\n",attempt,d,stage,elapsed,flags,money,seconds,ui.ticks);fflush(log);if(!flags){fclose(log);return 1;}
 if(stage==4)ui.randomState=cruiseGame.randomState;else if(stage==3)ui.randomState=bombGame.randomState;else if(stage==1)ui.randomState=airGame.randomState;
 ui.finishStunt(flags,money,seconds,extra,collected);if(flags&2)++wins;
 for(int t=0;t<3000&&(ui.phase==UiPhase::StuntOutro||ui.phase==UiPhase::Result);++t)ui.step(t%2?A:0);
 if(ui.phase==UiPhase::Ending){fprintf(log,"ENDING wins=%d savings=%d lives=%d\n",wins,ui.campaign.players[0].savings,ui.campaign.players[0].lives);fclose(log);return wins==20?0:1;}
 }
 fprintf(log,"STOP wins=%d phase=%d\n",wins,(int)ui.phase);fclose(log);return 1;
}

}
