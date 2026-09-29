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

namespace {
std::unique_ptr<ticd::Assets> assets;
std::unique_ptr<ticd::Game> game;
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
    game->render();for(size_t i=0;i<game->screen.size();++i)pixels[i]=palette[game->screen[i]&3];
    BITMAPINFO info={};info.bmiHeader.biSize=sizeof(BITMAPINFOHEADER);info.bmiHeader.biWidth=160;info.bmiHeader.biHeight=-144;
    info.bmiHeader.biPlanes=1;info.bmiHeader.biBitCount=32;info.bmiHeader.biCompression=BI_RGB;
    SetStretchBltMode(dc,COLORONCOLOR);
    StretchDIBits(dc,gx,gy,160*scale,144*scale,0,0,160,144,pixels,&info,DIB_RGB_COLORS,SRCCOPY);
    const wchar_t* difficulty[]={L"LEICHT",L"NORMAL",L"SCHWER",L"SEHR SCHWER"};
    std::wstring status=L"DACHSTUNT   /   ";status+=difficulty[game->difficulty];
    label(dc,gx,gy+144*scale+16,600,28,status.c_str(),RGB(224,238,205),smallFont);
    if(side){
        int sx=w-side;
        label(dc,sx,102,240,30,L"ROOF JUMP",RGB(224,238,205),headingFont);
        label(dc,sx,148,232,136,L"Pfeiltasten  Bewegen / Haltung\nZ oder A      Abspringen\nX oder S      Zweite Aktion\nEnter            Stunt starten\nEsc               Pause / weiter\nR                   Neustart\n1 - 4             Schwierigkeit",RGB(193,207,197),bodyFont);
        label(dc,sx,322,232,32,L"ORIGINALDATEN",RGB(224,238,205),smallFont);
        label(dc,sx,353,232,96,L"Grafiken und Objektlisten stammen aus deiner ROM. Die Spiellogik wird als C++ direkt unter Windows ausgefuehrt.",RGB(149,175,162),bodyFont);
        label(dc,sx,465,232,96,L"Noch unvollstaendig: vier weitere Stunts, Ton und Abgleich mit dem Original. Dieser Build ist keine fertige Vollversion.",RGB(218,186,128),bodyFont);
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
    case WM_KILLFOCUS:std::fill(std::begin(keys),std::end(keys),false);if(game->started)game->paused=true;return 0;
    case WM_KEYUP:if(wp<256)keys[wp]=false;return 0;
    case WM_KEYDOWN:
        if(wp<256)keys[wp]=true;
        if(lp&(1LL<<30))return 0;
        if(wp==VK_RETURN){if(!game->started||game->result){game->start(game->difficulty);}else game->paused=!game->paused;}
        if(wp=='R'){game->start(game->difficulty);}
        if(wp==VK_ESCAPE&&game->started)game->paused=!game->paused;
        if(wp>='1'&&wp<='4'){game->difficulty=static_cast<int>(wp-'1');if(game->started)game->start(game->difficulty);}
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
        int argc=0;LPWSTR* argv=CommandLineToArgvW(GetCommandLineW(),&argc);
        bool tests=argc>1&&std::wstring(argv[1])==L"--self-test";
        bool capture=argc>1&&std::wstring(argv[1])==L"--capture";
        bool smoke=argc>1&&std::wstring(argv[1])==L"--smoke-test";
        LocalFree(argv);
        if(tests)return ticd::runSelfTests(*assets);
        if(capture){
            game->render();ticd::saveBmp(directory+L"launcher.bmp",game->screen);
            game->start(0);for(int i=0;i<950;++i)game->step(i>400?ticd::A:0);
            game->render();ticd::saveBmp(directory+L"roof-jump.bmp",game->screen);return 0;
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
            while(accumulator>=step){game->step(buttons());accumulator-=step;changed=true;if(smoke&&++smokeTicks==10)DestroyWindow(window);}
            if(changed)InvalidateRect(window,nullptr,FALSE);
            MsgWaitForMultipleObjectsEx(0,nullptr,1,QS_ALLINPUT,MWMO_INPUTAVAILABLE);
        }
        DeleteObject(headingFont);DeleteObject(bodyFont);DeleteObject(smallFont);return 0;
    }catch(const std::exception& e){MessageBoxA(nullptr,e.what(),"Crash Dummies - Startfehler",MB_ICONERROR);return 1;}
}
