// Native title raster/fade ownership; synthetic audio, no original recording.
#include "air_title_fade.h"
#include <cstdio>
#include <memory>
using namespace ticd;
int main(){
    int checks=0;auto require=[&](bool condition,const char* why){++checks;if(!condition)throw std::runtime_error(why);};
    try{
        AudioAssets audio;auto ui=std::make_unique<UiAssets>();ui->fadePalettes={0xe4,0xe4,0xe4,0xa4,0x90,0x50,0x50,0};
        AirTitleLayout layout;auto& r=layout.reset;auto& t=r.timing;
        r.pendingRequests=3;r.servicesMasked=true;r.lcdc=0xc3;r.stat=1;layout.lyc=23;layout.windowX=166;layout.windowY=112;
        t.lcdEpoch=1000000;t.end=t.lcdEpoch+20;t.nextStat=t.lcdEpoch+23*456;t.nextVBlank=t.lcdEpoch+144*456;
        t.displays=t.stats=546;t.tick=65530;t.countdown=54;t.input={255,33,0};
        for(int held:{0,1,33,64,-1}){
            NativeAudio sound(audio);sound.enabled=true;sound.song=13;sound.measureWork=true;
            int samples=0,services=0,vectors=0,rasters=0,stores=0,waits=0;bool top=true;
            auto state=airTitleFade(layout,sound,*ui,
                [&](const char* name,int64_t,int,int countdown,const AirTitleFade&){require(countdown==54,"Title services must not decrement result countdown");if(std::string(name)=="wait")++waits;},
                [&](unsigned index,int64_t,int,int countdown,int display,int,int,const DisplayInput& input){
                    require(index==unsigned(546+services)&&countdown==54&&display==116,"Title callback owns normal display dispatch only");
                    int expected=held<0?(samples%2?1:64):held;
                    require(input.held==expected&&input.pressed==(held<0&&samples>1?expected:0),"Held sentinel and later fresh edges retain independent samples");++services;},
                [&](const char*,int64_t,AirIrqOwner owner){require(owner==(vectors<2?AirIrqOwner::PendingStartup:AirIrqOwner::CounterWait),"Pending and HALT-owned vector acceptance remain distinct");++vectors;},
                [&](const char* name,int64_t,int stat,int lcdc,int scrollY,int lyc){
                    bool before=std::string(name)=="begin";bool upper=before?top:!top;
                    require(stat==(upper?1:2)&&lcdc==(upper?0xc3:0xfb)&&scrollY==(upper?0:88)&&lyc==(upper?23:103),"Both raster branches retain independent geometry");
                    if(!before)top=!top;++rasters;},[&](int64_t,int,int){++stores;},[&]{++samples;return held<0?(samples%2?1:64):held;});
            const auto& end=state.layout.reset.timing;
            require(samples==34&&services==34&&vectors==100&&rasters==132&&stores==321&&waits==32,"Complete fade, pending services and final wait");
            require(end.displays==580&&end.stats==612&&end.tick==28&&end.countdown==54,"Title display ticks wrap independently of the retained result timer");
            require(sound.ticks==34&&sound.enabled&&sound.song==13,"Every display services existing music without selecting a new song");
            require(state.bgp==0xe4&&state.obp0==0xc4&&state.obp1==0xe0,"Incoming fade reaches decoded full palettes");
            require(end.nextStat==t.lcdEpoch+33*70224+23*456&&end.nextVBlank==t.lcdEpoch+33*70224+144*456,"Alternating raster work retains next-frame deadlines");
            require(!state.layout.reset.servicesMasked&&!state.layout.reset.pendingRequests,"Both initial requests consumed exactly once");
        }
        for(int mode=0;mode<11;++mode){auto invalid=layout;NativeAudio sound(audio);sound.enabled=true;sound.song=13;sound.measureWork=true;
            if(mode==0)invalid.reset.stat=2;if(mode==1)invalid.lyc=103;if(mode==2)invalid.reset.scrollY=1;if(mode==3)invalid.windowX=7;
            if(mode==4)invalid.reset.pendingRequests=0;if(mode==5)invalid.reset.timing.end+=4;if(mode==6)invalid.reset.timing.input.held=33;if(mode==7)sound.song=1;
            if(mode==9)++invalid.reset.timing.nextStat;if(mode==10)++invalid.reset.timing.nextVBlank;
            bool rejected=false;try{airTitleFade(invalid,sound,*ui,[](auto...){},[](auto...){},[](auto...){},[](auto...){},[](auto...){},[mode]{return mode==8?15:0;});}catch(const std::runtime_error&){rejected=true;}
            require(rejected,"Unknown center geometry/startup/reset input must reject");}
        {AirClock clock;clock.now=100;clock.rasterWork=[](int64_t){return -1;};bool rejected=false;
            try{clock.stat();}catch(const std::runtime_error&){rejected=true;}require(rejected&&clock.now==100&&clock.statServices==0,"Unknown raster work cannot advance the shared clock");}
        printf("PASS: %d native title-fade assertions.\n",checks);return 0;
    }catch(const std::exception& e){fprintf(stderr,"FAIL after %d checks: %s\n",checks,e.what());return 1;}
}
