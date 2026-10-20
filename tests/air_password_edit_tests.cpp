#include "air_password_edit.h"
#include <cstdio>
using namespace ticd;
int main(){int checks=0;auto require=[&](bool ok,const char* why){++checks;if(!ok)throw std::runtime_error(why);};try{
    auto audio=AudioAssets::load(L"build/audio.dat");AirTitlePassword seed;seed.closed=seed.opened=40;seed.cleared=2;auto& l=seed.menu.page.close.fade.layout;auto& r=l.reset;auto& t=r.timing;
    l.windowX=166;l.windowY=112;l.lyc=23;r.servicesMasked=false;r.stat=1;r.lcdc=0xc3;r.window.fill(23);r.background.fill(19);
    t.end=100*AirClock::Frame+144*456+4000;t.nextStat=101*AirClock::Frame+23*456;t.nextVBlank=101*AirClock::Frame+144*456;t.tick=65520;t.countdown=54;t.displays=765;t.stats=1138;
    std::vector<std::vector<int>> cases={{0,8},{0,1},{0,2},{32,0},{128,0,64,0},{48,0,192,0,16,0,96,0,8},{24}};
    for(int i=0;i<9;++i)cases[3].insert(cases[3].end(),{16,0});for(int i=0;i<9;++i)cases[3].insert(cases[3].end(),{32,0});cases[3].push_back(8);
    for(int i=0;i<10;++i)cases[4].insert(cases[4].end(),{64,0});cases[4].insert(cases[4].end(),{128,0,128,0,8});
    std::vector<int> held(24,64);held.push_back(0);held.insert(held.end(),18,16);held.push_back(0);held.insert(held.end(),24,128);held.insert(held.end(),{0,8});cases.push_back(held);
    for(size_t scenario=0;scenario<cases.size();++scenario){NativeAudio sound(audio);sound.measureWork=true;sound.playMusic(7);int samples=0,services=0;std::vector<int> values;
        auto result=airPasswordEdit(seed,sound,
            [&](const char*,int64_t,const AirPasswordEdit& s){require(s.password.cursor>=0&&s.password.cursor<=7,"Native cursor stays within all eight password cells");},
            [&](unsigned index,int64_t,int tick,int countdown,int display,int effects,int music,const DisplayInput&){require(index==unsigned(765+services)&&tick==((65520+services)&65535)&&countdown==54&&display==116&&effects==64&&music>=60,"Editing waits own the original input/tick/audio service");++services;},
            [&](const char*,int64_t,AirIrqOwner owner){require(owner!=AirIrqOwner::Unqualified,"Editing vectors have explicit completion ownership");},[](auto...){},
            [&](int64_t,int mode){require(mode>=0&&mode<=3,"Edit glyphs retain independently owned LCD readiness with cursor objects present");},
            [&](int64_t,int address,int value){if(address>=0x9c00&&address<0xa000)values.push_back(value);},
            [&]{if(samples>=int(cases[scenario].size()))throw std::runtime_error("Native editing failed to stop at its final submit edge");return cases[scenario][samples++];});
        require(samples==int(cases[scenario].size())&&result.waits==samples&&services==samples,"Held keys do not fabricate additional fresh editing edges");
        require(result.submit==(cases[scenario].back()&11),"Start/A/B submission retains the actual mask after all direction decisions");
        if(scenario<3)require(values.empty()&&result.password.cursor==0,"Each submit button works without mutating password digits");
        if(scenario==3)require(result.password.cursor==0&&values.empty(),"Both cursor boundaries reject extra navigation presses");
        if(scenario==4)require(result.password.digits[0]==9&&values.front()==10&&values[1]==1&&values[11]==1,"Zero decrements to ten; ten increments to one; repeated fresh digits wrap");
        if(scenario==5)require(result.password.cursor==1&&result.password.digits[1]==1&&values==std::vector<int>({1,10,1}),"Combined directions execute Left/Right then Up/Down in original order");
        if(scenario==6)require(result.password.cursor==1&&result.password.menu.page.close.fade.layout.reset.objects[1]==56,"Cursor object publication precedes the simultaneous movement/submit decision");
        if(scenario==7)require(result.password.cursor==1&&result.password.digits[0]==1&&result.password.digits[1]==10&&values.size()==2,"Long holds create one edit/navigation edge each");
        const auto& after=result.password.menu.page.close.fade.layout.reset;
        require(after.background==r.background&&std::equal(after.objects.begin()+4,after.objects.end(),r.objects.begin()+4)&&sound.enabled&&sound.song==7,"Only password cells and cursor object change; background, other objects and song are retained");
    }
    auto reject=[&](auto alter){auto bad=seed;alter(bad);NativeAudio sound(audio);sound.measureWork=true;sound.playMusic(7);bool rejected=false;try{airPasswordEdit(bad,sound,[](auto...){},[](auto...){},[](auto...){},[](auto...){},[](auto...){},[](auto...){},[]{return 8;});}catch(const std::runtime_error&){rejected=true;}require(rejected,"Unowned initial editing state rejects before timing is borrowed");};
    reject([](auto& s){s.cursor=1;});reject([](auto& s){s.digits[0]=1;});reject([](auto& s){s.closed=39;});reject([](auto& s){s.menu.page.close.fade.layout.reset.objects[0]=1;});reject([](auto& s){s.menu.page.close.fade.layout.reset.display=1;});
    printf("PASS: %d native password-edit assertions.\n",checks);return 0;
}catch(const std::exception& e){fprintf(stderr,"FAIL after %d checks: %s\n",checks,e.what());return 1;}}
