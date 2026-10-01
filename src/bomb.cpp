#include "bomb.h"
#include "sprites.h"
#include <algorithm>
#include <cstdio>
#include <cstring>
#include <stdexcept>
namespace ticd {
namespace {
int s8(int n){return static_cast<int8_t>(n);}
int s16(int n){return static_cast<int16_t>(n);}
struct BombReader {
    std::vector<uint8_t> data;size_t pos=0;
    explicit BombReader(const std::wstring& path){
        FILE* f=_wfopen(path.c_str(),L"rb");
        if(!f)throw std::runtime_error("bomb.dat is missing. Run build.ps1 with the original ROM.");
        fseek(f,0,SEEK_END);long size=ftell(f);rewind(f);
        if(size<8||size>2*1024*1024){fclose(f);throw std::runtime_error("Invalid Bomb Factory data size.");}
        data.resize(size);size_t n=fread(data.data(),1,data.size(),f);fclose(f);
        if(n!=data.size())throw std::runtime_error("Could not read Bomb Factory data.");
    }
    void raw(void* out,size_t n){if(n>data.size()-pos)throw std::runtime_error("Truncated Bomb Factory data.");memcpy(out,data.data()+pos,n);pos+=n;}
    int byte(){uint8_t v;raw(&v,1);return v;}
    int word(){int lo=byte();return lo+(byte()<<8);}
};
void check(bool ok){if(!ok)throw std::runtime_error("Invalid Bomb Factory asset record. Rebuild the local data.");}
}

void BombGame::setFrame(int i,int frame,int flags){
    auto& e=entities[i];e.frame=frame;e.flags=(e.flags&31)|flags;e.animDone=true;e.frameWaiting=false;
}

void BombGame::startAnimation(int i,int sequence,bool force){
    auto& e=entities[i];if(!force&&!e.animDone)return;
    e.anim=assets.animationStarts.at(sequence);e.animDone=false;
}

void BombGame::animate(int i){
    auto& e=entities[i];if(e.animDone||!e.alive)return;
    if(e.delay){--e.delay;return;}
    for(int guard=0;guard<256;++guard){
        if(e.anim<=0||e.anim>=static_cast<int>(assets.commands.size()))break;
        int commandIndex=e.anim;auto c=assets.commands[e.anim];e.anim=c.next;
        switch(c.op){
        case 0:e.animDone=true;return;
        case 1:e.delay=e.period;return;
        case 2:e.move(c.a,0);break;
        case 3:e.move(0,c.a);break;
        case 4:
            if(c.a<20){
                // 00:3c74 keeps the command pointer at the frame operand while
                // its asynchronous graphics transfer is pending.
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
        case 9:e.loop=(e.loop-1)&255;if(e.loop)e.anim=e.loopStart;e.delay=e.period;return;
        case 10:e.anim=c.a;break;
        case 11:e.handler=static_cast<BombHandler>(c.a);e.animDone=true;return;
        case 12:e.move(c.a*16,0);break;
        case 13:e.move(0,c.a*16);break;
        case 14:e.alive=false;e.animDone=true;return;
        case 15:e.flags^=8;break;
        case 16:spawn(c.c,e.x+c.a,e.y+c.b);break;
        case 17:e.flags|=32;break;
        case 18:break; // Original stage activation event; unused by Bomb graphs.
        case 20:collide();break;
        case 19:pendingSound=c.a;break;
        default:++animationFaults;e.animDone=true;return;
        }
    }
    ++animationFaults;e.animDone=true;
}

void BombGame::text(int x,int y,const std::string& value){
    for(char c:value){int n=c==' '?0:c>='0'&&c<='9'?c-'0'+1:c>='A'&&c<='Z'?c-'A'+11:c=='-'?39:0;
        for(int py=0;py<8;++py)for(int px=0;px<8;++px)if(x+px>=0&&x+px<Width&&y+py>=0&&y+py<Height)screen[(y+py)*Width+x+px]=shared.font[n*64+py*8+px];x+=8;}
}


BombAssets BombAssets::load(const std::wstring& path){
    BombReader r(path);char magic[8];r.raw(magic,8);check(!memcmp(magic,"TICDBOM2",8));
    BombAssets a;r.raw(a.tiles.data(),a.tiles.size());r.raw(a.layout.data(),340);
    for(auto& f:a.frames){r.raw(f.meta.data(),8);r.raw(f.pixels.data(),f.pixels.size());readSpritePieces(r,f);}
    for(auto& l:a.levels){for(auto& v:l.speeds)v=r.byte();l.quota=r.byte();r.raw(l.distribution.data(),32);
        for(int v:l.speeds)check(v>0&&v<128);check(l.quota>0&&l.quota<100);
        for(int v:l.distribution)check(v==0||v==47||v==48||(v>=51&&v<=53));}
    for(int j=0;j<7;++j){int k=r.byte();check(k==45||k==46||k==47||k==48||(k>=51&&k<=53));auto& d=a.definitions[k-45];
        d.frame=r.byte();d.flags=r.byte();int h=r.byte();d.handler=static_cast<BombHandler>(h);d.collision=r.byte();r.raw(d.params.data(),7);check(d.frame<33&&h<=10);}
    int roots=r.word(),count=r.word();check(roots==6&&count>0&&count<4096);
    for(int j=0;j<roots;++j){int root=r.word();check(root>0&&root<=count);a.animationStarts.push_back(root);}
    a.commands.push_back({});for(int j=0;j<count;++j){Command c;c.op=r.byte();c.a=s16(r.word());c.b=s16(r.word());c.c=s16(r.word());c.next=r.word();
        check(c.op<=20&&c.next<=count);if(c.op==10)check(c.a>0&&c.a<=count);if(c.op==4)check(c.a>=0&&c.a<33);
        if(c.op==11)check(c.a>=0&&c.a<=10);if(c.op==20)check(c.a==0);a.commands.push_back(c);}
    r.raw(a.transferChunks.data(),20);r.raw(a.upFrames.data(),12);r.raw(a.downFrames.data(),12);
    for(auto& x:a.positions)x=r.word();r.raw(a.stanceFrames.data(),8);
    r.raw(a.hudTiles.data(),a.hudTiles.size());r.raw(a.hudMap.data(),20);r.raw(a.hudColumns.data(),5);
    for(int v:a.tiles)check(v<4);for(int v:a.hudTiles)check(v<4);for(int v:a.layout)check(v<87);
    for(int v:a.hudColumns)check(v<20);for(const auto& f:a.frames)for(int v:f.pixels)check(v<4||v==255);
    check(r.pos==r.data.size());return a;
}
int BombGame::spawn(int kind,int x,int y){
    if(kind<45||kind>53||kind==49||kind==50)return -1;
    for(int j=0;j<16;++j)if(!entities[j].alive){const auto& d=assets.definitions[kind-45];BombEntity e;
        e.alive=true;e.kind=kind;e.frame=d.frame;e.flags=d.flags;e.collision=d.collision;e.handler=d.handler;e.params=d.params;
        e.x=x&65535;e.y=y&65535;entities[j]=e;return j;}
    return -1;
}
void BombGame::start(int level,int player){
    playerNumber=player&1;pendingSound=-1;sprites=SpriteLayer(false);reverseSprites=false;
    difficulty=std::clamp(level,0,3);entities={};speeds=assets.levels[difficulty].speeds;totals={};spawnPending={};displayTotals={};
    ticks=money=cooldown=action=lostLanes=randomState=hudCursor=result=resultFlags=held=pressed=previous=animationFaults=0;
    transferState=transferRemaining=transferFrame=transferFlags=0;finishTimer=64;started=true;paused=false;
    spawn(45,0,256);for(int x:{192,1088,1984})for(int y:{384,896})spawn(46,x,y);
    hudMap=assets.hudMap;refreshHud();for(int j=0;j<5;++j)hudMap[assets.hudColumns[j]]=hudValues[j];
}
void BombGame::beginVideoTick(){
    // Bomb's room never scrolls: 00:10e7 can transfer four chunks each tick.
    if(transferRemaining){transferRemaining=std::max(0,transferRemaining-4);
        if(!transferRemaining){entities[0].frame=transferFrame;entities[0].flags=transferFlags;transferState=2;}}
}
void BombGame::finishVideoTick(int oldFrame,int oldFlags){
    if(transferState==2)transferState=0;auto& p=entities[0];
    if(p.frame<20&&p.frame!=oldFrame){
        if(!transferState){transferState=1;transferFrame=-1;}
        if(p.frame!=transferFrame){transferRemaining=assets.transferChunks[p.frame];if(!transferRemaining)return;transferFrame=p.frame;transferFlags=p.flags;}
        p.frame=oldFrame;p.flags=oldFlags;
    }
}
void BombGame::updateVisibility(){
    reverseSprites=!reverseSprites;sprites=SpriteLayer(reverseSprites);
    for(auto& e:entities)if(e.alive){e.offscreen=false;if(e.flags&8)continue;
        const auto& m=assets.frames[e.frame].meta;int x=s16(e.x&0xfff0)/16+s8(m[0]),y=s16(e.y&0xfff0)/16+s8(m[1]);
        if(x < -2*m[6]-16||x>176||y < -2*m[7]-16||y>152){if(e.flags&16)e.alive=false;else e.offscreen=true;}
        else {sprites.add(assets.frames[e.frame],s16(e.x&0xfff0)/16,s16(e.y&0xfff0)/16,e.flags);if(sprites.exhausted())return;}
    }
}
void BombGame::movePlayer(bool down){
    if(cooldown)return;auto& p=entities[0];const auto& table=down?assets.downFrames:assets.upFrames;
    int offset=(p.params[1]&252)/2;setFrame(0,table.at(offset),table.at(offset+1));
    if(down?(p.y>>8)>=5:p.y<64)return;p.move(0,down?16:-16);p.params[1]=(p.params[1]+1)%24;
}
void BombGame::startAction(int kind){
    if(cooldown)return;auto& p=entities[0];startAnimation(0,(kind==1?0:2)+(p.params[0]&1));
    p.handler=BombHandler::Animation;action=kind;
}
int BombGame::randomByte(){
    int swapped=((randomState&255)<<8)|(randomState>>8),first=(randomState-swapped)&65535;
    int value=(first-swapped-(randomState<swapped)+254)&65535;
    int lo=value&255,hi=value>>8,out=(lo-hi-(lo>=hi))&255;randomState=(randomState&255)|(out<<8);return out;
}
void BombGame::emitObjects(){
    for(int lane=0;lane<3;++lane)if(spawnPending[lane]){spawnPending[lane]=0;
        int kind=assets.levels[difficulty].distribution[randomByte()&31];if(kind)spawn(kind,256+896*lane,0xff80);}
}
int BombGame::lane(int i)const {int x=entities[i].x>>8;return x==1?0:x==4?1:2;}
void BombGame::speedUp(int i){int& speed=speeds[lane(i)];if(speed&&speed!=127)++speed;}
void BombGame::explode(int i){pendingSound=14;entities[i].handler=BombHandler::Animation;startAnimation(i,5,true);}
void BombGame::moveObject(int i){
    auto& e=entities[i];int speed=speeds[lane(i)];e.move(0,s8(speed));
    if((e.y>>8)==4){e.handler=BombHandler::Fall;e.params[0]=static_cast<uint8_t>(speed);fall(i);}
}
void BombGame::fall(int i){
    auto& e=entities[i];e.params[0]+=2;e.move(0,s8(e.params[0]));if((e.y>>8)<5)return;
    int l=lane(i);pendingSound=4;
    if(e.frame==23){e.alive=false;totals[l]=(totals[l]+1)%100;money+=5;return;}
    if(e.frame==25||e.frame==31||e.frame==32){entities[0].params[2]=0;e.alive=false;speedUp(i);return;}
    entities[0].params[2]=0;
    if(!lostLanes){int extra=(s8(speeds[l])>>1)+1;for(int j=0;j<3;++j)if(j!=l)speeds[j]=(speeds[j]+extra)&255;}
    speeds[l]=0;lostLanes=(lostLanes+1)&255;explode(i);
}
void BombGame::collideWith(int other){
    auto& o=entities[other];if(!o.alive||o.collision==255)return;
    switch(o.collision){
    case 22: // 01:7218: A removes the fuse; B blows up the armed bomb.
        if(action!=1){o.frame=23;o.handler=BombHandler::Disarmed;o.collision=23;money+=10;break;}
        explode(other);speedUp(other);break;
    case 23:if(action==1){explode(other);speedUp(other);}break;
    case 31:case 32:case 33:if(action==1){pendingSound=9;money+=o.collision==31?25:o.collision==32?15:10;o.alive=false;}break;
    default:break;
    }
}
void BombGame::collide(){
    auto box=[&](const BombEntity& e){return spriteBounds(assets.frames[e.frame],e.x,e.y,0,0);};
    auto a=box(entities[0]);for(int j=1;j<16;++j){const auto& e=entities[j];if(!e.alive||e.offscreen||e.collision==255)continue;auto b=box(e);
        if(spriteOverlap(a,b))collideWith(j);}
}
void BombGame::beginFinish(int flags){resultFlags=flags;entities[0].handler=BombHandler::FinishDelay;if(--finishTimer==0)result=flags;}
void BombGame::update(int i){
    auto& e=entities[i];
    switch(e.handler){
    case BombHandler::Play:
        if(cooldown)--cooldown;emitObjects();displayTotals=totals;
        setFrame(0,assets.stanceFrames[e.params[0]*2+1],assets.stanceFrames[e.params[0]*2]);
        if(transferState==2)e.x=assets.positions[e.params[0]];
        if(held&Up)movePlayer(false);if(held&Down)movePlayer(true);
        if(pressed&Left){e.params[0]=(e.params[0]-1)&3;cooldown=4;}
        if(pressed&Right){e.params[0]=(e.params[0]+1)&3;cooldown=4;}
        if(held&B)startAction(1);if(held&A)startAction(2);
        if((totals[0]+totals[1]+totals[2])%100>=assets.levels[difficulty].quota)beginFinish(e.params[2]?0x47:0x43);
        else if(lostLanes>=2)beginFinish(1);break;
    case BombHandler::Belt:{
        int l=(e.x>>8)==0?0:(e.x>>8)==4?1:2;e.move(0,s8(speeds[l]));
        if((e.y>>8)==5&&(e.y&255)>=128){e.y=384;spawnPending[l]=(spawnPending[l]+1)&255;}break;}
    case BombHandler::Disarmed:case BombHandler::Bonus:moveObject(i);break;
    case BombHandler::Armed:
        animate(i);moveObject(i);startAnimation(i,4);
        if(speeds[lane(i)])break;
        e.handler=BombHandler::Stopped;e.params[0]=static_cast<uint8_t>(((e.y&255)-48)*4);
        [[fallthrough]];
    case BombHandler::Stopped:
        animate(i);startAnimation(i,4);if(--e.params[0]==0)explode(i);break;
    case BombHandler::Fall:fall(i);break;
    case BombHandler::Animation:animate(i);break;
    case BombHandler::FinishDelay:if(--finishTimer==0)result=resultFlags;break;
    case BombHandler::BeginFinish:beginFinish(resultFlags);break;
    case BombHandler::Idle:break;
    }
}
void BombGame::step(int buttons){
    pendingSound=-1;
    if(!started||paused||result)return;held=buttons;pressed=buttons&~previous;previous=buttons;ticks=(ticks+1)&65535;
    beginVideoTick();tickHud();int oldFrame=entities[0].frame,oldFlags=entities[0].flags;
    for(int j=0;j<16;++j)if(entities[j].alive)update(j);
    finishVideoTick(oldFrame,oldFlags);updateVisibility();
}
void BombGame::refreshHud(){hudValues[0]=0xf7+playerNumber;int score=money%10000;
    hudValues[1]=0xf6+score/1000;hudValues[2]=0xf6+score/100%10;hudValues[3]=0xf6+score/10%10;hudValues[4]=0xf6+score%10;}
void BombGame::tickHud(){hudMap[assets.hudColumns[hudCursor]]=hudValues[hudCursor];hudCursor=(hudCursor+1)%5;if(!hudCursor)refreshHud();}
void BombGame::render(bool developmentOverlay){
    auto room=assets.layout;for(int l=0;l<3;++l){int x=2+7*l,total=displayTotals[l];room[15*20+x]=47+2*(total/10);room[15*20+x+1]=67+2*(total%10);
        room[16*20+x]=room[15*20+x]+1;room[16*20+x+1]=room[15*20+x+1]+1;}
    for(int y=0;y<PlayHeight;++y)for(int x=0;x<Width;++x)screen[y*Width+x]=assets.tiles[room[(y/8)*20+x/8]*64+(y&7)*8+(x&7)];
    if(started){sprites.draw(screen);
        for(int col=0;col<20;++col)for(int y=0;y<8;++y)for(int x=0;x<8;++x)screen[(PlayHeight+y)*Width+col*8+x]=assets.hudTiles[hudMap[col]*64+y*8+x];
    }else{for(int y=64;y<144;++y)std::fill_n(screen.begin()+y*Width,Width,0);text(8,72,"NATIVE PORT - WIP");text(32,88,"BOMB FACTORY");text(16,104,"ENTER TO START");text(16,120,"1-4 DIFFICULTY");}
    if(developmentOverlay&&(paused||result)){for(int y=48;y<104;++y)std::fill_n(screen.begin()+y*Width+8,144,0);text(40,56,paused?"PAUSED":"STUNT END");if(result)text(16,72,(result&2)?"TARGET REACHED":"TRY AGAIN");text(16,88,paused?"ESC TO RESUME":"R TO RESTART");}
}
}
