#pragma once
#include <windows.h>
#include <xinput.h>
#include "controller_input.h"

namespace ticd {
class WindowsController {
    HMODULE module=nullptr;
    using GetState=DWORD (WINAPI*)(DWORD,XINPUT_STATE*);
    GetState getState=nullptr;
    int slot=-1;
    ULONGLONG nextScan=0;
public:
    WindowsController(){
        // Only load the Windows component, never a DLL beside the executable.
        for(const wchar_t* name:{L"xinput1_4.dll",L"xinput9_1_0.dll"}){
            module=LoadLibraryExW(name,nullptr,LOAD_LIBRARY_SEARCH_SYSTEM32);
            if(module){getState=reinterpret_cast<GetState>(GetProcAddress(module,"XInputGetState"));
                if(getState)break;FreeLibrary(module);module=nullptr;}
        }
    }
    ~WindowsController(){if(module)FreeLibrary(module);}
    WindowsController(const WindowsController&)=delete;
    WindowsController& operator=(const WindowsController&)=delete;
    ControllerSample poll(){
        if(!getState)return {};
        XINPUT_STATE state{};
        if(slot>=0){
            if(getState(static_cast<DWORD>(slot),&state)==ERROR_SUCCESS)
                return {slot,state.Gamepad.wButtons,state.Gamepad.sThumbLX,state.Gamepad.sThumbLY};
            slot=-1;nextScan=GetTickCount64()+500;
            return {}; // Publish disconnect before selecting a replacement.
        }
        auto now=GetTickCount64();if(now<nextScan)return {};
        nextScan=now+1000;
        for(DWORD i=0;i<XUSER_MAX_COUNT;++i)if(getState(i,&state)==ERROR_SUCCESS){
            slot=static_cast<int>(i);
            return {slot,state.Gamepad.wButtons,state.Gamepad.sThumbLX,state.Gamepad.sThumbLY};
        }
        return {};
    }
};
}
