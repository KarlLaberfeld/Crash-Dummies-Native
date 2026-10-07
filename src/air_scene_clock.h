#pragma once
#include "air.h"
#include "air_clock.h"
#include "air_map_publication.h"

namespace ticd {
// Identified scene-preparation operations, with source completion boundaries.
// These are fixed native algorithms over decoded layouts and world values;
// no cartridge instructions, register state or observed IRQ returns drive them.
template<class Display> struct AirSceneSteps {
    AirClock& clock; Display& display; int total=0;
    template<class Effect> void write(int cost,Effect&& effect){
        total+=cost;clock.atomicWork(cost,effect,display,false);
    }
    void step(int cost){write(cost,[]{});}
    void steps(std::initializer_list<int> costs){for(int cost:costs)step(cost);}
    void unsignedAdd(int value,int offset){
        steps({4,4});
        if((value&255)+offset>255)steps({8,4,16});else step(20);
    }
    void signedAdd(int value,int offset){
        steps({8,(offset&128)?12:16,4,4});
        bool carry=(value&255)+offset>255;
        if(carry==bool(offset&128))step(20);else steps({8,4,16});
    }
};

template<class Display>
int airSpriteClock(AirGame& game,AirClock& clock,Display&& display){
    AirSceneSteps<Display> s{clock,display};
    auto relative=[](int p,int camera){return static_cast<int16_t>((p&65520)-(camera&65520))/16;};
    // 03e4's call, followed by 1bfb's allocation-direction setup.
    s.steps({24,12,8,12,12,12,8,12,12});
    auto nextEntity=[&](bool last){s.steps({12,4,8,4,last?8:12});if(last)s.step(16);};
    for(int i=0;i<16;++i){
        const auto& e=game.spriteInputEntities[i];bool last=i==15;
        s.steps({16,12,4,4,12,4,8,8,e.alive?8:12});
        if(!e.alive){nextEntity(last);continue;}
        const auto& frame=game.assets.frames.at(e.frame);const auto& m=frame.meta;
        s.steps({16,4,4,e.frame<12?8:12});if(e.frame<12)s.step(12);s.step(12);
        // 1c22/1c40 quantize each camera-relative coordinate by sixteen.
        for(int axis=0;axis<2;++axis){
            s.steps({12,8,4,12,4,8,8,4,4,8,4,4,4});
            for(int shift=0;shift<4;++shift)s.steps({8,4});
            s.step(4);
        }
        s.steps({16,8,8,12,12,12,(e.flags&8)?12:8});
        if(e.flags&8){nextEntity(last);continue;}
        int x=relative(e.x,game.cameraX),y=relative(e.y,game.cameraY);
        // 1cb6's bounded frame-table lookup. The table starts at low byte 0;
        // this release has fewer than 128 frame records, hence no carry.
        if(e.frame<0||e.frame>=128)throw std::runtime_error("Unowned scene frame lookup");
        s.steps({24,12,24,4,16});s.unsignedAdd(0,2*e.frame);s.steps({8,8,4,16});
        s.steps({8,24});s.signedAdd(x,m[0]);x+=static_cast<int8_t>(m[0]);
        s.steps({8,24});s.signedAdd(y,m[1]);y+=static_cast<int8_t>(m[1]);
        s.steps({8,8,8,8,16,8,4,8,16});s.unsignedAdd(x,2*m[6]+16);
        bool rejected=((x+2*m[6]+16)&65280)!=0;
        s.steps({4,4,rejected?16:12});
        if(!rejected){rejected=x>176;s.steps({8,4,8,4,rejected?12:8});}
        if(!rejected){
            s.steps({12,8,8,16});s.unsignedAdd(x,m[6]+8);
            s.steps({16,8,4,8,16});s.unsignedAdd(y,2*m[7]+16);
            rejected=((y+2*m[7]+16)&65280)!=0;
            s.steps({4,4,rejected?16:12});
            if(!rejected){rejected=y>152;s.steps({8,4,8,4,rejected?16:12});}
        }
        if(rejected){
            // 1c7c either marks the offscreen actor or evicts a disposable one.
            s.steps({12,12,12,4,8,4,12,(e.flags&16)?12:8});
            if(e.flags&16){
                s.steps({12,4,12,12,(e.flags&4)?24:12});
                if(e.flags&4)s.steps({16,4,8,4,4,8,8,4,4,12,12,16});
                s.steps({4,8,4,12,8,4,last?12:16});
            }else s.steps({16,4,8,4,last?12:16});
            if(last)s.step(16);
            continue;
        }
        s.steps({12,8,8,16});s.unsignedAdd(y,m[7]+16);s.steps({4,8,12,4});
        x+=m[6]+8;y+=m[7]+16;
        for(const auto& piece:frame.pieces){
            s.steps({8,4,8}); // Nonterminal layout record, 1cfd.
            s.steps({12,8,8,(e.flags&64)?8:12});if(e.flags&64)s.steps({4,8});s.steps({4,12});
            s.steps({12,8,8,(e.flags&32)?8:12});if(e.flags&32)s.steps({4,8});s.steps({4,12});
            int sx=(x+((e.flags&32)?-piece.x-8:piece.x))&255;
            int sy=(y+((e.flags&64)?-piece.y-16:piece.y))&255;
            s.steps({8,sx>=168?12:8});
            if(sx<168)s.steps({12,8,sy>=152?12:8});
            if(sx>=168||sy>=152){s.steps({8,8,12});continue;}
            int slot=game.sprites.preparedSlot();
            auto* entry=slot>=0&&slot<40?&game.sprites.slots[slot]:nullptr;
            s.step(12);s.write(8,[&]{if(entry){entry->y=sy;entry->present=sy!=0;}});
            s.steps({4,12});s.write(8,[&]{if(entry)entry->x=sx;});
            s.steps({4,12,8});s.write(8,[&]{if(entry)entry->colors=e.frame<12&&piece.chunk>=0?game.spriteResources.colors(piece.chunk):piece.colors;});
            s.steps({8,4,12,8});s.write(8,[&]{if(entry)entry->flags=(e.flags&0xe0)^piece.flags;});
            s.steps({8,12,4});s.write(4,[&]{game.sprites.advancePreparedPiece();});s.step(12);
        }
        s.steps({8,4,20}); // Sentinel's taken conditional return.
        // SpriteLayer reports the source cursor via unusedCount as well: the
        // descending cursor wraps to 252 when full, ascending reaches 160.
        bool full=game.sprites.unusedCount()==0;
        s.steps({4,12,8,full?12:8});
        game.sprites.finishPreparedEntity();
        if(full){s.steps({12,16});break;}nextEntity(last);
    }
    return s.total;
}

template<class Display>
int airSpriteClearClock(SpriteLayer& sprites,AirClock& clock,Display&& display){
    AirSceneSteps<Display> s{clock,display};
    int first=sprites.unusedFirst(),bytes=4*sprites.unusedCount();
    s.steps({24,12,8,sprites.descending()?12:8});
    if(sprites.descending())s.steps({12,8,8,bytes?8:20});
    else s.steps({8,12,8,bytes?8:20});
    if(bytes){
        if(sprites.descending())s.step(12);else s.step(4);
        s.steps({12,16});s.unsignedAdd(0x33,160-bytes);s.steps({16,4,16});
        for(int byte=0;byte<bytes;++byte)s.write(8,[&]{if(!(byte&3))sprites.slots[first+byte/4].present=false;});
        s.steps({4,16});
    }
    // 03ea changes back to the placement data bank after clear's return.
    s.steps({8,16,12,16,16});return s.total;
}

template<class Display>
int airMapClock(AirClock& clock,int oldCamera,int camera,bool& transfer,Display&& display,
                bool* flagOwned=nullptr,bool* rowReady=nullptr,AirMapPublication* publication=nullptr,const AirGame* game=nullptr){
    if(bool(publication)!=bool(game))throw std::runtime_error("Incomplete native row publication owner");
    AirSceneSteps<Display> s{clock,display};
    bool changed=((oldCamera^camera)&128)!=0;
    s.steps({12,16,16,4,16,4,4,24,4});
    s.write(16,[&]{transfer=false;if(flagOwned)*flagOwned=true;if(rowReady)*rowReady=!changed;});
    s.steps({16,4,16,4,16,4,16,4,4,16,4,16,4,4,4,4,4,4,4,4});
    s.step(changed?8:20);
    if(changed){
        s.step(8);s.write(16,[&]{transfer=true;});
        s.steps({16,8,4,8,8,4,4,4});
        s.write(16,[&]{if(publication)publication->destination=AirMapPublication::destinationRow(oldCamera);});
        s.steps({12,4,8,4,4,8,4,4,8,8});
        bool down=(static_cast<uint16_t>(oldCamera-camera)&0x8000)!=0;
        s.step(down?8:12);if(down)s.step(8);
        s.steps({8,16,8,4,12,8,8,4,12,8});
        for(int cell=0;cell<16;++cell){s.steps({8,16,4,4,8,4});
            s.write(8,[&]{if(publication)publication->buffer[2*cell]=AirMapPublication::cellTile(*game,oldCamera,camera,cell,0);});
            s.steps({4,8});
            s.write(8,[&]{if(publication)publication->buffer[2*cell+1]=AirMapPublication::cellTile(*game,oldCamera,camera,cell,1);});
            s.steps({4,12,4,cell==15?8:12});}
        s.step(16);if(rowReady)*rowReady=true;
    }
    s.step(16);return s.total;
}
}
