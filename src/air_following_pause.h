#pragma once
#include "air_following_gameplay.h"
#include "air_pause_session.h"
#include "air_pause_lcd.h"
#include <memory>

namespace ticd {
// The established steady-frame pause geometry is relative to this new LCD
// epoch. It does not borrow the initial main game's old zero epoch.
struct AirFollowingPauseLcd:AirPauseLcd {
    int64_t epoch=0;
    int mode(int64_t cycle)const{return AirPauseLcd::mode(cycle-epoch);}
    bool readable(int64_t cycle)const{return AirPauseLcd::readable(cycle-epoch);}
    bool writable(int64_t cycle)const{return AirPauseLcd::writable(cycle-epoch);}
};
template<class Service,class Phase,class Bus,class Snapshot>
void airFollowingEntryPause(AirClock& clock,AirFollowingSetup& state,const AirGame& preceding,NativeAudio& sound,
    const AirPauseAssets& assets,Service&& service,Phase&& phase,Bus&& bus,Snapshot&& snapshot,std::function<int()> sampleInput){
    auto& t=state.instruction.map.campaign.timing;
    if(state.stage!=1||state.display!=4||state.ready||!(t.input.pressed&8)||sound.pendingEffect!=-1||!sampleInput)
        throw std::runtime_error("Unowned following first-entry pause");
    auto game=std::make_unique<AirGame>(preceding.assets,preceding.shared);airFollowingAirHandoff(*game,preceding,state);
    AirFollowingPauseLcd lcd;lcd.epoch=t.lcdEpoch;lcd.scrollX=(state.cameraX>>4)&255;
    AirPauseGraphics graphics;graphics.row=game->hudMap;graphics.font=assets.restoreFont;const auto row=graphics.row;
    auto display=[&](bool ready){
        if(ready||state.display!=1||state.ready||!sound.paused)throw std::runtime_error("Unowned following paused display gate");
        int raw=sampleInput();if(raw<0||raw>255||(raw&15)==15)throw std::runtime_error("Unowned following pause reset input");
        t.input.sample(raw);int tick=t.tick;t.tick=(tick+1)&65535;state.lcdc|=2;sound.tick();
        if(sound.effectWorkCycles!=64||sound.musicWorkCycles!=60)throw std::runtime_error("Unowned following pause audio work");
        service(clock.displays,clock.now+20,tick,160,64,60,t.input);return 1592+160+64+60;
    };
    airPauseSession(clock,t.input,graphics,assets,display,lcd,
        [&](bool paused){state.display=paused?1:4;sound.setPaused(paused);},phase,bus,snapshot);
    if(graphics.row!=row||graphics.font!=assets.restoreFont||sound.paused||state.display!=4)
        throw std::runtime_error("Following entry pause did not restore its native graphics/audio");
    state.entryPauseComplete=true;
}
}
