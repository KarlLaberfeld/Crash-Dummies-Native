#define WIN32_LEAN_AND_MEAN
#define NOMINMAX
#include <windows.h>
#include <shellapi.h>
#include <algorithm>
#include <chrono>
#include <memory>
#include <stdexcept>
#include <string>
#include "game.h"
#include "air.h"
#include "ski.h"
#include "bomb.h"

namespace {
std::unique_ptr<ticd::Assets> assets;
std::unique_ptr<ticd::Game> game;
std::unique_ptr<ticd::AirAssets> airAssets;
std::unique_ptr<ticd::AirGame> air;
std::unique_ptr<ticd::SkiAssets> skiAssets;
std::unique_ptr<ticd::SkiGame> ski;
std::unique_ptr<ticd::BombAssets> bombAssets;
std::unique_ptr<ticd::BombGame> bomb;
int selectedStunt=0;
bool started(){return selectedStunt==3?bomb->started:selectedStunt==2?ski->started:selectedStunt==1?air->started:game->started;}
bool& paused(){return selectedStunt==3?bomb->paused:selectedStunt==2?ski->paused:selectedStunt==1?air->paused:game->paused;}
int& difficulty(){return selectedStunt==3?bomb->difficulty:selectedStunt==2?ski->difficulty:selectedStunt==1?air->difficulty:game->difficulty;}
int result(){return selectedStunt==3?bomb->result:selectedStunt==2?ski->result:selectedStunt==1?air->result:game->result;}
void restart(){if(selectedStunt==3)bomb->start(bomb->difficulty);else if(selectedStunt==2)ski->start(ski->difficulty);else if(selectedStunt==1)air->start(air->difficulty);else game->start(game->difficulty);}
bool keys[256]{};
HFONT headingFont,bodyFont,smallFont;
uint32_t pixels[ticd::Width*ticd::Height];
const uint32_t palette[]={0xe0eecd,0x8dac74,0x395841,0x111f1d};
std::wstring appDirectory() {
    wchar_t buffer[32768];DWORD n=GetModuleFileNameW(nullptr,buffer,32768);
    if(!n||n==32768)throw std::runtime_error("Programmpfad ist zu lang.");
    std::wstring p(buffer,n);return p.substr(0,p.find_last_of(L"\\/")+1);
}
void label(HDC dc,int x,int y,int w,int h,const wchar_t* text,COLORREF color,HFONT font) {
    SelectObject(dc,font);SetTextColor(dc,color);SetBkMode(dc,TRANSPARENT);
    RECT r={x,y,x+w,y+h};DrawTextW(dc,text,-1,&r,DT_LEFT|DT_WORDBREAK|DT_NOPREFIX);
}
void paint(HWND hwnd,HDC dc) {
    RECT r;GetClientRect(hwnd,&r);int w=r.right,h=r.bottom;
    HBRUSH bg=CreateSolidBrush(RGB(17,24,26));FillRect(dc,&r,bg);DeleteObject(bg);
    int side=w>=800?260:0;
    int scale=std::max(1,std::min((w-side-48)/160,(h-160)/144));
    int gx=(w-side-160*scale)/2,gy=100;
    label(dc,24,18,w-48,36,L"THE INCREDIBLE CRASH DUMMIES",RGB(224,238,205),headingFont);
    label(dc,24,57,w-48,26,L"Native Windows-Portierung  /  Entwicklungsstand 0.1",RGB(149,175,162),smallFont);
    if(selectedStunt==3)bomb->render();else if(selectedStunt==2)ski->render();else if(selectedStunt==1)air->render();else game->render();
    const auto& screen=selectedStunt==3?bomb->screen:selectedStunt==2?ski->screen:selectedStunt==1?air->screen:game->screen;
    for(size_t i=0;i<screen.size();++i)pixels[i]=palette[screen[i]&3];
    BITMAPINFO info={};info.bmiHeader.biSize=sizeof(BITMAPINFOHEADER);info.bmiHeader.biWidth=160;info.bmiHeader.biHeight=-144;
    info.bmiHeader.biPlanes=1;info.bmiHeader.biBitCount=32;info.bmiHeader.biCompression=BI_RGB;
    SetStretchBltMode(dc,COLORONCOLOR);
    StretchDIBits(dc,gx,gy,160*scale,144*scale,0,0,160,144,pixels,&info,DIB_RGB_COLORS,SRCCOPY);
    const wchar_t* difficulties[]={L"LEICHT",L"NORMAL",L"SCHWER",L"SEHR SCHWER"};
    std::wstring status=selectedStunt==3?L"BOMB FACTORY   /   ":selectedStunt==2?L"SKI SLOPE   /   ":selectedStunt==1?L"AIR BUMPER   /   ":L"ROOF JUMP   /   ";status+=difficulties[difficulty()];
    label(dc,gx,gy+144*scale+16,600,28,status.c_str(),RGB(224,238,205),smallFont);
    if(side){
        int sx=w-side;
        label(dc,sx,102,240,30,selectedStunt==3?L"BOMB FACTORY":selectedStunt==2?L"SKI SLOPE":selectedStunt==1?L"AIR BUMPER":L"ROOF JUMP",RGB(224,238,205),headingFont);
        label(dc,sx,148,232,162,selectedStunt==3?
            L"Links / rechts  Band waehlen\nOben / unten  Bewegen\nZ oder A          Entschaerfen\nX oder S          Schlagen\nEnter / Esc     Start / Pause\nR / 1 - 4           Neustart / Stufe\nF1 - F4             Stunt waehlen":selectedStunt==2?
            L"Links / rechts  Lenken\nPfeil unten      Geradeaus\nZ oder A          Springen\nX oder S          Beschleunigen\nEnter / Esc     Start / Pause\nR / 1 - 4           Neustart / Stufe\nF1 - F4             Stunt waehlen":selectedStunt==1?
            L"Links / rechts  Neigen\nZ oder A          Aufsteigen\nX oder S          Absteigen\nEnter / Esc     Start / Pause\nR                       Neustart\n1 - 4                 Schwierigkeit\nF1 - F4             Stunt waehlen":
            L"Pfeiltasten  Bewegen / Haltung\nZ oder A      Abspringen\nX oder S      Zweite Aktion\nEnter / Esc  Start / Pause\nR                   Neustart\n1 - 4             Schwierigkeit\nF1 - F4         Stunt waehlen",RGB(193,207,197),bodyFont);
        label(dc,sx,322,232,32,L"ORIGINALDATEN",RGB(224,238,205),smallFont);
        label(dc,sx,353,232,96,L"Grafiken und Objektlisten stammen aus deiner ROM. Die Spiellogik wird als C++ direkt unter Windows ausgefuehrt.",RGB(149,175,162),bodyFont);
        label(dc,sx,465,232,96,L"Noch unvollstaendig: Cruise Missile, Originalmenues, Ton und Originalabgleich. Dieser Build ist keine fertige Vollversion.",RGB(218,186,128),bodyFont);
    }
}
LRESULT CALLBACK windowProc(HWND hwnd,UINT msg,WPARAM wp,LPARAM lp) {
    switch(msg){
    case WM_ERASEBKGND:return 1;
    case WM_PAINT:{PAINTSTRUCT ps;HDC dc=BeginPaint(hwnd,&ps);RECT r;GetClientRect(hwnd,&r);
        HDC back=CreateCompatibleDC(dc);HBITMAP bitmap=CreateCompatibleBitmap(dc,r.right,r.bottom);HGDIOBJ old=SelectObject(back,bitmap);
        paint(hwnd,back);BitBlt(dc,0,0,r.right,r.bottom,back,0,0,SRCCOPY);SelectObject(back,old);DeleteObject(bitmap);DeleteDC(back);EndPaint(hwnd,&ps);return 0;}
    case WM_SIZE:InvalidateRect(hwnd,nullptr,FALSE);return 0;
    case WM_GETMINMAXINFO:{auto* m=reinterpret_cast<MINMAXINFO*>(lp);m->ptMinTrackSize={420,450};return 0;}
    case WM_KILLFOCUS:std::fill(std::begin(keys),std::end(keys),false);if(started())paused()=true;return 0;
    case WM_KEYUP:if(wp<256)keys[wp]=false;return 0;
    case WM_KEYDOWN:
        if(wp<256)keys[wp]=true;
        if(lp&(1LL<<30))return 0;
        if(wp==VK_RETURN){if(!started()||result())restart();else paused()=!paused();}
        if(wp=='R')restart();
        if(wp==VK_ESCAPE&&started())paused()=!paused();
        if(wp>='1'&&wp<='4'){difficulty()=static_cast<int>(wp-'1');if(started())restart();}
        if(wp>=VK_F1&&wp<=VK_F4){if(started())paused()=true;selectedStunt=static_cast<int>(wp-VK_F1);std::fill(std::begin(keys),std::end(keys),false);}
        InvalidateRect(hwnd,nullptr,FALSE);return 0;
    case WM_DESTROY:PostQuitMessage(0);return 0;
    }
    return DefWindowProcW(hwnd,msg,wp,lp);
}
int buttons(){return (keys[VK_RIGHT]?ticd::Right:0)|(keys[VK_LEFT]?ticd::Left:0)|(keys[VK_UP]?ticd::Up:0)|(keys[VK_DOWN]?ticd::Down:0)|((keys['Z']||keys['A'])?ticd::A:0)|((keys['X']||keys['S'])?ticd::B:0);}
}

