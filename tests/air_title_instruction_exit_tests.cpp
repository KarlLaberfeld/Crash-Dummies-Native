// Prompt/fresh-Start and held-Start instruction exit with active native music.
#include "air_title_instruction_exit.h"
#include <cstdio>
#include <memory>
using namespace ticd;
int main(){int checks=0;auto require=[&](bool ok,const char* why){++checks;if(!ok)throw std::runtime_error(why);};
try{
    auto assets=AudioAssets::load(L"build/audio.dat");auto ui=std::make_unique<UiAssets>();ui->startPrompt.fill(7);ui->fadePalettes={228,208,160,144,80,64,0,0};
    for(bool held:{false,true}){NativeAudio sound(assets);sound.measureWork=true;sound.playMusic(2);AirTitleText seed;seed.picture.title.fresh.campaign.start(false,1,0);
        auto& f=seed.picture.title.fresh.instruction.start.menu.page.close.fade;f.bgp=0xe4;f.obp0=0xc4;f.obp1=0xe0;f.layout.reset.alternate=1;f.layout.reset.background.fill(19);
        auto& map=seed.text.map;map.lcdc=0xd1;map.lyc=95;map.alternate=1;map.display=map.stat=5;map.scroll=8;map.campaign.lives={5,0};
        auto& t=map.campaign.timing;t.end=2*AirClock::Frame+7000;t.nextStat=2*AirClock::Frame+95*456;t.nextVBlank=2*AirClock::Frame+144*456;t.tick=65520;t.countdown=54;t.displays=1000;t.stats=1000;t.lives=5;t.input={held?8:0,held?8:0,0};
        seed.text.backgroundOwned=true;seed.text.background=f.layout.reset.background;seed.text.cursor=0x9800+17*32;seed.text.row=17;seed.picture.tiles.fill(37);
        int samples=0,services=0,glyphs=0,palettes=0,waits=0,inputWaits=0;bool prompt=false;
        auto out=airTitleInstructionExit(seed,sound,*ui,
            [&](const char* name,int64_t,int,int,int,int,int,int,bool,const DisplayInput&){std::string kind=name;if(kind=="prompt")prompt=true;if(kind=="fadePalette")++palettes;if(kind=="fadeReady")++waits;if(kind=="inputWait")++inputWaits;},
            [&](unsigned index,int64_t,int tick,int countdown,int display,int effects,int music,const DisplayInput&){require(index==unsigned(1000+services)&&tick==((65520+services)&65535)&&countdown==54&&display==144&&effects==64&&music>=60,"Actual prompt/fade displays preserve campaign countdown and advance music/input/tick");++services;},
            [&](const char*,int64_t,AirIrqOwner owner){require(owner!=AirIrqOwner::Unqualified,"Every exit vector has a native acceptance owner");},
            [&](int64_t,int mode){require(mode>=0&&mode<=3,"Prompt glyph stores retain readiness ownership");},
            [&](int64_t,int address,int value){if(address>=0x9800&&address<0x9c00){require(address==seed.text.cursor+glyphs&&value==7,"Prompt uses the retained text cursor and independent glyphs");++glyphs;}
                else require(address==0xff42||address==0xff47||address==0xff48||address==0xff49,"Exit cannot modify unrelated game state");},
            [&]{++samples;return held||samples>=3?8:0;});
        require(prompt!=held&&glyphs==(held?0:20)&&inputWaits==(held?0:3)&&palettes==8&&waits==32&&services==(held?33:36),"Held Start bypasses prompt; fresh confirmation retains its waits and full outgoing fade");
        require(!sound.enabled&&sound.song==-1&&std::none_of(sound.voices.begin(),sound.voices.end(),[](const MusicVoice& v){return v.active;}),"Native logical driver and voices stop after the final wait/reset");
        require(out.text.map.campaign.timing.tick==((65520+services)&65535)&&out.text.map.campaign.timing.countdown==54&&out.picture.title.fresh.campaign.players[0].lives==5,"Exit retains native campaign and actual wrapped tick");
        require(out.picture.tiles==seed.picture.tiles&&out.text.background==out.picture.title.fresh.instruction.start.menu.page.close.fade.layout.reset.background,"Exit preserves image tiles and publishes its own prompt map");
        for(int mode=0;mode<4;++mode){sound.playMusic(2);auto bad=seed;if(mode==0)bad.text.backgroundOwned=false;if(mode==1)bad.text.skipMask=8;if(mode==2)bad.picture.title.fresh.instruction.start.menu.page.close.fade.bgp=0;if(mode==3)bad.text.map.alternate=0;bool rejected=false;
            try{airTitleInstructionExit(bad,sound,*ui,[](auto...){},[](auto...){},[](auto...){},[](auto...){},[](auto...){ });}catch(const std::exception&){rejected=true;}require(rejected,"Incomplete text or incorrect palette/map ownership cannot enter the exit");}
    }
    printf("PASS: %d native title-instruction-exit assertions.\n",checks);return 0;
}catch(const std::exception& e){fprintf(stderr,"FAIL after %d checks: %s\n",checks,e.what());return 1;}}
