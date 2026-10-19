#pragma once
#include "air_following_setup.h"
#include "air_placement_clock.h"
#include "air_scene_clock.h"
#include "audio_work.h"

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
    // 0387 explicitly clears the sprite allocation selector after masked stage
    // initialization. Animation blocks survive; this selector does not.
    game.reverseSprites=false;game.sprites=SpriteLayer(false);
    auto decode=[](int raw){return ((raw&1)?A:0)|((raw&2)?B:0)|((raw&16)?Right:0)|
        ((raw&32)?Left:0)|((raw&64)?Up:0)|((raw&128)?Down:0);};
    game.held=decode(t.input.held);game.previous=decode(t.input.previous);game.pressed=decode(t.input.pressed);game.publishVideo();
}

// Bounded following Air quiet update and next counter wait. The actor/resource
// body must be quiet: a crossing requires a separately qualified owner. Scene
// and placement work can accept services at their identified completion
// boundaries; persistent source-owned row storage preserves partial publication. The
// explicit terminal extent retains the busy gate and omits the next input test.
template<class Boundary,class Service,class Interrupt>
AirFollowingSetup airFollowingAirQuietUpdate(AirFollowingSetup state,AirGame& game,NativeAudio& sound,
    Boundary&& boundary,Service&& service,Interrupt&& interrupt,std::function<int()> sampleInput={},bool terminal=false,
    std::function<void(const char*,unsigned,int64_t,const AirFollowingSetup&,const AirGame&)> mapSnapshot={}){
    auto& t=state.instruction.map.campaign.timing;
    if(state.stage!=1||state.ready||game.result||!game.measureWork||!game.entities[0].alive||
       game.transferState<0||game.transferState>2||game.transferRemaining<0||
       (game.transferState==1)!=(game.transferRemaining>0)||
       (game.transferState&& (game.transferFrame<0||game.transferFrame>=12))||
       (game.transferState&&game.transferRemaining>game.assets.transferChunks[game.transferFrame])||
       game.pendingSound!=-1||!sound.enabled||sound.pendingEffect!=-1||((t.input.pressed&8)&&!state.entryPauseComplete))
        throw std::runtime_error("Unowned following Air quiet update");
    AirClock clock;clock.now=t.end;clock.nextStat=t.nextStat;clock.nextVBlank=t.nextVBlank;clock.displays=t.displays;clock.statServices=t.stats;
    clock.interrupt=[&](const char* kind,int64_t cycle,AirIrqOwner owner){interrupt(kind,cycle,owner);};
    clock.objectDisable=[&](int64_t,AirIrqOwner){state.lcdc&=~2;};
    if(!state.rowPublicationReady){
        state.rowPublication.initialize(game,state.instruction.backgroundOwned?&state.instruction.background:nullptr);state.rowPublicationReady=true;
        if(mapSnapshot)mapSnapshot("startup",clock.displays,clock.now,state,game);
    }
    auto point=[&](const char* name){boundary(name,clock.now,state,game);};
    int scenePhase=0;bool rowFlagOwned=false,rowReady=false;AirPlacementRange range;
    auto display=[&](bool ready){
        const bool ownedBody=scenePhase==1||scenePhase==2||scenePhase==4||scenePhase==5||
            (scenePhase==3&&rowFlagOwned&&state.rowPublicationReady&&(rowReady||state.instruction.backgroundOwned));
        if(int(ready)!=state.ready||(!ready&&!ownedBody))throw std::runtime_error("Following Air body needs an interrupted-work owner");
        t.input.sample(sampleInput?sampleInput():t.input.held);
        if(t.input.held<0||t.input.held>255||(t.input.held&15)==15)throw std::runtime_error("Unowned restarted Air reset input");
        int tick=game.ticks;bool refreshRangeScratch=game.hudCursor==12;
        int64_t mapEntry=clock.now+20+180+704+280+116;
        if(mapSnapshot)mapSnapshot("before",clock.displays,mapEntry,state,game);
        if(game.mapTransfer)state.rowPublication.publish();
        if(mapSnapshot)mapSnapshot("after",clock.displays,mapEntry+24+(game.mapTransfer?736:40),state,game);
        game.displayTick(ready);state.lcdc|=2;
        // The HUD progress division shares the placement scan's low-range
        // scratch. A display can complete between its individual reads.
        if(refreshRangeScratch)range.low=0;
        if(game.pendingSound>=0)sound.queueEffect(game.pendingSound);game.pendingSound=-1;sound.tick();
        if(game.displayWorkCycles<0||sound.effectWorkCycles<0||sound.musicWorkCycles<0)
            throw std::runtime_error("Unowned following Air display/audio");
        service(clock.displays,clock.now+20,tick,game.displayWorkCycles,sound.effectWorkCycles,sound.musicWorkCycles,t.input);
        return 1592+game.displayWorkCycles+sound.effectWorkCycles+sound.musicWorkCycles;
    };
    auto quiet=[&](int cost){
        if(cost<0||clock.now+cost>=std::min(clock.nextStat,clock.nextVBlank))throw std::runtime_error("Unowned interrupted following Air body");
        clock.work(cost,display,false);
    };
    point("begin");quiet(96);point("savedPlayer");
    const auto priorSprites=game.sprites;bool priorMap=game.mapTransfer,priorReverse=game.reverseSprites;int priorCamera=game.lastMapCamera;
    const int priorTransfer=game.transferState,priorRemaining=game.transferRemaining,priorFrame=game.transferFrame,priorFlags=game.transferFlags;
    auto decode=[](int raw){return ((raw&1)?A:0)|((raw&2)?B:0)|((raw&16)?Right:0)|
        ((raw&32)?Left:0)|((raw&64)?Up:0)|((raw&128)?Down:0);};
    game.previous=decode(t.input.previous);game.updateGame(decode(t.input.held),true,true);const auto visibleEntities=game.entities;
    const auto resourceEntities=game.spriteInputEntities;
    const int preparedTransfer=game.transferState,preparedRemaining=game.transferRemaining,preparedFrame=game.transferFrame,preparedFlags=game.transferFlags;
    game.entities=game.resourceInputEntities;bool preparedMap=game.mapTransfer,preparedReverse=game.reverseSprites;
    game.transferState=priorTransfer;game.transferRemaining=priorRemaining;game.transferFrame=priorFrame;game.transferFlags=priorFlags;
    game.sprites=priorSprites;game.reverseSprites=priorReverse;game.mapTransfer=priorMap;game.lastMapCamera=priorCamera;
    if(game.pendingSound<-1||game.pendingSound>=26||game.animationFaults||game.entityWorkCycles<96)
        throw std::runtime_error("Unowned following Air quiet actor/resource outcome");
    quiet(game.entityWorkCycles-96);point("entitiesDone");
    int resource=0;for(int cost:game.resourceCompletionCosts){resource+=cost;quiet(cost);}
    if(resource!=game.resourceWorkCycles)throw std::runtime_error("Incomplete following Air resource work");
    // The entire callback is quiet here. Commit its native queue/frame outcome
    // only after completion, so entitiesDone still exposes the requested pose.
    // Any interrupt within the callback remains an unqualified hard boundary.
    game.entities=resourceEntities;game.transferState=preparedTransfer;game.transferRemaining=preparedRemaining;
    game.transferFrame=preparedFrame;game.transferFlags=preparedFlags;point("sprites");
    game.entities=visibleEntities;game.reverseSprites=preparedReverse;game.sprites=SpriteLayer(preparedReverse);game.sprites.slots=priorSprites.slots;
    scenePhase=1;
    int sprites=airSpriteClock(game,clock,display);
    if(sprites!=game.spriteWorkCycles)throw std::runtime_error("Incomplete following Air sprite work");point("spritesDone");
    scenePhase=2;int clear=airSpriteClearClock(game.sprites,clock,display);
    if(clear!=game.clearWorkCycles)throw std::runtime_error("Incomplete following Air clear work");point("mapCallback");
    scenePhase=3;int map=airMapClock(clock,priorCamera,game.cameraY,game.mapTransfer,display,&rowFlagOwned,&rowReady,&state.rowPublication,&game);
    if(map!=game.mapWorkCycles||game.mapTransfer!=preparedMap)throw std::runtime_error("Incomplete following Air map work");
    game.lastMapCamera=game.cameraY;if(preparedMap)state.mapScratch=256+8*state.rowPublication.destination;
    else state.mapScratch&=255; // C00D is also the row-publication gate.
    point("placements");
    scenePhase=4;airPlacementClock(game,clock,range,display);point("done");
    if(game.result&&!terminal)throw std::runtime_error("Following Air quiet update ended the stunt; exit owner required");
    if(terminal&&!(game.result&1))throw std::runtime_error("Following Air terminal extent did not end the stunt");
    scenePhase=5;clock.atomicWork(16,[]{},display,false);clock.atomicWork(4,[]{},display,false);
    clock.atomicWork(terminal?8:12,[]{},display,false);
    if(terminal){point("terminalWait");clock.wait(display,false);point("terminalEnd");}
    else{
        point("backEdge");
        clock.atomicWork(8,[]{},display,false);clock.atomicWork(12,[&]{state.ready=1;},display,true);clock.wait(display,true);
        clock.atomicWork(4,[]{},display,true);clock.atomicWork(12,[&]{state.ready=0;},display,false);
        int fresh=0;clock.accessWork(12,8,[&]{fresh=t.input.pressed;},display,false);clock.atomicWork(8,[]{},display,false);
        if(fresh&8)throw std::runtime_error("Following Air next update requires its pause owner");clock.atomicWork(12,[]{},display,false);point("end");
    }
    t.end=clock.now;t.tick=game.ticks;t.nextStat=clock.nextStat;t.nextVBlank=clock.nextVBlank;t.displays=clock.displays;t.stats=clock.statServices;
    state.hudCursor=game.hudCursor;state.fadeRemaining=game.displayFadeRemaining;return state;
}

