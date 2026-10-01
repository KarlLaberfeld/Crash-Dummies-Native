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
    static UiAssets load(const std::wstring& path);
};
// Title pages and center transitions reconstructed from the original raster layout.
std::array<uint8_t,Width*Height> renderTitle(const UiAssets& assets,int page,bool twoPlayers,int ticks,int titleScroll=0,bool pointer=true);
std::array<uint8_t,Width*Height> renderPausedGame(const UiAssets& assets,const std::array<uint8_t,Width*Height>& game);
constexpr int UiStart=64,UiSelect=128;
enum class UiPhase {Title,Instructions,Playing,Result,Ending,NameEntry,Boot,TitleIntro,
                    HiddenTransition,Password,PasswordSubmit,PasswordFeedback,MusicTest};
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
    int scroll=0,position=0,anchor=0,row=0,speed=0,delay=0,scrollStep=-1,pendingGlyph=-1;
    size_t cursor=0;
    UiMap map{};
    std::vector<uint8_t> text;
    int flagsHit=0,timerPhase=0;
    int resultStage=0,resultWait=0,displaySavings=0,displayPay=0,displayTime=0;
    bool showFlags=false,showSavings=false,showPay=false,showTime=false;
    std::array<uint8_t,48> scores{};
    int scoreRank=-1,nameLength=0,nameScroll=180,nameMotion=0;
    explicit UiFlow(const UiAssets& a):assets(a),scores(a.initialScores){}
    void beginBoot(){phase=UiPhase::Boot;phaseTicks=0;previous=0;}
    void step(int buttons);
    void beginInstructions();
    void finishStunt(int flags,int earned,int seconds,int extraLives=0,int flagsCollected=0);
    std::array<uint8_t,Width*Height> render() const;
private:
    void advanceText();
    void queueTitlePage(int next);
    void enterHighScore();
    void advanceResult(bool skip);
    void continueCampaign();
    void hiddenTransition(UiPhase target,const UiMap& next,int closedWait=0,int music=-2);
    void leavePassword();
};
int runUiTests(const UiAssets& assets);
}
