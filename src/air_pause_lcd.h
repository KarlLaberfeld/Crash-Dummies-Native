#pragma once
#include "air_clock.h"
#include <algorithm>
#include <array>

namespace ticd {
// Bounded steady-frame DMG graphics readiness candidate, not a CPU emulator.
// Geometry/scroll come from native publication. The first LCD-on line and
// changing geometry are outside scope; only the explicit empty-result text
// owner below admits later visible lines in the first frame. Normal-line
// Geometry durations follow published DMG scrolling/window/OBJ rules. The
// counter-wait phase and inclusive edges are derived from the pinned reference
// event ordering; those conventions are not yet qualified against hardware.
struct AirPauseLcd {
    struct Object {int x=0,y=0;};
    std::array<Object,40> objects{};
    int scrollX=0,windowX=7,windowY=136;
    int objectHeight=16,objectDisableLine=135;
    bool enabled=true,objectsEnabled=true,windowEnabled=true;
    // Separately qualified result text: empty OAM, no window/scroll, visible
    // lines after the first restart line. No first-line/access owner implied.
    bool resultFirstVisibleFrame=false;
    // Post-title instruction clear: empty OAM, disabled objects/window and
    // no scroll; also qualifies line 143 and first-frame VBlank. Still no
    // first LCD-on line or nonempty/changing geometry owner.
    bool instructionRestartFrame=false;
    // Separately bounded title readiness at WX=166 on pinned DMG: empty
    // eight-pixel OAM and no horizontal scroll. The window's HBlank edge
    // does not extend visible transfer here; pixels/glitches stay unowned.
    bool titleRightEdge=false;
    int transferEnd(int line) const {return transferEndForGeometry(line,false);}
private:
    int transferEndForGeometry(int line,bool cancellationUpperBound) const {
        if(line<0||line>=144)return -1;
        bool window=windowEnabled&&line>=windowY;
        if(window&&windowX==166&&titleRightEdge&&scrollX==0&&objectHeight==8&&
           std::all_of(objects.begin(),objects.end(),[](const Object& o){return o.x==0&&o.y==0;}))window=false;
        if(window&&(windowX<7||windowX>165))return -1; // Other special WX edges.
        int end=256+(scrollX&7)+(window?6:0);
        if(objectHeight!=8&&objectHeight!=16)return -1;
        if(!objectsEnabled||line>objectDisableLine)return end;
        std::array<int,10> selected{};int count=0;
        for(int i=0;i<40&&count<10;++i){
            int top=objects[i].y-16;
            if(line>=top&&line<top+objectHeight)selected[count++]=i;
        }
        for(int n=0;n<count;++n){
            int x=objects[selected[n]].x;if(x<0||x>255)return -1;
        }
        // The STAT handler can cancel an in-progress object fetch. Its exact
        // shortened transfer remains unowned. A late sample is nevertheless
        // readable after the uninterrupted worst case: each of at most ten
        // selected objects adds at most five alignment dots and six fetch dots.
        // DMG cancellation drops the remaining fetch; it adds no extra work.
        if(line==objectDisableLine&&count)
            return cancellationUpperBound?end+11*count:-1;
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
public:
    int mode(int64_t time) const {
        if(!enabled)return 0;
        if(time<AirClock::Frame&&!(((resultFirstVisibleFrame&&time<143*456)||instructionRestartFrame)&&time>=456&&
            !objectsEnabled&&!windowEnabled&&scrollX==0))return -1;
        // Experimental clock deadlines identify counter-wait IRQ acceptance,
        // not the earlier graphics-line boundary. The independent DMG source
        // asserts VBlank five dots into the line; aligned DMG HALT polling
        // samples that request and completes its remaining half-step three
        // dots later. This bounded post-wait owner is 5+3 dots ahead. It must
        // not be generalized to arbitrary instruction/IRQ acceptance.
        int position=static_cast<int>((time+5+3)%AirClock::Frame),line=position/456,dot=position%456;
        if(line>=144)return 1;
        int end=transferEnd(line);
        if(end<0){
            int bound=transferEndForGeometry(line,true);
            return bound>=0&&dot>bound?0:-1;
        }
        // The pinned independent observer exposes the completed edge before
        // advancing its graphics state (its sleep boundary is inclusive).
        // This reference-edge convention still needs hardware qualification.
        // The first visible line retains VBlank at the frame boundary's
        // inclusive source sample, then enters the short horizontal blank
        // before scanning. Other lines retain horizontal blank throughout.
        if(dot<=4)return line==0&&!dot?1:0;
        if(dot>end)return 0;
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
        int end=transferEnd(line);
        if(end<0){
            int bound=transferEndForGeometry(line,true);
            if(bound>=0&&dot>bound)return true;
            throw std::runtime_error("Unreconstructed pause graphics transfer");
        }
        return dot<=blockStart||dot>end;
    }
};
}
