#include "cruise.h"
#include <cstdio>
#include <stdexcept>
namespace ticd {
int runCruiseTests(const CruiseAssets& assets,const Assets& shared){
    FILE* log=fopen("cruise-test.txt","w");if(!log)return 2;int count=0;
    auto require=[&](bool value,const char* message){++count;if(!value)throw std::runtime_error(message);};
    try{
        CruiseGame g(assets,shared);g.start(0);
        require(g.cameraY==1920&&g.entities[0].x==1040&&g.entities[0].y==3424,"Original Cruise camera and launch origin");
        require(g.entities[0].params[0]==4&&g.entities[0].params[2]==232,"Original upward heading and launch velocity");
        for(int t=0;t<31;++t)g.step(0);require(g.introTimer==31&&g.entities[0].handler==CruiseHandler::Intro,"Launch waits 31 complete updates");
        g.step(0);require(g.introTimer==33&&g.entities[0].handler==CruiseHandler::Ignition,"Launch immediately enters ignition on update 32");
        for(int t=32;t<191;++t)g.step(0);require(g.entities[0].handler==CruiseHandler::Fly&&g.seconds==60,"Ignition ends without consuming gameplay timer");
        g.start(0);g.ticks=4;g.held=A;g.entities[0].params[2]=0;g.movePlayer();
        require(g.entities[0].params[2]==254&&g.entities[0].y==3422,"Upward thrust adds the original heading vector");
        g.entities[0].params[2]=240;g.movePlayer();require(g.entities[0].params[2]==238,"Negative velocity can overshoot -16 once");
        g.movePlayer();require(g.entities[0].params[2]==238,"Negative velocity stops accelerating below -16");
        g.held=0;g.movePlayer();require(g.entities[0].params[2]==239,"Gravity approaches +8 when thrust is released");
        g.start(0);int spring=g.spawn(63,0,0,0);g.collideWith(spring);
        require(g.money==50&&g.entities[spring].collision==37,"Spring awards fifty and changes its collision during compression");
        g.reward(spring,50);require(g.money==50,"Placement rewards cannot repeat");
        for(int angle:{4,12}){g.start(0);int target=g.spawn(60,0,0);g.entities[0].params[0]=angle;g.collideWith(target);
            require(g.resultFlags==(angle==12?0x27:0x23),"Target differentiates downward perfect hit");
            for(int t=0;t<500&&!g.result;++t)g.step(0);require(g.result==(angle==12?0x27:0x23),"Target animation finishes with original success result");}
        g.start(0);int bonus=g.spawn(65,0,0);g.collideWith(bonus);require(g.extraLives==1&&!g.entities[bonus].alive,"Bonus actor awards an extra life");
        for(int d=0;d<4;++d)for(int pattern=0;pattern<3;++pattern){
            g.start(d);for(int t=0;t<8000&&!g.result;++t){int input=pattern==0?0:pattern==1?A:A|((t/120)%2?Left:Right);g.step(input);
                require(g.animationFaults==0,"Cruise replay animation graph valid");
                for(const auto& e:g.entities)if(e.alive)require(e.frame>=0&&e.frame<42&&e.x>=0&&e.x<=65535&&e.y>=0&&e.y<=65535,"Cruise replay entity bounds");
            }
            fprintf(log,"difficulty=%d pattern=%d ticks=%d flags=%02x money=%d\n",d,pattern,g.ticks,g.result,g.money);
            require(g.result!=0,"Cruise replay reaches terminal result");g.render();for(int shade:g.screen)require(shade>=0&&shade<4,"Cruise palette bounds");
        }
        fprintf(log,"PASS: %d assertions. Native rule/replay checks; original equivalence remains unverified.\n",count);fclose(log);return 0;
    }catch(const std::exception& e){fprintf(log,"FAIL after %d assertions: %s\n",count,e.what());fclose(log);return 1;}
}
}
