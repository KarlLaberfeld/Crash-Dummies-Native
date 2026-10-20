// Synthetic layout/macro/scroll/skip cases with native instruction music.
#include "air_title_text.h"
#include <memory>
#include <cstdio>
using namespace ticd;
int main(){int checks=0;auto require=[&](bool ok,const char* why){++checks;if(!ok)throw std::runtime_error(why);};
try{
    auto audio=AudioAssets::load(L"build/audio.dat");auto ui=std::make_unique<UiAssets>();ui->names={1,2,3,4,5,6,7,8,9,10};
    ui->instructions[1].text={0x82,0,0x81,0,17,0x86,5,0x87,8,0x89,0x85,0x84,4,0x80};
    AirTitlePicture seed;seed.title.fresh.campaign.start(false,1,0);auto& f=seed.title.fresh.instruction.start.menu.page.close.fade;auto& r=f.layout.reset;auto& t=r.timing;
    r.servicesMasked=false;r.alternate=1;r.display=r.stat=5;r.lcdc=0xd1;f.layout.lyc=95;f.bgp=0xe4;f.obp0=0xc4;f.obp1=0xe0;
    r.background.fill(19);seed.tiles.fill(37);t.end=2*AirClock::Frame+7000;t.nextStat=2*AirClock::Frame+95*456;t.nextVBlank=2*AirClock::Frame+144*456;t.tick=65520;t.countdown=54;t.displays=739;t.stats=968;t.lives=5;
    for(bool skip:{false,true}){NativeAudio sound(audio);sound.measureWork=true;sound.playMusic(2);int samples=0,services=0,steps=0;std::vector<int> glyphs,centers;
        auto state=airTitleText(seed,sound,*ui,
            [&](const char* name,int64_t,int,int,const AirInstructionTextState& s,const DisplayInput&){if(std::string(name)=="skip")require(s.skipContext==1,"A Start edge inside a name retains its semantic substitution context");if(std::string(name)=="scrollStored")++steps;},
            [&](unsigned index,int64_t,int tick,int countdown,int display,int effects,int music,const DisplayInput&){require(index==unsigned(739+services)&&tick==((65520+services)&65535)&&countdown==54&&display==144&&effects==64&&music>=60,"Actual text waits advance input/tick/music without spending campaign countdown");++services;},
            [&](const char*,int64_t,AirIrqOwner owner){require(owner!=AirIrqOwner::Unqualified,"Every text interrupt has an explicit completion owner");},
            [&](int64_t,int mode){require(mode>=0&&mode<=3,"All text stores retain LCD readiness ownership");},
            [&](int64_t,int address,int value){if(address>=0x9800&&address<0x9c00)glyphs.push_back(value);else if(address==0xc09c)centers.push_back(value);else require(address==0xff42&&value>=0&&value<=8,"Only identified scroll writes occur outside text storage");},
            [&]{++samples;return skip&&samples==1?8:0;});
        require(state.text.skipped==skip&&!state.text.speed&&!state.text.skipMask&&state.text.backgroundOwned,"Text returns its own completion/skip and published map state");
        if(skip)require(glyphs.empty()&&centers.empty()&&services==1&&steps==0,"A fresh Start aborts its delayed first glyph and scans to the actual terminator");
        else require(glyphs==std::vector<int>({1,2,3,4,5,4})&&centers==std::vector<int>({1,3,6,7,8})&&services==40&&steps==5&&state.text.map.scroll==8,"Full text owns name substitution, glyph delays and all five scroll steps");
        const auto& after=state.picture.title.fresh.instruction.start.menu.page.close.fade.layout.reset;
        require(after.timing.tick==((65520+services)&65535)&&after.timing.countdown==54&&state.picture.title.fresh.campaign.players[0].lives==5,"Returned native campaign/counters continue correctly across tick wrap");
        require(state.picture.tiles==seed.tiles&&after.window==r.window&&after.objects==r.objects&&state.text.background==after.background,"Text preserves full picture/window/object storage and exposes its own full background");
    }
    printf("PASS: %d native title-text assertions.\n",checks);return 0;
}catch(const std::exception& e){fprintf(stderr,"FAIL after %d checks: %s\n",checks,e.what());return 1;}}
