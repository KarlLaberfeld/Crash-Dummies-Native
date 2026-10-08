#pragma once
#include "air_instruction_exit.h"
#include "air_video_work.h"

namespace ticd {
struct AirFollowingSetup {
    AirInstructionTextState instruction;
    int stage=0,difficulty=0,lcdc=0,lyc=95,display=5,stat=5;
    int64_t lcdDisabled=0;
    int pendingRequests=0,pollReads=0;
    int cameraX=0,cameraY=0,mapScratch=0,ready=0,randomState=0,hudCursor=0,fadeRemaining=8;
    std::array<unsigned char,256> objects{},actors{};
};
// 0355..0367: the identified instruction-to-stunt service gate. The inherited
// LCD epoch determines the line-145 equality wait; no observed duration enters
// this owner. Services are masked until a later, separately owned LCD restart.
template<class Boundary,class Poll,class Write>
AirFollowingSetup airFollowingSetupPrefix(AirInstructionTextState instruction,int stage,int difficulty,
    const NativeAudio& sound,Boundary&& boundary,Poll&& poll,Write&& write){
    const auto& map=instruction.map;
    if((stage!=1&&stage!=2)||difficulty<0||difficulty>3||map.campaign.player<0||map.campaign.player>1||
       map.campaign.lives[map.campaign.player]<1||map.campaign.lives[map.campaign.player]>255||sound.enabled||map.display!=5||map.stat!=5||map.lyc!=95||
       !(map.lcdc&128)||(map.lcdc&2)||instruction.speed||instruction.skipMask)
        throw std::runtime_error("Unowned following stunt setup entry");
    AirFollowingSetup state;state.instruction=instruction;state.stage=stage;state.difficulty=difficulty;
    state.lcdc=map.lcdc;auto& timing=state.instruction.map.campaign.timing;int64_t now=timing.end;
    auto point=[&](const char* name){boundary(name,now,state);};
    point("begin");now+=4+100; // DI, caller, on test, save IE and mask VBlank.
    for(;;){
        if(state.pollReads>=2200)throw std::runtime_error("Following LCD-off equality wait did not terminate");
        int line=airResultScanline(now+8-timing.lcdEpoch);now+=12;++state.pollReads;poll(now,line);
        now+=8;if(line==145){now+=8;break;}now+=12;
    }
    now+=12+8+12;state.lcdc&=127;state.lcdDisabled=now;
    state.pendingRequests=(timing.nextStat<=now?2:0)|(timing.nextVBlank<=now?1:0);
    now+=16+12+16;point("lcdOffReturned");
    now+=12+24+4;
    for(int i=0;i<256;++i){write(now,0xc100+i,0);now+=8;state.objects[i]=0;now+=4+(i==255?8:12);}
    now+=16;point("objectsCleared");
    now+=12+24+12+8+24;
    for(int i=0;i<256;++i){write(now,0xc200+i,255);now+=8;state.actors[i]=255;now+=4+(i==255?8:12);}
    now+=16+4+12+16;point("stateReset");
    // Selected native campaign player's eight-byte record; no source pointer
    // or CPU register is needed to compute its identified selection work.
    now+=24+16+4+4+4+8+4+8+16;point("stagePointer");
    timing.end=now;return state;
}

struct AirFollowingStageProfile {
    int bands=0,lookupCarries=0,placements=0,chunks=0,cameraX=0,cameraY=0;
    void validate()const{
        if(bands<1||bands>64||lookupCarries<0||lookupCarries>bands||placements<1||placements>512||chunks<1||chunks>13||
            cameraX<0||cameraX>65535||cameraY<0||cameraY>65535)
            throw std::runtime_error("Invalid native following-stage workload");
    }
};
struct AirFollowingStageAssets {
    std::array<AirFollowingStageProfile,8> profiles;
    static AirFollowingStageAssets load(const char* path){
        std::ifstream file(path,std::ios::binary);char magic[8];AirFollowingStageAssets assets;
        if(!file.read(magic,8)||std::string(magic,8)!="TICDFS01")throw std::runtime_error("Missing following-stage workload assets");
        for(auto& p:assets.profiles){
            int* fields[]={&p.bands,&p.lookupCarries,&p.placements,&p.chunks,&p.cameraX,&p.cameraY};
            for(int* value:fields){unsigned char bytes[2];if(!file.read(reinterpret_cast<char*>(bytes),2))throw std::runtime_error("Truncated following-stage workload");*value=bytes[0]+256*bytes[1];}
            p.validate();
        }
        if(file.peek()!=std::char_traits<char>::eof())throw std::runtime_error("Trailing following-stage workload");return assets;
    }
};
// Identified fixed native copies. Callers supply their semantic byte counts;
// the LCD-off path has no readiness stalls. A 9800 destination wrap adds four.
inline int followingRamCopyWork(int bytes){return 52*bytes-4+16;}
inline int followingVideoCopyWork(int bytes,int wraps=0){return 104*bytes-4+16+4*wraps;}
inline int followingQuadrantCopyWork(int bytes){
    int copy=followingRamCopyWork(bytes);
    return 3*(12+16+24+copy+12)+12+16+copy;
}
inline int followingInitialMapWork(bool air,int cameraY){
    // 1e77's 32 rows: direct preparation body (2116/192), 32-byte row
    // publication (736/40), and source loop/coordinate wrappers. Air's first
    // row's bit-7 change and downward branch come from native word-wrapped
    // coordinates, including the high-difficulty initial-coordinate wrap.
    int work=24+108+32*192-4+16,previous=air?0x8000:0x4000,current=(cameraY+4096)&65535;
    for(int row=0;row<32;++row){
        bool changed=(previous^current)&128;
        work+=changed?2116+736+(((previous-current)&0x8000)?4:0):192+40;
        previous=current;current=(current-128)&65535;
    }
    return work;
}
// 0367..039c. Services remain masked throughout these decoded-map/template,
// placement, sprite, initial-map and music-start operations. This owner does
// not claim physical bus contents or the later display callbacks.
template<class Boundary>
AirFollowingSetup airFollowingStageSetup(AirFollowingSetup state,const AirFollowingStageProfile& p,
    NativeAudio& sound,Boundary&& boundary){
    p.validate();const bool air=state.stage==1;auto& timing=state.instruction.map.campaign.timing;
    if((state.stage!=1&&state.stage!=2)||sound.enabled||state.pendingRequests!=3||state.lcdc&128||
        (air&&(p.cameraY&255)!=128)||(!air&&p.cameraY))throw std::runtime_error("Unowned masked following-stage setup");
    int64_t now=timing.end;auto point=[&](const char* name){boundary(name,now,state);};
    now+=8+12+24+72;point("stageEntry");
    now+=68+36+24+followingRamCopyWork(air?48:52)+24+24+followingRamCopyWork(air?118:78);point("rootsReady");
    if(air){
        now+=68+36+24+followingVideoCopyWork(2048,1)+36+24+followingRamCopyWork(128)+24+24+followingQuadrantCopyWork(128);
    }else{
        now+=8+60+8+12+36+24+followingVideoCopyWork(1472)+36+24+followingVideoCopyWork(2032)+
            24+24+followingQuadrantCopyWork(64)+36+24+followingRamCopyWork(128);
    }
    point("terrainReady");
    // 16 columns x four rows per band, rotated columns; table and destination
    // carries add their identified eight-cycle helper paths.
    now+=(air?360:352)+48+5556*p.bands+8*(p.bands/4+p.lookupCarries);point("mapReady");
    now+=124+104+376*p.placements;point("placementsReady");
    now+=80+76*p.placements;point("offsetsReady");
    if(air){now+=68+8+12+36+24+followingVideoCopyWork(2848);point("fixedTilesReady");}
    now+=air?348:264;state.cameraX=p.cameraX;state.cameraY=p.cameraY;state.display=air?4:6;point("scalarsReady");
    now+=(air?68:64)+24+816;point("playerReady");
    now+=492+followingRamCopyWork(32*p.chunks);state.ready=1;point("spritesReady");
    if(air){now+=60+24+816+52;point("helperReady");}
    now+=followingInitialMapWork(air,p.cameraY);
    // Last native row destination is derived from the penultimate row's world
    // coordinate. C00C/D has a row-publication role here, not RNG ownership.
    state.mapScratch=256+(((2*((p.cameraY+256)&65535)>>8)+24)&31)*8;point("mapPrepared");
    now+=airResultMusicStartWork();sound.playMusic(air?9:10);point("stageReady");
    now+=240;state.stat=4;state.lcdc=0x67;state.lyc=135;state.randomState=0;point("registersReady");
    timing.end=now;return state;
}

inline int followingHudSetupWork(bool air){
    // Shared callback selection, seven header/scalar stores and 20 map bytes.
    int work=220+92+36+24+followingRamCopyWork(20);
    if(air)work+=60+followingVideoCopyWork(128)+2*(48+followingVideoCopyWork(16))+24+airHudRefreshWork(0,1);
    else work+=60+followingVideoCopyWork(16)+24+476; // Three BCD pairs, no progress division.
    int columns=air?13:7;
    // JP into the all-column writer. The last cursor wrap adds twelve while
    // the final loop branch saves four; each column has its own 224 work.
    return work+16+36+292*columns+12-4;
}
// 039c..03d8, ending before the next stunt's first update. Initial scene seed,
// fixed glyph copies, HUD composition, LCD restart, the two pending vectors,
// first counter wait, input/audio and ready-clear all belong to this owner.
// The limited two-display callback has no actor/resource update or HUD wrap.
template<class Boundary,class Service,class Interrupt>
AirFollowingSetup airFollowingEntry(AirFollowingSetup state,NativeAudio& sound,
    Boundary&& boundary,Service&& service,Interrupt&& interrupt,std::function<int()> sampleInput={}){
    if((state.stage!=1&&state.stage!=2)||!sound.enabled||state.stat!=4||state.lyc!=135||state.lcdc!=0x67||state.ready!=1||state.pendingRequests!=3)
        throw std::runtime_error("Unowned following LCD/gameplay entry");
    const bool air=state.stage==1;auto& timing=state.instruction.map.campaign.timing;int64_t now=timing.end;
    auto point=[&](const char* name,int64_t cycle){boundary(name,cycle,state);};
    point("begin",now);now+=72;state.randomState=(timing.tick&255)<<8;point("scenePrepared",now);
    now+=68;point("resourceBank",now);now+=24;point("resourceCopy",now);
    // Inline semantic font list contains thirteen selected 16-byte glyphs.
    // Table dispatch costs 120 per glyph, then the 52-cycle byte copy.
    now+=24+68+13*(8+16+16+24+120+followingRamCopyWork(16)+12+12+4+12)-4+4;point("resourceReady",now);
    now+=followingHudSetupWork(air);point("hudReady",now);
    now+=88;point("lcdEnableCall",now);now+=56;state.lcdc|=128;point("lcdEnabled",now);
    timing.lcdEpoch=now-4;now+=16;point("enableReturned",now);
    AirClock clock;clock.now=now;clock.nextStat=timing.lcdEpoch+AirClock::StatLine;clock.nextVBlank=timing.lcdEpoch+AirClock::VBlankLine;
    clock.displays=timing.displays;clock.statServices=timing.stats;unsigned initial=clock.displays;
    clock.interrupt=[&](const char* kind,int64_t cycle,AirIrqOwner owner){interrupt(kind,cycle,owner);};
    clock.objectDisable=[&](int64_t,AirIrqOwner){state.lcdc&=~2;};
    auto display=[&](bool ready){
        if(!ready||clock.displays-initial>=2||state.hudCursor>1)throw std::runtime_error("Unowned following entry display extent");
        timing.input.sample(sampleInput?sampleInput():timing.input.held);
        if(timing.input.held<0||timing.input.held>255||(timing.input.held&15)==15)throw std::runtime_error("Unowned following entry reset input");
        int tick=timing.tick;auto work=airDisplayWork(true,true,0,state.hudCursor,tick,state.fadeRemaining,0,1);
        ++state.hudCursor;if(!(tick&1)&&state.fadeRemaining)--state.fadeRemaining;state.lcdc|=2;
        timing.tick=(timing.tick+1)&65535;sound.tick();
        if(sound.effectWorkCycles<0||sound.musicWorkCycles<0)throw std::runtime_error("Unowned following entry audio work");
        service(clock.displays,clock.now+20,tick,work.total(),sound.effectWorkCycles,sound.musicWorkCycles,timing.input);
        return 1592+work.total()+sound.effectWorkCycles+sound.musicWorkCycles;
    };
    // Both IF requests survived the masked LCD-off interval. The periodic
    // requests restart independently from the native new LCD epoch.
    clock.startup(display);state.pendingRequests=0;
    // Source 03c9 is reached after both pending services, before its store.
    point("displayReturned",clock.now-12);point("readyStored",clock.now);
    clock.wait(display,true);
    clock.atomicWork(4,[]{},display,true);clock.atomicWork(12,[&]{state.ready=0;},display,true);
    clock.atomicWork(12,[]{},display,false);clock.atomicWork(8,[]{},display,false);
    if(timing.input.pressed&8)throw std::runtime_error("Fresh Start at following entry needs its pause owner");
    clock.atomicWork(12,[]{},display,false);point("end",clock.now);
    timing.end=clock.now;timing.nextStat=clock.nextStat;timing.nextVBlank=clock.nextVBlank;
    timing.displays=clock.displays;timing.stats=clock.statServices;return state;
}
}
