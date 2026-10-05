// Experimental ordinary-clock native replay. No original service costs, per-
// update counters, world outcomes or voice states drive this probe. Source
// work is charged at semantic phase boundaries; subinstruction IRQ latency is
// deliberately not certified, and this is not yet the Windows-loop scheduler.
// Optional display input replaces update-aligned buttons with a button sample
// at every service; neither mode reads original per-update counters or costs.
#include "air.h"
#include "air_clock.h"
#include "air_placement_clock.h"
#include "air_work.h"
#include "audio.h"
#include "audio_work.h"
#include "ui.h"
#include <cstdio>
#include <fstream>
#include <memory>
#include <stdexcept>
#include <string>

using namespace ticd;
int main(int argc,char** argv){
    if(argc<3){fprintf(stderr,"Usage: air-clock-probe inputs.txt services.csv [difficulty [sprites.csv]] [--entities-csv entities.csv] [--display-inputs buttons.txt] [--final-wait | --outro-fade]\n");return 2;}
    try{
        int difficulty=1,positional=0;std::string spritePath,displayInputPath,entityPath;bool finalWait=false,outroFade=false;
        for(int i=3;i<argc;++i){std::string option=argv[i];
            if(option=="--display-inputs"&&i+1<argc)displayInputPath=argv[++i];
            else if(option=="--entities-csv"&&i+1<argc)entityPath=argv[++i];
            else if(option=="--final-wait")finalWait=true;
            else if(option=="--outro-fade"){finalWait=true;outroFade=true;}
            else if(option.rfind("--",0)==0)throw std::runtime_error("Unknown/incomplete clock probe option");
            else if(positional++==0)difficulty=std::stoi(option);
            else if(positional==2)spritePath=option;
            else throw std::runtime_error("Too many clock probe arguments");
        }
        auto assets=std::make_unique<AirAssets>(AirAssets::load(L"build/air.dat"));
        auto shared=std::make_unique<Assets>(Assets::load(L"build/crash.dat"));
        auto audio=std::make_unique<AudioAssets>(AudioAssets::load(L"build/audio.dat"));
        if(difficulty<0||difficulty>3)throw std::runtime_error("Invalid Air difficulty");
        auto game=std::make_unique<AirGame>(*assets,*shared);game->start(difficulty);game->measureWork=true;
        NativeAudio sound(*audio);sound.playMusic(9);sound.measureWork=true;
        AirClock clock;std::ifstream input(argv[1]);std::ofstream services(argv[2]);
        std::ifstream displayInputs;DisplayInput sampled;
        if(!displayInputPath.empty()){displayInputs.open(displayInputPath);if(!displayInputs)throw std::runtime_error("Cannot open display button samples");}
        auto decode=[](int held){return ((held&1)?A:0)|((held&2)?B:0)|((held&16)?Right:0)|((held&32)?Left:0)|((held&64)?Up:0)|((held&128)?Down:0);};
        std::ofstream phases(std::string(argv[2])+".phases.csv");
        if(!phases)throw std::runtime_error("Cannot open source-phase output");
        phases<<"update,phase,tick,start,end,work\n";
        int initialTick;
        if(!services||!(input>>initialTick>>game->secondTicks>>game->randomState))return 2;
        // Capture header describes the initial clock/timer/random phase after
        // the source pending startup service; it supplies no per-update clocks.
        game->ticks=(initialTick-1)&65535;
        services<<"service,cycle,ready,tick,display,effects,music,cursor,pending,bar0,bar1,bar2,bar3,bar4,bar5,inputHeld,inputPressed\n";
        std::ofstream spriteLog;
        if(!spritePath.empty()){spriteLog.open(spritePath);if(!spriteLog)throw std::runtime_error("Cannot open sprite-service output");spriteLog<<"service,slot,present,x,y,flags\n";}
        std::ofstream entityLog;
        if(!entityPath.empty()){entityLog.open(entityPath);if(!entityLog)throw std::runtime_error("Cannot open entity-state output");entityLog<<"update,slot,frame,flags,x,y\n";}
        int activeGamePhase=-1;
        bool spriteBoundarySafe=false;
        bool mapBoundarySafe=false;
        bool loopBoundarySafe=false;
        AirPlacementRange placementRange;
        auto display=[&](bool ready){
            if(!ready&&!loopBoundarySafe&&activeGamePhase!=3&&activeGamePhase!=5&&!(activeGamePhase==2&&spriteBoundarySafe)&&!(activeGamePhase==4&&mapBoundarySafe))throw std::runtime_error("Display interrupted unsupported gameplay phase "+std::to_string(activeGamePhase)+" at tick "+std::to_string(game->ticks)+" (service "+std::to_string(clock.displays)+"); finer ownership is required");
            if(spriteLog.is_open())for(int i=0;i<40;++i){const auto& s=game->sprites.slots[i];spriteLog<<clock.displays<<','<<i<<','<<(s.present&&s.y!=0)<<','<<s.x<<','<<s.y<<','<<s.flags<<'\n';}
            if(displayInputs.is_open()){
                int held;if(!(displayInputs>>held)||held<0||held>255)throw std::runtime_error("Missing/invalid display button sample");
                if(held&8)throw std::runtime_error("Display input requests pause; native pause-clock ownership is not yet accepted");
                sampled.sample(held);
            }
            int tick=game->ticks,pending=game->pendingSound;
            bool refreshRangeScratch=game->hudCursor==12;
            game->displayTick(ready);
            // 2f4c/16eb divides 48 * the byte-sized collected count. Its
            // overflow scratch FF9C ends at zero and can change later range
            // reads in an interrupted 19a2 scan. FF9E is not changed here.
            if(refreshRangeScratch)placementRange.low=0;
            if(pending>=0)sound.queueEffect(pending);
            game->pendingSound=-1;sound.tick();
            services<<clock.displays<<','<<clock.now<<','<<ready<<','<<tick<<','<<game->displayWorkCycles<<','<<sound.effectWorkCycles<<','<<sound.musicWorkCycles<<','<<game->hudCursor<<','<<pending;
            for(int i=7;i<13;++i)services<<','<<int(game->hudValues[i]);
            services<<','<<(displayInputs.is_open()?sampled.held:-1)<<','<<(displayInputs.is_open()?sampled.pressed:-1)<<'\n';
            if(game->displayWorkCycles<0||sound.effectWorkCycles<0||sound.musicWorkCycles<0)return -1;
            return 1592+game->displayWorkCycles+sound.effectWorkCycles+sound.musicWorkCycles;
        };
        clock.startup(display);
        puts("tick,handler,frame,flags,x,y,cameraX,cameraY,speed,rate,tilt,count,crash,anim,done,waiting,delay,period,transfer,remaining,map,result,seconds,secondTicks,random,pending");
        int ignoredTick,held,updates=0;
        while(input>>ignoredTick>>held){
            // 03c7's LD A completes before 03c9 commits the ready flag. A
            // pending display between them still sees the busy resource gate.
            loopBoundarySafe=true;clock.work(8,display,false);
            clock.atomicWork(12,[]{},display,true);loopBoundarySafe=false;
            clock.wait(display);clock.work(48,display,false);
            if(entityLog.is_open())for(int slot=0;slot<16;++slot){const auto& e=game->entities[slot];
                entityLog<<updates<<','<<slot<<','<<(e.alive?e.frame:255)<<','<<((e.flags&~2)|(e.offscreen?2:0))<<','<<e.x<<','<<e.y<<'\n';
            }
            int buttons=decode(displayInputs.is_open()?sampled.held:held);
            if(displayInputs.is_open())game->previous=decode(sampled.previous);
            bool priorMap=game->mapTransfer;
            auto priorSprites=game->sprites.slots;
            game->updateGame(buttons,true,true);
            game->sprites.slots=priorSprites;
            bool preparedMap=game->mapTransfer;
            game->mapTransfer=priorMap;
            mapBoundarySafe=!priorMap&&!preparedMap;
            // Entity updates are not interrupted in these accepted reference
            // cases. STAT affects only LCD object visibility. A
            // placement's spawn does not change callback-owned player/HUD,
            // prepared sprites, camera, transfer gate or pending effect.
            activeGamePhase=0;
            for(int work:{game->entityWorkCycles,game->resourceWorkCycles,game->spriteWorkCycles,
                          game->clearWorkCycles,game->mapWorkCycles,game->placementWorkCycles}){
                auto phaseStart=clock.now;
                int phaseTick=game->ticks;
                if(work<0){fprintf(stderr,"Unknown source work at update %d; replay stops before certification.\n",updates);return 3;}
                if(activeGamePhase==5){
                    work=airPlacementClock(*game,clock,placementRange,display);
                }else if(activeGamePhase==2){
                    int sum=112;
                    for(int n:game->spriteEntityWorkCycles)sum+=n;
                    if(sum!=work)throw std::runtime_error("Incomplete per-entity sprite work");
                    game->sprites=SpriteLayer(game->reverseSprites);game->sprites.slots=priorSprites;
                    spriteBoundarySafe=true;clock.work(112,display,false);
                    auto preparation=std::make_unique<AirGame>(*game);
                    preparation->entities=game->spriteInputEntities;
                    // airSpriteWork chooses the next allocation direction.
                    preparation->reverseSprites=!game->reverseSprites;
                    std::array<AirSpriteEntityWork,16> publication{};
                    auto planned=airSpriteWork(*preparation,nullptr,&publication);
                    if(planned.prepare!=work)throw std::runtime_error("Sprite publication work disagrees with preparation");
                    for(int i=0;i<16;++i){
                        int cost=game->spriteEntityWorkCycles[i];if(!cost)break;
                        clock.work(76,display,false);
                        const auto& plan=publication[i];
                        if(!plan.geometry){clock.work(cost-76,display,false);continue;}
                        int accounted=76+plan.geometry+plan.tail;
                        for(const auto& piece:plan.pieces)accounted+=piece.before+(piece.writes?156:0);
                        if(accounted!=cost)throw std::runtime_error("Incomplete piece-publication work");
                        clock.work(plan.geometry,display,false);
                        const auto& e=game->spriteInputEntities[i];const auto& frame=assets->frames[e.frame];
                        auto relative=[](int p,int c){return static_cast<int16_t>((p&65520)-(c&65520))/16;};
                        int x=relative(e.x,game->cameraX)+static_cast<int8_t>(frame.meta[0])+frame.meta[6]+8;
                        int y=relative(e.y,game->cameraY)+static_cast<int8_t>(frame.meta[1])+frame.meta[7]+16;
                        for(size_t n=0;n<plan.pieces.size();++n){
                            const auto& piece=frame.pieces[n];const auto& charge=plan.pieces[n];
                            clock.work(charge.before,display,false);
                            if(!charge.writes)continue;
                            int slot=game->sprites.preparedSlot();
                            auto* entry=slot>=0&&slot<40?&game->sprites.slots[slot]:nullptr;
                            // 1d24..1d3b writes Y, X, tile and flags in order.
                            // Decode/rendered colors stand in for tile data;
                            // this probe makes no tile/pixel parity claim.
                            clock.work(12,display,false);
                            clock.atomicWork(8,[&]{if(entry){entry->y=(y+((e.flags&64)?-piece.y-16:piece.y))&255;entry->present=entry->y!=0;}},display,false);
                            clock.work(16,display,false);
                            clock.atomicWork(8,[&]{if(entry)entry->x=(x+((e.flags&32)?-piece.x-8:piece.x))&255;},display,false);
                            clock.work(24,display,false);
                            clock.atomicWork(8,[&]{if(entry)entry->colors=e.frame<12&&piece.chunk>=0?game->spriteResources.colors(piece.chunk):piece.colors;},display,false);
                            clock.work(32,display,false);
                            clock.atomicWork(8,[&]{if(entry)entry->flags=(e.flags&0xe0)^piece.flags;},display,false);
                            clock.work(40,display,false);game->sprites.advancePreparedPiece();
                        }
                        game->sprites.finishPreparedEntity();
                        clock.work(plan.tail,display,false);
                    }
                    // The replay accounts for geometry/culling in updateGame;
                    // publication uses this independently rebuilt partial list.
                }else if(activeGamePhase==3){
                    int first=game->sprites.unusedFirst(),bytes=4*game->sprites.unusedCount();
                    if(!bytes)clock.work(work,display,false);
                    else{
                        int prefix=game->sprites.descending()?196:184;
                        if(work!=prefix+8*bytes+88)throw std::runtime_error("Incomplete sprite-clear source decomposition");
                        clock.work(prefix,display,false);
                        for(int byte=0;byte<bytes;++byte)clock.atomicWork(8,[&]{if(!(byte&3))game->sprites.slots[first+byte/4].present=false;},display,false);
                        clock.work(88,display,false);
                    }
                }else clock.work(work,display,false);
                if(activeGamePhase==4)game->mapTransfer=preparedMap;
                phases<<updates<<','<<activeGamePhase<<','<<phaseTick<<','<<phaseStart<<','<<clock.now<<','<<work<<'\n';
                ++activeGamePhase;
            }
            const auto& p=game->entities[0];
            printf("%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d\n",
                game->ticks,int(p.handler),p.frame,p.flags,p.x,p.y,game->cameraX,game->cameraY,
                game->speed,game->rate,game->tilt,p.params[0],p.params[2],p.anim,p.animDone,p.frameWaiting,
                p.delay,p.period,game->transferState,game->transferRemaining,game->mapTransfer,
                game->result,game->seconds,game->secondTicks,game->randomState,game->crashRecoveryPending);
            ++updates;
            // 03fa's result read/rotate/branch follows all six completed
            // gameplay phases. A display here sees the complete prepared
            // state while FFAE stays busy; it does not interrupt an entity.
            loopBoundarySafe=true;
            if(!game->result)clock.work(32,display,false); // Result test + taken back-edge.
            else clock.work(28,display,false); // Exit result test before 0400's optional final wait.
            loopBoundarySafe=false;
        }
        if(!input.eof())return 2;
        if(finalWait){
            if(!game->result)throw std::runtime_error("Final wait requires a completed stunt result");
            auto start=clock.now;int tick=game->ticks;unsigned servicesBefore=clock.displays;
            loopBoundarySafe=true;clock.wait(display,false);loopBoundarySafe=false;
            std::ofstream exit(std::string(argv[2])+".exit.csv");
            if(!exit)throw std::runtime_error("Cannot open final-wait output");
            exit<<"tickBefore,tickAfter,elapsed,displayServices,ready\n"
                <<tick<<','<<game->ticks<<','<<(clock.now-start)<<','<<(clock.displays-servicesBefore)<<",0\n";
            // With --final-wait alone, stop before 0403's audio stop/fade.
        }
        if(outroFade){
            auto ui=std::make_unique<UiAssets>(UiAssets::load(L"build/ui.dat"));
            std::ofstream outro(std::string(argv[2])+".outro.csv");
            if(!outro)throw std::runtime_error("Cannot open outro-phase output");
            outro<<"phase,index,tickBefore,tickAfter,elapsed,work,bgp,obp0,obp1,musicEnabled\n";
            int bgp=ui->fadePalettes[0],obp0=bgp&0xcf,obp1=bgp&0xf3;
            auto phase=[&](const char* name,int index,int work,auto&& operation){
                auto start=clock.now;int tick=game->ticks;operation();
                outro<<name<<','<<index<<','<<tick<<','<<game->ticks<<','<<(clock.now-start)<<','<<(work<0?clock.lastWaitWork:work)
                     <<','<<bgp<<','<<obp0<<','<<obp1<<','<<sound.enabled<<'\n';
            };
            // Until reset finishes, an interrupt could observe partially
            // cleared audio state. Reject that ownership rather than guessing.
            activeGamePhase=-1;
            phase("audioStop",0,audioStopWork(),[&]{clock.work(audioStopWork(),display,false);sound.stop();});
            loopBoundarySafe=true;
            phase("fadeEntry",0,44,[&]{clock.work(44,display,false);});
            for(int segment=0;segment<8;++segment){
                phase("palette",segment,76,[&]{clock.work(76,display,false);bgp=ui->fadePalettes[segment];obp0=bgp&0xcf;obp1=bgp&0xf3;});
                for(int wait=0;wait<4;++wait){
                    phase("wait",4*segment+wait,-1,[&]{clock.wait(display,false);});
                    int tail=wait<3?16:segment<7?28:40;
                    phase("tail",4*segment+wait,tail,[&]{clock.work(tail,display,false);});
                }
            }
            loopBoundarySafe=false;
            // 0409 starts DI/setup of the result screen. Its work, pixels and
            // original audio software-state reset are outside this probe.
        }
        fprintf(stderr,"Completed %d ordinary-clock updates, %u display services, %u STAT services; %s buttons.\n",updates,clock.displays,clock.statServices,displayInputs.is_open()?"display-sampled":"update-aligned");
        return 0;
    }catch(const std::exception& e){fprintf(stderr,"%s\n",e.what());return 1;}
}
