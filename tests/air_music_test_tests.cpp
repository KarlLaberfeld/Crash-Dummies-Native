#include "air_music_test.h"
#include <cstdio>
#include <memory>
using namespace ticd;
int main(){int checks=0;auto require=[&](bool ok,const char* why){++checks;if(!ok)throw std::runtime_error(why);};try{
    auto audio=AudioAssets::load(L"build/audio.dat");auto ui=std::make_unique<UiAssets>(UiAssets::load(L"build/ui.dat"));AirPasswordReturn seed;seed.target=3;seed.closed=seed.opened=40;seed.cleared=2;
    seed.feedback.remaining=0;seed.feedback.closed=seed.feedback.opened=40;seed.feedback.cleared=2;seed.feedback.action=9;seed.feedback.musicTest=true;seed.feedback.edit.submit=8;
    auto& l=seed.feedback.edit.password.menu.page.close.fade.layout;auto& r=l.reset;auto& t=r.timing;l.windowX=166;l.windowY=112;l.lyc=23;r.servicesMasked=false;r.stat=1;r.lcdc=0xc3;r.window=ui->hiddenMaps[3];r.background.fill(19);
    t.end=200*AirClock::Frame+144*456+2300;t.nextStat=201*AirClock::Frame+23*456;t.nextVBlank=201*AirClock::Frame+144*456;t.tick=65520;t.countdown=54;t.displays=1500;t.stats=2800;
    std::vector<std::vector<int>> cases(5);cases[0]={48,0,192,0};cases[0].insert(cases[0].end(),24,16);cases[0].push_back(0);cases[0].insert(cases[0].end(),24,64);cases[0].insert(cases[0].end(),{0,8});
    cases[1]={1,0,2,0,1,0,3,0,2,0,8};
    for(int tune=0;tune<14;++tune){cases[2].insert(cases[2].end(),{1,0,0,0});if(tune<13)cases[2].insert(cases[2].end(),{16,0});}cases[2].push_back(8);
    cases[3]={16,0,1,0,0,0};for(int fx=0;fx<26;++fx){cases[3].insert(cases[3].end(),{1,0});if(fx<25)cases[3].insert(cases[3].end(),{64,0});}cases[3].push_back(8);
    cases[4]={32,0,1,0};cases[4].insert(cases[4].end(),1200,0);cases[4].insert(cases[4].end(),{1,0,2,0,8});
    for(size_t scenario=0;scenario<cases.size();++scenario){NativeAudio sound(audio);sound.measureWork=true;sound.stop();int samples=0,services=0,glyphs=0;
        auto result=airMusicTest(seed,sound,
            [&](const char*,int64_t,const AirMusicTest& s,const NativeAudio&){require(s.screen.tune>=0&&s.screen.tune<14&&s.screen.effect>=0&&s.screen.effect<26,"Selectors stay in their native fourteen/twenty-six item domains at every semantic boundary");},
            [&](unsigned index,int64_t,int tick,int countdown,int display,int effects,int music,const DisplayInput&){require(index==unsigned(1500+services)&&tick==((65520+services)&65535)&&countdown==54&&display==116&&effects>=64&&music>=60,"Actual services own all native music/effect work, input and tick rollover");++services;},
            [&](const char*,int64_t,AirIrqOwner owner){require(owner!=AirIrqOwner::Unqualified,"Music-test interruptions retain explicit completion ownership");},[](auto...){},
            [&](int64_t,int mode){require(mode>=0&&mode<=3,"Live music does not bypass numeric glyph readiness");},
            [&](int64_t,int address,int value){if(address>=0x9c00&&address<0xa000){require(value>=1&&value<=16,"Hexadecimal number glyphs keep both zero nibbles");++glyphs;}},
            [&]{if(samples>=int(cases[scenario].size()))throw std::runtime_error("Native music test did not return at Start");return cases[scenario][samples++];});
        require(result.exited&&result.waits==samples&&services==samples&&samples==int(cases[scenario].size())&&glyphs==4*services,"Every iteration renders both complete numbers before processing input and returning");
        if(scenario==0)require(result.screen.tune==1&&result.screen.effect==1&&result.plays==0&&result.effects==0,"Combined wrap and long holds have the original directional order/fresh-edge behavior");
        if(scenario==1)require(result.plays==3&&result.stops==3&&result.effects==0&&!sound.enabled&&result.screen.lastTune==255,"B precedes A, resets last-tune state and permits immediate restart");
        if(scenario==2)require(result.plays==14&&result.effects==0&&sound.song==13&&result.screen.lastTune==13,"Every different selected tune starts its own native roots");
        if(scenario==3)require(result.plays==1&&result.effects==26&&result.screen.effect==25&&sound.song==1,"All twenty-six effects can be queued on the same live tune");
        if(scenario==4)require(result.plays==2&&result.stops==1&&!sound.enabled,"A completed same tune restarts instead of queueing an effect");
        const auto& after=result.screen.feedback.edit.password.menu.page.close.fade.layout.reset;
        require(after.background==r.background&&after.objects==r.objects&&after.timing.tick==((65520+services)&65535)&&after.timing.nextStat>after.timing.end&&after.timing.nextVBlank>after.timing.end,"Test retains background/objects and its independently advanced LCD clock");
        auto feedback=result.screen.feedback;feedback.edit.password.cursor=result.screen.tune;int returnedServices=0;
        auto returned=airPasswordReturn(feedback,sound,*ui,[](auto...){},
            [&](unsigned,int64_t,int,int,int display,int effects,int music,const DisplayInput&){require(display==116&&effects>=64&&music>=60,"Post-test return services retain the actual current music until title reset");++returnedServices;},
            [](auto...){},[](auto...){},[](auto...){},[](auto...){},[]{return 0;},true);
        require(returned.target==1&&returned.closed==40&&returned.cleared==2&&returned.opened==40&&returned.rows==10&&returnedServices==83&&sound.enabled&&sound.song==1,"Every stopped/live/completed test case returns through the entire title page and song restart");
        require(returned.feedback.edit.password.menu.remaining==480&&returned.feedback.edit.password.menu.index==0&&returned.feedback.edit.password.menu.route==0,"Music-test return restores the actual page-zero menu loop");
    }
    printf("PASS: %d native music-test assertions.\n",checks);return 0;
}catch(const std::exception& e){fprintf(stderr,"FAIL after %d checks: %s\n",checks,e.what());return 1;}}
