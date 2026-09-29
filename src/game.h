#pragma once
#include <array>
#include <cstdint>
#include <string>
#include <vector>

namespace ticd {
constexpr int Width=160, Height=144, PlayHeight=136;
enum Button { Right=1, Left=2, Up=4, Down=8, A=16, B=32 };
enum class Handler { Idle, IntroPan, IntroRise, IntroAnimation, RoofWait, Falling,
    Timeout, FinishDelay, Animation, Fire, Balloon, Burst, Awning, Puff, Plane,
    PlaneFly, PlaneStun, Platform, LimbLeft, LimbRight, LimbUp, LimbSideRight,
    LimbSideLeft, BackgroundCloud, Burning, Bounce, BalloonRide, Rope, RopeRelease,
    Finish };
struct Frame { std::array<uint8_t,8> meta{}; std::array<uint8_t,96*96> pixels{}; };
struct Placement { int kind=0,x=0,y=0,state=0; bool active=false; };
struct Level { int height=0,quota=0,seconds=0,fireHits=0; std::vector<uint8_t> pixels; std::vector<Placement> objects; };
struct Definition { int frame=0,flags=0; Handler handler{}; int collision=255; std::array<int,7> params{}; };
struct Command { int op=0,a=0,b=0,c=0,next=0; };
struct Assets {
    std::array<uint8_t,Width*Height> title{};
    std::array<uint8_t,52*64> font{};
    std::vector<Frame> frames=std::vector<Frame>(69);
    std::array<Level,4> levels{};
    std::array<Definition,16> definitions{};
    std::vector<int> animationStarts;
    std::vector<Command> commands;
    static Assets load(const std::wstring& path);
};
struct Entity {
    bool alive=false,animDone=true,hidden=false,offscreen=false;
    int kind=0,frame=0,flags=0,x=0,y=0,collision=255,placement=-1;
    int vy=0,pose=0,vx=0,counter=0,parent=-1,offsetX=0,offsetY=0;
    Handler handler=Handler::Idle;
    int anim=0,delay=0,period=0,loop=0,loopStart=0;
};
struct Game {
    const Assets& assets;
    std::array<Entity,16> entities{};
    std::vector<Placement> placements;
    int difficulty=0,ticks=0,seconds=60,secondTicks=0,money=0,remaining=0;
    int breaksNeeded=10,fireHits=4,camera=0,cameraLead=24,cameraLeadTarget=24;
    int scan=0,introCounter=128,finishTimer=64,result=0,pendingResult=0,resultFlags=0;
    int held=0,pressed=0,previous=0,animationFaults=0;
    bool launched=false,hazardsActive=false,paused=false,started=false,targetReached=false;
    std::array<uint8_t,Width*Height> screen{};
    explicit Game(const Assets& a):assets(a){}
    void start(int level);
    void step(int buttons);
    void render();
    int spawn(int kind,int x,int y,int placement=-1);
    void animate(int i);
    void startAnimation(int i,int sequence,bool force=false);
    void update(int i);
    void collide(int i);
    void destroy(int i);
    void moveFalling(Entity& e);
    void gravity(Entity& e);
    void followCamera(const Entity& e);
    void followParent(Entity& e);
    void collideWith(int player,int other);
    void decrementGoal(int other);
    void finish(int i,int code);
    void land(int i);
    void tickTimer();
    void updateVisibility();
    void drawFrame(int number,int x,int y,int flags=0);
    void text(int x,int y,const std::string& value);
};
void saveBmp(const std::wstring& path,const std::array<uint8_t,Width*Height>& screen);
int runSelfTests(const Assets& assets);
}
