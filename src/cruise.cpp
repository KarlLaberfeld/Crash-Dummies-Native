#include "cruise.h"
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
// Quantize positions separately, as 00:1c22 / 00:1747 do before subtracting.
int relativePixel(int position,int camera){return s16((position&0xfff0)-(camera&0xfff0))/16;}
struct CruiseReader {
    std::vector<uint8_t> data;size_t pos=0;
    explicit CruiseReader(const std::wstring& path){
        FILE* f=_wfopen(path.c_str(),L"rb");
        if(!f)throw std::runtime_error("cruise.dat is missing. Run build.ps1 with the original ROM.");
        fseek(f,0,SEEK_END);long size=ftell(f);rewind(f);
        if(size<8||size>2*1024*1024){fclose(f);throw std::runtime_error("Invalid Cruise Missile data size.");}
        data.resize(size);size_t n=fread(data.data(),1,data.size(),f);fclose(f);
        if(n!=data.size())throw std::runtime_error("Could not read Cruise Missile data.");
    }
    void raw(void* out,size_t n){if(n>data.size()-pos)throw std::runtime_error("Truncated Cruise Missile data.");memcpy(out,data.data()+pos,n);pos+=n;}
    int byte(){uint8_t v;raw(&v,1);return v;}
    int word(){int lo=byte();return lo+(byte()<<8);}
};
void check(bool ok){if(!ok)throw std::runtime_error("Invalid Cruise Missile asset record. Rebuild the local data.");}
}

void CruiseGame::setFrame(int i,int frame,int flags){
    auto& e=entities[i];e.frame=frame;e.flags=(e.flags&31)|flags;e.animDone=true;e.frameWaiting=false;
}

void CruiseGame::startAnimation(int i,int sequence,bool force){
    auto& e=entities[i];if(!force&&!e.animDone)return;
    e.anim=assets.animationStarts.at(sequence);e.animDone=false;
}

void CruiseGame::animate(int i){
    auto& e=entities[i];if(e.animDone||!e.alive)return;
    if(e.delay){--e.delay;return;}
    // 3c41 commits the script cursor only at a delay/loop yield;
    // 3c92 leaves the saved block unchanged during a dynamic-frame wait.
    int cursor=e.anim;
    for(int guard=0;guard<256;++guard){
        if(cursor<=0||cursor>=static_cast<int>(assets.commands.size()))break;
        auto c=assets.commands[cursor];cursor=c.next;
        switch(c.op){
        case 0:e.animDone=true;return;
        case 1:e.anim=cursor;e.delay=e.period;return;
        case 2:e.move(c.a,0);break;
        case 3:e.move(0,c.a);break;
        case 4:
            if(c.a<12){
                if(e.frameWaiting){
                    if(transferState!=2)return;
                    e.frameWaiting=false;break;
                }
                if(e.frame!=c.a){e.frame=c.a;e.frameWaiting=true;return;}
            }
            e.frame=c.a;break;
        case 5:e.period=c.a;break;
        case 6:e.flags^=32;break;
        case 7:e.flags&=~32;break;
        case 8:e.loop=c.a;e.loopStart=cursor;break;
        case 9:e.loop=(e.loop-1)&255;if(e.loop)cursor=e.loopStart;e.anim=cursor;e.delay=e.period;return;
        case 10:cursor=c.a;break;
        case 11:e.handler=static_cast<CruiseHandler>(c.a);e.animDone=true;return;
        case 12:e.move(c.a*16,0);break;
        case 13:e.move(0,c.a*16);break;
        case 14:e.alive=false;e.animDone=true;return;
        case 15:e.flags^=8;break;
        case 16:spawn(c.c,e.x+c.a,e.y+c.b);break;
        case 17:e.flags|=32;break;
        case 18:break; // Original stage activation event; unused by Cruise graphs.
        case 19:pendingSound=c.a;break;
        default:++animationFaults;e.animDone=true;return;
        }
    }
    ++animationFaults;e.animDone=true;
}

void CruiseGame::beginVideoTick(){
    // 00:1325 / 00:1897: a map column has priority; otherwise copy four
    // 32-byte resource chunks. This models the original asset queue, not a CPU.
    if(transferRemaining&&!mapTransfer){
        transferRemaining=std::max(0,transferRemaining-4);
        if(!transferRemaining){entities[0].frame=transferFrame;entities[0].flags=transferFlags;transferState=2;}
    }
}

