// Native state replay for tools/air_reference.py. No emulator or ROM execution.
#include "air.h"
#include <cstdio>
#include <fstream>
#include <memory>
#include <string>

using namespace ticd;
int main(int argc,char**argv){
    if(argc<2||argc>3){fprintf(stderr,"Usage: air-reference-probe inputs.txt [--recorded-clock]\n");return 2;}
    const bool aligned=argc==3&&std::string(argv[2])=="--recorded-clock";
    if(argc==3&&!aligned){fprintf(stderr,"Unknown counter mode\n");return 2;}
    try{
        auto shared=std::make_unique<Assets>(Assets::load(L"build/crash.dat"));
        auto assets=std::make_unique<AirAssets>(AirAssets::load(L"build/air.dat"));
        auto game=std::make_unique<AirGame>(*assets,*shared);game->start(1);
        std::ifstream inputs(argv[1]);
        if(!(inputs>>game->ticks>>game->secondTicks>>game->randomState))return 2;
        puts("tick,handler,frame,flags,x,y,cameraX,cameraY,speed,rate,tilt,count,crash,anim,done,waiting,delay,period,transfer,remaining,map,result,seconds,secondTicks,random,pending");
        int tick,held;
        while(inputs>>tick>>held){
            int buttons=((held&1)?A:0)|((held&2)?B:0)|((held&16)?Right:0)|((held&32)?Left:0)|((held&64)?Up:0)|((held&128)?Down:0);
            // Diagnostic alignment only; contiguous mode advances the ordinary
            // native clock. Neither mode copies original player/world state.
            if(aligned)game->ticks=(tick-1)&65535;
            game->step(buttons);const auto& p=game->entities[0];
            printf("%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d\n",
                   game->ticks,int(p.handler),p.frame,p.flags,p.x,p.y,game->cameraX,game->cameraY,
                   game->speed,game->rate,game->tilt,p.params[0],p.params[2],p.anim,p.animDone,p.frameWaiting,
                   p.delay,p.period,game->transferState,game->transferRemaining,game->mapTransfer,
                   game->resultFlags,game->seconds,game->secondTicks,game->randomState,game->crashRecoveryPending);
        }
        if(!inputs.eof())return 2;
        return 0;
    }catch(const std::exception& e){fprintf(stderr,"%s\n",e.what());return 1;}
}
