#include "game.h"
#include "air.h"
#include "ski.h"
#include "bomb.h"
#include "cruise.h"
#include "ui.h"
#include <cstdio>
#include <memory>
#include <type_traits>
namespace ticd {
int roofTestInput(const Game&);
int airTestInput(const AirGame&);
void prepareAirTestInput(const AirGame&);
int skiTestInput(const SkiGame&);
int bombTestInput(const BombGame&);
int cruiseTestInput(const CruiseGame&);
void prepareCruiseTestInput(const CruiseGame&);
template<class Stunt> bool verifyStuntOutroHud(Stunt& game,const UiAssets& uiAssets){
 game.start(0);game.publishVideo();game.render(false);
 UiFlow flow(uiAssets);flow.campaign.start(false);flow.phase=UiPhase::Playing;
 flow.outroScene=game.screen;flow.finishStunt(3,1234,0);
 game.money=1234;game.transferRemaining=8;game.transferState=1;
 const auto player=game.entities[0];int seconds=0,ticks=game.ticks;
 if constexpr(!std::is_same_v<Stunt,BombGame>)seconds=game.seconds;
 flow.refreshStuntOutro(game);if(game.hudCursor!=0)return false;
 for(int n=0;n<32;++n){flow.step(0);flow.refreshStuntOutro(game);}
 // Even the 13-column HUD must publish the last score within two cycles.
 if(game.hudMap[game.assets.hudColumns[1]]!=0xf7||game.transferRemaining!=8||game.transferState!=1||
    game.entities[0].x!=player.x||game.entities[0].y!=player.y||game.ticks!=ticks)return false;
 if constexpr(!std::is_same_v<Stunt,BombGame>)if(game.seconds!=seconds)return false;
 int cursor=game.hudCursor;flow.step(0);flow.refreshStuntOutro(game);
 if(game.hudCursor!=cursor||flow.phase!=UiPhase::Result)return false;
 game.start(0);return true;
}
template<class Stunt> bool verifyPausePublication(Stunt& game,const UiAssets& uiAssets){
 game.start(0);game.render(false);auto before=game.screen;
 Frame marker;marker.meta={};SpritePiece piece;piece.colors.fill(before[40*Width+24]==3?1:3);marker.pieces.push_back(piece);
 game.sprites.add(marker,24,40,0);game.transferState=1;
 // Use a real two-update resource, rather than an impossible eight-chunk
 // transfer for a frame whose payload may contain fewer chunks.
 game.transferFrame=0;
 while(game.assets.transferChunks[game.transferFrame]<=4||game.assets.transferChunks[game.transferFrame]>8)++game.transferFrame;
 int chunks=game.assets.transferChunks[game.transferFrame];game.transferRemaining=chunks;
 game.transferFlags=game.entities[0].flags;
 // Isolate the pending display transfer from new requests made by intro logic.
 game.entities[0].handler=decltype(game.entities[0].handler)::Idle;
 if constexpr(!std::is_same_v<Stunt,BombGame>)game.mapTransfer=false;
 int x=game.entities[0].x,y=game.entities[0].y;
 UiFlow flow(uiAssets);flow.phase=UiPhase::Playing;flow.gameplayFade=8;flow.ticks=1;
 game.paused=true;flow.gameplayPaused=game.videoTickPrepared;flow.step(0);flow.stepStunt(game);game.render(false);
 if(game.screen==before||!game.videoTickPrepared||game.transferRemaining!=chunks-4||game.hudCursor!=1||flow.gameplayFade!=7)return false;
 for(int n=0;n<3;++n){flow.gameplayPaused=game.videoTickPrepared;flow.step(0);flow.stepStunt(game);}
 if(game.entities[0].x!=x||game.entities[0].y!=y||game.transferRemaining!=chunks-4||game.hudCursor!=1||flow.gameplayFade!=7)return false;
 game.paused=false;flow.gameplayPaused=game.videoTickPrepared;flow.step(0);flow.stepStunt(game);
 if(game.videoTickPrepared||game.transferRemaining!=chunks-4||game.hudCursor!=1||flow.gameplayFade!=7)return false;
 if constexpr(!std::is_same_v<Stunt,BombGame>)game.mapTransfer=false;
 flow.gameplayPaused=game.videoTickPrepared;flow.step(0);flow.stepStunt(game);
 if(game.transferRemaining||game.hudCursor!=2)return false;
 game.start(0);return !game.videoTickPrepared;
}
template<class Stunt> bool verifyVideoPublication(Stunt& game){
 game.start(0);game.sprites=SpriteLayer(false);game.publishVideo();game.render(false);
 Frame marker;marker.meta={};SpritePiece piece;piece.colors.fill(game.screen[40*Width+24]==3?1:3);marker.pieces.push_back(piece);
 game.sprites.add(marker,24,40,0);game.publishVideo();game.render(false);auto visible=game.screen;
 game.sprites=SpriteLayer(false);game.sprites.add(marker,56,40,0);game.render(false);
 if(game.screen!=visible)return false;
 game.beginVideoTick();game.render(false);if(game.screen==visible)return false;
 game.start(0);return true;
}
template<class Stunt> bool verifyAnimationResume(Stunt& game){
 game.start(0);auto& p=game.entities[0];p.anim=1;p.animDone=false;p.delay=0;p.period=2;p.frame=0;
 int x=p.x;
 // Movement and sound precede a jump to a dynamic frame. The original
 // frame wait exits without saving the cursor; all three must replay.
 for(int tick=1;tick<=3;++tick){game.transferState=1;game.pendingSound=-1;game.animate(0);
  if(p.x!=x+tick*5||game.pendingSound!=13||!p.frameWaiting||p.anim!=1||p.delay)return false;
  p.frame=0;
 }
 game.transferState=2;game.pendingSound=-1;game.animate(0);
 if(p.x!=x+20||game.pendingSound!=13||p.frameWaiting||p.anim!=8||p.delay!=2)return false;
 game.pendingSound=-1;game.animate(0);game.animate(0);
 if(p.delay||p.animDone||p.x!=x+20||game.pendingSound!=-1)return false;
 game.animate(0);return p.animDone&&p.anim==8&&p.x==x+20;
}
// Native integration harness: real outcomes and carried timer/random phase.
// Predictive pilots provide only button inputs; this is not an original-game oracle.
// Instructions/results are skipped, and one UI tick separates start and first play.
int runPlaythroughTests(const Assets& shared,const AirAssets& aa,const SkiAssets& sa,const BombAssets& ba,const CruiseAssets& ca,const UiAssets& ua){
 FILE* log=fopen("playthrough-test.txt","w");if(!log)return 2;
 {
  std::vector<Command> script(9);script[1]={2,5,0,0,2};script[2]={19,13,0,0,3};
  script[3]={10,6,0,0,0};script[6]={4,1,0,0,7};script[7]={1,0,0,0,8};script[8]={0,0,0,0,0};
  auto roof=std::make_unique<Assets>(shared);roof->commands=script;Game r(*roof);
  auto air=std::make_unique<AirAssets>(aa);air->commands=script;AirGame a(*air,shared);
  auto ski=std::make_unique<SkiAssets>(sa);ski->commands=script;SkiGame s(*ski,shared);
  auto bomb=std::make_unique<BombAssets>(ba);bomb->commands=script;BombGame b(*bomb,shared);
  auto cruise=std::make_unique<CruiseAssets>(ca);cruise->commands=script;CruiseGame c(*cruise,shared);
  if(!verifyAnimationResume(r)||!verifyAnimationResume(a)||!verifyAnimationResume(s)||!verifyAnimationResume(b)||!verifyAnimationResume(c)){
   fprintf(log,"FAIL: animation script block resume\n");fclose(log);return 1;}
  fprintf(log,"PASS: saved animation block, repeated side effects and delay commit for all five stunts\n");
 }
 Game roofGame(shared);AirGame airGame(aa,shared);SkiGame skiGame(sa,shared);BombGame bombGame(ba,shared);CruiseGame cruiseGame(ca,shared);
 if(!verifyVideoPublication(roofGame)||!verifyVideoPublication(airGame)||!verifyVideoPublication(skiGame)||!verifyVideoPublication(bombGame)||!verifyVideoPublication(cruiseGame)){
  fprintf(log,"FAIL: prepared/visible sprite publication\n");fclose(log);return 1;}
 fprintf(log,"PASS: prepared sprite changes become visible only on the next display update in all five stunts\n");
 if(!verifyPausePublication(roofGame,ua)||!verifyPausePublication(airGame,ua)||!verifyPausePublication(skiGame,ua)||!verifyPausePublication(bombGame,ua)||!verifyPausePublication(cruiseGame,ua)){
  fprintf(log,"FAIL: pause entry/resume display boundary\n");fclose(log);return 1;}
 fprintf(log,"PASS: pause publishes one display update, preserves pending transfers, freezes gameplay and resumes without a duplicate display update in all five stunts\n");
 if(!verifyStuntOutroHud(roofGame,ua)||!verifyStuntOutroHud(airGame,ua)||!verifyStuntOutroHud(skiGame,ua)||!verifyStuntOutroHud(bombGame,ua)||!verifyStuntOutroHud(cruiseGame,ua)){
  fprintf(log,"FAIL: outgoing HUD refresh without gameplay/transfer updates\n");fclose(log);return 1;}
 fprintf(log,"PASS: final score reaches the HUD during the outgoing fade without entity, timer or resource updates in all five stunts\n");
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
 for(int scenario=0;scenario<3;++scenario){
 UiFlow ui(ua);ui.twoPlayers=scenario!=0;ui.step(UiStart);for(int wait=0;wait<66;++wait)ui.step(0);
 std::array<int,2> wins{},failures{},endings{};int expectedPlayer=0;
 fprintf(log,"SCENARIO %d: %s\n",scenario,scenario==0?"single player":scenario==1?"both players complete":"player one eliminated, player two completes");
 for(int attempt=0;attempt<100&&ui.phase==UiPhase::Instructions;++attempt){while(ui.instructionEnter)ui.step(0);ui.step(0);ui.step(UiStart);for(int wait=0;wait<33;++wait)ui.step(0);int d=ui.level,stage=ui.stunt,player=ui.campaign.current;int flags=0,money=0,seconds=0,extra=0,collected=0,elapsed=0;int buttons=0,left=0;
 if(player!=expectedPlayer){fprintf(log,"FAIL: wrong player handoff\n");fclose(log);return 1;}
 const auto other=ui.campaign.players[player^1];bool idle=scenario==2&&player==0;
 switch(stage){case 0:roofGame.start(d,player);roofGame.secondTicks=ui.timerPhase;break;case 1:airGame.start(d,player);airGame.secondTicks=ui.timerPhase;airGame.randomState=(ui.ticks&255)<<8;break;case 2:skiGame.start(d,player);skiGame.secondTicks=ui.timerPhase;break;case 3:bombGame.start(d,player);bombGame.randomState=(ui.ticks&255)<<8;break;case 4:cruiseGame.start(d,player);cruiseGame.secondTicks=ui.timerPhase;cruiseGame.randomState=(ui.ticks&255)<<8;prepareCruiseTestInput(cruiseGame);break;}
 switch(stage){case 0:roofGame.ticks=ui.ticks;break;case 1:airGame.ticks=ui.ticks;prepareAirTestInput(airGame);break;case 2:skiGame.ticks=ui.ticks;break;case 3:bombGame.ticks=ui.ticks;break;case 4:cruiseGame.ticks=ui.ticks;break;}
 for(;elapsed<10000&&!flags;++elapsed){
  if(left==0){left=stage==3||(stage==1&&d==0)?1:stage==4?4:8;buttons=idle?0:stage==0?roofTestInput(roofGame):stage==1?airTestInput(airGame):stage==2?skiTestInput(skiGame):stage==3?bombTestInput(bombGame):cruiseTestInput(cruiseGame);}--left;
  ui.step(buttons);
  switch(stage){case 0:ui.stepStunt(roofGame);flags=roofGame.terminalFlags();money=roofGame.money;seconds=roofGame.seconds;ui.timerPhase=roofGame.secondTicks;break;case 1:ui.stepStunt(airGame);flags=airGame.result;money=airGame.money;seconds=airGame.seconds;ui.timerPhase=airGame.secondTicks;extra=airGame.livesEarned;break;case 2:ui.stepStunt(skiGame);flags=skiGame.result;money=skiGame.money;seconds=skiGame.seconds;ui.timerPhase=skiGame.secondTicks;collected=skiGame.collected;break;case 3:ui.stepStunt(bombGame);flags=bombGame.result;money=bombGame.money;break;case 4:ui.stepStunt(cruiseGame);flags=cruiseGame.result;money=cruiseGame.money;seconds=cruiseGame.seconds;ui.timerPhase=cruiseGame.secondTicks;extra=cruiseGame.extraLives;break;}
 }
 fprintf(log,"attempt=%d player=%d d=%d stage=%d elapsed=%d flags=%02x pay=%d seconds=%d global=%d\n",attempt,player,d,stage,elapsed,flags,money,seconds,ui.ticks);fflush(log);if(!flags){fprintf(log,"FAIL: no terminal result\n");fclose(log);return 1;}
 if(stage==4)ui.randomState=cruiseGame.randomState;else if(stage==3)ui.randomState=bombGame.randomState;else if(stage==1)ui.randomState=airGame.randomState;
 ui.finishStunt(flags,money,seconds,extra,collected);if(flags&2)++wins[player];else ++failures[player];
 const auto& unchanged=ui.campaign.players[player^1];
 if(unchanged.savings!=other.savings||unchanged.day!=other.day||unchanged.difficulty!=other.difficulty||unchanged.lives!=other.lives||unchanged.completed!=other.completed){fprintf(log,"FAIL: settlement changed the other player\n");fclose(log);return 1;}
 expectedPlayer=other.lives?player^1:player;
 for(int t=0;t<3000&&ui.phase!=UiPhase::Instructions&&ui.phase!=UiPhase::Title;++t){
  auto before=ui.phase;int input=t%2?A:0;
  if(ui.phase==UiPhase::NameEntry){
   // Select End using actual name-entry buttons, without changing UI state.
   input=0;if(!ui.nameEnter){int letter=((ui.nameScroll+76)&248)>>3;
    if(!ui.nameMotion&&letter!=31)input=Left;
    else if(!ui.nameMotion&&!(ui.previous&A))input=A;}
  }
  ui.step(input);if(before!=UiPhase::Ending&&ui.phase==UiPhase::Ending)++endings[player];
 }
 }
 bool passed=ui.phase==UiPhase::Title&&!ui.campaign.active&&
  wins[0]==(scenario==2?0:20)&&wins[1]==(scenario==0?0:20)&&
  (scenario!=0||failures[0]==0)&&(scenario!=2||failures[0]==5)&&
  endings[0]==(scenario==2?0:1)&&endings[1]==(scenario==0?0:1);
 fprintf(log,"%s scenario=%d wins=%d/%d failures=%d/%d endings=%d/%d savings=%d/%d phase=%d\n",passed?"PASS":"FAIL",scenario,wins[0],wins[1],failures[0],failures[1],endings[0],endings[1],ui.campaign.players[0].savings,ui.campaign.players[1].savings,(int)ui.phase);fflush(log);
 if(!passed){fclose(log);return 1;}
 }
 fclose(log);return 0;
}

}
