// First-instruction fade routing, frozen campaign and active audio continuation.
#include "air_title_entrance.h"
#include <cstdio>
#include <memory>
using namespace ticd;
int main(){int checks=0;auto require=[&](bool ok,const char* why){++checks;if(!ok)throw std::runtime_error(why);};
try{
    auto assets=AudioAssets::load(L"build/audio.dat");auto ui=std::make_unique<UiAssets>(UiAssets::load(L"build/ui.dat"));NativeAudio sound(assets);sound.measureWork=true;sound.playMusic(2);
    AirTitlePicture seed;seed.title.fresh.campaign.start(false,1,0);auto& l=seed.title.fresh.instruction.start.menu.page.close.fade.layout;auto& r=l.reset;auto& t=r.timing;
    r.servicesMasked=false;r.display=r.stat=5;r.lcdc=0xd1;l.lyc=95;t.end=2*AirClock::Frame+7000;t.nextStat=2*AirClock::Frame+95*456;t.nextVBlank=2*AirClock::Frame+144*456;
    t.tick=65520;t.countdown=54;t.displays=707;t.stats=936;t.lives=5;r.background.fill(19);seed.tiles.fill(37);
    int samples=0,services=0,stats=0,palettes=0,tails=0,points=0,selectors=0;std::vector<std::pair<int,int>> colors;
    auto out=airTitleEntrance(seed,sound,*ui,
        [&](const char* name,int64_t,int paletteCount,int waits,const AirTitlePicture& s){++points;const auto& r=s.title.fresh.instruction.start.menu.page.close.fade.layout.reset;
            if(std::string(name)=="palette"){++palettes;require(paletteCount==palettes,"Each incoming palette step has one owner");}
            if(std::string(name)=="tail"){++tails;require(waits==tails,"Each of the 32 actual waits completes separately");}
            require(r.timing.countdown==54&&s.title.fresh.campaign.players[0].lives==5,"Instruction reveal retains game countdown/lives");},
        [&](unsigned index,int64_t,int tick,int countdown,int display,int effects,int music,const DisplayInput&){require(index==unsigned(707+services)&&tick==((65520+services)&65535)&&countdown==54&&display==144&&effects==64&&music>=60,"Actual displays independently advance input/tick/music");++services;},
        [&](const char* kind,int64_t,AirIrqOwner owner){require(owner!=AirIrqOwner::Unqualified,"Every reveal vector has an explicit semantic acceptance owner");if(std::string(kind)=="stat")++stats;},
        [&](int64_t,int address,int value){if(address==0xc09d){++selectors;require(value==1,"First instruction owns exactly one alternate-flag enable");}
            else if(address==0xff42)require(value==0,"Empty instruction scroll remains zero");
            else{require(address==0xff47||address==0xff48||address==0xff49,"Reveal cannot modify picture/maps or unrelated game state");colors.emplace_back(address,value);}},
        [&]{++samples;return samples==10?8:0;});
    const auto& f=out.title.fresh.instruction.start.menu.page.close.fade;const auto& end=f.layout.reset.timing;
    require(points==76&&palettes==8&&tails==32&&samples==32&&services==32&&stats==32&&selectors==1,"Incoming reveal takes the first-instruction branch and all waits, even with a fresh Start");
    require(colors.size()==24,"All background/object palettes are written independently");
    for(int i=0;i<8;++i){int color=ui->fadePalettes[7-i];require(colors[3*i]==std::make_pair(0xff47,color)&&colors[3*i+1]==std::make_pair(0xff49,color&0xf3)&&colors[3*i+2]==std::make_pair(0xff48,color&0xcf),"Fade masks and order follow decoded palette data");}
    require(end.tick==16&&end.countdown==54&&end.displays==739&&end.stats==968&&f.layout.reset.alternate==1,"Return preserves campaign and carries actual future-instruction state");
    require(f.bgp==0xe4&&f.obp0==0xc4&&f.obp1==0xe0&&sound.song==2&&sound.enabled&&sound.ticks==32,"Reveal ends visible while the native instruction song continues");
    require(out.tiles==seed.tiles&&f.layout.reset.background==r.background&&f.layout.reset.window==r.window&&f.layout.reset.objects==r.objects,"Reveal preserves every picture/map/object byte");
    for(int mode=0;mode<8;++mode){auto bad=seed;auto& f=bad.title.fresh.instruction.start.menu.page.close.fade;auto& r=f.layout.reset;
        if(mode==0)r.alternate=1;if(mode==1)f.bgp=0xe4;if(mode==2)r.display=10;if(mode==3)r.stat=0;if(mode==4)r.timing.lives=4;
        if(mode==5)r.objects[255]=1;if(mode==6)r.window[1023]=1;if(mode==7)bad.title.fresh.campaign.active=false;bool rejected=false;
        try{airTitleEntrance(bad,sound,*ui,[](auto...){},[](auto...){},[](auto...){},[](auto...){ });}catch(const std::exception&){rejected=true;}
        require(rejected,"A later instruction/result/uncleared entry cannot borrow first-instruction timing");}
    printf("PASS: %d native title-entrance assertions.\n",checks);return 0;
}catch(const std::exception& e){fprintf(stderr,"FAIL after %d checks: %s\n",checks,e.what());return 1;}}
