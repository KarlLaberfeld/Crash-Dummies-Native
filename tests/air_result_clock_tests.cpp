// Source-shaped native result tests; no ROM or reference emulator.
#include "air_result_transition.h"
#include "air_result_accounting.h"
#include "air_result_handoff.h"
#include "air_instruction_header.h"
#include "air_instruction_picture.h"
#include <cstdio>
#include <memory>
using namespace ticd;
int main(){
    int checks=0;auto require=[&](bool value,const char* message){++checks;if(!value)throw std::runtime_error(message);};
    try{
        {
            AirClock clock;clock.now=10*AirClock::Frame+100;
            clock.nextStat=10*AirClock::Frame+AirClock::StatLine;clock.nextVBlank=10*AirClock::Frame+AirClock::VBlankLine;
            auto ordinary=airResultSetupPrefix(clock,3,[](const char*,int64_t){},[](int64_t,int){});
            for(int seed:{0,65535,65280,255,2056}){
                std::vector<std::string> names;std::vector<int64_t> cycles;
                auto perfect=airResultSetupPrefix(clock,7,[&](const char* name,int64_t cycle){names.push_back(name);cycles.push_back(cycle);},[](int64_t,int){},seed);
                require(perfect.end-ordinary.end==1556&&perfect.lcdDisabled==ordinary.lcdDisabled&&perfect.pollReads==ordinary.pollReads,"Perfect initialization adds its own work without changing the LCD-off wait");
                require(perfect.display==2&&perfect.stat==4&&perfect.countdown==720,"Perfect setup selects celebration, object-disable STAT and the longer countdown");
                require((perfect.celebration.randomState&255)==(seed&255),"Four emitter seeds retain the native shared random low byte");
                require(names[5]=="celebrationSelected"&&names[6]=="emitter0Ready"&&names[9]=="flagsReady","Perfect prefix exposes each completed initialization without duplicate terminal boundaries");
                require(cycles[6]-cycles[5]==364&&cycles[8]-cycles[7]==364&&cycles[9]-cycles[8]==356,"The final emitter tail call retains its shorter preparation cost");
                for(int i=0;i<4;++i){const auto& e=perfect.celebration.emitters[i];
                    require(e.x>=16&&e.x<=143&&e.y==143&&e.velocity==251&&e.radius==0&&e.delay==i*16,"Perfect emitters start at bounded positions with staggered delays");}
            }
            for(int seed:{-1,65536}){
                bool rejected=false;try{airResultSetupPrefix(clock,7,[](const char*,int64_t){},[](int64_t,int){},seed);}catch(const std::runtime_error&){rejected=true;}
                require(rejected,"Perfect prefix requires a valid native gameplay random seed");
            }
            require(ordinary.display==10&&ordinary.stat==0&&ordinary.countdown==600,"Ordinary result initialization remains separate");
        }
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
        {
            AirCelebration state;state.randomState=65535;
            for(int i=0;i<4;++i){state.reset(i);state.emitters[i].delay=2;}
            state.prepared.fill(77);
            require(state.advance(65535,*ui)==2084&&state.spriteCount==0&&std::all_of(state.prepared.begin(),state.prepared.end(),[](int b){return b==0;}),"Delayed emitters clear every old sprite byte before preparing an empty list");
            for(auto& e:state.emitters){e.delay=0;e.y=192;}
            require(state.advance(0,*ui)==4212&&state.spriteCount==0,"Completed particles reset their emitters without drawing in the same service");
            require((state.randomState&255)==255&&state.emitters[3].delay==48,"Celebration restarts retain low-byte RNG and staggered delays");
            for(auto& e:state.emitters){e.delay=0;e.y=143;e.radius=128;}
            require(state.advance(0,*ui)>2000&&state.spriteCount==40,"Four active emitters prepare the full sprite list at counter wrap");
            for(int i=0;i<40;++i)require(state.prepared[i*4+3]==128,"Prepared celebration keeps its original priority flag");
            struct WaveFixture {std::array<unsigned char,128> celebrationWave{};std::array<unsigned char,256> celebrationProducts{};} wave;
            wave.celebrationWave.fill(64);for(int i=0;i<256;++i)wave.celebrationProducts[i]=static_cast<unsigned char>(i*i/2);
            int work=0;int positive=state.offset(0,5,wave,work),negative=state.offset(128,5,wave,work);
            require(positive!=0&&negative==((-positive)&255),"Signed wave quadrants retain byte-wrapped symmetry for a nonzero displacement");
        }
        AirResultLayoutAssets layouts;NativeAudio sound(audio);sound.measureWork=true;
        for(int variant=0;variant<4;++variant){
            const char* path="local/air-result-profile-fixture.dat";
            {std::ofstream file(path,std::ios::binary);file.write(variant%2?"TICDRT02":"TICDRT01",8);
                std::array<char,16> zero{};int count=variant==0?5:variant==1?6:variant==2?6:5;
                for(int i=0;i<count;++i)file.write(zero.data(),zero.size());}
            bool rejected=false;AirResultLayoutAssets loaded;
            try{loaded=AirResultLayoutAssets::load(path);}catch(const std::runtime_error&){rejected=true;}
            std::remove(path);
            require(variant<2?(!rejected&&loaded.perfectProfile==bool(variant)):rejected,"Layout assets preserve legacy ordinary profiles and reject missing/trailing perfect profile data");
        }
        AirResultPrefix prefix;prefix.end=800000;prefix.lcdDisabled=prefix.end-727820;prefix.pendingRequests=3;
        for(int variant=0;variant<4;++variant){
            const char* path="local/air-result-label-fixture.dat";
            {std::ofstream file(path,std::ios::binary);file.write(variant%2?"TICDRL02":"TICDRL01",8);
                const char terminal[5]={1,0,4,0,0};int count=variant==0?3:variant==1?5:variant==2?5:3;
                for(int i=0;i<count;++i)file.write(terminal,5);}
            bool rejected=false;AirResultTextAssets loaded;
            try{loaded=AirResultTextAssets::load(path);}catch(const std::runtime_error&){rejected=true;}
            std::remove(path);
            require(variant<2?(!rejected&&loaded.perfectLabels==bool(variant)):rejected,"Result labels retain ordinary format compatibility and reject truncated/trailing perfect labels");
        }
        {
            auto perfectPrefix=prefix;perfectPrefix.display=2;perfectPrefix.stat=4;perfectPrefix.countdown=720;
            perfectPrefix.celebration.randomState=0;
            for(int i=0;i<4;++i)perfectPrefix.celebration.reset(i);
            auto perfectLayouts=layouts;perfectLayouts.perfectProfile=true;
            std::array<unsigned char,160> previous{};int prepared=0,services=0,stats=0;
            auto incoming=airResultIncoming(perfectPrefix,7,65530,5,0,sound,perfectLayouts,*ui,
                [](const char*,int64_t,int,int,int,int,int,bool){},
                [&](unsigned index,int64_t,int tick,int countdown,int display,int,int,bool){
                    require(index==unsigned(services)&&tick==((65530+services)&65535)&&countdown==719-services&&display>272,"Perfect services retain the old counter and their own celebration/countdown work");++services;},
                [&](const char* kind,int64_t,AirIrqOwner owner){require(owner!=AirIrqOwner::Unqualified,"Perfect pending/fade IRQs have explicit ownership");stats+=std::string(kind)=="stat";},{},
                [&](unsigned index,int tick,const AirCelebration& state,const std::array<unsigned char,160>& visible,int work){
                    require(index==unsigned(prepared)&&tick==((65530+prepared)&65535)&&work>0&&visible==previous,"Perfect publication retains the preceding prepared list while advancing the current one");previous=state.prepared;++prepared;});
            require(incoming.perfect&&services==33&&prepared==33&&stats==33&&incoming.countdown==687,"Perfect incoming fade completes 33 services from its longer countdown");
            require(incoming.celebration.emitters[3].delay==15&&sound.enabled,"Perfect incoming carries ongoing emitter and music state into subsequent accounting");
            AirResultTextAssets texts;texts.perfectLabels=true;
            for(auto& list:texts.layouts)list={{1,0,15},{0,0,0},{0,3,0},{4,0,0}};
            int publications=0;
            auto account=airResultAccount(incoming,7,0,3,4,2,sound,texts,
                [](const char*,int64_t,int,int,int,int,int,int,bool,int){},
                [](unsigned,int64_t,int,int,int,int,int,bool){},[](const char*,int64_t,AirIrqOwner){},
                [](int64_t,int){},[](int64_t,int,int){},{},ui.get(),
                [&](unsigned,int,const AirCelebration&,const std::array<unsigned char,160>&,int){++publications;});
            require(account.savings==14&&account.pay==0&&account.seconds==0&&account.stage==2,"Perfect accounting pays each original unit twice without doubling its decrement");
            require(account.timing.perfect&&account.timing.countdown==1&&account.timing.displays==780&&publications==747,"Perfect accounting retains animation through its longer timer and final hold");
            for(int branch=0;branch<3;++branch){
                NativeAudio skipSound(audio);skipSound.measureWork=true;skipSound.playMusic(5);
                int sample=0,payWaits=0,timeWaits=0;std::string phase;
                auto skipped=airResultAccount(incoming,7,0,3,4,2,skipSound,texts,
                    [&](const char* name,int64_t,int,int,int,int,int,int,bool,int){phase=name;payWaits+=phase=="payWait";timeWaits+=phase=="timeWait";},
                    [](unsigned,int64_t,int,int,int,int,int,bool){},[](const char*,int64_t,AirIrqOwner){},
                    [](int64_t,int){},[](int64_t,int,int){},[&]{++sample;
                        if(branch==0&&sample==1)return 2;
                        if(branch==1&&phase=="payWait"&&payWaits==1)return 2;
                        if(branch==2&&phase=="timeWait"&&timeWaits==1)return 2;
                        if(phase=="timerWait"&&sample%2==0)return 2;
                        return 0;},ui.get());
                require(skipped.savings==14&&skipped.pay==0&&skipped.seconds==0&&skipped.stage==2,"Perfect input skips preserve the complete doubled pay/time ledger");
                require(skipped.timing.displays<780&&skipped.timing.countdown>1&&!skipSound.enabled,"Perfect final-hold action skips retain animation state and stop music");
            }
            sound.stop();
        }
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
                    require(waits==expectedWaits&&skipped.displays==34+expectedWaits,"Failure hold accepts fresh actions, ignores directions and does not reskip a held action");
                    require(skipped.countdown==566-expectedWaits&&!skipSound.enabled,"Shortened failure hold preserves timer and music-stop ownership");
                }
            }
        }
        for(int scenario=0;scenario<3;++scenario){
            sound.stop();AirResultTransition start;start.end=10*AirClock::Frame+100;start.lcdEpoch=0;
            start.nextStat=10*AirClock::Frame+143*456;start.nextVBlank=10*AirClock::Frame+AirClock::VBlankLine;
            start.tick=65535;start.countdown=2;
            int player=scenario==2?1:0;std::array<int,2> lives={5,scenario==1?5:0};
            int stores=0,points=0,polls=0,displays=0;
            auto handoff=airResultHandoff(start,player,lives,3,sound,
                [&](const char*,int64_t,int,int,int,int,int,int,const DisplayInput&){++points;},
                [&](unsigned,int64_t,int tick,int countdown,int cost,int,int,const DisplayInput&){
                    require(tick==((65535+displays)&65535)&&countdown==1&&cost==(displays?228:272),"Handoff services retain counter wrapping and the frozen-one timer");++displays;},
                [&](const char*,int64_t,AirIrqOwner owner){require(owner==AirIrqOwner::SourceBoundary,"Handoff requests wait for identified access completion");},
                [&](int64_t,int mode){require(mode>=0&&mode<=3,"Handoff readiness stays in qualified steady LCD modes");++polls;},
                [&](int64_t,int destination,int value){require(destination==0x9800+stores&&value==0,"Handoff clears all map cells in destination order");++stores;});
            require(stores==1024&&polls>=stores&&displays>0,"Complete background clear owns every store and display service");
            require(handoff.player==(scenario==1?1:0)&&handoff.lives==lives&&handoff.result==0,"Handoff selects a live player, retains both life records and clears the result");
            require(points==(scenario==0?11:7),"Only an eliminated opposite player requires a second selection pass");
            require(handoff.timing.tick==((65535+displays)&65535)&&handoff.timing.countdown==1,"Handoff returns the continuing timer and input clock");
        }
        {
            sound.stop();bool rejected=false;try{airResultHandoff(AirResultTransition{},0,{0,0},3,sound,
                [](const char*,int64_t,int,int,int,int,int,int,const DisplayInput&){},
                [](unsigned,int64_t,int,int,int,int,int,const DisplayInput&){},
                [](const char*,int64_t,AirIrqOwner){},[](int64_t,int){},[](int64_t,int,int){});
            }catch(const std::runtime_error&){rejected=true;}
            require(rejected,"All-player elimination requires its separate title return owner");
        }
        for(int variant=0;variant<4;++variant){
            const char* path="local/air-header-fixture.dat";
            {std::ofstream file(path,std::ios::binary);file.write("TICDIH01",8);const char names[6]={1,2,3,4,5,6};file.write(names,6);
                const char terminal[5]={1,0,4,0,0};for(int i=0;i<(variant==1?11:12);++i)file.write(terminal,5);
                if(variant==2)file.put(0);}
            bool rejected=false;AirInstructionHeaderAssets header;
            try{header=AirInstructionHeaderAssets::load(path);}catch(const std::runtime_error&){rejected=true;}
            std::remove(path);
            require(variant==1||variant==2?rejected:!rejected,"Header asset loader rejects missing lists and trailing bytes");
            if(variant!=3)continue;
            header.layouts[0]={{1,0,0},{5,0,0},{4,0,0}};
            for(int lives:{1,9,255})for(int player:{0,1}){
                sound.stop();AirResultHandoff state;state.player=player;state.lives={lives,lives};
                state.timing.end=2*AirClock::Frame+100;state.timing.nextStat=2*AirClock::Frame+120*456;
                state.timing.nextVBlank=2*AirClock::Frame+AirClock::VBlankLine;state.timing.countdown=100;
                std::vector<int> glyphs;int services=0;
                auto finished=airInstructionHeader(state,2,3,sound,header,
                    [](const char*,int64_t,int,int,int,int,int,const DisplayInput&){},
                    [&](unsigned,int64_t,int,int,int,int,int,const DisplayInput&){++services;},
                    [](const char*,int64_t,AirIrqOwner owner){if(owner==AirIrqOwner::Unqualified)throw std::runtime_error("Unowned header fixture vector");},
                    [](int64_t,int){},[&](int64_t,int address,int value){require(address>=0x9800&&address<0x9c00,"Header uses its cleared background layer");glyphs.push_back(value);});
                require(glyphs==std::vector<int>({header.playerNames[player][0],header.playerNames[player][1],header.playerNames[player][2],std::min(lives,9)+1}),"Header name substitution and life clamp own their glyph values");
                require(services==1&&finished.timing.tick==1&&finished.timing.countdown==99&&finished.lives==state.lives,"Header retains campaign lives and completes its own counter wait");
            }
        }
        for(int stage:{1,2}){
            sound.stop();AirResultHandoff state;state.lives={5,0};
            state.timing.end=2*AirClock::Frame+AirClock::VBlankLine+3000;
            state.timing.nextStat=3*AirClock::Frame+120*456;state.timing.nextVBlank=3*AirClock::Frame+AirClock::VBlankLine;
            state.timing.countdown=100;
            for(int tile=52;tile<116;++tile)for(int row=0;row<8;++row)for(int column=0;column<8;++column)
                ui->instructions[stage].tiles[tile*64+row*8+column]=(row+column)&3;
            for(auto& value:ui->instructions[stage].map)value=37;
            int tiles=0,maps=0,services=0,polls=0;
            auto picture=airInstructionPicture(state,stage,sound,*ui,
                [](const char*,int64_t,int,int,bool,const DisplayInput&){},
                [&](unsigned,int64_t,int,int,int,int,int,const DisplayInput&){++services;},
                [](const char*,int64_t,AirIrqOwner owner){if(owner!=AirIrqOwner::SourceBoundary)throw std::runtime_error("Unowned picture fixture vector");},
                [&](int64_t,int mode){require(mode>=0&&mode<=3,"Picture polls native steady LCD readiness");++polls;},
                [&](const char* kind,int64_t,int address,int value){
                    if(std::string(kind)=="tile"){
                        require(address==0x8340+tiles&&value==std::array<int,8>{0x55,0x33,0xaa,0x66,0x55,0xcc,0xaa,0x99}[tiles%8],"Instruction tile bytes retain plane order and pixel positions");++tiles;
                    }else{require(address==0x9800+(3+maps/10)*32+5+maps%10&&value==37,"Picture rows retain their ten-column width and 32-column map pitch");++maps;}
                });
            require(tiles==1024&&maps==90&&polls>=1114&&services>0,"Picture prefix owns every tile and map destination and its intervening services");
            require(sound.enabled&&picture.timing.tick==services&&picture.timing.countdown==100-services,"Instruction song and timer retain their native continuing state");
        }
        {
            sound.stop();AirResultHandoff state;state.timing.end=2*AirClock::Frame;
            state.timing.nextStat=state.timing.end+100;state.timing.nextVBlank=state.timing.end+1000;
            bool rejected=false;int writes=0;
            try{airInstructionPicture(state,1,sound,*ui,[](const char*,int64_t,int,int,bool,const DisplayInput&){},
                [](unsigned,int64_t,int,int,int,int,int,const DisplayInput&){},[](const char*,int64_t,AirIrqOwner){},
                [](int64_t,int){},[&](const char*,int64_t,int,int){++writes;});}
            catch(const std::runtime_error&){rejected=true;}
            require(rejected&&!sound.enabled&&!writes,"An unowned interrupt during song reset cannot receive an aggregate timing allowance");
        }
        auto reject=[&](int result,int lives,int held){sound.stop();try{airResultIncoming(prefix,result,0,lives,held,sound,layouts,*ui,[](const char*,int64_t,int,int,int,int,int,bool){},[](unsigned,int64_t,int,int,int,int,int,bool){},[](const char*,int64_t,AirIrqOwner){});return false;}catch(const std::runtime_error&){return true;}};
        require(reject(1,1,0),"Final-life transition cannot borrow ordinary failure timing");
        require(reject(7,5,0),"Perfect celebration cannot borrow ordinary success timing");
        require(reject(3,5,15),"Soft reset cannot borrow returning display bookkeeping");
        prefix.pendingRequests=0;require(reject(3,5,0),"Unqualified result startup cannot borrow pending requests");
        printf("Air result-clock checks: %d passed (synthetic; no original parity claim)\n",checks);return 0;
    }catch(const std::exception& error){fprintf(stderr,"Air result-clock test failed after %d checks: %s\n",checks,error.what());return 1;}
}
