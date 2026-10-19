// Native final-life ownership and fixed-wait guards; no ROM/reference input.
#include "air_final_result.h"
#include "air_game_over_return.h"
#include "audio_music_work.h"
#include <cstdio>
#include <memory>
using namespace ticd;
int main(){
    int checks=0;auto require=[&](bool ok,const char* why){++checks;if(!ok)throw std::runtime_error(why);};
    try{
        AirPauseLcd lcd;lcd.objectsEnabled=lcd.windowEnabled=false;
        require(lcd.mode(3040)==-1,"Steady-frame owner still rejects first-frame text");lcd.resultFirstVisibleFrame=true;
        require(lcd.mode(3040)==0&&lcd.mode(3264)==2&&lcd.mode(3296)==3,"Qualified result text samples retain observed blank/scan/transfer modes");
        for(int64_t t:{int64_t(-4),int64_t(0),int64_t(455),int64_t(143*456)})require(lcd.mode(t)==-1,"Restart line and first-frame VBlank remain unowned");
        lcd.scrollX=1;require(lcd.mode(3040)==-1,"First-frame result cannot acquire scrolling geometry");lcd.scrollX=0;
        lcd.objectsEnabled=true;require(lcd.mode(3040)==-1,"First-frame result cannot acquire objects");lcd.objectsEnabled=false;
        lcd.windowEnabled=true;require(lcd.mode(3040)==-1,"First-frame result cannot acquire a window");lcd.windowEnabled=false;
        bool rejected=false;try{lcd.readable(3040);}catch(const std::runtime_error&){rejected=true;}
        require(rejected,"Readiness qualification does not certify arbitrary first-frame VRAM reads");
        MusicVoice voice;voice.stage=255;voice.envelopeCounter=1;
        require(audioEnvelopeWork(3,voice,3,5)==284&&audioEnvelopeWork(5,voice,3,5)==284,"Both noise channels use register-bit lookup work");
        require(audioEnvelopeWork(0,voice,3,5)==288,"Pulse lookup retains memory-bit work");
        require(audioEnvelopeWork(0,voice,255,5)-audioEnvelopeWork(3,voice,255,5)==4,"Noise marker branch also retains register-bit work");
        AudioAssets audio;for(int v=0;v<4;++v)audio.commands.emplace(AudioAssets::key(v,0,false),MusicCommand{MusicOp::Stop,0,{}});
        auto ui=std::make_unique<UiAssets>();ui->fadePalettes={0xe4,0xe4,0xe4,0xa4,0x90,0x50,0x50,0};
        AirResultLayoutAssets layouts;AirResultTextAssets text;text.finalLabel=true;
        const char* fixture="build/air-final-layout-fixture.dat";
        for(int version:{1,2,3}){
            {std::ofstream file(fixture,std::ios::binary);file<<"TICDRL0"<<version;
                for(int i=0;i<(version==1?3:version==2?5:6);++i){const unsigned char data[]={1,0,4,0,0};file.write(reinterpret_cast<const char*>(data),5);}}
            auto loaded=AirResultTextAssets::load(fixture);
            require(loaded.perfectLabels==(version>=2)&&loaded.finalLabel==(version==3),"Older text assets retain their explicit capabilities");
            require(loaded.layouts[0].size()==1&&loaded.layouts[5].size()==(version==3?1:0),"Final banner is required only in the new diagnostic asset version");
        }
        {std::ofstream file(fixture,std::ios::binary);file<<"TICDRL03";}
        {bool failed=false;try{AirResultTextAssets::load(fixture);}catch(const std::runtime_error&){failed=true;}
            require(failed,"Truncated final text assets cannot masquerade as a complete banner");}
        std::remove(fixture);
        text.layouts[5].push_back({1,0,17});for(int i=0;i<13;++i)text.layouts[5].push_back({0,0,0});text.layouts[5].push_back({4,0,0});
        AirResultPrefix prefix;prefix.end=800000;prefix.lcdDisabled=72000;prefix.pendingRequests=3;
        int64_t baseline=0;
        for(int money:{0,1,99,100,9999,10000,999999})for(int buttons:{0,1,8,33}){
            NativeAudio sound(audio);sound.measureWork=true;int waits=0,stored=0,reads=0;int64_t store=0;std::vector<int> tail;
            auto state=airFinalResult(prefix,33,65530,1,33,money,sound,layouts,text,*ui,
                [&](const char* name,int64_t cycle,int,int,int,int,int,bool,int lives,int savings){
                    const std::string n=name;if(n=="holdWait")++waits;if(n=="lifeStored"){++stored;store=cycle;}
                    if(n=="lifeExhausted")require(cycle-store==16&&lives==0,"Taken final-life branch owns its exact completion");
                    require(savings==money,"Final failure preserves supplied campaign savings");},
                [](auto...){},[](auto...){},[&](auto...){++reads;},[&](int64_t,int,int value){tail.push_back(value);},
                [&,buttons]{return (++reads&1)?buttons:0;});
            require(state.lives==0&&stored==1,"Final result consumes one native life exactly once");
            require(waits==480&&state.displays==514&&state.stats==514,"Fresh actions cannot skip the fixed game-over hold");
            require(state.countdown==86&&state.tick==((65530+514)&65535),"Full fixed hold retains display/countdown wrap ownership");
            require(sound.song==13&&sound.enabled,"Game-over music remains selected through the high-score call boundary");
            require(tail.size()>=7&&tail[tail.size()-3]==0x2c&&tail[tail.size()-2]==(money%100)/10+1&&tail.back()==money%10+1,"Savings retain comma and two forced cents digits");
            if(money==0&&buttons==0)baseline=state.end;
            if(money==0&&buttons==0){
                for(int position=0;position<3;++position){
                    std::array<uint8_t,48> board{};for(int row=0;row<8;++row)board[6*row+3+position]=1;
                    const auto original=board;int rows=0,compares=0;
                    auto returned=airGameOverReturn(state,0,{0,0},board,sound,*ui,
                        [&](const char* name,auto...){if(std::string(name)=="row")++rows;if(std::string(name)=="compare")++compares;},[](auto...){},[](auto...){},[]{return 0;});
                    require(rows==8&&compares==8*(position+1),"Ranking rejects at the first differing BCD byte in every row");
                    require(board==original,"A rejected result never inserts or changes names/scores");
                    require(returned.displays==546&&returned.stats==546&&returned.countdown==54,"No-survivor return owns all 32 outgoing fade displays");
                }
                for(int mode=0;mode<3;++mode){
                    std::array<uint8_t,48> board{};std::array<int,2> living{};
                    if(mode==1)living[1]=1;if(mode==2)board[3]=0xfa;
                    bool failed=false;try{airGameOverReturn(state,0,living,board,sound,*ui,[](auto...){},[](auto...){},[](auto...){ });}catch(const std::runtime_error&){failed=true;}
                    require(failed,"Qualifying scores, surviving players and invalid BCD need separate owners");
                }
            }
            if(money==0)require(state.end==baseline,"Action edges do not change fixed-hold completion");
        }
        for(int lives:{0,2,5}){
            NativeAudio sound(audio);sound.measureWork=true;bool failed=false;
            try{airFinalResult(prefix,33,0,lives,0,0,sound,layouts,text,*ui,[](auto...){},[](auto...){},[](auto...){},[](auto...){},[](auto...){ });}catch(const std::runtime_error&){failed=true;}
            require(failed,"Separate final owner cannot consume zero or multiple remaining lives");
        }
        for(int mode=0;mode<4;++mode){
            auto invalid=prefix;int held=0;
            if(mode==0)invalid.display=2;if(mode==1)invalid.stat=4;if(mode==2)invalid.countdown=720;if(mode==3)held=256;
            NativeAudio sound(audio);sound.measureWork=true;bool failed=false;
            try{airFinalResult(invalid,33,0,1,held,0,sound,layouts,text,*ui,[](auto...){},[](auto...){},[](auto...){},[](auto...){},[](auto...){ });}catch(const std::runtime_error&){failed=true;}
            require(failed,"Final-life accounting cannot borrow another result's selectors or input");
        }
        {NativeAudio sound(audio);sound.measureWork=true;bool failed=false;
            try{airResultIncoming(prefix,33,0,1,0,sound,layouts,*ui,[](auto...){},[](auto...){},[](auto...){ });}catch(const std::runtime_error&){failed=true;}
            require(failed,"Established non-final incoming API still rejects last-life accounting");}
        printf("PASS: %d native final-result assertions.\n",checks);return 0;
    }catch(const std::exception& e){fprintf(stderr,"FAIL after %d checks: %s\n",checks,e.what());return 1;}
}
