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
    auto write=[&](int cost,auto&& effect){total+=cost;clock.atomicWork(cost,effect,display,false);};
    // Fixed completion boundaries within identified native operations. These
    // charge source work; they execute no opcodes and hold no CPU state.
    auto boundary=[&](int cost){write(cost,[]{});};
    auto boundaries=[&](std::initializer_list<int> costs){for(int cost:costs)boundary(cost);};
    // 19a2..19ac initializes the shared lower and upper range before wrappers.
    boundary(12);write(12,[&]{range.low=cameraRow;});
    boundary(8);write(12,[&]{range.high=(cameraRow+14)&255;});boundary(8);
    for(int n=0;n<8;++n){
        boundaries({16,24,24}); // Saved loop, wrapper and range-test calls.
        auto& p=game.placements[game.scan];int row=((p.y>>8)+3)&255;
        boundaries({16,4,16,4,8,8,8,8,8,8,8,8,4}); // Record coordinate/pointer loads, 19dd..19ef.
        int low=0,high=0;
        write(12,[&]{low=range.low;});boundary(4);
        if(low>=row)boundary(20);
        else{
            boundary(8);write(12,[&]{high=range.high;});boundary(4);
            if(high<row)boundary(20);
            else{
                boundaries({8,8,4}); // Failed upper return, active-byte read and test.
                if(p.active)boundary(20);
                else{
                    boundaries({8,4,8,4,8,16,24}); // Inactive return, coordinates, allocation call.
                    int slot=0;while(slot<16&&game.entities[slot].alive)++slot;
                    // 1abc's fixed pool scan, then the native actor-definition
                    // copy. Completing each identified access owns IRQ
                    // acceptance; no observed return address selects a path.
                    if(p.kind<18||p.kind>30)throw std::runtime_error("Unowned placement definition lookup");
                    boundaries({12,12});
                    for(int i=0;i<slot;++i)
                        boundaries({8,8,8,4,8,4,i==15?8:12});
                    if(slot==16)boundary(16);
                    else{
                        boundaries({8,8,12});
                        boundaries({16,16,16,4,4,8,4,16,16}); // Retained animation flags, 1acd..1ad9.
                        boundaries({12,4,12,16,4,4,20}); // Kind lookup: bounded table offset has no low-byte carry.
                        boundaries({8,4,8,12,8,12,8,8,12,8,4,8,4,12,8,4,8,4}); // Definition and coordinates.
                        for(int i=0;i<4;++i)boundaries({8,8,8}); // Frame/flags/handler fields.
                        boundaries({16,8});
                        for(int i=0;i<7;++i)boundaries({8,8,8,4,i==6?8:12}); // Seven actor parameters.
                        boundaries({12,12,12,4,16});
                    }
                    if(slot<16){
                        int allocated=game.spawn(p.kind,p.x,p.y,game.scan);
                        if(allocated!=slot)throw std::runtime_error("Placement allocation ownership changed");
                        p.active=true;boundaries({12,8,8,8,8,4,4,4,8,4,8,16});
                    }else boundaries({12,20});
                }
            }
        }
        // Pointer advance and source table wrap do not read the range scratch.
        boundaries({16,4,16,4,12,8,4,16,4,16,8,4}); // Pointer advance, 19b8..19ce.
        if(game.scan+1==int(game.placements.size())){
            boundary(8);boundaries({12,16,4,16,4,16,12,16}); // Sentinel, wrap stores and return.
        }else boundary(20);
        game.scan=(game.scan+1)%int(game.placements.size());
        boundaries({12,4,n==7?8:12}); // Saved loop restore, decrement and branch.
    }
    boundary(16);game.placementWorkCycles=total;return total;
}
}
