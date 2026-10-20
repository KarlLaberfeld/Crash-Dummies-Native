// Native retained choices, both life-init branches and masked window/LCD work.
#include "air_title_campaign.h"
#include <cstdio>
using namespace ticd;
int main(){
    int checks=0;auto require=[&](bool ok,const char* why){++checks;if(!ok)throw std::runtime_error(why);};
    try{
        AudioAssets assets;NativeAudio sound(assets);sound.ticks=123;
        AirTitleInstruction prefix;auto& l=prefix.start.menu.page.close.fade.layout;auto& r=l.reset;auto& t=r.timing;
        r.servicesMasked=true;r.pendingRequests=3;r.display=r.stat=5;r.lcdc=0x51;l.lyc=95;
        t.displays=698;t.stats=927;t.countdown=54;t.tick=65535;t.input={0,0,0};t.lcdEpoch=1000000;t.end=1200000;
        r.background.fill(19);r.window.fill(23);
        Campaign previous;previous.players[0].day=4;previous.players[1].day=2;previous.players[0].difficulty=3;previous.players[1].difficulty=1;
        int64_t single=0;
        for(int two=0;two<2;++two)for(int day=0;day<5;++day)for(int difficulty=0;difficulty<4;++difficulty){
            int points=0,polls=0,cells=0,stores=0;int64_t lastPoll=0;
            auto fresh=airTitleCampaign(prefix,previous,{day,difficulty,bool(two)},sound,
                [&](const char* name,int64_t,const AirTitleCampaign& s){
                    ++points;const auto& r=s.instruction.start.menu.page.close.fade.layout.reset;const auto& p=s.campaign.players;
                    require(r.servicesMasked&&r.pendingRequests==3,"Restart keeps services masked and retains pending requests before EI");
                    if(std::string(name)=="begin")require(p[0].day==4&&p[1].day==2&&p[0].difficulty==3&&p[1].difficulty==1,"Native prior player choices are retained until their stores");
                    if(std::string(name)=="daysReady")require(p[0].day==day&&p[1].day==day&&p[0].difficulty==3&&p[1].difficulty==1,"Day stores precede difficulty stores");
                    if(std::string(name)=="difficultyReady")require(p[0].difficulty==difficulty&&p[1].difficulty==difficulty&&!p[0].lives&&!p[1].lives,"Difficulty stores precede life initialization");
                    if(std::string(name)=="livesReady")require(p[0].lives==5&&p[1].lives==(two?5:0)&&s.campaign.active,"Both players receive independent life values before map work");
                },[&](int64_t cycle,int mode){require(mode==0&&(!polls||cycle-lastPoll==144),"Every masked cell retains one independent ready read");lastPoll=cycle;++polls;},
                [&](int64_t cycle,int address,int value){++stores;if(address>=0x9800&&address<0xa000){require(address==0x9c00+cells&&value==0&&cycle-lastPoll==28,"Window stores keep their own address and readiness boundary");++cells;}});
            const auto& out=fresh.instruction.start.menu.page.close.fade.layout;const auto& s=out.reset;const auto& end=s.timing;
            require(points==9&&polls==1024&&cells==1024&&stores==1032,"Full masked setup has no shortened or doubled clear");
            require(s.background==r.background&&s.objects==r.objects&&std::all_of(s.window.begin(),s.window.end(),[](int v){return !v;}),"Clear covers full window and preserves background/object storage");
            require(end.tick==65535&&end.displays==698&&end.stats==927&&end.countdown==54&&!end.input.held&&!end.input.pressed&&sound.ticks==123,"Masked setup executes no display, input or audio services");
            require(end.end==end.lcdEpoch+20&&end.nextStat==end.lcdEpoch+95*456&&end.nextVBlank==end.lcdEpoch+144*456&&s.lcdc==0xd1,"Restart creates a fresh LCD epoch and future deadlines before EI");
            require(fresh.campaign.current==0&&fresh.campaign.active&&end.lives==5&&fresh.campaign.players[0].day==day&&fresh.campaign.players[1].difficulty==difficulty,"Actual native campaign and current-life continuation receive selected values");
            if(!two)single=end.end;else require(end.end==single-4,"Taken two-player branch omits the single-player zero-load path");
        }
        for(int mode=0;mode<10;++mode){auto bad=prefix;auto old=previous;AirTitleChoices choices{1,0,false};
            if(mode==0)bad.start.menu.page.close.fade.layout.reset.servicesMasked=false;
            if(mode==1)bad.start.menu.page.close.fade.layout.reset.pendingRequests=0;
            if(mode==2)old.active=true;if(mode==3)old.players[1].lives=1;if(mode==4)old.players[0].savings=1;
            if(mode==5)old.players[0].completed=true;if(mode==6)choices.day=5;if(mode==7)choices.difficulty=4;
            if(mode==8)choices.day=-1;if(mode==9)old.current=1;bool rejected=false;
            try{airTitleCampaign(bad,old,choices,sound,[](auto...){},[](auto...){},[](auto...){ });}catch(const std::exception&){rejected=true;}
            require(rejected,"Invalid native choice/routing/state cannot silently restart a campaign");
        }
        printf("PASS: %d native title-campaign assertions.\n",checks);return 0;
    }catch(const std::exception& e){fprintf(stderr,"FAIL after %d checks: %s\n",checks,e.what());return 1;}
}
