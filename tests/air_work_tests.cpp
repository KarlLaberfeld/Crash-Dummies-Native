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

        // Contact is asymmetric in the original byte-edge comparisons. The
        // ignored-callback branch must still pay the conditional CALL cost.
        g.cameraX=g.cameraY=0;p.x=p.y=256;p.frame=0;
        assets->frames[0].meta={0,0,0,0,8,8,0,0};
        auto& o=g.entities[1];o={};o.frame=0;o.x=o.y=256;
        require(airCollisionSlotWork(g,0).scan==56&&airCollisionSlotWork(g,1).scan==84,"Self and empty collision slots have distinct early returns");
        o.alive=true;o.offscreen=true;
        require(airCollisionSlotWork(g,1).scan==416,"Offscreen collision returns after relative-position work");
        o.offscreen=false;o.collision=8;auto contact=airCollisionSlotWork(g,1);
        require(contact.callback,"Overlapping live objects request a callback");
        o.collision=255;
        require(!airCollisionSlotWork(g,1).callback&&airCollisionSlotWork(g,1).scan==contact.scan+12,"Ignored contacts still pay twelve cycles for the untaken CALL");
        o.collision=8;o.x=p.x+8*16;
        require(airCollisionSlotWork(g,1).callback,"Player right-edge equality is contact");
        o.x=p.x-8*16;
        require(!airCollisionSlotWork(g,1).callback,"Player left-edge equality with the other right edge is rejected");
        o.x=p.x;p.params[2]=0;
        require(airCollisionCallbackWork(g,1)==492,"Active pickup contact includes dispatch and score work");
        p.params[2]=255;
        require(airCollisionCallbackWork(g,1)==196,"Crash state suppresses ordinary callbacks after dispatch");
        o.collision=13;
        require(airCollisionCallbackWork(g,1)==492,"Recovery contact is allowed while crashing");
        p.params[2]=0;
        require(airCollisionCallbackWork(g,1)==196,"Recovery contact returns early outside a crash");
        o.collision=7;o.animDone=false;int continuing=airCollisionCallbackWork(g,1);o.animDone=true;
        require(airCollisionCallbackWork(g,1)==continuing+44,"Stopped breakable animations require a new script address");
        o.collision=15;p.params[5]=31;int lowDamage=airCollisionCallbackWork(g,1);p.params[5]=32;
        require(lowDamage==692&&airCollisionCallbackWork(g,1)==676,"Damage threshold and dispatch-table carry contribute separate work");
        require(airDamageWork(239,16,2)==108&&airDamageWork(240,16,2)==276&&airDamageWork(240,16,1)==324,"Damage overflow and final finish-delay expiration have distinct paths");
        g.entities[2].alive=false;
        require(airSpawnRelativeWork(g,true)==1216&&airSpawnRelativeWork(g,false)==1204,"Allocation scans occupied slots and distinguishes caller-relative coordinates");
        for(auto& e:g.entities)e.alive=true;
        require(airSpawnRelativeWork(g,true)==1164,"Full allocation pool returns without initialization");
        require(airTimerWork(58,1)==64&&airTimerWork(59,1)==136&&airTimerWork(59,0)==116,"Timer rollover keeps the already-zero terminal branch distinct");
        g.ticks=4;g.cameraY=15*256;g.held=Left|Right|A|B|Up;g.transferState=0;g.lastForce=0;g.rate=1;g.tilt=-2;g.speed=-5;
        int inputCost=airInputWork(g);g.input();
        require(g.tilt==-1&&g.speed==-5&&inputCost==788,"Input cost follows ordered left/right and acceleration/braking decisions");
        g.cameraY=0;g.held=Left;g.transferState=1;g.speed=-20;
        require(airInputWork(g)==324,"Transfer-gated steering and forced ascent include their early returns");
        g.cameraY=15*256;g.speed=-7;g.tilt=0;g.probes={};g.probes[2]=2;
        require(airWallWork(g)==488,"Wall crash initialization includes both entity-address helper calls");
        g.speed=-6;require(airWallWork(g)==504,"Wall clamp checks the strict signed boundary");
        g.probes={};p.params[3]=0;g.speed=1;
        require(airTerrainBounceWork(g)==152,"No terrain impact scans all three forward probes");
        p.params[3]=1;
        require(airTerrainBounceWork(g)==136,"Boosted motion examines all six probes before returning");
        g.probes[5]=1;require(airTerrainBounceWork(g)==160,"Boost cancellation includes the byte reset");
        before.handler=AirHandler::Wait;before.params[0]=1;g.complexBodyWorkCycles=-1;
        require(airSimpleHandlerWork(g,before,after,0,0,0)==-1,"Wait transition propagates an unknown Play budget");
        g.complexBodyWorkCycles=1000;
        require(airSimpleHandlerWork(g,before,after,0,0,0)==1184,"Wait transition includes the original setup before Play");
        before.handler=AirHandler::FinishDelay;g.finishTimer=1;
        require(airSimpleHandlerWork(g,before,after,0,0,0)==44,"Living finish delay does not publish a result");
        g.finishTimer=0;
        require(airSimpleHandlerWork(g,before,after,0,0,0)==92,"Finish delay expiration publishes the result after its final decrement");
        before.handler=AirHandler::BeginFinish;
        require(airSimpleHandlerWork(g,before,after,0,0,0)==188,"Begin-finish includes the handler setter and immediate delay expiration");

        // A non-yielding loop is invalid game data; its partial count cannot be
        // accepted as a complete source interval.
        assets->commands[1]={10,1};p.anim=1;p.animDone=false;
        run();require(!g.animationWorkComplete&&g.animationFaults==1,"Guard exhaustion marks timing evidence incomplete");
        printf("Air source-work checks: %d passed (synthetic; no original parity claim)\n",checks);
        return 0;
    }catch(const std::exception& e){fprintf(stderr,"Air work test failed after %d checks: %s\n",checks,e.what());return 1;}
}
