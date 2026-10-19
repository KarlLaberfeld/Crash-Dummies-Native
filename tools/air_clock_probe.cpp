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
#include "air_result_accounting.h"
#include "air_result_handoff.h"
#include "air_instruction_header.h"
#include "air_instruction_picture.h"
#include "air_instruction_map.h"
#include "air_instruction_text.h"
#include "air_instruction_exit.h"
#include "air_following_setup.h"
#include "air_following_gameplay.h"
#include "air_following_pause.h"
#include "air_next_instruction_probe.h"
#include "air_next_retry_probe.h"
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
static void celebrationHeader(std::ostream& out,bool publication=false){
    out<<"service,tick,work,random,spriteCount";
    for(int i=0;i<4;++i)for(const char* field:{"x","y","velocity","radius","delay"})out<<",emitter"<<i<<field;
    for(int i=0;i<160;++i)out<<",prepared"<<i;
    if(publication)for(int i=0;i<160;++i)out<<",visible"<<i;
    out<<'\n';
}
static void celebrationRow(std::ostream& out,unsigned service,int tick,const AirCelebration& state,int work,
    const std::array<unsigned char,160>* visible=nullptr){
    out<<service<<','<<tick<<','<<work<<','<<state.randomState<<','<<state.spriteCount;
    for(const auto& e:state.emitters)out<<','<<e.x<<','<<e.y<<','<<e.velocity<<','<<e.radius<<','<<e.delay;
    for(auto byte:state.prepared)out<<','<<int(byte);
    if(visible)for(auto byte:*visible)out<<','<<int(byte);
    out<<'\n';
}
int main(int argc,char** argv){
    if(argc<3){fprintf(stderr,"Usage: air-clock-probe inputs.txt services.csv [difficulty [sprites.csv]] [--entities-csv entities.csv] [--map-csv map.csv] [--audio-csv voices.csv] [--interrupts-csv interrupts.csv] [--display-inputs buttons.txt] [--result-inputs result-buttons.txt] [--pause-entry graphics.json | --pause-replay] [--final-wait | --outro-fade | --result-prefix | --perfect-celebration services | --result-incoming | --result-failure-hold | --result-accounting | --result-handoff | --instruction-header | --instruction-picture | --instruction-map | --instruction-text | --instruction-exit | --following-setup-prefix | --following-stage-setup | --following-entry | --following-gameplay | --following-entry-pause]\n");return 2;}
    try{
        int nextInstructionExtent=0,nextUpdates=1,thirdInstructionExtent=0,fourthUpdates=1,fifthInstructionExtent=0,fifthUpdates=1;bool nextRetry=false,nextTerminal=false,nextResult=false,fourthEntry=false,fourthResult=false,fifthEntry=false,fifthTerminal=false;
        bool instructionExit=false,followingSetupPrefix=false,followingStageSetup=false,followingEntry=false,followingGameplay=false,followingEntryPause=false,followingPauseReached=false,followingTerminal=false,followingOutro=false,followingResult=false,followingResultHold=false;
        int difficulty=1,positional=0,celebrationServices=0,followingUpdates=1;std::string spritePath,displayInputPath,resultInputPath,mapPath,entityPath,pauseEntryPath,audioPath,framesPath,frameSelection,interruptPath;bool finalWait=false,outroFade=false,resultPrefix=false,resultIncoming=false,resultHold=false,resultAccounting=false,resultHandoff=false,instructionHeader=false,instructionPicture=false,instructionMap=false,instructionText=false,pauseEntryReached=false,pauseReplay=false,paused=false;
        for(int i=3;i<argc;++i){std::string option=argv[i];
            if(option=="--display-inputs"&&i+1<argc)displayInputPath=argv[++i];
            else if(option=="--perfect-celebration"&&i+1<argc){celebrationServices=std::stoi(argv[++i]);
                if(celebrationServices<1||celebrationServices>2000)throw std::runtime_error("Invalid perfect celebration extent");resultPrefix=outroFade=finalWait=true;}
            else if(option=="--result-inputs"&&i+1<argc)resultInputPath=argv[++i];
            else if(option=="--result-prefix"){resultPrefix=true;outroFade=true;finalWait=true;}
            else if(option=="--result-incoming"){resultIncoming=true;resultPrefix=true;outroFade=true;finalWait=true;}
            else if(option=="--result-failure-hold"){resultHold=true;resultIncoming=true;resultPrefix=true;outroFade=true;finalWait=true;}
            else if(option=="--result-accounting"){resultAccounting=true;resultIncoming=true;resultPrefix=true;outroFade=true;finalWait=true;}
            else if(option=="--result-handoff"){resultHandoff=true;resultIncoming=true;resultPrefix=true;outroFade=true;finalWait=true;}
            else if(option=="--instruction-header"){instructionHeader=resultHandoff=resultIncoming=resultPrefix=outroFade=finalWait=true;}
            else if(option=="--instruction-picture"){instructionPicture=instructionHeader=resultHandoff=resultIncoming=resultPrefix=outroFade=finalWait=true;}
            else if(option=="--instruction-map"){instructionMap=instructionPicture=instructionHeader=resultHandoff=resultIncoming=resultPrefix=outroFade=finalWait=true;}
            else if(option=="--instruction-text"){instructionText=instructionMap=instructionPicture=instructionHeader=resultHandoff=resultIncoming=resultPrefix=outroFade=finalWait=true;}
            else if(option=="--instruction-exit"){instructionExit=instructionText=instructionMap=instructionPicture=instructionHeader=resultHandoff=resultIncoming=resultPrefix=outroFade=finalWait=true;}
            else if(option=="--following-setup-prefix"){followingSetupPrefix=instructionExit=instructionText=instructionMap=instructionPicture=instructionHeader=resultHandoff=resultIncoming=resultPrefix=outroFade=finalWait=true;}
            else if(option=="--following-stage-setup"){followingStageSetup=followingSetupPrefix=instructionExit=instructionText=instructionMap=instructionPicture=instructionHeader=resultHandoff=resultIncoming=resultPrefix=outroFade=finalWait=true;}
            else if(option=="--following-entry"){followingEntry=followingStageSetup=followingSetupPrefix=instructionExit=instructionText=instructionMap=instructionPicture=instructionHeader=resultHandoff=resultIncoming=resultPrefix=outroFade=finalWait=true;}
            else if(option=="--following-gameplay"){followingGameplay=followingEntry=followingStageSetup=followingSetupPrefix=instructionExit=instructionText=instructionMap=instructionPicture=instructionHeader=resultHandoff=resultIncoming=resultPrefix=outroFade=finalWait=true;}
            else if(option=="--following-updates"&&i+1<argc){followingUpdates=std::stoi(argv[++i]);if(followingUpdates<1||followingUpdates>100000)throw std::runtime_error("Invalid following Air update extent");}
            else if(option=="--following-terminal"){followingTerminal=true;}
            else if(option=="--following-outro"){followingOutro=followingTerminal=true;}
            else if(option=="--following-result"){followingResult=followingOutro=followingTerminal=true;}
            else if(option=="--following-result-hold"){followingResultHold=followingResult=followingOutro=followingTerminal=true;}
            else if(option=="--next-instruction"&&i+1<argc){nextInstructionExtent=std::stoi(argv[++i]);if(nextInstructionExtent<1||nextInstructionExtent>5)throw std::runtime_error("Invalid next instruction extent");followingResultHold=followingResult=followingOutro=followingTerminal=true;}
            else if(option=="--next-retry"){nextRetry=true;nextInstructionExtent=5;followingResultHold=followingResult=followingOutro=followingTerminal=true;}
            else if(option=="--next-updates"&&i+1<argc){nextUpdates=std::stoi(argv[++i]);if(nextUpdates<1||nextUpdates>100000)throw std::runtime_error("Invalid second-retry update extent");}
            else if(option=="--next-terminal")nextTerminal=true;
            else if(option=="--next-result")nextResult=nextTerminal=true;
            else if(option=="--fourth-entry"){fourthEntry=true;thirdInstructionExtent=5;nextResult=nextTerminal=true;}
            else if(option=="--fourth-result"){fourthResult=fourthEntry=true;thirdInstructionExtent=5;nextResult=nextTerminal=true;}
            else if(option=="--fifth-instruction"&&i+1<argc){fifthInstructionExtent=std::stoi(argv[++i]);if(fifthInstructionExtent<1||fifthInstructionExtent>5)throw std::runtime_error("Invalid fifth instruction extent");fourthResult=fourthEntry=true;thirdInstructionExtent=5;nextResult=nextTerminal=true;}
            else if(option=="--fifth-entry"){fifthEntry=true;fifthInstructionExtent=5;fourthResult=fourthEntry=true;thirdInstructionExtent=5;nextResult=nextTerminal=true;}
            else if(option=="--fifth-updates"&&i+1<argc){fifthUpdates=std::stoi(argv[++i]);if(fifthUpdates<1||fifthUpdates>100000)throw std::runtime_error("Invalid fifth Air update extent");}
            else if(option=="--fifth-terminal")fifthTerminal=true;
            else if(option=="--fourth-updates"&&i+1<argc){fourthUpdates=std::stoi(argv[++i]);if(fourthUpdates<1||fourthUpdates>100000)throw std::runtime_error("Invalid fourth Air update extent");}
            else if(option=="--third-instruction"&&i+1<argc){thirdInstructionExtent=std::stoi(argv[++i]);if(thirdInstructionExtent<1||thirdInstructionExtent>5)throw std::runtime_error("Invalid third-result instruction extent");nextResult=nextTerminal=true;}
            else if(option=="--following-entry-pause"){followingEntryPause=followingEntry=followingStageSetup=followingSetupPrefix=instructionExit=instructionText=instructionMap=instructionPicture=instructionHeader=resultHandoff=resultIncoming=resultPrefix=outroFade=finalWait=true;}
            else if(option=="--entities-csv"&&i+1<argc)entityPath=argv[++i];
            else if(option=="--map-csv"&&i+1<argc)mapPath=argv[++i];
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
        if(celebrationServices<0||celebrationServices>2000||(celebrationServices&&resultIncoming))throw std::runtime_error("Invalid isolated perfect celebration scope");
        if(pauseReplay&&(displayInputPath.empty()||!pauseEntryPath.empty()))throw std::runtime_error("Pause replay requires display inputs and cannot stop at pause entry");
        if(framesPath.empty()!=frameSelection.empty())throw std::runtime_error("Frame output requires a directory and selected services");
        if(!resultInputPath.empty()&&!resultIncoming)throw std::runtime_error("Result input requires incoming/accounting ownership");
        if(followingUpdates!=1&&!followingGameplay)throw std::runtime_error("Following update extent requires gameplay ownership");
        if(followingTerminal&&!followingGameplay)throw std::runtime_error("Following terminal wait requires gameplay ownership");
        if(nextUpdates!=1&&!nextRetry)throw std::runtime_error("Second-retry extent requires --next-retry");
        if(fourthUpdates!=1&&!fourthEntry)throw std::runtime_error("Fourth gameplay extent requires --fourth-entry");
        if(fifthEntry&&fifthInstructionExtent!=5)throw std::runtime_error("Fifth entry requires complete instruction ownership");
        if((fifthUpdates!=1||fifthTerminal)&&!fifthEntry)throw std::runtime_error("Fifth gameplay extent requires --fifth-entry");
        if(nextTerminal&&!nextRetry)throw std::runtime_error("Second-retry terminal requires --next-retry");
        if(nextRetry&&nextInstructionExtent!=5)throw std::runtime_error("Second retry requires complete next instruction");
        if(!mapPath.empty()&&!outroFade)throw std::runtime_error("Complete map comparison requires the outgoing result boundary");
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
        AirMapPublication mapPublication;mapPublication.initialize(*game);
        std::ofstream mapLog;
        if(!mapPath.empty()){mapLog.open(mapPath);if(!mapLog)throw std::runtime_error("Cannot open native map publication output");
            mapLog<<"boundary,service,cycle,pending,row";for(int i=0;i<32;++i)mapLog<<",buffer"<<i;for(int i=0;i<1024;++i)mapLog<<",tile"<<i;mapLog<<'\n';}
        auto mapSnapshot=[&](const char* boundary,int64_t time){if(!mapLog.is_open())return;mapLog<<boundary<<','<<clock.displays<<','<<time<<','<<game->mapTransfer<<','<<mapPublication.destination;
            for(int v:mapPublication.buffer)mapLog<<','<<v;for(int v:mapPublication.tiles)mapLog<<','<<v;mapLog<<'\n';};
        mapSnapshot("startup",clock.now);
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
            }else{
                int64_t mapEntry=clock.now+20+180+704+280+116;
                mapSnapshot("before",mapEntry);if(game->mapTransfer)mapPublication.publish();mapSnapshot("after",mapEntry+24+(game->mapTransfer?736:40));
                game->displayTick(ready);
            }
            // 2f4c/16eb divides 48 * the byte-sized collected count. Its
            // overflow scratch FF9C ends at zero and can change later range
            // reads in an interrupted 19a2 scan. FF9E is not changed here.
            if(refreshRangeScratch)placementRange.low=0;
            if(pending>=0)sound.queueEffect(pending);
            game->pendingSound=-1;sound.tick();
            selectedProjection=frameServices.count(clock.displays);
            if(selectedProjection){
                mapPublication.render(*game,&projectedOwners);projectedScene=paused?renderPausedGame(*frameUi,game->screen):game->screen;
                if(paused)std::fill(projectedOwners.begin()+PlayHeight*Width,projectedOwners.end(),0);
                projectedSprites=game->visibleSprites;projectedScroll=(game->visibleCameraX>>4)&255;
                for(int x=0;x<Width;++x)projectedBackground[x]=mapPublication.pixel(*game,x,135);
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
                    int charged=airMapClock(clock,priorMapCamera,game->cameraY,game->mapTransfer,display,&mapBoundarySafe,&mapRowReady,&mapPublication,game.get());
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
        if(!mapPath.empty())mapSnapshot("end",clock.now);
        if(!boundary)throw std::runtime_error("Cannot open native replay completion boundary");
        boundary<<"boundary,cycle,updates,result\n"<<(outroFade?"resultSetup":pauseEntryReached?"pauseEntry":game->result?"gameExitTest":"partialUpdates")
                <<','<<clock.now<<','<<updates<<','<<game->result<<'\n';
        if(resultPrefix){
            std::ofstream points(std::string(argv[2])+".result.csv"),polls(std::string(argv[2])+".result.polls.csv");
            if(!points||!polls)throw std::runtime_error("Cannot open result-prefix boundaries");
            points<<"boundary,cycle\n";polls<<"cycle,ly\n";
            auto prefix=airResultSetupPrefix(clock,game->result,[&](const char* name,int64_t cycle){points<<name<<','<<cycle<<'\n';},
                [&](int64_t cycle,int line){polls<<cycle<<','<<line<<'\n';},game->randomState);
            std::ofstream summary(std::string(argv[2])+".result.summary.csv");
            summary<<"end,lcdDisabled,pollReads,pendingRequests,display,stat,countdown,random";
            for(int i=0;i<4;++i)for(const char* field:{"x","y","velocity","radius","delay"})summary<<",emitter"<<i<<field;
            summary<<'\n'<<prefix.end<<','<<prefix.lcdDisabled<<','<<prefix.pollReads<<','<<prefix.pendingRequests<<','<<prefix.display<<','<<prefix.stat<<','<<prefix.countdown<<','<<prefix.celebration.randomState;
            for(const auto& emitter:prefix.celebration.emitters)summary<<','<<emitter.x<<','<<emitter.y<<','<<emitter.velocity<<','<<emitter.radius<<','<<emitter.delay;
            summary<<'\n';
            if(celebrationServices){
                if(game->result!=7)throw std::runtime_error("Perfect celebration replay requires native perfect gameplay");
                auto ui=std::make_unique<UiAssets>(UiAssets::load(L"build/ui.dat"));auto celebration=prefix.celebration;
                std::ofstream frames(std::string(argv[2])+".celebration.csv");if(!frames)throw std::runtime_error("Cannot open native celebration component output");
                celebrationHeader(frames);
                int tick=game->ticks;
                for(int i=0;i<celebrationServices;++i){int work=celebration.advance(tick,*ui);
                    celebrationRow(frames,i,tick,celebration,work);tick=(tick+1)&65535;
                }
            }
            if(resultIncoming){
                auto layouts=AirResultLayoutAssets::load("build/result-timing.dat");auto ui=std::make_unique<UiAssets>(UiAssets::load(L"build/ui.dat"));
                std::ofstream resultPoints(std::string(argv[2])+".incoming.csv"),resultServices(std::string(argv[2])+".incoming.services.csv"),resultIrqs(std::string(argv[2])+".incoming.interrupts.csv");
                if(!resultPoints||!resultServices||!resultIrqs)throw std::runtime_error("Cannot open result incoming outputs");
                resultPoints<<"boundary,cycle,tick,countdown,bgp,obp0,obp1,musicEnabled,inputHeld,inputPressed\n";
                resultServices<<"service,cycle,tick,countdown,display,effects,music,musicEnabled,inputHeld,inputPressed\n";
                resultIrqs<<"kind,vectorCycle,owner\n";
                // These standalone controls begin with the native campaign's
                // five lives. Final-life and reset ownership explicitly reject.
                auto point=[&](const char* name,int64_t cycle,int tick,int countdown,int bgp,int obp0,int obp1,bool enabled){resultPoints<<name<<','<<cycle<<','<<tick<<','<<countdown<<','<<bgp<<','<<obp0<<','<<obp1<<','<<enabled<<','<<sampled.held<<','<<sampled.pressed<<'\n';};
                std::ifstream resultInputs;if(!resultInputPath.empty()){resultInputs.open(resultInputPath);if(!resultInputs)throw std::runtime_error("Cannot open result button samples");}
                auto nextResultInput=[&]{int held=sampled.held;
                    if(resultInputs.is_open()&&(!(resultInputs>>held)||held<0||held>255))throw std::runtime_error("Missing/invalid result button sample");
                    sampled.sample(held);return held;};
                auto resultDisplay=[&](unsigned service,int64_t cycle,int tick,int countdown,int display,int effects,int music,bool enabled){resultServices<<service<<','<<cycle<<','<<tick<<','<<countdown<<','<<display<<','<<effects<<','<<music<<','<<enabled<<','<<sampled.held<<','<<sampled.pressed<<'\n';};
                auto resultIrq=[&](const char* kind,int64_t cycle,AirIrqOwner owner){resultIrqs<<kind<<','<<cycle<<','<<int(owner)<<'\n';};
                std::ofstream celebrationFrames;
                if(game->result&4){celebrationFrames.open(std::string(argv[2])+".incoming.celebration.csv");
                    if(!celebrationFrames)throw std::runtime_error("Cannot open incoming celebration output");celebrationHeader(celebrationFrames,true);}
                auto incoming=airResultIncoming(prefix,game->result,game->ticks,5,sampled.held,sound,layouts,*ui,point,resultDisplay,resultIrq,nextResultInput,
                    [&](unsigned service,int tick,const AirCelebration& state,const std::array<unsigned char,160>& visible,int work){celebrationRow(celebrationFrames,service,tick,state,work,&visible);});
                if(resultHold||(resultHandoff&&!(game->result&2)))incoming=airResultFailureHold(incoming,game->result,sampled.held,sound,*ui,point,resultDisplay,resultIrq,nextResultInput);
                std::ofstream resultSummary(std::string(argv[2])+".incoming.summary.csv");
                resultSummary<<"end,lcdEpoch,tick,countdown,displays,stats\n"<<incoming.end<<','<<incoming.lcdEpoch<<','<<incoming.tick<<','<<incoming.countdown<<','<<incoming.displays<<','<<incoming.stats<<'\n';
                auto handoffTiming=incoming;
                int nextStage=1;
                if(resultAccounting||(resultHandoff&&(game->result&2))){
                    auto texts=AirResultTextAssets::load("build/result-layouts.dat");
                    std::ofstream accountPoints(std::string(argv[2])+".account.csv"),accountServices(std::string(argv[2])+".account.services.csv"),accountIrqs(std::string(argv[2])+".account.interrupts.csv"),accountPolls(std::string(argv[2])+".account.polls.csv"),accountWrites(std::string(argv[2])+".account.writes.csv");
                    if(!accountPoints||!accountServices||!accountIrqs||!accountPolls||!accountWrites)throw std::runtime_error("Cannot open result accounting outputs");
                    accountPoints<<"boundary,cycle,tick,countdown,pay,savings,seconds,stage,musicEnabled,skip,inputHeld,inputPressed\n";
                    accountServices<<"service,cycle,tick,countdown,display,effects,music,musicEnabled,inputHeld,inputPressed\n";
                    accountIrqs<<"kind,vectorCycle,owner\n";accountPolls<<"cycle,mode\n";accountWrites<<"cycle,address,value\n";
                    std::ofstream accountCelebration;
                    if(game->result&4){accountCelebration.open(std::string(argv[2])+".account.celebration.csv");
                        if(!accountCelebration)throw std::runtime_error("Cannot open accounting celebration output");celebrationHeader(accountCelebration,true);}
                    auto account=airResultAccount(incoming,game->result,sampled.held,game->money,0,game->seconds,sound,texts,
                        [&](const char* name,int64_t cycle,int tick,int countdown,int pay,int savings,int seconds,int stage,bool enabled,int skip){accountPoints<<name<<','<<cycle<<','<<tick<<','<<countdown<<','<<pay<<','<<savings<<','<<seconds<<','<<stage<<','<<enabled<<','<<skip<<','<<sampled.held<<','<<sampled.pressed<<'\n';},
                        [&](unsigned service,int64_t cycle,int tick,int countdown,int display,int effects,int music,bool enabled){accountServices<<service<<','<<cycle<<','<<tick<<','<<countdown<<','<<display<<','<<effects<<','<<music<<','<<enabled<<','<<sampled.held<<','<<sampled.pressed<<'\n';},
                        [&](const char* kind,int64_t cycle,AirIrqOwner owner){accountIrqs<<kind<<','<<cycle<<','<<int(owner)<<'\n';},
                        [&](int64_t cycle,int mode){accountPolls<<cycle<<','<<mode<<'\n';},
                        [&](int64_t cycle,int address,int value){accountWrites<<cycle<<','<<address<<','<<value<<'\n';},nextResultInput,ui.get(),
                        [&](unsigned service,int tick,const AirCelebration& state,const std::array<unsigned char,160>& visible,int work){celebrationRow(accountCelebration,service,tick,state,work,&visible);});
                    std::ofstream accountSummary(std::string(argv[2])+".account.summary.csv");accountSummary<<"end,tick,countdown,displays,stats,pay,savings,seconds,stage\n"<<account.timing.end<<','<<account.timing.tick<<','<<account.timing.countdown<<','<<account.timing.displays<<','<<account.timing.stats<<','<<account.pay<<','<<account.savings<<','<<account.seconds<<','<<account.stage<<'\n';
                    handoffTiming=account.timing;
                    nextStage=account.stage;
                }
                if(resultHandoff){
                    std::ofstream handPoints(std::string(argv[2])+".handoff.csv"),handServices(std::string(argv[2])+".handoff.services.csv"),handIrqs(std::string(argv[2])+".handoff.interrupts.csv"),handPolls(std::string(argv[2])+".handoff.polls.csv"),handWrites(std::string(argv[2])+".handoff.writes.csv");
                    if(!handPoints||!handServices||!handIrqs||!handPolls||!handWrites)throw std::runtime_error("Cannot open result handoff outputs");
                    handPoints<<"boundary,cycle,tick,countdown,player,lives0,lives1,result,inputHeld,inputPressed\n";
                    handServices<<"service,cycle,tick,countdown,display,effects,music,inputHeld,inputPressed\n";
                    handIrqs<<"kind,vectorCycle,owner\n";handPolls<<"cycle,mode\n";handWrites<<"cycle,address,value\n";
                    std::ofstream handCelebration;
                    if(game->result&4){handCelebration.open(std::string(argv[2])+".handoff.celebration.csv");
                        if(!handCelebration)throw std::runtime_error("Cannot open handoff celebration output");celebrationHeader(handCelebration,true);}
                    // Native initial solo campaign: five lives, then the failure
                    // result consumes one. No recorded player/life state enters.
                    auto handoff=airResultHandoff(handoffTiming,0,{(game->result&2)?5:4,0},game->result,sound,
                        [&](const char* name,int64_t cycle,int tick,int countdown,int player,int lives0,int lives1,int result,const DisplayInput& input){handPoints<<name<<','<<cycle<<','<<tick<<','<<countdown<<','<<player<<','<<lives0<<','<<lives1<<','<<result<<','<<input.held<<','<<input.pressed<<'\n';},
                        [&](unsigned service,int64_t cycle,int tick,int countdown,int display,int effects,int music,const DisplayInput& input){handServices<<service<<','<<cycle<<','<<tick<<','<<countdown<<','<<display<<','<<effects<<','<<music<<','<<input.held<<','<<input.pressed<<'\n';},
                        [&](const char* kind,int64_t cycle,AirIrqOwner owner){handIrqs<<kind<<','<<cycle<<','<<int(owner)<<'\n';},
                        [&](int64_t cycle,int mode){handPolls<<cycle<<','<<mode<<'\n';},
                        [&](int64_t cycle,int address,int value){handWrites<<cycle<<','<<address<<','<<value<<'\n';},nextResultInput,ui.get(),
                        [&](unsigned service,int tick,const AirCelebration& state,const std::array<unsigned char,160>& visible,int work){celebrationRow(handCelebration,service,tick,state,work,&visible);});
                    std::ofstream handSummary(std::string(argv[2])+".handoff.summary.csv");
                    handSummary<<"end,tick,countdown,displays,stats,player,lives0,lives1,result\n"<<handoff.timing.end<<','<<handoff.timing.tick<<','<<handoff.timing.countdown<<','<<handoff.timing.displays<<','<<handoff.timing.stats<<','<<handoff.player<<','<<handoff.lives[0]<<','<<handoff.lives[1]<<','<<handoff.result<<'\n';
                    if(instructionHeader){
                        auto headers=AirInstructionHeaderAssets::load("build/instruction-header.dat");
                        std::ofstream points(std::string(argv[2])+".header.csv"),services(std::string(argv[2])+".header.services.csv"),
                            irqs(std::string(argv[2])+".header.interrupts.csv"),polls(std::string(argv[2])+".header.polls.csv"),writes(std::string(argv[2])+".header.writes.csv");
                        if(!points||!services||!irqs||!polls||!writes)throw std::runtime_error("Cannot open instruction header outputs");
                        points<<"boundary,cycle,tick,countdown,player,stage,difficulty,inputHeld,inputPressed\n";
                        services<<"service,cycle,tick,countdown,display,effects,music,inputHeld,inputPressed\n";
                        irqs<<"kind,vectorCycle,owner\n";polls<<"cycle,mode\n";writes<<"cycle,address,value\n";
                        auto header=airInstructionHeader(handoff,nextStage,difficulty,sound,headers,
                            [&](const char* name,int64_t cycle,int tick,int countdown,int player,int stage,int level,const DisplayInput& input){points<<name<<','<<cycle<<','<<tick<<','<<countdown<<','<<player<<','<<stage<<','<<level<<','<<input.held<<','<<input.pressed<<'\n';},
                            [&](unsigned index,int64_t cycle,int tick,int countdown,int display,int effects,int music,const DisplayInput& input){services<<index<<','<<cycle<<','<<tick<<','<<countdown<<','<<display<<','<<effects<<','<<music<<','<<input.held<<','<<input.pressed<<'\n';},
                            [&](const char* kind,int64_t cycle,AirIrqOwner owner){irqs<<kind<<','<<cycle<<','<<int(owner)<<'\n';},
                            [&](int64_t cycle,int mode){polls<<cycle<<','<<mode<<'\n';},
                            [&](int64_t cycle,int address,int value){writes<<cycle<<','<<address<<','<<value<<'\n';},nextResultInput);
                        std::ofstream summary(std::string(argv[2])+".header.summary.csv");summary<<"end,tick,countdown,displays,stats\n"<<header.timing.end<<','<<header.timing.tick<<','<<header.timing.countdown<<','<<header.timing.displays<<','<<header.timing.stats<<'\n';
                        if(instructionPicture){
                            std::ofstream points(std::string(argv[2])+".picture.csv"),services(std::string(argv[2])+".picture.services.csv"),
                                irqs(std::string(argv[2])+".picture.interrupts.csv"),polls(std::string(argv[2])+".picture.polls.csv"),writes(std::string(argv[2])+".picture.writes.csv");
                            if(!points||!services||!irqs||!polls||!writes)throw std::runtime_error("Cannot open instruction picture outputs");
                            points<<"boundary,cycle,tick,countdown,musicEnabled,inputHeld,inputPressed\n";
                            services<<"service,cycle,tick,countdown,display,effects,music,inputHeld,inputPressed\n";
                            irqs<<"kind,vectorCycle,owner\n";polls<<"cycle,mode\n";writes<<"kind,cycle,address,value\n";
                            auto picture=airInstructionPicture(header,nextStage,sound,*ui,
                                [&](const char* name,int64_t cycle,int tick,int countdown,bool enabled,const DisplayInput& input){points<<name<<','<<cycle<<','<<tick<<','<<countdown<<','<<enabled<<','<<input.held<<','<<input.pressed<<'\n';},
                                [&](unsigned index,int64_t cycle,int tick,int countdown,int display,int effects,int music,const DisplayInput& input){services<<index<<','<<cycle<<','<<tick<<','<<countdown<<','<<display<<','<<effects<<','<<music<<','<<input.held<<','<<input.pressed<<'\n';},
                                [&](const char* kind,int64_t cycle,AirIrqOwner owner){irqs<<kind<<','<<cycle<<','<<int(owner)<<'\n';},
                                [&](int64_t cycle,int mode){polls<<cycle<<','<<mode<<'\n';},
                                [&](const char* kind,int64_t cycle,int address,int value){writes<<kind<<','<<cycle<<','<<address<<','<<value<<'\n';},nextResultInput);
                            std::ofstream summary(std::string(argv[2])+".picture.summary.csv");summary<<"end,tick,countdown,displays,stats\n"<<picture.timing.end<<','<<picture.timing.tick<<','<<picture.timing.countdown<<','<<picture.timing.displays<<','<<picture.timing.stats<<'\n';
                            if(instructionMap){
                                std::ofstream points(std::string(argv[2])+".instruction-map.csv"),services(std::string(argv[2])+".instruction-map.services.csv"),
                                    irqs(std::string(argv[2])+".instruction-map.interrupts.csv"),polls(std::string(argv[2])+".instruction-map.polls.csv");
                                if(!points||!services||!irqs||!polls)throw std::runtime_error("Cannot open instruction map outputs");
                                points<<"boundary,cycle,tick,countdown,lcdc,lyc,scroll,alternate,display,stat,inputHeld,inputPressed\n";
                                services<<"service,cycle,tick,countdown,display,effects,music,inputHeld,inputPressed\n";
                                irqs<<"kind,vectorCycle,owner\n";polls<<"cycle,ly\n";
                                auto map=airInstructionMap(picture,sound,*ui,
                                    [&](const char* name,int64_t cycle,int tick,int countdown,const AirInstructionMapState& state,const DisplayInput& input){points<<name<<','<<cycle<<','<<tick<<','<<countdown<<','<<state.lcdc<<','<<state.lyc<<','<<state.scroll<<','<<state.alternate<<','<<state.display<<','<<state.stat<<','<<input.held<<','<<input.pressed<<'\n';},
                                    [&](unsigned index,int64_t cycle,int tick,int countdown,int display,int effects,int music,const DisplayInput& input){services<<index<<','<<cycle<<','<<tick<<','<<countdown<<','<<display<<','<<effects<<','<<music<<','<<input.held<<','<<input.pressed<<'\n';},
                                    [&](const char* kind,int64_t cycle,AirIrqOwner owner){irqs<<kind<<','<<cycle<<','<<int(owner)<<'\n';},
                                    [&](int64_t cycle,int ly){polls<<cycle<<','<<ly<<'\n';},nextResultInput);
                                std::ofstream summary(std::string(argv[2])+".instruction-map.summary.csv");summary<<"end,tick,countdown,displays,stats\n"<<map.campaign.timing.end<<','<<map.campaign.timing.tick<<','<<map.campaign.timing.countdown<<','<<map.campaign.timing.displays<<','<<map.campaign.timing.stats<<'\n';
                                if(instructionText){
                                    std::ofstream points(std::string(argv[2])+".text.csv"),services(std::string(argv[2])+".text.services.csv"),
                                        irqs(std::string(argv[2])+".text.interrupts.csv"),polls(std::string(argv[2])+".text.polls.csv"),writes(std::string(argv[2])+".text.writes.csv");
                                    if(!points||!services||!irqs||!polls||!writes)throw std::runtime_error("Cannot open timed instruction text outputs");
                                    points<<"boundary,cycle,tick,countdown,scroll,speed,delay,skipMask,layer,column,row,inputHeld,inputPressed,skipContext\n";
                                    services<<"service,cycle,tick,countdown,display,effects,music,inputHeld,inputPressed\n";
                                    irqs<<"kind,vectorCycle,owner\n";polls<<"cycle,mode\n";writes<<"cycle,address,value\n";
                                    auto text=airInstructionText(map,nextStage,difficulty,sound,*ui,
                                        [&](const char* name,int64_t cycle,int tick,int countdown,const AirInstructionTextState& state,const DisplayInput& input){points<<name<<','<<cycle<<','<<tick<<','<<countdown<<','<<state.map.scroll<<','<<state.speed<<','<<state.delay<<','<<state.skipMask<<",152,"<<state.anchor<<','<<state.row<<','<<input.held<<','<<input.pressed<<','<<state.skipContext<<'\n';},
                                        [&](unsigned index,int64_t cycle,int tick,int countdown,int display,int effects,int music,const DisplayInput& input){services<<index<<','<<cycle<<','<<tick<<','<<countdown<<','<<display<<','<<effects<<','<<music<<','<<input.held<<','<<input.pressed<<'\n';},
                                        [&](const char* kind,int64_t cycle,AirIrqOwner owner){irqs<<kind<<','<<cycle<<','<<int(owner)<<'\n';},
                                        [&](int64_t cycle,int mode){polls<<cycle<<','<<mode<<'\n';},
                                        [&](int64_t cycle,int address,int value){writes<<cycle<<','<<address<<','<<value<<'\n';},nextResultInput);
                                    std::ofstream summary(std::string(argv[2])+".text.summary.csv");summary<<"end,tick,countdown,displays,stats,scroll,skipped\n"<<text.map.campaign.timing.end<<','<<text.map.campaign.timing.tick<<','<<text.map.campaign.timing.countdown<<','<<text.map.campaign.timing.displays<<','<<text.map.campaign.timing.stats<<','<<text.map.scroll<<','<<text.skipped<<'\n';
                                    if(instructionExit){
                                        std::ofstream points(std::string(argv[2])+".instruction-exit.csv"),services(std::string(argv[2])+".instruction-exit.services.csv"),
                                            irqs(std::string(argv[2])+".instruction-exit.interrupts.csv"),polls(std::string(argv[2])+".instruction-exit.polls.csv"),writes(std::string(argv[2])+".instruction-exit.writes.csv");
                                        if(!points||!services||!irqs||!polls||!writes)throw std::runtime_error("Cannot open instruction exit outputs");
                                        points<<"boundary,cycle,tick,countdown,scroll,bgp,obp0,obp1,musicEnabled,inputHeld,inputPressed\n";
                                        services<<"service,cycle,tick,countdown,display,effects,music,inputHeld,inputPressed\n";
                                        irqs<<"kind,vectorCycle,owner\n";polls<<"cycle,mode\n";writes<<"cycle,address,value\n";
                                        auto exited=airInstructionExit(text,sound,*ui,
                                            [&](const char* name,int64_t cycle,int tick,int countdown,int scroll,int bgp,int obp0,int obp1,bool enabled,const DisplayInput& input){points<<name<<','<<cycle<<','<<tick<<','<<countdown<<','<<scroll<<','<<bgp<<','<<obp0<<','<<obp1<<','<<enabled<<','<<input.held<<','<<input.pressed<<'\n';},
                                            [&](unsigned index,int64_t cycle,int tick,int countdown,int display,int effects,int music,const DisplayInput& input){services<<index<<','<<cycle<<','<<tick<<','<<countdown<<','<<display<<','<<effects<<','<<music<<','<<input.held<<','<<input.pressed<<'\n';},
                                            [&](const char* kind,int64_t cycle,AirIrqOwner owner){irqs<<kind<<','<<cycle<<','<<int(owner)<<'\n';},
                                            [&](int64_t cycle,int mode){polls<<cycle<<','<<mode<<'\n';},
                                            [&](int64_t cycle,int address,int value){writes<<cycle<<','<<address<<','<<value<<'\n';},nextResultInput);
                                        std::ofstream summary(std::string(argv[2])+".instruction-exit.summary.csv");summary<<"end,tick,countdown,displays,stats\n"<<exited.map.campaign.timing.end<<','<<exited.map.campaign.timing.tick<<','<<exited.map.campaign.timing.countdown<<','<<exited.map.campaign.timing.displays<<','<<exited.map.campaign.timing.stats<<'\n';
                                        if(followingSetupPrefix){
                                            std::ofstream points(std::string(argv[2])+".following-prefix.csv"),polls(std::string(argv[2])+".following-prefix.polls.csv"),writes(std::string(argv[2])+".following-prefix.writes.csv");
                                            if(!points||!polls||!writes)throw std::runtime_error("Cannot open following setup prefix outputs");
                                            points<<"boundary,cycle,tick,countdown,player,stage,difficulty,lives,display,stat,lcdc,lyc,pendingRequests\n";
                                            polls<<"cycle,ly\n";writes<<"cycle,address,value\n";
                                            auto setup=airFollowingSetupPrefix(exited,nextStage,difficulty,sound,
                                                [&](const char* name,int64_t cycle,const AirFollowingSetup& state){const auto& campaign=state.instruction.map.campaign;points<<name<<','<<cycle<<','<<campaign.timing.tick<<','<<campaign.timing.countdown<<','<<campaign.player<<','<<state.stage<<','<<state.difficulty<<','<<campaign.lives[campaign.player]<<','<<state.display<<','<<state.stat<<','<<state.lcdc<<','<<state.lyc<<','<<state.pendingRequests<<'\n';},
                                                [&](int64_t cycle,int ly){polls<<cycle<<','<<ly<<'\n';},
                                                [&](int64_t cycle,int address,int value){writes<<cycle<<','<<address<<','<<value<<'\n';});
                                            std::ofstream summary(std::string(argv[2])+".following-prefix.summary.csv");summary<<"end,tick,countdown,displays,stats,pollReads,lcdDisabled,pendingRequests\n"<<setup.instruction.map.campaign.timing.end<<','<<setup.instruction.map.campaign.timing.tick<<','<<setup.instruction.map.campaign.timing.countdown<<','<<setup.instruction.map.campaign.timing.displays<<','<<setup.instruction.map.campaign.timing.stats<<','<<setup.pollReads<<','<<setup.lcdDisabled<<','<<setup.pendingRequests<<'\n';
                                            if(followingStageSetup){
                                                auto profiles=AirFollowingStageAssets::load("build/following-setup.dat");
                                                std::ofstream points(std::string(argv[2])+".following-stage.csv");
                                                if(!points)throw std::runtime_error("Cannot open following stage outputs");
                                                points<<"boundary,cycle,tick,countdown,player,stage,difficulty,lives,display,stat,lcdc,lyc,pendingRequests,cameraX,cameraY,mapScratch,ready,musicEnabled\n";
                                                auto stage=airFollowingStageSetup(setup,profiles.profiles[(nextStage-1)*4+difficulty],sound,
                                                    [&](const char* name,int64_t cycle,const AirFollowingSetup& state){const auto& c=state.instruction.map.campaign;points<<name<<','<<cycle<<','<<c.timing.tick<<','<<c.timing.countdown<<','<<c.player<<','<<state.stage<<','<<state.difficulty<<','<<c.lives[c.player]<<','<<state.display<<','<<state.stat<<','<<state.lcdc<<','<<state.lyc<<','<<state.pendingRequests<<','<<state.cameraX<<','<<state.cameraY<<','<<state.mapScratch<<','<<state.ready<<','<<sound.enabled<<'\n';});
                                                std::ofstream summary(std::string(argv[2])+".following-stage.summary.csv");const auto& t=stage.instruction.map.campaign.timing;
                                                summary<<"end,tick,countdown,displays,stats\n"<<t.end<<','<<t.tick<<','<<t.countdown<<','<<t.displays<<','<<t.stats<<'\n';
                                                if(followingEntry){
                                                    std::ofstream points(std::string(argv[2])+".following-entry.csv"),services(std::string(argv[2])+".following-entry.services.csv"),irqs(std::string(argv[2])+".following-entry.interrupts.csv");
                                                    if(!points||!services||!irqs)throw std::runtime_error("Cannot open following LCD entry outputs");
                                                    points<<"boundary,cycle,tick,countdown,display,stat,lcdc,lyc,pendingRequests,cameraX,cameraY,mapScratch,randomState,ready,musicEnabled,inputHeld,inputPressed\n";
                                                    services<<"service,cycle,tick,display,effects,music,inputHeld,inputPressed\n";irqs<<"kind,vectorCycle,owner\n";
                                                    std::ofstream pausePhases,pauseBus,pauseStorage;std::function<void(AirClock&,AirFollowingSetup&)> pauseOwner;
                                                    if(followingEntryPause){
                                                        pausePhases.open(std::string(argv[2])+".following-pause.phases.csv");pauseBus.open(std::string(argv[2])+".following-pause.bus.csv");pauseStorage.open(std::string(argv[2])+".following-pause.graphics.csv");
                                                        if(!pausePhases||!pauseBus||!pauseStorage)throw std::runtime_error("Cannot open following entry pause outputs");
                                                        pausePhases<<"phase,start,end,work\n";pauseBus<<"phase,kind,address,value,cycle\n";pauseStorage<<"phase,cycle";for(int i=0;i<20;++i)pauseStorage<<",status"<<i;for(int i=0;i<128;++i)pauseStorage<<",font"<<i;pauseStorage<<'\n';
                                                        pauseOwner=[&](AirClock& clock,AirFollowingSetup& state){auto assets=AirPauseAssets::load("build/pause.dat");
                                                            followingPauseReached=true;
                                                            std::ofstream prefix(std::string(argv[2])+".following-pause.prefix.csv");if(!prefix)throw std::runtime_error("Cannot open following pause geometry");
                                                            prefix<<"version,cycle,scrollX,scrollY,windowX,windowY";for(int i=0;i<40;++i)prefix<<",objectX"<<i<<",objectY"<<i;prefix<<'\n';
                                                            prefix<<1<<','<<clock.now<<','<<((state.cameraX>>4)&255)<<','<<((state.cameraY>>4)&255)<<",7,136";for(int i=0;i<40;++i)prefix<<','<<int(state.objects[4*i+1])<<','<<int(state.objects[4*i]);prefix<<'\n';
                                                            airFollowingEntryPause(clock,state,*game,sound,assets,
                                                                [&](unsigned index,int64_t cycle,int tick,int display,int effects,int music,const DisplayInput& input){services<<index<<','<<cycle<<','<<tick<<','<<display<<','<<effects<<','<<music<<','<<input.held<<','<<input.pressed<<'\n';},
                                                                [&](const char* name,int64_t start,int64_t end,int work){pausePhases<<name<<','<<start<<','<<end<<','<<work<<'\n';},
                                                                [&](const char* name,const char* kind,unsigned address,int value,int64_t cycle){pauseBus<<name<<','<<kind<<','<<address<<','<<value<<','<<cycle<<'\n';},
                                                                [&](const char* name,int64_t cycle,const AirPauseGraphics& state){pauseStorage<<name<<','<<cycle;for(int value:state.row)pauseStorage<<','<<value;for(int value:state.font)pauseStorage<<','<<value;pauseStorage<<'\n';},nextResultInput);};
                                                    }
                                                    auto entered=airFollowingEntry(stage,sound,
                                                        [&](const char* name,int64_t cycle,const AirFollowingSetup& state){const auto& t=state.instruction.map.campaign.timing;points<<name<<','<<cycle<<','<<t.tick<<','<<t.countdown<<','<<state.display<<','<<state.stat<<','<<state.lcdc<<','<<state.lyc<<','<<state.pendingRequests<<','<<state.cameraX<<','<<state.cameraY<<','<<state.mapScratch<<','<<state.randomState<<','<<state.ready<<','<<sound.enabled<<','<<t.input.held<<','<<t.input.pressed<<'\n';},
                                                        [&](unsigned index,int64_t cycle,int tick,int display,int effects,int music,const DisplayInput& input){services<<index<<','<<cycle<<','<<tick<<','<<display<<','<<effects<<','<<music<<','<<input.held<<','<<input.pressed<<'\n';},
                                                        [&](const char* kind,int64_t cycle,AirIrqOwner owner){irqs<<kind<<','<<cycle<<','<<int(owner)<<'\n';},nextResultInput,pauseOwner);
                                                    std::ofstream summary(std::string(argv[2])+".following-entry.summary.csv");const auto& t=entered.instruction.map.campaign.timing;
                                                    summary<<"end,tick,countdown,displays,stats,lcdEpoch,nextStat,nextVBlank,randomState,hudCursor,fadeRemaining,entryPauseComplete\n"<<t.end<<','<<t.tick<<','<<t.countdown<<','<<t.displays<<','<<t.stats<<','<<t.lcdEpoch<<','<<t.nextStat<<','<<t.nextVBlank<<','<<entered.randomState<<','<<entered.hudCursor<<','<<entered.fadeRemaining<<','<<entered.entryPauseComplete<<'\n';
                                                    if(followingGameplay){
                                                        auto next=std::make_unique<AirGame>(*assets,*shared);airFollowingAirHandoff(*next,*game,entered);
                                                        std::ofstream points(std::string(argv[2])+".following-gameplay.csv"),entities(std::string(argv[2])+".following-gameplay.entities.csv"),services(std::string(argv[2])+".following-gameplay.services.csv"),irqs(std::string(argv[2])+".following-gameplay.interrupts.csv"),spritePublications(std::string(argv[2])+".following-gameplay.sprites.csv");
                                                        if(!points||!entities||!services||!irqs||!spritePublications)throw std::runtime_error("Cannot open following gameplay outputs");
                                                        points<<"boundary,cycle,tick,secondTicks,seconds,random,ready,map,lastMapCamera,mapScratch,cameraX,cameraY,hudCursor,fadeRemaining,held,pressed,lcdc,display,transfer,remaining,effect,reverse,transferFrame,transferFlags,result\n";
                                                        entities<<"boundary,slot,alive,frame,flags,handler,x,y,done,waiting,delay,period";for(int i=0;i<7;++i)entities<<",param"<<i;entities<<'\n';
                                                        services<<"service,cycle,tick,display,effects,music,inputHeld,inputPressed\n";irqs<<"kind,vectorCycle,owner\n";
                                                        spritePublications<<"service,slot,present,x,y,flags\n";
                                                        auto restarted=entered;
                                                        for(int update=0;update<followingUpdates;++update){
                                                        restarted=airFollowingAirQuietUpdate(restarted,*next,sound,
                                                            [&](const char* name,int64_t cycle,const AirFollowingSetup& s,const AirGame& g){const auto& input=s.instruction.map.campaign.timing.input;
                                                                points<<name<<','<<cycle<<','<<g.ticks<<','<<g.secondTicks<<','<<g.seconds<<','<<g.randomState<<','<<s.ready<<','<<g.mapTransfer<<','<<g.lastMapCamera<<','<<s.mapScratch<<','<<g.cameraX<<','<<g.cameraY<<','<<g.hudCursor<<','<<g.displayFadeRemaining<<','<<input.held<<','<<input.pressed<<','<<s.lcdc<<','<<s.display<<','<<g.transferState<<','<<g.transferRemaining<<','<<g.pendingSound<<','<<g.reverseSprites<<','<<g.transferFrame<<','<<g.transferFlags<<','<<g.result<<'\n';
                                                                for(int i=0;i<16;++i){const auto& e=g.entities[i];entities<<name<<','<<i<<','<<e.alive<<','<<(e.alive?e.frame:255)<<','<<((e.flags&~2)|(e.offscreen?2:0))<<','<<int(e.handler)<<','<<e.x<<','<<e.y<<','<<e.animDone<<','<<e.frameWaiting<<','<<e.delay<<','<<e.period;for(int value:e.params)entities<<','<<value;entities<<'\n';}},
                                                            [&](unsigned index,int64_t cycle,int tick,int display,int effects,int music,const DisplayInput& input){services<<index<<','<<cycle<<','<<tick<<','<<display<<','<<effects<<','<<music<<','<<input.held<<','<<input.pressed<<'\n';
                                                                for(int slot=0;slot<40;++slot){const auto& e=next->visibleSprites.slots[slot];spritePublications<<index<<','<<slot<<','<<(e.present&&e.y!=0)<<','<<e.x<<','<<e.y<<','<<e.flags<<'\n';}},
                                                            [&](const char* kind,int64_t cycle,AirIrqOwner owner){irqs<<kind<<','<<cycle<<','<<int(owner)<<'\n';},nextResultInput,followingTerminal&&update==followingUpdates-1);
                                                        }
                                                        std::ofstream summary(std::string(argv[2])+".following-gameplay.summary.csv");const auto& t=restarted.instruction.map.campaign.timing;
                                                        summary<<"end,tick,countdown,displays,stats,lcdEpoch,nextStat,nextVBlank\n"<<t.end<<','<<t.tick<<','<<t.countdown<<','<<t.displays<<','<<t.stats<<','<<t.lcdEpoch<<','<<t.nextStat<<','<<t.nextVBlank<<'\n';
                                                        if(followingOutro){
                                                            std::ofstream phases(std::string(argv[2])+".following-outro.csv"),outServices(std::string(argv[2])+".following-outro.services.csv"),outIrqs(std::string(argv[2])+".following-outro.interrupts.csv"),outSprites(std::string(argv[2])+".following-outro.sprites.csv"),outSummary(std::string(argv[2])+".following-outro.summary.csv");
                                                            if(!phases||!outServices||!outIrqs||!outSprites||!outSummary)throw std::runtime_error("Cannot open following outgoing-fade outputs");
                                                            phases<<"phase,index,start,end,tickBefore,tickAfter,elapsed,work,bgp,obp0,obp1,musicEnabled\n";
                                                            outServices<<"service,cycle,tick,display,effects,music,inputHeld,inputPressed\n";outIrqs<<"kind,vectorCycle,owner\n";outSprites<<"service,slot,present,x,y,flags\n";
                                                            restarted=airFollowingAirOutro(restarted,*next,sound,*ui,
                                                                [&](const char* name,int index,int64_t begin,int64_t end,int before,int after,int work,int bgp,int obp0,int obp1,bool enabled){phases<<name<<','<<index<<','<<begin<<','<<end<<','<<before<<','<<after<<','<<(end-begin)<<','<<work<<','<<bgp<<','<<obp0<<','<<obp1<<','<<enabled<<'\n';},
                                                                [&](unsigned index,int64_t cycle,int tick,int display,int effects,int music,const DisplayInput& input){outServices<<index<<','<<cycle<<','<<tick<<','<<display<<','<<effects<<','<<music<<','<<input.held<<','<<input.pressed<<'\n';for(int slot=0;slot<40;++slot){const auto& e=next->visibleSprites.slots[slot];outSprites<<index<<','<<slot<<','<<(e.present&&e.y!=0)<<','<<e.x<<','<<e.y<<','<<e.flags<<'\n';}},
                                                                [&](const char* kind,int64_t cycle,AirIrqOwner owner){outIrqs<<kind<<','<<cycle<<','<<int(owner)<<'\n';},nextResultInput);
                                                            const auto& end=restarted.instruction.map.campaign.timing;
                                                            outSummary<<"end,tick,countdown,displays,stats,lcdEpoch,nextStat,nextVBlank\n"<<end.end<<','<<end.tick<<','<<end.countdown<<','<<end.displays<<','<<end.stats<<','<<end.lcdEpoch<<','<<end.nextStat<<','<<end.nextVBlank<<'\n';
                                                            if(followingResult){
                                                                auto& campaign=restarted.instruction.map.campaign;
                                                                int player=campaign.player,lives=campaign.lives[player];
                                                                if((next->result&6)||lives<=1||sound.enabled)throw std::runtime_error("Following result requires its non-final failure owner");
                                                                AirClock resultClock;resultClock.now=end.end;resultClock.nextStat=end.nextStat;resultClock.nextVBlank=end.nextVBlank;
                                                                std::ofstream points(std::string(argv[2])+".following-result.csv"),polls(std::string(argv[2])+".following-result.polls.csv"),prefixSummary(std::string(argv[2])+".following-result.summary.csv");
                                                                if(!points||!polls||!prefixSummary)throw std::runtime_error("Cannot open following result-prefix outputs");
                                                                points<<"boundary,cycle\n";polls<<"cycle,ly\n";
                                                                auto prefix=airResultSetupPrefix(resultClock,next->result,[&](const char* name,int64_t cycle){points<<name<<','<<cycle<<'\n';},[&](int64_t cycle,int line){polls<<cycle<<','<<line<<'\n';},next->randomState,end.lcdEpoch);
                                                                prefixSummary<<"end,lcdDisabled,pollReads,pendingRequests,display,stat,countdown,random,tick,player,lives,inputHeld,inputPressed\n"<<prefix.end<<','<<prefix.lcdDisabled<<','<<prefix.pollReads<<','<<prefix.pendingRequests<<','<<prefix.display<<','<<prefix.stat<<','<<prefix.countdown<<','<<prefix.celebration.randomState<<','<<end.tick<<','<<player<<','<<lives<<','<<end.input.held<<','<<end.input.pressed<<'\n';
                                                                auto layouts=AirResultLayoutAssets::load("build/result-timing.dat");
                                                                std::ofstream incomingPoints(std::string(argv[2])+".following-incoming.csv"),incomingServices(std::string(argv[2])+".following-incoming.services.csv"),incomingIrqs(std::string(argv[2])+".following-incoming.interrupts.csv"),incomingSummary(std::string(argv[2])+".following-incoming.summary.csv");
                                                                if(!incomingPoints||!incomingServices||!incomingIrqs||!incomingSummary)throw std::runtime_error("Cannot open following incoming-result outputs");
                                                                incomingPoints<<"boundary,cycle,tick,countdown,bgp,obp0,obp1,musicEnabled,inputHeld,inputPressed\n";
                                                                incomingServices<<"service,cycle,tick,countdown,display,effects,music,musicEnabled,inputHeld,inputPressed\n";incomingIrqs<<"kind,vectorCycle,owner\n";
                                                                auto incomingPoint=[&](const char* name,int64_t cycle,int tick,int countdown,int bgp,int obp0,int obp1,bool enabled){incomingPoints<<name<<','<<cycle<<','<<tick<<','<<countdown<<','<<bgp<<','<<obp0<<','<<obp1<<','<<enabled<<','<<sampled.held<<','<<sampled.pressed<<'\n';};
                                                                auto incomingService=[&](unsigned index,int64_t cycle,int tick,int countdown,int display,int effects,int music,bool enabled){incomingServices<<index<<','<<cycle<<','<<tick<<','<<countdown<<','<<display<<','<<effects<<','<<music<<','<<enabled<<','<<sampled.held<<','<<sampled.pressed<<'\n';};
                                                                auto incomingIrq=[&](const char* kind,int64_t cycle,AirIrqOwner owner){incomingIrqs<<kind<<','<<cycle<<','<<int(owner)<<'\n';};
                                                                auto incoming=airResultIncoming(prefix,next->result,end.tick,lives,end.input.held,sound,layouts,*ui,incomingPoint,incomingService,incomingIrq,nextResultInput);
                                                                campaign.lives[player]=incoming.lives;
                                                                if(followingResultHold)incoming=airResultFailureHold(incoming,next->result,incoming.input.held,sound,*ui,incomingPoint,incomingService,incomingIrq,nextResultInput);
                                                                incomingSummary<<"end,lcdEpoch,tick,countdown,displays,stats,nextStat,nextVBlank,player,lives\n"<<incoming.end<<','<<incoming.lcdEpoch<<','<<incoming.tick<<','<<incoming.countdown<<','<<incoming.displays<<','<<incoming.stats<<','<<incoming.nextStat<<','<<incoming.nextVBlank<<','<<player<<','<<incoming.lives<<'\n';
                                                                if(nextInstructionExtent){auto typed=airProbeNextInstruction(argv[2],campaign,incoming,next->result,restarted.stage,restarted.difficulty,restarted.instruction.map.scroll,sound,*ui,nextInstructionExtent,nextResultInput);
                                                                    if(nextRetry)airProbeNextRetry(argv[2],typed,*next,*assets,*shared,restarted.stage,restarted.difficulty,sound,*ui,nextResultInput,nextUpdates,nextTerminal,nextResult,thirdInstructionExtent,fourthEntry,fourthUpdates,fourthResult,fifthInstructionExtent,fifthEntry,fifthUpdates,fifthTerminal);}
                                                            }
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
                if(resultInputs.is_open()){int spare;if(resultInputs>>spare)throw std::runtime_error("Result button input extends beyond replay completion");if(!resultInputs.eof())throw std::runtime_error("Malformed trailing result input");}
            }
        }
        if(!frameServices.empty()&&*frameServices.rbegin()>=clock.displays)throw std::runtime_error("Selected native frame services exceed replay coverage");
        if(followingEntryPause&&!followingPauseReached)throw std::runtime_error("Following entry replay did not reach its fresh Start pause");
        fprintf(stderr,"Completed %d ordinary-clock updates, %u display services, %u STAT services; %s buttons.\n",updates,clock.displays,clock.statServices,displayInputs.is_open()?"display-sampled":"update-aligned");
        return 0;
    }catch(const std::exception& e){fprintf(stderr,"%s\n",e.what());return 1;}
}