void CruiseGame::finishVideoTick(int oldFrame,int oldFlags){
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

void CruiseGame::updateVisibility(){
    reverseSprites=!reverseSprites;sprites=SpriteLayer(reverseSprites);
    for(auto& e:entities)if(e.alive){
        e.offscreen=false;if(e.flags&8)continue;
        const auto& m=assets.frames[e.frame].meta;
        int x=relativePixel(e.x,cameraX)+s8(m[0]),y=relativePixel(e.y,cameraY)+s8(m[1]);
        if(x < -2*m[6]-16||x>176||y < -2*m[7]-16||y>152){
            if(e.flags&16){if((e.flags&4)&&e.placement>=0)placements[e.placement].active=false;e.alive=false;}
            else e.offscreen=true;
        }else {sprites.add(assets.frames[e.frame],relativePixel(e.x,cameraX),relativePixel(e.y,cameraY),e.flags);if(sprites.exhausted())return;}
    }
}

void CruiseGame::text(int x,int y,const std::string& value){
    for(char c:value){int n=c==' '?0:c>='0'&&c<='9'?c-'0'+1:c>='A'&&c<='Z'?c-'A'+11:c=='-'?39:0;
        for(int py=0;py<8;++py)for(int px=0;px<8;++px)if(x+px>=0&&x+px<Width&&y+py>=0&&y+py<Height)screen[(y+py)*Width+x+px]=shared.font[n*64+py*8+px];x+=8;}
}


CruiseAssets CruiseAssets::load(const std::wstring& path){
    CruiseReader r(path);char magic[8];r.raw(magic,8);check(!memcmp(magic,"TICDCRU2",8));
    CruiseAssets a;r.raw(a.tiles.data(),a.tiles.size());r.raw(a.cells.data(),2048);r.raw(a.quadrants.data(),192);r.raw(a.collision.data(),128);
    for(auto& f:a.frames){r.raw(f.meta.data(),8);r.raw(f.pixels.data(),f.pixels.size());readSpritePieces(r,f);}
    for(auto& l:a.levels){l.initial=r.byte();l.seconds=r.byte();int count=r.word();check(count<=512&&l.seconds<=99);
        for(int j=0;j<count;++j){Placement p;p.kind=r.byte();p.x=r.word();p.y=r.word();check(p.kind>=58&&p.kind<=65);l.objects.push_back(p);}}
    for(int j=0;j<11;++j){int k=r.byte();check(k==49||k==50||(k>=57&&k<=65));auto& d=a.definitions[k];
        d.frame=r.byte();d.flags=r.byte();int h=r.byte();d.handler=static_cast<CruiseHandler>(h);d.collision=r.byte();r.raw(d.params.data(),7);check(d.frame<42&&h<=20);}
    int roots=r.word(),count=r.word();check(roots==10&&count>0&&count<=4096);
    for(int j=0;j<roots;++j){int root=r.word();check(root>0&&root<=count);a.animationStarts.push_back(root);}
    a.commands.push_back({});for(int j=0;j<count;++j){Command c;c.op=r.byte();c.a=s16(r.word());c.b=s16(r.word());c.c=s16(r.word());c.next=r.word();
        check(c.op<=19&&c.next<=count);if(c.op==10)check(c.a>0&&c.a<=count);if(c.op==4)check(c.a>=0&&c.a<42);
        if(c.op==11)check(c.a>=0&&c.a<=20);a.commands.push_back(c);}
    r.raw(a.transferChunks.data(),12);for(auto& h:a.headings){h[0]=r.byte();h[1]=r.byte();h[2]=s8(r.byte());h[3]=s8(r.byte());check(h[0]<5);}
    for(auto& probe:a.probes)for(auto& v:probe)v=s16(r.word());for(auto& v:a.wave)v=s8(r.byte());
    r.raw(a.hudTiles.data(),a.hudTiles.size());r.raw(a.hudMap.data(),20);r.raw(a.hudColumns.data(),7);
    for(int v:a.tiles)check(v<4);for(int v:a.hudTiles)check(v<4);for(int v:a.cells)check(v<48);for(int v:a.quadrants)check(v<82);
    for(int v:a.hudColumns)check(v<20);for(const auto& f:a.frames)for(int v:f.pixels)check(v<4||v==255);check(r.pos==r.data.size());return a;
}
int CruiseGame::spawn(int kind,int x,int y,int placement){
    if(kind!=49&&kind!=50&&(kind<57||kind>65))return -1;
    for(int j=0;j<16;++j)if(!entities[j].alive){const auto& d=assets.definitions[kind];CruiseEntity e;e.alive=true;e.kind=kind;e.frame=d.frame;
        e.flags=d.flags;e.collision=d.collision;e.handler=d.handler;e.params=d.params;e.x=x&65535;e.y=y&65535;e.placement=placement;entities[j]=e;return j;}
    return -1;
}
void CruiseGame::start(int level,int player){
    playerNumber=player&1;pendingSound=-1;sprites=SpriteLayer(false);reverseSprites=false;
    difficulty=std::clamp(level,0,3);entities={};placements=assets.levels[difficulty].objects;rewarded.assign(placements.size(),false);
    seconds=assets.levels[difficulty].seconds;cameraX=0;cameraY=1920;
    ticks=secondTicks=money=introTimer=balls=randomState=extraLives=scan=hudCursor=result=resultFlags=held=pressed=previous=animationFaults=0;
    transferState=transferRemaining=transferFrame=transferFlags=0;lastMapCamera=128;mapTransfer=true;finishTimer=64;started=true;paused=false;
    spawn(57,1040,3424);hudMap=assets.hudMap;refreshHud();for(int j=0;j<7;++j)hudMap[assets.hudColumns[j]]=hudValues[j];
}
int CruiseGame::tileAt(int x,int y)const{
    x&=65535;y&=65535;
    // The declared map is 128 columns by 16 rows. Reads outside its RAM
    // allocation are not reconstructed; safe blank pixels are a known limit.
    if(x>=32768||y>=4096)return 0;
    int cell=assets.cells[(x>>8)*16+(y>>8)],quadrant=((x>>7)&1)|((y>>6)&2);
    return assets.quadrants[quadrant*48+cell];
}
int CruiseGame::terrainAt(int x,int y)const{if((x&65535)>=32768||(y&65535)>=4096)return 0;return assets.collision[tileAt(x,y)];}
void CruiseGame::followCamera(){
    const auto& p=entities[0];cameraX=std::clamp(cameraX+s8(((p.x-cameraX)&4095)/16-64),0,30208);
    cameraY=std::clamp(cameraY+s8(((p.y-cameraY)&4095)/16-48),0,1920);
}
int CruiseGame::randomByte(){
    int swapped=((randomState&255)<<8)|(randomState>>8),first=(randomState-swapped)&65535;
    int value=(first-swapped-(randomState<swapped)+254)&65535,lo=value&255,hi=value>>8,out=(lo-hi-(lo>=hi))&255;
    randomState=(randomState&255)|(out<<8);return out;
}
void CruiseGame::introBob(){if(!(introTimer&3))entities[0].move(0,(introTimer&4)?-16:16);}
void CruiseGame::ignition(){
    introBob();if(introTimer>=128&&!(introTimer&7)){int dx=randomByte()+32;spawn(49,entities[0].x+dx,entities[0].y+192);}
    introTimer=(introTimer+1)&255;if(introTimer==192){entities[0].handler=CruiseHandler::Fly;pendingSound=8;}
}
void CruiseGame::thrustSmoke(){if(!(ticks&15))spawn(49,entities[0].x+192,entities[0].y+128);}
void CruiseGame::movePlayer(){
    auto& p=entities[0];const auto& h=assets.headings[p.params[0]];
    if(!(ticks&3)){
        if(held&A){
            auto accelerate=[](uint8_t& byte,int amount){int v=s8(byte);if(v>=0){if(amount>=0&&v>=16)return;}else if(amount<0&&v< -16)return;byte=static_cast<uint8_t>(v+amount);};
            accelerate(p.params[1],h[2]);accelerate(p.params[2],h[3]);
            if(!h[3])p.params[2]=static_cast<uint8_t>(approach(s8(p.params[2]),8));thrustSmoke();
        }else p.params[2]=static_cast<uint8_t>(approach(s8(p.params[2]),8));
    }
    p.move(s8(p.params[1]),s8(p.params[2]));
}
void CruiseGame::crashFrame(){setFrame(0,5);if(((entities[0].params[0]+4)&15)<8)entities[0].flags|=32;}
void CruiseGame::reward(int other,int points){int placement=entities[other].placement;
    if(placement>=0&&!rewarded[placement]){rewarded[placement]=true;money+=points;}}
void CruiseGame::collideWith(int other){
    auto& p=entities[0];auto& o=entities[other];if(!o.alive||o.collision==255)return;
    switch(o.collision){
    case 21:case 28:case 35:case 37:p.handler=CruiseHandler::Crash;break;
    case 25:break; // Magnet applies attraction in its own update.
    case 30:
        if(p.params[0]!=12){crashFrame();beginFinish(0x23);pendingSound=14;}else{resultFlags=0x27;p.handler=CruiseHandler::Success;update(0);}break;
    case 34:++extraLives;o.alive=false;pendingSound=9;break;
    case 38:reward(other,50);o.collision=37;o.frame=20;o.handler=CruiseHandler::Animation;startAnimation(other,7,true);break;
    default:break;
    }
}
void CruiseGame::collide(){
    auto box=[&](const CruiseEntity& e){return spriteBounds(assets.frames[e.frame],e.x,e.y,cameraX,cameraY);};
    auto a=box(entities[0]);for(int j=1;j<16;++j){const auto& e=entities[j];if(!e.alive||e.offscreen||e.collision==255)continue;auto b=box(e);
        if(spriteOverlap(a,b))collideWith(j);}
}
void CruiseGame::tickTimer(){if(++secondTicks==60){secondTicks=0;if(seconds)--seconds;}}
void CruiseGame::beginFinish(int flags){resultFlags=flags;entities[0].handler=CruiseHandler::FinishDelay;if(--finishTimer==0)result=flags;}
void CruiseGame::update(int i){
    auto& e=entities[i];
    switch(e.handler){
    case CruiseHandler::Intro:if(++introTimer==32){e.handler=CruiseHandler::Ignition;ignition();}break;
    case CruiseHandler::Ignition:ignition();break;
    case CruiseHandler::Fly:{
        followCamera();const auto& h=assets.headings[e.params[0]];setFrame(i,h[0],h[1]);movePlayer();
        if(!(ticks&3)){if(held&Left)e.params[0]=(e.params[0]-1)&15;if(held&Right)e.params[0]=(e.params[0]+1)&15;}
        tickTimer();if(!seconds){resultFlags=0x11;if(--finishTimer==0)result=resultFlags;break;}
        collide();int bits=0;for(const auto& probe:assets.probes)bits|=terrainAt(e.x+probe[0],e.y+probe[1]);
        if(bits&3){crashFrame();beginFinish(0x21);pendingSound=14;}break;}
    case CruiseHandler::Smoke:animate(i);startAnimation(i,0);break;
    case CruiseHandler::Ball:{
        if(e.offscreen){--balls;e.alive=false;}
        e.move(s8(e.params[0]),0);int vy=s8(e.params[1]),next=(e.params[1]+e.params[2])&255;
        if(vy>=0&&next>=128)next=127;e.params[1]=static_cast<uint8_t>(next);e.move(0,s8(next));
        if(next>=128)break;if(!(terrainAt(e.x,e.y)&3))break;
        if(next<16){--balls;e.alive=false;}else e.params[1]=static_cast<uint8_t>(-(next-16));break;}
    case CruiseHandler::RocketUp:animate(i);startAnimation(i,1);break;
    case CruiseHandler::RocketDown:animate(i);startAnimation(i,4);break;
    case CruiseHandler::RocketWait:
        if(!e.offscreen&&(e.x>>8)==(((entities[0].x>>8)+1)&255)){
            e.handler=CruiseHandler::RocketFlight;e.collision=21;money+=25;pendingSound=12;update(i);}break;
    case CruiseHandler::RocketFlight:
        if(!(ticks&7))spawn(49,e.x+64,e.y);e.move(0,s8(e.params[0]));break;
    case CruiseHandler::Magnet:{
        animate(i);startAnimation(i,2);const auto& p=entities[0];int x=(p.x>>8)+2,y=(p.y>>8)+2;
        if((x&255)<(e.x>>8)||((x-4)&255)>=(e.x>>8)||(y&255)<(e.y>>8)||((y-4)&255)>=(e.y>>8)||(ticks&1))break;
        auto& player=entities[0];player.params[1]+=s16(player.x-(e.x+128))>=0?-1:1;
        player.params[2]+=s16(player.y-(e.y-128))>=0?-1:1;reward(i,75);break;}
    case CruiseHandler::Target:animate(i);startAnimation(i,3);break;
    case CruiseHandler::Wave:
        if(!(ticks&3)){e.params[0]=(e.params[0]+1)&63;e.move(0,assets.wave[e.params[0]>>2]);}break;
    case CruiseHandler::Spring:e.collision=38;animate(i);startAnimation(i,5);break;
    case CruiseHandler::Emitter:
        if(e.offscreen)break;animate(i);
        // 01:76c0 returns when the stored difficulty byte equals one.
        if(difficulty!=1&&balls!=3&&randomByte()<31){int slot=spawn(50,e.x+192,e.y);
            if(slot>=0){entities[slot].params[0]=static_cast<uint8_t>((randomByte()&31)-16);entities[slot].params[1]=static_cast<uint8_t>(-((randomByte()&31)+32));++balls;}}
        startAnimation(i,6);break;
    case CruiseHandler::Crash:animate(i);startAnimation(i,8);break;
    case CruiseHandler::Failure:beginFinish(0x21);break;
    case CruiseHandler::Success:animate(i);startAnimation(i,9);break;
    case CruiseHandler::BeginFinish:beginFinish(resultFlags);break;
    case CruiseHandler::FinishDelay:if(--finishTimer==0)result=resultFlags;break;
    case CruiseHandler::Animation:animate(i);break;
    case CruiseHandler::Idle:break;
    }
}
void CruiseGame::step(int buttons){
    pendingSound=-1;
    if(!started||paused||result)return;held=buttons;pressed=buttons&~previous;previous=buttons;ticks=(ticks+1)&65535;
    beginVideoTick();tickHud();int oldFrame=entities[0].frame,oldFlags=entities[0].flags;
    for(int j=0;j<16;++j)if(entities[j].alive)update(j);
    finishVideoTick(oldFrame,oldFlags);updateVisibility();mapTransfer=((lastMapCamera^cameraX)&128)!=0;lastMapCamera=cameraX;
    for(int n=0;n<8&&!placements.empty();++n){auto& p=placements[scan];int low=cameraX>>8,high=(low+12)&255,column=((p.x>>8)+2)&255;
        if(!p.active&&low<column&&high>=column){int slot=spawn(p.kind,p.x,p.y,scan);if(slot>=0)p.active=true;}scan=(scan+1)%static_cast<int>(placements.size());}
}
void CruiseGame::refreshHud(){hudValues[0]=0xf7+playerNumber;int score=money%10000;
    hudValues[1]=0xf6+score/1000;hudValues[2]=0xf6+score/100%10;hudValues[3]=0xf6+score/10%10;hudValues[4]=0xf6+score%10;
    hudValues[5]=0xf6+seconds/10;hudValues[6]=0xf6+seconds%10;}
void CruiseGame::tickHud(){hudMap[assets.hudColumns[hudCursor]]=hudValues[hudCursor];hudCursor=(hudCursor+1)%7;if(!hudCursor)refreshHud();}
void CruiseGame::render(bool developmentOverlay){
    int cx=started?cameraX:0,cy=started?cameraY:1920;
    for(int y=0;y<PlayHeight;++y)for(int x=0;x<Width;++x){int wx=(cx>>4)+x,wy=(cy>>4)+y;int tile=tileAt(wx*16,wy*16);screen[y*Width+x]=assets.tiles[tile*64+(wy&7)*8+(wx&7)];}
    if(started){sprites.draw(screen);
        for(int col=0;col<20;++col)for(int y=0;y<8;++y)for(int x=0;x<8;++x)screen[(PlayHeight+y)*Width+col*8+x]=assets.hudTiles[hudMap[col]*64+y*8+x];
    }else{for(int y=64;y<144;++y)std::fill_n(screen.begin()+y*Width,Width,0);text(8,72,"NATIVE PORT - WIP");text(24,88,"CRUISE MISSILE");text(16,104,"ENTER TO START");text(16,120,"1-4 DIFFICULTY");}
    if(developmentOverlay&&(paused||result)){for(int y=48;y<104;++y)std::fill_n(screen.begin()+y*Width+8,144,0);text(40,56,paused?"PAUSED":"STUNT END");if(result)text(16,72,(result&2)?"TARGET REACHED":"TRY AGAIN");text(16,88,paused?"ESC TO RESUME":"R TO RESTART");}
}
}
