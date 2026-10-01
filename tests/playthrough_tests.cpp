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
 Game roofGame(shared);AirGame airGame(aa,shared);SkiGame skiGame(sa,shared);BombGame bombGame(ba,shared);CruiseGame cruiseGame(ca,shared);UiFlow ui(ua);ui.step(UiStart);
 int wins=0;
 for(int attempt=0;attempt<40&&ui.phase==UiPhase::Instructions;++attempt){ui.step(0);ui.step(UiStart);int d=ui.level,stage=ui.stunt,player=ui.campaign.current;int flags=0,money=0,seconds=0,extra=0,collected=0,elapsed=0;int buttons=0,left=0;
 switch(stage){case 0:roofGame.start(d,player);roofGame.secondTicks=ui.timerPhase;break;case 1:airGame.start(d,player);airGame.secondTicks=ui.timerPhase;airGame.randomState=(ui.ticks&255)<<8;break;case 2:skiGame.start(d,player);skiGame.secondTicks=ui.timerPhase;break;case 3:bombGame.start(d,player);bombGame.randomState=(ui.ticks&255)<<8;break;case 4:cruiseGame.start(d,player);cruiseGame.secondTicks=ui.timerPhase;cruiseGame.randomState=(ui.ticks&255)<<8;prepareCruiseTestInput(cruiseGame);break;}
 switch(stage){case 0:roofGame.ticks=ui.ticks;break;case 1:airGame.ticks=ui.ticks;prepareAirTestInput(airGame);break;case 2:skiGame.ticks=ui.ticks;break;case 3:bombGame.ticks=ui.ticks;break;case 4:cruiseGame.ticks=ui.ticks;break;}
 for(;elapsed<10000&&!flags;++elapsed){
  if(left==0){left=stage==3||(stage==1&&d==0)?1:stage==4?4:8;buttons=stage==0?roofTestInput(roofGame):stage==1?airTestInput(airGame):stage==2?skiTestInput(skiGame):stage==3?bombTestInput(bombGame):cruiseTestInput(cruiseGame);}--left;
  ui.step(buttons);
  int prior=(ui.ticks-1)&65535;
  switch(stage){case 0:roofGame.ticks=prior;break;case 1:airGame.ticks=prior;break;case 2:skiGame.ticks=prior;break;case 3:bombGame.ticks=prior;break;case 4:cruiseGame.ticks=prior;break;}
  switch(stage){case 0:roofGame.step(buttons);flags=roofGame.terminalFlags();money=roofGame.money;seconds=roofGame.seconds;ui.timerPhase=roofGame.secondTicks;break;case 1:airGame.step(buttons);flags=airGame.result;money=airGame.money;seconds=airGame.seconds;ui.timerPhase=airGame.secondTicks;extra=airGame.livesEarned;break;case 2:skiGame.step(buttons);flags=skiGame.result;money=skiGame.money;seconds=skiGame.seconds;ui.timerPhase=skiGame.secondTicks;collected=skiGame.collected;break;case 3:bombGame.step(buttons);flags=bombGame.result;money=bombGame.money;break;case 4:cruiseGame.step(buttons);flags=cruiseGame.result;money=cruiseGame.money;seconds=cruiseGame.seconds;ui.timerPhase=cruiseGame.secondTicks;extra=cruiseGame.extraLives;break;}
 }
 fprintf(log,"attempt=%d d=%d stage=%d elapsed=%d flags=%02x pay=%d seconds=%d global=%d\n",attempt,d,stage,elapsed,flags,money,seconds,ui.ticks);fflush(log);if(!flags){fclose(log);return 1;}
 ui.finishStunt(flags,money,seconds,extra,collected);if(flags&2)++wins;
 for(int t=0;t<3000&&ui.phase==UiPhase::Result;++t)ui.step(t%2?A:0);
 if(ui.phase==UiPhase::Ending){fprintf(log,"ENDING wins=%d savings=%d lives=%d\n",wins,ui.campaign.players[0].savings,ui.campaign.players[0].lives);fclose(log);return wins==20?0:1;}
 }
 fprintf(log,"STOP wins=%d phase=%d\n",wins,(int)ui.phase);fclose(log);return 1;
}

}
