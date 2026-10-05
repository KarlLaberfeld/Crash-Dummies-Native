#pragma once
#include "air.h"
#include "air_clock.h"

namespace ticd {
// The identified eight-record placement scan, with explicit range-read owners.
// No CPU/register interpreter. VBlank's progress division shares FF9C with the
// lower bound; CPU register pushes do not protect this shared scratch byte.
struct AirPlacementRange {int low=0,high=0;};
template<class Display>
int airPlacementClock(AirGame& game,AirClock& clock,AirPlacementRange& range,Display&& display){
    if(game.placements.empty())return 0;
    if(game.scan<0||game.scan>=int(game.placements.size()))throw std::runtime_error("Invalid placement scan");
    int total=0,cameraRow=(game.cameraY>>8)&255;
    auto work=[&](int cost){total+=cost;clock.work(cost,display,false);};
    auto write=[&](int cost,auto&& effect){total+=cost;clock.atomicWork(cost,effect,display,false);};
    // 19a2..19ac initializes the shared lower and upper range before wrappers.
    work(12);write(12,[&]{range.low=cameraRow;});
    work(8);write(12,[&]{range.high=(cameraRow+14)&255;});work(8);
    for(int n=0;n<8;++n){
        work(16+24+24); // PUSH BC, wrapper CALL, range-test CALL.
        auto& p=game.placements[game.scan];int row=((p.y>>8)+3)&255;
        work(108); // Identified record coordinate/pointer loads, 19dd..19ef.
        int low=0,high=0;
        write(12,[&]{low=range.low;});work(4);
        if(low>=row)work(20);
        else{
            work(8);write(12,[&]{high=range.high;});work(4);
            if(high<row)work(20);
            else{
                work(8+8+4); // Failed upper return, active-byte read and AND.
                if(p.active)work(20);
                else{
                    work(8+64); // Inactive return, coordinates, allocation CALL.
                    int slot=0;while(slot<16&&game.entities[slot].alive)++slot;
                    work(slot==16?868:816+52*slot);
                    if(slot<16){
                        int allocated=game.spawn(p.kind,p.x,p.y,game.scan);
                        if(allocated!=slot)throw std::runtime_error("Placement allocation ownership changed");
                        p.active=true;work(92);
                    }else work(32);
                }
            }
        }
        // Pointer advance and source table wrap do not read the range scratch.
        work(132);if(game.scan+1==int(game.placements.size()))work(84);
        game.scan=(game.scan+1)%int(game.placements.size());
        work(12+4+(n==7?8:12)); // POP BC, DEC B, loop branch.
    }
    work(16);game.placementWorkCycles=total;return total;
}
}
