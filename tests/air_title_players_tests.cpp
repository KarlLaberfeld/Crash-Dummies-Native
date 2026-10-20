#include "air_title_players.h"
#include <cstdio>
#include <memory>
using namespace ticd;
int main(){int checks=0;auto require=[&](bool ok,const char* why){++checks;if(!ok)throw std::runtime_error(why);};try{
    auto audio=AudioAssets::load(L"build/audio.dat");auto ui=std::make_unique<UiAssets>(UiAssets::load(L"build/ui.dat"));
    std::vector<std::vector<int>> cases={{8},{4,0,8},{1},{2},std::vector<int>(24,4),{204},{9},std::vector<int>(64,0)};cases[4].insert(cases[4].end(),{0,8});cases[7].push_back(8);
    for(size_t scenario=0;scenario<cases.size();++scenario){AirTitleMenu seed;seed.route=3;seed.waits=3;seed.remaining=478;seed.page.cleared=2;seed.page.rows=10;seed.page.opened=40;
        auto& l=seed.page.close.fade.layout;auto& r=l.reset;auto& t=r.timing;l.windowX=166;l.windowY=112;l.lyc=23;r.servicesMasked=false;r.stat=1;r.lcdc=195;r.background.fill(19);r.window=ui->titleMaps[0];
        t.displays=665;t.stats=860;t.countdown=54;t.tick=65500;t.input.held=t.input.pressed=4;t.end=200*AirClock::Frame+144*456+2400;t.nextStat=201*AirClock::Frame+23*456;t.nextVBlank=201*AirClock::Frame+144*456;
        NativeAudio sound(audio);sound.measureWork=true;sound.playMusic(1);int samples=0,services=0,glyphs=0,cursorWrites=0;
        auto result=airTitlePlayers(seed,sound,*ui,
            [&](const char*,int64_t,const AirTitlePlayers& s,int song,bool enabled){require(s.players>=0&&s.players<=1&&s.closed<=40&&s.opened<=40&&song==1&&enabled,"Native player page retains its selection range and live title music");},
            [&](unsigned i,int64_t,int tick,int countdown,int display,int effects,int music,const DisplayInput&){require(i==unsigned(665+services)&&tick==((65500+services)&65535)&&countdown==54&&display==116&&effects>=64&&music>=60,"Player page owns independent services and rollover");++services;},
            [](auto...){},[](auto...){},[](auto...){},[&](int64_t,int address,int){if(address>=0x9c00&&address<0xa000)++glyphs;if(address>=0xc100&&address<=0xc103)++cursorWrites;},
            [&]{int index=samples++-81;if(index<0)return 0;if(index>=int(cases[scenario].size()))throw std::runtime_error("Missing player page exit");return cases[scenario][index];});
        const auto& after=result.menu.page.close.fade.layout.reset;
        require(result.closed==40&&result.cleared==2&&result.opened==40&&glyphs==684,"Select page completes both clears, all forty-four glyphs and both forty-wait motions");
        require(result.waits==int(cases[scenario].size())&&services==81+result.waits&&samples==services&&cursorWrites==4*result.waits,"Every loop updates all four cursor bytes once before fresh input");
        require(result.players==int(scenario==1||scenario==4||scenario==5)&&result.route==((scenario==2||scenario==3)?1:2),"Toggle precedes Start, held selection creates one edge and Start outranks A/B");
        require(after.objects[1]==24&&after.objects[3]==128&&after.background==r.background&&sound.song==1,"Blink cursor retains original X/priority and surrounding storage");
        require(after.timing.nextStat>after.timing.end&&after.timing.nextVBlank>after.timing.end,"Player page preserves a continuing independent clock at the outgoing clear entry");
    }
    printf("PASS: %d native player-selection assertions.\n",checks);return 0;
}catch(const std::exception& e){fprintf(stderr,"FAIL after %d checks: %s\n",checks,e.what());return 1;}}
