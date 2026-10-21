// Native retained campaign, inherited scroll, substitutions and input branches.
#include "../tools/selected_following_instruction_probe.h"
#include <cstdio>
#include <memory>
using namespace ticd;
int main(){int checks=0;auto require=[&](bool ok,const char* why){++checks;if(!ok)throw std::runtime_error(why);};
try{
    auto audio=AudioAssets::load(L"build/audio.dat");auto ui=std::make_unique<UiAssets>();
    ui->names={1,2,3,4,5,6,7,8,9,10};ui->startPrompt.fill(7);ui->fadePalettes={228,208,160,144,80,64,0,0};
    ui->instructions[1].text={0x82,0,0x81,0,17,0x86,5,0x87,8,0x89,0x85,0x84,4,0x80};
    for(bool two:{false,true})for(int profile=0;profile<3;++profile){bool skip=profile==1,scrollHeld=profile==2;
        NativeAudio sound(audio);sound.measureWork=true;sound.playMusic(2);
        // A completed instruction picture has already serviced its new song;
        // the first reset/start tick is not deferred into this continuation.
        for(int i=0;i<4;++i)sound.tick();
        AirResultHandoff campaign;campaign.player=two?1:0;campaign.lives={4,two?5:0};
        // The first LY read latches line 144 at VBlank, before its owned
        // display service completes; the earlier line-143 STAT is finished.
        auto& t=campaign.timing;t.end=2*AirClock::Frame+144*456-60;t.lcdEpoch=0;t.nextStat=3*AirClock::Frame+143*456;t.nextVBlank=2*AirClock::Frame+144*456;
        t.tick=65520;t.countdown=78;t.displays=554;t.stats=554;
        std::array<uint8_t,1024> background;background.fill(19);int samples=0;
        auto ended=airProbeSelectedFollowingInstruction("build/selected-following-instruction-unit-"+std::to_string(two)+"-"+std::to_string(profile),campaign,background,1,0,sound,*ui,[&]{return ++samples>=(skip?70:scrollHeld?92:150)?8:0;},64);
        const auto& c=ended.map.campaign;const auto& timing=c.timing;
        require(c.player==campaign.player&&c.lives==campaign.lives&&!c.result,"Instruction retains actual next player and both life counts");
        require(ended.skipped==skip&&ended.backgroundOwned&&!ended.speed&&!ended.skipMask,"Text completion and background ownership are native decisions");
        require(ended.map.scroll==(skip?0:8)&&ended.map.lyc==95&&ended.map.display==5&&ended.map.stat==5,"Inherited scroll clears at map setup and full text owns its scroll steps");
        require(!sound.enabled&&sound.song==-1&&std::none_of(sound.voices.begin(),sound.voices.end(),[](const MusicVoice& v){return v.active;}),"Exit independently stops all native logical voices");
        require(timing.tick==((65520+samples)&65535)&&timing.displays==554+samples&&timing.countdown==77,"Display/input/music counters continue across tick wrap and callback replacement");
        require(timing.nextStat>timing.end&&timing.nextVBlank>timing.end&&timing.nextStat%AirClock::Frame==95*456&&timing.nextVBlank%AirClock::Frame==144*456,"Returned deadlines preserve the actual instruction LCD epoch");
        if(!skip){for(int glyph=0;glyph<5;++glyph)require(ended.background[17*32+glyph]==ui->names[(two?5:0)+glyph],"Actual target player chooses the native name substitution");}
        else require(ended.background[17*32]==19,"Start skip cannot invent a delayed glyph publication");
        require(ended.background[19*32+1]==(skip||scrollHeld?19:7),"Start held during scrolling is ignored for skipping but retained for prompt bypass");
        for(int bad=0;bad<5;++bad){sound.playMusic(2);auto altered=campaign;if(bad==0)altered.lives[0]=5;if(bad==1)altered.player^=1;if(bad==2)altered.result=1;if(bad==3)altered.timing.perfect=true;if(bad==4)sound.stop();bool rejected=false;
            try{airProbeSelectedFollowingInstruction("build/selected-following-instruction-unit-invalid",altered,background,1,0,sound,*ui,{},64);}catch(const std::exception&){rejected=true;}
            require(rejected,"Unowned campaign/result/music cannot enter selected continuation");}
    }
    printf("PASS: %d native selected following-instruction assertions.\n",checks);return 0;
}catch(const std::exception& e){fprintf(stderr,"FAIL after %d checks: %s\n",checks,e.what());return 1;}}
