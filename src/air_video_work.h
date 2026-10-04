#pragma once
#include <algorithm>

namespace ticd {
// Original T-cycle work of the Air display callback. Semantic state only:
// no CPU registers, opcode execution, ROM reads or measured frame indices.
struct AirDisplayWork {
    int map=0,resources=0,hud=0,scroll=176,lcd=32,fade=0,refresh=0;
    int total()const{
        if(map<0||resources<0||hud<0||scroll<0||lcd<0||fade<0||refresh<0)return -1;
        return 116+map+resources+hud+scroll+lcd+fade+refresh+16;
    }
};
inline int airUploadWork(bool ready,int chunks){
    if(!ready)return 36; // 1897 checks FFAE before any descriptor/transfer work.
    if(!chunks)return 60;
    return chunks>4?3112:456+672*chunks;
}
inline int airProgressBarWork(int value){
    value&=255;
    if(!value)return 172;
    int full=std::min(value/8,6);
    if(full==6)return 288;
    return full==5?304:208+20*full;
}
inline int airHudRefreshWork(int collected,int quota){
    if(quota<=0)return -1;
    int quotient=48*collected/quota;
    // The restoring divide's successful subtractions are the set bits of
    // its mathematical quotient. Count those bits; do not reproduce a CPU.
    int divide=2632;
    for(int bits=quotient;bits;bits>>=1)divide-=20*(bits&1);
    int tableCarry=(((2*collected)&255)+collected)>255?8:0;
    return 708+tableCarry+divide+airProgressBarWork(quotient);
}
inline AirDisplayWork airDisplayWork(bool map,bool ready,int chunks,int cursor,
                                    int ticks,int fadeRemaining,int collected,int quota){
    AirDisplayWork work;
    work.map=24+(map?736:40);
    work.resources=map?32:44+airUploadWork(ready,chunks);
    work.hud=24+224+(cursor==12?12:0);
    work.fade=24+((ticks&1)?40:fadeRemaining?208:68);
    int refresh=cursor==12?airHudRefreshWork(collected,quota):40;
    work.refresh=refresh<0?-1:24+refresh;
    return work;
}
}
