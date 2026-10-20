// Real native direction sequencing without recorded state or clock inputs.
#include "air_title_menu.h"
#include <cstdio>
using namespace ticd;
int main(){int checks=0;auto require=[&](bool ok,const char* why){++checks;if(!ok)throw std::runtime_error(why);};
try{
    AudioAssets assets;AirTitlePage page;page.cleared=2;page.rows=10;page.opened=40;
    auto& l=page.close.fade.layout;auto& r=l.reset;auto& t=r.timing;
    l.windowX=166;l.windowY=112;l.lyc=23;r.stat=1;r.lcdc=0xc3;r.servicesMasked=false;
    t.end=1000000+100*AirClock::Frame+144*456+4000;t.lcdEpoch=1000000;t.nextStat=t.lcdEpoch+101*AirClock::Frame+23*456;t.nextVBlank=t.lcdEpoch+101*AirClock::Frame+144*456;
    t.tick=65534;t.countdown=54;t.displays=662;t.stats=854;r.background.fill(19);r.window.fill(23);
    std::vector<std::vector<int>> cases={{0,0,64,64,0,128,128,0,32,32,0,16},{0,0,64,64,64,64,64,64,64,64,64,64,64,64,0,128,0,32,0,16},{0,0,64,0,16,0,64,0,128,0,32,0,16},{0,0,96,0,64,0,128,0,32,0,16}};
    std::vector<std::vector<int>> expected={{0x16,0x17,0x18,0x15},{0x16,0x17,0x18,0x15},{0x16,0x15,0x16,0x17,0x18,0x15},{0x15,0x16,0x17,0x18,0x15}};
    for(size_t scenario=0;scenario<cases.size();++scenario){NativeAudio sound(assets);sound.enabled=true;sound.song=1;sound.measureWork=true;int samples=0,displays=0,high=0,pages=0;std::vector<int> low;
        auto result=airTitleMenuIdle(page,sound,
            [&](const char*,int64_t,const AirTitleMenu& s){require(s.unlockProgress>=0&&s.unlockProgress<4&&s.page.close.fade.layout.reset.timing.countdown==54,"Sequence is native bounded state and does not spend the game timer");},
            [&](unsigned index,int64_t,int tick,int countdown,int display,int,int,const DisplayInput&){require(index==unsigned(662+displays)&&tick==((65534+displays)&65535)&&countdown==54&&display==116,"Input/audio sampling belongs to actual displays");++displays;},
            [&](const char*,int64_t,AirIrqOwner owner){require(owner!=AirIrqOwner::Unqualified,"Every sequence vector has an explicit native boundary owner");},
            [](auto...){},[&](int64_t,int address,int value){if(address==0xc0b5)low.push_back(value);if(address==0xc0b6){require(value==0x2b,"Sequence high-byte projection stays in its fixed table");++high;}if(address==0xc03e)++pages;},
            [&]{if(samples>=int(cases[scenario].size()))throw std::runtime_error("Native sequence did not terminate on its own final edge");return cases[scenario][samples++];},true,true);
        require(low==expected[scenario]&&high==int(low.size()),"Fresh directions advance, held inputs do not repeat and mismatch/combined masks reset exactly once");
        require(samples==int(cases[scenario].size())&&result.route==4&&!result.unlockProgress&&!result.index&&!pages,"Completed sequence selects password transition before page/action work");
        require(result.waits==samples&&result.remaining==481-samples&&result.page.close.fade.layout.reset.timing.tick==((65534+samples)&65535),"Only nonterminal iterations decrement page duration");
        require(result.page.close.fade.layout.reset.background==r.background&&result.page.close.fade.layout.reset.window==r.window&&result.page.close.fade.layout.reset.objects==r.objects,"Unlock decisions do not compose a password screen or alter unrelated storage");
    }
    NativeAudio sound(assets);sound.enabled=true;sound.song=1;sound.measureWork=true;bool rejected=false;
    try{airTitleMenuIdle(page,sound,[](auto...){},[](auto...){},[](auto...){},[](auto...){},[](auto...){},[]{return 0;},false,true);}catch(const std::exception&){rejected=true;}
    require(rejected,"Direction ownership cannot silently skip its action prerequisites");
    printf("PASS: %d native title-unlock assertions.\n",checks);return 0;
}catch(const std::exception& e){fprintf(stderr,"FAIL after %d checks: %s\n",checks,e.what());return 1;}}
