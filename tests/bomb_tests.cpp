#include "bomb.h"
#include <algorithm>
#include <cstdio>
#include <stdexcept>
namespace ticd {
namespace {
// Planner observes state and forecasts A in a copy. The actual game receives
// only Button inputs; no actor, score, quota or result values are injected.
int bombInput(const BombGame& game){
    const auto& player=game.entities[0];if(player.handler!=BombHandler::Play)return 0;
    int target=-1,urgency=-99999;
    for(int i=1;i<16;++i){const auto& e=game.entities[i];int y=static_cast<int16_t>(e.y);
        if(e.alive&&e.collision==22&&game.speeds[game.lane(i)]&&y>urgency){target=i;urgency=y;}}
    if(target<0)return 0;
    int lane=game.lane(target),pose=player.params[0],desired=lane==0?0:lane==2?3:(pose<2?1:2);
    if(pose!=desired){int key=((desired-pose)&3)<=2?Right:Left;return game.previous&key?0:key;}
    BombGame forecast=game;for(int frame=0;frame<28&&!forecast.result;++frame)forecast.step(A);
    if(forecast.entities[target].collision==23&&forecast.money>game.money)return A;
    int goal=std::clamp(static_cast<int>(static_cast<int16_t>(game.entities[target].y)),64,1280);
    return player.y>goal+8?Up:player.y<goal-8?Down:0;
}
}
int bombTestInput(const BombGame& game){return bombInput(game);}
int runBombTests(const BombAssets& assets,const Assets& shared){
    FILE* log=fopen("bomb-test.txt","w");if(!log)return 2;int count=0;
    auto require=[&](bool value,const char* message){++count;if(!value)throw std::runtime_error(message);};
    try{
        BombGame g(assets,shared);g.start(0);
        require(g.entities[0].y==256&&g.entities[0].params[2]==1&&g.speeds==std::array<int,3>{3,3,3},"Original Bomb start and perfect flag");
        require(g.entities[1].x==192&&g.entities[6].y==896,"Six belt markers begin at original spacing");
        g.step(Right);require(g.entities[0].params[0]==1&&g.cooldown==4,"Lane changes use press edges and arm movement delay");
        g.step(Right);require(g.entities[0].params[0]==1&&g.cooldown==3,"Holding Right does not change lane repeatedly");
        g.start(0);g.update(0);require(g.entities[0].frame==6&&g.entities[0].x==0,"Stance requests frame before repositioning");
        g.transferState=2;g.update(0);require(g.entities[0].x==576,"Only completed sprite transfer repositions player");
        g.start(0);g.entities[0].y=64;g.movePlayer(false);require(g.entities[0].y==48,"Up includes one final step at exact top boundary");
        g.movePlayer(false);require(g.entities[0].y==48,"Up stops below top boundary");
        g.entities[0].y=1280;g.movePlayer(true);require(g.entities[0].y==1280,"Down stops at row five");
        g.start(0);int obj=g.spawn(48,256,512);g.action=2;g.collideWith(obj);
        require(g.entities[obj].frame==23&&g.entities[obj].collision==23&&g.money==10,"A removes fuse and awards ten");
        g.pendingSound=-1;g.explode(obj);require(g.pendingSound==14,"Bomb explosion queues original effect 14");
        g.collideWith(obj);require(g.money==10,"A cannot score on the same disarmed bomb twice");
        g.entities[obj].y=1279;g.entities[obj].params[0]=0;g.fall(obj);
        require(!g.entities[obj].alive&&g.totals[0]==1&&g.money==15,"Disarmed bomb reaching bottom counts and awards five");
        g.start(0);obj=g.spawn(48,1152,1279);g.fall(obj);
        require(g.lostLanes==1&&g.speeds==std::array<int,3>{5,0,5}&&!g.entities[0].params[2],"First missed bomb stops its belt and accelerates both others");
        obj=g.spawn(48,2048,1279);g.fall(obj);require(g.lostLanes==2&&g.speeds[0]==5,"Second belt loss does not accelerate survivor again");
        g.update(0);require(g.resultFlags==1&&g.finishTimer==63,"Two belt losses start failure delay");
        g.start(0);obj=g.spawn(48,256,200);g.action=1;g.collideWith(obj);
        require(g.speeds[0]==4&&g.entities[obj].handler==BombHandler::Animation,"B explodes armed bomb and increases that belt's speed");
        g.speeds[0]=127;g.speedUp(obj);require(g.speeds[0]==127,"Belt acceleration saturates at 127");
        g.speeds[0]=0;g.speedUp(obj);require(g.speeds[0]==0,"Stopped belts stay stopped");
        for(int perfect:{0,1}){g.start(0);g.totals={20,20,0};g.entities[0].params[2]=perfect;g.update(0);require(g.resultFlags==(perfect?0x47:0x43),"Quota distinguishes perfect and ordinary success");}
        for(int d=0;d<4;++d)for(int pattern=0;pattern<3;++pattern){
            g.start(d);for(int t=0;t<40000&&!g.result;++t){
                int input=pattern==0?0:pattern==1?A:((t%120==0)?Right:A);
                g.step(input);require(g.animationFaults==0,"Bomb replay animation graph valid");
                for(const auto& e:g.entities)if(e.alive)require(e.frame>=0&&e.frame<33,"Bomb replay frame bounds");
            }
            fprintf(log,"difficulty=%d pattern=%d ticks=%d flags=%02x money=%d counts=%d/%d/%d\n",d,pattern,g.ticks,g.result,g.money,g.totals[0],g.totals[1],g.totals[2]);
            require(g.result!=0,"Bomb replay reaches terminal result");g.render();for(int shade:g.screen)require(shade>=0&&shade<4,"Bomb palette bounds");
        }
        for(int d=0;d<4;++d){
            g.start(d);std::vector<int> replay;
            for(int t=0;t<10000&&!g.result;++t){int input=bombInput(g);replay.push_back(input);g.step(input);}
            require(g.result==0x43,"Input-only Bomb planner completes every difficulty without injected outcomes");
            require(g.totals[0]+g.totals[1]+g.totals[2]>=assets.levels[d].quota,"Successful replay fills original quota");
            BombGame replayed(assets,shared);replayed.start(d);for(int input:replay)replayed.step(input);
            require(replayed.result==g.result&&replayed.money==g.money&&replayed.totals==g.totals,"Recorded inputs reproduce success from a fresh state");
            fprintf(log,"input-only success difficulty=%d ticks=%d flags=%02x money=%d counts=%d/%d/%d\n",d,g.ticks,g.result,g.money,g.totals[0],g.totals[1],g.totals[2]);
        }
        BombGame secondPlayer(assets,shared);secondPlayer.start(0,1);require(secondPlayer.hudValues[0]==0xf8,"bomb HUD identifies second campaign player");
        fprintf(log,"PASS: %d assertions. Native rule/replay checks; original equivalence remains unverified.\n",count);fclose(log);return 0;
    }catch(const std::exception& e){fprintf(log,"FAIL after %d assertions: %s\n",count,e.what());fclose(log);return 1;}
}
}
