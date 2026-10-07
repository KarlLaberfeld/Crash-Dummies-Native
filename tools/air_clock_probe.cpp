// Experimental ordinary-clock native replay. No original service costs, per-
// update counters, world outcomes or voice states drive this probe. Source
// work is charged at semantic boundaries. Identified placement/access owners
// now qualify their completion; other aggregate IRQ latency is not certified.
// This is not yet the Windows-loop scheduler.
// Optional display input replaces update-aligned buttons with a button sample
// at every service; neither mode reads original per-update counters or costs.
#include "air.h"
#include "air_clock.h"
#include "air_placement_clock.h"
#include "air_scene_clock.h"
#include "air_result_clock.h"
#include "air_result_transition.h"
#include "air_pause_session.h"
#include "air_pause_lcd.h"
#include "air_pixels.h"
#include "air_work.h"
#include "audio.h"
#include "audio_work.h"
#include "ui.h"
#include <cstdio>
#include <fstream>
#include <memory>
#include <set>
#include <stdexcept>
#include <string>

using namespace ticd;
int main(int argc,char** argv){
    if(argc<3){fprintf(stderr,"Usage: air-clock-probe inputs.txt services.csv [difficulty [sprites.csv]] [--entities-csv entities.csv] [--audio-csv voices.csv] [--interrupts-csv interrupts.csv] [--display-inputs buttons.txt] [--pause-entry graphics.json | --pause-replay] [--final-wait | --outro-fade | --result-prefix | --result-incoming | --result-failure-hold]\n");return 2;}
    try{
        int difficulty=1,positional=0;std::string spritePath,displayInputPath,entityPath,pauseEntryPath,audioPath,framesPath,frameSelection,interruptPath;bool finalWait=false,outroFade=false,resultPrefix=false,resultIncoming=false,resultHold=false,pauseEntryReached=false,pauseReplay=false,paused=false;
        for(int i=3;i<argc;++i){std::string option=argv[i];
            if(option=="--display-inputs"&&i+1<argc)displayInputPath=argv[++i];
            else if(option=="--result-prefix"){resultPrefix=true;outroFade=true;finalWait=true;}
            else if(option=="--result-incoming"){resultIncoming=true;resultPrefix=true;outroFade=true;finalWait=true;}
            else if(option=="--result-failure-hold"){resultHold=true;resultIncoming=true;resultPrefix=true;outroFade=true;finalWait=true;}
            else if(option=="--entities-csv"&&i+1<argc)entityPath=argv[++i];
            else if(option=="--pause-entry"&&i+1<argc)pauseEntryPath=argv[++i];
            else if(option=="--pause-replay")pauseReplay=true;
            else if(option=="--audio-csv"&&i+1<argc)audioPath=argv[++i];
            else if(option=="--interrupts-csv"&&i+1<argc)interruptPath=argv[++i];
            else if(option=="--frames-dir"&&i+1<argc)framesPath=argv[++i];
            else if(option=="--frame-services"&&i+1<argc)frameSelection=argv[++i];
            else if(option=="--final-wait")finalWait=true;
            else if(option=="--outro-fade"){finalWait=true;outroFade=true;}
            else if(option.rfind("--",0)==0)throw std::runtime_error("Unknown/incomplete clock probe option");
            else if(positional++==0)difficulty=std::stoi(option);
            else if(positional==2)spritePath=option;
            else throw std::runtime_error("Too many clock probe arguments");
        }
        if(!pauseEntryPath.empty()&&(displayInputPath.empty()||finalWait))throw std::runtime_error("Pause entry requires display inputs and cannot include an outro");
        if(pauseReplay&&(displayInputPath.empty()||!pauseEntryPath.empty()))throw std::runtime_error("Pause replay requires display inputs and cannot stop at pause entry");
        if(framesPath.empty()!=frameSelection.empty())throw std::runtime_error("Frame output requires a directory and selected services");
        std::set<unsigned> frameServices;
        for(size_t begin=0;begin<frameSelection.size();){
            auto end=frameSelection.find(',',begin);auto value=frameSelection.substr(begin,end-begin);
            if(value.empty()||value.find_first_not_of("0123456789")!=std::string::npos)throw std::runtime_error("Invalid frame service selection");
            frameServices.insert(static_cast<unsigned>(std::stoul(value)));if(end==std::string::npos)break;begin=end+1;
        }
        std::unique_ptr<UiAssets> frameUi;if(!framesPath.empty())frameUi=std::make_unique<UiAssets>(UiAssets::load(L"build/ui.dat"));
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
        services<<"service,cycle,ready,tick,display,effects,music,cursor,pending,bar0,bar1,bar2,bar3,bar4,bar5,inputHeld,inputPressed,displaySelector\n";
        std::ofstream pausePhases,pauseBus,pauseStorage;
        std::ofstream audioLog;
        if(!audioPath.empty()){
            audioLog.open(audioPath);if(!audioLog)throw std::runtime_error("Cannot open native audio-state output");
            audioLog<<"service,voice,musicCost,voiceCost,active,position,remaining,fixed,loopCount,transpose,noTranspose,fineTune,note,targetNote,frequency,stage,envelopeCounter,volume,releaseCounter,tableIndex,arpCounter,direction,vibratoWait,vibratoCounter,pitchWait,effectRequest\n";
        }
        AirPauseAssets pauseAssets;
        if(pauseReplay){
            pauseAssets=AirPauseAssets::load("build/pause.dat");
            pausePhases.open(std::string(argv[2])+".pause.phases.csv");pauseBus.open(std::string(argv[2])+".pause.bus.csv");pauseStorage.open(std::string(argv[2])+".pause.graphics.csv");
            if(!pausePhases||!pauseBus||!pauseStorage)throw std::runtime_error("Cannot open pause replay outputs");
            pausePhases<<"phase,start,end,work\n";pauseBus<<"phase,kind,address,value,cycle\n";
            pauseStorage<<"phase,cycle";for(int i=0;i<20;++i)pauseStorage<<",status"<<i;for(int i=0;i<128;++i)pauseStorage<<",font"<<i;pauseStorage<<'\n';
        }
        std::ofstream spriteLog;
        if(!spritePath.empty()){spriteLog.open(spritePath);if(!spriteLog)throw std::runtime_error("Cannot open sprite-service output");spriteLog<<"service,slot,present,x,y,flags\n";}
        std::ofstream entityLog;
        if(!entityPath.empty()){entityLog.open(entityPath);if(!entityLog)throw std::runtime_error("Cannot open entity-state output");entityLog<<"update,slot,frame,flags,x,y\n";}
        int activeGamePhase=-1;
        int currentUpdate=-1;
        std::ofstream interruptLog;
        if(!interruptPath.empty()){
            interruptLog.open(interruptPath);if(!interruptLog)throw std::runtime_error("Cannot open native interrupt output");
            interruptLog<<"kind,vectorCycle,owner,update,phase\n";
        }
        clock.interrupt=[&](const char* kind,int64_t time,AirIrqOwner owner){
            // Protected handoffs have a source model and synthetic tests, but
            // no independently captured pending-service crossing yet. Quiet
            // controls must not silently certify that unobserved path.
            if(owner==AirIrqOwner::ProtectedResume)
                throw std::runtime_error("Protected Air service resume needs an independent pending-interrupt witness");
            if(interruptLog.is_open())interruptLog<<kind<<','<<time<<','<<int(owner)<<','<<currentUpdate<<','<<activeGamePhase<<'\n';
        };
        bool spriteBoundarySafe=false;
        bool mapBoundarySafe=false;
        bool mapRowReady=true;
        bool loopBoundarySafe=false;
        AirPlacementRange placementRange;
        int projectionPalette=-1; // Only the native outgoing palette owner overrides gameplay fade.
        std::array<uint8_t,Width*Height> projectedScene{};unsigned projectedService=0;
        int projectedPalette=0;bool selectedProjection=false;
        std::array<uint8_t,Width> projectedBackground{};SpriteLayer projectedSprites(false);int projectedScroll=0;
        std::array<uint8_t,Width*Height> projectedOwners{};
        std::array<int,Width*Height> projectedPalettes{};
        int64_t projectedLineZero=0;
        std::ofstream pixelEdges;
        if(!framesPath.empty()){pixelEdges.open(framesPath+"/edges.csv");if(!pixelEdges)throw std::runtime_error("Cannot open native pixel edges");pixelEdges<<"service,disableDot,halted,limit,owner\n";}
        auto writeProjection=[&]{
            std::ofstream file(framesPath+"/native-"+std::to_string(projectedService)+".pgm",std::ios::binary);
            if(!file)throw std::runtime_error("Cannot open local frame output");
            file<<"P5\n160 144\n255\n";
            for(size_t i=0;i<projectedScene.size();++i)file.put(static_cast<char>(255-85*((projectedPalettes[i]>>(projectedScene[i]*2))&3)));
        };
        clock.objectDisable=[&](int64_t time,AirIrqOwner owner){
            if(!selectedProjection)return;
            if(time<AirClock::StatLine)return; // Startup's pending STAT precedes the first projected visible frame.
            int dot=static_cast<int>((time+8)%AirClock::Frame)-AirClock::StatLine;
            int limit=airLastLineObjectLimit(projectedSprites,projectedScroll,dot);
            // Interrupted instructions still have unqualified acceptance
            // latency. Certify only if a conservative 24-cycle range changes
            // none of this publication's actual object pixels.
            if(owner==AirIrqOwner::Unqualified){
                int later=airLastLineObjectLimit(projectedSprites,projectedScroll,std::min(dot+24,456));
                for(int x=limit;x<later;++x)if(projectedScene[135*Width+x]!=projectedBackground[x])
                    throw std::runtime_error("Unowned interrupted line-135 object edge");
            }
            for(int x=limit;x<Width;++x){projectedScene[135*Width+x]=projectedBackground[x];projectedOwners[135*Width+x]=0;}
            pixelEdges<<projectedService<<','<<dot<<','<<(owner==AirIrqOwner::CounterWait)<<','<<limit<<','<<int(owner)<<'\n';writeProjection();
        };
        auto display=[&](bool ready){
            if(!ready&&!loopBoundarySafe&&activeGamePhase!=3&&activeGamePhase!=5&&!(activeGamePhase==2&&spriteBoundarySafe)&&!(activeGamePhase==4&&mapBoundarySafe))throw std::runtime_error("Display interrupted unsupported gameplay phase "+std::to_string(activeGamePhase)+" at tick "+std::to_string(game->ticks)+" (service "+std::to_string(clock.displays)+"); finer ownership is required");
            // The transfer flag already has a source owner, so scalar display
            // work can be compared while row data is still being prepared.
            // A partial row's actual transferred tiles need a separate image
            // owner; selecting this publication must still reject.
            if(activeGamePhase==4&&!mapRowReady&&frameServices.count(clock.displays))
                throw std::runtime_error("Interrupted row pixels need a buffered tile publication owner");
            if(spriteLog.is_open())for(int i=0;i<40;++i){const auto& s=game->sprites.slots[i];spriteLog<<clock.displays<<','<<i<<','<<(s.present&&s.y!=0)<<','<<s.x<<','<<s.y<<','<<s.flags<<'\n';}
            if(displayInputs.is_open()){
                int held;if(!(displayInputs>>held)||held<0||held>255)throw std::runtime_error("Missing/invalid display button sample");
                if((held&8)&&pauseEntryPath.empty()&&!pauseReplay)throw std::runtime_error("Display input requests pause; native pause-clock ownership is not yet accepted");
                sampled.sample(held);
            }
            int tick=game->ticks,pending=game->pendingSound;
            bool refreshRangeScratch=!paused&&game->hudCursor==12;
            if(paused){
                if(ready||pending!=-1||sound.pendingEffect!=-1||(sampled.held&15)==15)
                    throw std::runtime_error("Unowned paused resource/effect/reset service");
                game->publishVideo();game->ticks=(game->ticks+1)&65535;game->displayWorkCycles=160;
            }else game->displayTick(ready);
            // 2f4c/16eb divides 48 * the byte-sized collected count. Its
            // overflow scratch FF9C ends at zero and can change later range
            // reads in an interrupted 19a2 scan. FF9E is not changed here.
            if(refreshRangeScratch)placementRange.low=0;
            if(pending>=0)sound.queueEffect(pending);
            game->pendingSound=-1;sound.tick();
            selectedProjection=frameServices.count(clock.displays);
            if(selectedProjection){
                game->render(false,Width,&projectedOwners);projectedScene=paused?renderPausedGame(*frameUi,game->screen):game->screen;
                if(paused)std::fill(projectedOwners.begin()+PlayHeight*Width,projectedOwners.end(),0);
                projectedSprites=game->visibleSprites;projectedScroll=(game->visibleCameraX>>4)&255;
                game->render(false,0);std::copy_n(game->screen.begin()+135*Width,Width,projectedBackground.begin());
                projectedService=clock.displays;
                projectedPalette=projectionPalette>=0?projectionPalette:frameUi->fadePalettes[std::min(game->displayFadeRemaining,7)];
                // Keep the published scene; apply later source palette writes
                // only to pixels whose bounded output edge follows each write.
                projectedLineZero=(clock.now/AirClock::Frame+1)*AirClock::Frame-8;
                projectedPalettes.fill(projectedPalette);
                writeProjection();
            }
            if(audioLog.is_open())for(int i=0;i<6;++i){const auto& v=sound.voices[i];
                audioLog<<clock.displays<<','<<i<<','<<sound.musicWorkCycles<<','<<sound.voiceWorkCycles[i]<<','<<int(v.active)<<','<<v.position<<','<<v.remaining<<','<<v.fixed<<','<<v.loopCount
                    <<','<<v.transpose<<','<<v.noTranspose<<','<<v.fineTune<<','<<v.note<<','<<v.targetNote<<','<<v.frequency<<','<<v.stage<<','<<v.envelopeCounter<<','<<v.volume
                    <<','<<v.releaseCounter<<','<<v.tableIndex<<','<<v.arpCounter<<','<<v.direction<<','<<v.vibratoWait<<','<<v.vibratoCounter<<','<<v.pitchWait<<','<<pending<<'\n';
            }
            services<<clock.displays<<','<<clock.now<<','<<ready<<','<<tick<<','<<game->displayWorkCycles<<','<<sound.effectWorkCycles<<','<<sound.musicWorkCycles<<','<<game->hudCursor<<','<<pending;
            for(int i=7;i<13;++i)services<<','<<int(game->hudValues[i]);
            services<<','<<(displayInputs.is_open()?sampled.held:-1)<<','<<(displayInputs.is_open()?sampled.pressed:-1)<<','<<(paused?1:4)<<'\n';
            if(game->displayWorkCycles<0||sound.effectWorkCycles<0||sound.musicWorkCycles<0)return -1;
            return 1592+game->displayWorkCycles+sound.effectWorkCycles+sound.musicWorkCycles;
        };
        std::ofstream startupLog(std::string(argv[2])+".startup.csv");
        if(!startupLog)throw std::runtime_error("Cannot open native startup boundaries");
        startupLog<<"boundary,cycle\n";
        clock.startup(display,[&](const char* name,int64_t cycle){startupLog<<name<<','<<cycle<<'\n';});
        puts("tick,handler,frame,flags,x,y,cameraX,cameraY,speed,rate,tilt,count,crash,anim,done,waiting,delay,period,transfer,remaining,map,result,seconds,secondTicks,random,pending");
        int ignoredTick,held,updates=0,pauses=0;
        while(input>>ignoredTick>>held){
            currentUpdate=updates;activeGamePhase=-1;
            // 03c7's LD A completes before 03c9 commits the ready flag. A
            // pending display between them still sees the busy resource gate.
            // The first ready store already belongs to startup's pending
            // services. Later iterations arrive at 03c7 via the back-edge.
            if(updates){
                loopBoundarySafe=true;clock.work(8,display,false);
                clock.atomicWork(12,[]{},display,true);loopBoundarySafe=false;
            }
            clock.wait(display);
            if(!pauseEntryPath.empty()||pauseReplay){
                // The original reads fresh Start before its conditional pause
                // call. Preserve that read across a later pending service.
                int fresh=0;loopBoundarySafe=true;
                clock.work(4,display,false);clock.atomicWork(12,[]{},display,false);
                clock.accessWork(12,8,[&]{fresh=sampled.pressed;},display,false);
                clock.work(8+(fresh&8?24:12),display,false);loopBoundarySafe=false;
                if((fresh&8)&&!pauseEntryPath.empty()){
                    std::ofstream out(pauseEntryPath);if(!out)throw std::runtime_error("Cannot open native pause-entry graphics output");
                    out<<"{\"version\":1,\"pauseComplete\":false,\"cycle\":"<<clock.now<<",\"updates\":"<<updates
                       <<",\"tick\":"<<game->ticks<<",\"inputHeld\":"<<sampled.held<<",\"inputPrevious\":"<<sampled.previous
                       <<",\"pendingEffect\":"<<game->pendingSound<<",\"displayServices\":"<<clock.displays
                       <<",\"scrollX\":"<<((game->visibleCameraX>>4)&255)
                       <<",\"scrollY\":"<<((game->visibleCameraY>>4)&255)<<",\"windowX\":7,\"windowY\":136,\"objects\":[";
                    for(int i=0;i<40;++i){if(i)out<<',';const auto& s=game->visibleSprites.slots[i];
                        out<<"{\"x\":"<<s.x<<",\"y\":"<<(s.present?s.y:0)<<",\"flags\":"<<s.flags<<'}';
                    }
                    out<<"],\"hudRow\":[";for(int i=0;i<20;++i){if(i)out<<',';out<<int(game->hudMap[i]);}
                    out<<"]}\n";pauseEntryReached=true;break;
                }
                if((fresh&8)&&pauseReplay){
                    if(pauses++)throw std::runtime_error("Candidate currently compares one pause per replay");
                    if(game->pendingSound!=-1||sound.pendingEffect!=-1)throw std::runtime_error("Unowned pending effect at pause entry");
                    AirPauseLcd lcd;lcd.scrollX=(game->visibleCameraX>>4)&255;
                    for(int i=0;i<40;++i){const auto& s=game->visibleSprites.slots[i];lcd.objects[i]={s.x,s.present?s.y:0};}
                    AirPauseGraphics graphics;graphics.row=game->hudMap;graphics.font=pauseAssets.restoreFont;
                    loopBoundarySafe=true;
                    airPauseSession(clock,sampled,graphics,pauseAssets,display,lcd,[&](bool value){paused=value;sound.setPaused(value);},
                        [&](const char* name,int64_t start,int64_t end,int work){pausePhases<<name<<','<<start<<','<<end<<','<<work<<'\n';},
                        [&](const char* name,const char* kind,unsigned address,int value,int64_t time){pauseBus<<name<<','<<kind<<','<<address<<','<<value<<','<<time<<'\n';},
                        [&](const char* name,int64_t time,const AirPauseGraphics& state){pauseStorage<<name<<','<<time;for(int value:state.row)pauseStorage<<','<<value;for(int value:state.font)pauseStorage<<','<<value;pauseStorage<<'\n';});
                    loopBoundarySafe=false;placementRange.low=0;
                    if(graphics.row!=game->hudMap)throw std::runtime_error("Pause did not restore the native HUD row");
                }
            }else clock.work(48,display,false);
            if(entityLog.is_open())for(int slot=0;slot<16;++slot){const auto& e=game->entities[slot];
                entityLog<<updates<<','<<slot<<','<<(e.alive?e.frame:255)<<','<<((e.flags&~2)|(e.offscreen?2:0))<<','<<e.x<<','<<e.y<<'\n';
            }
            int buttons=decode(displayInputs.is_open()?sampled.held:held);
            if(displayInputs.is_open())game->previous=decode(sampled.previous);
            bool priorMap=game->mapTransfer;
            int priorMapCamera=game->lastMapCamera;
            auto priorSprites=game->sprites.slots;
            game->updateGame(buttons,true,true);
            game->sprites.slots=priorSprites;
            bool preparedMap=game->mapTransfer;
            game->mapTransfer=priorMap;
            mapBoundarySafe=!priorMap&&!preparedMap;
            mapRowReady=!preparedMap;
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
                }else if(activeGamePhase==1){
                    int charged=0;for(int cost:game->resourceCompletionCosts){charged+=cost;clock.atomicWork(cost,[]{},display,false);}
                    if(charged!=work)throw std::runtime_error("Resource completion work disagrees with native queue: "+std::to_string(charged)+" vs "+std::to_string(work));
                }else if(activeGamePhase==2){
                    int sum=112;
                    for(int n:game->spriteEntityWorkCycles)sum+=n;
                    if(sum!=work)throw std::runtime_error("Incomplete per-entity sprite work");
                    game->sprites=SpriteLayer(game->reverseSprites);game->sprites.slots=priorSprites;
                    spriteBoundarySafe=true;
                    auto preparation=std::make_unique<AirGame>(*game);
                    preparation->entities=game->spriteInputEntities;
                    // airSpriteWork chooses the next allocation direction.
                    preparation->reverseSprites=!game->reverseSprites;
                    std::array<AirSpriteEntityWork,16> publication{};
                    auto planned=airSpriteWork(*preparation,nullptr,&publication);
                    if(planned.prepare!=work)throw std::runtime_error("Sprite publication work disagrees with preparation");
                    int charged=airSpriteClock(*game,clock,display);
                    if(charged!=work)throw std::runtime_error("Sprite completion work disagrees with native preparation: "+std::to_string(charged)+" vs "+std::to_string(work));
                    // The replay accounts for geometry/culling in updateGame;
                    // publication uses this independently rebuilt partial list.
                }else if(activeGamePhase==3){
                    int charged=airSpriteClearClock(game->sprites,clock,display);
                    if(charged!=work)throw std::runtime_error("Sprite clear completion disagrees with native work");
                }else if(activeGamePhase==4){
                    int charged=airMapClock(clock,priorMapCamera,game->cameraY,game->mapTransfer,display,&mapBoundarySafe,&mapRowReady);
                    if(charged!=work||game->mapTransfer!=preparedMap)throw std::runtime_error("Map completion work disagrees with native preparation: "+std::to_string(charged)+" vs "+std::to_string(work));
                }else clock.work(work,display,false);
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
            clock.atomicWork(16,[]{},display,false);
            clock.atomicWork(4,[]{},display,false);
            clock.atomicWork(game->result?8:12,[]{},display,false);
            loopBoundarySafe=false;
        }
        if(!pauseEntryPath.empty()&&!pauseEntryReached)throw std::runtime_error("Native prefix did not reach a fresh Start request");
        if(pauseReplay&&!pauses)throw std::runtime_error("Native replay did not reach a pause");
        if(!pauseEntryReached&&!input.eof())return 2;
        if(finalWait){
            activeGamePhase=-1;currentUpdate=-1;
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
            projectionPalette=bgp;
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
                phase("palette",segment,76,[&]{
                    auto start=clock.now;
                    clock.work(76,display,false);bgp=ui->fadePalettes[segment];obp0=bgp&0xcf;obp1=bgp&0xf3;projectionPalette=bgp;
                    if(selectedProjection&&projectedPalette!=bgp){
                        if(clock.now-start!=76)throw std::runtime_error("Unowned interrupted palette projection");
                        // The three identified palette writes have separate
                        // bus samples: BGP +16, OBP1 +36, OBP0 +64. Observer
                        // sampling is two cycles ahead of completion owners.
                        for(int y=0;y<Height;++y)for(int x=0;x<Width;++x){int i=y*Width+x;
                            int64_t pixelTime=projectedLineZero+456*y+airPixelDot(projectedSprites,projectedScroll,y,x);
                            if(start+airPaletteSampleOffset(projectedOwners[i])<pixelTime)projectedPalettes[i]=bgp;
                        }
                        projectedPalette=bgp;writeProjection();
                    }
                });
                for(int wait=0;wait<4;++wait){
                    phase("wait",4*segment+wait,-1,[&]{clock.wait(display,false);});
                    int tail=wait<3?16:segment<7?28:40;
                    phase("tail",4*segment+wait,tail,[&]{clock.work(tail,display,false);});
                }
            }
            loopBoundarySafe=false;
            // 0409 starts DI/setup. Optional separate result owners follow;
            // the ordinary gameplay IRQ interval still terminates here.
        }
        std::ofstream boundary(std::string(argv[2])+".boundary.csv");
        if(!boundary)throw std::runtime_error("Cannot open native replay completion boundary");
        boundary<<"boundary,cycle,updates,result\n"<<(outroFade?"resultSetup":pauseEntryReached?"pauseEntry":game->result?"gameExitTest":"partialUpdates")
                <<','<<clock.now<<','<<updates<<','<<game->result<<'\n';
        if(resultPrefix){
            std::ofstream points(std::string(argv[2])+".result.csv"),polls(std::string(argv[2])+".result.polls.csv");
            if(!points||!polls)throw std::runtime_error("Cannot open result-prefix boundaries");
            points<<"boundary,cycle\n";polls<<"cycle,ly\n";
            auto prefix=airResultSetupPrefix(clock,game->result,[&](const char* name,int64_t cycle){points<<name<<','<<cycle<<'\n';},
                [&](int64_t cycle,int line){polls<<cycle<<','<<line<<'\n';});
            std::ofstream summary(std::string(argv[2])+".result.summary.csv");
            summary<<"end,lcdDisabled,pollReads,pendingRequests\n"<<prefix.end<<','<<prefix.lcdDisabled<<','<<prefix.pollReads<<','<<prefix.pendingRequests<<'\n';
            if(resultIncoming){
                auto layouts=AirResultLayoutAssets::load("build/result-timing.dat");auto ui=std::make_unique<UiAssets>(UiAssets::load(L"build/ui.dat"));
                std::ofstream resultPoints(std::string(argv[2])+".incoming.csv"),resultServices(std::string(argv[2])+".incoming.services.csv"),resultIrqs(std::string(argv[2])+".incoming.interrupts.csv");
                if(!resultPoints||!resultServices||!resultIrqs)throw std::runtime_error("Cannot open result incoming outputs");
                resultPoints<<"boundary,cycle,tick,countdown,bgp,obp0,obp1,musicEnabled\n";
                resultServices<<"service,cycle,tick,countdown,display,effects,music,musicEnabled,inputHeld\n";
                resultIrqs<<"kind,vectorCycle,owner\n";
                // These standalone controls begin with the native campaign's
                // five lives. Final-life and reset ownership explicitly reject.
                auto point=[&](const char* name,int64_t cycle,int tick,int countdown,int bgp,int obp0,int obp1,bool enabled){resultPoints<<name<<','<<cycle<<','<<tick<<','<<countdown<<','<<bgp<<','<<obp0<<','<<obp1<<','<<enabled<<'\n';};
                auto resultDisplay=[&](unsigned service,int64_t cycle,int tick,int countdown,int display,int effects,int music,bool enabled){sampled.sample(sampled.held);resultServices<<service<<','<<cycle<<','<<tick<<','<<countdown<<','<<display<<','<<effects<<','<<music<<','<<enabled<<','<<sampled.held<<'\n';};
                auto resultIrq=[&](const char* kind,int64_t cycle,AirIrqOwner owner){resultIrqs<<kind<<','<<cycle<<','<<int(owner)<<'\n';};
                auto incoming=airResultIncoming(prefix,game->result,game->ticks,5,sampled.held,sound,layouts,*ui,point,resultDisplay,resultIrq);
                if(resultHold)incoming=airResultFailureHold(incoming,game->result,sampled.held,sound,*ui,point,resultDisplay,resultIrq);
                std::ofstream resultSummary(std::string(argv[2])+".incoming.summary.csv");
                resultSummary<<"end,lcdEpoch,tick,countdown,displays,stats\n"<<incoming.end<<','<<incoming.lcdEpoch<<','<<incoming.tick<<','<<incoming.countdown<<','<<incoming.displays<<','<<incoming.stats<<'\n';
            }
        }
        if(!frameServices.empty()&&*frameServices.rbegin()>=clock.displays)throw std::runtime_error("Selected native frame services exceed replay coverage");
        fprintf(stderr,"Completed %d ordinary-clock updates, %u display services, %u STAT services; %s buttons.\n",updates,clock.displays,clock.statServices,displayInputs.is_open()?"display-sampled":"update-aligned");
        return 0;
    }catch(const std::exception& e){fprintf(stderr,"%s\n",e.what());return 1;}
}
