// Synthetic workload boundaries. No ROM, extracted assets or emulator needed.
#include "air_work.h"
#include "air_video_work.h"
#include "air_clock.h"
#include "air_placement_clock.h"
#include "air_scene_clock.h"
#include "air_result_clock.h"
#include "audio_work.h"
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
        for(int frame:{0,1,11,12})for(int state:{0,1,2})for(int queued:{0,1,11})for(int oldFrame:{0,1,12})for(int chunks:{0,4}){
            p.frame=frame;g.transferState=state;g.transferFrame=queued;
            if(frame<12)assets->transferChunks[frame]=chunks;
            int charged=0;for(int cost:airResourceBoundaries(g,oldFrame))charged+=cost;
            require(charged==airResourceWork(g,oldFrame),"Resource completion covers acknowledgement, unchanged/static frames, queued/replaced and empty descriptors");
        }

        AirEntity before;before.alive=true;before.handler=AirHandler::DebrisLeft;
        before.x=32;before.y=64;before.params[0]=1;auto after=before;after.alive=false;g.ticks=8;
        require(airSimpleHandlerWork(g,before,after,0,0,0)==700,"Expiring debris returns before the periodic flip");
        before.params[0]=2;after.alive=true;
        require(airSimpleHandlerWork(g,before,after,0,0,0)==744,"Living debris performs the periodic flip");
        g.ticks=9;
        require(airSimpleHandlerWork(g,before,after,0,0,0)==648,"Living debris skips flips between eight-frame boundaries");
        for(int i=1;i<16;++i)g.entities[i].alive=false;
        require(airExplodingWork(g,2)==124&&airExplodingWork(g,0)==124,"Explosion countdown retains byte wrap and skips the particle body between eight-count boundaries");
        require(airExplodingWork(g,1)==384,"Expiration enters hide/frame work before particle and sound work");
        require(airExplodingWork(g,9)==1988&&airExplodingWork(g,17)==2028,"Particle branches use pre-allocation occupancy and only every other particle requests sound");
        for(auto& entity:g.entities)entity.alive=true;
        require(airExplodingWork(g,17)==2028,"Full allocation failure has its own bounded source work");
        for(int i=1;i<16;++i)g.entities[i].alive=false;
        require(airExplodingWork(g,-1)==-1&&airExplodingWork(g,256)==-1,"Invalid explosion countdown cannot certify source work");
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
        o.collision=14;p.params[2]=0;g.speed=-5;g.money=50;
        require(airCollisionCallbackWork(g,1)==584,"Moving enemy contact uses the forced script setter and score subtraction");
        g.money=49;require(airCollisionCallbackWork(g,1)==616,"Enemy penalty underflow adds score clearing after the untaken return");
        require(airDamageWork(239,16,2)==108&&airDamageWork(240,16,2)==276&&airDamageWork(240,16,1)==324,"Damage overflow and final finish-delay expiration have distinct paths");
        g.entities[2].alive=false;
        require(airSpawnRelativeWork(g,true)==1216&&airSpawnRelativeWork(g,false)==1204,"Allocation scans occupied slots and distinguishes caller-relative coordinates");
        for(auto& e:g.entities)e.alive=true;
        require(airSpawnRelativeWork(g,true)==1164,"Full allocation pool returns without initialization");
        require(airTimerWork(58,1)==64&&airTimerWork(59,1)==136&&airTimerWork(59,0)==116,"Timer rollover keeps the already-zero terminal branch distinct");
        require(airCameraLeadWork(176,96)==84&&airCameraLeadWork(96,176)==80,"Camera lead uses the source taken/not-taken carry branches");
        require(airCameraLeadWork(96,96)==56,"Unchanged camera lead returns before increment/decrement work");
        g.ticks=4;g.cameraY=15*256;g.held=Left|Right|A|B|Up;g.transferState=0;g.lastForce=0;g.rate=1;g.tilt=-2;g.speed=-5;
        int inputCost=airInputWork(g);g.input();
        require(g.tilt==-1&&g.speed==-5&&inputCost==788,"Input cost follows ordered left/right and acceleration/braking decisions");
        g.cameraY=0;g.held=Left;g.transferState=1;g.speed=-20;
        require(airInputWork(g)==324,"Transfer-gated steering and forced ascent include their early returns");
        g.cameraY=15*256;g.speed=-7;g.tilt=0;g.probes={};g.probes[2]=2;
        require(airWallWork(g)==488,"Wall crash initialization includes both entity-address helper calls");
        g.speed=-6;require(airWallWork(g)==504,"Wall clamp checks the strict signed boundary");
        g.speed=-20;g.probes={2,0,0,0,0,0};
        require(airWallWork(g)==468,"Wall-slide entry includes frame preparation and the strict speed return");
        g.speed=-6;require(airWallWork(g)==492,"Wall-slide entry at the limit stores its clamped speed");
        g.probes={24,0,0,0,0,0};g.speed=-20;p.params[1]=10;p.params[5]=192;assets->levels[0].quota=14;
        require(airFinishGateWork(g)==1404,"Successful bonus gate follows source score, frame and quota branches");
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
        require(airUploadWork(false,8)==36&&airUploadWork(true,0)==60,"Busy main update skips resource copying before reading its descriptor");
        require(airUploadWork(true,1)==1128&&airUploadWork(true,4)==3144&&airUploadWork(true,5)==3112,"Completion publishes the player frame while partial transfers retain the descriptor");
        auto video=airDisplayWork(false,true,0,0,1,0,0,6);
        require(video.total()==884,"Idle display service still samples scroll and one HUD column");
        auto mapVideo=airDisplayWork(true,false,8,0,1,0,0,6);
        require(mapVideo.map==760&&mapVideo.resources==32,"Map rows transfer even during work and take priority over dynamic sprites");
        require(airProgressBarWork(0)==172&&airProgressBarWork(8)==228&&airProgressBarWork(40)==304&&airProgressBarWork(48)==288,"Empty, partial and full progress bars take distinct source return paths");
        require(airHudRefreshWork(0,6)==3512&&airHudRefreshWork(1,6)==3548,"HUD refresh includes quotient-dependent division and bar drawing work");
        require(airHudRefreshWork(1,0)==-1,"Invalid HUD quota cannot certify a divide workload");
        require(airDisplayWork(false,true,0,12,2,8,1,0).total()==-1,"Unknown HUD work propagates through the complete display service");
        auto refreshing=airDisplayWork(false,true,0,12,2,8,1,6);
        require(refreshing.hud==260&&refreshing.refresh==3572&&refreshing.fade==232,"HUD wrap and fade are separate display components");
        assets->levels[g.difficulty].quota=6;p.params[1]=0;g.refreshHud();
        require(std::all_of(g.hudValues.begin()+7,g.hudValues.end(),[](int v){return v==0;}),"Zero progress clears every segment");
        p.params[1]=1;g.refreshHud();
        require(g.hudValues[7]==0xe9&&g.hudValues[8]==0xf0&&g.hudValues[9]==0,"Exact segment boundary emits the original terminator glyph");
        p.params[1]=5;g.refreshHud();
        require(g.hudValues[11]==0xe9&&g.hudValues[12]==0xf0,"Five exact segments retain the final partial terminator");
        p.params[1]=6;g.refreshHud();
        require(std::all_of(g.hudValues.begin()+7,g.hudValues.end(),[](int v){return v==0xe9;}),"A full bar returns without writing a terminator beyond the six slots");
        assets->levels[g.difficulty].quota=3;p.params[1]=32;g.refreshHud();
        require(std::all_of(g.hudValues.begin()+7,g.hudValues.end(),[](int v){return v==0;}),"Progress rendering retains the original low-byte quotient wrap");

        g.started=true;g.ticks=65535;g.mapTransfer=false;g.transferRemaining=8;g.transferState=1;
        int playerY=p.y,cursor=g.hudCursor;
        g.displayTick(false);
        require(g.ticks==0&&g.hudCursor==(cursor+1)%13&&p.y==playerY,"Independent display advances the wrapping clock and HUD without a game update");
        require(g.transferRemaining==8&&g.transferState==1,"Closed main-loop gate retains dynamic resources during an extra display");
        g.mapTransfer=true;g.displayTick(true);
        require(g.transferRemaining==8,"Pending map row still takes priority over a ready resource upload");
        AirClock clock;int displayCalls=0;bool lastReady=false;
        DisplayInput inputSample;inputSample.sample(A);
        require(inputSample.pressed==A&&inputSample.previous==0,"First display samples a fresh button without a game update");
        inputSample.sample(A);
        require(!inputSample.pressed&&inputSample.previous==A,"Extra display clears the edge before the next gameplay read");
        inputSample.sample(0);inputSample.sample(A|B);
        require(inputSample.pressed==(A|B)&&inputSample.previous==0,"Release/repress between game updates is captured by the display sampler");
        auto display=[&](bool ready){++displayCalls;lastReady=ready;return 5000;};
        clock.startup(display);
        require(clock.displays==1&&clock.statServices==1&&clock.nextVBlank==144*456,"Pending startup services do not consume the first LCD deadline");
        clock.wait(display);
        require(displayCalls==2&&clock.displays==2&&lastReady,"First wait requires a later display after the pending startup service");
        auto beforeClock=clock.now;
        bool unknownRejected=false;try{clock.work(-1,display,false);}catch(const std::runtime_error&){unknownRejected=true;}
        require(unknownRejected,"Unknown game work must reject scheduling");
        require(clock.now==beforeClock,"Unknown game work cannot become a guessed scheduling allowance");
        clock.work(AirClock::Frame,display,false);
        require(displayCalls==3&&clock.statServices==3&&!lastReady,"Long game work advances independent display and STAT services with resource gate closed");
        AirClock entryWait;entryWait.now=entryWait.nextVBlank-40;entryWait.nextStat+=AirClock::Frame;
        entryWait.wait([](bool){return 5000;});
        require(entryWait.displays==2,"Display before the wait counter read must be included in the snapshot and cannot end the wait");
        AirClock readWait;readWait.now=readWait.nextVBlank-48;readWait.nextStat+=AirClock::Frame;
        readWait.wait([](bool){return 5000;});
        require(readWait.displays==1&&readWait.now<AirClock::Frame+AirClock::VBlankLine,"Display pending during the counter read sees the prior snapshot and can end the wait after STAT");
        AirClock finalWait;bool observedReady=true;
        finalWait.wait([&](bool ready){observedReady=ready;return 5000;},false);
        require(finalWait.displays==1&&!observedReady,"Final result wait retains the busy resource gate; it does not enable gameplay uploads");
        require(finalWait.lastWaitWork==156,"Wait active work includes one STAT wake and excludes idle and interrupt service bodies");
        require(audioStopWork()==12384,"Stop/reset source work includes bounded byte clears and initial wave copy");
        AirClock atomic;atomic.now=atomic.nextVBlank-4;atomic.nextStat=AirClock::Frame+AirClock::StatLine;
        bool changed=false,observed=false;
        atomic.atomicWork(8,[&]{changed=true;},[&](bool){observed=changed;return 5000;},false);
        require(observed&&atomic.displays==1,"Sprite clearing commits its semantic write before a pending publication");
        auto placementGame=std::make_unique<AirGame>(*assets,*shared);
        placementGame->cameraY=86*256;
        for(int row:{33,35,39,40,41,42,43,44})placementGame->placements.push_back({18,0,row*256,false});
        for(int i=0;i<13;++i)placementGame->entities[i].alive=true;
        AirClock placementClock;placementClock.now=0;placementClock.nextVBlank=1380;placementClock.nextStat=AirClock::Frame;
        AirPlacementRange range;
        int placementWork=airPlacementClock(*placementGame,placementClock,range,[&](bool ready){
            require(!ready,"Interrupted placement keeps the resource gate closed");range.low=0;return 0;
        });
        require(placementWork==9284&&placementGame->scan==0,"HUD scratch overwrite changes four subsequent range tests; this short table also charges its wrap");
        require(!placementGame->placements[3].active&&placementGame->placements[4].active&&placementGame->placements[5].active&&placementGame->placements[6].active&&!placementGame->placements[7].active,"Three free slots fill after the overwrite; the fourth allocation fails");
        auto stablePlacement=std::make_unique<AirGame>(*assets,*shared);
        stablePlacement->cameraY=86*256;stablePlacement->placements=placementGame->placements;
        for(auto& record:stablePlacement->placements)record.active=false;
        AirClock quietClock;quietClock.now=0;AirPlacementRange stableRange;
        require(airPlacementClock(*stablePlacement,quietClock,stableRange,[](bool){return 0;})==3092,"Uninterrupted range scan retains source work including the table wrap");
        AirClock prefixClock;prefixClock.now=0;prefixClock.nextVBlank=28;prefixClock.nextStat=AirClock::Frame;
        AirPlacementRange prefixRange;stablePlacement->scan=0;
        airPlacementClock(*stablePlacement,prefixClock,prefixRange,[&](bool){prefixRange.low=0;return 0;});
        require(prefixRange.high==100,"Upper bound uses the retained camera value even if a display changes the lower scratch between its stores");
        auto verifyPlacementEdge=[&](int deadline,int accepted,int row){
            stablePlacement->scan=0;stablePlacement->placements.assign(8,{18,0,row*256,0,true});
            AirClock edge;edge.now=0;edge.nextStat=deadline;edge.nextVBlank=AirClock::Frame;
            AirPlacementRange bounds;int64_t vector=-1;AirIrqOwner owner=AirIrqOwner::Unqualified;
            edge.interrupt=[&](const char*,int64_t time,AirIrqOwner value){vector=time;owner=value;};
            auto work=airPlacementClock(*stablePlacement,edge,bounds,[](bool){return 0;});
            if(vector!=accepted+20||owner!=AirIrqOwner::SourceBoundary)
                fprintf(stderr,"Placement edge: deadline=%d row=%d vector=%lld expected=%d owner=%d\n",deadline,row,static_cast<long long>(vector),accepted+20,int(owner));
            require(vector==accepted+20&&owner==AirIrqOwner::SourceBoundary,"Pending placement STAT waits for the identified access/conditional-return completion");
            require(edge.now==work+324,"Source-boundary completion changes acceptance, not total active work or service cost");
        };
        verifyPlacementEdge(252,260,92); // High-range read completes before 19f5.
        verifyPlacementEdge(276,284,140); // Taken upper-range return completes before 19b8.
        verifyPlacementEdge(292,304,92); // Upper comparison + active-byte test precede the taken return.
        Frame one;one.pieces.push_back({});
        SpriteLayer partial(true);partial.slots[0].present=true;partial.slots[0].y=20;
        partial.add(one,16,16,0);
        require(partial.unusedFirst()==0&&partial.unusedCount()==39&&partial.slots[0].present&&partial.slots[39].present,"Partial reverse preparation retains prior unused entries until clearing");
        partial.clearUnused();
        require(!partial.slots[0].present&&partial.slots[39].present,"Clearing the unused range preserves newly prepared entries");
        std::array<int,16> perEntity{};
        auto workSplit=airSpriteWork(g,&perEntity);int prepareSum=112;for(int n:perEntity)prepareSum+=n;
        require(prepareSum==workSplit.prepare,"Source sprite preparation decomposes into entry and per-entity work without an allowance");
        auto publishing=std::make_unique<AirGame>(*assets,*shared);
        publishing->entities[0].alive=true;publishing->entities[0].x=80*16;publishing->entities[0].y=80*16;
        assets->frames[0].meta={};assets->frames[0].pieces={{},{127,0}};
        std::array<AirSpriteEntityWork,16> publication{};
        auto published=airSpriteWork(*publishing,&perEntity,&publication);
        auto unsplit=airSpriteWork(*publishing);
        require(published.prepare==unsplit.prepare&&published.clear==unsplit.clear,"Publication decomposition preserves the source totals");
        require(publication[0].pieces.size()==2&&publication[0].pieces[0].writes&&!publication[0].pieces[1].writes,"Publication distinguishes a written piece from a clipped piece");
        int pieceSum=76+publication[0].geometry+publication[0].tail;
        for(const auto& piece:publication[0].pieces)pieceSum+=piece.before+(piece.writes?156:0);
        require(pieceSum==perEntity[0],"Piece writes and actor tails cover the full source preparation interval");
        // Exercise both allocation directions, camera wrap, culling/eviction,
        // mirroring, static/dynamic layouts and last-slot returns. Compare the
        // clock's native publication with the existing renderer and workload.
        for(bool reverse:{false,true})for(int frame:{0,12})for(int flags:{0,8,16,20,32,64,96})
        for(int x:{-40,-16,0,80,176,190})for(int y:{-40,-16,80,152,170}){
            publishing->entities={};auto& actor=publishing->entities[15];actor.alive=true;
            actor.frame=frame;actor.flags=flags;actor.x=(x*16)&65535;actor.y=(y*16)&65535;
            assets->frames[frame].meta={255,1,0,0,0,0,4,4};assets->frames[frame].pieces={{},{127,0},{0,127}};
            publishing->reverseSprites=!reverse;auto expected=airSpriteWork(*publishing);
            publishing->spriteInputEntities=publishing->entities;publishing->reverseSprites=reverse;
            publishing->sprites=SpriteLayer(reverse);
            AirClock scene;scene.now=0;scene.nextStat=scene.nextVBlank=1000000;
            int charged=airSpriteClock(*publishing,scene,[](bool){return 0;});
            require(charged==expected.prepare&&scene.now==charged,"Scene completion preserves native work across geometry/branch variants");
            SpriteLayer expectedSprites(reverse);
            if(!(flags&8))expectedSprites.add(assets->frames[frame],x,y,flags);
            bool same=true;for(int slot=0;slot<40;++slot){const auto& a=publishing->sprites.slots[slot];const auto& b=expectedSprites.slots[slot];
                same&=a.present==b.present&&a.x==b.x&&a.y==b.y&&a.flags==b.flags;}
            require(same,"Scene completion publishes the same native sprite list without interrupts");
        }
        for(int oldY:{0,128,65535})for(int newY:{0,64,128,192,65535}){
            AirClock scene;scene.now=0;scene.nextStat=scene.nextVBlank=1000000;bool transfer=true;
            int charged=airMapClock(scene,oldY,newY,transfer,[](bool){return 0;});
            bool changed=((oldY^newY)&128)!=0;
            require(charged==(changed?2228+((static_cast<uint16_t>(oldY-newY)&32768)?4:0):304)&&transfer==changed,"Row completion retains source costs for both directions, unchanged rows and wrap");
        }
        // The pending vector must follow completion of the map flag store,
        // not its request deadline; the callback observes the completed clear.
        AirClock mapEdge;mapEdge.now=0;mapEdge.nextVBlank=108;mapEdge.nextStat=1000000;
        bool pendingMap=true,sawClear=false;int64_t mapVector=0;
        mapEdge.interrupt=[&](const char*,int64_t time,AirIrqOwner owner){mapVector=time;require(owner==AirIrqOwner::SourceBoundary,"Row IRQ has a source completion owner");};
        airMapClock(mapEdge,0,0,pendingMap,[&](bool){sawClear=!pendingMap;return 0;});
        require(sawClear&&mapVector==136,"Pending row IRQ observes the completed native flag store at cycle 116");
        // A real successful control interrupts after the pending flag is set,
        // before row cells are filled. Scalar transfer work is owned here;
        // this deliberately does not certify the still incomplete tile data.
        AirClock rowEdge;rowEdge.now=0;rowEdge.nextVBlank=328;rowEdge.nextStat=1000000;
        bool rowFlag=false,flagOwned=false,rowReady=true,sawPending=false;
        airMapClock(rowEdge,649,617,rowFlag,[&](bool){sawPending=rowFlag&&flagOwned&&!rowReady;return 0;},&flagOwned,&rowReady);
        require(sawPending&&rowReady,"Interrupted row preparation exposes the completed transfer request before cell readiness");
        publishing->entities={};auto& publishActor=publishing->entities[0];publishActor.alive=true;
        publishActor.frame=12;publishActor.x=publishActor.y=80*16;
        assets->frames[12].meta={};assets->frames[12].pieces={{}};assets->frames[12].pieces[0].colors.fill(2);
        publishing->reverseSprites=true;airSpriteWork(*publishing,nullptr,&publication);
        int firstWrite=112+76+publication[0].geometry+publication[0].pieces[0].before+12;
        for(int part=0;part<4;++part){
            publishing->spriteInputEntities=publishing->entities;publishing->reverseSprites=false;publishing->sprites=SpriteLayer(false);
            auto& old=publishing->sprites.slots[0];old={true,44,24,64,{}};old.colors.fill(1);
            const int offsets[]={0,24,56,96};
            AirClock edge;edge.now=0;edge.nextVBlank=firstWrite+offsets[part]+4;edge.nextStat=1000000;
            int64_t vector=-1;edge.interrupt=[&](const char*,int64_t time,AirIrqOwner owner){vector=time;require(owner==AirIrqOwner::SourceBoundary,"Partial piece IRQ retains completion ownership");};
            SpriteLayer::Entry observed;
            airSpriteClock(*publishing,edge,[&](bool ready){require(!ready,"Partial piece publication keeps the resource gate closed");observed=publishing->sprites.slots[0];return 0;});
            require(vector==firstWrite+offsets[part]+8+20,"Pending piece IRQ waits for its eight-cycle write to complete");
            require(observed.y==96&&observed.x==(part>=1?88:44)&&observed.colors[0]==(part>=2?2:1)&&observed.flags==(part>=3?0:64),"Partial publication retains unwritten X/tile/flags while exposing each completed write");
        }
        for(bool reverse:{false,true})for(int count:{0,1,39,40}){
            SpriteLayer clearing(reverse);for(int i=0;i<40;++i)clearing.slots[i].present=true;
            for(int i=0;i<count;++i)clearing.advancePreparedPiece();clearing.finishPreparedEntity();
            int first=clearing.unusedFirst(),unused=clearing.unusedCount();
            AirClock scene;scene.now=0;scene.nextStat=scene.nextVBlank=1000000;
            int charged=airSpriteClearClock(clearing,scene,[](bool){return 0;});
            require(charged==(unused?(reverse?196:184)+32*unused+88:reverse?172:168),"Sprite clear retains both direction and exhausted-list source costs");
            bool same=true;for(int slot=0;slot<40;++slot)same&=clearing.slots[slot].present==!(slot>=first&&slot<first+unused);
            require(same,"Native sprite clear changes exactly the unprepared portion");
        }
        for(int offset:{0,4,100,144*456,145*456,146*456,153*456,AirClock::Frame-4}){
            AirClock endClock;endClock.now=2*AirClock::Frame+offset;
            while(endClock.nextStat<=endClock.now)endClock.nextStat+=AirClock::Frame;
            while(endClock.nextVBlank<=endClock.now)endClock.nextVBlank+=AirClock::Frame;
            int reads=0,lastLine=-1;std::vector<int64_t> boundaries;
            auto prefix=airResultSetupPrefix(endClock,3,[&](const char*,int64_t cycle){boundaries.push_back(cycle);},
                [&](int64_t,int line){++reads;lastLine=line;});
            require(reads==prefix.pollReads&&lastLine==145&&reads<=2200,"Result LCD-off waits for line equality even when setup starts later in VBlank");
            require(prefix.end-boundaries[1]==727820,"Common LCD-off result operations retain the full object/map/tile copy work");
            require(endClock.displays==0&&endClock.now==2*AirClock::Frame+offset,"Result setup records masked requests without running gameplay/display services");
        }
        int64_t lastLine=2*AirClock::Frame+153*456-8;
        require(airResultScanline(lastLine+0)==152&&airResultScanline(lastLine+4)==153&&airResultScanline(lastLine+8)==0,"Result polling includes the short line-153 readback and early zero reset");
        bool perfectRejected=false;try{airResultSetupPrefix(clock,7,[](const char*,int64_t){},[](int64_t,int){});}catch(const std::runtime_error&){perfectRejected=true;}
        require(perfectRejected,"Perfect-result celebration cannot borrow the ordinary result prefix");
        SpriteLayer staged(false);staged.advancePreparedPiece();staged.finishPreparedEntity();
        require(staged.preparedSlot()==1&&!staged.exhausted(),"Staged source publication advances capacity after piece writes");
        int savedCamera=g.cameraY,savedY=p.y;g.cameraY=0xae80;p.y=g.cameraY+8*g.cameraLead;
        assets->levels[0].cameraY=0xae80;assets->levels[0].rows=184;
        int limited=airCameraWork(g,false);assets->levels[0].cameraY=0xaf80;
        require(limited==airCameraWork(g,false)+36,"Camera source limit uses the original scroll bound rather than padded map rows");
        g.cameraY=savedCamera;p.y=savedY;

        // A non-yielding loop is invalid game data; its partial count cannot be
        // accepted as a complete source interval.
        assets->commands[1]={10,1};p.anim=1;p.animDone=false;
        run();require(!g.animationWorkComplete&&g.animationFaults==1,"Guard exhaustion marks timing evidence incomplete");
        printf("Air source-work checks: %d passed (synthetic; no original parity claim)\n",checks);
        return 0;
    }catch(const std::exception& e){fprintf(stderr,"Air work test failed after %d checks: %s\n",checks,e.what());return 1;}
}
