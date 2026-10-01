#pragma once
#include "game.h"
namespace ticd {
enum class CruiseHandler {Idle,Intro,Ignition,Fly,Smoke,Ball,RocketUp,Magnet,Target,Wave,RocketDown,Spring,Emitter,RocketWait,RocketFlight,Crash,Failure,Success,BeginFinish,FinishDelay,Animation};
struct CruiseDefinition {int frame=0,flags=0,collision=255;CruiseHandler handler=CruiseHandler::Idle;std::array<uint8_t,7> params{};};
struct CruiseLevel {int initial=0,seconds=0;std::vector<Placement> objects;};
struct CruiseAssets {
    std::array<uint8_t,82*64> tiles{};std::array<uint8_t,2048> cells{};
    std::array<uint8_t,192> quadrants{};std::array<uint8_t,128> collision{};
    std::vector<Frame> frames=std::vector<Frame>(42);
    std::array<CruiseLevel,4> levels{};std::array<CruiseDefinition,66> definitions{};
    std::vector<int> animationStarts;std::vector<Command> commands;
    std::array<uint8_t,12> transferChunks{};std::array<std::array<int,4>,16> headings{};
    std::array<std::array<int,2>,4> probes{};std::array<int,16> wave{};
    std::array<uint8_t,256*64> hudTiles{};std::array<uint8_t,20> hudMap{};std::array<uint8_t,7> hudColumns{};
    static CruiseAssets load(const std::wstring& path);
};
struct CruiseEntity {
    bool alive=false,animDone=true,offscreen=false,frameWaiting=false;
    int kind=0,frame=0,flags=0,x=0,y=0,collision=255,placement=-1;
    CruiseHandler handler=CruiseHandler::Idle;std::array<uint8_t,7> params{};
    int anim=0,delay=0,period=0,loop=0,loopStart=0;
    void move(int dx,int dy){x=(x+dx)&65535;y=(y+dy)&65535;}
};
struct CruiseGame {
    const CruiseAssets& assets;const Assets& shared;
    std::array<CruiseEntity,16> entities{};std::vector<Placement> placements;std::vector<bool> rewarded;
    std::array<uint8_t,Width*Height> screen{};
    std::array<uint8_t,20> hudMap{};std::array<uint8_t,7> hudValues{};
    SpriteLayer sprites{false};
    bool reverseSprites=false;
    int playerNumber=0,pendingSound=-1;
    int difficulty=0,ticks=0,seconds=0,secondTicks=0,money=0,cameraX=0,cameraY=0,introTimer=0,balls=0,randomState=0,extraLives=0;
    bool started=false,paused=false;
    int scan=0,hudCursor=0,finishTimer=64,result=0,resultFlags=0,held=0,pressed=0,previous=0,animationFaults=0;
    int transferState=0,transferRemaining=0,transferFrame=0,transferFlags=0,lastMapCamera=0;
    bool mapTransfer=true;
    CruiseGame(const CruiseAssets& a,const Assets& s):assets(a),shared(s){}
    void start(int level,int player=0);void step(int buttons);void render(bool developmentOverlay=true);void update(int i);
    int spawn(int kind,int x,int y,int placement=-1);void setFrame(int i,int frame,int flags=0);
    void startAnimation(int i,int sequence,bool force=false);void animate(int i);
    int tileAt(int x,int y)const;int terrainAt(int x,int y)const;
    void beginVideoTick();void finishVideoTick(int oldFrame,int oldFlags);void updateVisibility();
    void followCamera();void movePlayer();void crashFrame();void introBob();void ignition();void thrustSmoke();
    int randomByte();void collide();void collideWith(int other);void reward(int other,int points);
    void beginFinish(int flags);void tickTimer();void refreshHud();void tickHud();
    void text(int x,int y,const std::string& value);
};
int runCruiseTests(const CruiseAssets& assets,const Assets& shared);
}
