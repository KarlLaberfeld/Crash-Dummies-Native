#include "air_title_password.h"
#include <cstdio>
#include <memory>
using namespace ticd;
int main(){int checks=0;auto require=[&](bool ok,const char* why){++checks;if(!ok)throw std::runtime_error(why);};try{
    auto audio=AudioAssets::load(L"build/audio.dat");auto ui=std::make_unique<UiAssets>();
    for(const auto& row:std::array<std::array<int,3>,3>{{{5,16,10},{3,19,14},{6,21,8}}})for(int i=0;i<row[2];++i)ui->hiddenMaps[0][32*row[1]+row[0]+i]=i+1;
    AirTitleMenu seed;seed.route=4;seed.waits=21;seed.remaining=460;auto& l=seed.page.close.fade.layout;auto& r=l.reset;auto& t=r.timing;
    l.windowX=166;l.windowY=112;l.lyc=23;r.servicesMasked=false;r.stat=1;r.display=0;r.lcdc=0xc3;r.background.fill(19);r.window.fill(23);
    t.end=100*AirClock::Frame+144*456+4000;t.nextStat=101*AirClock::Frame+23*456;t.nextVBlank=101*AirClock::Frame+144*456;t.tick=65520;t.countdown=54;t.displays=683;t.stats=896;t.input.held=t.input.pressed=16;
    NativeAudio sound(audio);sound.measureWork=true;sound.playMusic(1);int services=0,polls=0;std::vector<std::pair<int,int>> glyphs;
    auto result=airTitlePassword(seed,sound,*ui,
        [&](const char*,int64_t,const AirTitlePassword& s,int song,bool enabled){require(enabled&&(song==1||song==7)&&s.menu.page.close.fade.layout.reset.timing.countdown==54,"Actual password callbacks retain countdown and enabled music");},
        [&](unsigned index,int64_t,int tick,int countdown,int display,int effects,int music,const DisplayInput&){require(index==unsigned(683+services)&&tick==((65520+services)&65535)&&countdown==54&&display==116&&effects==64&&music>=60,"Independent displays own input, tick and active music");++services;},
        [&](const char*,int64_t,AirIrqOwner owner){require(owner!=AirIrqOwner::Unqualified,"Every presentation vector has a completion owner");},[](auto...){},
        [&](int64_t,int mode){require(mode>=0&&mode<=3,"Password accesses preserve identified LCD readiness");++polls;},
        [&](int64_t,int address,int value){if(address>=0x9c00&&address<0xa000)glyphs.emplace_back(address,value);},[]{return 0;});
    require(result.closed==40&&result.cleared==2&&result.opened==40&&!result.center&&!result.cursor&&result.digits==std::array<uint8_t,8>{},"Complete native close/clear/open resets cursor and digits");
    require(glyphs.size()==672&&polls>=672&&services>=81&&services<=83,"Both clears and all three text rows keep their actual access work");
    auto expected=r.window;for(int i=448;i<768;++i)expected[i]=0;
    for(const auto& row:std::array<std::array<int,3>,3>{{{5,16,10},{3,19,14},{6,21,8}}})for(int i=0;i<row[2];++i)expected[32*row[1]+row[0]+i]=ui->hiddenMaps[0][32*row[1]+row[0]+i];
    const auto& after=result.menu.page.close.fade.layout;const auto& a=after.reset.timing;
    require(after.reset.window==expected&&after.reset.background==r.background&&after.reset.objects==r.objects,"All final map bytes derive from native clear/glyph writes; background and objects stay unchanged");
    require(after.windowY==112&&after.windowX==166&&after.lyc==23&&after.reset.stat==1&&after.reset.lcdc==0xc3&&!after.reset.scrollY&&a.tick==((65520+services)&65535)&&a.displays==683+services,"Restored title geometry retains independently advanced tick and service count");
    require(sound.enabled&&sound.song==7&&!sound.paused,"Password music replaces title song at its native reset completion");
    for(int page=1;page<=4;++page){
        auto later=seed;later.carouselOwned=true;later.index=page;later.remaining=(page==2||page==4?960:480)-later.waits+1;
        auto& before=later.page.close.fade.layout.reset.timing;before.displays+=1000*page;before.stats+=2000*page;
        const unsigned origin=before.displays;NativeAudio live(audio);live.measureWork=true;live.playMusic(1);int sampled=0;
        auto completed=airTitlePassword(later,live,*ui,[](auto...){},[&](unsigned index,int64_t,int,int,int,int,int,const DisplayInput&){require(index==origin+sampled++,"Later password retains actual carousel service indices");},[](auto...){},[](auto...){},[](auto...){},[](auto...){},[]{return 0;});
        const auto& out=completed.menu.page.close.fade.layout;
        require(completed.menu.index==page&&completed.menu.carouselOwned&&completed.digits==std::array<uint8_t,8>{}&&!completed.cursor,"Later password resets digits without fabricating first-page ownership");
        require(out.reset.window==expected&&out.reset.background==r.background&&out.reset.objects==r.objects&&out.windowY==112,"Every later-page password completes the same independently expected window storage");
        require(live.enabled&&live.song==7&&out.reset.timing.displays==int(origin)+sampled&&out.reset.timing.nextVBlank>out.reset.timing.end,"Later password owns music replacement and actual future deadlines");
        later.carouselOwned=false;NativeAudio invalid(audio);invalid.measureWork=true;invalid.playMusic(1);bool rejected=false;
        try{airTitlePassword(later,invalid,*ui,[](auto...){},[](auto...){},[](auto...){},[](auto...){},[](auto...){},[](auto...){},[]{return 0;});}catch(const std::runtime_error&){rejected=true;}
        require(rejected,"Arbitrary non-first-page counters cannot borrow retained-carousel ownership");
    }
    auto reject=[&](auto alter){auto bad=seed;alter(bad);NativeAudio test(audio);test.measureWork=true;test.playMusic(1);bool rejected=false;try{airTitlePassword(bad,test,*ui,[](auto...){},[](auto...){},[](auto...){},[](auto...){},[](auto...){},[](auto...){},[]{return 0;});}catch(const std::runtime_error&){rejected=true;}require(rejected,"Unowned entry must be rejected before borrowing password timing");};
    reject([](auto& s){s.route=2;});reject([](auto& s){s.unlockProgress=1;});reject([](auto& s){s.waits=3;});reject([](auto& s){s.remaining=459;});reject([](auto& s){s.page.close.fade.layout.reset.objects[0]=1;});reject([](auto& s){s.page.close.fade.layout.windowX=7;});reject([](auto& s){s.page.close.fade.layout.reset.timing.displays--;});reject([](auto& s){s.page.close.fade.layout.reset.timing.countdown=53;});reject([](auto& s){s.page.close.fade.layout.reset.timing.input.pressed=0;});
    printf("PASS: %d native password-presentation assertions.\n",checks);return 0;
}catch(const std::exception& e){fprintf(stderr,"FAIL after %d checks: %s\n",checks,e.what());return 1;}}
