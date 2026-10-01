#include "ski.h"
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
struct SkiReader {
    std::vector<uint8_t> data;size_t pos=0;
    explicit SkiReader(const std::wstring& path){
        FILE* f=_wfopen(path.c_str(),L"rb");
        if(!f)throw std::runtime_error("ski.dat is missing. Run build.ps1 with the original ROM.");
        fseek(f,0,SEEK_END);long size=ftell(f);rewind(f);
        if(size<8||size>2*1024*1024){fclose(f);throw std::runtime_error("Invalid Ski Slope data size.");}
        data.resize(size);size_t n=fread(data.data(),1,data.size(),f);fclose(f);
        if(n!=data.size())throw std::runtime_error("Could not read Ski Slope data.");
    }
    void raw(void* out,size_t n){if(n>data.size()-pos)throw std::runtime_error("Truncated Ski Slope data.");memcpy(out,data.data()+pos,n);pos+=n;}
    int byte(){uint8_t v;raw(&v,1);return v;}
    int word(){int lo=byte();return lo+(byte()<<8);}
};
void check(bool ok){if(!ok)throw std::runtime_error("Invalid Ski Slope asset record. Rebuild the local data.");}
}

int SkiGame::spawn(int kind,int x,int y,int placement){
    if(kind<35||kind>44)return -1;
    for(int j=0;j<16;++j)if(!entities[j].alive){
        const auto& d=assets.definitions[kind-35];SkiEntity e;
        e.alive=true;e.kind=kind;e.frame=d.frame;e.flags=d.flags;e.collision=d.collision;
        e.handler=d.handler;e.params=d.params;e.x=x&65535;e.y=y&65535;e.placement=placement;
        entities[j]=e;return j;
    }
    return -1;
}

void SkiGame::setFrame(int i,int frame,int flags){
    auto& e=entities[i];e.frame=frame;e.flags=(e.flags&31)|flags;e.animDone=true;e.frameWaiting=false;
}

void SkiGame::startAnimation(int i,int sequence,bool force){
    auto& e=entities[i];if(!force&&!e.animDone)return;
    e.anim=assets.animationStarts.at(sequence);e.animDone=false;
}

void SkiGame::animate(int i){
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
            if(c.a<13){
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
        case 11:e.handler=static_cast<SkiHandler>(c.a);e.animDone=true;return;
        case 12:e.move(c.a*16,0);break;
        case 13:e.move(0,c.a*16);break;
        case 14:e.alive=false;e.animDone=true;return;
        case 15:e.flags^=8;break;
        case 16:spawn(c.c,e.x+c.a,e.y+c.b);break;
        case 17:e.flags|=32;break;
        case 18:break; // Original stage activation event; unused by Ski graphs.
        case 19:pendingSound=c.a;break;
        default:++animationFaults;e.animDone=true;return;
        }
    }
    ++animationFaults;e.animDone=true;
}

int SkiGame::tileAt(int x,int y) const {
    x&=65535;y&=65535;
    int cell=assets.levels[difficulty].cells[(y>>8)*16+((x>>8)&15)];
    int quadrant=((x>>7)&1)|((y>>6)&2);
    return assets.quadrants[quadrant*64+cell];
}

int SkiGame::terrainAt(int x,int y) const{return assets.collision[tileAt(x,y)];}

void SkiGame::beginVideoTick(){
    // 00:0ebc / 00:1897: a map row has priority; otherwise copy at most four
    // 32-byte resource chunks. This models the original asset queue, not a CPU.
    if(transferRemaining&&!mapTransfer){
        transferRemaining=std::max(0,transferRemaining-4);
        if(!transferRemaining){entities[0].frame=transferFrame;entities[0].flags=transferFlags;transferState=2;}
    }
}

void SkiGame::finishVideoTick(int oldFrame,int oldFlags){
    // 00:3f30 runs after game handlers and before visibility / map preparation.
    if(transferState==2)transferState=0;
    auto& p=entities[0];
    if(p.frame<13&&p.frame!=oldFrame){
        if(!transferState){transferState=1;transferFrame=-1;}
        if(p.frame!=transferFrame){
            transferRemaining=assets.transferChunks[p.frame];
            if(!transferRemaining)return;
            transferFrame=p.frame;transferFlags=p.flags;
        }
        p.frame=oldFrame;p.flags=oldFlags;
    }
}

