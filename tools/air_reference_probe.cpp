// Native state replay for tools/air_reference.py. No emulator or ROM execution.
#include "air.h"
#include <cstdio>
#include <fstream>
#include <memory>
#include <string>

using namespace ticd;
int main(int argc,char**argv){
    if(argc<2){fprintf(stderr,"Usage: air-reference-probe inputs.txt [--recorded-clock] [--difficulty 0..3] [--work-csv path] [--entities-csv path] [--handlers-csv path] [--display-csv path]\n");return 2;}
    bool aligned=false;int difficulty=1;std::string workPath,entityPath,handlerPath,displayPath;
    try{
    for(int i=2;i<argc;++i){
        std::string option=argv[i];
        if(option=="--recorded-clock")aligned=true;
        else if(option=="--difficulty"&&i+1<argc)difficulty=std::stoi(argv[++i]);
        else if(option=="--work-csv"&&i+1<argc)workPath=argv[++i];
        else if(option=="--entities-csv"&&i+1<argc)entityPath=argv[++i];
        else if(option=="--handlers-csv"&&i+1<argc)handlerPath=argv[++i];
        else if(option=="--display-csv"&&i+1<argc)displayPath=argv[++i];
        else{fprintf(stderr,"Unknown or incomplete option\n");return 2;}
    }
        if(difficulty<0||difficulty>3)throw std::runtime_error("Invalid Air difficulty");
        auto shared=std::make_unique<Assets>(Assets::load(L"build/crash.dat"));
        auto assets=std::make_unique<AirAssets>(AirAssets::load(L"build/air.dat"));
        auto game=std::make_unique<AirGame>(*assets,*shared);game->start(difficulty);
        game->measureWork=!workPath.empty()||!handlerPath.empty()||!displayPath.empty();
        std::ifstream inputs(argv[1]);
        if(!(inputs>>game->ticks>>game->secondTicks>>game->randomState))return 2;
        std::ofstream work;
        std::ofstream entityLog;
        std::ofstream handlerLog;
        std::ofstream displayLog;
        if(!displayPath.empty()){
            displayLog.open(displayPath);if(!displayLog)throw std::runtime_error("Could not open display output");
            displayLog<<"update,cost,cursor,fade,bar0,bar1,bar2,bar3,bar4,bar5\n";
        }
        if(!handlerPath.empty()){
            handlerLog.open(handlerPath);if(!handlerLog)throw std::runtime_error("Could not open handler output");
            handlerLog<<"update,slot,handler,cost\n";
        }
        if(!entityPath.empty()){
            entityLog.open(entityPath);if(!entityLog)throw std::runtime_error("Could not open entity output");
            entityLog<<"update,slot,frame,flags,x,y\n";
        }
        if(!workPath.empty()){
            work.open(workPath);if(!work)throw std::runtime_error("Could not open workload output");
            work<<"update,entitiesDone,sprites,spritesDone,mapCallback,placements,animation,collisionScan,collisionCallbacks,playerMotion,playerInput\n";
        }
        puts("tick,handler,frame,flags,x,y,cameraX,cameraY,speed,rate,tilt,count,crash,anim,done,waiting,delay,period,transfer,remaining,map,result,seconds,secondTicks,random,pending");
        int tick,held,index=0;
        while(inputs>>tick>>held){
            if(entityLog.is_open())for(int slot=0;slot<16;++slot){const auto& e=game->entities[slot];
                entityLog<<index<<','<<slot<<','<<(e.alive?e.frame:255)<<','<<((e.flags&~2)|(e.offscreen?2:0))<<','<<e.x<<','<<e.y<<'\n';
            }
            ++index;
            int buttons=((held&1)?A:0)|((held&2)?B:0)|((held&16)?Right:0)|((held&32)?Left:0)|((held&64)?Up:0)|((held&128)?Down:0);
            // Diagnostic alignment only; contiguous mode advances the ordinary
            // native clock. Neither mode copies original player/world state.
            if(aligned)game->ticks=(tick-1)&65535;
            game->step(buttons);const auto& p=game->entities[0];
            if(displayLog.is_open()){
                displayLog<<index-1<<','<<game->displayWorkCycles<<','<<game->hudCursor<<','<<game->displayFadeRemaining;
                for(int j=7;j<13;++j)displayLog<<','<<static_cast<int>(game->hudValues[j]);
                displayLog<<'\n';
            }
            if(handlerLog.is_open())for(int slot=0;slot<16;++slot)if(game->handlerWorkCycles[slot]!=-2)
                handlerLog<<index-1<<','<<slot<<','<<game->handlerWorkKinds[slot]<<','<<game->handlerWorkCycles[slot]<<'\n';
            if(work.is_open())work<<game->entityWorkCycles<<','<<game->resourceWorkCycles<<','<<game->spriteWorkCycles<<','<<game->clearWorkCycles<<','<<game->mapWorkCycles<<','<<game->placementWorkCycles<<','<<(game->animationWorkComplete?game->animationWorkCycles:-1)<<','<<game->collisionScanWorkCycles<<','<<game->collisionCallbackWorkCycles<<','<<game->playerMotionWorkCycles<<','<<game->playerInputWorkCycles<<'\n';
            printf("%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d\n",
                   game->ticks,int(p.handler),p.frame,p.flags,p.x,p.y,game->cameraX,game->cameraY,
                   game->speed,game->rate,game->tilt,p.params[0],p.params[2],p.anim,p.animDone,p.frameWaiting,
                   p.delay,p.period,game->transferState,game->transferRemaining,game->mapTransfer,
                   game->result,game->seconds,game->secondTicks,game->randomState,game->crashRecoveryPending);
        }
        if(!inputs.eof())return 2;
        return 0;
    }catch(const std::exception& e){fprintf(stderr,"%s\n",e.what());return 1;}
}
