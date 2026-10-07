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
    SpriteLayer sprites{false},visibleSprites{false};
    SpriteResources spriteResources;
    int visibleCameraX=0,visibleCameraY=0;

    bool reverseSprites=false;
    int playerNumber=0,pendingSound=-1;
    int difficulty=0,ticks=0,seconds=0,secondTicks=0,money=0,livesEarned=0;
    int cameraX=0,cameraY=0,cameraLead=176,cameraLeadTarget=176;
    int tilt=0,speed=0,rate=0,lastForce=0,returnX=0,returnY=0;
    int scan=0,hudCursor=0,finishTimer=128,result=0,resultFlags=0;
    int held=0,pressed=0,previous=0,animationFaults=0,randomState=0;
    int transferState=0,transferRemaining=0,transferFrame=0,transferFlags=0,lastMapCamera=0;
    bool mapTransfer=true;
    // Source-derived work accounting, in original T-cycles. These are partial
    // costs, not a complete frame budget; they do not yet drive scheduling.
    int mapWorkCycles=0,placementWorkCycles=0,spriteWorkCycles=0,clearWorkCycles=0;
    std::array<int,16> spriteEntityWorkCycles{};
    std::array<AirEntity,16> spriteInputEntities{};
    std::vector<int> resourceCompletionCosts; // Diagnostic source boundaries; no runtime clock input.
    int resourceWorkCycles=0,animationWorkCycles=0,entityWorkCycles=-1;
    // -2 = unoccupied; -1 = handler body not yet reconstructed.
    std::array<int,16> handlerWorkCycles{},handlerWorkKinds{};
    int starterWorkCycles=0,cameraWorkCycles=0;
    int collisionScanWorkCycles=0,collisionCallbackWorkCycles=0;
    int complexBodyWorkCycles=-1;
    int playerMotionWorkCycles=0;
    int playerInputWorkCycles=0;
    int displayWorkCycles=-1,displayFadeRemaining=8;
    bool animationWorkComplete=true;
    bool measureWork=false; // Enable partial source-work accounting in reference probes.
    // Native liveness safeguard: retain a recovery rejected by 00:3b84.
    bool crashRecoveryPending=false;
    bool started=false,paused=false;
    AirGame(const AirAssets& a,const Assets& s):assets(a),shared(s){}
    void start(int level,int player=0);
    bool videoTickPrepared=false; // Display callback already ran before a blocking pause.
    void step(int buttons);
    // Separate owners for the source-derived service/update scheduler. step()
    // retains the legacy one-service wrapper until ordinary-clock acceptance.
    void displayTick(bool resourceReady=true);
    void updateGame(int buttons,bool deferSpriteClear=false,bool deferPlacements=false);
    void updatePlacements();
    void render(bool developmentOverlay=true,int finalPlayRowLimit=Width,
                std::array<uint8_t,Width*Height>* paletteOwners=nullptr);
    int spawn(int kind,int x,int y,int placement=-1);
    void update(int i);
    void startAnimation(int i,int sequence,bool force=false);
    void animate(int i);
    void setFrame(int i,int frame,int flags=0);
    void followCamera(bool horizontal=true);
    void movePlayer();
    void input();
    void lookupRate();
    void publishVideo();
    void beginVideoTick(bool resourceReady=true);
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
    void updateVisibility(bool deferSpriteClear=false);
    void tickTimer();
    int randomByte();
    void refreshHud();
    void tickHud();
    void text(int x,int y,const std::string& value);
};
int runAirTests(const AirAssets& assets,const Assets& shared);
}
