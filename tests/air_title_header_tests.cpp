// Native campaign values, instruction callback ownership and shared layouts.
#include "air_title_header.h"
#include <cstdio>
using namespace ticd;
int main(){int checks=0;auto require=[&](bool ok,const char* why){++checks;if(!ok)throw std::runtime_error(why);};
try{
    AudioAssets audio;NativeAudio sound(audio);sound.measureWork=true;
    AirInstructionHeaderAssets assets;assets.playerNames[0]={1,2,3};assets.playerNames[1]={4,5,6};
    for(auto& list:assets.layouts)list={{4,0,0}};
    assets.layouts[0]={{1,0,0},{5,0,0},{4,0,0}};
    assets.layouts[1]={{0,10,0},{4,0,0}};assets.layouts[2]={{0,11,0},{4,0,0}};
    for(int day=0;day<5;++day)assets.layouts[3+day]={{0,20+day,0},{4,0,0}};
    for(int diff=0;diff<4;++diff)assets.layouts[8+diff]={{0,30+diff,0},{4,0,0}};
    AirTitleResume initial;auto& l=initial.fresh.instruction.start.menu.page.close.fade.layout;auto& r=l.reset;auto& t=r.timing;
    r.servicesMasked=false;r.pendingRequests=0;r.display=r.stat=5;r.lcdc=0xd1;l.lyc=95;
    t.end=2*AirClock::Frame+100;t.lcdEpoch=0;t.nextStat=2*AirClock::Frame+95*456;t.nextVBlank=2*AirClock::Frame+144*456;
    t.tick=65535;t.countdown=54;t.displays=702;t.stats=931;t.lives=5;t.input={8,0,8};
    initial.fresh.campaign.start(false,1,0);
    for(int day=0;day<5;++day)for(int diff=0;diff<4;++diff){auto seed=initial;seed.fresh.campaign.start(false,day,diff);sound.stop();
        int points=0,services=0,samples=0,polls=0,scrolls=0;std::vector<int> glyphs;std::vector<int64_t> addresses;
        auto out=airTitleHeader(seed,sound,assets,
            [&](const char*,int64_t cycle,const AirTitleResume& s){++points;const auto& r=s.fresh.instruction.start.menu.page.close.fade.layout.reset;
                require(r.timing.end==cycle&&r.timing.countdown==54&&s.fresh.campaign.players[0].lives==5&&!s.result,"Header boundaries retain countdown, native lives and cleared result");},
            [&](unsigned index,int64_t,int tick,int countdown,int display,int effects,int music,const DisplayInput& input){
                require(index==702&&tick==65535&&countdown==54&&display==144&&effects==64&&music==60,"Instruction callback retains countdown with stopped audio work");
                require(!input.held&&!input.pressed,"First wait samples fresh display input and clears stale edge");++services;},
            [&](const char*,int64_t,AirIrqOwner owner){require(owner!=AirIrqOwner::Unqualified,"Header owns every service acceptance");},
            [&](int64_t,int mode){require(mode>=0&&mode<=3,"Text retains an owned readiness read");++polls;},
            [&](int64_t,int address,int value){if(address==0xff42){require(value==0,"Instruction callback preserves zero vertical scroll");++scrolls;}
                else{require(address>=0x9800&&address<0x9c00,"Header glyph destination stays in background map");addresses.push_back(address);glyphs.push_back(value);}},
            [&]{++samples;return 0;});
        const auto& r=out.fresh.instruction.start.menu.page.close.fade.layout.reset;const auto& end=r.timing;
        require(glyphs==std::vector<int>({1,2,3,6,10,20+day,11,30+diff}),"Header substitutes native player/lives/day/difficulty into independent layouts");
        require(points==12&&services==1&&samples==1&&polls>=8&&scrolls>=1,"All header stages finish with their own counter wait");
        require(end.tick==0&&end.countdown==54&&end.displays==703&&end.lives==5&&!sound.enabled,"Instruction display rolls tick over without charging countdown/lives");
        require(end.nextStat>end.end&&end.nextVBlank>end.end&&end.lcdEpoch==t.lcdEpoch,"Header preserves LCD epoch and future deadlines");
        for(size_t i=0;i<glyphs.size();++i)require(r.background[addresses[i]-0x9800]==glyphs[i],"Returned map owns every native glyph");
        require(r.window==initial.fresh.instruction.start.menu.page.close.fade.layout.reset.window&&r.objects==initial.fresh.instruction.start.menu.page.close.fade.layout.reset.objects,"Header leaves window and objects unchanged");
    }
    for(int mode=0;mode<13;++mode){auto bad=initial;auto& l=bad.fresh.instruction.start.menu.page.close.fade.layout;auto& r=l.reset;
        if(mode==0)bad.result=33;if(mode==1)r.pendingRequests=2;if(mode==2)r.servicesMasked=true;if(mode==3)r.stat=0;if(mode==4)r.display=10;
        if(mode==5)r.background[1023]=1;if(mode==6)r.objects[255]=1;if(mode==7)r.window[1023]=1;if(mode==8)r.timing.lives=4;
        if(mode==9)bad.fresh.campaign.current=1;if(mode==10)r.timing.perfect=true;if(mode==11)r.timing.nextStat=r.timing.end;if(mode==12)l.lyc=120;
        bool rejected=false;try{airTitleHeader(bad,sound,assets,[](auto...){},[](auto...){},[](auto...){},[](auto...){},[](auto...){ });}catch(const std::exception&){rejected=true;}
        require(rejected,"Different routing, geometry or incomplete clear cannot enter the post-title header");
    }
    printf("PASS: %d native title-header assertions.\n",checks);return 0;
}catch(const std::exception& e){fprintf(stderr,"FAIL after %d checks: %s\n",checks,e.what());return 1;}}
