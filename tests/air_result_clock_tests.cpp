// Source-shaped native result tests; no ROM or reference emulator.
#include "air_result_transition.h"
#include <cstdio>
#include <memory>
using namespace ticd;
int main(){
    int checks=0;auto require=[&](bool value,const char* message){++checks;if(!value)throw std::runtime_error(message);};
    try{
        AirResultLayoutProfile glyphs;glyphs.zero=2;glyphs.nonzero=3;glyphs.anchors=1;glyphs.rows=1;
        require(glyphs.work()==2112,"Static layout work distinguishes zero glyphs, text and row movement");
        AirResultLayoutProfile rectangle;rectangle.width=10;rectangle.height=9;rectangle.carries=1;
        auto noCarry=rectangle;noCarry.carries=0;
        require(rectangle.work()-noCarry.work()==8,"Rectangle row carry retains its conditional return cost");
        AirResultLayoutProfile empty;require(empty.work()==360,"Empty script retains entry and terminator work");
        require(airResultMusicStartWork()==14052,"Music start includes fixed reset, song roots and hardware restore");
        bool invalid=false;rectangle.width=33;try{rectangle.work();}catch(const std::runtime_error&){invalid=true;}
        require(invalid,"Unsupported rectangle size rejects");
        AudioAssets audio;for(int voice=0;voice<4;++voice)audio.commands.emplace(AudioAssets::key(voice,0,false),MusicCommand{MusicOp::Stop,0,{}});
        auto ui=std::make_unique<UiAssets>();ui->fadePalettes={0xe4,0xe4,0xe4,0xa4,0x90,0x50,0x50,0};
        AirResultLayoutAssets layouts;NativeAudio sound(audio);sound.measureWork=true;
        AirResultPrefix prefix;prefix.end=800000;prefix.lcdDisabled=prefix.end-727820;prefix.pendingRequests=3;
        for(int result:{1,3,17}){
            sound.stop();int services=0;int64_t previous=-1;std::vector<std::string> kinds;std::vector<int64_t> times;
            auto incoming=airResultIncoming(prefix,result,65530,5,0,sound,layouts,*ui,
                [&](const char*,int64_t cycle,int,int,int,int,int,bool){require(cycle>previous,"Result boundaries increase across masked setup and restarted display");previous=cycle;},
                [&](unsigned index,int64_t,int tick,int countdown,int display,int,int,bool){require(index==unsigned(services)&&tick==((65530+services)&65535)&&countdown==599-services&&display==272,"Result counter, timer and update counter belong to the display service");++services;},
                [&](const char* kind,int64_t cycle,AirIrqOwner owner){require(owner!=AirIrqOwner::Unqualified,"Every result IRQ has an identified completion owner");kinds.push_back(kind);times.push_back(cycle);});
            int expected=result&2?33:34;
            require(services==expected&&incoming.displays==expected&&incoming.countdown==600-expected,"Incoming fade completes 32 waits after identified setup services");
            require(incoming.tick==((65530+expected)&65535),"Result services retain original 16-bit counter wrapping");
            require(kinds.size()==size_t(2*expected)&&kinds[0]=="vblank"&&kinds[1]=="stat","Pending result services retain priority and full vector coverage");
            require(times[2]==incoming.lcdEpoch+143*456+20,"Restarted result STAT belongs to line 143");
            if(result==1){
                int holdServices=0,holdWaits=0,holdTails=0;bool stopped=false;
                auto held=airResultFailureHold(incoming,result,0,sound,*ui,
                    [&](const char* name,int64_t cycle,int,int,int,int,int,bool enabled){require(cycle>previous,"Failure result boundaries increase through all hold waits");previous=cycle;
                        holdWaits+=std::string(name)=="holdWait";holdTails+=std::string(name)=="holdTail";if(std::string(name)=="musicStopped")stopped=!enabled;},
                    [&](unsigned index,int64_t,int tick,int countdown,int,int,int,bool){require(index==unsigned(34+holdServices)&&tick==((65530+34+holdServices)&65535)&&countdown==565-holdServices,"Failure hold continues the display counter and timer after incoming fade");++holdServices;},
                    [&](const char*,int64_t,AirIrqOwner owner){require(owner==AirIrqOwner::CounterWait,"Failure hold requests are owned by the source counter waits");});
                require(holdServices==480&&holdWaits==480&&holdTails==480&&held.displays==514&&held.countdown==86,"Failure result holds all 480 services without expiring its 600-service timer");
                require(stopped&&!sound.enabled&&held.end>incoming.end,"Failure result stops music before campaign handoff");
            }
        }
        auto reject=[&](int result,int lives,int held){sound.stop();try{airResultIncoming(prefix,result,0,lives,held,sound,layouts,*ui,[](const char*,int64_t,int,int,int,int,int,bool){},[](unsigned,int64_t,int,int,int,int,int,bool){},[](const char*,int64_t,AirIrqOwner){});return false;}catch(const std::runtime_error&){return true;}};
        require(reject(1,1,0),"Final-life transition cannot borrow ordinary failure timing");
        require(reject(7,5,0),"Perfect celebration cannot borrow ordinary success timing");
        require(reject(3,5,15),"Soft reset cannot borrow returning display bookkeeping");
        prefix.pendingRequests=0;require(reject(3,5,0),"Unqualified result startup cannot borrow pending requests");
        printf("Air result-clock checks: %d passed (synthetic; no original parity claim)\n",checks);return 0;
    }catch(const std::exception& error){fprintf(stderr,"Air result-clock test failed after %d checks: %s\n",checks,error.what());return 1;}
}
