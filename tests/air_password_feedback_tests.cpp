#include "air_password_feedback.h"
#include <cstdio>
#include <memory>
using namespace ticd;
int main(){int checks=0;auto require=[&](bool ok,const char* why){++checks;if(!ok)throw std::runtime_error(why);};try{
    auto audio=AudioAssets::load(L"build/audio.dat");auto ui=std::make_unique<UiAssets>(UiAssets::load(L"build/ui.dat"));
    for(int wanted:{-1,0,4,5,8,9}){AirPasswordEdit seed;seed.submit=8;auto& p=seed.password;p.closed=p.opened=40;p.cleared=2;p.cursor=7;if(wanted>=0)p.digits=ui->passwords[wanted];
        auto& l=p.menu.page.close.fade.layout;auto& r=l.reset;auto& t=r.timing;l.windowX=166;l.windowY=112;l.lyc=23;r.servicesMasked=false;r.stat=1;r.lcdc=0xc3;r.window=ui->hiddenMaps[0];r.background.fill(19);r.objects[0]=96;r.objects[1]=112;r.objects[2]=0x45;r.objects[3]=128;
        t.end=100*AirClock::Frame+144*456+4000;t.nextStat=101*AirClock::Frame+23*456;t.nextVBlank=101*AirClock::Frame+144*456;t.tick=65520;t.countdown=54;t.displays=765;t.stats=1138;t.input.held=t.input.pressed=8;
        NativeAudio sound(audio);sound.measureWork=true;sound.playMusic(7);int services=0,hold=0,closed=0,opened=0,stopStats=0;bool resetting=false;int64_t resetBegin=0,resetEnd=0;std::vector<std::pair<int,int>> glyphs;
        auto result=airPasswordFeedback(seed,sound,*ui,1,0,
            [&](const char* name,int64_t cycle,const AirPasswordFeedback& s,bool enabled){std::string n=name;if(n=="waitReturned"){resetting=true;resetBegin=cycle;}if(n=="audioStopped"){resetting=false;resetEnd=cycle;require(!enabled,"Native driver is disabled after the reset completion");}if(n=="holdWait"){require(s.remaining==60-hold,"Feedback retains its independent sixty-step counter");++hold;}if(n=="centerStored")++closed;if(n=="openStored")++opened;},
            [&](unsigned index,int64_t,int tick,int countdown,int display,int effects,int music,const DisplayInput&){require(!resetting&&index==unsigned(765+services)&&tick==((65520+services)&65535)&&countdown==54&&display==116&&effects==64&&music>=60,"Only completed audio state is observed by real feedback display services");++services;},
            [&](const char* kind,int64_t,AirIrqOwner owner){require(owner!=AirIrqOwner::Unqualified,"Feedback vectors retain source completion ownership");if(resetting&&std::string(kind)=="stat")++stopStats;},[](auto...){},
            [&](int64_t,int mode){require(mode>=0&&mode<=3,"Feedback glyph readiness remains native despite silent audio");},
            [&](int64_t,int address,int value){if(address>=0x9c00&&address<0xa000)glyphs.emplace_back(address,value);},[]{return 0;});
        require(result.action==wanted&&result.candidate==(wanted<0?10:wanted),"All ten rows are searched in order and resolve only their own full digit match");
        require(hold==60&&closed==40&&opened==40&&result.cleared==2&&!result.remaining&&!result.center,"Feedback owns all close/clear/open/hold operations");
        require(resetEnd-resetBegin>=audioStopWork()&&(resetEnd-resetBegin==audioStopWork()||stopStats>0),"Additional stop time comes from actual raster interrupts");
        require(!sound.enabled&&sound.song==-1&&std::none_of(sound.voices.begin(),sound.voices.end(),[](const auto& v){return v.active;}),"Logical native audio stops rather than retaining parked raw presets");
        require(result.startDay==(wanted>=0&&wanted<5?wanted:1)&&result.startDifficulty==(wanted>=5&&wanted<9?wanted-5:0)&&result.musicTest==(wanted==9),"Selection and music-test handlers preserve unrelated native start choices");
        auto expected=r.window;for(int i=448;i<768;++i)expected[i]=0;for(int i=0;i<18;++i)expected[19*32+1+i]=ui->hiddenMaps[wanted<0?1:2][19*32+1+i];
        const auto& after=result.edit.password.menu.page.close.fade.layout.reset;
        require(glyphs.size()==658&&after.window==expected&&after.background==r.background&&std::all_of(after.objects.begin(),after.objects.end(),[](int value){return value==0;}),"Feedback publishes its own complete map and removes only the native cursor object");
    }
    printf("PASS: %d native password-feedback assertions.\n",checks);return 0;
}catch(const std::exception& e){fprintf(stderr,"FAIL after %d checks: %s\n",checks,e.what());return 1;}}
