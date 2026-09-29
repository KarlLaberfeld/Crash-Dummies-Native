#include "game.h"
#include <algorithm>
#include <cstdio>
#include <cstring>
#include <fstream>
#include <stdexcept>

namespace ticd {
static int s8(int x) { return static_cast<int8_t>(x); }
static int approach(int x,int target) { return x+(x<target)-(x>target); }
struct Reader {
    std::vector<uint8_t> bytes; size_t pos=0;
    explicit Reader(const std::wstring& path) {
        FILE* f=_wfopen(path.c_str(),L"rb");
        if(!f)throw std::runtime_error("crash.dat fehlt. Bitte zuerst build.ps1 mit der Original-ROM ausfuehren.");
        fseek(f,0,SEEK_END);long size=ftell(f);rewind(f);
        if(size<8 || size>4*1024*1024){fclose(f);throw std::runtime_error("Ungueltige Datendatei.");}
        bytes.resize(size);size_t got=fread(bytes.data(),1,bytes.size(),f);fclose(f);
        if(got!=bytes.size())throw std::runtime_error("Datendatei unvollstaendig.");
    }
    void raw(void* p,size_t n){if(n>bytes.size()-pos)throw std::runtime_error("Datendatei abgeschnitten.");memcpy(p,bytes.data()+pos,n);pos+=n;}
    int byte(){uint8_t v;raw(&v,1);return v;}
    int word(){int l=byte();return l|(byte()<<8);}
    int signedWord(){return static_cast<int16_t>(word());}
};
Assets Assets::load(const std::wstring& path) {
    Reader r(path);char magic[8];r.raw(magic,8);
    if(memcmp(magic,"TICDNAT4",8))throw std::runtime_error("Falsches Datenformat. Bitte Daten mit build.ps1 neu extrahieren.");
    Assets a;r.raw(a.title.data(),a.title.size());r.raw(a.font.data(),a.font.size());
    for(auto& f:a.frames){r.raw(f.meta.data(),8);r.raw(f.pixels.data(),f.pixels.size());}
    for(auto& level:a.levels){
        level.height=r.word();level.quota=r.word();level.seconds=r.word();level.fireHits=r.word();int count=r.word();
        if(level.height<176||level.height>4096||level.height%16||count>512||level.seconds>99||level.fireHits>20)throw std::runtime_error("Ungueltige Leveldaten.");
        level.pixels.resize(Width*level.height);r.raw(level.pixels.data(),level.pixels.size());
        for(int j=0;j<count;++j){Placement p;p.kind=r.byte();p.x=r.word();p.y=r.word();if(p.kind>=16)throw std::runtime_error("Ungueltiger Objekttyp.");level.objects.push_back(p);}
    }
    for(auto& d:a.definitions){d.frame=r.byte();d.flags=r.byte();d.handler=static_cast<Handler>(r.byte());d.collision=r.byte();for(auto& p:d.params)p=r.byte();}
    int starts=r.word(),commands=r.word();
    if(starts!=25||commands<1||commands>4096)throw std::runtime_error("Ungueltige Animationstabelle.");
    for(int i=0;i<starts;++i)a.animationStarts.push_back(r.word());
    a.commands.push_back({});
    for(int i=0;i<commands;++i){Command c;c.op=r.byte();c.a=r.signedWord();c.b=r.signedWord();c.c=r.signedWord();c.next=r.word();a.commands.push_back(c);}
    r.raw(a.hudTiles.data(),a.hudTiles.size());r.raw(a.hudMap.data(),a.hudMap.size());
    r.raw(a.hudColumns.data(),a.hudColumns.size());r.raw(a.cloudSpeeds.data(),a.cloudSpeeds.size());
    r.raw(a.transferChunks.data(),a.transferChunks.size());
    for(int col:a.hudColumns)if(col>=20)throw std::runtime_error("Ungueltige Statuszeile.");
    for(const auto& c:a.commands){
        if(c.op<0||c.op>19||c.next<0||c.next>commands||(c.op==10&&(c.a<=0||c.a>commands))||(c.op==4&&(c.a<0||c.a>=69))||(c.op==11&&(c.a<0||c.a>29)))throw std::runtime_error("Ungueltiger Animationsbefehl.");
    }
    for(int i:a.animationStarts)if(i<=0||i>commands)throw std::runtime_error("Ungueltiger Animationseinstieg.");
    for(const auto& d:a.definitions)if(d.frame>=69||static_cast<int>(d.handler)>29)throw std::runtime_error("Ungueltige Objektdefinition.");
    auto validPixels=[](const auto& p,bool transparent){return std::all_of(p.begin(),p.end(),[=](int v){return v<4||(transparent&&v==255);});};
    if(!validPixels(a.title,false)||!validPixels(a.font,false)||!validPixels(a.hudTiles,false))throw std::runtime_error("Ungueltige Bilddaten.");
    for(const auto& f:a.frames)if(!validPixels(f.pixels,true))throw std::runtime_error("Ungueltige Spritedaten.");
    for(const auto& l:a.levels)if(!validPixels(l.pixels,false))throw std::runtime_error("Ungueltige Hintergrunddaten.");
    if(r.pos!=r.bytes.size())throw std::runtime_error("Unerwartete Daten am Dateiende.");
    return a;
}

void Game::start(int level) {
    difficulty=std::clamp(level,0,3);entities={};placements=assets.levels[difficulty].objects;
    const auto& l=assets.levels[difficulty];
    ticks=0;seconds=l.seconds;secondTicks=0;money=0;remaining=l.quota;fireHits=l.fireHits;
    breaksNeeded=10;camera=(l.height-152)*16;cameraLead=cameraLeadTarget=24;
    scan=0;introCounter=128;finishTimer=64;result=pendingResult=resultFlags=0;previous=held=pressed=0;
    paused=false;launched=false;hazardsActive=false;targetReached=false;started=true;animationFaults=0;
    transferState=transferRemaining=transferFrame=transferFlags=0;lastMapCamera=camera+128;mapTransfer=true;
    spawn(0,0x1290,0x0150);
    spawn(15,0x1a00,0);
    hudMap=assets.hudMap;hudCursor=0;refreshHud();
    for(int j=0;j<13;++j)hudMap[assets.hudColumns[j]]=hudValues[j];
}
int Game::spawn(int kind,int x,int y,int placement) {
    if(kind<0||kind>=16)return -1;
    for(int i=0;i<16;++i)if(!entities[i].alive){
        Entity e;const auto& d=assets.definitions[kind];
        e.alive=true;e.kind=kind;e.frame=d.frame;e.flags=d.flags;e.hidden=(d.flags&8)!=0;
        e.handler=d.handler;e.collision=d.collision;e.x=x;e.y=y;e.placement=placement;
        e.vy=s8(d.params[0]);e.pose=d.params[1];e.vx=s8(d.params[2]);e.counter=d.params[3];
        e.cloudX={d.params[0]|(d.params[1]<<8),d.params[4]|(d.params[5]<<8)};
        e.cloudSpeed={d.params[2]&7,d.params[6]&7};
        entities[i]=e;return i;
    }
    return -1;
}
void Game::destroy(int i) {
    // 00:3da5 only frees the live slot. Collected/destroyed placements stay used.
    entities[i].alive=false;
}
void Game::startAnimation(int i,int sequence,bool force) {
    auto& e=entities[i];if(!force&&!e.animDone)return;
    e.anim=assets.animationStarts.at(sequence);e.animDone=false;
}
void Game::animate(int i) {
    auto& e=entities[i];if(e.animDone||!e.alive)return;
    if(e.delay>0){--e.delay;return;}
    for(int safeguard=0;safeguard<256;++safeguard){
        if(e.anim<=0||e.anim>=static_cast<int>(assets.commands.size())){++animationFaults;e.animDone=true;return;}
        int commandIndex=e.anim;auto c=assets.commands[e.anim];e.anim=c.next;
        switch(c.op){
        case 0:e.animDone=true;return;
        case 1:e.delay=e.period;return;
        case 2:e.x+=c.a;break;
        case 3:e.y+=c.a;break;
        case 4:
            if(c.a<35){
                if(e.frameWaiting){
                    if(transferState!=2){e.anim=commandIndex;return;}
                    e.frameWaiting=false;break;
                }
                if(e.frame!=c.a){e.frame=c.a;e.frameWaiting=true;e.anim=commandIndex;return;}
            }
            e.frame=c.a;break;
        case 5:e.period=c.a;break;
        case 6:e.flags^=32;break;
        case 7:e.flags&=~32;break;
        case 8:e.loop=c.a;e.loopStart=e.anim;break;
        case 9:if(--e.loop>0)e.anim=e.loopStart;e.delay=e.period;return;
        case 10:e.anim=c.a;break;
        case 11:e.handler=static_cast<Handler>(c.a);e.animDone=true;return;
        case 12:e.x+=c.a*16;break;
        case 13:e.y+=c.a*16;break;
        case 14:destroy(i);e.animDone=true;return;
        case 15:e.hidden=!e.hidden;break;
        case 16:spawn(c.c,e.x+c.a,e.y+c.b);break;
        case 17:e.flags|=32;break;
        case 18:launched=true;break;
        case 19:break; // Audio event retained in data; sound driver not ported yet.
        default:++animationFaults;e.animDone=true;return;
        }
    }
    ++animationFaults;e.animDone=true;
}
void Game::gravity(Entity& e) { e.vy=approach(e.vy,e.pose); }
void Game::moveFalling(Entity& e) {
    e.y+=e.vy;e.x=std::clamp(e.x+e.vx,0x1040,0x1880);
}
void Game::followCamera(const Entity& e) {
    if((ticks&7)==0)cameraLead=approach(cameraLead,cameraLeadTarget);
    int difference=(e.y/16-camera/16)-cameraLead;
    camera=std::clamp(camera+difference,0,(assets.levels[difficulty].height-152)*16);
}
void Game::followParent(Entity& e) {
    if(e.parent>=0&&e.parent<16&&entities[e.parent].alive){e.x=entities[e.parent].x+e.offsetX*16;e.y=entities[e.parent].y+e.offsetY*16;}
}
void Game::finish(int i,int code) {
    // 01:59b6 falls directly into 59be: the first countdown tick is immediate.
    pendingResult=code;entities[i].handler=Handler::FinishDelay;
    if(--finishTimer==0)result=pendingResult;
}
void Game::tickTimer() {
    if(++secondTicks==60){secondTicks=0;if(seconds>0)--seconds;}
}
void Game::beginVideoTick() {
    if(transferRemaining&&!mapTransfer){
        transferRemaining=std::max(0,transferRemaining-4);
        if(!transferRemaining){entities[0].frame=transferFrame;entities[0].flags=transferFlags;transferState=2;}
    }
}
void Game::finishVideoTick(int oldFrame,int oldFlags) {
    // Original resource queue, 00:3f30. No SM83 instructions are executed.
    if(transferState==2)transferState=0;
    auto& p=entities[0];
    if(p.frame<35&&p.frame!=oldFrame){
        if(!transferState){transferState=1;transferFrame=-1;}
        if(p.frame!=transferFrame){
            transferRemaining=assets.transferChunks[p.frame];
            if(!transferRemaining)return;
            transferFrame=p.frame;transferFlags=p.flags;
        }
        p.frame=oldFrame;p.flags=oldFlags;
    }
}
void Game::land(int i) {
    auto& e=entities[i];
    // 01:5722 checks the 16-pixel row, then snaps to the following row.
    const int row=assets.levels[difficulty].height/16-2;
    if((e.y>>8)!=row)return;
    e.y=(row+1)*256;
    if(targetReached){
        e.frame=29;e.flags&=31;e.animDone=true;e.handler=Handler::Idle;
        resultFlags=breaksNeeded>=0?0x81:remaining!=0?0x03:0x07;
        pendingResult=(resultFlags&2)?3:5;
        spawn(4,e.x,e.y);
        spawn(9,e.x-16,e.y+128);spawn(10,e.x+80,e.y+128);
        spawn(11,e.x,e.y-128); // This piece starts the result countdown at 01:591b.
        spawn(12,e.x+128,e.y-96);spawn(13,e.x-96,e.y-96);
    }else{
        resultFlags=1;pendingResult=1;
        if(e.pose==28){
            spawn(4,e.x,e.y);e.handler=Handler::Animation;startAnimation(i,19,true);
        }else{
            e.frame=25;e.flags&=31;e.animDone=true;
            spawn(4,e.x+64,e.y);finish(i,1);
        }
    }
}
void Game::decrementGoal(int other) {
    auto& e=entities[other];
    if(e.placement>=0&&placements[e.placement].state==0){--remaining;--breaksNeeded;placements[e.placement].state=1;}
}
void Game::collideWith(int player,int other) {
    auto& p=entities[player];auto& o=entities[other];
    switch(o.collision){
    case 0: // 01:5c8b, cloth awning, five hits or immediate head-first break.
        if(o.placement>=0){
            auto& state=placements[o.placement].state;
            if(state>=5)break;
            if(p.pose==20||p.pose==28){
                if(p.pose==20){p.pose=24;startAnimation(player,7,true);}
                state=5;--remaining;--breaksNeeded;money+=10;
            }else{
                if(p.vy<0)break;
                int old=state++;
                if(old==4){--remaining;--breaksNeeded;money+=5;}
                else{p.vy=-((4-old)*4+24)-1;startAnimation(other,13);startAnimation(player,14,true);p.handler=Handler::Bounce;money+=2;}
            }
        }break;
    case 1: // 01:5bdb, balloon ride only in neutral posture.
        if(p.pose!=24)break;
        p.frame=18;p.handler=Handler::BalloonRide;p.vy=0;p.vx=0;p.counter=192;
        p.parent=other;p.offsetX=2;p.offsetY=31;o.collision=255;o.vy=12;
        decrementGoal(other);cameraLeadTarget=48;money+=5;break;
    case 2: // 01:5ad9, fire extinguishes on contact and costs money.
        if(o.placement>=0&&placements[o.placement].state)break;
        if(o.placement>=0)placements[o.placement].state=1;
        o.collision=255;startAnimation(other,10,true);spawn(4,o.x,o.y);money=std::max(0,money-10);
        if(--fireHits==0){p.handler=Handler::Animation;p.vy=-32;startAnimation(player,11,true);}
        break;
    case 3: // 01:5df4, pole/rope catch requires lateral movement in neutral pose.
        if(p.vy<0)break;
        if(p.pose==24){
            if(!(held&(Left|Right)))break;
            p.frame=19;p.flags=(p.flags&~32)|((held&Right)?32:0);p.vx=(held&Right)?17:-17;
            p.handler=Handler::Rope;p.parent=other;p.offsetX=2;p.offsetY=0;
            startAnimation(player,16,true);startAnimation(other,17,true);money+=25;decrementGoal(other);
        }else{startAnimation(other,18,true);o.collision=255;decrementGoal(other);money+=10;}
        break;
    case 4: // 01:5dbd, plane hit and temporary stun.
        o.frame=53;o.handler=Handler::PlaneStun;o.collision=255;money=std::max(0,money-20);break;
    case 5: // 01:5ef3, solid balcony breaks on first collision.
        if(o.placement>=0&&!placements[o.placement].state){
            decrementGoal(other);spawn(4,o.x+128,o.y);
            if(p.pose==24){p.vy=-4;money+=5;}
            else{if(p.pose==20){p.pose=24;startAnimation(player,7,true);}money+=10;}
        }break;
    case 6: // 01:5f29, collect target and set landing flag.
        --remaining;--breaksNeeded;money+=100;targetReached=true;destroy(other);break;
    default:break;
    }
}
void Game::collide(int i) {
    const auto box=[this](const Entity& e){
        const auto& m=assets.frames[e.frame].meta;
        return std::array<int,4>{e.x/16+s8(m[0])+s8(m[2]),e.y/16+s8(m[1])+s8(m[3]),m[4],m[5]};
    };
    auto a=box(entities[i]);
    for(int j=0;j<16;++j)if(j!=i&&entities[j].alive&&!entities[j].offscreen&&entities[j].collision!=255){
        auto b=box(entities[j]);
        if(a[0]+a[2]>=b[0]&&a[0]<b[0]+b[2]&&a[1]+a[3]>=b[1]&&a[1]<b[1]+b[3])collideWith(i,j);
    }
}
void Game::update(int i) {
    auto& e=entities[i];
    switch(e.handler){
    case Handler::IntroPan:if(--introCounter==0){e.handler=Handler::IntroRise;update(i);}break;
    case Handler::IntroRise:
        camera+=s8(introCounter);
        if(static_cast<uint8_t>(introCounter-1)!=127)introCounter=static_cast<uint8_t>(introCounter-1);
        if(camera<0x600){hazardsActive=true;e.handler=Handler::IntroAnimation;startAnimation(i,0);}
        break;
    case Handler::IntroAnimation:animate(i);followCamera(e);break;
    case Handler::RoofWait:
        animate(i);
        if(e.counter>0){
            if((held&Left)&&e.x!=0x1050)startAnimation(i,2);
            if((held&Right)&&e.x!=0x1830)startAnimation(i,3);
            if(!(held&(A|B))){if(!(ticks&1))--e.counter;break;}
        }
        if(e.animDone){e.handler=Handler::Animation;startAnimation(i,1,true);}
        break;
    case Handler::Falling:
    case Handler::Bounce:
    case Handler::RopeRelease:{
        Handler before=e.handler;animate(i);
        if(before==Handler::Falling&&e.animDone){
            e.frame=e.pose==20?34:e.pose==28?12:e.vx==0?9:13;
            e.flags=(e.flags&31)|((e.pose==24&&e.vx<0)?32:0);
        }
        followCamera(e);
        if(before!=Handler::RopeRelease){if(held&Left)e.vx=-10;if(held&Right)e.vx=10;}
        if(before==Handler::Falling&&e.animDone){
            if((pressed&Up)&&e.pose!=20){bool neutral=e.pose!=24;e.pose=neutral?24:20;startAnimation(i,neutral?4:5,true);}
            if((pressed&Down)&&e.pose!=28&&e.animDone){bool neutral=e.pose==20;e.pose=neutral?24:28;startAnimation(i,neutral?7:6,true);}
        }
        collide(i);moveFalling(e);gravity(e);
        if(before!=Handler::RopeRelease||(ticks&15)==0)e.vx=approach(e.vx,0);
        tickTimer();
        // Only the main fall handler checks time/ground (01:571c).
        // Bounce and rope-release finish their current routines first.
        if(before==Handler::Falling){
            if(seconds==0){e.handler=Handler::Timeout;update(i);}
            else land(i);
        }
        break;}
    case Handler::Timeout:e.y+=e.vy;gravity(e);if(e.offscreen){resultFlags=0x11;finish(i,2);}break;
    case Handler::Finish:finish(i,pendingResult?pendingResult:1);break;
    case Handler::FinishDelay:if(--finishTimer<=0)result=pendingResult;break;
    case Handler::Animation:animate(i);break;
    case Handler::Fire:
        e.handler=Handler::Animation;
        if(e.placement<0||!placements[e.placement].state)e.collision=2;
        startAnimation(i,e.placement>=0&&placements[e.placement].state?9:8);break;
    case Handler::Awning:
        if(e.placement>=0&&placements[e.placement].state==5){e.frame=44;e.collision=255;}
        else animate(i);break;
    case Handler::Platform:
        if(e.placement>=0&&placements[e.placement].state){e.frame=61;e.collision=255;}
        break;
    case Handler::Puff:e.handler=Handler::Animation;startAnimation(i,12);break;
    case Handler::Balloon:
        if(!hazardsActive){e.flags|=20;break;}
        if((ticks&3)==0&&e.vy!=-8)--e.vy;e.y+=e.vy;
        if((camera>>8)>=(e.y>>8)+2)destroy(i);
        break;
    case Handler::Burst:e.frame=40;if(--e.vy==0)destroy(i);break;
    case Handler::BalloonRide:
        followCamera(e);followParent(e);
        tickTimer();
        if((held&(A|B))||(!(ticks&1)&&--e.counter==0)){
            e.handler=Handler::Falling;
            if(e.parent>=0){entities[e.parent].handler=Handler::Burst;entities[e.parent].vy=16;}
            cameraLeadTarget=24;
        }break;
    case Handler::Rope:
        animate(i);followCamera(e);followParent(e);
        if(e.animDone){e.vy=-32;e.x+=(e.flags&32)?0:-384;startAnimation(i,14,true);e.handler=Handler::RopeRelease;}
        break;
    case Handler::Plane:if(hazardsActive){e.handler=Handler::PlaneFly;startAnimation(i,15);}else e.flags|=20;break;
    case Handler::PlaneFly:
        animate(i);
        if(e.x<0x0e00||e.x>=0x1b00)destroy(i);
        e.x+=e.vy;e.y+=s8(e.pose);
        if(e.y<entities[0].y){if(s8(e.pose)<8)e.pose=static_cast<uint8_t>(s8(e.pose)+1);}
        else if(s8(e.pose)>-8)e.pose=static_cast<uint8_t>(s8(e.pose)-1);
        break;
    case Handler::PlaneStun:e.vx=static_cast<uint8_t>(e.vx-1);if(e.vx==0)e.handler=Handler::PlaneFly;break;
    case Handler::Burning:
        moveFalling(e);gravity(e);if(!(ticks&7))e.vx=approach(e.vx,0);
        if(!(ticks&15))spawn(4,e.x+64,e.y);
        if(e.offscreen){resultFlags=0x21;finish(i,4);}break;
    case Handler::LimbLeft:case Handler::LimbRight:case Handler::LimbUp:
    case Handler::LimbSideRight:case Handler::LimbSideLeft:{
        int sequence=20+static_cast<int>(e.handler)-static_cast<int>(Handler::LimbLeft);
        e.handler=Handler::Animation;startAnimation(i,sequence);break;}
    case Handler::BackgroundCloud:{
        // 01:5f40 multiplexes two clouds in a single entity slot, one per frame.
        int cloud=ticks&1;
        e.cloudX[cloud]+=s8(assets.cloudSpeeds[e.cloudSpeed[cloud]]);
        e.x=e.cloudX[cloud];e.y=cloud?0x90:-0x10;
        if(e.x==0x0d80){e.cloudX[cloud]=0x1a00;e.cloudSpeed[cloud]=(e.cloudSpeed[cloud]+1)&7;}
        break;}
    case Handler::Idle:break;
    }
}
void Game::step(int buttons) {
    if(!started||paused||result)return;
    held=buttons;pressed=buttons&~previous;previous=buttons;++ticks;beginVideoTick();
    tickHud();
    int oldFrame=entities[0].frame,oldFlags=entities[0].flags;
    for(int i=0;i<16;++i)if(entities[i].alive)update(i);
    finishVideoTick(oldFrame,oldFlags);
    updateVisibility();
    mapTransfer=((lastMapCamera^camera)&128)!=0;lastMapCamera=camera;
    // The original scans eight records per frame (00:19a2), with 16 live slots.
    for(int k=0;k<8&&!placements.empty();++k){
        auto& p=placements[scan];int low=camera>>8,high=low+14;
        int row=(p.y>>8)+3;
        if(!p.active&&low<row&&high>=row){int id=spawn(p.kind,p.x,p.y,scan);if(id>=0)p.active=true;}
        scan=(scan+1)%static_cast<int>(placements.size());
    }
}

void Game::refreshHud() {
    // 00:2e9b displays player number, the low four BCD score digits, seconds,
    // then six height-bar tiles. The counter is camera-based, not goal-based.
    hudValues[0]=0xf7; // First player; campaign/multiplayer is not ported yet.
    int score=money%10000;
    hudValues[1]=0xf6+score/1000;hudValues[2]=0xf6+(score/100)%10;
    hudValues[3]=0xf6+(score/10)%10;hudValues[4]=0xf6+score%10;
    hudValues[5]=0xf6+seconds/10;hudValues[6]=0xf6+seconds%10;
    int bar=48-((camera>>8)*48)/(assets.levels[difficulty].height/16-10);
    bar=static_cast<uint8_t>(bar);
    for(int j=7;j<13;++j){
        if(bar>=8){hudValues[j]=0x78;bar-=8;}
        else if(bar>0){hudValues[j]=0x78+(bar^7);bar=0;}
        else hudValues[j]=0;
    }
}
void Game::tickHud() {
    // 00:3198 updates one tile per frame; 00:2e9b refreshes the source buffer
    // only after all thirteen updates. Preserve its visible score/time lag.
    hudMap[assets.hudColumns[hudCursor]]=hudValues[hudCursor];
    hudCursor=(hudCursor+1)%13;
    if(hudCursor==0)refreshHud();
}
void Game::drawHud() {
    for(int col=0;col<20;++col)for(int y=0;y<8;++y)for(int x=0;x<8;++x)
        screen[(PlayHeight+y)*Width+col*8+x]=assets.hudTiles[hudMap[col]*64+y*8+x];
}
void Game::updateVisibility() {
    // 00:1cb6-1cf6 tests the frame's padded bounds; 1c7c handles removal.
    // This belongs to the simulation tick, independent of Windows repaint rate.
    for(int i=0;i<16;++i)if(entities[i].alive){
        auto& e=entities[i];e.offscreen=false;if(e.hidden)continue;
        const auto& m=assets.frames[e.frame].meta;
        int x=(e.x>>4)-256+s8(m[0]),y=(e.y>>4)-(camera>>4)+s8(m[1]);
        bool outside=x < -2*m[6]-16||x>176||y < -2*m[7]-16||y>152;
        if(outside){
            if(e.flags&16){
                if((e.flags&4)&&e.placement>=0)placements[e.placement].active=false;
                destroy(i);
            }else e.offscreen=true;
        }
    }
}

void Game::drawFrame(int number,int x,int y,int flags) {
    if(number<0||number>=69)return;
    const auto& f=assets.frames[number];
    for(int sy=0;sy<96;++sy)for(int sx=0;sx<96;++sx){
        int value=f.pixels[sy*96+sx];if(value==255)continue;
        int dx=x+((flags&32)?2*(s8(f.meta[0])+f.meta[6])+47-sx:sx-48);
        int dy=y+((flags&64)?2*(s8(f.meta[1])+f.meta[7])+47-sy:sy-48);
        if(dx>=0&&dx<Width&&dy>=0&&dy<PlayHeight)screen[dy*Width+dx]=static_cast<uint8_t>(value);
    }
}
void Game::text(int x,int y,const std::string& value) {
    for(char c:value){
        int n=c==' '?0:c>='0'&&c<='9'?c-'0'+1:c>='A'&&c<='Z'?c-'A'+11:c=='-'?39:c==':'?40:c=='!'?46:0;
        for(int py=0;py<8;++py)for(int px=0;px<8;++px){int dx=x+px,dy=y+py;if(dx>=0&&dx<Width&&dy>=0&&dy<Height)screen[dy*Width+dx]=assets.font[n*64+py*8+px];}
        x+=8;
    }
}
void Game::render() {
    screen.fill(0);
    if(!started){
        // A clearly labeled development launcher, not an invented original menu.
        const auto& l=assets.levels[difficulty];
        std::copy(l.pixels.begin(),l.pixels.begin()+Width*Height,screen.begin());
        std::fill(screen.begin()+Width*72,screen.begin()+Width*136,0);
        text(8,78,"NATIVE PORT - WIP");text(16,94,"1  ROOF JUMP");
        text(16,110,"ENTER TO START");text(16,126,"1-4 DIFFICULTY");return;
    }
    const auto& l=assets.levels[difficulty];
    for(int y=0;y<PlayHeight;++y){int row=camera/16+y;if(row>=0&&row<l.height)std::copy_n(l.pixels.begin()+row*Width,Width,screen.begin()+y*Width);}
    for(int i=15;i>=0;--i){const auto& e=entities[i];if(e.alive&&!e.hidden)drawFrame(e.frame,e.x/16-256,e.y/16-camera/16,e.flags);}
    drawHud();
    if(paused||result){
        for(int y=48;y<104;++y)std::fill_n(screen.begin()+y*Width+8,144,0);
        text(40,56,paused?"PAUSED":"STUNT END");
        if(!paused)text(16,72,result==3?"TARGET REACHED":result==5?"MORE BREAKS!":"TRY AGAIN");
        text(16,88,paused?"ESC TO RESUME":"R TO RESTART");
    }
}

void saveBmp(const std::wstring& path,const std::array<uint8_t,Width*Height>& screen) {
    FILE* f=_wfopen(path.c_str(),L"wb");if(!f)throw std::runtime_error("Bilddatei konnte nicht gespeichert werden.");
    auto u16=[&](uint16_t v){fputc(v&255,f);fputc(v>>8,f);};
    auto u32=[&](uint32_t v){u16(v&65535);u16(v>>16);};
    const uint32_t palette[]={0xe0eecd,0x8dac74,0x395841,0x111f1d};
    fputc('B',f);fputc('M',f);u32(54+Width*Height*4);u32(0);u32(54);
    u32(40);u32(Width);u32(Height);u16(1);u16(32);u32(0);u32(Width*Height*4);u32(2835);u32(2835);u32(0);u32(0);
    for(int y=Height-1;y>=0;--y)for(int x=0;x<Width;++x)u32(palette[screen[y*Width+x]&3]);
    fclose(f);
}
}
