#include "game.h"
#include <cstdio>
#include <stdexcept>

namespace ticd {
int runSelfTests(const Assets& assets) {
    FILE* log=fopen("self-test.txt","w");if(!log)return 2;
    int assertions=0;
    auto require=[&](bool ok,const char* message){++assertions;if(!ok)throw std::runtime_error(message);};
    try {
        require(assets.levels[0].height==1888,"Easy map height");
        require(assets.levels[0].objects.size()==36,"Easy placement count");
        require(assets.levels[3].objects.size()==46,"Very hard placement count");
        Game g(assets);g.start(0);
        require(g.entities[0].x==0x1290&&g.entities[0].y==0x150,"Original player origin");
        Entity p;p.x=0x1040;p.vx=-10;p.vy=24;p.y=0;
        g.moveFalling(p);require(p.x==0x1040&&p.y==24,"Left clamp / fixed point fall");
        p.x=0x1880;p.vx=10;g.moveFalling(p);require(p.x==0x1880,"Right clamp");
        p.vy=-41;p.pose=24;for(int i=0;i<65;++i)g.gravity(p);require(p.vy==24,"Bounce gravity converges");
        int unchanged=g.ticks;g.paused=true;g.step(A);require(g.ticks==unchanged,"Pause freezes simulation");g.paused=false;
        g.entities[0].pose=28;g.entities[0].vy=28;
        int awning=g.spawn(3,0x1400,0x1000,0);g.placements[0].state=0;
        g.collideWith(0,awning);require(g.placements[0].state==5&&g.money==10,"Head-first awning break");
        int remaining=g.remaining;g.collideWith(0,awning);require(g.remaining==remaining,"Broken awning cannot score twice");
        g.start(0);int balcony=g.spawn(8,0x1400,0x1000,0);g.entities[0].pose=24;g.collideWith(0,balcony);
        require(g.entities[0].vy==-4&&g.money==5&&g.placements[0].state==1,"Neutral balcony break from 01:5ef3");
        g.start(0);int target=g.spawn(14,0x1400,0x1000);g.collideWith(0,target);
        require(g.targetReached&&g.pendingResult==0&&g.money==100&&!g.entities[target].alive,"Target flags landing without prematurely choosing result");
        g.start(0);awning=g.spawn(3,0x1400,0x1000,0);
        g.entities[0].pose=28;g.entities[0].vy=-10;g.collideWith(0,awning);
        require(g.placements[0].state==5,"Diving breaks awning even while rising (01:5c8b)");
        g.start(0);awning=g.spawn(3,0x1400,0x1000,0);
        g.entities[0].pose=24;g.entities[0].vy=-10;g.collideWith(0,awning);
        require(g.placements[0].state==0,"Neutral upward contact does not damage awning");
        for(int hit=0;hit<4;++hit){
            g.entities[0].vy=24;g.collideWith(0,awning);
            require(g.entities[0].vy==-41+hit*4,"Original neutral bounce velocity sequence");
        }
        g.entities[0].vy=24;g.collideWith(0,awning);
        require(g.placements[0].state==5&&g.money==13,"Four bounces then fifth-hit break");

        // Contact removes a placement permanently; visibility eviction permits
        // respawning only for flagged scenery (00:1c91 / 00:3da5).
        g.start(0);target=g.spawn(14,0x1400,0x1000,0);g.placements[0].active=true;
        g.collideWith(0,target);require(g.placements[0].active,"Collected target cannot respawn");
        g.start(0);g.camera=0;awning=g.spawn(3,0x1400,0x4000,0);g.placements[0].active=true;
        g.updateVisibility();require(!g.entities[awning].alive&&!g.placements[0].active,"Offscreen scenery recycles placement");
        g.start(0);g.camera=0;g.entities[0].frame=9;g.entities[0].x=0x1200;g.entities[0].y=152*16;
        g.updateVisibility();require(!g.entities[0].offscreen,"Original lower visibility boundary is inclusive");
        g.entities[0].y+=16;g.updateVisibility();require(g.entities[0].offscreen,"Original lower visibility boundary + one pixel");

        // Landing uses the original result bitfield and body-piece scripts.
        const int landing=(assets.levels[0].height-32)*16;
        for(int allObjects=0;allObjects<2;++allObjects){
            g.start(0);g.placements.clear();g.camera=landing-100*16;
            g.targetReached=true;g.breaksNeeded=-1;g.remaining=allObjects?0:1;
            g.entities[0].y=landing+17;g.land(0);
            require(g.entities[0].y==landing+256&&g.entities[0].frame==29,"Landing snaps to next tile row");
            require(g.entities[0].handler==Handler::Idle&&g.result==0&&g.finishTimer==64,"Target landing waits for body-piece animation");
            require(g.resultFlags==(allObjects?7:3),"Perfect result requires every object");
            for(int n=0;n<300&&!g.result;++n)g.step(0);
            require(g.result==3,"Body-piece completion drives delayed success");
        }
        g.start(0);g.targetReached=true;g.breaksNeeded=0;g.entities[0].y=landing;g.land(0);
        require(g.resultFlags==0x81&&g.pendingResult==5,"Ten breaks are insufficient; threshold is eleven");
        g.start(0);g.entities[0].pose=28;g.entities[0].y=landing;g.land(0);
        require(g.entities[0].handler==Handler::Animation&&g.finishTimer==64,"Head-first miss plays impact sequence before result delay");
        g.placements.clear();for(int n=0;n<1000&&!g.result;++n)g.step(0);
        require(g.result==1,"Head-first impact sequence reaches failure");
        g.start(0);g.entities[0].pose=24;g.entities[0].y=landing;g.land(0);
        require(g.entities[0].frame==25&&g.finishTimer==63,"Neutral miss starts countdown on same tick");

        g.start(0);g.entities[0].handler=Handler::Bounce;g.entities[0].y=landing;
        g.seconds=0;g.update(0);require(g.entities[0].handler==Handler::Bounce,"Bounce routine does not run main-fall landing or timeout checks");
        g.start(0);g.entities[0].handler=Handler::Falling;g.entities[0].frame=9;g.entities[0].y=1000;
        g.seconds=1;g.secondTicks=59;g.update(0);
        require(g.seconds==0&&g.entities[0].handler==Handler::Timeout&&g.entities[0].y==969,"Timeout falls through to its movement on same tick");
        g.start(0);int plane=g.spawn(5,0x1400,0x1000);g.collideWith(0,plane);
        for(int n=0;n<63;++n)g.update(plane);
        require(g.entities[plane].handler==Handler::PlaneStun,"Plane's definition provides 64-tick stun");
        g.update(plane);require(g.entities[plane].handler==Handler::PlaneFly,"Plane resumes after original countdown");
        require(g.entities[plane].collision==255,"Plane remains non-colliding after stun");
        g.start(0);g.entities[0].handler=Handler::Falling;g.entities[0].frame=9;
        g.pressed=Up|Down;g.update(0);
        require(g.entities[0].pose==20,"Simultaneous posture presses respect animation busy check");
        for(int difficulty=0;difficulty<4;++difficulty){
            Game first(assets),second(assets);first.start(difficulty);second.start(difficulty);
            for(int i=0;i<12000;++i){
                // Complete the roof jump before steering: the original checks
                // walking first, so continuous lateral input can postpone A.
                int input=(i>450?A:0)|(i>1000?((i/180)%2?Right:Left):0)|((i/240)%3==0?Down:0);
                first.step(input);second.step(input);
                require(first.camera>=0&&first.camera<assets.levels[difficulty].height*16,"Camera stays inside level");
                if(i%60==0){first.render();second.render();require(first.screen==second.screen,"Replay determinism");}
            }
            require(first.animationFaults==0,"Animation graph terminates without invalid commands");
            require(first.launched,"Original intro reaches jump");
            require(first.result!=0,"Stunt has a terminal result");
            fprintf(log,"difficulty=%d ticks=%d result=%d money=%d animation_faults=%d\n",difficulty,first.ticks,first.result,first.money,first.animationFaults);
        }
        fprintf(log,"PASS: %d assertions. These validate the native implementation, not complete equivalence to the original.\n",assertions);fclose(log);return 0;
    }catch(const std::exception& e){fprintf(log,"FAIL after %d assertions: %s\n",assertions,e.what());fclose(log);return 1;}
}
}
