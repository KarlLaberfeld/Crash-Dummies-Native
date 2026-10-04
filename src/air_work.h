#pragma once
#include "air.h"

namespace ticd {
struct AirSpriteWork {int prepare=0,clear=0;};

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
    if((y>>8)==game.assets.levels[game.difficulty].rows-9)cost+=36;
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
    case AirHandler::Wait:return before.params[0]!=1?100:-1;
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
inline AirSpriteWork airSpriteWork(const AirGame& game){
    const bool reverse=!game.reverseSprites;
    auto relative=[](int p,int camera){return static_cast<int16_t>((p&65520)-(camera&65520))/16;};
    auto addCost=[](int value,int offset){return 28+(((value&255)+offset>255)?8:0);};
    auto signedCost=[](int value,int offset){
        bool carry=(value&255)+offset>255;
        return (offset&128)?(carry?48:56):(carry?60:52);
    };
    int cycles=24+88,cursor=reverse?156:0;
    for(int i=0;i<16;++i){
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
        for(const auto& piece:frame.pieces){
            int sx=(x+((flags&32)?-piece.x-8:piece.x))&255;
            int sy=(y+((flags&64)?-piece.y-16:piece.y))&255;
            cycles+=20+((flags&64)?64:56)+((flags&32)?64:56);
            if(sx>=168)cycles+=20+28;
            else if(sy>=152)cycles+=48+28;
            else{cycles+=44+156;cursor=(cursor+(reverse?-4:4))&255;}
        }
        cycles+=32; // End-of-layout return at 1cff.
        if(cursor>=160){cycles+=36+28;break;}
        cycles+=32+40+(last?12:0);
    }
    int clear;
    // 1bd5 clears the unused portion of the prepared OAM list, then 03ea
    // switches the data bank. Four written bytes per sprite entry.
    if(reverse)clear=cursor>156?172:316+8*cursor;
    else clear=cursor>=160?168:1552-8*cursor;
    return {cycles,clear};
}
}
