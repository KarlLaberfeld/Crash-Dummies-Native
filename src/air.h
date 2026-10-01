#pragma once
#include "game.h"

namespace ticd {
enum class AirHandler { Idle, Intro, Rise, Wait, Play, Animation, FinishMotion,
    WallSlide, Crash, Exploding, Hide, Return, BeginFinish, FinishDelay, Breakable,
    Pickup, Countdown, Booster, Bouncer, Emitter, Particle, FallingPickup, Enemy,
    DebrisLeft, DebrisRight, ExplosionSlow, ExplosionFast };
struct AirDefinition {
    int frame=0,flags=0,collision=255;
    AirHandler handler=AirHandler::Idle;
    std::array<uint8_t,7> params{};
};
struct AirLevel {
    int cameraX=0,cameraY=0,seconds=0,quota=0,rows=0;
    std::array<uint8_t,4096> cells{};
    std::vector<Placement> objects;
};
struct AirAssets {
    std::array<uint8_t,128*64> tiles{};
    std::array<uint8_t,512> quadrants{};
    std::array<uint8_t,128> collision{};
    std::vector<Frame> frames=std::vector<Frame>(59);
    std::array<AirLevel,4> levels{};
    std::array<AirDefinition,18> definitions{};
    std::vector<int> animationStarts;
    std::vector<Command> commands;
    std::array<std::array<std::array<int,2>,6>,5> probes{};
    std::array<int,32> speeds{};
    std::array<std::array<int,4>,5> tilts{};
    std::array<uint8_t,12> transferChunks{};
    std::array<uint8_t,256*64> hudTiles{};
    std::array<uint8_t,20> hudMap{};
    std::array<uint8_t,13> hudColumns{};
    static AirAssets load(const std::wstring& path);
};
struct AirEntity {
    bool alive=false,animDone=true,offscreen=false,frameWaiting=false;
    int kind=0,frame=0,flags=0,x=0,y=0,collision=255,placement=-1;
    AirHandler handler=AirHandler::Idle;
    // Original entity fields 09..0f; byte overflow is intentional game logic.
    std::array<uint8_t,7> params{};
    int anim=0,delay=0,period=0,loop=0,loopStart=0;
    void move(int dx,int dy){x=(x+dx)&65535;y=(y+dy)&65535;}
};
struct AirGame {
    const AirAssets& assets;
    const Assets& shared;
    std::array<AirEntity,16> entities{};
    std::vector<Placement> placements;
    std::array<uint8_t,Width*Height> screen{};
    std::array<uint8_t,20> hudMap{};
    std::array<uint8_t,13> hudValues{};
    std::array<int,6> probes{};
    SpriteLayer sprites{false};
    bool reverseSprites=false;
    int playerNumber=0,pendingSound=-1;
    int difficulty=0,ticks=0,seconds=0,secondTicks=0,money=0,livesEarned=0;
    int cameraX=0,cameraY=0,cameraLead=176,cameraLeadTarget=176;
    int tilt=0,speed=0,rate=0,lastForce=0,returnX=0,returnY=0;
    int scan=0,hudCursor=0,finishTimer=128,result=0,resultFlags=0;
    int held=0,pressed=0,previous=0,animationFaults=0,randomState=0;
    int transferState=0,transferRemaining=0,transferFrame=0,transferFlags=0,lastMapCamera=0;
    bool mapTransfer=true;
    bool started=false,paused=false;
    AirGame(const AirAssets& a,const Assets& s):assets(a),shared(s){}
    void start(int level,int player=0);
    void step(int buttons);
    void render(bool developmentOverlay=true);
    int spawn(int kind,int x,int y,int placement=-1);
    void update(int i);
    void startAnimation(int i,int sequence,bool force=false);
    void animate(int i);
    void setFrame(int i,int frame,int flags=0);
    void followCamera(bool horizontal=true);
    void movePlayer();
    void input();
    void lookupRate();
    void beginVideoTick();
    void finishVideoTick(int oldFrame,int oldFlags);
    int tileAt(int x,int y) const;
    int terrainAt(int x,int y) const;
    void sampleProbes(int pose);
    void terrainBounce();
    void impact();
    void damage(int amount);
    void walls();
    void finishGate();
    void beginFinish(int flags);
    void collide();
    void collideWith(int other);
    void updateVisibility();
    void tickTimer();
    int randomByte();
    void refreshHud();
    void tickHud();
    void text(int x,int y,const std::string& value);
};
int runAirTests(const AirAssets& assets,const Assets& shared);
}
