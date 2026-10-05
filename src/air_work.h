#pragma once
#include "air.h"

namespace ticd {
struct AirSpriteWork {int prepare=0,clear=0;};
struct AirSpritePieceWork {int before=0;bool writes=false;};
struct AirSpriteEntityWork {int geometry=0,tail=0;std::vector<AirSpritePieceWork> pieces;};

inline int airResourceWork(const AirGame& game,int oldFrame){
    int state=game.transferState,frame=game.entities[0].frame;
    int cost=24+68+24+(state==2?56:40);
    if(state==2)state=0;
    if(frame>=12)return cost+56;
    cost+=44;if(frame==oldFrame)return cost+52;
    cost+=40;
    if(!state){cost+=24+92+28;return game.assets.transferChunks[frame]?cost-12+316:cost;}
    cost+=28;if(frame==game.transferFrame)return cost+44+72;
    cost+=40+76+28;return game.assets.transferChunks[frame]?cost-12+244+72:cost;
}

inline int airAnimationMoveWork(int position,int offset){
    const bool carry=(position&255)+(offset&255)>255;
    int add=(offset&128)?(carry?48:56):(carry?60:52);
    return 84+132+44+add; // 3c50/58, 3d2f/3e and the signed-add helper.
}

inline int airMoveWork(int position,int offset){return airAnimationMoveWork(position,offset)-84;}
inline int airStartAnimationWork(bool done){return done?108:64;} // 00:3b84.

inline int airCollisionBoundsWork(const AirGame& game,const AirEntity& e){
    const auto& m=game.assets.frames[e.frame].meta;
    int x=static_cast<int16_t>((e.x&65520)-(game.cameraX&65520))/16;
    int y=static_cast<int16_t>((e.y&65520)-(game.cameraY&65520))/16;
    auto add=[](int value,int offset){return airMoveWork(value,offset)-176;};
    int cost=84+88+add(x,m[0])+add(y,m[1]); // 23dd pointer lookup and two bank switches.
    x+=static_cast<int8_t>(m[0]);y+=static_cast<int8_t>(m[1]);
    return cost+add(x,m[2])+add(y,m[3]);
}

struct AirCollisionSlotWork {int scan=0;bool callback=false;};
inline AirCollisionSlotWork airCollisionSlotWork(const AirGame& game,int slot){
    const auto& e=game.entities[slot];int cost=52;
    if(slot==0)return {cost+4,false}; // Skip the caller itself at 17c0.
    cost+=28;
    if(!e.alive)return {cost+4,false};
    cost+=308;
    if(e.offscreen)return {cost+4+24,false};
    cost+=308+airCollisionBoundsWork(game,e);
    const auto& p=game.entities[0];
    auto a=spriteBounds(game.assets.frames[p.frame],p.x,p.y,game.cameraX,game.cameraY);
    auto b=spriteBounds(game.assets.frames[e.frame],e.x,e.y,game.cameraX,game.cameraY);
    // Four byte-edge comparisons at 1834; later tests are skipped on rejection.
    for(bool reject:{a[1]<b[0],a[0]>=b[1],a[3]<b[2],a[2]>=b[3]}){
        cost+=24;if(reject)return {cost+4,false};
    }
    // Exclude the entire conditional CALL/dispatch/body span when it runs;
    // reference hooks measure that span separately. No callback is free.
    cost+=32;
    if(e.collision==255)return {cost+12,false}; // Conditional CALL not taken.
    return {cost,true};
}

inline int airDamageWork(int value,int amount,int finishTimer){
    if(value+amount<=255)return 108; // 6613 ordinary return, including RST 18.
    return 276+(finishTimer==1?48:0); // Overflow enters 59b6/59be.
}
inline int airTimerWork(int secondTicks,int seconds){return secondTicks!=59?64:seconds?136:116;}
inline int airApproachByteWork(int value){return !value?32:value<0?68:64;} // 3d5a branch work; INC/DEC updates Z.
inline int airCameraLeadWork(int value,int target){return value==target?56:value>target?84:80;} // 161a.
inline int airInputWork(const AirGame& g){
    int tilt=g.tilt,speed=g.speed,cost=(g.cameraY>>8)<15?160:252;
    auto steer=[&](int direction){
        if(g.transferState)return 36;
        if(g.lastForce)return 60;
        if(!g.rate)return 92;
        if(tilt==2*direction)return 116;
        tilt+=direction;return 132;
    };
    auto up=[&]{if(g.ticks&3)return 44;int work=speed==-20?104:120;if(speed>-20)--speed;return work;};
    if(g.held&Left)cost+=12+steer(-1);
    if(g.held&Right)cost+=12+steer(1);
    if((g.cameraY>>8)>=15){
        if(g.held&A)cost+=12+up();
        if(g.held&B){cost+=12+((g.ticks&1)?44:speed==11?104:120);if(!(g.ticks&1)&&speed<11)++speed;}
        if(!(g.held&(Up|Down))){cost+=12+((g.ticks&15)?44:60+airApproachByteWork(speed));
            if(!(g.ticks&15))speed+=speed<0?1:speed>0?-1:0;}
    }
    if(!(g.held&(Left|Right)))cost+=12+((g.ticks&3)?44:g.lastForce?68:84+airApproachByteWork(tilt));
    if((g.cameraY>>8)<15)cost+=12+up();
    return cost;
}
inline int airImpactWork(const AirGame& g){return 152+(g.speed<0?4:0)+airDamageWork(g.entities[0].params[5],16,g.finishTimer);}
inline int airTerrainBounceWork(const AirGame& g){
    const auto& p=g.entities[0];
    if(p.params[3])return 136+(((g.probes[0]|g.probes[1]|g.probes[2]|g.probes[3]|g.probes[4]|g.probes[5])&0x43)?24:0);
    int base=g.speed<0?0:3,mask=g.speed<0?0x41:0x43,cost=g.speed<0?72:76;
    int turn=0;
    cost+=20;
    if(g.probes[base]&mask){cost+=4;turn=g.speed<0?1:-1;}
    else{cost+=20;if(g.probes[base+1]&mask){cost+=4;turn=g.speed<0?-1:1;}
        else{cost+=20;return cost+((g.probes[base+2]&mask)?4+airImpactWork(g):16);}}
    return cost+((g.tilt==2*turn)?40+airImpactWork(g):112);
}
inline int airSidePushWork(const AirGame& g){
    int base=g.speed<0?0:3,cost=g.speed<0?44:48;
    cost+=20;if(g.probes[base]&32)return cost+4+36+airMoveWork(g.entities[0].x,4);
    cost+=20;if(g.probes[base+1]&32)return cost+4+36+airMoveWork(g.entities[0].x,-4);
    return cost+16;
}
inline int airSlowSurfaceWork(const AirGame& g){
    if(g.ticks&3)return 44;
    return ((g.probes[0]|g.probes[1]|g.probes[2])&4)?148+(g.speed<0?4:0):100;
}
inline int airWallWork(const AirGame& g){
    if(g.speed>=0)return 36;
    int cost=24+36;
    if(g.probes[2]&2)return cost+4+(g.speed<-6?32:48)+224+88+80;
    cost+=36;
    if(!(g.probes[0]&2)){cost+=36;if(!(g.probes[1]&2))return cost+16;}
    cost+=4;
    return cost+(g.tilt?32+airImpactWork(g):368+(g.speed<-6?0:24));
}
constexpr int AirProbeWork=328+28+6*(148+292+44); // 6459 and six 1628/163a calls.
inline int airPlayerMotionWork(const AirGame& game){
    const auto& p=game.entities[0];bool active=p.params[3]!=0;
    bool boosted=active&&p.params[3]!=1&&p.params[3]!=255;
    int pose=boosted?static_cast<int8_t>(p.params[4]):game.tilt;
    const auto& motion=game.assets.tilts.at(pose+2);
    static constexpr int multiplyBody[5]={28,24,20,16,20}; // 1379 table selects -2..2.
    int cost=360+28+(game.tilt>=0?8:0)+(active?(p.params[3]&128?128:124):92);
    if(!game.transferState)cost+=12+148; // Conditional 3d15 and frame/animation flags.
    if(boosted)cost+=12+60+28+(pose>=0?8:0);
    int dx=static_cast<int8_t>(motion[2]*game.rate),dy=static_cast<int8_t>(motion[3]*game.rate);
    cost+=352+multiplyBody[motion[2]+2]+multiplyBody[motion[3]+2]
        +airMoveWork(p.x,dx)+airMoveWork(p.y,dy);
    if(game.rate>=0)cost+=108+((((p.y+dy)&65535)>>8)==game.assets.levels[game.difficulty].rows-2?16:0);
    return cost;
}
inline int airSpawnRelativeWork(const AirGame& game,bool other){
    for(int slot=0;slot<16;++slot)if(!game.entities[slot].alive)
        return (other?296:284)+816+52*slot;
    return (other?296:284)+868;
}
inline int airExplodingWork(const AirGame& game,int countBefore){
    if(countBefore<0||countBefore>255)return -1;
    int phase=(countBefore-1)&255;
    // 62a9 countdown + branch to 62f6's hide/frame helper.
    if(!phase)return 92+292;
    if(phase&7)return 124;
    // Two 1723 calls cost 172 each. Their carry paths take equal work.
    // 62b3..62ea contributes 276, followed by the countdown/sound test.
    return 112+276+2*172+airSpawnRelativeWork(game,false)+((phase&15)?104:144);
}
inline int airSeverityWork(const AirGame& g){
    int severity=g.entities[0].params[5]>>6;
    if(!severity)return 208;
    if(severity==1)return (g.pressed&A)?268+airSpawnRelativeWork(g,false):232;
    if(g.ticks&(severity==2?31:15))return 236;
    int cost=192+32+(severity==3?12:0)+12+24+airApproachByteWork(g.speed);
    return cost+(g.speed>=-1&&g.speed<=1?20:8+144+172+airSpawnRelativeWork(g,false));
}
inline int airFinishGateWork(const AirGame& g){
    if(g.speed>=0)return 36;
    int flags=(g.probes[0]|g.probes[1]|g.probes[2])&0x18;
    if(!flags)return 92;
    const auto& p=g.entities[0];int quota=g.assets.levels[g.difficulty].quota;
    int end=p.params[1]==quota?72:p.params[1]>quota/2?96:92;
    // 60c2..60d0: effect/handler writes plus their called bodies. 60d0..60e7:
    // frame selection, BCD score, two RST 18 bodies and the frame helper.
    return 80+((flags&8)?304:28)+172+airImpactWork(g)+140+108+88+148
        +(((p.params[5]+16)&128)?4:0)+end;
}
inline int airCollisionCallbackWork(const AirGame& game,int slot){
    const auto& p=game.entities[0];const auto& e=game.entities[slot];
    int dispatch=96+(e.collision>=15?8:0); // Conditional CALL + 23d6, table carry.
    if(e.collision!=13&&e.collision!=34&&p.params[2])return dispatch+100;
    switch(e.collision){
    case 7:return dispatch+252+132+108+airStartAnimationWork(e.animDone)+12;
    case 8:return dispatch+396;
    case 9:{
        int impact=152+(game.speed<0?4:0)+airDamageWork(p.params[5],16,game.finishTimer);
        return dispatch+332+132+impact+airSpawnRelativeWork(game,true)+108
            +airDamageWork((p.params[5]+16)&255,32,game.finishTimer)+28;
    }
    case 10:return dispatch+452;
    case 11:return dispatch+256;
    case 12:return dispatch+180+44+airSpawnRelativeWork(game,true)+80+airDamageWork(p.params[5],16,game.finishTimer)+28;
    case 13:return dispatch+(p.params[2]?396:100);
    case 14:return dispatch+(game.speed?488+(game.money<50?32:0):316);
    case 15:return dispatch+572+(p.params[5]<32?16:0);
    case 34:return dispatch+264;
    default:return -1;
    }
}

inline int airCameraWork(const AirGame& game,bool horizontal){
    const auto& p=game.entities[0];int cost=0;
    if(horizontal){
        int dx=static_cast<int8_t>(((p.x-game.cameraX)&4095)/16-64);
        cost=300+44+airMoveWork(game.cameraX,dx)-176; // 3e41 + RST 18 + signed add.
    }
    int dy=static_cast<int8_t>((static_cast<int16_t>(p.y-game.cameraY)>>3)-game.cameraLead);
    int y=(game.cameraY+dy)&65535;
    cost+=244+44; // 3ecc..3ef8 and RST 18; negative branch not taken.
    if(dy<0)return cost+88+airMoveWork(game.cameraY,dy)-176+((y>>8)==255?32:0);
    cost+=4+76+28+(((game.cameraY&255)+dy>255)?8:0);
    if((y&255)<128)return cost;
    cost+=36;
    if((y>>8)==(game.assets.levels[game.difficulty].cameraY>>8))cost+=36;
    return cost;
}

// Body costs only: the sixteen-slot dispatcher adds 1612 + 60 per live call.
// Unknown handlers deliberately return -1; never treat this as a frame budget.
inline int airSimpleHandlerWork(const AirGame& game,const AirEntity& before,
                                const AirEntity& after,int animation,int starter,int camera){
    switch(before.handler){
    case AirHandler::Intro:case AirHandler::Rise:
        return 184+camera+airMoveWork(before.y,before.params[0])
            +(before.handler==AirHandler::Intro?96:0)+(before.params[0]==255?264:0);
    case AirHandler::Return:{
        int dx=static_cast<int16_t>(before.x-game.returnX),dy=static_cast<int16_t>(before.y-game.returnY);
        return 544+camera+(dx?dx>0?24:28:0)+(dy?dy>0?24:28:0)
            +airMoveWork(before.x,dx>0?-16:dx<0?16:0)+airMoveWork(before.y,dy>0?-16:dy<0?16:0)
            +(!dx&&!dy?152:0);
    }
    case AirHandler::Idle:return 16;
    case AirHandler::BeginFinish:return 140+(game.finishTimer==0?48:0);
    case AirHandler::FinishDelay:return 44+(game.finishTimer==0?48:0);
    case AirHandler::FinishMotion:return game.complexBodyWorkCycles;
    case AirHandler::Exploding:return game.complexBodyWorkCycles;
    case AirHandler::Wait:return before.params[0]!=1?100:game.complexBodyWorkCycles<0?-1:184+game.complexBodyWorkCycles;
    case AirHandler::Animation:return starter?-1:animation; // Deferred native safeguard is not an original body.
    case AirHandler::Hide:return 292;
    case AirHandler::Breakable:
        return animation+124+(before.params[2]?124+airMoveWork(before.x,before.params[0])+airMoveWork(before.y,before.params[1]):0);
    case AirHandler::Pickup:case AirHandler::Emitter:
    case AirHandler::ExplosionSlow:case AirHandler::ExplosionFast:return animation+52+starter;
    case AirHandler::Countdown:return animation+208+starter;
    case AirHandler::Booster:return 124+starter;
    case AirHandler::Enemy:return animation+starter+264+44+airMoveWork(before.x,before.params[0])
        +292+44+((game.terrainAt(after.x+96,after.y)&0x63)?188:0);
    case AirHandler::Bouncer:return animation+184+starter+(after.alive?0:80);
    case AirHandler::Particle:
        if(before.params[0]==1)return 188;
        return animation+176+airMoveWork(before.y,-16)+starter;
    case AirHandler::FallingPickup:return 84+airMoveWork(before.y,4)+(after.alive?0:96);
    case AirHandler::DebrisLeft:case AirHandler::DebrisRight:{
        int cost=156+airMoveWork(before.x,before.handler==AirHandler::DebrisLeft?-16:16)+airMoveWork(before.y,-32);
        return cost+(before.params[0]==1?96:(game.ticks&7)?44:140);
    }
    default:return -1;
    }
}

// Source-work accounting for 03e4..03ed. Operates on native entities and decoded
// layouts; it neither executes cartridge code nor simulates a CPU. All totals
// are original oscillator T-cycles. See docs/AIR_TIMING.md for validation and
// the missing costs that prevent these partial totals driving the game clock.
inline AirSpriteWork airSpriteWork(const AirGame& game,std::array<int,16>* entityCosts=nullptr,
    std::array<AirSpriteEntityWork,16>* publication=nullptr){
    if(entityCosts)entityCosts->fill(0);
    if(publication)*publication={};
    const bool reverse=!game.reverseSprites;
    auto relative=[](int p,int camera){return static_cast<int16_t>((p&65520)-(camera&65520))/16;};
    auto addCost=[](int value,int offset){return 28+(((value&255)+offset>255)?8:0);};
    auto signedCost=[](int value,int offset){
        bool carry=(value&255)+offset>255;
        return (offset&128)?(carry?48:56):(carry?60:52);
    };
    int cycles=24+88,cursor=reverse?156:0;
    for(int i=0;i<16;++i){
        struct Record {int& total;int start;int* out;~Record(){if(out)*out=total-start;}} record{cycles,cycles,entityCosts?&(*entityCosts)[i]:nullptr};
        const auto& entity=game.entities[i];bool last=i==15;
        cycles+=76; // 1c0c..1c19, with the empty-slot branch not taken.
        if(!entity.alive){cycles+=4+40+(last?12:0);continue;}
        const auto& frame=game.assets.frames[entity.frame];const auto& m=frame.meta;
        int flags=entity.flags;
        cycles+=(entity.frame<12?56:48)+348;
        if(flags&8){cycles+=4+40+(last?12:0);continue;}
        int x=relative(entity.x,game.cameraX),y=relative(entity.y,game.cameraY);
        cycles+=24+132+84+signedCost(x,m[0])+signedCost(y,m[1]);
        x+=static_cast<int8_t>(m[0]);y+=static_cast<int8_t>(m[1]);
        cycles+=72+addCost(x,2*m[6]+16);
        bool rejected=x < -2*m[6]-16||x>176;
        if((x+2*m[6]+16)&65280)cycles+=4;
        else cycles+=32+(rejected?4:0);
        if(!rejected){
            cycles+=44+addCost(x,m[6]+8)+72+addCost(y,2*m[7]+16);
            rejected=y < -2*m[7]-16||y>152;
            if((y+2*m[7]+16)&65280)cycles+=4;
            else cycles+=36+(rejected?4:0);
        }
        if(rejected){
            // 1c7c unwinds the geometry call, then marks/evicts the entity.
            cycles+=(flags&16)?76+52+((flags&4)?112:0)+56:72+48;
            if(last)cycles+=12;
            continue;
        }
        cycles+=72+addCost(y,m[7]+16);x+=m[6]+8;y+=m[7]+16;
        auto* plan=publication?&(*publication)[i]:nullptr;
        if(plan)plan->geometry=cycles-record.start-76;
        for(const auto& piece:frame.pieces){
            int sx=(x+((flags&32)?-piece.x-8:piece.x))&255;
            int sy=(y+((flags&64)?-piece.y-16:piece.y))&255;
            int before=20+((flags&64)?64:56)+((flags&32)?64:56);
            bool writes=sx<168&&sy<152;
            before+=sx>=168?20+28:sy>=152?48+28:44;
            cycles+=before;
            if(writes){cycles+=156;cursor=(cursor+(reverse?-4:4))&255;}
            if(plan)plan->pieces.push_back({before,writes});
        }
        cycles+=32; // End-of-layout return at 1cff.
        if(cursor>=160){cycles+=36+28;if(plan)plan->tail=96;break;}
        cycles+=32+40+(last?12:0);
        if(plan)plan->tail=104+(last?12:0);
    }
    int clear;
    // 1bd5 clears the unused portion of the prepared OAM list, then 03ea
    // switches the data bank. Four written bytes per sprite entry.
    if(reverse)clear=cursor>156?172:316+8*cursor;
    else clear=cursor>=160?168:1552-8*cursor;
    return {cycles,clear};
}
}
