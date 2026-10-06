#pragma once
#include "air_pause_clock.h"
#include <algorithm>
#include <fstream>
#include <string>

namespace ticd {
struct AirPauseAssets {
    std::array<unsigned char,128> font{},restoreFont{};
    std::array<unsigned char,20> text{};
    static AirPauseAssets load(const char* path){
        std::ifstream input(path,std::ios::binary);std::array<char,8> magic{};AirPauseAssets assets;
        input.read(magic.data(),magic.size());
        if(std::string(magic.data(),magic.size())!="TICDPA01")throw std::runtime_error("Missing/invalid local pause assets");
        auto read=[&](auto& data){if(!input.read(reinterpret_cast<char*>(data.data()),data.size()))throw std::runtime_error("Truncated local pause assets");};
        read(assets.font);read(assets.restoreFont);read(assets.text);
        char extra;if(input.get(extra))throw std::runtime_error("Trailing local pause assets");return assets;
    }
};
struct AirPauseGraphics {
    std::array<unsigned char,20> row{},saved{};
    std::array<unsigned char,128> font{};
};
// The identified pause session, for the bounded candidate clock. Display and
// audio ownership belong to the caller's actual native state. Unknown graphics
// edges reject, never become allowances. Protected service handoffs follow
// the two identified short source sections and their delayed-enable follower;
// a pending crossing still needs an independent original witness.
template<class Display,class Lcd,class Audio,class Phase,class Bus,class Snapshot>
void airPauseSession(AirClock& clock,DisplayInput& input,AirPauseGraphics& graphics,
                     const AirPauseAssets& assets,Display&& display,Lcd& lcd,
                     Audio&& audio,Phase&& phase,Bus&& bus,Snapshot&& snapshot){
    const char* owner="entry";
    auto quietProtected=[&](int cost,int follower){
        if(clock.now+cost+follower>=std::min(clock.nextStat,clock.nextVBlank))
            throw std::runtime_error("Unqualified pending Air pause handoff");
    };
    auto status=[&](int64_t time){int mode=lcd.mode(time);bus(owner,"read",0xff41,mode,time);return mode;};
    auto write=[&](unsigned address,unsigned char value,int64_t time){
        if(address>=0xc0a0&&address<0xc0b4){graphics.saved[address-0xc0a0]=value;return;}
        if(!lcd.writable(time))throw std::runtime_error("Native pause graphics write is blocked");
        if(address>=0x9c00&&address<0x9c14)graphics.row[address-0x9c00]=value;
        else if(address>=0x8f80&&address<0x9000)graphics.font[address-0x8f80]=value;
        else throw std::runtime_error("Unowned native pause graphics destination");
        bus(owner,"write",address,value,time);
    };
    auto copy=[&](const char* name,int size,unsigned destination,int source){
        owner=name;auto start=clock.now;
        auto result=airPauseCopy(clock,size,destination,display,status,[&](int i,int64_t time){
            if(source==0){
                if(!lcd.readable(time))throw std::runtime_error("Native pause saved-row read is blocked");
                bus(owner,"read",0x9c00+i,graphics.row[i],time);return graphics.row[i];
            }
            return source==1?assets.font[i]:source==2?graphics.saved[i]:assets.restoreFont[i];
        },write);
        phase(owner,start,clock.now,result.cycles);
    };
    quietProtected(192,12);
    snapshot("enter",clock.now,graphics);clock.holdServices(192);audio(true);
    // 1491's enable takes effect after 1492's 12-cycle copy-source setup.
    // The remaining destination/size/call prefix still owns 48 cycles.
    clock.resumeServices(12,display,false);
    clock.work(48,display,false);copy("copy0",20,0xc0a0,0);
    clock.work(68,display,false);copy("copy1",128,0x8f80,1);
    owner="script";auto start=clock.now;
    auto text=airPauseText(clock,assets.text,display,status,write);
    phase(owner,start,clock.now,text.cycles);snapshot("wait",clock.now,graphics);
    for(int waits=0;;++waits){
        if(waits>=1000000)throw std::runtime_error("Pause counter waits did not complete");
        owner="wait";start=clock.now;clock.wait(display,false);
        phase(owner,start,clock.now,clock.lastWaitWork);
        start=clock.now;bool resume=input.pressed&8;int work=resume?28:32;
        clock.work(work,display,false);phase("wake",start,clock.now,work);
        if(resume)break;
    }
    clock.work(60,display,false);copy("copy2",20,0x9c00,2);
    clock.work(68,display,false);copy("copy3",128,0x8f80,3);
    quietProtected(140,16);
    snapshot("restoreAudio",clock.now,graphics);
    start=clock.now;clock.holdServices(140);audio(false);phase("restoreAudio",start,clock.now,140);
    // 14f0's enable takes effect after 14f1's return has completed. Pending
    // callbacks therefore see restored selector/audio and the caller boundary.
    start=clock.now;clock.resumeServices(16,display,false);phase("return",start,clock.now,16);
}
}
