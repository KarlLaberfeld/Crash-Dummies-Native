// First-frame scope, pending priority, independent readiness and native state.
#include "air_title_resume.h"
#include <cstdio>
using namespace ticd;
int main(){int checks=0;auto require=[&](bool ok,const char* why){++checks;if(!ok)throw std::runtime_error(why);};
try{
    AudioAssets assets;NativeAudio sound(assets);sound.measureWork=true;sound.ticks=123;
    AirTitleCampaign fresh;auto& l=fresh.instruction.start.menu.page.close.fade.layout;auto& r=l.reset;auto& t=r.timing;
    fresh.campaign.start(false,1,0);r.servicesMasked=true;r.pendingRequests=3;r.display=r.stat=5;r.lcdc=0xd1;l.lyc=95;
    r.background.fill(19);t.lcdEpoch=1000000;t.end=t.lcdEpoch+20;t.nextStat=t.lcdEpoch+95*456;t.nextVBlank=t.lcdEpoch+144*456;
    t.tick=65535;t.displays=698;t.stats=927;t.countdown=54;t.input={8,0,8};t.lives=5;
    int samples=0,services=0,vectors=0,polls=0,cells=0,writes=0,points=0,firstFramePolls=0;int64_t lastReady=0;
    auto resumed=airTitleResume(fresh,33,sound,
        [&](const char* name,int64_t,const AirTitleResume& s){++points;const auto& r=s.fresh.instruction.start.menu.page.close.fade.layout.reset;
            if(std::string(name)=="begin")require(r.servicesMasked&&r.pendingRequests==3&&s.result==33,"Prior requests and result survive until resume");
            else require(!r.servicesMasked&&!r.pendingRequests,"Services consume both pending requests");
            if(std::string(name)=="backgroundCleared")require(s.result==33,"Old result survives through the full clear");
            if(std::string(name)=="end")require(s.result==0,"New instruction clears result only at its own store");},
        [&](unsigned index,int64_t,int tick,int countdown,int display,int effects,int music,const DisplayInput& input){
            require(index==unsigned(698+services)&&tick==((65535+services)&65535)&&countdown==54,"Only actual services advance native tick, never countdown");
            require(display==144&&effects==64&&music==60&&!input.held&&!input.pressed,"Disabled audio and new input sample have independent owners");++services;},
        [&](const char* kind,int64_t cycle,AirIrqOwner owner){
            if(vectors<2){require(owner==AirIrqOwner::PendingStartup,"Inherited requests have explicit startup ownership");require(std::string(kind)==(vectors?"stat":"vblank"),"VBlank wins over inherited STAT");
                if(!vectors)require(cycle==t.end+48,"Pending acceptance follows the whole EI/CALL boundary");}
            else require(owner==AirIrqOwner::SourceBoundary,"Clear services occur at identified access boundaries");++vectors;},
        [&](int64_t cycle,int mode){++polls;require(mode>=0&&mode<=3,"Every readiness read has an owned mode");if(!(mode&2))lastReady=cycle;
            if(cycle-t.lcdEpoch<AirClock::Frame)++firstFramePolls;},
        [&](int64_t cycle,int address,int value){++writes;if(address>=0x9800&&address<0x9c00){require(address==0x9800+cells&&value==0&&cycle>=lastReady+28,"Every background cell has its own ready read and store");++cells;}
            else require((address==0xff42&&value==0)||(address==0xc035&&value==0x98)||(address==0xc095&&value==0),"Clear cannot write unrelated game/asset storage");},
        [&]{++samples;return 0;});
    const auto& out=resumed.fresh.instruction.start.menu.page.close.fade.layout.reset;const auto& end=out.timing;
    require(points==7&&samples==4&&services==4&&vectors==8&&cells==1024&&polls==3567&&writes==1034&&firstFramePolls>1000,"Complete resumed clear keeps all accesses and services");
    require(end.tick==3&&end.countdown==54&&end.displays==702&&end.stats==931&&sound.ticks==127,"Tick rollover, audio and both service counters advance independently");
    require(out.window==r.window&&out.objects==r.objects&&std::all_of(out.background.begin(),out.background.end(),[](int v){return !v;}),"Both full maps end blank without changing the object list");
    require(resumed.fresh.campaign.players[0].lives==5&&resumed.fresh.campaign.current==0&&resumed.fresh.campaign.active&&end.lives==5,"First display does not consume fresh campaign lives");
    require(end.lcdEpoch==t.lcdEpoch&&end.nextStat>end.end&&end.nextVBlank>end.end,"Original LCD epoch persists and next deadlines remain future");
    require(end.end-t.end==237944,"Completed operation retains identified busy and service work");
    for(int mode=0;mode<14;++mode){auto bad=fresh;auto& l=bad.instruction.start.menu.page.close.fade.layout;auto& r=l.reset;int result=33;
        if(mode==0)r.servicesMasked=false;if(mode==1)r.pendingRequests=2;if(mode==2)r.objects[255]=1;if(mode==3)r.window[1023]=1;
        if(mode==4)l.lyc=96;if(mode==5)r.timing.end+=4;if(mode==6)l.reset.stat=4;if(mode==7)bad.campaign.players[0].lives=0;
        if(mode==8)bad.campaign.current=1;if(mode==9)bad.instruction.start.menu.page.close.center=1;if(mode==10)result=1;if(mode==11)r.scrollX=1;
        if(mode==12)l.bootShown=false;if(mode==13)r.timing.lives=4;
        bool rejected=false;try{airTitleResume(bad,result,sound,[](auto...){},[](auto...){},[](auto...){},[](auto...){},[](auto...){ });}catch(const std::exception&){rejected=true;}
        require(rejected,"Unowned geometry, pending state or player routing rejects");}
    AirPauseLcd lcd;lcd.objectsEnabled=lcd.windowEnabled=false;lcd.instructionRestartFrame=true;
    for(int64_t cycle=0;cycle<456;++cycle)require(lcd.mode(cycle)==-1,"First LCD-on line is still unowned");
    for(int64_t cycle=456;cycle<AirClock::Frame;cycle+=4)require(lcd.mode(cycle)==lcd.mode(cycle+AirClock::Frame),"Bounded empty first-frame geometry agrees with steady later lines");
    lcd.instructionRestartFrame=false;lcd.resultFirstVisibleFrame=true;require(lcd.mode(143*456)==-1,"Existing result-only owner still excludes line 143");
    lcd.instructionRestartFrame=true;lcd.objectsEnabled=true;require(lcd.mode(65000)==-1,"New owner does not qualify nonempty object geometry");
    printf("PASS: %d native title-resume assertions.\n",checks);return 0;
}catch(const std::exception& e){fprintf(stderr,"FAIL after %d checks: %s\n",checks,e.what());return 1;}}
