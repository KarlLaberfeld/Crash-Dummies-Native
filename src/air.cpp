#include "air.h"
#include "air_work.h"
#include "air_video_work.h"
#include "sprites.h"
#include <algorithm>
#include <cstdio>
#include <cstring>
#include <stdexcept>

namespace ticd {
namespace {
int s8(int n){return static_cast<int8_t>(n);}
int s16(int n){return static_cast<int16_t>(n);}
int approach(int n,int target){return n+(n<target)-(n>target);}
int bcd(int n){return (n>>4)*10+(n&15);}
// Quantize positions separately, as 00:1c22 / 00:1747 do before subtracting.
int relativePixel(int position,int camera){return s16((position&0xfff0)-(camera&0xfff0))/16;}
struct AirReader {
    std::vector<uint8_t> data;size_t pos=0;
    explicit AirReader(const std::wstring& path){
        FILE* f=_wfopen(path.c_str(),L"rb");
        if(!f)throw std::runtime_error("air.dat is missing. Run build.ps1 with the original ROM.");
        fseek(f,0,SEEK_END);long size=ftell(f);rewind(f);
        if(size<8||size>2*1024*1024){fclose(f);throw std::runtime_error("Invalid Air Bumper data size.");}
        data.resize(size);size_t n=fread(data.data(),1,data.size(),f);fclose(f);
        if(n!=data.size())throw std::runtime_error("Could not read Air Bumper data.");
    }
    void raw(void* out,size_t n){if(n>data.size()-pos)throw std::runtime_error("Truncated Air Bumper data.");memcpy(out,data.data()+pos,n);pos+=n;}
    int byte(){uint8_t v;raw(&v,1);return v;}
    int word(){int lo=byte();return lo+(byte()<<8);}
};
void check(bool ok){if(!ok)throw std::runtime_error("Invalid Air Bumper asset record. Rebuild the local data.");}
}
AirAssets AirAssets::load(const std::wstring& path){
    AirReader r(path);char magic[8];r.raw(magic,8);check(!memcmp(magic,"TICDAIR5",8));
    AirAssets a;r.raw(a.tiles.data(),a.tiles.size());r.raw(a.quadrants.data(),a.quadrants.size());r.raw(a.collision.data(),a.collision.size());
    for(auto& f:a.frames){r.raw(f.meta.data(),8);r.raw(f.pixels.data(),f.pixels.size());readSpritePieces(r,f);}
    for(auto& l:a.levels){
        l.cameraX=r.word();l.cameraY=r.word();l.seconds=r.byte();l.quota=r.byte();l.rows=r.word();int count=r.word();
        check(l.rows>=9&&l.rows<=256&&l.seconds<=99&&l.quota>0&&count<=512);
        r.raw(l.cells.data(),l.cells.size());
        for(int j=0;j<count;++j){Placement p;p.kind=r.byte();p.x=r.word();p.y=r.word();check(p.kind>=18&&p.kind<=30);l.objects.push_back(p);}
        for(int v:l.cells)check(v<128);
    }
    for(auto& d:a.definitions){d.frame=r.byte();d.flags=r.byte();int h=r.byte();d.handler=static_cast<AirHandler>(h);d.collision=r.byte();r.raw(d.params.data(),7);check(d.frame<59&&h<=26);}
    int roots=r.word(),count=r.word();check(roots==13&&count>0&&count<=4096);
    for(int j=0;j<roots;++j){int root=r.word();check(root>0&&root<=count);a.animationStarts.push_back(root);}
    a.commands.push_back({});
    for(int j=0;j<count;++j){
        Command c;c.op=r.byte();c.a=s16(r.word());c.b=s16(r.word());c.c=s16(r.word());c.next=r.word();
        check(c.op<=19&&c.next<=count);
        if(c.op==10)check(c.a>0&&c.a<=count);
        if(c.op==11)check(c.a>=0&&c.a<=26);
        if(c.op==4)check(c.a>=0&&c.a<59);
        if(c.op==16)check(c.c>=17&&c.c<=34);
        a.commands.push_back(c);
    }
    for(auto& pose:a.probes)for(auto& probe:pose)for(auto& axis:probe)axis=s16(r.word());
    for(auto& speed:a.speeds)speed=s8(r.byte());
    for(auto& pose:a.tilts)for(int j=0;j<4;++j)pose[j]=j>=2?s8(r.byte()):r.byte();
    r.raw(a.transferChunks.data(),a.transferChunks.size());
    r.raw(a.hudTiles.data(),a.hudTiles.size());r.raw(a.hudMap.data(),20);r.raw(a.hudColumns.data(),13);
    for(int col:a.hudColumns)check(col<20);
    for(int v:a.tiles)check(v<4);
    for(int v:a.hudTiles)check(v<4);
    for(int v:a.quadrants)check(v<128);
    for(const auto& f:a.frames)for(int v:f.pixels)check(v<4||v==255);
    for(const auto& p:a.tilts)check(p[0]>=0&&p[0]<59&&p[2]>=-2&&p[2]<=2&&p[3]==2);
    readSpriteResources(r,a.frames,12,13);
    check(r.pos==r.data.size());return a;
}

void AirGame::start(int level,int player){
    playerNumber=player&1;pendingSound=-1;sprites=SpriteLayer(false);reverseSprites=false;
    difficulty=std::clamp(level,0,3);const auto& l=assets.levels[difficulty];
    entities={};placements=l.objects;cameraX=l.cameraX;cameraY=l.cameraY;
    ticks=secondTicks=money=livesEarned=0;seconds=l.seconds;
    cameraLead=cameraLeadTarget=176;tilt=speed=rate=lastForce=returnX=returnY=0;
    scan=hudCursor=result=resultFlags=held=pressed=previous=animationFaults=randomState=0;
    finishTimer=128;started=true;paused=false;videoTickPrepared=false;probes={};crashRecoveryPending=false;
    transferState=transferRemaining=transferFrame=transferFlags=0;
    lastMapCamera=(cameraY+128)&65535;mapTransfer=true;
    mapWorkCycles=placementWorkCycles=spriteWorkCycles=clearWorkCycles=0;
    spriteEntityWorkCycles.fill(0);spriteInputEntities={};
    resourceWorkCycles=animationWorkCycles=0;
    starterWorkCycles=cameraWorkCycles=0;animationWorkComplete=true;
    collisionScanWorkCycles=collisionCallbackWorkCycles=0;
    playerMotionWorkCycles=playerInputWorkCycles=0;complexBodyWorkCycles=entityWorkCycles=-1;
    displayWorkCycles=-1;displayFadeRemaining=8;
    handlerWorkCycles.fill(-2);handlerWorkKinds.fill(-1);
    spawn(17,cameraX+0x400,(cameraY&0xff00)+0x800);
    spawn(22,cameraX+0x100,(cameraY&0xff00)+0x100);
    spriteResources.reset(assets.frames[entities[0].frame]);
    hudMap=assets.hudMap;refreshHud();
    for(int j=0;j<13;++j)hudMap[assets.hudColumns[j]]=hudValues[j];
    publishVideo();
}
int AirGame::spawn(int kind,int x,int y,int placement){
    if(kind<17||kind>34)return -1;
    for(int j=0;j<16;++j)if(!entities[j].alive){
        const auto& d=assets.definitions[kind-17];AirEntity e;
        // 00:1acd changes only done/waiting in the animation block. A reused
        // slot retains its delay, period and script/loop cursors. Clearing
        // them advances the new object's first animation frame too early.
        const auto& previousEntity=entities[j];
        e.anim=previousEntity.anim;e.delay=previousEntity.delay;e.period=previousEntity.period;
        e.loop=previousEntity.loop;e.loopStart=previousEntity.loopStart;
        e.alive=true;e.kind=kind;e.frame=d.frame;e.flags=d.flags;e.collision=d.collision;
        e.handler=d.handler;e.params=d.params;e.x=x&65535;e.y=y&65535;e.placement=placement;
        entities[j]=e;return j;
    }
    return -1;
}
void AirGame::setFrame(int i,int frame,int flags){
    auto& e=entities[i];e.frame=frame;e.flags=(e.flags&31)|flags;e.animDone=true;e.frameWaiting=false;
}
void AirGame::startAnimation(int i,int sequence,bool force){
    if(measureWork)starterWorkCycles+=force?80:airStartAnimationWork(entities[i].animDone);
    auto& e=entities[i];if(!force&&!e.animDone)return;
    e.anim=assets.animationStarts.at(sequence);e.animDone=false;
}
void AirGame::animate(int i){
    auto& e=entities[i];if(!e.alive)return;
    auto work=[&](int cost){if(measureWork)animationWorkCycles+=cost;};
    if(e.animDone){work(64);return;}
    if(e.delay){work(104);--e.delay;return;}
    work(124); // 3bb3 eligibility/delay check and saved script cursor load.
    // 3bc4 loads the saved script position into a temporary cursor. Only
    // delay/loop-yield (3c41) saves it back. A pending dynamic frame (3c92)
    // exits without saving, so preceding commands run again on the next tick.
    int cursor=e.anim;
    for(int guard=0;guard<256;++guard){
        if(cursor<=0||cursor>=static_cast<int>(assets.commands.size()))break;
        auto c=assets.commands[cursor];cursor=c.next;
        work(124); // 3bcc command fetch and semantic command dispatch.
        switch(c.op){
        case 0:work(76);e.animDone=true;return;
        case 1:work(100);e.anim=cursor;e.delay=e.period;return;
        case 2:work(airAnimationMoveWork(e.x,c.a));e.move(c.a,0);break;
        case 3:work(airAnimationMoveWork(e.y,c.a));e.move(0,c.a);break;
        case 4:
            if(c.a<12){
                // 3c74's waiting flag belongs to the saved script block,
                // rather than a new resume position at the frame operand.
                if(e.frameWaiting){
                    if(transferState!=2){work(148);return;}
                    work(196);
                    e.frameWaiting=false;break;
                }
                if(e.frame!=c.a){work(268);e.frame=c.a;e.frameWaiting=true;return;}
                work(236);
            }else work(148);
            e.frame=c.a;break;
        case 5:work(72);e.period=c.a;break;
        case 6:work(108);e.flags^=32;break;
        case 7:work(100);e.flags&=~32;break;
        case 8:work(92);e.loop=c.a;e.loopStart=cursor;break;
        case 9:e.loop=(e.loop-1)&255;work(e.loop?176:156);if(e.loop)cursor=e.loopStart;e.anim=cursor;e.delay=e.period;return;
        case 10:work(48);cursor=c.a;break;
        case 11:work(192);e.handler=static_cast<AirHandler>(c.a);e.animDone=true;return;
        case 12:work(c.a<0?92+20+124+44:92+132+44);e.move(c.a*16,0);break;
        case 13:work(c.a<0?92+20+124+44:92+132+44);e.move(0,c.a*16);break;
        case 14:work(204);e.alive=false;e.animDone=true;return;
        case 15:work(108);e.flags^=8;break;
        case 16:{int slot=spawn(c.c,e.x+c.a,e.y+c.b);work(456+(slot<0?868:816+52*slot));break;}
        case 17:work(100);e.flags|=32;break;
        case 18:work(36);break; // Original stage activation event; unused by Air graphs.
        case 19:work(44);pendingSound=c.a;break;
        default:++animationFaults;animationWorkComplete=false;e.animDone=true;return;
        }
        work(12); // 3bd4 returns to the next animation command.
    }
    ++animationFaults;animationWorkComplete=false;e.animDone=true;
}
int AirGame::tileAt(int x,int y) const {
    x&=65535;y&=65535;
    int cell=assets.levels[difficulty].cells[(y>>8)*16+((x>>8)&15)];
    int quadrant=((x>>7)&1)|((y>>6)&2);
    return assets.quadrants[quadrant*128+cell];
}
int AirGame::terrainAt(int x,int y) const{return assets.collision[tileAt(x,y)];}
void AirGame::sampleProbes(int pose){
    const auto& p=entities[0];const auto& offsets=assets.probes.at(pose+2);
    for(int n=0;n<6;++n)probes[n]=terrainAt(p.x+offsets[n][0],p.y+offsets[n][1]);
}
void AirGame::followCamera(bool horizontal){
    if(measureWork)cameraWorkCycles+=airCameraWork(*this,horizontal);
    const auto& p=entities[0];
    if(horizontal)cameraX=(cameraX+s8(((p.x-cameraX)&4095)/16-64))&65535;
    int delta=s8((s16(p.y-cameraY)>>3)-cameraLead);
    cameraY=std::clamp(cameraY+delta,0,assets.levels[difficulty].cameraY);
}
void AirGame::movePlayer(){
    if(measureWork)playerMotionWorkCycles+=airPlayerMotionWork(*this);
    auto& p=entities[0];const auto& display=assets.tilts.at(tilt+2);
    if(!transferState)setFrame(0,display[0],display[1]);
    // 3d61 / 3d63 updates Z while approaching zero. The optional stored-pose
    // call at 65b7 is skipped on the expiration tick as well as an idle boost.
    p.params[3]=static_cast<uint8_t>(approach(s8(p.params[3]),0));
    bool boosted=p.params[3]!=0;
    const auto& motion=assets.tilts.at((boosted?s8(p.params[4]):tilt)+2);
    p.move(s8(motion[2]*rate),s8(motion[3]*rate));
    if(rate>=0&&(p.y>>8)==assets.levels[difficulty].rows-2)speed=0;
}
void AirGame::input(){
    if(measureWork)playerInputWorkCycles+=airInputWork(*this);
    if(!transferState&&!lastForce&&rate){if((held&Left)&&tilt>-2)--tilt;if((held&Right)&&tilt<2)++tilt;}
    auto up=[&]{if(!(ticks&3)){cameraLeadTarget=176;if(speed>-20)--speed;}};
    if((cameraY>>8)>=15){
        if(held&A)up();
        if((held&B)&&!(ticks&1)){cameraLeadTarget=96;if(speed<11)++speed;}
        if(!(held&(Up|Down))&&!(ticks&15))speed=approach(speed,0);
    }
    if(!(held&(Left|Right))&&!(ticks&3)&&!lastForce)tilt=approach(tilt,0);
    if((cameraY>>8)<15)up();
}
void AirGame::lookupRate(){rate=assets.speeds.at(speed+20);}
// 2430 publishes prepared objects; the display callback reads scroll before
// 03db runs the next entity update. Keep visible and prepared state separate.
void AirGame::publishVideo(){visibleSprites=sprites;visibleCameraX=cameraX;visibleCameraY=cameraY;}
void AirGame::beginVideoTick(bool resourceReady){
    if(measureWork)displayWorkCycles=airDisplayWork(mapTransfer,resourceReady,transferRemaining,hudCursor,
        ticks,displayFadeRemaining,entities[0].params[1],assets.levels[difficulty].quota).total();
    if(!(ticks&1)&&displayFadeRemaining)--displayFadeRemaining;
    publishVideo();
    // 00:0c3f / 00:1897: a map row has priority; otherwise copy at most four
    // 32-byte resource chunks. This models the original asset queue, not a CPU.
    if(resourceReady&&transferRemaining&&!mapTransfer){
        spriteResources.advance(assets.frames[transferFrame],transferRemaining);
        transferRemaining=std::max(0,transferRemaining-4);
        if(!transferRemaining){entities[0].frame=transferFrame;entities[0].flags=transferFlags;transferState=2;}
    }
}
void AirGame::finishVideoTick(int oldFrame,int oldFlags){
    // 00:3f30 runs after game handlers and before visibility / map preparation.
    if(transferState==2)transferState=0;
    auto& p=entities[0];
    if(p.frame<12&&p.frame!=oldFrame){
        if(!transferState){transferState=1;transferFrame=-1;}
        if(p.frame!=transferFrame){
            transferRemaining=assets.transferChunks[p.frame];
            if(!transferRemaining)return;
            transferFrame=p.frame;transferFlags=p.flags;
        }
        p.frame=oldFrame;p.flags=oldFlags;
    }
}
void AirGame::tickTimer(){if(++secondTicks==60){secondTicks=0;if(seconds)--seconds;}}
void AirGame::beginFinish(int flags){crashRecoveryPending=false;resultFlags=flags;entities[0].handler=AirHandler::FinishDelay;if(--finishTimer==0)result=resultFlags;}
void AirGame::damage(int amount){
    auto& value=entities[0].params[5];int sum=value+amount;value=static_cast<uint8_t>(sum);
    if(sum>255)beginFinish(0x21);
}
void AirGame::impact(){damage(16);pendingSound=10;speed=speed<0?9:-4;}
void AirGame::terrainBounce(){
    auto& p=entities[0];
    if(p.params[3]){if((probes[0]|probes[1]|probes[2]|probes[3]|probes[4]|probes[5])&0x43)p.params[3]=0;return;}
    int base=speed<0?0:3,mask=speed<0?0x41:0x43;
    int turn=0;
    if(probes[base]&mask)turn=speed<0?1:-1;
    else if(probes[base+1]&mask)turn=speed<0?-1:1;
    else if(probes[base+2]&mask){impact();return;}
    if(turn){if(tilt+turn<-2||tilt+turn>2)impact();else{tilt+=turn;lastForce=12;pendingSound=12;}}
}
void AirGame::walls(){
    if(speed>=0)return;
    auto& p=entities[0];
    if(probes[2]&2){
        speed=std::min(speed,-6);returnX=p.x;returnY=p.y;
        crashRecoveryPending=false;p.handler=AirHandler::Crash;p.params[0]=80;p.params[2]=255;startAnimation(0,0,true);
    }else if((probes[0]|probes[1])&2){
        if(tilt){impact();return;}
        setFrame(0,8,(probes[0]&2)?0:32);p.handler=AirHandler::WallSlide;p.params[0]=128;
        speed=std::min(speed,-6);
    }
}
void AirGame::finishGate(){
    if(speed>=0)return;
    int flags=(probes[0]|probes[1]|probes[2])&0x18;if(!flags)return;
    auto& p=entities[0];if(flags&8)money+=100;
    pendingSound=(flags&8)?9:4;p.handler=AirHandler::FinishMotion;impact();money+=50;setFrame(0,(p.params[5]&128)?11:7);
    int quota=assets.levels[difficulty].quota,collected=p.params[1];
    resultFlags=collected==quota?7:collected>quota/2?3:1;
}
int AirGame::randomByte(){
    // 00:1723; only the high seed byte is replaced. Menu-seeded initial phase
    // is not yet available, so each standalone run begins with seed zero.
    int swapped=((randomState&255)<<8)|(randomState>>8);
    int first=(randomState-swapped)&65535;
    int value=(first-swapped-(randomState<swapped)+254)&65535;
    int lo=value&255,hi=value>>8,out=(lo-hi-(lo>=hi))&255;
    randomState=(randomState&255)|(out<<8);return out;
}
void AirGame::collideWith(int other){
    auto& p=entities[0];auto& o=entities[other];if(!o.alive||o.collision==255)return;
    if(o.collision!=34&&o.collision!=13&&p.params[2])return;
    switch(o.collision){
    case 7:o.flags&=~4;o.collision=255;o.params[0]=static_cast<uint8_t>((ticks&31)-15);o.params[1]=224;++o.params[2];money+=2;startAnimation(other,2);break;
    case 8:++p.params[1];o.alive=false;money+=10;pendingSound=16;break;
    case 9:++o.frame;o.flags=16;o.handler=AirHandler::DebrisLeft;o.collision=255;impact();spawn(31,o.x+256,o.y);money+=10;damage(32);break;
    case 10:money+=bcd(o.params[0]);o.alive=false;pendingSound=18;break;
    case 11:p.params[3]=64;p.params[4]=static_cast<uint8_t>(tilt);o.collision=255;pendingSound=19;break;
    case 12:spawn(33,o.x,o.y);o.alive=false;damage(16);pendingSound=10;break;
    case 13:if(p.params[2]){++p.params[1];o.alive=false;money+=20;pendingSound=16;}break;
    case 14:
        if(speed==0){o.params[0]=static_cast<uint8_t>(-s8(o.params[0]));o.flags^=32;}
        else{money=std::max(0,money-50);o.handler=AirHandler::Animation;o.collision=255;startAnimation(other,10,true);}break;
    case 15:money+=bcd(o.params[0]);o.alive=false;p.params[5]=static_cast<uint8_t>(std::max(0,p.params[5]-32));pendingSound=17;break;
    case 34:++livesEarned;o.alive=false;pendingSound=9;break;
    default:break;
    }
}
void AirGame::collide(){
    if(measureWork)collisionScanWorkCycles+=644+airCollisionBoundsWork(*this,entities[0])
        +airCollisionSlotWork(*this,0).scan+36;
    auto box=[&](const AirEntity& e){return spriteBounds(assets.frames[e.frame],e.x,e.y,cameraX,cameraY);};
    auto a=box(entities[0]);
    for(int j=1;j<16;++j){const auto& e=entities[j];
        if(measureWork){auto work=airCollisionSlotWork(*this,j);
            collisionScanWorkCycles+=work.scan+(j==15?48:36);
            if(work.callback&&collisionCallbackWorkCycles>=0){
                int callback=airCollisionCallbackWork(*this,j);
                collisionCallbackWorkCycles=callback<0?-1:collisionCallbackWorkCycles+callback;
            }
        }
        if(!e.alive||e.offscreen||e.collision==255)continue;
        auto b=box(e);if(spriteOverlap(a,b))collideWith(j);
    }
}
void AirGame::update(int i){
    auto& e=entities[i];
    switch(e.handler){
    case AirHandler::Intro:e.handler=AirHandler::Rise;[[fallthrough]];
    case AirHandler::Rise:
        followCamera(false);e.move(0,s8(e.params[0]));
        if(++e.params[0])break;
        e.handler=AirHandler::Wait;e.params[0]=224;[[fallthrough]];
    case AirHandler::Wait:
        if(--e.params[0])break;e.handler=AirHandler::Play;[[fallthrough]];
    case AirHandler::Play:{
        int body=376+(measureWork?airCameraLeadWork(cameraLead,cameraLeadTarget):0);
        cameraLead=approach(cameraLead,cameraLeadTarget);followCamera();movePlayer();
        if(measureWork)body+=airSeverityWork(*this);
        int severity=e.params[5]>>6;
        if(severity==1&&(pressed&A))spawn(34,e.x,e.y+512);
        if((severity==2&&!(ticks&31))||(severity==3&&!(ticks&15))){
            speed=approach(speed,0);if(speed)spawn(34,e.x+(randomByte()&15)*16,e.y+384);
        }
        if(measureWork)body+=airTimerWork(secondTicks,seconds);
        tickTimer();if(!seconds){
            if(measureWork)complexBodyWorkCycles=body-16+(finishTimer==1?48:0)+cameraWorkCycles+playerMotionWorkCycles;
            beginFinish(0x11);break;
        }
        input();lookupRate();sampleProbes(tilt);lastForce=0;
        if(measureWork)body+=112+AirProbeWork+airTerrainBounceWork(*this);
        terrainBounce();
        if(measureWork)body+=airSidePushWork(*this);
        int base=speed<0?0:3;
        if(probes[base]&32){lastForce=4;e.move(4,0);}else if(probes[base+1]&32){lastForce=-4;e.move(-4,0);}
        if(measureWork)body+=airSlowSurfaceWork(*this);
        if(!(ticks&3)&&((probes[0]|probes[1]|probes[2])&4))speed=speed<0?-2:4;
        if(measureWork)body+=airWallWork(*this);
        walls();if(measureWork)body+=airFinishGateWork(*this);
        finishGate();collide();
        if(measureWork&&collisionCallbackWorkCycles>=0)complexBodyWorkCycles=body+cameraWorkCycles
            +playerMotionWorkCycles+playerInputWorkCycles+collisionScanWorkCycles+collisionCallbackWorkCycles;
        break;}
    case AirHandler::Animation:
        animate(i);
        if(i==0&&crashRecoveryPending&&e.animDone){
            crashRecoveryPending=false;startAnimation(i,1);
        }
        break;
    case AirHandler::FinishMotion:{
        int body=192+96+28+(tilt>=0?8:0)+40+136+20+airMoveWork(e.y,s8(2*rate))
            +((ticks&15)?44:60+airApproachByteWork(speed))+112+AirProbeWork;
        followCamera();e.move(0,s8(2*rate));if(!(ticks&15))speed=approach(speed,0);
        lookupRate();sampleProbes(tilt);
        if(measureWork)body+=airTerrainBounceWork(*this);
        terrainBounce();if(--finishTimer==0)result|=resultFlags;
        body+=44+(finishTimer==0?48:0);
        // 59be leaves HL on C095 when the countdown reaches zero. The
        // following phase test therefore reads the completed result byte.
        int phase=finishTimer?finishTimer:result;
        if(!(phase&7)){
            if(measureWork)body+=24+628+airSpawnRelativeWork(*this,false);
            int dx=(randomByte()&15)*16,dy=((randomByte()&15)+16)*16;spawn(33,e.x+dx,e.y+dy);
            // 611e returns on other countdown phases; 6158 then tests C097,
            // the finish countdown, rather than the global display counter.
            if(!(finishTimer&15))pendingSound=14;
            body+=((finishTimer&15)?44:84);
        }else body+=36;
        if(measureWork)complexBodyWorkCycles=body+cameraWorkCycles;
        break;}
    case AirHandler::WallSlide:{
        int body=148+airCameraLeadWork(cameraLead,cameraLeadTarget)+112+AirProbeWork-12;
        cameraLead=approach(cameraLead,cameraLeadTarget);followCamera();lookupRate();sampleProbes(0);
        if(measureWork)body+=airTerrainBounceWork(*this);
        terrainBounce();
        body+=48;
        if((probes[0]|probes[1]|probes[2])&0x7d){
            e.handler=AirHandler::Play;
            if(measureWork)complexBodyWorkCycles=body+12+112+cameraWorkCycles;
            break;
        }
        body+=8+64+airTimerWork(secondTicks,seconds);
        tickTimer();collide();
        if(rate>=0){
            e.handler=AirHandler::Play;body+=12+112;
        }else{
            body+=8+60+44+airMoveWork(e.y,s8(2*rate));
            e.move(0,s8(2*rate));
            body+=e.params[0]==1?8+112:20;
            if(--e.params[0]==0)e.handler=AirHandler::Play;
        }
        if(measureWork&&collisionCallbackWorkCycles>=0)complexBodyWorkCycles=body+cameraWorkCycles+collisionScanWorkCycles+collisionCallbackWorkCycles;
        break;}
    case AirHandler::Crash:{
        int animationBefore=animationWorkCycles;
        int body=304+44+112+airTimerWork(secondTicks,seconds);
        animate(i);followCamera();lookupRate();tickTimer();
        if(held&Left){if(measureWork)body+=12+24+airMoveWork(e.x,-16);e.move(-16,0);}
        if(held&Right){if(measureWork)body+=12+24+airMoveWork(e.x,16);e.move(16,0);}
        if(measureWork)body+=airMoveWork(e.y,s8(2*rate));
        e.move(0,s8(2*rate));collide();
        if(measureWork&&collisionCallbackWorkCycles>=0)complexBodyWorkCycles=body+cameraWorkCycles
            +animationWorkCycles-animationBefore+collisionScanWorkCycles+collisionCallbackWorkCycles;
        if(--e.params[0])break;
        if(measureWork&&complexBodyWorkCycles>=0)complexBodyWorkCycles+=-12+104+AirProbeWork;
        e.params[2]=0;sampleProbes(tilt);
        if((probes[0]|probes[1]|probes[2])&64){
            e.handler=AirHandler::Animation;
            // 01:6307 calls the conditional starter. A map-delayed crash can
            // still be active at this deadline, so its recovery is rejected.
            // Deliberate native fix: remember that request, finish the crash
            // normally, then start the unchanged recovery script exactly once.
            // This is not evidence of the original cartridge's timing.
            if(measureWork&&complexBodyWorkCycles>=0)complexBodyWorkCycles+=4+124+airStartAnimationWork(e.animDone);
            crashRecoveryPending=!e.animDone;startAnimation(i,1);break;
        }
        if(!((probes[0]|probes[1]|probes[2]|probes[3]|probes[4]|probes[5])&1)){
            if(measureWork&&complexBodyWorkCycles>=0)complexBodyWorkCycles+=52+68+44;
            e.handler=AirHandler::Play;break;
        }
        complexBodyWorkCycles=-1; // Exploding fallthrough still needs a complete source model.
        e.handler=AirHandler::Exploding;e.params[0]=64;setFrame(i,6);[[fallthrough]];
    }
    case AirHandler::Exploding:
        if(--e.params[0]){if(!(e.params[0]&7)){int dx=(randomByte()&15)*16,dy=(randomByte()&31)*16;spawn(33,e.x+dx,e.y+dy);}if(!(e.params[0]&15))pendingSound=14;break;}
        [[fallthrough]];
    case AirHandler::Hide:e.flags|=8;e.handler=AirHandler::Return;setFrame(i,0);break;
    case AirHandler::Return:{
        followCamera();int dx=s16(e.x-returnX),dy=s16(e.y-returnY);
        e.move(dx>0?-16:dx<0?16:0,dy>0?-16:dy<0?16:0);
        if(!dx&&!dy){tilt=0;speed=8;e.flags&=~8;e.handler=AirHandler::Play;}break;}
    case AirHandler::BeginFinish:beginFinish(resultFlags);break;
    case AirHandler::FinishDelay:if(--finishTimer==0)result=resultFlags;break;
    case AirHandler::Breakable:animate(i);if(e.params[2]){e.move(s8(e.params[0]),s8(e.params[1]));++e.params[1];}break;
    case AirHandler::Pickup:animate(i);startAnimation(i,3);break;
    case AirHandler::Countdown:animate(i);e.x=(cameraX+256)&65535;e.y=(cameraY+256)&65535;startAnimation(i,4);break;
    case AirHandler::Booster:e.handler=AirHandler::Animation;startAnimation(i,5);break;
    case AirHandler::Bouncer:animate(i);startAnimation(i,6);if((e.y>>8)>(((cameraY>>8)+8)&255))e.alive=false;break;
    case AirHandler::Emitter:animate(i);startAnimation(i,7);break;
    case AirHandler::Particle:if(--e.params[0]==0){e.alive=false;break;}e.move(0,-16);animate(i);startAnimation(i,8);break;
    case AirHandler::FallingPickup:e.move(0,4);if((e.y>>8)>(((cameraY>>8)+8)&255))e.alive=false;break;
    case AirHandler::Enemy:
        animate(i);startAnimation(i,9);e.collision=14;e.move(s8(e.params[0]),0);
        if(terrainAt(e.x+96,e.y)&0x63){e.params[0]=static_cast<uint8_t>(-s8(e.params[0]));e.flags^=32;}break;
    case AirHandler::DebrisLeft:case AirHandler::DebrisRight:
        e.move(e.handler==AirHandler::DebrisLeft?-16:16,-32);if(--e.params[0]==0)e.alive=false;
        if(!(ticks&7))e.flags^=64;break;
    case AirHandler::ExplosionSlow:animate(i);startAnimation(i,11);break;
    case AirHandler::ExplosionFast:animate(i);startAnimation(i,12);break;
    case AirHandler::Idle:break;
    }
}
void AirGame::updateVisibility(bool deferSpriteClear){
    SpriteLayer next(!reverseSprites);
    if(deferSpriteClear)next.slots=sprites.slots;
    reverseSprites=!reverseSprites;sprites=std::move(next);
    for(auto& e:entities)if(e.alive){
        e.offscreen=false;if(e.flags&8)continue;
        const auto& m=assets.frames[e.frame].meta;
        int x=relativePixel(e.x,cameraX)+s8(m[0]),y=relativePixel(e.y,cameraY)+s8(m[1]);
        if(x < -2*m[6]-16||x>176||y < -2*m[7]-16||y>152){
            if(e.flags&16){if((e.flags&4)&&e.placement>=0)placements[e.placement].active=false;e.alive=false;}
            else e.offscreen=true;
        }else {sprites.add(assets.frames[e.frame],relativePixel(e.x,cameraX),relativePixel(e.y,cameraY),e.flags,e.frame<12?&spriteResources:nullptr);if(sprites.exhausted())return;}
    }
}
void AirGame::step(int buttons){
    pendingSound=-1;
    if(!started||result)return;
    // 03cb completes the display callback before 03d5 enters the pause loop.
    // 14f1 resumes the interrupted update without another display callback.
    if(!videoTickPrepared){beginVideoTick();tickHud();videoTickPrepared=true;}
    if(paused)return;
    videoTickPrepared=false;
    ticks=(ticks+1)&65535;
    updateGame(buttons);
}
void AirGame::displayTick(bool resourceReady){
    if(!started)return;
    beginVideoTick(resourceReady);tickHud();ticks=(ticks+1)&65535;
}
void AirGame::updateGame(int buttons,bool deferSpriteClear){
    if(!started||result||paused)return;
    held=buttons;pressed=buttons&~previous;previous=buttons;
    animationWorkCycles=0;animationWorkComplete=true;
    collisionScanWorkCycles=collisionCallbackWorkCycles=0;
    playerMotionWorkCycles=playerInputWorkCycles=0;
    if(measureWork){handlerWorkCycles.fill(-2);handlerWorkKinds.fill(-1);}
    entityWorkCycles=-1;
    int oldFrame=entities[0].frame,oldFlags=entities[0].flags;
    for(int j=0;j<16;++j)if(entities[j].alive){
        if(measureWork){
            const auto before=entities[j];int animationBefore=animationWorkCycles,faultsBefore=animationFaults;
            starterWorkCycles=cameraWorkCycles=0;complexBodyWorkCycles=-1;update(j);
            handlerWorkKinds[j]=static_cast<int>(before.handler);
            handlerWorkCycles[j]=animationFaults==faultsBefore?
                airSimpleHandlerWork(*this,before,entities[j],animationWorkCycles-animationBefore,starterWorkCycles,cameraWorkCycles):-1;
            if(handlerWorkCycles[j]==-1&&animationFaults==faultsBefore)handlerWorkCycles[j]=complexBodyWorkCycles;
        }else update(j);
    }
    if(measureWork){
        entityWorkCycles=1612;
        for(int work:handlerWorkCycles){
            if(work==-1){entityWorkCycles=-1;break;}
            if(work>=0)entityWorkCycles+=60+work;
        }
    }
    if(measureWork)resourceWorkCycles=airResourceWork(*this,oldFrame);
    finishVideoTick(oldFrame,oldFlags);
    if(measureWork){const auto spriteWork=airSpriteWork(*this,deferSpriteClear?&spriteEntityWorkCycles:nullptr);
        spriteWorkCycles=spriteWork.prepare;clearWorkCycles=spriteWork.clear;}
    if(deferSpriteClear)spriteInputEntities=entities;
    updateVisibility(deferSpriteClear);
    mapTransfer=((lastMapCamera^cameraY)&128)!=0;
    // 03ed..19a2: indirect callback + 1ead's sixteen-cell row preparation.
    // The downward branch at 1ef2 costs four more T-cycles. No ROM execution
    // or measured frame indices are involved in this source-work calculation.
    mapWorkCycles=mapTransfer?2228+((static_cast<uint16_t>(lastMapCamera-cameraY)&0x8000)?4:0):304;
    lastMapCamera=cameraY;
    // 19a2: entry + eight wrappers (final JR not taken) + RET. Every placement
    // adds the 19b5 call/pointer advance, its range/allocation path and wrap.
    placementWorkCycles=placements.empty()?0:608;
    for(int n=0;n<8&&!placements.empty();++n){
        auto& p=placements[scan];int low=cameraY>>8,high=(low+14)&255,row=((p.y>>8)+3)&255;
        placementWorkCycles+=156;
        if(low>=row)placementWorkCycles+=144; // 19f2 return.
        else if(high<row)placementWorkCycles+=168; // 19f6 return.
        else if(p.active)placementWorkCycles+=188; // 19f9 return.
        else{
            int slot=spawn(p.kind,p.x,p.y,scan);
            // 1abc allocation: 52 per occupied slot; successful fixed copy
            // 816, failed full-table scan 868. Includes caller bookkeeping.
            placementWorkCycles+=slot>=0?1148+52*slot:1140;
            if(slot>=0)p.active=true;
        }
        if(scan+1==static_cast<int>(placements.size()))placementWorkCycles+=84;
        scan=(scan+1)%static_cast<int>(placements.size());
    }
}
void AirGame::refreshHud(){
    hudValues[0]=0xf7+playerNumber;int score=money%10000;
    hudValues[1]=0xf6+score/1000;hudValues[2]=0xf6+score/100%10;hudValues[3]=0xf6+score/10%10;hudValues[4]=0xf6+score%10;
    hudValues[5]=0xf6+seconds/10;hudValues[6]=0xf6+seconds%10;
    int bar=(entities[0].params[1]*48/assets.levels[difficulty].quota)&255;
    int j=7;
    if(bar){
        while(j<13&&bar>=8){hudValues[j++]=0xe9;bar-=8;}
        if(j<13)hudValues[j++]=0xe9+(bar^7); // 317d tests zero only before the first segment.
    }
    while(j<13)hudValues[j++]=0;
}
void AirGame::tickHud(){hudMap[assets.hudColumns[hudCursor]]=hudValues[hudCursor];hudCursor=(hudCursor+1)%13;if(!hudCursor)refreshHud();}

void AirGame::text(int x,int y,const std::string& value){
    for(char c:value){int n=c==' '?0:c>='0'&&c<='9'?c-'0'+1:c>='A'&&c<='Z'?c-'A'+11:c=='-'?39:0;
        for(int py=0;py<8;++py)for(int px=0;px<8;++px)if(x+px>=0&&x+px<Width&&y+py>=0&&y+py<Height)screen[(y+py)*Width+x+px]=shared.font[n*64+py*8+px];x+=8;}
}
void AirGame::render(bool developmentOverlay){
    const auto& l=assets.levels[difficulty];int cx=started?visibleCameraX:l.cameraX,cy=started?visibleCameraY:l.cameraY;
    for(int y=0;y<PlayHeight;++y)for(int x=0;x<Width;++x){int wx=(cx>>4)+x,wy=(cy>>4)+y;
        int tile=tileAt(wx*16,wy*16);screen[y*Width+x]=assets.tiles[tile*64+(wy&7)*8+(wx&7)];}
    if(started){
        visibleSprites.draw(screen);
        for(int col=0;col<20;++col)for(int y=0;y<8;++y)for(int x=0;x<8;++x)screen[(PlayHeight+y)*Width+col*8+x]=assets.hudTiles[hudMap[col]*64+y*8+x];
    }else{
        for(int y=64;y<144;++y)std::fill_n(screen.begin()+y*Width,Width,0);
        text(8,72,"NATIVE PORT - WIP");text(32,88,"AIR BUMPER");text(16,104,"ENTER TO START");text(16,120,"1-4 DIFFICULTY");
    }
    if(developmentOverlay&&(paused||result)){
        for(int y=48;y<104;++y)std::fill_n(screen.begin()+y*Width+8,144,0);
        text(40,56,paused?"PAUSED":"STUNT END");
        if(result)text(16,72,(result&2)?"TARGET REACHED":"TRY AGAIN");
        text(16,88,paused?"ESC TO RESUME":"R TO RESTART");
    }
}
}
