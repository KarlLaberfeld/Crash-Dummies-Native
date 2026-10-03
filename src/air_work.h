#pragma once
#include "air.h"

namespace ticd {
struct AirSpriteWork {int prepare=0,clear=0;};

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
