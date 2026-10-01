#pragma once
#include "game.h"
#include "campaign.h"
namespace ticd {
using UiMap=std::array<uint8_t,1024>;
using UiTiles=std::array<uint8_t,256*64>;
struct InstructionAssets {UiTiles tiles{};UiMap map{};std::vector<uint8_t> text;};
struct UiAssets {
    std::array<uint8_t,256*64> tiles{};
    std::array<uint8_t,Width*Height> titleBackground{};
    std::array<std::array<uint8_t,1024>,6> titleMaps{};
    std::array<uint8_t,48> initialScores{};
    std::array<InstructionAssets,5> instructions{};
    std::array<UiMap,40> headers{};
    std::array<UiTiles,3> resultTiles{};
    std::array<UiMap,16> resultTexts{};
    std::array<UiMap,8> resultLayouts{};
    UiTiles endingTiles{};
    std::array<UiMap,2> endings{};
    std::array<uint8_t,10> names{};
    std::array<uint8_t,12> skiQuotas{},bombQuotas{};
    std::array<uint8_t,20> startPrompt{};
    UiTiles nameTiles{};
    std::array<UiMap,2> nameMaps{};
    UiMap bootMap{},initialTitleMap{};
    std::array<uint8_t,8> fadePalettes{};
    std::array<UiMap,4> hiddenMaps{}; // Password, rejected, accepted, music test.
    std::array<std::array<uint8_t,8>,10> passwords{};
    std::array<uint8_t,Width*8> pauseStrip{};
    std::array<uint8_t,256> celebrationProducts{};
    std::array<uint8_t,128> celebrationWave{};
    std::array<uint8_t,8> celebrationTiles{};
    std::array<uint8_t,8> instructionPattern{};
    static UiAssets load(const std::wstring& path);
};
// Title pages and center transitions reconstructed from the original raster layout.
std::array<uint8_t,Width*Height> renderTitle(const UiAssets& assets,int page,bool twoPlayers,int ticks,int titleScroll=0,bool pointer=true);
std::array<uint8_t,Width*Height> renderPausedGame(const UiAssets& assets,const std::array<uint8_t,Width*Height>& game);
constexpr int UiStart=64,UiSelect=128;
enum class UiPhase {Title,Instructions,Playing,Result,Ending,NameEntry,Boot,TitleIntro,
                    StuntOutro,TitleExit,HiddenTransition,Password,PasswordSubmit,PasswordFeedback,MusicTest};
// Native presentation state machine. No CPU, memory bus or instruction dispatch.
struct UiFlow {
    const UiAssets& assets;
    Campaign campaign;
    UiPhase phase=UiPhase::Title;
    bool twoPlayers=false,textDone=false;
    int pendingSound=-1;
    int pendingMusic=-2; // -2: unchanged, -1: stop, 0..13: start.
    bool musicActive=false; // Host supplies the four music voices' activity.
    int unlockPosition=0,startDay=0,startDifficulty=0;
    std::array<uint8_t,8> password{};
    int passwordCursor=0,passwordPointer=0,passwordAction=-1;
    bool passwordExit=false;
    int testTune=0,testEffect=0,testLastTune=-1;
    UiPhase hiddenTarget=UiPhase::Password;
    UiMap hiddenNextMap{};
    int hiddenWait=0,hiddenClosedWait=0,hiddenMusic=-2;
    int titleScroll=0,titleDirection=0,nextPage=0;
    int page=0,ticks=0,phaseTicks=0,previous=0,stunt=0,level=0;
    int priorButtons=0;
    int randomState=0;
    struct CelebrationEmitter {int x=0,y=143,velocity=251,radius=0,delay=0;};
    struct CelebrationSprite {int x=0,y=0,tile=0;};
    std::array<CelebrationEmitter,4> celebration{};
    std::array<CelebrationSprite,40> celebrationSprites{};
    int celebrationCount=0;
    int scroll=0,position=0,anchor=0,row=0,speed=0,delay=0,scrollStep=-1,pendingGlyph=-1;
    size_t cursor=0;
    UiMap map{};
    std::vector<uint8_t> text;
    int flagsHit=0,timerPhase=0;
    int gameplayFade=8;
    int instructionExit=0; // 32 blocking fade updates, then one white-screen wait.
    int instructionEnter=0; // First instruction: one setup wait, then 32 fade updates.
    bool instructionAlternate=false;
    bool gameplayPaused=false;
    std::array<uint8_t,Width*Height> outroScene{};
    int resultStage=0,resultWait=0,displaySavings=0,displayPay=0,displayTime=0;
    int resultFade=0,resultHold=0;
    bool showFlags=false,showSavings=false,showPay=false,showTime=false;
    std::array<uint8_t,48> scores{};
    int scoreRank=-1,nameLength=0,nameScroll=180,nameMotion=0;
    explicit UiFlow(const UiAssets& a):assets(a),scores(a.initialScores){}
    void beginBoot(){phase=UiPhase::Boot;phaseTicks=0;previous=0;}
    void step(int buttons);
    template<class Stunt> void stepStunt(Stunt& game) const {
        // 03cb waits for the next update after setup. 2405-240c samples input
        // throughout menus and pause, so a held key must not become a new edge.
        if(phase!=UiPhase::Playing||phaseTicks==0)return;
        game.ticks=(ticks-1)&65535;
        game.previous=priorButtons&63;
        game.step(previous&63);
    }
    void beginInstructions(bool first=false,bool alternate=false);
    void finishStunt(int flags,int earned,int seconds,int extraLives=0,int flagsCollected=0);
    std::array<uint8_t,Width*Height> render(bool objects=true) const;
    std::array<uint8_t,Width*Height> renderGameplay(const std::array<uint8_t,Width*Height>& scene,bool paused) const;
private:
    void advanceText();
    void queueTitlePage(int next);
    void enterHighScore();
    void advanceResult(bool skip);
    void continueCampaign();
    void resetCelebrationEmitter(int index);
    void advanceCelebration();
    void hiddenTransition(UiPhase target,const UiMap& next,int closedWait=0,int music=-2);
    void leavePassword();
};
int runUiTests(const UiAssets& assets);
}
