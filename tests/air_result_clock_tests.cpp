// Source-shaped native result tests; no ROM or reference emulator.
#include "air_result_transition.h"
#include "air_result_accounting.h"
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
        int timer=2;require(airResultCountdownWork(timer)==272&&timer==1,"The penultimate result service stores one");
        require(airResultCountdownWork(timer)==228&&timer==1,"Result timer's guarded zero decrement retains one and returns early");
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
            if(result==3){
                previous=-1; // The separate accounting interval begins at the shared fade return.
                AirResultTextAssets texts;for(auto& list:texts.layouts)list={{1,0,15},{0,0,0},{0,3,0},{4,0,0}};
                int glyphs=0,polls=0,sourceVectors=0;bool sawFrozenCounter=false;
                auto account=airResultAccount(incoming,3,0,3,4,2,sound,texts,
                    [&](const char*,int64_t cycle,int,int,int,int,int,int,bool,int){require(cycle>previous,"Success accounting boundaries increase through counting and final waits");previous=cycle;},
                    [&](unsigned,int64_t,int,int countdown,int display,int,int,bool){if(display==228)sawFrozenCounter=countdown==1;},
                    [&](const char*,int64_t,AirIrqOwner owner){require(owner==AirIrqOwner::CounterWait||owner==AirIrqOwner::SourceBoundary,"Every accounting request is owned by a wait or completed native operation");++sourceVectors;},
                    [&](int64_t,int mode){require(mode>=0&&mode<=3,"Accounting status reads retain native LCD modes");++polls;},
                    [&](int64_t,int address,int value){require(address>=0x9800&&address<0xa000&&value>=0&&value<=127,"Result glyph formatting retains bounded map destinations and values");++glyphs;});
                require(account.pay==0&&account.seconds==0&&account.savings==9&&account.stage==2,"Successful accounting transfers pay and time then advances Air's stage");
                require(account.timing.displays==660&&account.timing.countdown==1&&sawFrozenCounter,"Ordinary result completes its countdown plus the final 60-service hold");
                require(account.timing.tick==((65530+660)&65535)&&!sound.enabled,"Successful result retains counter wrapping and stops music");
                require(glyphs>60&&polls>=glyphs&&sourceVectors>1200,"Accounting owns actual glyph readiness accesses and complete periodic requests");
                for(int branch=0;branch<4;++branch){
                    NativeAudio skipSound(audio);skipSound.measureWork=true;skipSound.playMusic(4);
                    int sample=0,payWaits=0,timeWaits=0,skipSeen=0;std::string phase;
                    auto skipped=airResultAccount(incoming,3,0,10,0,3,skipSound,texts,
                        [&](const char* name,int64_t,int,int,int,int,int,int,bool,int latch){phase=name;skipSeen=latch;
                            payWaits+=phase=="payWait";timeWaits+=phase=="timeWait";},
                        [](unsigned,int64_t,int,int,int,int,int,bool){},
                        [](const char*,int64_t,AirIrqOwner){},[](int64_t,int){},[](int64_t,int,int){},
                        [&]{++sample;
                            if(branch==0&&sample==1)return 2;
                            if(branch==1&&sample==1)return 64;
                            if(branch==2&&phase=="payWait"&&payWaits==1)return 2;
                            if(branch==3&&phase=="timeWait"&&timeWaits==1)return 2;
                            if(phase=="timerWait"&&sample%2==0)return 2;
                            return 0;});
                    require(skipped.savings==13&&skipped.pay==0&&skipped.seconds==0&&skipped.stage==2,"Input skips preserve the complete pay/time ledger and stunt advance");
                    require(skipped.timing.displays<660&&skipped.timing.countdown>1,"A fresh action ends the final hold before the guarded timer");
                    require(skipSeen==(branch==1?64:2),"Ready wait retains unmasked direction edges; pay/time waits latch only action edges");
                    require(payWaits==(branch<2?0:branch==2?1:10)&&timeWaits==(branch<3?0:1),"Latched skips bypass subsequent per-cent waits and refreshes");
                }
            }
            if(result==1){
                int holdServices=0,holdWaits=0,holdTails=0;bool stopped=false;
                auto held=airResultFailureHold(incoming,result,0,sound,*ui,
                    [&](const char* name,int64_t cycle,int,int,int,int,int,bool enabled){require(cycle>previous,"Failure result boundaries increase through all hold waits");previous=cycle;
                        holdWaits+=std::string(name)=="holdWait";holdTails+=std::string(name)=="holdTail";if(std::string(name)=="musicStopped")stopped=!enabled;},
                    [&](unsigned index,int64_t,int tick,int countdown,int,int,int,bool){require(index==unsigned(34+holdServices)&&tick==((65530+34+holdServices)&65535)&&countdown==565-holdServices,"Failure hold continues the display counter and timer after incoming fade");++holdServices;},
                    [&](const char*,int64_t,AirIrqOwner owner){require(owner==AirIrqOwner::CounterWait,"Failure hold requests are owned by the source counter waits");});
                require(holdServices==480&&holdWaits==480&&holdTails==480&&held.displays==514&&held.countdown==86,"Failure result holds all 480 services without expiring its 600-service timer");
                require(stopped&&!sound.enabled&&held.end>incoming.end,"Failure result stops music before campaign handoff");
                for(int branch=0;branch<3;++branch){
                    NativeAudio skipSound(audio);skipSound.measureWork=true;skipSound.playMusic(3);
                    auto start=incoming;int sample=0,waits=0;
                    if(branch==2)start.input.held=start.input.previous=2;
                    auto skipped=airResultFailureHold(start,1,branch==2?2:0,skipSound,*ui,
                        [&](const char* name,int64_t,int,int,int,int,int,bool){waits+=std::string(name)=="holdWait";},
                        [](unsigned,int64_t,int,int,int,int,int,bool){},[](const char*,int64_t,AirIrqOwner){},
                        [&]{++sample;return branch==0?2:branch==1?(sample==1?64:2):2;});
                    int expectedWaits=branch==0?1:branch==1?2:480;
                    require(waits==expectedWaits&&skipped.displays==unsigned(34+expectedWaits),"Failure hold accepts fresh actions, ignores directions and does not reskip a held action");
                    require(skipped.countdown==566-expectedWaits&&!skipSound.enabled,"Shortened failure hold preserves timer and music-stop ownership");
                }
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
