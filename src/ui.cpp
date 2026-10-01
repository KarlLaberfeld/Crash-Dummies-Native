#include "ui.h"
#include <algorithm>
#include <cstdio>
#include <cstring>
#include <stdexcept>
namespace ticd {
UiAssets UiAssets::load(const std::wstring& path){
    FILE* f=_wfopen(path.c_str(),L"rb");if(!f)throw std::runtime_error("ui.dat is missing. Rebuild with the original ROM.");
    std::vector<uint8_t> data(1024*1024);size_t n=fread(data.data(),1,data.size(),f);int extra=fgetc(f);fclose(f);data.resize(n);
    if(n<8||extra!=EOF||memcmp(data.data(),"TICDUI07",8))throw std::runtime_error("Invalid UI asset package.");
    UiAssets a;size_t offset=8;
    auto read=[&](auto& target){if(target.size()>data.size()-offset)throw std::runtime_error("Truncated UI package");
        memcpy(target.data(),data.data()+offset,target.size());offset+=target.size();};
    read(a.tiles);read(a.titleBackground);for(auto& m:a.titleMaps)read(m);read(a.initialScores);
    for(auto& instruction:a.instructions){read(instruction.tiles);read(instruction.map);
        std::array<uint8_t,2> length{};read(length);size_t count=length[0]+256*length[1];
        if(!count||count>4096)throw std::runtime_error("Invalid instruction text length");
        instruction.text.resize(count);read(instruction.text);}
    for(auto& m:a.headers)read(m);for(auto& t:a.resultTiles)read(t);
    for(auto& m:a.resultTexts)read(m);for(auto& m:a.resultLayouts)read(m);
    read(a.endingTiles);for(auto& m:a.endings)read(m);
    read(a.names);read(a.skiQuotas);read(a.bombQuotas);read(a.startPrompt);
    read(a.nameTiles);for(auto& m:a.nameMaps)read(m);
    read(a.bootMap);read(a.initialTitleMap);read(a.fadePalettes);
    for(auto& m:a.hiddenMaps)read(m);for(auto& p:a.passwords){read(p);
        for(int digit:p)if(digit<1||digit>10)throw std::runtime_error("Invalid password digit");}
    read(a.pauseStrip);
    read(a.celebrationProducts);read(a.celebrationWave);read(a.celebrationTiles);read(a.instructionPattern);
    if(offset!=data.size())throw std::runtime_error("Trailing UI package data");
    auto validate=[](const auto& tiles){for(int shade:tiles)if(shade>3)throw std::runtime_error("Invalid UI palette");};
    validate(a.tiles);validate(a.titleBackground);for(const auto& i:a.instructions)validate(i.tiles);
    for(const auto& t:a.resultTiles)validate(t);validate(a.endingTiles);validate(a.nameTiles);validate(a.pauseStrip);return a;
}

std::array<uint8_t,Width*Height> renderPausedGame(const UiAssets& assets,const std::array<uint8_t,Width*Height>& game){
    auto screen=game;std::copy(assets.pauseStrip.begin(),assets.pauseStrip.end(),screen.begin()+PlayHeight*Width);return screen;
}

static std::array<uint8_t,Width*Height> titleImage(const UiAssets& a,const UiMap& map,int titleScroll){
    auto screen=a.titleBackground;
    // 00:2502-2535: stable phase uses unsigned window-map tiles with SCY=88
    // between the two fixed signed-tile logo strips at scanlines 24 and 104.
    for(int y=24;y<104;++y)for(int x=0;x<Width;++x){int wy=y+88+(y<24-titleScroll?titleScroll:0),tile=map[(wy/8)*32+x/8];
        screen[y*Width+x]=a.tiles[tile*64+(wy&7)*8+(x&7)];}
    return screen;
}

std::array<uint8_t,Width*Height> renderTitle(const UiAssets& a,int page,bool twoPlayers,int ticks,int titleScroll,bool pointer){
    if(titleScroll>0||titleScroll< -80)throw std::invalid_argument("Invalid title scroll");
    if(page<0||page>=6)throw std::invalid_argument("Invalid title page");
    auto screen=titleImage(a,a.titleMaps[page],titleScroll);
    if(page==5&&pointer){int tile=254+((ticks>>4)&1),py=56+(twoPlayers?16:0);
        for(int y=0;y<8;++y)for(int x=0;x<8;++x){int shade=a.tiles[tile*64+y*8+x];if(shade)screen[(py+y)*Width+16+x]=(0xc4>>(shade*2))&3;}}
    return screen;
}
namespace {
std::array<uint8_t,Width*Height> renderMap(const UiTiles& tiles,const UiMap& map,int scroll=0){
    std::array<uint8_t,Width*Height> screen{};
    for(int y=0;y<Height;++y)for(int x=0;x<Width;++x){
        int wy=(y+(y>=96?scroll:0))&255;
        int tile=map[(wy/8)*32+x/8];screen[y*Width+x]=tiles[tile*64+(wy&7)*8+(x&7)];
    }
    return screen;
}
void scoreRows(UiMap& canvas,const std::array<uint8_t,48>& records,int top){
    for(int n=0;n<8;++n){int row=(top+n)*32;canvas[row+3]=n+2;
        for(int j=0;j<3;++j)canvas[row+5+j]=records[n*6+j];
        int digits[6];for(int j=0;j<3;++j){digits[j*2]=records[n*6+3+j]>>4;digits[j*2+1]=records[n*6+3+j]&15;}
        int first=0;while(first<3&&!digits[first])++first;
        for(int j=9;j<17;++j)canvas[row+j]=0;
        for(int j=first;j<4;++j)canvas[row+10+j]=digits[j]+1;
        canvas[row+9+first]=0x33;canvas[row+14]=0x2c;canvas[row+15]=digits[4]+1;canvas[row+16]=digits[5]+1;
    }
}
void overlay(UiMap& dest,const UiMap& source){for(size_t i=0;i<dest.size();++i)if(source[i])dest[i]=source[i];}
void money(UiMap& map,int row,int value){
    int digits[6];for(int i=5;i>=0;--i){digits[i]=value%10;value/=10;}
    int first=0;while(first<3&&!digits[first])++first;
    for(int i=0;i<4;++i)map[row*32+13+i]=i<first?0:digits[i]+1;
    map[row*32+12+first]=0x33;map[row*32+17]=0x2c;
    map[row*32+18]=digits[4]+1;map[row*32+19]=digits[5]+1;
}
int resultText(int stunt,int flags){
    if(flags&2)return stunt;
    switch(stunt){
    case 0:return flags&16?6:flags&32?7:flags&128?8:5;
    case 1:return flags&16?10:9;
    case 2:return flags&32?12:11;
    case 3:return 13;
    default:return flags&16?15:14;
    }
}
}
void UiFlow::beginInstructions(bool first,bool alternate){
    const auto& player=campaign.players[campaign.current];stunt=player.day;level=player.difficulty;
    phase=UiPhase::Instructions;phaseTicks=0;scroll=0;position=anchor=row=speed=delay=0;scrollStep=pendingGlyph=-1;
    cursor=0;textDone=false;instructionExit=0;instructionAlternate=alternate;
    instructionEnter=first?33:alternate?65:0;map=assets.instructions[stunt].map;
    overlay(map,assets.headers[(campaign.current*5+stunt)*4+level]);map[19]=static_cast<uint8_t>(std::min(player.lives,9)+1);
    text.clear();
    // Resolve the identified text macros into glyphs. Their 0x88 terminators
    // never become native operations or cartridge return addresses.
    for(int op:assets.instructions[stunt].text){
        if(op==0x89){auto start=assets.names.begin()+campaign.current*5;text.insert(text.end(),start,start+5);}
        else if(op==0x8a||op==0x8c){const auto& quota=op==0x8a?assets.skiQuotas:assets.bombQuotas;text.push_back(quota[level*3]);text.push_back(quota[level*3+1]);}
        else text.push_back(static_cast<uint8_t>(op));
    }
    if(!instructionEnter)advanceText();
}
void UiFlow::advanceText(){
    auto byte=[&](){if(cursor>=text.size())throw std::runtime_error("Truncated instruction text");return text[cursor++];};
    auto put=[&](int glyph){if(position<0||position>=1024)throw std::runtime_error("Instruction text outside map");map[position++]=static_cast<uint8_t>(glyph);};
    if(delay>0&&--delay>0)return;
    if(pendingGlyph>=0){put(pendingGlyph);pendingGlyph=-1;}
    if(scrollStep>=0){constexpr int increments[]={1,2,3,1,1};scroll=(scroll+increments[scrollStep++])&255;
        if(scrollStep<5){delay=2;return;}scrollStep=-1;position=(++row)*32+anchor;}
    while(!textDone){int op=byte();
        if(op<128){if(op&&speed){pendingGlyph=op;delay=speed;return;}put(op);}
        else switch(op){
        case 0x80:{
            // 032b checks held Start after the text script returns. A key
            // held through entry does not interrupt typing, but exits here.
            textDone=true;if(previous&UiStart){instructionExit=33;return;}
            for(int glyph:assets.startPrompt){put(glyph);}return;
        }
        case 0x81:anchor=byte();row=byte();position=row*32+anchor;break;
        case 0x82:if(byte()!=0)throw std::runtime_error("Unexpected instruction text layer");break;
        case 0x84:position=(++row)*32+anchor;break;
        case 0x85:scrollStep=0;delay=2;return;
        case 0x86:speed=byte();break;
        case 0x87:if(byte()!=8)throw std::runtime_error("Unexpected instruction skip input");break;
        default:throw std::runtime_error("Unsupported instruction text operation");
        }
    }
}
void UiFlow::finishStunt(int flags,int earned,int seconds,int extraLives,int flagsCollected){
    if(phase!=UiPhase::Playing)throw std::logic_error("Stunt result outside gameplay");
    displaySavings=campaign.players[campaign.current].savings;
    campaign.settle(flags,earned,seconds,extraLives);flagsHit=flagsCollected;
    displayPay=earned%1000000;displayTime=(flags&64)?0:seconds;
    resultStage=0;resultWait=15;showFlags=showSavings=showPay=showTime=false;
    phase=UiPhase::StuntOutro;phaseTicks=0;resultFade=32;resultHold=0;
}
void UiFlow::continueCampaign(){
    // 268b disables objects before alternation between the two background maps.
    outroScene=render(false);
    if(campaign.next())beginInstructions(false,true);else{
        // 051d fades the last screen before re-entering title setup at 019c.
        // 020a skips the copyright screen after it has been shown once.
        titleIntroMusic=phase==UiPhase::NameEntry?-1:13;
        phase=UiPhase::TitleReturn;page=0;phaseTicks=0;
    }
}
void UiFlow::advanceResult(bool skip){
    if(skip){showFlags=stunt==2;showSavings=showPay=true;showTime=!(campaign.last.flags&64);
        displaySavings=campaign.players[campaign.current].savings;displayPay=displayTime=0;resultStage=6;resultWait=0;return;}
    if(resultWait>0&&--resultWait>0)return;
    int multiplier=campaign.last.perfect?2:1;
    for(;;)switch(resultStage){
    case 0:
        ++resultStage;if(stunt==2){showFlags=true;resultWait=20;return;}break;
    case 1:showSavings=true;++resultStage;resultWait=20;return;
    case 2:showPay=true;++resultStage;break;
    case 3:
        if(displayPay){--displayPay;displaySavings=(displaySavings+multiplier)%1000000;return;}
        if(campaign.last.flags&64){resultStage=6;return;}
        ++resultStage;resultWait=15;return;
    case 4:showTime=true;++resultStage;break;
    case 5:
        if(displayTime){--displayTime;displaySavings=(displaySavings+multiplier)%1000000;return;}
        resultStage=6;return;
    default:return;
    }
}
void UiFlow::enterHighScore(){
    int savings=campaign.players[campaign.current].savings;scoreRank=-1;
    for(int n=0;n<8;++n){int value=0;for(int j=0;j<3;++j){int b=scores[n*6+3+j];value=value*100+10*(b>>4)+(b&15);}
        if(savings>=value){scoreRank=n;break;}}
    if(scoreRank<0){continueCampaign();return;}
    for(int i=47;i>=(scoreRank+1)*6;--i)scores[i]=scores[i-6];
    for(int i=0;i<3;++i)scores[scoreRank*6+i]=0;
    for(int i=2;i>=0;--i){int b=savings%100;savings/=100;scores[scoreRank*6+3+i]=static_cast<uint8_t>(((b/10)<<4)|(b%10));}
    outroScene=render();
    phase=UiPhase::NameEntry;phaseTicks=0;nameLength=0;nameScroll=180;nameMotion=0;nameEnter=64;nameBlink=false;nameClosed=false;
}
void UiFlow::queueTitlePage(int next){nextPage=next;titleDirection=-1;}
void UiFlow::hiddenTransition(UiPhase target,const UiMap& next,int closedWait,int music){
    hiddenTarget=target;hiddenNextMap=next;hiddenClosedWait=closedWait;hiddenMusic=music;
    hiddenWait=0;phase=UiPhase::HiddenTransition;phaseTicks=0;titleDirection=-1;titleScroll=0;
}
void UiFlow::resetCelebrationEmitter(int index){
    // 1723 changes only the high byte of the shared random state.
    int swapped=((randomState&255)<<8)|(randomState>>8);
    int first=(randomState-swapped)&65535;
    int value=(first-swapped-(randomState<swapped)+254)&65535;
    int lo=value&255,hi=value>>8,out=(lo-hi-(lo>=hi))&255;
    randomState=(randomState&255)|(out<<8);
    celebration[index]={(out&127)+16,143,251,0,index*16};
}
void UiFlow::advanceCelebration(){
    // 15da/15fa multiply the extracted wave by the signed radius using
    // the original byte lookup tables, including their rounding and wrap.
    auto offset=[&](int angle,int radius){
        bool negative=((angle^radius)&128)!=0;
        int wave=assets.celebrationWave[angle&127];
        int magnitude=radius&128?(-radius)&255:radius;
        int half=std::abs(wave-magnitude)/2;
        int product=(assets.celebrationProducts[std::min(wave,magnitude)+half]-assets.celebrationProducts[half])&255;
        return negative?(-product)&255:product;
    };
    celebrationCount=0;
    for(int i=0;i<4;++i){auto& emitter=celebration[i];
        if(emitter.delay){--emitter.delay;continue;}
        if(emitter.y>=192){resetCelebrationEmitter(i);continue;}
        int oldY=emitter.y;emitter.y=(emitter.y+emitter.velocity)&255;
        int tile=assets.celebrationTiles[(emitter.radius&112)>>4];
        for(int j=0;j<10;++j){int angle=(ticks+j*25)&255;
            celebrationSprites[celebrationCount++]={(emitter.x+offset((angle+64)&255,emitter.radius))&255,(oldY+offset(angle,emitter.radius))&255,tile};}
        if(!(ticks&7))emitter.velocity=(emitter.velocity+1)&255;
        if(!((emitter.velocity+2)&128))emitter.radius=(emitter.radius+1)&255;
    }
}
void UiFlow::leavePassword(){
    if(passwordExit){
        hiddenTransition(UiPhase::Title,assets.titleMaps[0]);
        hiddenWait=1;hiddenMusic=1;
    }else hiddenTransition(UiPhase::Password,assets.hiddenMaps[0],1,7);
}
void UiFlow::step(int buttons){
    pendingSound=-1;pendingMusic=-2;
    priorButtons=previous;
    int pressed=buttons&~previous;previous=buttons;ticks=(ticks+1)&65535;++phaseTicks;
    switch(phase){
    case UiPhase::TitleReturn:
        if(phaseTicks>=32){phase=UiPhase::TitleIntro;phaseTicks=0;titleScroll=titleDirection=0;page=0;}
        break;
    case UiPhase::Boot:
        // 280c: 32-update fade in, fixed 180-update hold, 32-update fade out.
        // 25c4 does not inspect input, so Start cannot skip the copyright screen.
        if(phaseTicks>=244){phase=UiPhase::TitleIntro;phaseTicks=0;titleScroll=0;page=0;}
        break;
    case UiPhase::TitleIntro:
        // 0259/0264/26ea: fade in, one wait, close the blank center, install
        // page zero, then open it. Start is accepted only by the page loop.
        if(phaseTicks>=33)titleScroll=phaseTicks<=73?-(phaseTicks-33)*2:(phaseTicks-113)*2;
        if(phaseTicks>=113){phase=UiPhase::Title;phaseTicks=0;titleScroll=titleDirection=0;page=0;}
        break;
    case UiPhase::Title:
        if(titleDirection){
            titleScroll+=titleDirection*2;
            if(titleScroll==-80){page=nextPage;titleDirection=1;}
            else if(titleScroll==0){titleDirection=0;phaseTicks=0;}
            break;
        }
        if(page!=5&&pressed){
            constexpr int sequence[]={Up,Down,Left,Right};
            if(pressed==sequence[unlockPosition])++unlockPosition;else unlockPosition=0;
            if(unlockPosition==4){unlockPosition=0;map=assets.titleMaps[page];if(page==2)scoreRows(map,scores,16);
                hiddenTransition(UiPhase::Password,assets.hiddenMaps[0],1,7);break;}
        }
        // 278f-279a toggles the player selection before handling Start.
        if(page==5&&(pressed&(UiSelect|Up|Down)))twoPlayers=!twoPlayers;
        if(pressed&UiStart){outroScene=render();campaign.start(twoPlayers,startDay,startDifficulty);phase=UiPhase::TitleExit;phaseTicks=0;}
        else if(page==5){
            if(pressed&(A|B))queueTitlePage(0);
        }else if(pressed&UiSelect)queueTitlePage(5);
        else{constexpr int durations[]={480,480,960,480,960};
            if((pressed&(A|B))||phaseTicks>=durations[page])queueTitlePage((page+1)%5);}
        break;
    case UiPhase::TitleExit:
        // 0269 fades for 32 updates; 026c waits once before stopping music.
        if(phaseTicks>=33)beginInstructions(true);
        break;
    case UiPhase::HiddenTransition:
        if(hiddenWait){if(--hiddenWait==0){pendingMusic=hiddenMusic;hiddenMusic=-2;}break;}
        if(titleDirection<0){
            titleScroll-=2;
            if(titleScroll==-80){map=hiddenNextMap;titleDirection=1;hiddenWait=hiddenClosedWait;
                if(!hiddenWait){pendingMusic=hiddenMusic;hiddenMusic=-2;}}
        }else{
            if(hiddenMusic!=-2){pendingMusic=hiddenMusic;hiddenMusic=-2;}
            titleScroll+=2;
            if(titleScroll==0){phase=hiddenTarget;phaseTicks=0;titleDirection=0;
                if(phase==UiPhase::Password){password={};passwordCursor=passwordPointer=0;}
                if(phase==UiPhase::MusicTest){testTune=testEffect=0;testLastTune=-1;}
                if(phase==UiPhase::Title)page=0;
            }
        }
        break;
    case UiPhase::Password:
        // 2baa publishes the pointer before processing this update's input.
        passwordPointer=passwordCursor;
        if((pressed&Left)&&passwordCursor>0)--passwordCursor;
        if((pressed&Right)&&passwordCursor<7)++passwordCursor;
        if(pressed&Up){auto& digit=password[passwordCursor];digit=digit==10?1:digit+1;map[21*32+6+passwordCursor]=digit;}
        if(pressed&Down){auto& digit=password[passwordCursor];digit=digit<=1?10:digit-1;map[21*32+6+passwordCursor]=digit;}
        if(pressed&(UiStart|A|B)){passwordExit=(pressed&UiStart)!=0;phase=UiPhase::PasswordSubmit;phaseTicks=0;}
        break;
    case UiPhase::PasswordSubmit:
        pendingMusic=-1;passwordAction=-1;
        for(int i=0;i<10;++i)if(password==assets.passwords[i]){passwordAction=i;break;}
        hiddenTransition(UiPhase::PasswordFeedback,assets.hiddenMaps[passwordAction<0?1:2]);break;
    case UiPhase::PasswordFeedback:
        if(phaseTicks>=60){
            if(passwordAction>=0&&passwordAction<5)startDay=passwordAction;
            else if(passwordAction>=5&&passwordAction<9)startDifficulty=passwordAction-5;
            if(passwordAction==9)hiddenTransition(UiPhase::MusicTest,assets.hiddenMaps[3]);else leavePassword();
        }
        break;
    case UiPhase::MusicTest:
        // Original number renderer prints hexadecimal nibbles before input.
        map[19*32+16]=(testTune>>4)+1;map[19*32+17]=(testTune&15)+1;
        map[21*32+16]=(testEffect>>4)+1;map[21*32+17]=(testEffect&15)+1;
        if(pressed&Left)testTune=(testTune+13)%14;
        if(pressed&Right)testTune=(testTune+1)%14;
        if(pressed&Down)testEffect=(testEffect+25)%26;
        if(pressed&Up)testEffect=(testEffect+1)%26;
        if(pressed&B){testLastTune=-1;pendingMusic=-1;}
        if(pressed&A){if(testLastTune==testTune&&musicActive&&!(pressed&B))pendingSound=testEffect;
            else{testLastTune=testTune;pendingMusic=testTune;}}
        if(pressed&UiStart)leavePassword();
        break;
    case UiPhase::Instructions:
        // 0319 waits before song 2; the first 268b path fades for 32 updates
        // before the instruction text interpreter can consume input.
        if(instructionEnter){if(--instructionEnter==0)advanceText();break;}
        // 034c/034f: stop the text interpreter, fade out for 32 updates,
        // then wait once before 0352 stops music and stunt setup begins.
        // Keeping the instruction phase also keeps its song running here.
        if(instructionExit){
            if(--instructionExit==0){phase=UiPhase::Playing;phaseTicks=0;gameplayFade=8;randomState=(ticks&255)<<8;}
        }else if(pressed&UiStart)instructionExit=33;
        else if(!textDone)advanceText();
        break;
    case UiPhase::StuntOutro:
        // 0400 waits once, 0403 stops music, 0406 fades for 32 updates.
        // Failed results wait once more at 05a7/068f before their song/fade.
        if(phaseTicks>=33+(campaign.last.success?0:1)){phase=UiPhase::Result;phaseTicks=0;celebrationCount=0;
            if(campaign.last.perfect)for(int i=0;i<4;++i)resetCelebrationEmitter(i);}
        break;
    case UiPhase::Result:{
        if(campaign.last.perfect)advanceCelebration();
        if(resultFade){--resultFade;break;}
        bool counting=campaign.last.success&&resultStage<6;
        if(counting)advanceResult((pressed&(UiStart|A|B))!=0);
        // 04f7 adds 60 to the remaining counter via RST 30. 24cf retains
        // one rather than storing zero when its background counter expires.
        // 14f2 replaces the 600-update budget with 720 for perfect results.
        if(counting&&resultStage==6)resultHold=60+std::max(1,(campaign.last.perfect?720:600)-phaseTicks);
        else if(!counting&&resultHold>0)--resultHold;
        // A button that accelerates counting is consumed by that operation.
        // Result timeout runs during counting, as in 24cf, but cannot cut it short.
        if((!counting&&!campaign.last.gameOver&&(pressed&(UiStart|A|B)))||
           ((!campaign.last.success&&phaseTicks>=32+480)||(campaign.last.success&&resultStage==6&&!resultHold))){
            if(campaign.last.completed){phase=UiPhase::Ending;phaseTicks=0;endingEnter=65;}
            else if(campaign.last.gameOver)enterHighScore();else continueCampaign();}
        break;}
    case UiPhase::Ending:
        // 05c0 keeps the result callback running during its fade. 05c8 then
        // disables it, before 068f's wait and 0697's blocking fade in.
        if(endingEnter){if(endingEnter>33&&campaign.last.perfect)advanceCelebration();--endingEnter;}
        else if(phaseTicks>=65+480)enterHighScore();
        break;
    case UiPhase::NameEntry:{
        // 3205 and 32bf run before the input/blink loop at 32c5. Input is
        // still sampled globally, so holding A across entry is not a press.
        if(nameEnter){--nameEnter;break;}
        if(!(ticks&15))nameBlink=!nameBlink;
        if(nameMotion<0){nameScroll=(nameScroll-1)&255;++nameMotion;}
        else if(nameMotion>0){nameScroll=(nameScroll+1)&255;--nameMotion;}
        if(!nameMotion){if(buttons&Left)nameMotion=-8;else if(buttons&Right)nameMotion=8;}
        if(pressed&(A|B)){
            int letter=((nameScroll+76)&248)>>3;
            if(letter==31){pendingSound=9;nameClosed=true;continueCampaign();}
            else if(letter==30){if(nameLength){scores[scoreRank*6+--nameLength]=0;pendingSound=4;}}
            else if(nameLength<3){scores[scoreRank*6+nameLength++]=assets.nameMaps[0][15*32+letter];pendingSound=17;}
        }
        break;}

    case UiPhase::Playing:break;
    }
    // 03bf initializes the eight-step counter. 20ee advances it on even
    // global frames during gameplay; the pause callback does not run 20ee.
    if(phase==UiPhase::Playing&&phaseTicks>0&&!gameplayPaused&&!(ticks&1)&&gameplayFade>0)--gameplayFade;
}
std::array<uint8_t,Width*Height> UiFlow::renderGameplay(const std::array<uint8_t,Width*Height>& scene,bool paused) const{
    auto screen=paused?renderPausedGame(assets,scene):scene;
    int palette=assets.fadePalettes[std::min(gameplayFade,7)];
    // Sprite colors already include their fixed white-color masks. The ROM's
    // fade palettes keep color zero white, so the same mapping applies here.
    for(auto& shade:screen)shade=(palette>>(shade*2))&3;
    return screen;
}
std::array<uint8_t,Width*Height> UiFlow::render(bool objects) const{
    if(phase==UiPhase::TitleExit||phase==UiPhase::TitleReturn){
        auto screen=outroScene;int palette=assets.fadePalettes[std::min(7,phaseTicks/4)];
        for(auto& shade:screen)shade=(palette>>(shade*2))&3;
        return screen;
    }
    if(phase==UiPhase::StuntOutro){
        if(!phaseTicks)return renderGameplay(outroScene,false);
        auto screen=outroScene;int palette=assets.fadePalettes[std::min(7,(phaseTicks-1)/4)];
        for(auto& shade:screen)shade=(palette>>(shade*2))&3;
        return screen;
    }
    if(phase==UiPhase::HiddenTransition||phase==UiPhase::Password||phase==UiPhase::PasswordSubmit||
       phase==UiPhase::PasswordFeedback||phase==UiPhase::MusicTest){
        auto screen=titleImage(assets,map,titleScroll);
        if(phase==UiPhase::Password||phase==UiPhase::PasswordSubmit){int px=48+passwordPointer*8;
            for(int y=0;y<8;++y)for(int x=0;x<8;++x){int color=assets.tiles[0x45*64+y*8+x];
                auto& background=screen[(80+y)*Width+px+x];if(color&&!background)background=(0xc4>>(color*2))&3;}}
        return screen;
    }
    if(phase==UiPhase::Boot||phase==UiPhase::TitleIntro){
        auto screen=phase==UiPhase::Boot?renderMap(assets.tiles,assets.bootMap):titleImage(assets,phaseTicks<73?assets.initialTitleMap:assets.titleMaps[0],titleScroll);
        int palette=0xe4;
        if(phaseTicks<32)palette=assets.fadePalettes[7-phaseTicks/4];
        else if(phase==UiPhase::Boot&&phaseTicks>=212)palette=assets.fadePalettes[std::min(7,(phaseTicks-212)/4)];
        for(auto& shade:screen)shade=(palette>>(shade*2))&3;
        return screen;
    }
    if(phase==UiPhase::Title){
        if(page!=2)return renderTitle(assets,page,twoPlayers,ticks,titleScroll,titleDirection==0);
        auto canvas=assets.titleMaps[2];scoreRows(canvas,scores,16);auto screen=assets.titleBackground;
        for(int y=24;y<104;++y)for(int x=0;x<Width;++x){int wy=y+88+(y<24-titleScroll?titleScroll:0),tile=canvas[(wy/8)*32+x/8];screen[y*Width+x]=assets.tiles[tile*64+(wy&7)*8+(x&7)];}
        return screen;
    }
    if(phase==UiPhase::NameEntry){
        if(nameEnter>32){auto screen=outroScene;int palette=assets.fadePalettes[(64-nameEnter)/4];
            for(auto& shade:screen)shade=(palette>>(shade*2))&3;
            return screen;}
        auto canvas=assets.nameMaps[campaign.current];scoreRows(canvas,scores,6);
        // 3358 clears twenty alphabet cells; 3371 disables both raster
        // callbacks and removes the arrows before returning to the caller.
        if(nameClosed)for(int x=0;x<20;++x)canvas[15*32+x]=0;
        auto screen=renderMap(assets.nameTiles,canvas);
        // 24a5 / 255d / 256c: scroll the alphabet horizontally and duplicate
        // scanlines by decreasing vertical scroll at every second raster line.
        for(int y=119;!nameClosed&&y<Height;++y)for(int x=0;x<Width;++x){
            int wx=(x+nameScroll)&255,wy=y-std::min(8,(y-118)/2),tile=canvas[(wy/8)*32+wx/8];
            screen[y*Width+x]=assets.nameTiles[tile*64+(wy&7)*8+(wx&7)];
        }
        for(int p=0;objects&&!nameClosed&&p<2;++p){int tile=(p?254:255)^nameBlink,py=p?136:112;
            for(int y=0;y<8;++y)for(int x=0;x<8;++x){int shade=assets.nameTiles[tile*64+y*8+x];
                if(shade)screen[(py+y)*Width+76+x]=(0xc4>>(shade*2))&3;}}
        if(nameEnter){int palette=assets.fadePalettes[(nameEnter-1)/4];
            for(auto& shade:screen)shade=(palette>>(shade*2))&3;}
        return screen;
    }
    if(phase==UiPhase::Instructions){
        auto screen=renderMap(assets.instructions[stunt].tiles,map,scroll);
        if(instructionEnter){
            if(instructionAlternate){
                int bit=63-instructionEnter;
                if(bit<0||((assets.instructionPattern[bit/8]>>(bit%8))&1))return outroScene;
            }else{int palette=assets.fadePalettes[std::min(7,(instructionEnter-1)/4)];
                for(auto& shade:screen)shade=(palette>>(shade*2))&3;}
        }
        if(instructionExit){int palette=assets.fadePalettes[std::min(7,(33-instructionExit)/4)];
            for(auto& shade:screen)shade=(palette>>(shade*2))&3;}
        return screen;
    }
    if(phase==UiPhase::Ending){
        if(endingEnter>33){auto screen=renderResult(objects);int palette=assets.fadePalettes[(65-endingEnter)/4];
            for(auto& shade:screen)shade=(palette>>(shade*2))&3;
            return screen;}
        auto canvas=assets.endings[campaign.current];overlay(canvas,assets.resultLayouts[7]);
        money(canvas,17,campaign.players[campaign.current].savings);auto screen=renderMap(assets.endingTiles,canvas);
        if(endingEnter){int palette=assets.fadePalettes[std::min(7,(endingEnter-1)/4)];
            for(auto& shade:screen)shade=(palette>>(shade*2))&3;}
        return screen;
    }
    if(phase==UiPhase::Result)return renderResult(objects);
    return {};
}
std::array<uint8_t,Width*Height> UiFlow::renderResult(bool objects) const{
        const auto& result=campaign.last;int portrait=result.success?(result.perfect?2:1):0;
        auto canvas=assets.resultTexts[resultText(stunt,result.flags)];overlay(canvas,assets.resultLayouts[portrait]);
        if(result.success){
            if(showSavings){overlay(canvas,assets.resultLayouts[3]);money(canvas,15,displaySavings);}
            if(showPay){overlay(canvas,assets.resultLayouts[4]);money(canvas,16,displayPay);
                if(result.perfect){canvas[16*32+10]=0x25;canvas[16*32+11]=3;}}
            if(showTime){overlay(canvas,assets.resultLayouts[5]);canvas[17*32+18]=(displayTime/10)%10+1;canvas[17*32+19]=displayTime%10+1;
                if(result.perfect){canvas[17*32+10]=0x25;canvas[17*32+11]=3;}}
            if(showFlags){overlay(canvas,assets.resultLayouts[6]);canvas[14*32+18]=(flagsHit/10)%10+1;canvas[14*32+19]=flagsHit%10+1;}
        }else if(result.gameOver){overlay(canvas,assets.resultLayouts[7]);money(canvas,17,campaign.players[campaign.current].savings);}
        auto screen=renderMap(assets.resultTiles[portrait],canvas);
        if(objects&&result.perfect){
            // The result screen uses 8x8 objects, behind nonzero background
            // colors, with the original ten-per-row and X/OAM overlap rules.
            for(int y=0;y<Height;++y){std::array<int,10> selected{};int count=0;
                for(int i=0;i<celebrationCount&&count<10;++i){const auto& sprite=celebrationSprites[i];
                    if(y>=sprite.y-16&&y<sprite.y-8)selected[count++]=i;}
                std::stable_sort(selected.begin(),selected.begin()+count,[&](int a,int b){return celebrationSprites[a].x<celebrationSprites[b].x;});
                for(int x=0;x<Width;++x)for(int n=0;n<count;++n){const auto& sprite=celebrationSprites[selected[n]];
                    int sx=x-sprite.x+8;if(sx<0||sx>=8)continue;
                    int color=assets.resultTiles[portrait][sprite.tile*64+(y-sprite.y+16)*8+sx];
                    if(!color)continue;
                    if(!screen[y*Width+x])screen[y*Width+x]=(0xc4>>(color*2))&3;
                    break;
                }
            }
        }
        if(resultFade){int palette=assets.fadePalettes[(resultFade-1)/4];for(auto& shade:screen)shade=(palette>>(shade*2))&3;}
        return screen;
}
}
