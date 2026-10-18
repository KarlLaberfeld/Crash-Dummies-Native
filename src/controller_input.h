#pragma once
#include "ui.h"

namespace ticd {
// XInput button bits; conversion is independent of Windows and game state.
struct ControllerSample { int slot=-1; unsigned buttons=0; int x=0,y=0; };
inline int controllerButtons(const ControllerSample& s) {
    constexpr int deadzone=7849;
    int result=0;
    if((s.buttons&0x0008)||s.x>deadzone)result|=Right;
    if((s.buttons&0x0004)||s.x<-deadzone)result|=Left;
    if((s.buttons&0x0001)||s.y>deadzone)result|=Up;
    if((s.buttons&0x0002)||s.y<-deadzone)result|=Down;
    if(s.buttons&0x1000)result|=A;
    if(s.buttons&0x2000)result|=B;
    if(s.buttons&0x0010)result|=UiStart;
    if(s.buttons&0x0020)result|=UiSelect;
    // Conflicting directions are neutral, including stick/D-pad opposition.
    if((result&(Left|Right))==(Left|Right))result&=~(Left|Right);
    if((result&(Up|Down))==(Up|Down))result&=~(Up|Down);
    return result;
}
struct ControllerInput {
    int slot=-1,held=0,pressed=0;
    bool armed=false,disconnected=false;
    void suspend(){held=pressed=0;armed=false;}
    void update(const ControllerSample& sample,bool focused) {
        disconnected=slot>=0&&sample.slot!=slot;
        if(sample.slot!=slot){slot=sample.slot;suspend();}
        pressed=0;
        if(slot<0||!focused){suspend();return;}
        int next=controllerButtons(sample);
        if(!armed){held=0;if(!next)armed=true;return;}
        pressed=next&~held;held=next;
    }
};
}