void SkiGame::updateVisibility(){
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

void SkiGame::text(int x,int y,const std::string& value){
    for(char c:value){int n=c==' '?0:c>='0'&&c<='9'?c-'0'+1:c>='A'&&c<='Z'?c-'A'+11:c=='-'?39:0;
        for(int py=0;py<8;++py)for(int px=0;px<8;++px)if(x+px>=0&&x+px<Width&&y+py>=0&&y+py<Height)screen[(y+py)*Width+x+px]=shared.font[n*64+py*8+px];x+=8;}
}

SkiAssets SkiAssets::load(const std::wstring& path){
    SkiReader r(path);char magic[8];r.raw(magic,8);check(!memcmp(magic,"TICDSKI2",8));
    SkiAssets a;r.raw(a.tiles.data(),a.tiles.size());r.raw(a.quadrants.data(),256);r.raw(a.collision.data(),128);
    for(auto& f:a.frames){r.raw(f.meta.data(),8);r.raw(f.pixels.data(),f.pixels.size());readSpritePieces(r,f);}
    for(auto& l:a.levels){
        l.cameraX=r.word();l.seconds=r.byte();l.quota=r.byte();l.rows=r.word();int count=r.word();
        check(l.rows>=9&&l.rows<=256&&l.seconds<=99&&count<=512);r.raw(l.cells.data(),4096);
        for(int j=0;j<count;++j){Placement p;p.kind=r.byte();p.x=r.word();p.y=r.word();check(p.kind>=36&&p.kind<=40);l.objects.push_back(p);}
        for(int v:l.cells)check(v<64);
    }
    for(auto& d:a.definitions){d.frame=r.byte();d.flags=r.byte();int h=r.byte();d.handler=static_cast<SkiHandler>(h);d.collision=r.byte();r.raw(d.params.data(),7);check(d.frame<39&&h<=12);}
    int roots=r.word(),count=r.word();check(roots==11&&count>0&&count<=4096);
    for(int j=0;j<roots;++j){int root=r.word();check(root>0&&root<=count);a.animationStarts.push_back(root);}
    a.commands.push_back({});
    for(int j=0;j<count;++j){Command c;c.op=r.byte();c.a=s16(r.word());c.b=s16(r.word());c.c=s16(r.word());c.next=r.word();
        check(c.op<=19&&c.next<=count);if(c.op==10)check(c.a>0&&c.a<=count);if(c.op==4)check(c.a>=0&&c.a<39);
        if(c.op==11)check(c.a>=0&&c.a<=12);if(c.op==16)check(c.c>=35&&c.c<=44);a.commands.push_back(c);}
    for(auto& velocity:a.velocities)for(auto& axis:velocity)axis=s8(r.byte());
    r.raw(a.jumpFrames.data(),9);for(auto& axis:a.probe)axis=s16(r.word());r.raw(a.transferChunks.data(),13);
    r.raw(a.hudTiles.data(),a.hudTiles.size());r.raw(a.hudMap.data(),20);r.raw(a.hudColumns.data(),7);
    for(int v:a.tiles)check(v<4);for(int v:a.hudTiles)check(v<4);for(int v:a.quadrants)check(v<127);
    for(int v:a.hudColumns)check(v<20);for(int v:a.jumpFrames)check(v<39);
    for(const auto& f:a.frames)for(int v:f.pixels)check(v<4||v==255);
    check(r.pos==r.data.size());return a;
}
void SkiGame::start(int level,int player){
    playerNumber=player&1;pendingSound=-1;sprites=SpriteLayer(false);reverseSprites=false;
    difficulty=std::clamp(level,0,3);const auto& l=assets.levels[difficulty];entities={};placements=l.objects;
    cameraX=l.cameraX;cameraY=0;seconds=l.seconds;remaining=l.quota;needed=l.quota/2;collected=0;
    ticks=secondTicks=money=jumpVelocity=jumpContact=returnX=returnY=scan=hudCursor=result=resultFlags=held=pressed=previous=animationFaults=0;
    transferState=transferRemaining=transferFrame=transferFlags=0;lastMapCamera=128;mapTransfer=true;
    finishTimer=64;finishZone=false;started=true;paused=false;spawn(35,cameraX+1024,0xff00);
    hudMap=assets.hudMap;refreshHud();for(int j=0;j<7;++j)hudMap[assets.hudColumns[j]]=hudValues[j];
}
void SkiGame::followCamera(){
    const auto& p=entities[0];cameraX=(cameraX+s8(((p.x-cameraX)&4095)/16-64))&65535;
    int delta=s8(((p.y-cameraY)&4095)/16-8);
    cameraY=std::clamp(cameraY+delta,0,(assets.levels[difficulty].rows-9)*256+128);
}
void SkiGame::input(){
    auto& p=entities[0];
    auto turn=[&](int direction){
        if(!p.animDone)return;int pose=s8(p.params[0]);if(pose==direction*2)return;
        pose+=direction;if(!pose)pose+=direction;p.params[0]=static_cast<uint8_t>(pose);
        startAnimation(0,(pose==2||pose==-2)?3:2);
        if(pose==2){spawn(42,p.x+528,p.y+400);spawn(42,p.x+656,p.y+272);pendingSound=22;}
        if(pose==-2){spawn(43,p.x,p.y+400);spawn(43,p.x-144,p.y+272);pendingSound=22;}
    };
    if(held&Left)turn(1);if(held&Right)turn(-1);
    if((held&Down)&&p.animDone&&p.params[0]){int pose=s8(p.params[0]);startAnimation(0,(pose==2||pose==-2)?0:1);p.params[0]=0;}
}
void SkiGame::movePlayer(){
    auto& p=entities[0];int pose=s8(p.params[0]);
    if(pose)p.flags=(p.flags|32)^((pose<0)?32:0);
    p.move(s8(p.params[1]),s8(p.params[2]));
    const auto& target=assets.velocities.at(pose+2);
    for(int repeat=0;repeat<((held&B)?2:1);++repeat){p.params[1]=static_cast<uint8_t>(approach(s8(p.params[1]),target[0]));p.params[2]=static_cast<uint8_t>(approach(s8(p.params[2]),target[1]));}
}
void SkiGame::jump(){
    auto& p=entities[0];spawn(44,p.x+128,p.y+256);p.handler=SkiHandler::Jump;p.params[0]=p.params[1]=0;
    jumpVelocity=-64;setFrame(0,7);pendingSound=24;
}
void SkiGame::jumpMotion(int i){auto& e=entities[i];if(held&Left)e.move(-16,0);if(held&Right)e.move(16,0);e.move(0,24);}
void SkiGame::depth(int i){
    auto& p=entities[i];p.flags&=~128;int row=p.y>>8,bottom=assets.levels[difficulty].rows;
    if(row>bottom-7&&row<=bottom-4){p.flags|=128;finishZone=true;}
}
void SkiGame::terrain(){
    auto& p=entities[0];if((p.y>>8)>assets.levels[difficulty].rows-3)return;
    if(!jumpContact){int bits=terrainAt(p.x+assets.probe[0],p.y+assets.probe[1]);if(bits&4){jump();return;}if(!(bits&11))return;}
    setFrame(0,12);pendingSound=14;beginFinish(0x21);
}
void SkiGame::finishLine(){
    if((entities[0].y>>8)!=assets.levels[difficulty].rows)return;
    beginFinish(s8((needed-1)&255)<0?(remaining?3:7):1);
}
void SkiGame::tickTimer(){if(++secondTicks==60){secondTicks=0;if(seconds)--seconds;}}
void SkiGame::beginFinish(int flags){resultFlags=flags;entities[0].handler=SkiHandler::FinishDelay;if(--finishTimer==0)result=flags;}
void SkiGame::collideWith(int other){
    auto& p=entities[0];auto& o=entities[other];if(!o.alive||o.collision==255)return;
    switch(o.collision){
    case 16:case 17:{int sequence=o.collision==16?4:5;money+=o.collision==16?10:5;o.collision=255;remaining=(remaining-1)&255;needed=(needed-1)&255;++collected;startAnimation(other,sequence);break;}
    case 18:setFrame(0,5);p.x=o.x;p.y=o.y;pendingSound=10;beginFinish(0x21);break;
    case 19:money+=100;o.collision=255;spawn(41,o.x,o.y-128);startAnimation(other,6);break;
    case 20:o.alive=false;p.handler=SkiHandler::Crash;p.params[3]=255;returnX=p.x&0xfff0;returnY=p.y&0xfff0;startAnimation(0,10,true);break;
    default:break;
    }
}
void SkiGame::collide(){
    auto box=[&](const SkiEntity& e){return spriteBounds(assets.frames[e.frame],e.x,e.y,cameraX,cameraY);};
    auto a=box(entities[0]);for(int j=1;j<16;++j){const auto& e=entities[j];if(!e.alive||e.offscreen||e.collision==255)continue;auto b=box(e);
        if(spriteOverlap(a,b))collideWith(j);}
}
void SkiGame::update(int i){
    auto& e=entities[i];
    switch(e.handler){
    case SkiHandler::Intro:e.handler=SkiHandler::Play;break;
    case SkiHandler::Play:
        animate(i);followCamera();input();if(pressed&A){jump();break;}
        movePlayer();depth();finishLine();if(!finishZone){collide();terrain();}tickTimer();if(!seconds)beginFinish(0x11);break;
    case SkiHandler::Jump:{
        followCamera();e.move(0,jumpVelocity>>1);jumpMotion(i);
        setFrame(i,assets.jumpFrames.at(((jumpVelocity+64)&240)>>4));e.flags&=~128;
        finishLine();tickTimer();jumpVelocity=s8(jumpVelocity+(jumpContact?8:2));
        if(jumpVelocity>=68){spawn(42,e.x+528,e.y+400);spawn(43,e.x,e.y+400);pendingSound=4;e.handler=SkiHandler::Play;}break;}
    case SkiHandler::Shadow:
        depth(i);if(terrainAt(e.x+assets.probe[0],e.y+assets.probe[1])&11)jumpContact=1;
        if(entities[0].frame!=7&&entities[0].frame!=8){e.alive=false;break;}jumpMotion(i);break;
    case SkiHandler::Animation:animate(i);break;
    case SkiHandler::Bonus:e.handler=SkiHandler::Animation;startAnimation(i,7);break;
    case SkiHandler::DebrisRight:animate(i);startAnimation(i,8);break;
    case SkiHandler::DebrisLeft:animate(i);startAnimation(i,9);break;
    case SkiHandler::Crash:
        animate(i);followCamera();e.move(0,e.params[3]>>3);depth();finishLine();tickTimer();
        if(--e.params[3]==0){e.flags|=8;e.handler=SkiHandler::Return;e.x&=0xfff0;e.y&=0xfff0;}break;
    case SkiHandler::Return:{
        followCamera();int dx=s16(e.x-returnX),dy=s16(e.y-returnY);e.move(dx>0?-16:dx<0?16:0,dy>0?-16:dy<0?16:0);
        if(!dx&&!dy){e.flags&=~8;e.handler=SkiHandler::Play;e.params[0]=e.params[1]=e.params[2]=0;setFrame(i,0);}break;}
    case SkiHandler::BeginFinish:beginFinish(resultFlags);break;
    case SkiHandler::FinishDelay:if(--finishTimer==0)result=resultFlags;break;
    case SkiHandler::Idle:break;
    }
}
void SkiGame::step(int buttons){
    pendingSound=-1;
    if(!started||paused||result)return;held=buttons;pressed=buttons&~previous;previous=buttons;ticks=(ticks+1)&65535;
    beginVideoTick();tickHud();int oldFrame=entities[0].frame,oldFlags=entities[0].flags;
    for(int j=0;j<16;++j)if(entities[j].alive)update(j);
    finishVideoTick(oldFrame,oldFlags);updateVisibility();mapTransfer=((lastMapCamera^cameraY)&128)!=0;lastMapCamera=cameraY;
    for(int n=0;n<8&&!placements.empty();++n){auto& p=placements[scan];int low=cameraY>>8,high=(low+14)&255,row=((p.y>>8)+3)&255;
        if(!p.active&&low<row&&high>=row){int slot=spawn(p.kind,p.x,p.y,scan);if(slot>=0)p.active=true;}scan=(scan+1)%static_cast<int>(placements.size());}
}
void SkiGame::refreshHud(){
    hudValues[0]=0xf7+playerNumber;int score=money%10000;
    hudValues[1]=0xf6+score/1000;hudValues[2]=0xf6+score/100%10;hudValues[3]=0xf6+score/10%10;hudValues[4]=0xf6+score%10;
    hudValues[5]=0xf6+seconds/10;hudValues[6]=0xf6+seconds%10;
}
void SkiGame::tickHud(){hudMap[assets.hudColumns[hudCursor]]=hudValues[hudCursor];hudCursor=(hudCursor+1)%7;if(!hudCursor)refreshHud();}
void SkiGame::render(bool developmentOverlay){
    int cx=started?cameraX:assets.levels[difficulty].cameraX,cy=started?cameraY:0;
    for(int y=0;y<PlayHeight;++y)for(int x=0;x<Width;++x){int wx=(cx>>4)+x,wy=(cy>>4)+y;int tile=tileAt(wx*16,wy*16);screen[y*Width+x]=assets.tiles[tile*64+(wy&7)*8+(wx&7)];}
    if(started){
        sprites.draw(screen);
        for(int col=0;col<20;++col)for(int y=0;y<8;++y)for(int x=0;x<8;++x)screen[(PlayHeight+y)*Width+col*8+x]=assets.hudTiles[hudMap[col]*64+y*8+x];
    }else{for(int y=64;y<144;++y)std::fill_n(screen.begin()+y*Width,Width,0);text(8,72,"NATIVE PORT - WIP");text(40,88,"SKI SLOPE");text(16,104,"ENTER TO START");text(16,120,"1-4 DIFFICULTY");}
    if(developmentOverlay&&(paused||result)){for(int y=48;y<104;++y)std::fill_n(screen.begin()+y*Width+8,144,0);text(40,56,paused?"PAUSED":"STUNT END");if(result)text(16,72,(result&2)?"TARGET REACHED":"TRY AGAIN");text(16,88,paused?"ESC TO RESUME":"R TO RESTART");}
}
}
