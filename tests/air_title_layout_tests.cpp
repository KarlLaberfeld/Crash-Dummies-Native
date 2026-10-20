// Static native title composition, input/audio preservation and entry guards.
#include "air_title_layout.h"
#include <cstdio>
using namespace ticd;
int main(){
    int checks=0;auto require=[&](bool ok,const char* why){++checks;if(!ok)throw std::runtime_error(why);};
    try{
        AudioAssets audio;NativeAudio sound(audio);sound.enabled=true;sound.song=13;
        AirTitleReset reset;reset.lcdc=0x5b;reset.pendingRequests=3;reset.timing.end=1000000;
        reset.timing.tick=65535;reset.timing.displays=reset.timing.stats=546;reset.timing.countdown=54;reset.timing.input={255,33,1};
        AirTitleLayoutAssets assets;
        for(int k:{0,1,2,1,2,0,1,2,1,2,3})assets.commands.push_back({k,0,0,0,0,{}});
        assets.commands[5].a=1;
        for(int i:{1,3,6,8}){assets.commands[i].a=3;assets.commands[i].b=i;}
        for(int i:{2,4,7,9}){auto& c=assets.commands[i];c.width=i;c.height=3;c.cells.assign(c.width*c.height,240+i);}
        UiMap background{},window{};
        int layer=0,x=0,y=0,expectedStores=7,commands=0,rows=0,stores=0;
        for(const auto& c:assets.commands){if(c.kind==0)layer=c.a;if(c.kind==1){x=c.a;y=c.b;}if(c.kind==2){
            expectedStores+=c.width*c.height;auto& map=layer?window:background;
            for(int r=0;r<c.height;++r)for(int col=0;col<c.width;++col)map[(y+r)*32+x+col]=c.cells[r*c.width+col];}}
        auto state=airTitleLayout(reset,true,sound,assets,
            [&](const char* name,int64_t,int,int,const AirTitleLayout& s){if(std::string(name)=="command")++commands;if(std::string(name)=="rowReady")++rows;
                require(s.reset.timing.tick==65535&&s.reset.timing.countdown==54,"No display bookkeeping during masked composition");},
            [&](int64_t,int,int){++stores;});
        require(commands==11&&rows==12&&stores==expectedStores,"Complete four-rectangle composition and register setup");
        for(int i=0;i<1024;++i){require(state.reset.background[i]==background[i],"Native background preserves untouched blank cells");require(state.reset.window[i]==window[i],"Native window uses the independently selected layer");}
        require(state.reset.timing.input.held==255&&state.reset.timing.input.pressed==1&&state.reset.timing.input.previous==33,"LCD restart does not resample input");
        require(state.reset.timing.lcdEpoch==state.reset.timing.end-20,"Restart epoch retains access tail and return");
        require(state.reset.timing.nextStat==state.reset.timing.lcdEpoch+23*456&&state.reset.timing.nextVBlank==state.reset.timing.lcdEpoch+144*456,"Future deadlines use new title geometry");
        require(state.reset.pendingRequests==3&&state.reset.servicesMasked&&state.reset.lcdc==0xc3&&state.reset.stat==1,"Pending services remain distinct from new periodic deadlines");
        require(state.lyc==23&&state.windowX==166&&state.windowY==112&&sound.enabled&&sound.song==13,"Title window setup retains game-over music without servicing it");
        for(int mode=0;mode<9;++mode){auto bad=reset;bool boot=true;
            if(mode==0)boot=false;if(mode==1)bad.servicesMasked=false;if(mode==2)bad.lcdc=0x43;if(mode==3)bad.pendingRequests=0;
            if(mode==4)bad.stat=1;if(mode==5)bad.timing.displays=545;if(mode==6)bad.timing.countdown=55;if(mode==7)bad.timing.input.held=33;if(mode==8)sound.enabled=false;
            bool rejected=false;try{airTitleLayout(bad,boot,sound,assets,[](auto...){},[](auto...){ });}catch(const std::runtime_error&){rejected=true;}
            require(rejected,"Unowned boot/reset/audio state must reject");sound.enabled=true;}
        for(int mode=0;mode<7;++mode){auto bad=assets;
            if(mode==0)bad.commands.pop_back();if(mode==1)bad.commands[1].kind=0;if(mode==2)bad.commands[5].a=0;if(mode==3)bad.commands[2].cells.pop_back();
            if(mode==4)bad.commands[1].a=31;if(mode==5)bad.commands[2].height=0;if(mode==6)bad.commands.back().cells.push_back(1);
            bool rejected=false;try{bad.validate();}catch(const std::runtime_error&){rejected=true;}require(rejected,"Invalid static geometry/payload must reject before timing");}
        const char* fixture="build/title-layout-test-fixture.dat";
        {std::ofstream f(fixture,std::ios::binary);f<<"CDNTL001";const char count[]={11,0};f.write(count,2);
            for(const auto& c:assets.commands){uint8_t h[]={uint8_t(c.kind),uint8_t(c.a),uint8_t(c.b),uint8_t(c.width),uint8_t(c.height)};f.write(reinterpret_cast<char*>(h),5);f.write(reinterpret_cast<const char*>(c.cells.data()),c.cells.size());}}
        require(AirTitleLayoutAssets::load(fixture).commands[9].cells==assets.commands[9].cells,"Decoded asset loader retains all raw tile identifiers");
        {std::ofstream f(fixture,std::ios::binary|std::ios::app);f.put(0);}
        bool rejected=false;try{AirTitleLayoutAssets::load(fixture);}catch(const std::runtime_error&){rejected=true;}require(rejected,"Trailing asset bytes must reject");std::remove(fixture);
        printf("PASS: %d native title-layout assertions.\n",checks);return 0;
    }catch(const std::exception& e){fprintf(stderr,"FAIL after %d checks: %s\n",checks,e.what());return 1;}
}
