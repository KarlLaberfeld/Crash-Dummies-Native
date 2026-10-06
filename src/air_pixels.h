#pragma once
#include "sprites.h"

namespace ticd {
inline int airPaletteSampleOffset(int owner){
    if(owner<0||owner>2)throw std::runtime_error("Invalid native Air palette owner");
    // 20b9..20c5: separate BGP, OBP1 and OBP0 source accesses, with the
    // pinned bus observer's two-cycle sample convention. No recorded offsets.
    return (owner==1?64:owner==2?36:16)-2;
}
inline int airPixelDot(const SpriteLayer& sprites,int scrollX,int row,int pixel){
    if(scrollX<0||scrollX>255||row<0||row>=Height||pixel<0||pixel>=Width)
        throw std::runtime_error("Invalid native Air pixel boundary");
    if(row>=PlayHeight)return 96+6+pixel; // Fixed WX=7 status window.
    int dot=96+(scrollX&7)+pixel;std::array<int,10> selected{};int count=0;
    for(int i=0;i<40&&count<10;++i){const auto& e=sprites.slots[i];if(e.present&&row>=e.y-16&&row<e.y)selected[count++]=i;}
    std::stable_sort(selected.begin(),selected.begin()+count,[&](int a,int b){return sprites.slots[a].x<sprites.slots[b].x;});
    std::array<int,10> tiles{};int used=0;
    for(int n=0;n<count;++n){int x=sprites.slots[selected[n]].x;
        if(x<0||x>255)throw std::runtime_error("Invalid native Air object coordinate");
        if(x>=168||x-8>pixel)continue;
        if(!x){dot+=11;continue;}
        int position=x-8+scrollX,fraction=position&7,tile=(position-fraction)/8;
        bool seen=false;for(int i=0;i<used;++i)seen|=tiles[i]==tile;
        if(!seen){tiles[used++]=tile;dot+=std::max(5-fraction,0);}dot+=6;
    }
    return dot;
}
// Bounded Air line-135 publication owner, not a general PPU or CPU engine.
// The source STAT handler clears OBJ enable while the final play row is still
// drawing. A selected object's fetch contributes its documented geometric
// stall even if its pixels are transparent. Later pixels retain background.
// The caller supplies its native, source-owned disable edge, never a capture.
inline int airLastLineObjectLimit(const SpriteLayer& sprites,int scrollX,int disableDot){
    if(scrollX<0||scrollX>255||disableDot<0||disableDot>456)
        throw std::runtime_error("Invalid native Air object-disable boundary");
    std::array<int,10> selected{};int count=0;
    for(int i=0;i<40&&count<10;++i){const auto& e=sprites.slots[i];
        if(e.present&&135>=e.y-16&&135<e.y)selected[count++]=i;
    }
    std::stable_sort(selected.begin(),selected.begin()+count,[&](int a,int b){return sprites.slots[a].x<sprites.slots[b].x;});
    int stalls=0,previous=0;std::array<int,10> tiles{};int used=0;
    auto clipped=[&](int end){return std::clamp(disableDot-(96+(scrollX&7)+stalls),previous,end);};
    for(int n=0;n<count;++n){int x=sprites.slots[selected[n]].x;
        if(x<0||x>255)throw std::runtime_error("Invalid native Air object coordinate");
        if(x>=168)continue;
        int position=std::max(x-8,0);
        int limit=clipped(position);if(limit<position)return limit;
        previous=position;
        if(!x)stalls+=11;
        else{
            int shifted=x-8+scrollX,fraction=shifted&7,tile=(shifted-fraction)/8;
            bool seen=false;for(int i=0;i<used;++i)seen|=tiles[i]==tile;
            if(!seen){tiles[used++]=tile;stalls+=std::max(5-fraction,0);}
            stalls+=6;
        }
        // An in-flight object can be cancelled before its first output pixel.
        if(96+(scrollX&7)+stalls+position>=disableDot)return position;
    }
    return clipped(Width);
}
}
