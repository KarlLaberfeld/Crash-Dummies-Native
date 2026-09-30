#include "ski.h"
#include <cstdio>
#include <stdexcept>
namespace ticd {
int runSkiTests(const SkiAssets& assets,const Assets& shared){
    FILE* log=fopen("ski-test.txt","w");if(!log)return 2;int count=0;
    auto require=[&](bool value,const char* message){++count;if(!value)throw std::runtime_error(message);};
    try{
        SkiGame g(assets,shared);g.start(0);
        require(g.cameraX==0x6400&&g.cameraY==0&&g.entities[0].x==0x6800&&g.entities[0].y==0xff00,"Original Ski camera and player origin");
        require(g.remaining==30&&g.needed==15&&g.seconds==80,"Original Ski easy counters");
        g.step(0);require(g.entities[0].handler==SkiHandler::Play&&g.secondTicks==0,"Ski intro changes state without falling into gameplay");
        g.placements.clear();g.step(0);require(g.entities[0].y==0xff00&&g.entities[0].params[2]==1,"Movement precedes velocity approach");
        g.step(0);require(g.entities[0].y==0xff01&&g.entities[0].params[2]==2,"Initial downward acceleration");
        g.start(0);g.held=B;g.movePlayer();require(g.entities[0].params[2]==2,"B doubles approach steps without replacing the speed target");
        g.held=Left;g.input();require(g.entities[0].params[0]==1&&!g.entities[0].animDone,"Left starts a positive-angle turn animation");
        g.input();require(g.entities[0].params[0]==1,"Active turn animation gates another turn");
        g.entities[0].animDone=true;g.input();require(g.entities[0].params[0]==2,"Second left turn reaches maximum angle");
        g.entities[0].animDone=true;g.held=Right;g.input();require(g.entities[0].params[0]==1,"Right reduces current left angle");
        g.entities[0].animDone=true;g.input();require(g.entities[0].params[0]==255,"Direction change skips neutral angle");
        g.entities[0].animDone=true;g.held=Down;g.input();require(g.entities[0].params[0]==0,"Down starts the return-to-straight animation");
        g.start(0);g.jump();require(g.jumpVelocity==-64&&g.entities[0].frame==7&&g.entities[1].kind==44,"Jump creates original shadow and vertical impulse");
        int y=g.entities[0].y;g.update(0);require(g.entities[0].y==((y-8)&65535)&&g.jumpVelocity==-62,"Jump combines half impulse with 24-unit forward motion");
        g.start(0);int flag=g.spawn(38,0,0);g.collideWith(flag);g.collideWith(flag);
        require(g.money==10&&g.remaining==29&&g.needed==14&&g.collected==1,"Flag collection scores once and reduces both counters");
        flag=g.spawn(36,0,0);g.collideWith(flag);require(g.money==15&&g.collected==2,"Second flag type awards five");
        for(int collected:{0,14,15,30}){
            g.start(0);g.remaining=30-collected;g.needed=(15-collected)&255;g.entities[0].y=120*256;
            g.finishLine();require(g.resultFlags==(collected>=15?(collected==30?7:3):1),"Finish requires at least half the flags; every flag gives perfect result");
            require(g.finishTimer==63,"Ski result delay starts on finish tick");
        }
        g.start(0);g.entities[0].y=114*256;g.depth();require(g.finishZone&&(g.entities[0].flags&128),"Entering finish tunnel sets original background priority");
        g.entities[0].y=117*256;g.depth();require(g.finishZone&&!(g.entities[0].flags&128),"Finish collision suppression persists after tunnel priority ends");
        g.start(0);g.entities[0].x+=7;g.entities[0].y=1007;int trap=g.spawn(40,0,0);g.collideWith(trap);
        require(g.entities[0].handler==SkiHandler::Crash&&g.returnY==992&&!g.entities[trap].alive,"Trap stores pixel-aligned return position and consumes object");
        for(int d=0;d<4;++d)for(int pattern=0;pattern<3;++pattern){
            g.start(d);for(int t=0;t<14000&&!g.result;++t){
                int input=pattern==0?0:pattern==1?B:((t/150)%2?Left:Right)|((t%180==0)?A:0);
                g.step(input);require(g.animationFaults==0,"Ski replay animation graph valid");
                for(const auto& e:g.entities)if(e.alive)require(e.frame>=0&&e.frame<39&&e.x>=0&&e.x<=65535&&e.y>=0&&e.y<=65535,"Ski replay entity bounds");
            }
            fprintf(log,"difficulty=%d pattern=%d ticks=%d flags=%02x money=%d collected=%d\n",d,pattern,g.ticks,g.result,g.money,g.collected);
            require(g.result!=0,"Ski replay reaches terminal result");g.render();for(int shade:g.screen)require(shade>=0&&shade<4,"Ski palette bounds");
        }
        fprintf(log,"PASS: %d assertions. Native rule/replay checks; original equivalence remains unverified.\n",count);fclose(log);return 0;
    }catch(const std::exception& e){fprintf(log,"FAIL after %d assertions: %s\n",count,e.what());fclose(log);return 1;}
}
}
