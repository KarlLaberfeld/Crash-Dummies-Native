// Synthetic workload boundaries. No ROM, extracted assets or emulator needed.
#include "air_work.h"
#include <cstdio>
#include <memory>
#include <stdexcept>

using namespace ticd;
int main(){
    int checks=0;
    auto require=[&](bool ok,const char* message){++checks;if(!ok)throw std::runtime_error(message);};
    try{
        auto assets=std::make_unique<AirAssets>();auto shared=std::make_unique<Assets>();
        auto game=std::make_unique<AirGame>(*assets,*shared);auto& g=*game;
        auto& p=g.entities[0];g.measureWork=true;p.alive=true;
        assets->commands={{},{4,1,0,0,2},{0}};
        auto run=[&]{g.animationWorkCycles=0;g.animationWorkComplete=true;g.animate(0);return g.animationWorkCycles;};
        require(run()==64,"Stopped animations return without dispatching commands");
        p.animDone=false;p.delay=1;p.anim=1;
        require(run()==104&&p.delay==0&&p.frame==0,"Inherited delay consumes an update without frame work");
        require(run()==516&&p.frameWaiting&&p.frame==1,"New dynamic frame waits without advancing the saved cursor");
        require(p.anim==1&&run()==396&&p.frameWaiting,"An incomplete upload repeats the waiting frame command");
        g.transferState=2;
        require(run()==656&&!p.frameWaiting&&p.animDone,"Completed upload continues to the script terminator");
        p.animDone=false;
        require(run()==696&&p.animDone,"Already-current dynamic frame requires no upload wait");
        assets->commands[1].a=12;p.animDone=false;
        require(run()==608&&p.frame==12,"Static frame path does not enter the dynamic transfer queue");
        require(airAnimationMoveWork(16,-17)==316&&airAnimationMoveWork(17,-17)==308,"Negative displacement carry changes source work");
        require(airAnimationMoveWork(255,1)==320&&airAnimationMoveWork(0,1)==312,"Positive displacement carry changes source work");

        p.frame=1;g.transferState=0;assets->transferChunks[1]=4;
        require(airResourceWork(g,0)==688,"New dynamic transfer includes descriptor preparation");
        require(airResourceWork(g,1)==252,"Unchanged dynamic frame does not queue a transfer");
        g.transferState=2;
        require(airResourceWork(g,1)==268,"Transfer completion acknowledgement has its own cost");
        g.transferState=1;g.transferFrame=1;
        require(airResourceWork(g,0)==384,"Already-queued frame restores the visible frame without requeueing");
        g.transferFrame=2;
        require(airResourceWork(g,0)==716,"Replacing a queued frame copies its new descriptor");
        assets->transferChunks[1]=0;
        require(airResourceWork(g,0)==412,"Empty replacement descriptor returns before frame restoration");
        g.transferState=0;
        require(airResourceWork(g,0)==384,"Empty new descriptor skips copying");
        p.frame=12;
        require(airResourceWork(g,0)==212,"Static sprites skip dynamic-resource comparisons");

        AirEntity before;before.alive=true;before.handler=AirHandler::DebrisLeft;
        before.x=32;before.y=64;before.params[0]=1;auto after=before;after.alive=false;g.ticks=8;
        require(airSimpleHandlerWork(g,before,after,0,0,0)==700,"Expiring debris returns before the periodic flip");
        before.params[0]=2;after.alive=true;
        require(airSimpleHandlerWork(g,before,after,0,0,0)==744,"Living debris performs the periodic flip");
        g.ticks=9;
        require(airSimpleHandlerWork(g,before,after,0,0,0)==648,"Living debris skips flips between eight-frame boundaries");
        before.handler=AirHandler::Play;
        require(airSimpleHandlerWork(g,before,after,0,0,0)==-1,"Unmodeled bodies are not reported as zero work");
        before.handler=AirHandler::Animation;
        require(airSimpleHandlerWork(g,before,after,64,108,0)==-1,"Native-only deferred recovery cannot certify original handler work");

        // A non-yielding loop is invalid game data; its partial count cannot be
        // accepted as a complete source interval.
        assets->commands[1]={10,1};p.anim=1;p.animDone=false;
        run();require(!g.animationWorkComplete&&g.animationFaults==1,"Guard exhaustion marks timing evidence incomplete");
        printf("Air source-work checks: %d passed (synthetic; no original parity claim)\n",checks);
        return 0;
    }catch(const std::exception& e){fprintf(stderr,"Air work test failed after %d checks: %s\n",checks,e.what());return 1;}
}
