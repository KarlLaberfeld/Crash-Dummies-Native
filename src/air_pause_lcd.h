#pragma once
#include "air_clock.h"
#include <algorithm>
#include <array>

namespace ticd {
// Bounded steady-frame DMG graphics readiness candidate, not a CPU emulator.
// Geometry/scroll come from native publication. The first LCD-on frame and
// changing geometry are deliberately outside this owner's scope. Normal-line
// Geometry durations follow published DMG scrolling/window/OBJ rules. The
// counter-wait phase and inclusive edges are derived from the pinned reference
// event ordering; those conventions are not yet qualified against hardware.
struct AirPauseLcd {
    struct Object {int x=0,y=0;};
    std::array<Object,40> objects{};
    int scrollX=0,windowX=7,windowY=136;
    bool enabled=true,objectsEnabled=true,windowEnabled=true;
    int transferEnd(int line) const {
        if(line<0||line>=144)return -1;
        bool window=windowEnabled&&line>=windowY;
        if(window&&(windowX<7||windowX>165))return -1; // Special WX edges.
        int end=256+(scrollX&7)+(window?6:0);
        if(!objectsEnabled||line>=136)return end;
        std::array<int,10> selected{};int count=0;
        for(int i=0;i<40&&count<10;++i){
            int top=objects[i].y-16;
            if(line>=top&&line<top+16)selected[count++]=i;
        }
        // The line-135 STAT handler disables objects mid-transfer. That write
        // needs a fetch owner when objects overlap; a whole-line guess rejects.
        if(line==135&&count)return -1;
        std::sort(selected.begin(),selected.begin()+count,[&](int a,int b){
            return objects[a].x==objects[b].x?a<b:objects[a].x<objects[b].x;
        });
        std::array<int,10> tiles{};int used=0;
        for(int n=0;n<count;++n){
            int x=objects[selected[n]].x;
            if(x<0||x>255)return -1;
            if(x>=168)continue; // Selected, but never fetched on this line.
            if(!x){end+=11;continue;}
            int pixel=x-8;bool inWindow=window&&pixel>=windowX-7;
            int position=inWindow?pixel-(windowX-7):pixel+scrollX;
            int fraction=position&7;
            int tile=(position-fraction)/8+(inWindow?1024:0);
            bool seen=false;for(int i=0;i<used;++i)seen|=tiles[i]==tile;
            if(!seen){tiles[used++]=tile;end+=std::max(5-fraction,0);}
            end+=6;
        }
        return end;
    }
    int mode(int64_t time) const {
        if(!enabled)return 0;
        if(time<AirClock::Frame)return -1; // LCD-enable/first-line owner pending.
        // Experimental clock deadlines identify counter-wait IRQ acceptance,
        // not the earlier graphics-line boundary. The independent DMG source
        // asserts VBlank five dots into the line; aligned DMG HALT polling
        // samples that request and completes its remaining half-step three
        // dots later. This bounded post-wait owner is 5+3 dots ahead. It must
        // not be generalized to arbitrary instruction/IRQ acceptance.
        int position=static_cast<int>((time+5+3)%AirClock::Frame),line=position/456,dot=position%456;
        if(line>=144)return 1;
        int end=transferEnd(line);if(end<0)return -1;
        // The pinned independent observer exposes the completed edge before
        // advancing its graphics state (its sleep boundary is inclusive).
        // This reference-edge convention still needs hardware qualification.
        if(dot<=4||dot>end)return 0;
        return dot<=84?2:3;
    }
    bool readable(int64_t time) const {return accessible(time,80);}
    bool writable(int64_t time) const {return accessible(time,84);}
private:
    bool accessible(int64_t time,int blockStart) const {
        if(!enabled)return true;
        if(time<AirClock::Frame)throw std::runtime_error("Unreconstructed first-frame LCD access");
        int position=static_cast<int>((time+5+3)%AirClock::Frame),line=position/456,dot=position%456;
        if(line>=144)return true;
        int end=transferEnd(line);if(end<0)throw std::runtime_error("Unreconstructed pause graphics transfer");
        return dot<=blockStart||dot>end;
    }
};
}
