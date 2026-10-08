#pragma once
#include "air_following_setup.h"
#include "air_placement_clock.h"
#include "air_scene_clock.h"

namespace ticd {
// Following Air entry inherits semantic animation blocks and the partial
// second from the previous native Air stunt. Result/instruction owners do not
// clear them. Neither original states nor reference times enter this handoff.
inline void airFollowingAirHandoff(AirGame& game,const AirGame& preceding,const AirFollowingSetup& state){
    const auto& c=state.instruction.map.campaign;const auto& t=c.timing;
    if(state.stage!=1||state.display!=4||state.stat!=4||state.ready||state.pendingRequests||state.hudCursor!=2||
       &game==&preceding||!(preceding.result&1)||(preceding.result&6)||preceding.animationFaults||preceding.secondTicks<0||preceding.secondTicks>=60||
       c.player!=preceding.playerNumber||state.difficulty!=preceding.difficulty)
        throw std::runtime_error("Unowned following Air gameplay handoff");
    game.start(state.difficulty,c.player);game.measureWork=true;
    if(game.cameraX!=state.cameraX||game.cameraY!=state.cameraY)throw std::runtime_error("Following Air camera disagrees with native level");
    for(int i=0;i<16;++i){auto& e=game.entities[i];const auto& old=preceding.entities[i];
        e.anim=old.anim;e.delay=old.delay;e.period=old.period;e.loop=old.loop;e.loopStart=old.loopStart;
        if(!e.alive){e.animDone=old.animDone;e.frameWaiting=old.frameWaiting;}
    }
    game.secondTicks=preceding.secondTicks;game.ticks=t.tick;game.randomState=state.randomState;
    game.hudCursor=state.hudCursor;game.displayFadeRemaining=state.fadeRemaining;
    game.reverseSprites=preceding.reverseSprites;game.sprites=SpriteLayer(game.reverseSprites);
    auto decode=[](int raw){return ((raw&1)?A:0)|((raw&2)?B:0)|((raw&16)?Right:0)|
        ((raw&32)?Left:0)|((raw&64)?Up:0)|((raw&128)?Down:0);};
    game.held=decode(t.input.held);game.previous=decode(t.input.previous);game.pressed=decode(t.input.pressed);game.publishVideo();
}

// Bounded first following Air update and next counter wait. The actor/resource
// body must be quiet: a crossing requires a separately qualified owner. Scene
// and placement work use the existing native completion algorithms.
template<class Boundary,class Service,class Interrupt>
AirFollowingSetup airFollowingAirFirstUpdate(AirFollowingSetup state,AirGame& game,NativeAudio& sound,
    Boundary&& boundary,Service&& service,Interrupt&& interrupt,std::function<int()> sampleInput={}){
    auto& t=state.instruction.map.campaign.timing;
    if(state.stage!=1||state.ready||game.result||!game.measureWork||game.entities[0].handler!=AirHandler::Intro||
       game.transferState||game.transferRemaining||game.pendingSound!=-1||!sound.enabled||sound.pendingEffect!=-1||((t.input.pressed&8)&&!state.entryPauseComplete))
        throw std::runtime_error("Unowned first following Air update");
    AirClock clock;clock.now=t.end;clock.nextStat=t.nextStat;clock.nextVBlank=t.nextVBlank;clock.displays=t.displays;clock.statServices=t.stats;
    clock.interrupt=[&](const char* kind,int64_t cycle,AirIrqOwner owner){interrupt(kind,cycle,owner);};
    clock.objectDisable=[&](int64_t,AirIrqOwner){state.lcdc&=~2;};
    auto point=[&](const char* name){boundary(name,clock.now,state,game);};
    auto display=[&](bool ready){
        if(!ready||state.ready!=1)throw std::runtime_error("First following Air body needs an interrupted-work owner");
        t.input.sample(sampleInput?sampleInput():t.input.held);
        if(t.input.held<0||t.input.held>255||(t.input.held&15)==15)throw std::runtime_error("Unowned restarted Air reset input");
        int tick=game.ticks;game.displayTick(true);state.lcdc|=2;sound.tick();
        if(game.pendingSound!=-1||game.displayWorkCycles<0||sound.effectWorkCycles<0||sound.musicWorkCycles<0)
            throw std::runtime_error("Unowned first following Air display/audio");
        service(clock.displays,clock.now+20,tick,game.displayWorkCycles,sound.effectWorkCycles,sound.musicWorkCycles,t.input);
        return 1592+game.displayWorkCycles+sound.effectWorkCycles+sound.musicWorkCycles;
    };
    auto quiet=[&](int cost){
        if(cost<0||clock.now+cost>=std::min(clock.nextStat,clock.nextVBlank))throw std::runtime_error("Unowned interrupted following Air body");
        clock.work(cost,display,false);
    };
    point("begin");quiet(96);point("savedPlayer");
    const auto priorSprites=game.sprites;bool priorMap=game.mapTransfer,priorReverse=game.reverseSprites;int priorCamera=game.lastMapCamera;
    game.updateGame(game.held,true,true);const auto visibleEntities=game.entities;
    game.entities=game.spriteInputEntities;bool preparedMap=game.mapTransfer,preparedReverse=game.reverseSprites;
    game.sprites=priorSprites;game.reverseSprites=priorReverse;game.mapTransfer=priorMap;game.lastMapCamera=priorCamera;
    if(game.transferState||game.transferRemaining||game.pendingSound!=-1||game.animationFaults||game.entityWorkCycles<96)
        throw std::runtime_error("Unowned following Air first actor/resource outcome");
    quiet(game.entityWorkCycles-96);point("entitiesDone");
    int resource=0;for(int cost:game.resourceCompletionCosts){resource+=cost;quiet(cost);}
    if(resource!=game.resourceWorkCycles)throw std::runtime_error("Incomplete following Air resource work");point("sprites");
    game.entities=visibleEntities;game.reverseSprites=preparedReverse;game.sprites=SpriteLayer(preparedReverse);game.sprites.slots=priorSprites.slots;
    int sprites=airSpriteClock(game,clock,display);
    if(sprites!=game.spriteWorkCycles)throw std::runtime_error("Incomplete following Air sprite work");point("spritesDone");
    int clear=airSpriteClearClock(game.sprites,clock,display);
    if(clear!=game.clearWorkCycles)throw std::runtime_error("Incomplete following Air clear work");point("mapCallback");
    AirMapPublication publication;int map=airMapClock(clock,priorCamera,game.cameraY,game.mapTransfer,display,nullptr,nullptr,&publication,&game);
    if(map!=game.mapWorkCycles||game.mapTransfer!=preparedMap)throw std::runtime_error("Incomplete following Air map work");
    game.lastMapCamera=game.cameraY;if(preparedMap)state.mapScratch=256+8*publication.destination;point("placements");
    AirPlacementRange range;airPlacementClock(game,clock,range,display);point("done");
    if(game.result)throw std::runtime_error("First following Air update unexpectedly ended the stunt");
    clock.atomicWork(16,[]{},display,false);clock.atomicWork(4,[]{},display,false);clock.atomicWork(12,[]{},display,false);point("backEdge");
    clock.atomicWork(8,[]{},display,false);clock.atomicWork(12,[&]{state.ready=1;},display,true);clock.wait(display,true);
    clock.atomicWork(4,[]{},display,true);clock.atomicWork(12,[&]{state.ready=0;},display,false);
    int fresh=0;clock.accessWork(12,8,[&]{fresh=t.input.pressed;},display,false);clock.atomicWork(8,[]{},display,false);
    if(fresh&8)throw std::runtime_error("Following Air next update requires its pause owner");clock.atomicWork(12,[]{},display,false);point("end");
    t.end=clock.now;t.tick=game.ticks;t.nextStat=clock.nextStat;t.nextVBlank=clock.nextVBlank;t.displays=clock.displays;t.stats=clock.statServices;
    state.hudCursor=game.hudCursor;state.fadeRemaining=game.displayFadeRemaining;return state;
}
}
