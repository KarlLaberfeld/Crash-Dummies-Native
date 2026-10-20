// Full menu duration, held-vs-fresh input, tick wrap and inherited geometry.
#include "air_title_menu.h"
#include <cstdio>
using namespace ticd;
int main(){
    int checks=0;auto require=[&](bool ok,const char* why){++checks;if(!ok)throw std::runtime_error(why);};
    try{
        AudioAssets assets;AirTitlePage initial;initial.cleared=2;initial.rows=10;initial.opened=40;
        auto& l=initial.close.fade.layout;auto& r=l.reset;auto& t=r.timing;
        l.windowX=166;l.windowY=112;l.lyc=23;r.stat=1;r.lcdc=0xc3;r.servicesMasked=false;
        t.end=1000000+100*70224+144*456+4000;t.lcdEpoch=1000000;
        t.nextStat=t.lcdEpoch+101*70224+23*456;t.nextVBlank=t.lcdEpoch+101*70224+144*456;
        t.tick=65520;t.countdown=54;t.displays=662;t.stats=854;
        r.background.fill(19);r.window.fill(23);
        for(int held:{0,33,8,4}){
            auto page=initial;page.close.fade.layout.reset.timing.input={held,held,0};
            NativeAudio sound(assets);sound.enabled=true;sound.song=1;sound.measureWork=true;
            int samples=0,points=0,waits=0,stores=0,displays=0,stats=0;
            auto menu=airTitleMenuIdle(page,sound,
                [&](const char* name,int64_t,const AirTitleMenu& s){++points;if(std::string(name)=="wait")++waits;
                    require(s.page.close.fade.layout.reset.timing.countdown==54,"The menu duration is separate from the frozen game countdown");},
                [&](unsigned index,int64_t,int tick,int countdown,int work,int,int,const DisplayInput& input){
                    require(index==unsigned(662+samples-1)&&tick==((65520+samples-1)&65535)&&countdown==54&&work==116,"Actual input/display counter and fixed callback ownership");
                    require(input.held==held&&!input.pressed,"Held Start/Select/actions cannot become fresh menu edges");},
                [&](const char* kind,int64_t,AirIrqOwner owner){require(owner==AirIrqOwner::CounterWait||owner==AirIrqOwner::SourceBoundary,"Every accepted vector retains its native boundary owner");if(std::string(kind)=="vblank")++displays;else ++stats;},
                [](auto...){},[&](int64_t,int address,int value){if(address==0xc03e){++stores;require(value==1,"Timeout advances the actual page index once");}
                    else require(address==0xff40||address==0xff42||address==0xff45||address==0xc099,"Idle work cannot modify maps or other source state");},[&]{++samples;return held;});
            const auto& out=menu.page.close.fade.layout.reset;
            require(points==4324&&waits==480&&samples==480&&displays==480&&stats==960,"Exactly 480 completed waits and both raster splits per display");
            require(stores==1&&menu.index==1&&menu.remaining==0&&menu.waits==480,"Complete timeout stops before the next page closes");
            require(out.timing.displays==1142&&out.timing.stats==1814&&out.timing.tick==464&&sound.ticks==480,"Full inherited tick wrap and service/audio counts");
            require(out.background==r.background&&out.window==r.window&&out.objects==r.objects,"Idle work preserves the entire inherited graphics storage");
            require(out.timing.nextStat>out.timing.end&&out.timing.nextVBlank>out.timing.end&&out.timing.lcdEpoch==t.lcdEpoch,"Next service deadlines derive from the retained LCD epoch");
        }
        for(int mode=0;mode<11;++mode){auto page=initial;NativeAudio sound(assets);sound.enabled=true;sound.song=1;sound.measureWork=true;
            if(mode==0)page.opened=39;if(mode==1)page.close.center=2;if(mode==2)page.close.fade.layout.windowY=111;
            if(mode==3)page.close.fade.layout.reset.objects[3]=1;if(mode==4)page.close.fade.layout.reset.timing.displays=661;
            if(mode==5)sound.song=13;if(mode==6)page.close.fade.layout.reset.scrollX=1;
            int samples=0;bool rejected=false;
            try{airTitleMenuIdle(page,sound,[](auto...){},[](auto...){},[](auto...){},[](auto...){},[](auto...){},[&]{++samples;return mode==7?15:mode==8?-1:mode==9?256:mode==10&&samples==200?8:0;});}
            catch(const std::runtime_error&){rejected=true;}
            require(rejected,"Unknown geometry/audio, reset chord, invalid samples and fresh menu branches must reject");
            if(mode==10)require(samples==200,"A late fresh edge rejects where it occurs, without silently completing timeout");
        }
        for(int mask:{1,2,4,8,9,12,7})for(int first:{0,32}){
            auto page=initial;page.close.fade.layout.reset.timing.input={33,33,0};
            NativeAudio sound(assets);sound.enabled=true;sound.song=1;sound.measureWork=true;
            int samples=0,selectors=0,pages=0;std::vector<std::string> names;
            auto menu=airTitleMenuIdle(page,sound,
                [&](const char* name,int64_t,const AirTitleMenu&){names.emplace_back(name);},
                [&](unsigned,int64_t,int,int,int,int,int,const DisplayInput& input){
                    require(input.held==(samples==1?first:samples==2?0:mask)&&input.pressed==(samples==3?mask:0),"A partial release can retain old bits but must not create a fresh edge");},
                [](auto...){},[](auto...){},[&](int64_t,int address,int value){
                    if(address==0xc0b5||address==0xc0b6){++selectors;require(value==(address==0xc0b5?0x15:0x2b),"Mismatched actions reset both unlock-selector bytes");}
                    if(address==0xc03e)++pages;
                },[&]{++samples;return samples==1?first:samples==2?0:mask;},true);
            int route=mask&8?2:mask&4?3:1;
            require(samples==3&&menu.waits==3&&menu.remaining==478&&selectors==2,"Fresh actions stop before another wait or duration decrement");
            require(menu.route==route&&menu.index==(route==1)&&pages==(route==1),"Start precedes Select, which precedes A/B; only A/B advance the page");
            require(menu.page.close.fade.layout.reset.background==r.background&&menu.page.close.fade.layout.reset.window==r.window&&sound.ticks==3,"Action branch preserves graphics and advances audio for actual displays only");
            require((std::find(names.begin(),names.end(),"selectDecision")!=names.end())&&names.back()=="end","Earlier idle iterations still include ordinary decisions");
        }
        for(int mask:{64,128,32,16,15}){NativeAudio sound(assets);sound.enabled=true;sound.song=1;sound.measureWork=true;bool rejected=false;
            try{airTitleMenuIdle(initial,sound,[](auto...){},[](auto...){},[](auto...){},[](auto...){},[](auto...){},[&]{return mask;},true);}
            catch(const std::runtime_error&){rejected=true;}require(rejected,"Action ownership cannot admit direction/unlock progression or reset chords");}
        printf("PASS: %d native title-menu assertions.\n",checks);return 0;
    }catch(const std::exception& e){fprintf(stderr,"FAIL after %d checks: %s\n",checks,e.what());return 1;}
}
