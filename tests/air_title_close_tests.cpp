// Native title song reset, third raster phase and forty unskippable steps.
#include "air_title_close.h"
#include <cstdio>
using namespace ticd;
int main(){
    int checks=0;auto require=[&](bool ok,const char* why){++checks;if(!ok)throw std::runtime_error(why);};
    try{
        AudioAssets audio;for(int v=0;v<4;++v)audio.commands.emplace(AudioAssets::key(v,0,false),MusicCommand{MusicOp::Stop,0,{}});
        AirTitleFade fade;fade.bgp=0xe4;fade.obp0=0xc4;fade.obp1=0xe0;auto& r=fade.layout.reset;auto& t=r.timing;
        r.servicesMasked=false;r.pendingRequests=0;r.lcdc=0xc3;r.stat=1;fade.layout.lyc=23;fade.layout.windowX=166;fade.layout.windowY=112;
        t.lcdEpoch=1000000;t.nextStat=t.lcdEpoch+33*70224+23*456;t.nextVBlank=t.lcdEpoch+33*70224+144*456;t.end=t.nextStat-12752;
        t.displays=580;t.stats=612;t.countdown=54;t.tick=65520;t.input={33,33,0};
        for(int mode=0;mode<3;++mode){NativeAudio sound(audio);sound.enabled=true;sound.song=13;sound.measureWork=true;
            int services=0,vectors=0,rasters=0,stores=0,steps=0,samples=0,phase3=0;bool reset=true;
            auto state=airTitleClose(fade,sound,
                [&](const char* name,int64_t,const AirTitleClose& s,int song){std::string n=name;
                    if(n=="musicReturned"){reset=false;require(song==1,"Completed reset selects title song");}
                    if(n=="centerStored"){++steps;require(s.steps==steps&&s.center==((-2*steps)&255)&&s.fade.layout.windowY==112-steps,"Every close step moves center and window independently");}
                    require(s.fade.layout.reset.timing.countdown==54,"Closing does not consume a result timer");},
                [&](unsigned index,int64_t,int,int,int work,int,int,const DisplayInput& input){
                    require(!reset&&index==unsigned(580+services)&&work==116,"No audio/display service observes partial music reset");
                    int expected=mode==0?0:mode==1?33:(samples%2?1:64);require(input.held==expected,"Display samples native input while fixed motion continues");++services;},
                [&](const char* kind,int64_t,AirIrqOwner owner){require(owner==(vectors==0?AirIrqOwner::SourceBoundary:AirIrqOwner::CounterWait),"Only initial music-reset STAT is accepted at a native source boundary");if(vectors==0)require(std::string(kind)=="stat","No VBlank during audio reset");++vectors;},
                [&](const char*,int64_t,int stat,int,int,int){++rasters;if(stat==3)++phase3;},[&](int64_t,int,int){++stores;},
                [&]{++samples;return mode==0?0:mode==1?33:(samples%2?1:64);});
            const auto& end=state.fade.layout.reset.timing;
            require(steps==40&&state.center==176&&state.fade.layout.windowY==72,"Close terminates at the blank-window update entry");
            require(services==40&&samples==40&&vectors==159&&rasters==238&&stores==518&&phase3==78,"Complete interrupted reset and three-phase closing raster");
            require(end.displays==620&&end.stats==731&&end.tick==24&&sound.ticks==40&&sound.song==1,"Actual returned counters/audio own the continuation");
            require(end.nextStat==t.lcdEpoch+73*70224+23*456&&end.nextVBlank==t.lcdEpoch+73*70224+144*456,"Closing retains the next periodic deadlines");
        }
        for(int mode=0;mode<6;++mode){auto bad=fade;NativeAudio sound(audio);sound.enabled=true;sound.song=13;sound.measureWork=true;
            if(mode==0)bad.layout.windowY=72;if(mode==1)bad.layout.reset.stat=2;if(mode==2)bad.bgp=0;if(mode==3)sound.song=1;
            if(mode==4)bad.layout.reset.timing.nextVBlank=bad.layout.reset.timing.end+1000;
            bool rejected=false;try{airTitleClose(bad,sound,[](auto...){},[](auto...){},[](auto...){},[](auto...){},[](auto...){},[mode]{return mode==5?15:0;});}catch(const std::runtime_error&){rejected=true;}
            require(rejected,"Unknown initial geometry, partial-reset observation or reset chord must reject");}
        // The final center extent merges the middle split with line 103.
        {auto title=fade.layout;title.reset.stat=2;title.reset.lcdc=0xfb;title.reset.scrollY=8;title.lyc=103;AirClock clock;
            int body=airTitleRasterWork(clock,title,176,t.end,[](auto...){},[](auto...){ });
            require(body==384&&title.reset.stat==1&&title.reset.scrollY==0&&title.lyc==23,"Merged edge follows the distinct phase-two bottom branch");}
        printf("PASS: %d native title-close assertions.\n",checks);return 0;
    }catch(const std::exception& e){fprintf(stderr,"FAIL after %d checks: %s\n",checks,e.what());return 1;}
}
