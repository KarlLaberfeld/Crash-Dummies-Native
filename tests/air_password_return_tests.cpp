#include "air_password_return.h"
#include <cstdio>
#include <memory>
using namespace ticd;
int main(){int checks=0;auto require=[&](bool ok,const char* why){++checks;if(!ok)throw std::runtime_error(why);};try{
    auto audio=AudioAssets::load(L"build/audio.dat");auto ui=std::make_unique<UiAssets>(UiAssets::load(L"build/ui.dat"));
    for(int target:{1,2,3}){AirPasswordFeedback seed;seed.remaining=0;seed.closed=seed.opened=40;seed.cleared=2;seed.action=target==3?9:-1;seed.musicTest=target==3;seed.startDay=3;seed.startDifficulty=2;seed.edit.submit=target==2?1:8;
        auto& p=seed.edit.password;p.cursor=7;p.digits.fill(3);auto& l=p.menu.page.close.fade.layout;auto& r=l.reset;auto& t=r.timing;
        l.windowX=166;l.windowY=112;l.lyc=23;r.servicesMasked=false;r.stat=1;r.lcdc=0xc3;r.window=ui->hiddenMaps[1];r.background.fill(19);
        t.end=200*AirClock::Frame+144*456+2500;t.nextStat=201*AirClock::Frame+23*456;t.nextVBlank=201*AirClock::Frame+144*456;t.tick=65520;t.countdown=54;t.displays=1400;t.stats=2600;
        NativeAudio sound(audio);sound.measureWork=true;sound.stop();int services=0,closed=0,opened=0,rows=0;std::vector<int> glyphs;
        auto result=airPasswordReturn(seed,sound,*ui,
            [&](const char* name,int64_t,const AirPasswordReturn& s,bool,int){require(s.target==target,"Native submit/action state chooses the actual destination");if(std::string(name)=="centerStored")++closed;if(std::string(name)=="openStored")++opened;if(std::string(name)=="rowReady")++rows;},
            [&](unsigned index,int64_t,int tick,int countdown,int display,int effects,int music,const DisplayInput&){require(index==unsigned(1400+services)&&tick==((65520+services)&65535)&&countdown==54&&display==116&&effects==64&&music>=60,"Return presentation retains actual independent input/music/tick services");++services;},
            [&](const char*,int64_t,AirIrqOwner owner){require(owner!=AirIrqOwner::Unqualified,"Every return vector has an owned instruction completion");},[](auto...){},
            [&](int64_t,int mode){require(mode>=0&&mode<=3,"Closed-window stores retain native LCD readiness");},
            [&](int64_t,int address,int value){if(address>=0x9c00&&address<0xa000)glyphs.push_back(value);},[]{return 0;});
        const auto& after=result.feedback.edit.password;const auto& layout=after.menu.page.close.fade.layout;const auto& a=layout.reset;
        require(closed==40&&opened==40&&result.closed==40&&result.cleared==2&&result.opened==40&&!result.center&&layout.windowY==112&&layout.lyc==23,"Every destination completes its whole close/clear/open presentation");
        require(a.background==r.background&&a.objects==r.objects&&result.feedback.startDay==3&&result.feedback.startDifficulty==2,"Returned screens retain background, empty objects and native start selections");
        if(target==1)require(sound.enabled&&sound.song==1&&rows==10&&result.rows==10&&glyphs.size()==840&&after.menu.remaining==480&&after.menu.index==0&&after.menu.route==0,"Title return resets its page-zero loop and independently copies all ten rows");
        if(target==2)require(sound.enabled&&sound.song==7&&glyphs.size()==672&&after.cursor==0&&after.digits==std::array<uint8_t,8>{},"Password return starts its own song and resets all eight editable digits");
        if(target==3)require(!sound.enabled&&sound.song==-1&&glyphs.size()==682&&result.tune==0&&result.effect==0&&result.lastTune==255&&after.cursor==0&&after.digits==p.digits,"Music-test entry publishes all three rows and initializes selectors without starting a tune or clearing unrelated digit storage");
        require(a.timing.end>t.end&&a.timing.tick==((65520+services)&65535)&&a.timing.displays==1400+services&&a.timing.nextStat>a.timing.end&&a.timing.nextVBlank>a.timing.end,"Final clock remains attached to actual presentation services and LCD epoch");
    }
    printf("PASS: %d native password-return assertions.\n",checks);return 0;
}catch(const std::exception& e){fprintf(stderr,"FAIL after %d checks: %s\n",checks,e.what());return 1;}}
