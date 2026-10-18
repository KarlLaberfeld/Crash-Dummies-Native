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
#include "cruise.h"
#include "campaign.h"
#include "ui.h"
#include "audio.h"
#include "windows_audio.h"
#include "sprites.h"
#include "windows_controller.h"

namespace ticd { int runPlaythroughTests(const Assets&,const AirAssets&,const SkiAssets&,const BombAssets&,const CruiseAssets&,const UiAssets&); }

namespace {
std::unique_ptr<ticd::Assets> assets;
std::unique_ptr<ticd::Game> game;
std::unique_ptr<ticd::AirAssets> airAssets;
std::unique_ptr<ticd::AirGame> air;
std::unique_ptr<ticd::SkiAssets> skiAssets;
std::unique_ptr<ticd::SkiGame> ski;
std::unique_ptr<ticd::BombAssets> bombAssets;
std::unique_ptr<ticd::BombGame> bomb;
std::unique_ptr<ticd::CruiseAssets> cruiseAssets;
std::unique_ptr<ticd::CruiseGame> cruise;
std::unique_ptr<ticd::UiAssets> uiAssets;
std::unique_ptr<ticd::UiFlow> ui;
std::unique_ptr<ticd::AudioAssets> audioAssets;
std::unique_ptr<ticd::NativeAudio> sound;
bool developerMode=false;
int selectedStunt=0,musicGeneration=0;
bool started(){return selectedStunt==4?cruise->started:selectedStunt==3?bomb->started:selectedStunt==2?ski->started:selectedStunt==1?air->started:game->started;}
bool& paused(){return selectedStunt==4?cruise->paused:selectedStunt==3?bomb->paused:selectedStunt==2?ski->paused:selectedStunt==1?air->paused:game->paused;}
bool videoTickPrepared(){return selectedStunt==4?cruise->videoTickPrepared:selectedStunt==3?bomb->videoTickPrepared:selectedStunt==2?ski->videoTickPrepared:selectedStunt==1?air->videoTickPrepared:game->videoTickPrepared;}
int& difficulty(){return selectedStunt==4?cruise->difficulty:selectedStunt==3?bomb->difficulty:selectedStunt==2?ski->difficulty:selectedStunt==1?air->difficulty:game->difficulty;}
int result(){return selectedStunt==4?cruise->result:selectedStunt==3?bomb->result:selectedStunt==2?ski->result:selectedStunt==1?air->result:game->terminalFlags();}
void restart(){++musicGeneration;int player=developerMode?0:ui->campaign.current;if(selectedStunt==4)cruise->start(cruise->difficulty,player);else if(selectedStunt==3)bomb->start(bomb->difficulty,player);else if(selectedStunt==2)ski->start(ski->difficulty,player);else if(selectedStunt==1)air->start(air->difficulty,player);else game->start(game->difficulty,player);}
bool keys[256]{};
bool inputFocused=true;
ticd::ControllerInput controller;
void startAction(){
    if(developerMode){if(!started()||result())restart();else paused()=!paused();}
    else if(ui->phase==ticd::UiPhase::Playing)paused()=!paused();
}
HFONT headingFont,bodyFont,smallFont;
uint32_t pixels[ticd::Width*ticd::Height];
const uint32_t palette[]={0xe0eecd,0x8dac74,0x395841,0x111f1d};
std::wstring appDirectory() {
    wchar_t buffer[32768];DWORD n=GetModuleFileNameW(nullptr,buffer,32768);
    if(!n||n==32768)throw std::runtime_error("Executable path is too long.");
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
    label(dc,24,18,w-48,36,L"CRASH DUMMIES NATIVE",RGB(224,238,205),headingFont);
    label(dc,24,57,w-48,26,L"Native Windows port  /  0.1.0-alpha.1",RGB(149,175,162),smallFont);
    if(selectedStunt==4)cruise->render(developerMode);else if(selectedStunt==3)bomb->render(developerMode);else if(selectedStunt==2)ski->render(developerMode);else if(selectedStunt==1)air->render(developerMode);else game->render(developerMode);
    const auto uiScreen=ui->render();
    auto screen=(!developerMode&&ui->phase!=ticd::UiPhase::Playing)?uiScreen:selectedStunt==4?cruise->screen:selectedStunt==3?bomb->screen:selectedStunt==2?ski->screen:selectedStunt==1?air->screen:game->screen;
    if(!developerMode&&ui->phase==ticd::UiPhase::Playing)screen=ui->renderGameplay(screen,paused());
    for(size_t i=0;i<screen.size();++i)pixels[i]=palette[screen[i]&3];
    BITMAPINFO info={};info.bmiHeader.biSize=sizeof(BITMAPINFOHEADER);info.bmiHeader.biWidth=160;info.bmiHeader.biHeight=-144;
    info.bmiHeader.biPlanes=1;info.bmiHeader.biBitCount=32;info.bmiHeader.biCompression=BI_RGB;
    SetStretchBltMode(dc,COLORONCOLOR);
    StretchDIBits(dc,gx,gy,160*scale,144*scale,0,0,160,144,pixels,&info,DIB_RGB_COLORS,SRCCOPY);
    const wchar_t* difficulties[]={L"EASY",L"NORMAL",L"HARD",L"VERY HARD"};
    std::wstring status=selectedStunt==4?L"CRUISE MISSILE   /   ":selectedStunt==3?L"BOMB FACTORY   /   ":selectedStunt==2?L"SKI SLOPE   /   ":selectedStunt==1?L"AIR BUMPER   /   ":L"ROOF JUMP   /   ";status+=difficulties[difficulty()];
    if(!developerMode&&ui->phase==ticd::UiPhase::Title)status=L"THE INCREDIBLE CRASH DUMMIES";
    label(dc,gx,gy+144*scale+16,600,28,status.c_str(),RGB(224,238,205),smallFont);
    if(side){
        int sx=w-side;
        label(dc,sx,102,240,30,selectedStunt==4?L"CRUISE MISSILE":selectedStunt==3?L"BOMB FACTORY":selectedStunt==2?L"SKI SLOPE":selectedStunt==1?L"AIR BUMPER":L"ROOF JUMP",RGB(224,238,205),headingFont);
        label(dc,sx,148,232,162,
            L"Arrows / D-pad / left stick: move\nZ or A / pad A: action A\nX or S / pad B: action B\nEnter / pad Start: start, pause\nTab / pad Back: Select, options\nEscape: pause\nF6: return to title",
            RGB(193,207,197),bodyFont);
        label(dc,sx,322,232,32,L"EXPERIMENTAL ALPHA",RGB(224,238,205),smallFont);
        label(dc,sx,353,232,96,L"Native C++ game logic. Original graphics and game data are prepared locally from your own ROM.",RGB(149,175,162),bodyFont);
        label(dc,sx,465,232,96,L"Original timing, image and audio comparisons remain incomplete. F1-F5: development stunt selection.",RGB(218,186,128),bodyFont);
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
    case WM_SETFOCUS:inputFocused=true;return 0;
    case WM_KILLFOCUS:inputFocused=false;controller.suspend();std::fill(std::begin(keys),std::end(keys),false);if(started()&&(developerMode||ui->phase==ticd::UiPhase::Playing))paused()=true;return 0;
    case WM_KEYUP:if(wp<256)keys[wp]=false;return 0;
    case WM_KEYDOWN:
        if(wp<256)keys[wp]=true;
        if(lp&(1LL<<30))return 0;
        if(wp==VK_RETURN)startAction();
        if(developerMode){
            if(wp=='R')restart();
            if(wp>='1'&&wp<='4'){difficulty()=static_cast<int>(wp-'1');if(started())restart();}
        }
        if(wp==VK_ESCAPE&&started()&&(developerMode||ui->phase==ticd::UiPhase::Playing))paused()=!paused();
        if(wp>=VK_F1&&wp<=VK_F5){if(started())paused()=true;developerMode=true;selectedStunt=static_cast<int>(wp-VK_F1);std::fill(std::begin(keys),std::end(keys),false);}
        if(wp==VK_F6){developerMode=false;ui->phase=ticd::UiPhase::Title;ui->page=ui->phaseTicks=ui->previous=ui->titleDirection=ui->titleScroll=0;ui->campaign.active=false;std::fill(std::begin(keys),std::end(keys),false);}
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
        uiAssets=std::make_unique<ticd::UiAssets>(ticd::UiAssets::load(directory+L"ui.dat"));
        ui=std::make_unique<ticd::UiFlow>(*uiAssets);
        assets=std::make_unique<ticd::Assets>(ticd::Assets::load(directory+L"crash.dat"));
        game=std::make_unique<ticd::Game>(*assets);
        airAssets=std::make_unique<ticd::AirAssets>(ticd::AirAssets::load(directory+L"air.dat"));
        air=std::make_unique<ticd::AirGame>(*airAssets,*assets);
        skiAssets=std::make_unique<ticd::SkiAssets>(ticd::SkiAssets::load(directory+L"ski.dat"));
        ski=std::make_unique<ticd::SkiGame>(*skiAssets,*assets);
        bombAssets=std::make_unique<ticd::BombAssets>(ticd::BombAssets::load(directory+L"bomb.dat"));
        bomb=std::make_unique<ticd::BombGame>(*bombAssets,*assets);
        cruiseAssets=std::make_unique<ticd::CruiseAssets>(ticd::CruiseAssets::load(directory+L"cruise.dat"));
        cruise=std::make_unique<ticd::CruiseGame>(*cruiseAssets,*assets);
        audioAssets=std::make_unique<ticd::AudioAssets>(ticd::AudioAssets::load(directory+L"audio.dat"));
        sound=std::make_unique<ticd::NativeAudio>(*audioAssets);
        int argc=0;LPWSTR* argv=CommandLineToArgvW(GetCommandLineW(),&argc);
        bool tests=argc>1&&std::wstring(argv[1])==L"--self-test";
        bool capture=argc>1&&std::wstring(argv[1])==L"--capture";
        bool audioSmoke=argc>1&&std::wstring(argv[1])==L"--audio-smoke-test";
        bool noAudioSmoke=argc>1&&std::wstring(argv[1])==L"--ui-no-audio-test";
        bool controllerSmoke=argc>1&&std::wstring(argv[1])==L"--controller-smoke-test";
        bool uiSmoke=controllerSmoke||noAudioSmoke||(argc>1&&std::wstring(argv[1])==L"--ui-smoke-test");
        bool smoke=uiSmoke||audioSmoke||(argc>1&&std::wstring(argv[1])==L"--smoke-test");
        LocalFree(argv);
        if(tests){int roofResult=ticd::runSelfTests(*assets);int airResult=ticd::runAirTests(*airAssets,*assets);int skiResult=ticd::runSkiTests(*skiAssets,*assets);int bombResult=ticd::runBombTests(*bombAssets,*assets);int cruiseResult=ticd::runCruiseTests(*cruiseAssets,*assets);int campaignResult=ticd::runCampaignTests();int uiResult=ticd::runUiTests(*uiAssets);int audioResult=ticd::runAudioTests(*audioAssets);int spriteResult=ticd::runSpriteTests();int playthroughResult=ticd::runPlaythroughTests(*assets,*airAssets,*skiAssets,*bombAssets,*cruiseAssets,*uiAssets);return roofResult?roofResult:airResult?airResult:skiResult?skiResult:bombResult?bombResult:cruiseResult?cruiseResult:campaignResult?campaignResult:uiResult?uiResult:audioResult?audioResult:spriteResult?spriteResult:playthroughResult;}
        if(capture){
            ticd::UiFlow opening(*uiAssets);opening.beginBoot();
            for(int i=0;i<32;++i)opening.step(0);
            ticd::saveBmp(directory+L"boot-copyright.bmp",opening.render());
            for(int i=32;i<244+53;++i)opening.step(0);
            ticd::saveBmp(directory+L"boot-title-closing.bmp",opening.render());
            ticd::UiFlow hidden(*uiAssets);
            for(int key:{ticd::Up,ticd::Down,ticd::Left,ticd::Right}){hidden.step(0);hidden.step(key);}
            for(int i=0;i<81;++i)hidden.step(0);
            ticd::saveBmp(directory+L"password-entry.bmp",hidden.render());
            hidden.phase=ticd::UiPhase::MusicTest;hidden.map=uiAssets->hiddenMaps[3];hidden.testTune=13;hidden.testEffect=25;hidden.step(0);
            ticd::saveBmp(directory+L"music-test.bmp",hidden.render());
            for(int page=0;page<6;++page)ticd::saveBmp(directory+L"title-"+std::to_wstring(page)+L".bmp",ticd::renderTitle(*uiAssets,page,false,0));
            ticd::saveBmp(directory+L"title-transition.bmp",ticd::renderTitle(*uiAssets,1,false,0,-40,false));
            for(int stage=0;stage<5;++stage){
                ticd::UiFlow sample(*uiAssets);sample.campaign.start(false,stage);sample.beginInstructions();
                for(int i=0;i<2500&&!sample.textDone;++i)sample.step(0);
                ticd::saveBmp(directory+L"instructions-"+std::to_wstring(stage)+L".bmp",sample.render());
                sample.step(ticd::UiStart);
                for(int i=0;i<33;++i){if(stage==0&&(i==16||i==32))ticd::saveBmp(directory+L"instruction-exit-"+std::to_wstring(i)+L".bmp",sample.render());sample.step(0);}
                sample.finishStunt(stage==3?0x47:7,123,45,0,20);while(sample.phase==ticd::UiPhase::StuntOutro)sample.step(0);
                for(int i=0;i<32;++i){if(stage==0&&i==16)ticd::saveBmp(directory+L"result-fade-half.bmp",sample.render());sample.step(0);}
                sample.step(0);sample.step(ticd::A);
                ticd::saveBmp(directory+L"result-"+std::to_wstring(stage)+L".bmp",sample.render());
            }
            ticd::UiFlow titleExit(*uiAssets);titleExit.step(ticd::UiStart);
            for(int frame=1;frame<=66;++frame){titleExit.step(0);if(frame==16||frame==32||frame==50||frame==66)ticd::saveBmp(directory+L"title-exit-"+std::to_wstring(frame)+L".bmp",titleExit.render());}
            ticd::UiFlow celebration(*uiAssets);celebration.campaign.start(false);celebration.phase=ticd::UiPhase::Playing;celebration.finishStunt(7,123,45);
            while(celebration.phase==ticd::UiPhase::StuntOutro)celebration.step(0);
            for(int frame=1;frame<=160;++frame){celebration.step(0);if(frame==48||frame==96||frame==160)ticd::saveBmp(directory+L"celebration-"+std::to_wstring(frame)+L".bmp",celebration.render());}
            ticd::UiFlow ending(*uiAssets);ending.campaign.start(false,4,3);ending.beginInstructions();ending.step(ticd::UiStart);for(int i=0;i<33;++i)ending.step(0);
            ending.finishStunt(7,123,45);while(ending.phase==ticd::UiPhase::StuntOutro)ending.step(0);for(int i=0;i<32;++i)ending.step(0);ending.step(0);ending.step(ticd::A);ending.step(0);ending.step(ticd::A);
            for(int i=0;i<65;++i){if(i==16||i==32||i==49)ticd::saveBmp(directory+L"ending-transition-"+std::to_wstring(i)+L".bmp",ending.render());ending.step(0);}
            ticd::saveBmp(directory+L"ending.bmp",ending.render());
            ticd::UiFlow name(*uiAssets);name.campaign.start(false);name.campaign.players[0].savings=100000;name.campaign.players[0].lives=1;
            name.beginInstructions();name.step(ticd::UiStart);for(int i=0;i<33;++i)name.step(0);name.finishStunt(1,0,0);while(name.phase==ticd::UiPhase::StuntOutro)name.step(0);for(int i=0;i<512;++i)name.step(0);
            for(int i=0;i<64;++i){if(i==16||i==32||i==48)ticd::saveBmp(directory+L"name-transition-"+std::to_wstring(i)+L".bmp",name.render());name.step(0);}
            ticd::saveBmp(directory+L"name-entry.bmp",name.render());
            name.nameScroll=172;name.step(ticd::A);
            for(int i=0;i<=145;++i){if(i==0||i==16||i==32||i==80||i==145)ticd::saveBmp(directory+L"title-return-"+std::to_wstring(i)+L".bmp",name.render());if(i<145)name.step(0);}
            game->render();ticd::saveBmp(directory+L"launcher.bmp",game->screen);
            ticd::UiFlow gameplayFade(*uiAssets);gameplayFade.phase=ticd::UiPhase::Playing;game->start(0);
            for(int tick=0;tick<=16;++tick){
                if(tick){gameplayFade.step(0);game->step(0);}
                if(tick==0||tick==8||tick==16){game->render(false);ticd::saveBmp(directory+L"gameplay-fade-"+std::to_wstring(tick)+L".bmp",gameplayFade.renderGameplay(game->screen,false));}
            }
            game->start(0);for(int i=0;i<950;++i)game->step(i>400?ticd::A:0);
            game->render();ticd::saveBmp(directory+L"roof-jump.bmp",game->screen);
            air->render();ticd::saveBmp(directory+L"air-launcher.bmp",air->screen);
            air->start(0);for(int i=0;i<650;++i)air->step(ticd::A);
            air->render();ticd::saveBmp(directory+L"air-bumper.bmp",air->screen);
            ski->start(0);for(int i=0;i<500;++i)ski->step(0);ski->render();ticd::saveBmp(directory+L"ski-slope.bmp",ski->screen);
            game->paused=true;game->render(false);ticd::saveBmp(directory+L"original-pause.bmp",ticd::renderPausedGame(*uiAssets,game->screen));
            bomb->start(0);for(int i=0;i<350;++i)bomb->step(0);bomb->render();ticd::saveBmp(directory+L"bomb-factory.bmp",bomb->screen);
            cruise->start(0);for(int i=0;i<240;++i)cruise->step(ticd::A);cruise->render();ticd::saveBmp(directory+L"cruise-missile.bmp",cruise->screen);return 0;
        }
        ticd::WindowsController controllerDevice;
        ticd::ControllerSample testController;
        ui->beginBoot();
        // The diagnostic uses an invalid identifier to exercise the real
        // waveOutOpen failure path without changing any Windows audio devices.
        ticd::WindowsAudio audioDevice(noAudioSmoke?static_cast<UINT>(-2):WAVE_MAPPER);std::vector<int16_t> audioSamples;
        int lastMusic=-1,lastMusicGeneration=-1;auto lastAudioPhase=ui->phase;
        SetProcessDPIAware();
        headingFont=CreateFontW(-24,0,0,0,FW_BOLD,0,0,0,DEFAULT_CHARSET,0,0,CLEARTYPE_QUALITY,0,L"Segoe UI");
        bodyFont=CreateFontW(-16,0,0,0,FW_NORMAL,0,0,0,DEFAULT_CHARSET,0,0,CLEARTYPE_QUALITY,0,L"Segoe UI");
        smallFont=CreateFontW(-15,0,0,0,FW_SEMIBOLD,0,0,0,DEFAULT_CHARSET,0,0,CLEARTYPE_QUALITY,0,L"Segoe UI");
        WNDCLASSW wc={};wc.lpfnWndProc=windowProc;wc.hInstance=instance;wc.lpszClassName=L"CrashDummiesNative";wc.hCursor=LoadCursorW(nullptr,IDC_ARROW);
        if(!RegisterClassW(&wc))throw std::runtime_error("Could not register the application window class.");
        HWND window=CreateWindowExW(0,wc.lpszClassName,L"Crash Dummies Native - 0.1.0-alpha.1",WS_OVERLAPPEDWINDOW,CW_USEDEFAULT,CW_USEDEFAULT,980,800,nullptr,nullptr,instance,nullptr);
        if(!window)throw std::runtime_error("Could not create the application window.");
        ShowWindow(window,smoke?SW_HIDE:show);
        using Clock=std::chrono::steady_clock;auto previousTime=Clock::now();double accumulator=0;
        // One gameplay update per DMG frame. No emulated CPU, interrupts or PPU.
        constexpr double step=70224.0/4194304.0;
        MSG message={};bool running=true;int smokeTicks=0;
        FILE* uiLog=uiSmoke?_wfopen((directory+(controllerSmoke?L"ui-controller-test.txt":noAudioSmoke?L"ui-window-no-audio-test.txt":L"ui-window-test.txt")).c_str(),L"w"):nullptr;
        bool uiFailed=uiSmoke&&!uiLog;int pausedY=0;
        auto checkWindow=[&](bool ok,const char* label){if(!ok)uiFailed=true;if(uiLog){fprintf(uiLog,"%s: %s\n",ok?"PASS":"FAIL",label);fflush(uiLog);}};
        if(noAudioSmoke)checkWindow(!audioDevice.available(),"Invalid device identifier exercises the audio-open failure path");
        while(running){
            while(PeekMessageW(&message,nullptr,0,0,PM_REMOVE)){if(message.message==WM_QUIT){running=false;break;}TranslateMessage(&message);DispatchMessageW(&message);}
            if(!running)break;
            auto now=Clock::now();accumulator+=std::min(0.1,std::chrono::duration<double>(now-previousTime).count());previousTime=now;
            bool changed=false;
            while(accumulator>=step){
                if(uiSmoke){
                    if(controllerSmoke&&smokeTicks==0)testController.slot=0;
                    auto down=[&](int key){if(controllerSmoke&&key==VK_RETURN)testController.buttons|=0x10;else SendMessageW(window,WM_KEYDOWN,key,0);};
                    auto up=[&](int key){if(controllerSmoke&&key==VK_RETURN)testController.buttons&=~0x10u;else SendMessageW(window,WM_KEYUP,key,0);};
                    switch(smokeTicks){
                    case 380:checkWindow(ui->phase==ticd::UiPhase::Title,"Windows loop completes boot and title opening");down(VK_RETURN);break;
                    case 381:case 501:case 561:case 581:case 641:case 842:case 902:case 962:up(VK_RETURN);break;
                    case 500:checkWindow(ui->phase==ticd::UiPhase::Instructions,"Enter starts campaign instructions");down(VK_RETURN);break;
                    case 550:checkWindow(ui->phase==ticd::UiPhase::Playing&&game->ticks>0,"Enter reaches native Roof gameplay");break;
                    case 560:down(VK_RETURN);pausedY=game->entities[0].y;if(!controllerSmoke)checkWindow(paused(),"Enter pauses gameplay");break;
                    case 580:checkWindow(paused()&&game->entities[0].y==pausedY&&sound->paused,"Pause freezes player and audio sequencer");down(VK_RETURN);break;
                    case 600:checkWindow(!paused()&&!sound->paused,"Enter resumes gameplay and audio");break;
                    case 620:down(VK_F6);break;case 621:case 801:up(VK_F6);break;
                    case 630:checkWindow(ui->phase==ticd::UiPhase::Title&&!ui->campaign.active,"F6 abandons campaign and returns to title");down(VK_F2);break;
                    case 631:up(VK_F2);break;case 640:down(VK_RETURN);break;
                    case 680:checkWindow(developerMode&&selectedStunt==1&&air->started&&air->ticks>0,"Development selection starts native Air through Windows keys");break;
                    case 700:down(VK_ESCAPE);break;case 701:case 713:case 741:up(VK_ESCAPE);break;
                    case 710:checkWindow(paused(),"Escape pauses development gameplay");break;
                    case 712:down(VK_ESCAPE);break;
                    case 720:checkWindow(!paused(),"Escape resumes development gameplay");down('Z');SendMessageW(window,WM_KILLFOCUS,0,0);checkWindow(paused()&&!keys['Z'],"Focus loss pauses and releases held keys");break;
                    case 740:SendMessageW(window,WM_SETFOCUS,0,0);down(VK_ESCAPE);break;
                    case 760:{SetWindowPos(window,nullptr,0,0,420,450,SWP_NOMOVE|SWP_NOZORDER|SWP_NOACTIVATE);RECT r{};GetClientRect(window,&r);checkWindow(r.right>0&&r.bottom>0,"Small window retains a usable drawing area");InvalidateRect(window,nullptr,FALSE);UpdateWindow(window);break;}
                    case 780:SetWindowPos(window,nullptr,0,0,980,800,SWP_NOMOVE|SWP_NOZORDER|SWP_NOACTIVATE);InvalidateRect(window,nullptr,FALSE);UpdateWindow(window);break;
                    case 800:down(VK_F6);break;
                    case 840:down(VK_F3);break;
                    case 841:up(VK_F3);down(VK_RETURN);break;
                    case 880:checkWindow(developerMode&&selectedStunt==2&&ski->started&&ski->ticks>0,"Windows input starts native Ski");break;
                    case 900:down(VK_F4);break;
                    case 901:up(VK_F4);down(VK_RETURN);break;
                    case 940:checkWindow(developerMode&&selectedStunt==3&&bomb->started&&bomb->ticks>0,"Windows input starts native Bomb");break;
                    case 960:down(VK_F5);break;
                    case 961:up(VK_F5);down(VK_RETURN);break;
                    case 1000:checkWindow(developerMode&&selectedStunt==4&&cruise->started&&cruise->ticks>0,"Windows input starts native Cruise");break;
                    case 820:checkWindow(!developerMode&&ui->phase==ticd::UiPhase::Title,"Return from development mode restores campaign title");break;
                    }
                    if(controllerSmoke)switch(smokeTicks){
                    case 390:checkWindow(ui->phase==ticd::UiPhase::TitleExit,"Controller Start leaves title");break;
                    case 565:checkWindow(paused(),"Controller Start pauses once");break;
                    case 610:testController.buttons=0x1008;break;
                    case 611:checkWindow(controller.held==(ticd::A|ticd::Right),"Controller action and movement reach Windows input");testController.buttons=0;break;
                    case 685:testController={};break;
                    case 686:checkWindow(paused()&&!controller.held,"Disconnect pauses gameplay and releases input");testController={0,0x10};break;
                    case 688:checkWindow(paused(),"Held Start on reconnect cannot resume");testController.buttons=0;break;
                    case 690:testController.buttons=0x10;break;
                    case 691:checkWindow(!paused(),"Fresh Start after reconnect resumes");break;
                    case 695:checkWindow(!paused(),"Held Start does not toggle repeatedly");testController.buttons=0;break;
                    case 721:testController.buttons=0x10;break;
                    case 724:SendMessageW(window,WM_SETFOCUS,0,0);break;
                    case 727:checkWindow(paused()&&!controller.held,"Focus regain ignores held controller Start");testController.buttons=0;break;
                    case 825:testController.buttons=0x20;break;
                    case 826:checkWindow(controller.held==ticd::UiSelect&&ui->nextPage==5&&ui->titleDirection!=0,"Controller Back opens options");testController.buttons=0;break;
                    }
                }
                controller.update(smoke?testController:controllerDevice.poll(),inputFocused&&(smoke||GetForegroundWindow()==window));
                if(controller.disconnected&&started()&&(developerMode||ui->phase==ticd::UiPhase::Playing))paused()=true;
                if((controller.pressed&ticd::UiStart)&&!keys[VK_RETURN])startAction();
                int input=buttons()|(controller.held&(ticd::Right|ticd::Left|ticd::Up|ticd::Down|ticd::A|ticd::B));
                if(!developerMode){ui->musicActive=sound->musicPlaying();ui->gameplayPaused=ui->phase==ticd::UiPhase::Playing&&videoTickPrepared();auto before=ui->phase;ui->step(input|(controller.held&(ticd::UiStart|ticd::UiSelect))|(keys[VK_RETURN]?ticd::UiStart:0)|(keys[VK_TAB]?ticd::UiSelect:0));
                    if(before==ticd::UiPhase::Instructions&&ui->phase==ticd::UiPhase::Playing){selectedStunt=ui->stunt;difficulty()=ui->level;restart();
                        if(selectedStunt==4){cruise->secondTicks=ui->timerPhase;cruise->randomState=(ui->ticks&255)<<8;}
                        else if(selectedStunt==3)bomb->randomState=(ui->ticks&255)<<8;
                        else if(selectedStunt==2)ski->secondTicks=ui->timerPhase;
                        else if(selectedStunt==1){air->secondTicks=ui->timerPhase;air->randomState=(ui->ticks&255)<<8;}
                        else game->secondTicks=ui->timerPhase;}}
                if(developerMode||ui->phase==ticd::UiPhase::Playing){
                    auto advance=[&](auto& stunt){if(developerMode)stunt.step(input);else ui->stepStunt(stunt);};
                    if(selectedStunt==4)advance(*cruise);else if(selectedStunt==3)advance(*bomb);
                    else if(selectedStunt==2)advance(*ski);else if(selectedStunt==1)advance(*air);else advance(*game);
                    if(!developerMode&&(result()&1)){
                        if(selectedStunt!=3)ui->timerPhase=selectedStunt==4?cruise->secondTicks:selectedStunt==2?ski->secondTicks:selectedStunt==1?air->secondTicks:game->secondTicks;
                        int pay=selectedStunt==4?cruise->money:selectedStunt==3?bomb->money:selectedStunt==2?ski->money:selectedStunt==1?air->money:game->money;
                        int seconds=selectedStunt==4?cruise->seconds:selectedStunt==3?0:selectedStunt==2?ski->seconds:selectedStunt==1?air->seconds:game->seconds;
                        int lives=selectedStunt==4?cruise->extraLives:selectedStunt==1?air->livesEarned:0;
                        // Preserve the last published scene while blocking waits/fade run.
                        if(selectedStunt==4){cruise->render(false);ui->outroScene=cruise->screen;}
                        else if(selectedStunt==3){bomb->render(false);ui->outroScene=bomb->screen;}
                        else if(selectedStunt==2){ski->render(false);ui->outroScene=ski->screen;}
                        else if(selectedStunt==1){air->render(false);ui->outroScene=air->screen;}
                        else{game->render(false);ui->outroScene=game->screen;}
                        if(selectedStunt==4)ui->randomState=cruise->randomState;else if(selectedStunt==3)ui->randomState=bomb->randomState;else if(selectedStunt==1)ui->randomState=air->randomState;
                        ui->finishStunt(result(),pay,seconds,lives,selectedStunt==2?ski->collected:0);
                        // 0400's final wait publishes the last prepared sprite
                        // list before fading. FFAE is already clear: no extra
                        // dynamic resource-transfer work or gameplay update.
                        auto prepareOutro=[&](auto& stunt){stunt.publishVideo();stunt.render(false);ui->outroNextScene=stunt.screen;};
                        if(selectedStunt==4)prepareOutro(*cruise);else if(selectedStunt==3)prepareOutro(*bomb);
                        else if(selectedStunt==2)prepareOutro(*ski);else if(selectedStunt==1)prepareOutro(*air);else prepareOutro(*game);
                    }
                }
                if(!developerMode&&ui->phase==ticd::UiPhase::StuntOutro){
                    if(selectedStunt==4)ui->refreshStuntOutro(*cruise);else if(selectedStunt==3)ui->refreshStuntOutro(*bomb);
                    else if(selectedStunt==2)ui->refreshStuntOutro(*ski);else if(selectedStunt==1)ui->refreshStuntOutro(*air);else ui->refreshStuntOutro(*game);
                }
                int music=1;
                if(developerMode){if(started())music=8+selectedStunt;}
                else switch(ui->phase){
                case ticd::UiPhase::Boot:music=0;break;
                case ticd::UiPhase::TitleIntro:music=ui->phaseTicks<33?ui->titleIntroMusic:1;break;
                case ticd::UiPhase::TitleReturn:music=ui->titleIntroMusic;break;
                case ticd::UiPhase::Title:music=1;break;
                case ticd::UiPhase::TitleExit:music=1;break;
                case ticd::UiPhase::Instructions:music=ui->instructionEnter==(ui->instructionAlternate?65:33)?-1:2;break;
                case ticd::UiPhase::Playing:music=8+selectedStunt;break;
                case ticd::UiPhase::StuntOutro:music=ui->phaseTicks? -1:8+selectedStunt;break;
                case ticd::UiPhase::Result:music=ui->campaign.last.gameOver?13:ui->campaign.last.success?(ui->campaign.last.perfect?5:4):3;break;
                case ticd::UiPhase::Ending:music=ui->endingEnter>32?-1:13;break;
                case ticd::UiPhase::NameEntry:music=ui->nameEnter>32?13:6;break;
                default:break; // Hidden menus issue explicit music/stop commands.
                }
                bool openingContinues=(lastAudioPhase==ticd::UiPhase::Boot&&ui->phase==ticd::UiPhase::TitleIntro)||(lastAudioPhase==ticd::UiPhase::TitleIntro&&ui->phase==ticd::UiPhase::Title)||
                    (lastAudioPhase==ticd::UiPhase::Title&&ui->phase==ticd::UiPhase::TitleExit)||
                    (lastAudioPhase==ticd::UiPhase::Playing&&ui->phase==ticd::UiPhase::StuntOutro)||
                    ((lastAudioPhase==ticd::UiPhase::Ending||lastAudioPhase==ticd::UiPhase::Result)&&ui->phase==ticd::UiPhase::NameEntry)||
                    (ui->phase==ticd::UiPhase::TitleReturn)||
                    (lastAudioPhase==ticd::UiPhase::TitleReturn&&ui->phase==ticd::UiPhase::TitleIntro);
                bool hiddenAudio=!developerMode&&(ui->phase>=ticd::UiPhase::HiddenTransition||lastAudioPhase>=ticd::UiPhase::HiddenTransition);
                if(hiddenAudio){if(ui->pendingMusic!=-2){if(ui->pendingMusic<0)sound->stop();else sound->playMusic(ui->pendingMusic);lastMusic=ui->pendingMusic;}}
                else if(music!=lastMusic||(ui->phase!=lastAudioPhase&&!openingContinues)||musicGeneration!=lastMusicGeneration){if(music<0)sound->stop();else sound->playMusic(music);lastMusic=music;lastMusicGeneration=musicGeneration;}
                lastAudioPhase=ui->phase;
                if(developerMode||ui->phase==ticd::UiPhase::Playing){int effect=selectedStunt==4?cruise->pendingSound:selectedStunt==3?bomb->pendingSound:selectedStunt==2?ski->pendingSound:selectedStunt==1?air->pendingSound:game->pendingSound;
                    if(effect>=0)sound->queueEffect(effect);}
                if(!developerMode&&ui->pendingSound>=0)sound->queueEffect(ui->pendingSound);
                bool audioPaused=(developerMode||ui->phase==ticd::UiPhase::Playing)&&paused();
                if(audioPaused!=sound->paused)audioDevice.discardQueued();
                sound->setPaused(audioPaused);
                sound->tick();sound->render(audioSamples);audioDevice.submit(audioSamples);
                accumulator-=step;changed=true;if(smoke&&++smokeTicks==(uiSmoke?1040:audioSmoke?300:10))DestroyWindow(window);
            }
            if(changed)InvalidateRect(window,nullptr,FALSE);
            MsgWaitForMultipleObjectsEx(0,nullptr,1,QS_ALLINPUT,MWMO_INPUTAVAILABLE);
        }
        if(smoke){FILE* log=_wfopen((directory+(noAudioSmoke?L"audio-output-no-device.txt":L"audio-output.txt")).c_str(),L"w");if(log){fprintf(log,"Windows output device: %s; dropped buffers: %u\n",audioDevice.available()?"available":"unavailable",audioDevice.droppedFrames);fclose(log);}}
        if(uiLog){fprintf(uiLog,"%s: automated Windows messages; not a human visual acceptance test\n",uiFailed?"FAIL":"PASS");fclose(uiLog);}
        DeleteObject(headingFont);DeleteObject(bodyFont);DeleteObject(smallFont);return uiFailed?1:0;
    }catch(const std::exception& e){MessageBoxA(nullptr,e.what(),"Crash Dummies Native - Startup error",MB_ICONERROR);return 1;}
}
