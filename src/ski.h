#pragma once
#include "game.h"
namespace ticd {
enum class SkiHandler { Idle, Intro, Play, Jump, Shadow, Animation, Bonus,
    DebrisRight, DebrisLeft, Crash, Return, FinishDelay, BeginFinish };
struct SkiDefinition {int frame=0,flags=0,collision=255;SkiHandler handler=SkiHandler::Idle;std::array<uint8_t,7> params{};};
struct SkiLevel {int cameraX=0,seconds=0,quota=0,rows=0;std::array<uint8_t,4096> cells{};std::vector<Placement> objects;};
struct SkiAssets {
    std::array<uint8_t,128*64> tiles{};
    std::array<uint8_t,256> quadrants{};
    std::array<uint8_t,128> collision{};
    std::vector<Frame> frames=std::vector<Frame>(39);
    std::array<SkiLevel,4> levels{};
    std::array<SkiDefinition,10> definitions{};
    std::vector<int> animationStarts;std::vector<Command> commands;
    std::array<std::array<int,2>,5> velocities{};
    std::array<uint8_t,9> jumpFrames{};
    std::array<int,2> probe{};
    std::array<uint8_t,13> transferChunks{};
    std::array<uint8_t,256*64> hudTiles{};
    std::array<uint8_t,20> hudMap{};std::array<uint8_t,7> hudColumns{};
    static SkiAssets load(const std::wstring& path);
};
struct SkiEntity {
    bool alive=false,animDone=true,offscreen=false,frameWaiting=false;
    int kind=0,frame=0,flags=0,x=0,y=0,collision=255,placement=-1;
    SkiHandler handler=SkiHandler::Idle;std::array<uint8_t,7> params{};
    int anim=0,delay=0,period=0,loop=0,loopStart=0;
    void move(int dx,int dy){x=(x+dx)&65535;y=(y+dy)&65535;}
};
struct SkiGame {
    const SkiAssets& assets;const Assets& shared;
    std::array<SkiEntity,16> entities{};std::vector<Placement> placements;
    std::array<uint8_t,Width*Height> screen{};
    std::array<uint8_t,20> hudMap{};std::array<uint8_t,7> hudValues{};
    SpriteLayer sprites{false},visibleSprites{false};
    int visibleCameraX=0,visibleCameraY=0;

    bool reverseSprites=false;
    int playerNumber=0,pendingSound=-1;
    int difficulty=0,ticks=0,seconds=0,secondTicks=0,money=0,remaining=0,needed=0,collected=0;
    int cameraX=0,cameraY=0,jumpVelocity=0,jumpContact=0,returnX=0,returnY=0;
    bool finishZone=false,started=false,paused=false;
    int scan=0,hudCursor=0,finishTimer=64,result=0,resultFlags=0;
    int held=0,pressed=0,previous=0,animationFaults=0;
    int transferState=0,transferRemaining=0,transferFrame=0,transferFlags=0,lastMapCamera=0;
    bool mapTransfer=true;
    SkiGame(const SkiAssets& a,const Assets& s):assets(a),shared(s){}
    bool videoTickPrepared=false; // Display callback already ran before a blocking pause.
    void start(int level,int player=0);void step(int buttons);void render(bool developmentOverlay=true);void update(int i);
    int spawn(int kind,int x,int y,int placement=-1);
    void setFrame(int i,int frame,int flags=0);void startAnimation(int i,int sequence,bool force=false);void animate(int i);
    int tileAt(int x,int y) const;int terrainAt(int x,int y) const;
    void publishVideo();
    void beginVideoTick();void finishVideoTick(int oldFrame,int oldFlags);void updateVisibility();
    void followCamera();void input();void movePlayer();void jump();void jumpMotion(int i);
    void terrain();void depth(int i=0);void finishLine();void beginFinish(int flags);void tickTimer();
    void collide();void collideWith(int other);
    void refreshHud();void tickHud();void text(int x,int y,const std::string& value);
};
int runSkiTests(const SkiAssets& assets,const Assets& shared);
}
