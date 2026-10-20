// Complete native image transfer with synthetic data and real local music.
#include "air_title_picture.h"
#include <memory>
#include <cstdio>
using namespace ticd;
int main(){int checks=0;auto require=[&](bool ok,const char* why){++checks;if(!ok)throw std::runtime_error(why);};
try{
    auto assets=AudioAssets::load(L"build/audio.dat");NativeAudio sound(assets);sound.measureWork=true;
    auto ui=std::make_unique<UiAssets>();
    for(int stage=1;stage<=2;++stage){
        for(int tile=52;tile<116;++tile)for(int pixel=0;pixel<64;++pixel)ui->instructions[stage].tiles[tile*64+pixel]=stage;
        for(auto& value:ui->instructions[stage].map)value=37+stage;
        AirTitleResume seed;seed.fresh.campaign.start(false,stage,0);auto& l=seed.fresh.instruction.start.menu.page.close.fade.layout;auto& r=l.reset;auto& t=r.timing;
        r.servicesMasked=false;r.display=r.stat=5;r.lcdc=0xd1;l.lyc=95;t.end=2*AirClock::Frame+144*456+3000;
        t.nextStat=3*AirClock::Frame+95*456;t.nextVBlank=3*AirClock::Frame+144*456;t.tick=65535;t.countdown=54;t.displays=703;t.stats=932;t.lives=5;
        r.background.fill(19);sound.stop();int cells=0,tiles=0,polls=0,services=0,points=0,scrolls=0;
        auto out=airTitlePicture(seed,sound,*ui,
            [&](const char* name,int64_t,const AirTitlePicture& s){++points;const auto& t=s.title.fresh.instruction.start.menu.page.close.fade.layout.reset.timing;
                require(t.countdown==54&&s.title.fresh.campaign.players[0].lives==5,"Instruction picture retains native countdown and fresh lives");
                if(std::string(name)=="musicReady")require(sound.enabled&&sound.song==2,"Instruction starts its own native song");},
            [&](unsigned index,int64_t,int tick,int countdown,int display,int effects,int music,const DisplayInput&){
                require(index==unsigned(703+services)&&tick==((65535+services)&65535)&&countdown==54&&display==144&&effects==64&&music>=60,"Only actual displays advance music/tick with callback 5");++services;},
            [&](const char*,int64_t,AirIrqOwner owner){require(owner==AirIrqOwner::SourceBoundary,"Picture transfers own each service acceptance boundary");},
            [&](int64_t,int mode){require(mode>=0&&mode<=3,"Every tile/map readiness read has owned geometry");++polls;},
            [&](const char* kind,int64_t,int address,int value){std::string type=kind;
                if(type=="tile"){require(address==0x8340+tiles&&value==((tiles%2==(stage==1?0:1))?255:0),"Solid synthetic pixels repack into exact independent bitplanes");++tiles;}
                else if(type=="map"){require(address==0x9800+(3+cells/10)*32+5+cells%10&&value==37+stage,"Picture map keeps its 32-column pitch and glyph value");++cells;}
                else{require(type=="scroll"&&address==0xff42&&!value,"Only qualified callback scroll stores occur outside image storage");++scrolls;}});
        const auto& after=out.title.fresh.instruction.start.menu.page.close.fade.layout.reset;
        require(points==9&&tiles==1024&&cells==90&&polls>1114&&services>0&&scrolls>0,"All picture bytes/cells and busy reads are retained");
        require(after.timing.tick==((65535+services)&65535)&&after.timing.countdown==54&&sound.song==2&&sound.enabled,"Picture return carries actual continuing music and timing");
        for(int i=0;i<1024;++i){int row=i/32,col=i%32;require(after.background[i]==(row>=3&&row<12&&col>=5&&col<15?37+stage:19),"Image changes only its own background rectangle");}
        require(after.objects==r.objects&&after.window==r.window,"Picture preserves full object/window storage");
        for(int mode=0;mode<7;++mode){sound.stop();auto bad=seed;auto& r=bad.fresh.instruction.start.menu.page.close.fade.layout.reset;
            if(mode==0)r.stat=0;if(mode==1)r.pendingRequests=2;if(mode==2)r.servicesMasked=true;if(mode==3)r.objects[255]=1;
            if(mode==4)r.window[1023]=1;if(mode==5)bad.fresh.campaign.players[0].day=4;if(mode==6)r.timing.lives=4;
            bool rejected=false;try{airTitlePicture(bad,sound,*ui,[](auto...){},[](auto...){},[](auto...){},[](auto...){},[](auto...){ });}catch(const std::exception&){rejected=true;}
            require(rejected,"Unowned post-title image entry rejects rather than borrowing another route");
        }
    }
    printf("PASS: %d native title-picture assertions.\n",checks);return 0;
}catch(const std::exception& e){fprintf(stderr,"FAIL after %d checks: %s\n",checks,e.what());return 1;}}
