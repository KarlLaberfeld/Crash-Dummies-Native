#pragma once
#include <array>
#include <stdexcept>
namespace ticd {
struct CampaignPlayer {
    int savings=0,day=0,difficulty=0,lives=0;
    bool completed=false;
};
struct StuntSettlement {
    int player=0,flags=0,pay=0,timeBonus=0;
    bool success=false,perfect=false,gameOver=false,completed=false;
};
// Native translation of the outer game loop (00:0272-069f). Presentation
// timing, result portraits and high-score entry are separate work in progress.
struct Campaign {
    std::array<CampaignPlayer,2> players{};
    int current=0;
    bool active=false,awaitingNext=false;
    StuntSettlement last{};
    void start(bool twoPlayers,int day=0,int difficulty=0){
        if(day<0||day>=5||difficulty<0||difficulty>=4)throw std::invalid_argument("Invalid campaign start");
        players={};for(int i=0;i<2;++i){players[i].day=day;players[i].difficulty=difficulty;players[i].lives=(i==0||twoPlayers)?5:0;}
        current=0;active=true;awaitingNext=false;last={};
    }
    StuntSettlement settle(int flags,int earned,int seconds,int extraLives=0){
        if(!active||awaitingNext||!(flags&1)||earned<0||seconds<0||extraLives<0)throw std::logic_error("Invalid campaign settlement");
        auto& p=players[current];p.lives=(p.lives+extraLives)&255;
        StuntSettlement result;result.player=current;result.flags=flags;result.success=(flags&2)!=0;result.perfect=(flags&4)!=0;
        if(result.success){
            int multiplier=result.perfect?2:1;
            result.pay=(earned%1000000)*multiplier;
            result.timeBonus=(flags&64)?0:seconds*multiplier;
            p.savings=(p.savings+result.pay+result.timeBonus)%1000000;
            if(++p.day==5){p.day=0;if(++p.difficulty==4){p.completed=true;p.lives=0;result.completed=true;}}
        }else{p.lives=(p.lives-1)&255;result.gameOver=p.lives==0;}
        awaitingNext=true;last=result;return result;
    }
    bool next(){
        if(!awaitingNext)throw std::logic_error("Campaign has no pending result");
        awaitingNext=false;
        if(!players[0].lives&&!players[1].lives){active=false;return false;}
        current^=1;if(!players[current].lives)current^=1;return true;
    }
};
int runCampaignTests();
}
