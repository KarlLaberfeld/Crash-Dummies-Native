// Start fade/stop continuation: synthetic audio and native state only.
#include "air_title_start.h"
#include <cstdio>
#include <memory>
using namespace ticd;
int main(){
    int checks=0;auto require=[&](bool ok,const char* why){++checks;if(!ok)throw std::runtime_error(why);};
    try{
        AudioAssets audio;auto ui=std::make_unique<UiAssets>();ui->fadePalettes={0xe4,0xe4,0xe4,0xa4,0x90,0x50,0x50,0};
        AirTitleMenu menu;menu.route=2;menu.waits=3;menu.remaining=478;menu.page.cleared=2;menu.page.rows=10;menu.page.opened=40;
        auto& f=menu.page.close.fade;auto& l=f.layout;auto& r=l.reset;auto& t=r.timing;
        f.bgp=0xe4;f.obp0=0xc4;f.obp1=0xe0;l.windowX=166;l.windowY=112;l.lyc=23;r.stat=1;r.lcdc=0xc3;r.servicesMasked=false;
        t.lcdEpoch=1000000;t.end=t.lcdEpoch+100*70224+144*456+4000;t.nextStat=t.lcdEpoch+101*70224+23*456;t.nextVBlank=t.lcdEpoch+101*70224+144*456;
        t.displays=665;t.stats=860;t.tick=65520;t.countdown=54;t.input={8,0,8};r.background.fill(19);r.window.fill(23);
        for(int held:{0,8,1,64}){NativeAudio sound(audio);sound.enabled=true;sound.song=1;sound.measureWork=true;int samples=0,waits=0,colors=0,audioStores=0,stats=0;
            auto started=airTitleStart(menu,sound,*ui,
                [&](const char* name,int64_t,const AirTitleStart& s,bool enabled){
                    if(std::string(name)=="wait")++waits;require(enabled==(std::string(name)!="audioDisabled"&&std::string(name)!="end"),"Logical audio stops at the owned completion boundary");
                    require(s.menu.page.close.fade.layout.reset.timing.countdown==54,"Start UI work preserves the frozen game countdown");},
                [&](unsigned index,int64_t,int tick,int countdown,int display,int,int,const DisplayInput& input){
                    require(index==unsigned(665+samples-1)&&tick==((65520+samples-1)&65535)&&countdown==54&&display==116&&input.held==held,"Each actual display owns input, wrapping tick and audio work");},
                [&](const char* kind,int64_t,AirIrqOwner owner){require(owner==AirIrqOwner::CounterWait||owner==AirIrqOwner::SourceBoundary,"Raster reset interruption retains an identified native boundary");if(std::string(kind)=="stat")++stats;},
                [](auto...){},[&](int64_t,int address,int value){if(address==0xff47||address==0xff48||address==0xff49)++colors;
                    if(address==0xff26||address==0xffcf){++audioStores;require(value==0,"Both identified audio-disable stores retain zero");}
                    require(address<0x9800||address>=0xa000,"Fade and stop never write map storage");},[&]{++samples;return held;});
            const auto& out=started.menu.page.close.fade;const auto& end=out.layout.reset.timing;
            require(samples==33&&waits==32&&started.palettes==8&&started.waits==32&&colors==24&&audioStores==2,"All eight palette steps, thirty-two fade waits and final wait remain unskippable");
            require(!out.bgp&&!out.obp0&&!out.obp1&&!sound.enabled&&sound.song==-1&&sound.pendingEffect==-1&&sound.ticks==33,"The transition reaches a white screen and stopped native audio");
            require(end.displays==698&&end.stats==860+stats&&end.tick==17&&end.countdown==54&&end.nextStat>end.end&&end.nextVBlank>end.end,"Final counters, tick wrap and future deadlines continue from actual execution");
            require(out.layout.reset.background==r.background&&out.layout.reset.window==r.window&&out.layout.reset.objects==r.objects,"Complete inherited graphics storage is preserved");
        }
        for(int mode=0;mode<8;++mode){auto bad=menu;NativeAudio sound(audio);sound.enabled=true;sound.song=1;sound.measureWork=true;
            if(mode==0)bad.route=3;if(mode==1)bad.remaining=477;if(mode==2)bad.page.close.fade.bgp=0;if(mode==3)bad.page.close.fade.layout.reset.objects[2]=1;
            if(mode==4)bad.page.close.fade.layout.reset.timing.input.pressed=0;if(mode==5)sound.song=13;
            bool rejected=false;try{airTitleStart(bad,sound,*ui,[](auto...){},[](auto...){},[](auto...){},[](auto...){},[](auto...){},[mode]{return mode==6?15:mode==7?256:0;});}catch(const std::runtime_error&){rejected=true;}
            require(rejected,"Wrong route/state/song/graphics, reset chord and invalid raw input reject");}
        printf("PASS: %d native title-Start assertions.\n",checks);return 0;
    }catch(const std::exception& e){fprintf(stderr,"FAIL after %d checks: %s\n",checks,e.what());return 1;}
}