// Restarted Air's 0403..0409 exit retains this LCD epoch, prepared scene and
// closed upload gate. Only counter waits own interrupts in the qualified fade;
// an audio reset or palette operation crossing a service remains guarded.
template<class Phase,class Service,class Interrupt>
AirFollowingSetup airFollowingAirOutro(AirFollowingSetup state,AirGame& game,NativeAudio& sound,const UiAssets& ui,
    Phase&& phase,Service&& service,Interrupt&& interrupt,std::function<int()> sampleInput={}){
    if(state.stage!=1||state.ready||state.display!=4||state.stat!=4||!(game.result&1)||
       !game.measureWork||!sound.measureWork||!sound.enabled||game.pendingSound!=-1)
        throw std::runtime_error("Unowned following Air outgoing fade");
    auto& t=state.instruction.map.campaign.timing;AirClock clock;
    clock.now=t.end;clock.nextStat=t.nextStat;clock.nextVBlank=t.nextVBlank;clock.displays=t.displays;clock.statServices=t.stats;
    clock.interrupt=[&](const char* kind,int64_t cycle,AirIrqOwner owner){interrupt(kind,cycle,owner);};
    clock.objectDisable=[&](int64_t,AirIrqOwner){state.lcdc&=~2;};
    auto display=[&](bool ready){
        if(ready)throw std::runtime_error("Outgoing Air opened resource gate");
        t.input.sample(sampleInput?sampleInput():t.input.held);
        if(t.input.held<0||t.input.held>255||(t.input.held&15)==15)throw std::runtime_error("Unowned outgoing Air reset input");
        int tick=game.ticks;game.displayTick(false);state.lcdc|=2;
        if(game.pendingSound!=-1||sound.pendingEffect!=-1)throw std::runtime_error("Unowned outgoing Air effect");
        sound.tick();
        if(game.displayWorkCycles<0||sound.effectWorkCycles<0||sound.musicWorkCycles<0)throw std::runtime_error("Unowned outgoing Air display/audio");
        service(clock.displays,clock.now+20,tick,game.displayWorkCycles,sound.effectWorkCycles,sound.musicWorkCycles,t.input);
        return 1592+game.displayWorkCycles+sound.effectWorkCycles+sound.musicWorkCycles;
    };
    auto quiet=[&](int work){
        if(clock.now+work>=std::min(clock.nextStat,clock.nextVBlank))throw std::runtime_error("Interrupted outgoing Air operation needs its completion owner");
        clock.work(work,display,false);
    };
    int bgp=ui.fadePalettes[0],obp0=bgp&0xcf,obp1=bgp&0xf3;
    auto span=[&](const char* name,int index,int work,auto&& operation){
        auto start=clock.now;int tick=game.ticks;operation();
        phase(name,index,start,clock.now,tick,game.ticks,work<0?clock.lastWaitWork:work,bgp,obp0,obp1,sound.enabled);
    };
    span("audioStop",0,audioStopWork(),[&]{quiet(audioStopWork());sound.stop();});
    span("fadeEntry",0,44,[&]{quiet(44);});
    for(int segment=0;segment<8;++segment){
        span("palette",segment,76,[&]{quiet(76);bgp=ui.fadePalettes[segment];obp0=bgp&0xcf;obp1=bgp&0xf3;});
        for(int wait=0;wait<4;++wait){
            span("wait",4*segment+wait,-1,[&]{clock.wait(display,false);});
            int tail=wait<3?16:segment<7?28:40;
            span("tail",4*segment+wait,tail,[&]{quiet(tail);});
        }
    }
    t.end=clock.now;t.tick=game.ticks;t.nextStat=clock.nextStat;t.nextVBlank=clock.nextVBlank;t.displays=clock.displays;t.stats=clock.statServices;
    state.hudCursor=game.hudCursor;state.fadeRemaining=game.displayFadeRemaining;return state;
}

template<class Boundary,class Service,class Interrupt>
AirFollowingSetup airFollowingAirFirstUpdate(AirFollowingSetup state,AirGame& game,NativeAudio& sound,
    Boundary&& boundary,Service&& service,Interrupt&& interrupt,std::function<int()> sampleInput={}){
    if(game.entities[0].handler!=AirHandler::Intro)throw std::runtime_error("First following Air update requires intro entry");
    return airFollowingAirQuietUpdate(state,game,sound,boundary,service,interrupt,sampleInput);
}
}
