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
        require(g.pendingResult==3&&g.money==100&&!g.entities[target].alive,"Target collected once");
        for(int difficulty=0;difficulty<4;++difficulty){
            Game first(assets),second(assets);first.start(difficulty);second.start(difficulty);
            for(int i=0;i<12000;++i){
                int input=(i>450?A:0)|((i/180)%2?Right:Left)|((i/240)%3==0?Down:0);
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
