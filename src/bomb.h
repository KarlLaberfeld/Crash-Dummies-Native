#pragma once
#include "game.h"
namespace ticd {
enum class BombHandler {Idle,Play,Belt,Disarmed,Armed,Bonus,Animation,Fall,Stopped,FinishDelay,BeginFinish};
struct BombDefinition {int frame=0,flags=0,collision=255;BombHandler handler=BombHandler::Idle;std::array<uint8_t,7> params{};};
struct BombLevel {std::array<int,3> speeds{};int quota=0;std::array<uint8_t,32> distribution{};};
struct BombAssets {
    std::array<uint8_t,87*64> tiles{};std::array<uint8_t,340> layout{};
    std::vector<Frame> frames=std::vector<Frame>(33);
    std::array<BombLevel,4> levels{};std::array<BombDefinition,9> definitions{};
    std::vector<int> animationStarts;std::vector<Command> commands;
    std::array<uint8_t,20> transferChunks{};
    std::array<uint8_t,12> upFrames{},downFrames{};
    std::array<int,4> positions{};std::array<uint8_t,8> stanceFrames{};
    std::array<uint8_t,256*64> hudTiles{};std::array<uint8_t,20> hudMap{};std::array<uint8_t,5> hudColumns{};
    static BombAssets load(const std::wstring& path);
};
struct BombEntity {
    bool alive=false,animDone=true,offscreen=false,frameWaiting=false;
    int kind=0,frame=0,flags=0,x=0,y=0,collision=255;
    BombHandler handler=BombHandler::Idle;std::array<uint8_t,7> params{};
    int anim=0,delay=0,period=0,loop=0,loopStart=0;
    void move(int dx,int dy){x=(x+dx)&65535;y=(y+dy)&65535;}
};
struct BombGame {
    const BombAssets& assets;const Assets& shared;
    std::array<BombEntity,16> entities{};std::array<uint8_t,Width*Height> screen{};
    std::array<int,3> speeds{},totals{},spawnPending{},displayTotals{};
    std::array<uint8_t,20> hudMap{};std::array<uint8_t,5> hudValues{};
    int difficulty=0,ticks=0,money=0,cooldown=0,action=0,lostLanes=0,randomState=0;
    bool started=false,paused=false;
    int hudCursor=0,finishTimer=64,result=0,resultFlags=0,held=0,pressed=0,previous=0,animationFaults=0;
    int transferState=0,transferRemaining=0,transferFrame=0,transferFlags=0;
    BombGame(const BombAssets& a,const Assets& s):assets(a),shared(s){}
    void start(int level);void step(int buttons);void render();void update(int i);
    int spawn(int kind,int x,int y);void setFrame(int i,int frame,int flags=0);
    void startAnimation(int i,int sequence,bool force=false);void animate(int i);
    void beginVideoTick();void finishVideoTick(int oldFrame,int oldFlags);void updateVisibility();
    void movePlayer(bool down);void startAction(int kind);void emitObjects();int randomByte();
    int lane(int i) const;void moveObject(int i);void fall(int i);void speedUp(int i);void explode(int i);
    void collide();void collideWith(int other);void beginFinish(int flags);
    void refreshHud();void tickHud();void drawFrame(int number,int x,int y,int flags);void text(int x,int y,const std::string& value);
};
int runBombTests(const BombAssets& assets,const Assets& shared);
}
