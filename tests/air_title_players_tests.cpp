#include "air_title_players_exit.h"
#include "air_following_setup.h"
#include "air_title_instruction_exit.h"
#include <cstdio>
#include <memory>
using namespace ticd;
int main(){int checks=0;auto require=[&](bool ok,const char* why){++checks;if(!ok)throw std::runtime_error(why);};try{
    auto audio=AudioAssets::load(L"build/audio.dat");auto ui=std::make_unique<UiAssets>(UiAssets::load(L"build/ui.dat"));
    std::vector<std::vector<int>> cases={{8},{4,0,8},{1},{2},std::vector<int>(24,4),{204},{9},std::vector<int>(64,0)};cases[4].insert(cases[4].end(),{0,8});cases[7].push_back(8);
    for(int page=0;page<5;++page)for(size_t scenario=0;scenario<cases.size();++scenario){AirTitleMenu seed;seed.route=3;seed.waits=3;seed.remaining=478;seed.page.cleared=2;seed.page.rows=10;seed.page.opened=40;
        seed.page.close.fade.bgp=228;seed.page.close.fade.obp0=196;seed.page.close.fade.obp1=224;
        auto& l=seed.page.close.fade.layout;auto& r=l.reset;auto& t=r.timing;l.bootShown=true;l.windowX=166;l.windowY=112;l.lyc=23;r.servicesMasked=false;r.stat=1;r.lcdc=195;r.background.fill(19);r.window=ui->titleMaps[0];
        t.displays=665;t.stats=860;t.countdown=54;t.tick=65500;t.input.held=t.input.pressed=4;t.end=200*AirClock::Frame+144*456+2400;t.nextStat=201*AirClock::Frame+23*456;t.nextVBlank=201*AirClock::Frame+144*456;
        if(page){seed.carouselOwned=true;seed.index=page;seed.remaining=std::array<int,5>{480,480,960,480,960}[page]-2;t.displays+=1000*page;t.stats+=2000*page;}
        const unsigned initialDisplays=t.displays;
        NativeAudio sound(audio);sound.measureWork=true;sound.playMusic(1);int samples=0,services=0,glyphs=0,cursorWrites=0;
        auto result=airTitlePlayers(seed,sound,*ui,
            [&](const char*,int64_t,const AirTitlePlayers& s,int song,bool enabled){require(s.players>=0&&s.players<=1&&s.closed<=40&&s.opened<=40&&song==1&&enabled,"Native player page retains its selection range and live title music");},
            [&](unsigned i,int64_t,int tick,int countdown,int display,int effects,int music,const DisplayInput&){require(i==unsigned(initialDisplays+services)&&tick==((65500+services)&65535)&&countdown==54&&display==116&&effects>=64&&music>=60,"Player page owns independent services and rollover");++services;},
            [](auto...){},[](auto...){},[](auto...){},[&](int64_t,int address,int){if(address>=0x9c00&&address<0xa000)++glyphs;if(address>=0xc100&&address<=0xc103)++cursorWrites;},
            [&]{int index=samples++-81;if(index<0)return 0;if(index>=int(cases[scenario].size()))throw std::runtime_error("Missing player page exit");return cases[scenario][index];});
        const auto& after=result.menu.page.close.fade.layout.reset;
        require(result.closed==40&&result.cleared==2&&result.opened==40&&glyphs==684,"Select page completes both clears, all forty-four glyphs and both forty-wait motions");
        require(result.waits==int(cases[scenario].size())&&services==81+result.waits&&samples==services&&cursorWrites==4*result.waits,"Every loop updates all four cursor bytes once before fresh input");
        require(result.players==int(scenario==1||scenario==4||scenario==5)&&result.route==((scenario==2||scenario==3)?1:2),"Toggle precedes Start, held selection creates one edge and Start outranks A/B");
        require(after.objects[1]==24&&after.objects[3]==128&&after.background==r.background&&sound.song==1,"Blink cursor retains original X/priority and surrounding storage");
        require(after.timing.nextStat>after.timing.end&&after.timing.nextVBlank>after.timing.end,"Player page preserves a continuing independent clock at the outgoing clear entry");
        int clearStores=0,returnDisplays=0;int64_t clearBegin=after.timing.end;
        auto continuation=airTitlePlayersExit(result,sound,*ui,[](auto...){},
            [&](unsigned,int64_t,int,int countdown,int display,int effects,int music,const DisplayInput&){require(countdown==54&&display==116&&effects>=64&&music>=60&&sound.song==1,"A/B return continues title music through every actual display");++returnDisplays;},
            [](auto...){},[](auto...){},[](auto...){},
            [&](int64_t cycle,int address,int value){if(address>=0xc100&&address<0xc200){require(address==0xc100+clearStores&&value==0&&cycle==clearBegin+16+8*clearStores,"Selection clear writes exactly 160 bytes at original completion boundaries");++clearStores;}},[]{return 0;});
        const auto& ended=continuation.selection.menu.page.close.fade.layout.reset;
        require(continuation.page==(result.route==2?page:0)&&continuation.selection.menu.carouselOwned==(page>0&&result.route==2),"Start retains the actual page; A/B resets page origin only after the real store and reopen");
        require(clearStores==160&&ended.objects==std::array<uint8_t,256>{}&&continuation.selection.players==result.players,"Continuation clears the arrow and preserves selected player count");
        if(result.route==2)require(!continuation.titleReturned&&returnDisplays==0&&ended.timing.end==clearBegin+1316,"Start returns after the exact source clear without a fabricated display");
        else require(continuation.titleReturned&&returnDisplays==82&&continuation.closed==40&&continuation.cleared==2&&continuation.opened==40&&continuation.rows==10&&continuation.selection.menu.remaining==480&&sound.song==1,"A/B completes closing, both clears, full page zero and reopening without restarting title music");
        if(result.route==2){
            auto noop=[](auto...){};auto service=[](auto...){};auto sample=[]{return 0;};
            require(continuation.selection.menu.selectedPlayers&&continuation.selection.menu.playerChoice==result.players&&continuation.selection.menu.route==2,"Selected Start is derived from the actual exit decision and retained player count");
            auto started=airTitleStart(continuation.selection.menu,sound,*ui,noop,service,noop,noop,noop,sample);
            auto prepared=airTitleInstruction(started,sound,noop,noop,noop);Campaign previous;for(auto& p:previous.players){p.day=1;p.difficulty=0;}
            auto fresh=airTitleCampaign(prepared,previous,{1,0,result.players!=0},sound,noop,noop,noop);
            require(fresh.campaign.players[0].lives==5&&fresh.campaign.players[1].lives==(result.players?5:0),"Fresh campaign gives five lives only to selected players");
            auto resumed=airTitleResume(fresh,33,sound,noop,service,noop,noop,noop,sample);auto headers=AirInstructionHeaderAssets::load("build/instruction-header.dat");
            auto headed=airTitleHeader(resumed,sound,headers,noop,service,noop,noop,noop,sample);auto picture=airTitlePicture(headed,sound,*ui,noop,service,noop,noop,noop,sample);
            require(sound.song==2&&sound.enabled&&picture.title.fresh.campaign.players[1].lives==(result.players?5:0),"Selected one/two-player Start reaches independent instruction picture and music with its actual lives");
            auto entered=airTitleEntrance(picture,sound,*ui,noop,service,noop,noop,sample);
            auto text=airTitleText(entered,sound,*ui,noop,service,noop,noop,noop,[]{return 8;});
            auto exited=airTitleInstructionExit(text,sound,*ui,noop,service,noop,noop,noop,[]{return 8;});
            require(!sound.enabled&&exited.text.backgroundOwned&&exited.picture.title.fresh.campaign.players[1].lives==(result.players?5:0),"Selected campaign also traverses held-Start instruction skip/exit without losing the second player");
            auto setup=airFollowingSetupPrefix(exited.text,1,0,sound,noop,noop,noop);auto profiles=AirFollowingStageAssets::load("build/following-setup.dat");
            auto staged=airFollowingStageSetup(setup,profiles.profiles[0],sound,noop);auto entry=airFollowingEntry(staged,sound,noop,noop,noop,[]{return 0;});
            require(entry.instruction.map.campaign.lives[0]==5&&entry.instruction.map.campaign.lives[1]==(result.players?5:0)&&entry.instruction.map.campaign.timing.displays==exited.text.map.campaign.timing.displays+2&&entry.hudCursor==2&&entry.fadeRemaining==7&&entry.display==4&&entry.stat==4&&sound.song==9,"Initial selected Air setup retains actual player lives and reaches two independently scheduled game displays");
        }
    }
    printf("PASS: %d native player-selection assertions.\n",checks);return 0;
}catch(const std::exception& e){fprintf(stderr,"FAIL after %d checks: %s\n",checks,e.what());return 1;}}
