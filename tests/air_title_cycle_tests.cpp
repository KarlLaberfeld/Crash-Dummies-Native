#include "air_title_cycle.h"
#include <cstdio>
#include <memory>
using namespace ticd;
int main(){int checks=0;auto require=[&](bool ok,const char* why){++checks;if(!ok)throw std::runtime_error(why);};try{
    auto ui=std::make_unique<UiAssets>(UiAssets::load(L"build/ui.dat"));auto audio=AudioAssets::load(L"build/audio.dat");auto texts=AirResultTextAssets::load("build/title-text.dat");NativeAudio sound(audio);sound.measureWork=true;sound.playMusic(1);
    AirTitleMenu menu;menu.index=1;menu.route=1;menu.waits=3;menu.remaining=478;menu.page.cleared=2;menu.page.rows=10;menu.page.opened=40;
    auto& l=menu.page.close.fade.layout;auto& r=l.reset;auto& t=r.timing;l.bootShown=true;l.windowX=166;l.windowY=112;l.lyc=23;r.servicesMasked=false;r.stat=1;r.lcdc=195;r.background.fill(19);r.window=ui->titleMaps[0];t.countdown=54;t.displays=665;t.stats=860;t.tick=65000;t.end=200*AirClock::Frame+144*456+2400;t.nextStat=201*AirClock::Frame+23*456;t.nextVBlank=201*AirClock::Frame+144*456;
    auto noop=[](auto...){};int64_t prior=t.end;unsigned expected=665;int selectedScores=0;
    for(int index:{1,2,3,4,0}){
        auto page=airTitleCycle(menu,sound,*ui,texts,[&](const char* name,int64_t,const AirTitleMenu& state,int,int,int,int,int){require(state.index==index,"Page composition retains the actual selector");if(std::string(name)=="scoreRow")++selectedScores;},
            [&](unsigned n,int64_t,int,int countdown,int display,int effects,int music,const DisplayInput&){require(n==expected++&&countdown==54&&display==116&&effects>=64&&music>=60,"Carousel owns every live audio/display service");},noop,noop,noop,noop,[]{return 0;});
        const auto& r=page.page.close.fade.layout.reset;require(r.timing.end>prior&&r.timing.nextStat>r.timing.end&&r.timing.nextVBlank>r.timing.end,"Reopened page retains independent future deadlines");prior=r.timing.end;
        require(page.remaining==(index==2||index==4?960:480)&&!page.route&&page.page.close.center==0,"Original page duration is loaded at the actual reopening endpoint");
        for(int row=14;row<24;++row)for(int column=0;column<32;++column){int address=32*row+column;int expected=column<20?ui->titleMaps[index][address]:0;require(r.window[address]==expected,"Every title page and high-score field matches local independently extracted map data");}
        require(r.background[0]==19&&sound.enabled&&sound.song==1,"Carousel preserves background and live title music");
        if(index==0){menu=page;break;}
        auto inherited=page;menu=airTitleMenuIdle(page.page,sound,noop,[&](unsigned n,int64_t,int,int,int,int,int,const DisplayInput&){require(n==expected++,"Idle service indices continue from the page owner");},noop,noop,noop,[]{return 0;},true,true,&inherited);
        require(menu.waits==(index==2||index==4?960:480)&&!menu.remaining&&menu.index==(index+1)%5&&menu.route==1,"Each complete idle duration advances and wraps the native selector");
    }
    require(selectedScores==8&&menu.index==0,"Eight high-score rows precede the complete wrap to page zero");
    auto bad=menu;bad.route=2;bool rejected=false;try{airTitleCycle(bad,sound,*ui,texts,noop,noop,noop,noop,noop,noop);}catch(const std::exception&){rejected=true;}require(rejected,"Non-advance route cannot enter the page owner");
    printf("PASS: %d native title-carousel assertions.\n",checks);return 0;
}catch(const std::exception& e){fprintf(stderr,"FAIL after %d checks: %s\n",checks,e.what());return 1;}}