int WINAPI wWinMain(HINSTANCE instance,HINSTANCE,PWSTR,int show) {
    try {
        auto directory=appDirectory();
        assets=std::make_unique<ticd::Assets>(ticd::Assets::load(directory+L"crash.dat"));
        game=std::make_unique<ticd::Game>(*assets);
        airAssets=std::make_unique<ticd::AirAssets>(ticd::AirAssets::load(directory+L"air.dat"));
        air=std::make_unique<ticd::AirGame>(*airAssets,*assets);
        skiAssets=std::make_unique<ticd::SkiAssets>(ticd::SkiAssets::load(directory+L"ski.dat"));
        ski=std::make_unique<ticd::SkiGame>(*skiAssets,*assets);
        bombAssets=std::make_unique<ticd::BombAssets>(ticd::BombAssets::load(directory+L"bomb.dat"));
        bomb=std::make_unique<ticd::BombGame>(*bombAssets,*assets);
        int argc=0;LPWSTR* argv=CommandLineToArgvW(GetCommandLineW(),&argc);
        bool tests=argc>1&&std::wstring(argv[1])==L"--self-test";
        bool capture=argc>1&&std::wstring(argv[1])==L"--capture";
        bool smoke=argc>1&&std::wstring(argv[1])==L"--smoke-test";
        LocalFree(argv);
        if(tests){int roofResult=ticd::runSelfTests(*assets);int airResult=ticd::runAirTests(*airAssets,*assets);int skiResult=ticd::runSkiTests(*skiAssets,*assets);int bombResult=ticd::runBombTests(*bombAssets,*assets);return roofResult?roofResult:airResult?airResult:skiResult?skiResult:bombResult;}
        if(capture){
            game->render();ticd::saveBmp(directory+L"launcher.bmp",game->screen);
            game->start(0);for(int i=0;i<950;++i)game->step(i>400?ticd::A:0);
            game->render();ticd::saveBmp(directory+L"roof-jump.bmp",game->screen);
            air->render();ticd::saveBmp(directory+L"air-launcher.bmp",air->screen);
            air->start(0);for(int i=0;i<650;++i)air->step(ticd::A);
            air->render();ticd::saveBmp(directory+L"air-bumper.bmp",air->screen);
            ski->start(0);for(int i=0;i<500;++i)ski->step(0);ski->render();ticd::saveBmp(directory+L"ski-slope.bmp",ski->screen);
            bomb->start(0);for(int i=0;i<350;++i)bomb->step(0);bomb->render();ticd::saveBmp(directory+L"bomb-factory.bmp",bomb->screen);return 0;
        }
        SetProcessDPIAware();
        headingFont=CreateFontW(-24,0,0,0,FW_BOLD,0,0,0,DEFAULT_CHARSET,0,0,CLEARTYPE_QUALITY,0,L"Segoe UI");
        bodyFont=CreateFontW(-16,0,0,0,FW_NORMAL,0,0,0,DEFAULT_CHARSET,0,0,CLEARTYPE_QUALITY,0,L"Segoe UI");
        smallFont=CreateFontW(-15,0,0,0,FW_SEMIBOLD,0,0,0,DEFAULT_CHARSET,0,0,CLEARTYPE_QUALITY,0,L"Segoe UI");
        WNDCLASSW wc={};wc.lpfnWndProc=windowProc;wc.hInstance=instance;wc.lpszClassName=L"TICDNativePort";wc.hCursor=LoadCursorW(nullptr,IDC_ARROW);
        if(!RegisterClassW(&wc))throw std::runtime_error("Fensterklasse konnte nicht erstellt werden.");
        HWND window=CreateWindowExW(0,wc.lpszClassName,L"Crash Dummies - Native Port (unvollstaendig)",WS_OVERLAPPEDWINDOW,CW_USEDEFAULT,CW_USEDEFAULT,980,800,nullptr,nullptr,instance,nullptr);
        if(!window)throw std::runtime_error("Fenster konnte nicht erstellt werden.");
        ShowWindow(window,smoke?SW_HIDE:show);
        using Clock=std::chrono::steady_clock;auto previousTime=Clock::now();double accumulator=0;
        // One gameplay update per DMG frame. No emulated CPU, interrupts or PPU.
        constexpr double step=70224.0/4194304.0;
        MSG message={};bool running=true;int smokeTicks=0;
        while(running){
            while(PeekMessageW(&message,nullptr,0,0,PM_REMOVE)){if(message.message==WM_QUIT){running=false;break;}TranslateMessage(&message);DispatchMessageW(&message);}
            if(!running)break;
            auto now=Clock::now();accumulator+=std::min(0.1,std::chrono::duration<double>(now-previousTime).count());previousTime=now;
            bool changed=false;
            while(accumulator>=step){if(selectedStunt==3)bomb->step(buttons());else if(selectedStunt==2)ski->step(buttons());else if(selectedStunt==1)air->step(buttons());else game->step(buttons());accumulator-=step;changed=true;if(smoke&&++smokeTicks==10)DestroyWindow(window);}
            if(changed)InvalidateRect(window,nullptr,FALSE);
            MsgWaitForMultipleObjectsEx(0,nullptr,1,QS_ALLINPUT,MWMO_INPUTAVAILABLE);
        }
        DeleteObject(headingFont);DeleteObject(bodyFont);DeleteObject(smallFont);return 0;
    }catch(const std::exception& e){MessageBoxA(nullptr,e.what(),"Crash Dummies - Startfehler",MB_ICONERROR);return 1;}
}
