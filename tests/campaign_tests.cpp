#include "campaign.h"
#include <cstdio>
namespace ticd {
int runCampaignTests(){
    FILE* log=fopen("campaign-test.txt","w");if(!log)return 2;int count=0;
    auto require=[&](bool condition,const char* message){++count;if(!condition)throw std::runtime_error(message);};
    try{
        Campaign c;c.start(false);require(c.players[0].lives==5&&c.players[1].lives==0,"One-player campaign begins with five lives");
        auto r=c.settle(3,123,40);require(r.pay==123&&r.timeBonus==40&&c.players[0].savings==163,"Successful pay and remaining seconds enter savings");
        require(c.players[0].day==1&&c.next()&&c.current==0,"Solo success advances day and skips inactive player");
        c.settle(0x21,900,50);require(c.players[0].lives==4&&c.players[0].savings==163&&c.players[0].day==1,"Failure loses a life, discards pay and retains day");c.next();
        r=c.settle(7,100,20);require(r.pay==200&&r.timeBonus==40&&c.players[0].savings==403,"Perfect doubles pay and time bonus");c.next();
        r=c.settle(0x47,100,99);require(r.pay==200&&r.timeBonus==0,"Bomb flag suppresses time bonus");c.next();
        c.start(true);c.settle(3,10,0);require(c.next()&&c.current==1&&c.players[1].day==0,"Two players alternate with independent progress");
        c.settle(1,0,0);require(c.next()&&c.current==0&&c.players[1].lives==4,"Failure also passes control to other player");
        c.start(false);for(int n=0;n<5;++n){r=c.settle(1,10,10);bool next=c.next();require(next==(n<4),"Solo campaign stops after fifth lost life");}
        require(r.gameOver&&!c.active,"Final failure is game over");
        c.start(false);c.settle(1,0,0,1);require(c.players[0].lives==5,"Earned extra life applies even on a failed stunt");c.next();
        c.start(false);for(int d=0;d<4;++d)for(int day=0;day<5;++day){
            require(c.players[0].difficulty==d&&c.players[0].day==day,"Campaign visits all twenty original day/difficulty combinations");
            r=c.settle(day==3?0x43:3,10,1);bool next=c.next();require(next==!(d==3&&day==4),"Only twentieth success completes full campaign");
        }
        require(r.completed&&c.players[0].completed&&!c.active,"Complete campaign enters ending state");
        c.start(true,4,3);c.settle(3,0,0);require(c.next()&&c.current==1&&!c.players[1].completed,"Second player continues after first player's ending");
        c.start(false);c.players[0].savings=999990;c.settle(3,20,0);require(c.players[0].savings==10,"Savings preserve six-digit BCD wrap");
        bool rejected=false;try{c.settle(3,1,0);}catch(const std::logic_error&){rejected=true;}require(rejected,"Result cannot be settled twice");
        fprintf(log,"PASS: %d campaign rule assertions. Presentation integration remains pending.\n",count);fclose(log);return 0;
    }catch(const std::exception& e){fprintf(log,"FAIL after %d assertions: %s\n",count,e.what());fclose(log);return 1;}
}
}
